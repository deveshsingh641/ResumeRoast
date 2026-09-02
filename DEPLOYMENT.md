# 🚀 Resume Roast — Production Deployment Guide

This guide covers the best, tested ways to deploy **Resume Roast** to production.

---

## 🏗️ Architecture Overview

| Component | Technology | Recommended Host | Free Tier Available? |
| :--- | :--- | :--- | :--- |
| **Frontend** | React 19 + Vite + Tailwind CSS | [Vercel](https://vercel.com) or [Netlify](https://netlify.com) | ✅ Yes |
| **Backend** | FastAPI + Python 3.11 + Uvicorn | [Render](https://render.com) or [Railway](https://railway.app) | ✅ Yes |
| **Database** | PostgreSQL (Schema auto-initialized) | [Supabase](https://supabase.com) or [Neon](https://neon.tech) | ✅ Yes (Optional; in-memory fallback enabled) |
| **AI Provider** | Google Gemini 1.5 Flash | [Google AI Studio](https://aistudio.google.com) | ✅ Yes (Free tier) |

---

## 🌟 Method 1: Split Cloud Deployment (Recommended)

This is the standard, modern setup: deploy the backend on **Render** (or Railway) and the frontend on **Vercel** (or Netlify).

### Step 1: Deploy Backend on Render

1. Push this repository to **GitHub**.
2. Go to [Render Dashboard](https://dashboard.render.com/) and click **New + > Web Service**.
3. Connect your GitHub repository.
4. Configure the service settings:
   - **Name**: `resumeroast-api`
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Region**: Closest to your users (e.g. Frankfurt, Oregon, Singapore)
   - **Branch**: `main` (or your default branch)
   - **Build Command**:
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command**:
     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```
5. Add **Environment Variables** under the "Environment" tab:
   | Variable | Value | Description |
   | :--- | :--- | :--- |
   | `GEMINI_API_KEY` | `AIzaSy...` | Your Gemini API Key from [Google AI Studio](https://aistudio.google.com) |
   | `ENVIRONMENT` | `production` | Enables production mode and disables Swagger docs |
   | `DATABASE_URL` | *(Optional)* | Your PostgreSQL connection string (from Supabase/Neon). If omitted, runs in memory. |
   | `FRONTEND_URL` | `https://your-frontend.vercel.app` | We will set this in Step 2 |
   | `FREE_TIER_DAILY_LIMIT` | `1` | Free roasts allowed per IP/fingerprint per day |

6. Click **Deploy Web Service**.
7. Once deployed, copy your backend service URL (e.g. `https://resumeroast-api.onrender.com`). Verify it by visiting `https://resumeroast-api.onrender.com/health` (should return `{"status":"ok"}`).

---

### Step 2: Deploy Frontend on Vercel

1. Go to [Vercel Dashboard](https://vercel.com/) and click **Add New... > Project**.
2. Import your GitHub repository.
3. Configure the project settings:
   - **Framework Preset**: `Vite`
   - **Root Directory**: Click `Edit` and choose `frontend`
   - **Build Command**: `npm run build` (default)
   - **Output Directory**: `dist` (default)
4. Add Environment Variable:
   | Name | Value |
   | :--- | :--- |
   | `VITE_API_URL` | `https://resumeroast-api.onrender.com` *(your Render backend URL from Step 1, without trailing slash)* |

5. Click **Deploy**.
6. Once Vercel finishes deploying, copy your production frontend URL (e.g. `https://resumeroast.vercel.app`).
7. *(Final Step)*: Go back to your **Render Web Service > Environment** and set:
   ```env
   FRONTEND_URL=https://resumeroast.vercel.app
   ```
   This ensures CORS requests from your frontend domain are accepted cleanly.

> **Note**: Both `frontend/vercel.json` and `frontend/public/_redirects` are already committed. This ensures Single Page App (SPA) routes like `/battle` or `/roast/:id` never 404 on refresh!

---

## 🐳 Method 2: Single-Server / Docker Deployment

If you want to host both frontend and backend on a single VPS (DigitalOcean, Hetzner, AWS EC2, Linode) or platforms like **Railway** / **Coolify**:

The repository includes a ready-to-go `docker-compose.yml`:

```bash
# 1. Create .env file in the root
cp backend/.env.example .env

# Edit .env with your GEMINI_API_KEY and FRONTEND_URL
nano .env

# 2. Build and run both services in background
docker compose up -d --build
```

- **Frontend with Nginx Reverse Proxy**: Accessible at `http://YOUR_SERVER_IP:3000` (or port 80).
- **Backend API**: Accessible internally at `http://backend:8000` and proxied automatically at `/api/` by Nginx.
- Nginx automatically handles SPA route refreshing and forwards `/api/*` to FastAPI with up to 10MB file upload support for resume attachments.

---

## 🗄️ Setting Up a Production Database (Optional)

By default, Resume Roast works with zero configuration using in-memory storage (great for immediate testing). For persistent storage across restarts:

1. Create a free project on [Supabase](https://supabase.com) or [Neon](https://neon.tech).
2. Get the connection string:
   ```env
   DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@[HOST]:5432/postgres
   ```
3. Add `DATABASE_URL` to your backend environment variables.
4. The database schema (tables for `roasts`, `battles`, `wall_entries`, `usage_counters`) will automatically be created on first launch by `app.main:on_startup`.

---

## 💳 Enabling Stripe Checkout (Optional)

To enable paid subscription unlocks for unlimited roasts:

1. Create a Stripe account at [stripe.com](https://stripe.com).
2. Create two recurring products/prices in Stripe:
   - Monthly Pass ($4.99/mo)
   - Annual Pass ($29/yr)
3. Set the following environment variables in your backend:
   ```env
   STRIPE_SECRET_KEY=sk_live_...
   STRIPE_WEBHOOK_SECRET=whsec_...
   STRIPE_MONTHLY_PRICE_ID=price_...
   STRIPE_ANNUAL_PRICE_ID=price_...
   ```
4. Point your Stripe Webhook endpoint to:
   `https://resumeroast-api.onrender.com/api/webhook/stripe`

---

## 🔍 Pre-Flight Checklist

Before opening to public traffic:
- [ ] `GEMINI_API_KEY` is configured and active.
- [ ] `FRONTEND_URL` on the backend matches the deployed frontend URL.
- [ ] `VITE_API_URL` on the frontend points to the deployed backend URL.
- [ ] Test a resume upload (.pdf / .docx) and verify roast generation.
- [ ] Test playing/generating a WhatsApp voice note.
- [ ] Test the Roast Battle comparison.
- [ ] Test the Wall of Flame / Wall of Fame page.
