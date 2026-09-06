# Resume Roast 🔥

<div align="center">

![GitHub repo size](https://img.shields.io/github/repo-size/deveshsingh641/ResumeRoast?style=for-the-badge&color=orange)
![GitHub stars](https://img.shields.io/github/stars/deveshsingh641/ResumeRoast?style=for-the-badge&color=yellow)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![React 19](https://img.shields.io/badge/React_19-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)
![Google Gemini](https://img.shields.io/badge/Google_Gemini-4285F4?style=for-the-badge&logo=google&logoColor=white)

**Brutally honest AI-powered resume critiques with WhatsApp-style audio voice notes, head-to-head roast battles, and a community wall of shame.**

[Features](#-key-features) • [Quick Start](#-quick-start) • [Tech Stack](#-tech-stack) • [Environment Variables](#-environment-variables) • [API Reference](#-api-endpoints) • [Deployment](#-deployment)

</div>

---

## 💡 About Resume Roast

Job hunting is exhausting, generic resume advice is boring, and sugarcoated feedback doesn't get you hired.

**Resume Roast** analyzes PDF/DOCX resumes through Google Gemini AI to tear apart fluff, buzzwords, cringe formatting, and ATS red flags. It delivers savage yet actionable feedback, audio roasts formatted like WhatsApp voice notes, social share cards, head-to-head resume battles, and a public community wall.

---

## ✨ Key Features

- 🔥 **Brutally Honest AI Roasts:** In-depth critique broken down by overall score, hilarious savage summaries, red flag callouts, and actionable fixes.
- 🎙️ **WhatsApp-Style Voice Notes:** Listen to a simulated voice critique complete with audio waveforms, playback controls, and realistic recruiter/reviewer delivery.
- ⚔️ **Head-to-Head Roast Battles:** Pit two resumes against each other to see who gets hired and who gets sent to the circular filing cabinet.
- 🧱 **Wall of Shame & Fame:** Community leaderboard featuring the funniest, most roasted resumes submitted by brave applicants.
- 🎯 **Job Description Match Mode:** Match a resume against a specific target role/JD to get ATS keyword coverage, gap analysis, and tailored critique.
- 📸 **Social Share Card Generator:** Instant, downloadable high-res image cards (via `html2canvas`) custom-tailored for sharing on LinkedIn, X (Twitter), and Instagram.
- 📜 **Downloadable PDF Certificate:** Branded, verifiable Roast Certificate PDF generated server-side for sharing accomplishments or roasting milestones.
- 🌐 **7-Language Internationalization (i18n):** Native multilingual support for English, Hinglish, Spanish, French, German, Japanese, and Hindi.
- 🛡️ **Privacy & Self-Destruct:** Anonymous submissions automatically expire and get scrubbed after 7 days; sensitive personal identifiable data (PII) is handled securely.
- ⚡ **Rate Limiting & Tiered Access:** Built-in per-IP rate limiting (SlowAPI) with Razorpay integration for single roast passes (₹99) and Pro waitlist onboarding.

---

## 🛠️ Tech Stack

### Frontend
- **Framework:** React 19 + TypeScript + Vite 8
- **Styling:** Tailwind CSS + Custom Animations & Glassmorphic / Paper Mockup UI
- **State Management:** Zustand
- **Routing:** React Router DOM v7
- **Internationalization:** i18next + react-i18next
- **Exports:** HTML2Canvas for dynamic social card generation
- **HTTP Client:** Axios

### Backend
- **Framework:** FastAPI (Python 3.10+)
- **Server:** Uvicorn (ASGI)
- **AI Core:** Google Gemini Free / Pro API
- **Document Processing:** PyPDF2 / pdfminer.six / python-docx / ReportLab
- **Audio / Voice:** Edge TTS / gTTS integration with cached audio storage
- **Rate Limiting:** SlowAPI (Token bucket / IP-based)
- **Database:** SQLite (default for local dev) or PostgreSQL / Supabase
- **Payments:** Razorpay API (with test sandbox mode & VIP waitlist for Pro)

---

## 🚀 Quick Start

### Prerequisites
- [Node.js](https://nodejs.org/) (v18+)
- [Python](https://www.python.org/) (v3.10+)
- [Git](https://git-scm.com/)

### 1. Clone the Repository
```bash
git clone https://github.com/deveshsingh641/ResumeRoast.git
cd ResumeRoast
```

### 2. Configure Environment Variables
Copy the sample environment file in `backend/`:
```bash
cp backend/.env.example backend/.env
```
Edit `backend/.env` and add your **Google Gemini API Key** (get one free at [Google AI Studio](https://aistudio.google.com/)):
```ini
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

### 3. Install Dependencies

**Root & Frontend:**
```bash
npm install
cd frontend && npm install && cd ..
```

**Backend:**
```bash
pip install -r backend/requirements.txt
```

---

## 🏃‍♂️ Running Frontend & Backend Together

You can start both the frontend and backend with a single command:

### Option 1: Unified Terminal (Recommended)
```bash
npm run dev
# or
npm start
```
*Spawns both backend (`:8000`) and frontend (`:5173`) in one terminal window with color-coded logs via `concurrently`.*

- **Frontend:** [http://localhost:5173](http://localhost:5173)
- **Backend API:** [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **API Health:** [http://localhost:8000/health](http://localhost:8000/health)

### Option 2: Windows Launcher Scripts
- **Command Prompt:** Run or double-click `start.bat`
- **PowerShell:** Run `.\start.ps1`

### Option 3: Docker Compose
```bash
docker compose up --build
```
- Frontend mapped to port `3000`
- Backend mapped to port `8000`

---

## ⚙️ Environment Variables

Configuration settings in `backend/.env`:

| Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | **Required.** Google Gemini API key | `AIzaSy...` |
| `ENVIRONMENT` | Environment mode (`development` or `production`) | `development` |
| `FRONTEND_URL` | Allowed CORS origins (comma-separated) | `http://localhost:5173` |
| `DATABASE_URL` | DB connection string (leave blank for SQLite) | `sqlite:///./resumeroast.db` |
| `FREE_TIER_DAILY_LIMIT` | Max free roasts per IP per day | `1` |
| `ANONYMOUS_ROAST_EXPIRY_DAYS`| Retention days for anonymous roasts | `7` |
| `RAZORPAY_KEY_ID` | Razorpay Key ID (test or live) | `rzp_test_...` |
| `RAZORPAY_KEY_SECRET` | Razorpay Key Secret | `your_secret_here` |
| `ENABLE_PAYMENTS` | Master toggle to enable Razorpay order processing | `false` *(set `true` when ready)* |

---

## 🌐 API Endpoints

FastAPI provides automated interactive OpenAPI documentation at `/docs`:

- `GET /health` — Health check status and environment validation
- `POST /api/roast` — Upload resume (PDF/DOCX) and generate roast critique
- `GET /api/roast/{id}` — Fetch roasted resume report by ID
- `POST /api/match` — Upload resume + job description for tailored match scoring
- `GET /api/voice/{id}` — Retrieve or stream WhatsApp voice note audio
- `GET /api/certificate/{id}` — Download verifiable Roast Certificate PDF
- `POST /api/battle` — Submit two resumes for a head-to-head battle
- `GET /api/battle/{id}` — Get battle results and commentary
- `GET /api/wall` — Retrieve community roast leaderboard / Wall of Shame
- `GET /api/usage` — Check IP quota and daily usage limits
- `POST /api/create-order` — Initialize Razorpay order (₹99 roast / ₹799 bundle)
- `POST /api/verify-payment` — Cryptographically verify Razorpay payment signature
- `POST /api/waitlist/join` — Join Pro Launching Soon VIP waitlist with early bird perk

---

## 🚢 Deployment

Detailed production deployment instructions are documented in [DEPLOYMENT.md](DEPLOYMENT.md):

- **Backend:** Ready for deployment on [Render](https://render.com) using the included `backend/Dockerfile` or native Python runtime with `Procfile`.
- **Frontend:** Instant one-click deployment on [Vercel](https://vercel.com) with root directory set to `frontend` and output directory `dist`.
- **Docker:** Production container configs included in `docker-compose.yml`.

---

## 🔒 Privacy & Data Policy

- Resumes submitted anonymously are never sold or shared with third parties.
- Uploaded files and generated feedback are automatically purged according to retention settings (`ANONYMOUS_ROAST_EXPIRY_DAYS=7`).
- Voice note audio files are cached temporarily for streaming and cleaned periodically.

---

## 📄 License

This project is licensed under the MIT License — feel free to modify and build upon it!

---

<div align="center">
Made with 🔥 and brutal honesty.
</div>