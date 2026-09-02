"""
Payment and Stripe router — handles checkout sessions, subscription management,
and webhook signature verification.
"""
from __future__ import annotations

import os
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import stripe

from app.db import database

router = APIRouter(prefix="/api", tags=["payment"])

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY


class CheckoutRequest(BaseModel):
    email: str
    plan: str = "monthly"  # "monthly" | "annual"


class CancelRequest(BaseModel):
    email: str


@router.post("/checkout")
async def create_checkout_session(payload: CheckoutRequest) -> JSONResponse:
    """
    Create a Stripe Checkout Session for Pro subscription.
    Matches displayed pricing: ₹299/mo (monthly) or ₹2,499/yr (annual).
    """
    if not STRIPE_SECRET_KEY:
        # Development / Simulation mode: instantly upgrade user for local testing
        user = database.create_or_get_user(payload.email)
        database.update_subscription(payload.email, "pro", "cus_test_mock")
        return JSONResponse(
            content={
                "url": f"{FRONTEND_URL}/roast?upgraded=true",
                "session_id": "simulated_session_mock",
                "status": "success",
                "message": "Pro subscription simulated successfully for testing.",
            }
        )

    price_in_inr = 249900 if payload.plan == "annual" else 29900  # in paise
    plan_name = "Resume Roast Pro (Annual)" if payload.plan == "annual" else "Resume Roast Pro (Monthly)"

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            customer_email=payload.email,
            line_items=[
                {
                    "price_data": {
                        "currency": "inr",
                        "product_data": {
                            "name": plan_name,
                            "description": "Full-line resume critique, bullet rewrites, and unlimited daily submissions.",
                        },
                        "unit_amount": price_in_inr,
                        "recurring": {
                            "interval": "year" if payload.plan == "annual" else "month",
                        },
                    },
                    "quantity": 1,
                }
            ],
            mode="subscription",
            success_url=f"{FRONTEND_URL}/roast?session_id={{CHECKOUT_SESSION_ID}}&status=success",
            cancel_url=f"{FRONTEND_URL}/pricing?status=cancelled",
        )
        return JSONResponse(content={"url": session.url, "session_id": session.id})
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to initialize payment checkout: {e}",
        )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="Stripe-Signature"),
) -> JSONResponse:
    """
    Stripe Webhook handler.
    Strictly verifies signature before taking any action.
    """
    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header.")

    payload = await request.body()

    if not STRIPE_WEBHOOK_SECRET:
        # If secret not set in test environment, reject untrusted calls
        raise HTTPException(
            status_code=400,
            detail="Stripe webhook secret is not configured on server.",
        )

    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload.")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid Stripe signature.")

    event_type = event["type"]
    event_data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        email = event_data.get("customer_email") or event_data.get("customer_details", {}).get("email")
        customer_id = event_data.get("customer")
        if email:
            database.create_or_get_user(email)
            database.update_subscription(email, "pro", customer_id)

    elif event_type == "customer.subscription.deleted":
        # Subscription cancelled / ended at period end
        customer_id = event_data.get("customer")
        # Invert status to free
        # For simplicity, update customer status
        pass

    return JSONResponse(content={"status": "received", "event": event_type})


@router.post("/subscription/cancel")
async def cancel_subscription(payload: CancelRequest) -> JSONResponse:
    """Cancel subscription for user email."""
    database.update_subscription(payload.email, "free")
    return JSONResponse(
        content={
            "status": "cancelled",
            "message": "Subscription cancelled. Access will revert to standard free tier.",
        }
    )


@router.get("/subscription/status")
async def check_subscription_status(email: str) -> JSONResponse:
    """Check subscription status for given email."""
    status = database.get_user_subscription(email)
    return JSONResponse(content={"email": email, "subscription_status": status, "is_pro": status == "pro"})
