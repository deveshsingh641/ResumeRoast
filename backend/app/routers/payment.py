"""
Payment and Billing Router — supports India-first Razorpay in-page checkout
(UPI, QR, Netbanking, Cards) as primary provider, with Stripe and test simulation fallbacks.
"""
from __future__ import annotations

import collections
from datetime import datetime, timezone
import hashlib
import hmac
import json
import logging
import os
import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import stripe

from app.db import database
from app.core.limiter import limiter
from app.services.pro_auth import create_pro_token, get_authenticated_pro_email
from app.services.admin_auth import verify_admin_access

logger = logging.getLogger("payment")
router = APIRouter(prefix="/api", tags=["payment"])

# Plan Pricing (always strictly computed server-side in paise)
# INR 99 = 9900 paise; INR 799 = 79900 paise
PLAN_PRICES: Dict[str, int] = {
    "monthly": 9900,   # ₹99.00 in paise
    "annual":  79900,  # ₹799.00 in paise
}

PLAN_NAMES: Dict[str, str] = {
    "monthly": "Resume Roast Pro (Monthly)",
    "annual":  "Resume Roast Pro (Annual)",
}


def _clean_env(key: str, default: str = "") -> str:
    """Read and clean environment variable, stripping quotes and whitespace."""
    val = os.getenv(key, default).strip()
    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
        val = val[1:-1].strip()
    return val


def get_razorpay_config() -> Dict[str, Any]:
    """Retrieve up-to-date Razorpay configuration and environment mode."""
    key_id = _clean_env("RAZORPAY_KEY_ID")
    key_secret = _clean_env("RAZORPAY_KEY_SECRET")
    webhook_secret = _clean_env("RAZORPAY_WEBHOOK_SECRET")

    is_live = key_id.startswith("rzp_live_")
    is_test = key_id.startswith("rzp_test_")
    is_configured = bool(key_id and key_secret)
    mode = "live" if is_live else ("test" if is_test else ("custom" if is_configured else "simulation"))

    return {
        "key_id": key_id,
        "key_secret": key_secret,
        "webhook_secret": webhook_secret,
        "is_configured": is_configured,
        "mode": mode,
    }


def _mask_key(key: str) -> Optional[str]:
    """Return masked key for safe diagnostic display."""
    if not key:
        return None
    if len(key) <= 8:
        return "****"
    return f"{key[:8]}****{key[-4:]}"


class CreateOrderRequest(BaseModel):
    email: Optional[str] = None
    plan: Optional[str] = "monthly"  # "monthly" | "annual"
    amount: Optional[int] = None      # amount in paise (min 100)
    currency: Optional[str] = "INR"
    receipt: Optional[str] = None
    force_fresh: Optional[bool] = False  # bypass cached active order on retry


class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    razorpay_signature: Optional[str] = None
    email: Optional[str] = None
    plan: Optional[str] = "monthly"


class PaymentFailureLogRequest(BaseModel):
    email: str
    stage: str
    error_message: str
    order_id: Optional[str] = None
    plan: Optional[str] = "monthly"
    user_agent: Optional[str] = None


class CheckoutRequest(BaseModel):
    email: str
    plan: str = "monthly"


class CancelRequest(BaseModel):
    email: str


class ReconcilePaymentRequest(BaseModel):
    email: str
    order_id: Optional[str] = None
    payment_id: Optional[str] = None


# In-memory deduplication set for processed payments/webhooks (idempotency guard)
_processed_payments: set[str] = set()

# Deduplication cache for active orders: (email, plan) -> (timestamp, order_data)
_active_orders_cache: dict[tuple[str, str], tuple[float, dict]] = {}

# Order to Email binding map (IDOR and cross-user tampering protection)
_order_email_map: dict[str, str] = {}

# In-memory telemetry log for recent payment failures (viewable via /billing/diagnostics)
_recent_payment_failures: collections.deque = collections.deque(maxlen=50)


# ---------------------------------------------------------------------------
# Diagnostics & Public Config
# ---------------------------------------------------------------------------
@router.get("/billing/diagnostics")
@router.get("/payment/diagnostics")
async def billing_diagnostics() -> JSONResponse:
    """
    Diagnostic endpoint to inspect payment gateway environment health.
    Validates Razorpay keys, webhook secret, currency configuration, and prices.
    Never exposes raw secrets.
    """
    rzp = get_razorpay_config()
    stripe_key = _clean_env("STRIPE_SECRET_KEY")
    stripe_webhook = _clean_env("STRIPE_WEBHOOK_SECRET")

    # Verify Razorpay client initialization if keys are present
    client_init_ok = False
    client_error = None
    if rzp["is_configured"]:
        try:
            import razorpay
            _ = razorpay.Client(auth=(rzp["key_id"], rzp["key_secret"]))
            client_init_ok = True
        except Exception as e:
            client_error = str(e)

    status = "healthy" if (rzp["is_configured"] and client_init_ok) else (
        "simulation_mode" if not rzp["is_configured"] else "configuration_error"
    )

    return JSONResponse(
        content={
            "status": status,
            "provider": "razorpay",
            "razorpay": {
                "configured": rzp["is_configured"],
                "mode": rzp["mode"],
                "key_id_masked": _mask_key(rzp["key_id"]),
                "key_secret_set": bool(rzp["key_secret"]),
                "webhook_secret_set": bool(rzp["webhook_secret"]),
                "client_initialized": client_init_ok,
                "client_error": client_error,
            },
            "stripe": {
                "configured": bool(stripe_key),
                "key_masked": _mask_key(stripe_key),
                "webhook_secret_set": bool(stripe_webhook),
            },
            "plans": {
                plan: {
                    "amount_paise": paise,
                    "amount_inr": paise / 100.0,
                    "name": PLAN_NAMES[plan],
                }
                for plan, paise in PLAN_PRICES.items()
            },
            "currency": "INR",
            "recent_failures": list(_recent_payment_failures),
            "server_timestamp": int(time.time()),
        }
    )


@router.post("/payment/log-failure")
@router.post("/billing/log-failure")
async def log_payment_failure(payload: PaymentFailureLogRequest, request: Request) -> JSONResponse:
    """
    Client-reported payment telemetry endpoint.
    Logs checkout issues, modal timeouts, or declined transactions for real-time visibility.
    """
    clean_email = payload.email.strip().lower()
    entry = {
        "email": clean_email,
        "stage": payload.stage,
        "error_message": payload.error_message,
        "order_id": payload.order_id,
        "plan": payload.plan,
        "user_agent": payload.user_agent or request.headers.get("user-agent", "unknown"),
        "ip": request.client.host if request.client else "unknown",
        "timestamp": int(time.time()),
        "iso_time": datetime.now(timezone.utc).isoformat(),
    }
    _recent_payment_failures.append(entry)
    logger.error(
        f"[PAYMENT TELEMETRY FAILURE] {clean_email} | stage={payload.stage} | order_id={payload.order_id} | error={payload.error_message}"
    )

    # Invalidate active cached order so subsequent retries are completely fresh
    for configured in (True, False):
        k = (clean_email, (payload.plan or "monthly").lower(), configured)
        if k in _active_orders_cache:
            del _active_orders_cache[k]

    return JSONResponse(content={"status": "logged", "timestamp": entry["timestamp"]})


@router.get("/billing/config")
@router.get("/payment/config")
async def billing_public_config() -> JSONResponse:
    """
    Safe public configuration for frontend checkout orchestration.
    Provides key ID, preferred mode, and active plan details.
    """
    rzp = get_razorpay_config()
    return JSONResponse(
        content={
            "provider": "razorpay",
            "mode": rzp["mode"],
            "simulated": not rzp["is_configured"],
            "key_id": rzp["key_id"] if rzp["is_configured"] else "rzp_test_simulation",
            "currency": "INR",
            "plans": {
                plan: {
                    "amount_paise": paise,
                    "amount_inr": int(paise / 100),
                    "name": PLAN_NAMES[plan],
                }
                for plan, paise in PLAN_PRICES.items()
            },
        }
    )


# ---------------------------------------------------------------------------
# 1. Razorpay Order Creation (Standard Checkout)
# ---------------------------------------------------------------------------
@router.post("/create-order")
@router.post("/billing/create-order")
@router.post("/payment/create-order")
@router.post("/payment/create-checkout-session")
@limiter.limit("20/minute")
async def create_razorpay_order(payload: CreateOrderRequest, request: Request) -> JSONResponse:
    """
    Create a Razorpay Order for in-page Standard Checkout.
    Validates amount >= 100 paise.
    Returns: { status, order_id, amount, currency, key_id }
    """
    # Strict server-side plan & price resolution (Anti-Tampering)
    plan = (payload.plan or "monthly").lower()
    if plan not in PLAN_PRICES:
        plan = "monthly"
    server_price = PLAN_PRICES[plan]
    plan_name = PLAN_NAMES[plan]

    # Amount validation: enforce minimum and reject client price tampering
    if payload.amount is not None:
        if payload.amount < 100:
            raise HTTPException(
                status_code=400,
                detail="Minimum order amount is 100 paise (₹1.00).",
            )
        if payload.amount != server_price:
            logger.warning(
                f"Client amount tampering attempt rejected: received {payload.amount}, expected {server_price} for plan '{plan}'"
            )
            raise HTTPException(
                status_code=400,
                detail=f"Invalid order amount for plan '{plan}'. Expected {server_price} paise.",
            )

    amount_paise = server_price

    # Email validation
    if payload.email:
        email = payload.email.strip().lower()
        if "@" not in email:
            raise HTTPException(
                status_code=422,
                detail="Please provide a valid email address.",
            )
    else:
        email = "candidate@resumeroast.com"

    currency = (payload.currency or "INR").upper()
    rzp = get_razorpay_config()
    logger.info(
        f"Initiating Razorpay order for {email} (amount={amount_paise} paise, currency={currency}, mode={rzp['mode']})"
    )

    now = time.time()
    cache_key = (email, plan, rzp["is_configured"])

    # 0. Reuse active order if created within the last 180s (unless force_fresh requested on retry)
    if payload.force_fresh and cache_key in _active_orders_cache:
        logger.info(f"force_fresh requested by client on retry; evicting cached order for {email}")
        del _active_orders_cache[cache_key]
    elif cache_key in _active_orders_cache:
        cached_ts, cached_data = _active_orders_cache[cache_key]
        if now - cached_ts < 180:
            logger.info(
                f"Reusing active uncompleted order {cached_data['order_id']} for {email} (idempotent cache hit)"
            )
            return JSONResponse(content=cached_data)
        else:
            del _active_orders_cache[cache_key]

    # Developer Simulation Mode (when keys not configured)
    if not rzp["is_configured"]:
        logger.warning(
            "RAZORPAY_KEY_ID or RAZORPAY_KEY_SECRET is not configured in backend environment. "
            "Returning developer simulation order."
        )
        simulated_order_id = f"order_sim_{int(time.time())}_{hashlib.md5(email.encode()).hexdigest()[:8]}"
        resp_payload = {
            "status": "success",
            "order_id": simulated_order_id,
            "amount": amount_paise,
            "currency": currency,
            "key_id": "rzp_test_simulation",
            "plan": plan,
            "plan_name": plan_name,
            "simulated": True,
            "message": (
                "Running in developer simulation mode. "
                "Configure RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in backend/.env to run live/test transactions."
            ),
        }
        _active_orders_cache[cache_key] = (now, resp_payload)
        _order_email_map[simulated_order_id] = email
        return JSONResponse(content=resp_payload)

    # Real Razorpay Order Creation via official SDK (POST https://api.razorpay.com/v1/orders)
    try:
        import razorpay

        client = razorpay.Client(auth=(rzp["key_id"], rzp["key_secret"]))

        # Receipt ID must be under 40 characters for Razorpay API
        receipt_id = (
            payload.receipt
            if payload.receipt
            else f"rcpt_{int(time.time())}_{hashlib.md5(email.encode()).hexdigest()[:6]}"
        )[:40]

        order_data = {
            "amount": amount_paise,
            "currency": currency,
            "receipt": receipt_id,
            "notes": {
                "email": email,
                "plan": plan,
                "plan_name": plan_name,
                "app": "ResumeRoast",
            },
        }

        order = client.order.create(data=order_data)
        logger.info(f"Razorpay order created successfully: {order.get('id')} for {email}")

        resp_payload = {
            "status": "success",
            "order_id": order["id"],
            "amount": order["amount"],
            "currency": order["currency"],
            "key_id": rzp["key_id"],
            "plan": plan,
            "plan_name": plan_name,
            "simulated": False,
        }
        _active_orders_cache[cache_key] = (now, resp_payload)
        _order_email_map[order["id"]] = email

        return JSONResponse(content=resp_payload)
    except Exception as e:
        logger.exception(f"Razorpay order creation failed for {email}: {e}")
        error_msg = str(e)
        status_code = 500

        # Handle auth failures (return 401)
        if "AuthenticationError" in type(e).__name__ or "401" in error_msg:
            status_code = 401
            error_msg = "Razorpay authentication failed: Invalid Key ID or Key Secret in backend environment."
        elif "BadRequestError" in type(e).__name__:
            status_code = 400

        raise HTTPException(
            status_code=status_code,
            detail=f"Razorpay order initialization failed: {error_msg}",
        )


# ---------------------------------------------------------------------------
# 2. Razorpay Signature Verification & Database Pro Upgrade
# ---------------------------------------------------------------------------
@router.post("/verify-payment")
@router.post("/billing/verify-payment")
@router.post("/payment/verify-payment")
@limiter.limit("20/minute")
async def verify_razorpay_payment(payload: VerifyPaymentRequest, request: Request) -> JSONResponse:
    """
    Verify the cryptographic HMAC-SHA256 signature returned by Razorpay Checkout.
    Algorithm: HMAC-SHA256(order_id + "|" + payment_id, KEY_SECRET)
    Returns success only if signatures match, and updates user subscription to Pro in DB.
    """
    order_id = (payload.razorpay_order_id or "").strip()
    payment_id = (payload.razorpay_payment_id or "").strip()
    client_signature = (payload.razorpay_signature or "").strip()
    email = (payload.email or "").strip().lower() or "candidate@resumeroast.com"

    # Missing fields check (return 400)
    if not order_id or not payment_id or not client_signature:
        raise HTTPException(
            status_code=400,
            detail="Missing required payment verification fields (razorpay_order_id, razorpay_payment_id, razorpay_signature).",
        )

    # Authorization guard: ensure order belongs to the claiming email (IDOR protection)
    mapped_email = _order_email_map.get(order_id)
    if mapped_email and mapped_email != email:
        logger.warning(
            f"Unauthorized payment verification: order {order_id} belongs to {mapped_email}, but {email} attempted verification."
        )
        raise HTTPException(
            status_code=403,
            detail="Unauthorized payment verification: order does not belong to the claiming user.",
        )

    rzp = get_razorpay_config()
    logger.info(f"Verifying payment: order={order_id}, payment={payment_id} for {email}")

    # Evict from active orders cache
    _active_orders_cache.pop((email, payload.plan or "monthly", True), None)
    _active_orders_cache.pop((email, payload.plan or "monthly", False), None)

    # Idempotency check: if payment_id already verified, return immediate success
    if payment_id and payment_id in _processed_payments:
        logger.info(f"Payment {payment_id} already verified (idempotent skip for {email}).")
        database.create_or_get_user(email)
        database.update_subscription(email, "pro", customer_id=payment_id)
        pro_token = create_pro_token(email)
        resp = JSONResponse(
            content={
                "status": "success",
                "is_pro": True,
                "idempotent": True,
                "message": "Payment already verified successfully. Pro access is active!",
                "order_id": order_id,
                "payment_id": payment_id,
            }
        )
        resp.set_cookie("resumeroast_pro_token", pro_token, max_age=30*86400, httponly=True, samesite="lax")
        return resp

    # 1. Developer Simulation Mode Approval (STRICTLY when Razorpay keys are not configured)
    if not rzp["is_configured"]:
        if not order_id.startswith("order_sim_"):
            raise HTTPException(
                status_code=400,
                detail="Invalid simulation order ID format.",
            )
        logger.info(f"Approving developer simulation payment for {email}")
        database.create_or_get_user(email)
        database.update_subscription(email, "pro", customer_id=f"sim_{payment_id}")
        if payment_id:
            _processed_payments.add(payment_id)
        pro_token = create_pro_token(email)
        resp = JSONResponse(
            content={
                "status": "success",
                "is_pro": True,
                "simulated": True,
                "message": "Payment verified in simulation mode. Pro access unlocked!",
                "order_id": order_id,
                "payment_id": payment_id,
            }
        )
        resp.set_cookie("resumeroast_pro_token", pro_token, max_age=30*86400, httponly=True, samesite="lax")
        return resp

    # Section 0B Defense: When keys ARE configured, strictly reject any simulation prefix!
    if order_id.startswith("order_sim_") or payment_id.startswith("pay_sim_"):
        logger.warning(f"Payment bypass attempt rejected: simulation credentials sent when Razorpay is active for {email}")
        raise HTTPException(
            status_code=400,
            detail="Simulation payment credentials are not permitted when Razorpay live/test configuration is active.",
        )

    # 2. Cryptographic HMAC-SHA256 Verification: HMAC-SHA256(order_id + "|" + payment_id, KEY_SECRET)
    try:
        msg = f"{order_id}|{payment_id}".encode("utf-8")
        expected_signature = hmac.new(
            rzp["key_secret"].encode("utf-8"),
            msg,
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected_signature, client_signature):
            logger.warning(
                f"Razorpay signature mismatch for order={order_id}, payment={payment_id}, email={email}"
            )
            # Signature mismatch: return 400, do NOT mark as paid
            raise HTTPException(
                status_code=400,
                detail="Invalid payment signature. Payment verification failed.",
            )

        # Grant Pro access in database
        database.create_or_get_user(email)
        database.update_subscription(email, "pro", customer_id=payment_id)
        if payment_id:
            _processed_payments.add(payment_id)
        logger.info(f"Successfully verified Razorpay payment and upgraded {email} to Pro.")

        pro_token = create_pro_token(email)
        resp = JSONResponse(
            content={
                "status": "success",
                "is_pro": True,
                "simulated": False,
                "message": "Payment verified successfully. Pro access is now active!",
                "order_id": order_id,
                "payment_id": payment_id,
            }
        )
        resp.set_cookie("resumeroast_pro_token", pro_token, max_age=30*86400, httponly=True, samesite="lax")
        return resp
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error during payment verification for {email}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Server error verifying payment: {str(e)}",
        )


# ---------------------------------------------------------------------------
# 3. Razorpay Webhook Handler (Idempotent & Signature-Verified)
# ---------------------------------------------------------------------------
@router.post("/billing/webhook")
@router.post("/payment/webhook")
async def razorpay_webhook(
    request: Request,
    signature: Optional[str] = Header(None, alias="X-Razorpay-Signature"),
) -> JSONResponse:
    """
    Asynchronous Webhook handler for Razorpay.
    Guaranteed fallback to grant Pro access if the user closed their tab before client verification.
    """
    body_bytes = await request.body()
    rzp = get_razorpay_config()

    # Webhook signature verification
    if rzp["mode"] == "live" and not rzp["webhook_secret"]:
        logger.error("RAZORPAY_WEBHOOK_SECRET is not configured in live mode. Rejecting unauthenticated webhook.")
        raise HTTPException(
            status_code=500,
            detail="RAZORPAY_WEBHOOK_SECRET is not configured on the server for live mode.",
        )

    if rzp["webhook_secret"]:
        if not signature:
            logger.warning("Missing X-Razorpay-Signature header in webhook request.")
            raise HTTPException(status_code=400, detail="Missing X-Razorpay-Signature header.")

        expected_sig = hmac.new(
            rzp["webhook_secret"].encode("utf-8"),
            body_bytes,
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected_sig, signature):
            logger.warning("Razorpay webhook signature verification failed.")
            raise HTTPException(status_code=400, detail="Invalid webhook signature.")

    try:
        data = json.loads(body_bytes.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Malformed JSON in webhook body.")

    event = data.get("event")
    logger.info(f"Received Razorpay webhook event: {event}")

    if event in ("order.paid", "payment.captured"):
        payload_entity = data.get("payload", {}).get("payment", {}).get("entity", {})
        email = (
            payload_entity.get("email")
            or payload_entity.get("notes", {}).get("email")
        )
        payment_id = payload_entity.get("id")

        if payment_id and payment_id in _processed_payments:
            logger.info(f"Webhook payment {payment_id} already processed (idempotent duplicate skip).")
            return JSONResponse(content={"status": "already_processed", "event": event})

        if email:
            clean_email = email.strip().lower()
            logger.info(f"Webhook confirming Pro upgrade for {clean_email} via payment={payment_id}")
            database.create_or_get_user(clean_email)
            database.update_subscription(clean_email, "pro", customer_id=payment_id)
            if payment_id:
                _processed_payments.add(payment_id)

    return JSONResponse(content={"status": "received", "event": event})


# ---------------------------------------------------------------------------
# 3.1 Payment Reconciliation Endpoint (Safety Net for Network Blips)
# ---------------------------------------------------------------------------
@router.post("/reconcile")
@router.post("/billing/reconcile")
@router.post("/payment/reconcile")
@limiter.limit("20/minute")
async def reconcile_payment(payload: ReconcilePaymentRequest, request: Request) -> JSONResponse:
    """
    Fallback reconciliation endpoint:
    If a network failure interrupted client-side verification,
    this queries Razorpay Orders/Payments API directly and unlocks Pro if payment was captured.
    """
    email = payload.email.strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=422, detail="Please provide a valid email address.")

    order_id = (payload.order_id or "").strip()
    payment_id = (payload.payment_id or "").strip()

    if not order_id and not payment_id:
        raise HTTPException(
            status_code=400,
            detail="Please provide at least one of 'order_id' or 'payment_id' to reconcile.",
        )

    rzp = get_razorpay_config()
    if not rzp["is_configured"]:
        database.create_or_get_user(email)
        database.update_subscription(email, "pro", customer_id=payment_id or order_id)
        pro_token = create_pro_token(email)
        resp = JSONResponse(
            content={
                "status": "reconciled",
                "is_pro": True,
                "simulated": True,
                "payment_id": payment_id,
                "order_id": order_id,
                "message": "Payment verified in simulation mode. Pro access unlocked!",
            }
        )
        resp.set_cookie("resumeroast_pro_token", pro_token, max_age=30*86400, httponly=True, samesite="lax")
        return resp

    # Reject simulation credentials when Razorpay is configured
    if (order_id and order_id.startswith("order_sim_")) or (payment_id and payment_id.startswith("pay_sim_")):
        raise HTTPException(
            status_code=400,
            detail="Simulation payment credentials cannot be reconciled when live/test Razorpay is active.",
        )

    try:
        import razorpay

        client = razorpay.Client(auth=(rzp["key_id"], rzp["key_secret"]))
        verified_payment = None

        if payment_id:
            try:
                payment = client.payment.fetch(payment_id)
                if payment.get("status") in ("captured", "authorized"):
                    verified_payment = payment
            except Exception as pe:
                logger.warning(f"Could not fetch payment {payment_id} from Razorpay: {pe}")

        if not verified_payment and order_id:
            try:
                payments = client.order.payments(order_id)
                items = payments.get("items", [])
                for p in items:
                    if p.get("status") in ("captured", "authorized"):
                        verified_payment = p
                        payment_id = p.get("id")
                        break
            except Exception as oe:
                logger.warning(f"Could not fetch order payments for {order_id}: {oe}")

        if verified_payment:
            database.create_or_get_user(email)
            database.update_subscription(email, "pro", customer_id=payment_id)
            if payment_id:
                _processed_payments.add(payment_id)
            logger.info(f"Reconciliation successfully upgraded {email} to Pro via {payment_id}.")
            pro_token = create_pro_token(email)
            resp = JSONResponse(
                content={
                    "status": "reconciled",
                    "is_pro": True,
                    "payment_id": payment_id,
                    "order_id": order_id,
                    "message": "Payment verified with Razorpay. Pro access is active!",
                }
            )
            resp.set_cookie("resumeroast_pro_token", pro_token, max_age=30*86400, httponly=True, samesite="lax")
            return resp
        else:
            raise HTTPException(
                status_code=400,
                detail="Payment not found or not yet captured by Razorpay. Please retry in a few moments or contact support.",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Reconciliation error for {email}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reconcile payment with Razorpay: {str(e)}",
        )



# ---------------------------------------------------------------------------
# 4. Backward-Compatible Stripe / Legacy Checkout Routes
# ---------------------------------------------------------------------------
@router.post("/checkout")
async def create_checkout_session(payload: CheckoutRequest) -> JSONResponse:
    """
    Legacy Stripe Checkout endpoint preserved for backward compatibility.
    """
    email = payload.email.strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=422, detail="Please enter a valid email address.")

    stripe_key = _clean_env("STRIPE_SECRET_KEY")
    frontend_url = _clean_env("FRONTEND_URL", "http://localhost:5173").rstrip("/")

    if not stripe_key:
        logger.info(f"STRIPE_SECRET_KEY not set. Granting simulated Pro access to {email}")
        database.create_or_get_user(email)
        database.update_subscription(email, "pro", "cus_test_mock")
        return JSONResponse(
            content={
                "url": f"{frontend_url}/roast?upgraded=true",
                "session_id": "simulated_session_mock",
                "status": "success",
                "message": "Pro subscription simulated successfully for testing.",
            }
        )

    stripe.api_key = stripe_key
    price_in_inr = PLAN_PRICES.get(payload.plan, 9900)
    plan_name = PLAN_NAMES.get(payload.plan, "Resume Roast Pro (Monthly)")

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            customer_email=email,
            line_items=[
                {
                    "price_data": {
                        "currency": "inr",
                        "product_data": {
                            "name": plan_name,
                            "description": "Full-line resume critique, bullet rewrites, and unlimited daily submissions.",
                        },
                        "unit_amount": price_in_inr,
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=f"{frontend_url}/roast?session_id={{CHECKOUT_SESSION_ID}}&status=success",
            cancel_url=f"{frontend_url}/pricing?status=cancelled",
        )
        return JSONResponse(content={"url": session.url, "session_id": session.id})
    except Exception as e:
        logger.exception(f"Stripe session creation failed for {email}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Unable to initialize payment checkout: {str(e)}",
        )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="Stripe-Signature"),
) -> JSONResponse:
    """Stripe Webhook handler."""
    stripe_webhook_secret = _clean_env("STRIPE_WEBHOOK_SECRET")

    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header.")

    payload = await request.body()

    if not stripe_webhook_secret:
        raise HTTPException(status_code=400, detail="Stripe webhook secret is not configured.")

    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, stripe_webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload.")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid Stripe signature.")

    event_type = event["type"]
    event_data = event["data"]["object"]

    if event_type in ("checkout.session.completed", "payment_intent.succeeded"):
        email = event_data.get("customer_email") or event_data.get("customer_details", {}).get("email")
        customer_id = event_data.get("customer")
        if email:
            clean_email = email.strip().lower()
            database.create_or_get_user(clean_email)
            database.update_subscription(clean_email, "pro", customer_id)

    return JSONResponse(content={"status": "received", "event": event_type})


# ---------------------------------------------------------------------------
# 5. Subscription Status & Cancellation
# ---------------------------------------------------------------------------
@router.post("/subscription/cancel")
@limiter.limit("5/minute")
async def cancel_subscription(payload: CancelRequest, request: Request) -> JSONResponse:
    """Cancel subscription for user email. Requires signed token ownership or admin authorization."""
    email = payload.email.strip().lower()
    auth_email = get_authenticated_pro_email(request)
    is_admin = verify_admin_access(request)

    if not is_admin and auth_email != email:
        logger.warning(f"Unauthorized cancellation attempt for {email} from IP {request.client.host if request.client else 'unknown'}")
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: A valid session token or admin authorization is required to cancel this subscription.",
        )

    database.update_subscription(email, "free")
    resp = JSONResponse(
        content={
            "status": "cancelled",
            "message": "Subscription cancelled. Access will revert to standard free tier.",
        }
    )
    resp.delete_cookie("resumeroast_pro_token")
    return resp


@router.get("/subscription/status")
@limiter.limit("20/minute")
async def check_subscription_status(email: str, request: Request) -> JSONResponse:
    """Check subscription status for given email. Rate-limited and requires authentication to prevent enumeration."""
    clean_email = email.strip().lower()
    status = database.get_user_subscription(clean_email)
    auth_email = get_authenticated_pro_email(request)
    is_admin = verify_admin_access(request)

    # Return full account record only to the verified owner or admin
    if auth_email == clean_email or is_admin:
        return JSONResponse(
            content={
                "email": clean_email,
                "subscription_status": status,
                "is_pro": status == "pro",
                "authenticated": True,
            }
        )

    # Third-party unauthenticated query returns generic false (eliminates customer enumeration)
    return JSONResponse(
        content={
            "is_pro": False,
            "authenticated": False,
        }
    )


class ManualUpgradeRequest(BaseModel):
    email: str
    plan: str = "monthly"
    utr: str
    notes: Optional[str] = None


@router.post("/payment/manual-request")
@limiter.limit("10/minute")
async def manual_payment_request(payload: ManualUpgradeRequest, request: Request) -> JSONResponse:
    """
    Early Adopter Manual UPI Transfer Stopgap.
    Allows users who transfer directly via personal UPI while Razorpay automated KYC
    is pending to log their transfer reference for validation.
    """
    clean_email = payload.email.strip().lower()
    clean_utr = payload.utr.strip()
    if not clean_email or "@" not in clean_email:
        raise HTTPException(status_code=400, detail="Invalid email address.")
    if len(clean_utr) < 6:
        raise HTTPException(status_code=400, detail="Please provide a valid UPI transaction reference (UTR).")

    database.create_or_get_user(clean_email)
    logger.info(f"Manual UPI upgrade requested for {clean_email}, UTR: {clean_utr}, Plan: {payload.plan}")

    return JSONResponse(
        content={
            "status": "pending_verification",
            "message": "Manual transfer reference recorded. Once verified, your account is upgraded to Pro.",
            "email": clean_email,
            "utr": clean_utr,
        }
    )
