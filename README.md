<div align="center">

<img src="https://img.shields.io/badge/version-1.0.0-6366f1?style=for-the-badge" />
<img src="https://img.shields.io/badge/license-MIT-a855f7?style=for-the-badge" />
<img src="https://img.shields.io/badge/PRs-welcome-22c55e?style=for-the-badge" />
<img src="https://img.shields.io/badge/status-active-22c55e?style=for-the-badge" />

<br/><br/>

```
 ██████╗ ██████╗ ██████╗  ██████╗ ██████╗ ████████╗██╗   ██╗███╗   ██╗██╗████████╗██╗   ██╗
██╔═══██╗██╔══██╗██╔══██╗██╔═══██╗██╔══██╗╚══██╔══╝██║   ██║████╗  ██║██║╚══██╔══╝╚██╗ ██╔╝
██║   ██║██████╔╝██████╔╝██║   ██║██████╔╝   ██║   ██║   ██║██╔██╗ ██║██║   ██║    ╚████╔╝
██║   ██║██╔═══╝ ██╔═══╝ ██║   ██║██╔══██╗   ██║   ██║   ██║██║╚██╗██║██║   ██║     ╚██╔╝
╚██████╔╝██║     ██║     ╚██████╔╝██║  ██║   ██║   ╚██████╔╝██║ ╚████║██║   ██║      ██║
 ╚═════╝ ╚═╝     ╚═╝      ╚═════╝ ╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚═╝  ╚═══╝╚═╝   ╚═╝      ╚═╝
```

# 🌐 OpporSphere

### 🚀 **AI-Powered Opportunity Discovery Platform for Students**

*Find hackathons, internships & competitions. Match with teammates. Get AI-guided recommendations — all in one place.*

<br/>

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16.3-000000?style=flat-square&logo=next.js&logoColor=white)](https://nextjs.org)
[![Supabase](https://img.shields.io/badge/Supabase-Database%20%26%20Auth-3ECF8E?style=flat-square&logo=supabase&logoColor=white)](https://supabase.com)
[![Gemini](https://img.shields.io/badge/Google%20Gemini-LLM-4285F4?style=flat-square&logo=google&logoColor=white)](https://ai.google.dev)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20AI-black?style=flat-square)](https://ollama.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://typescriptlang.org)

</div>

---

## 📖 Table of Contents

- [✨ Features](#-features)
- [🏗️ Architecture](#️-architecture)
- [🛠️ Tech Stack](#️-tech-stack)
- [⚡ Quick Start](#-quick-start)
  - [Prerequisites](#prerequisites)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Backend Setup (FastAPI)](#2-backend-setup-fastapi)
  - [3. Frontend Setup (Next.js)](#3-frontend-setup-nextjs)
  - [4. Supabase Setup](#4-supabase-setup)
  - [5. Run Both Servers](#5-run-both-servers)
- [🔑 Environment Variables](#-environment-variables)
- [🗄️ Database Migrations](#️-database-migrations)
- [🔐 Authentication](#-authentication)
- [🤖 AI & LLM Configuration](#-ai--llm-configuration)
- [👑 Admin Management](#-admin-management)
- [📚 API Documentation](#-api-documentation)
- [📁 Project Structure](#-project-structure)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

---

## ✨ Features

### 🔍 Smart Opportunity Discovery
- **Natural Language Search** — Type "ML hackathons in India this month" and get accurate results using spaCy NLP entity extraction
- **Semantic Vector Search** — pgvector cosine similarity search finds relevant opportunities even when keywords don't match exactly
- **Filters** — Domain, type, location, deadline, and eligibility filters

### 🎯 AI-Powered Matching
- **Profile-Based Recommendations** — Embeds your skills, interests, and career goals into 384-dim vectors and finds top-matching opportunities
- **Match Score** — Each recommendation comes with a "match relevance %" score
- **Cold-Start Handling** — Works even for new users with no interaction history

### 🤖 AI Copilot (RAG Chat)
- **Context-Grounded Responses** — Retrieves top-5 relevant opportunities from the DB before answering
- **Hallucination Guard** — If no relevant opportunities found, returns a safe fallback instead of making things up
- **Multi-turn Conversations** — Remembers last 3 turns of conversation per session
- **Source Citations** — Every answer links back to the actual opportunity IDs
- **Streaming** — Token-by-token streaming response (SSE)

### 👥 Team Finder
- **Compatibility Matching** — Finds students registered for the same event using embedding cosine similarity
- **Role Complementarity** — Rewards teams with diverse roles (e.g., Designer + Developer) over duplicate roles
- **Invite System** — Send AI-generated personalized team invitations
- **Team Management** — Create teams, accept/decline invites, manage members

### 🛡️ Trust Scanner
- **Duplicate Detection** — Catches near-duplicate opportunities using both vector similarity (>0.92) and fuzzy string matching (rapidfuzz)
- **Quality Scoring** — 0–100 trust score combining rule-based checks + ML classifier (scikit-learn LogisticRegression)
- **Flag Reports** — Detailed breakdown of why an opportunity scored low
- **Spam Detection** — Identifies suspicious patterns, missing fields, and spam keywords

### ✍️ AI Content Generation
- **Opportunity Summaries** — Generates clean 2–3 sentence summaries from raw text
- **Personalized Notifications** — AI-crafted messages for matched opportunities
- **Team Invite Messages** — Generates warm, personalized invitation messages
- **Student Bios** — Turns skill lists into professional profile bios

### 🔐 Authentication
- **Google OAuth** — Sign in with Google via Supabase Auth (one click, no password needed)
- **Email/Password** — Traditional registration and login as fallback
- **JWT Tokens** — Secure access + refresh token rotation
- **Row Level Security** — All Supabase tables protected by RLS policies

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Student / Admin Browser                      │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTPS
┌──────────────────────────▼──────────────────────────────────────┐
│               Next.js 16 Frontend  (localhost:3000)              │
│  Pages: Dashboard · Discovery · Opportunities · Team Finder      │
│  Auth: Supabase JS SDK (Google OAuth + Email/Password)           │
└──────────────────────────┬──────────────────────────────────────┘
                           │ REST API
┌──────────────────────────▼──────────────────────────────────────┐
│              FastAPI Backend  (localhost:8000)                    │
│                                                                   │
│  /api/v1/auth          → Auth (register, login, Google OAuth)    │
│  /api/v1/students      → Student profiles                        │
│  /api/v1/opportunities → Opportunity CRUD                        │
│  /api/v1/match         → AI recommendations + matching           │
│  /api/v1/discovery     → NLP smart search                        │
│  /api/v1/copilot       → RAG chat + streaming                    │
│  /api/v1/trust         → Trust scoring + duplicate detection     │
│  /api/v1/team-finder   → Team matching + invites                 │
│  /api/v1/content-gen   → AI content generation                   │
└──────┬──────────────────┬────────────────────┬───────────────────┘
       │                  │                    │
┌──────▼──────┐   ┌───────▼──────┐   ┌────────▼──────────────┐
│  Supabase   │   │ SentenceTf   │   │  LLM Provider         │
│  Postgres   │   │ all-MiniLM   │   │  ┌─────────────────┐  │
│  + pgvector │   │ L6-v2 (384d) │   │  │ Gemini (default)│  │
│  + Auth     │   │  (local,free)│   │  ├─────────────────┤  │
│  + RLS      │   └──────────────┘   │  │ Ollama (local)  │  │
└─────────────┘                      │  └─────────────────┘  │
                                     │  Switched live via DB  │
                                     └────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Next.js 16 + TypeScript | React framework with Turbopack |
| **Styling** | Tailwind CSS v4 | Utility-first CSS |
| **Backend** | FastAPI + Python 3.11+ | Async REST API |
| **Database** | Supabase (PostgreSQL) | Data storage + real-time |
| **Vector Search** | pgvector | Cosine similarity search |
| **Auth** | Supabase Auth | Google OAuth + JWT |
| **Embeddings** | SentenceTransformers | Local 384-dim vectors (free) |
| **LLM (default)** | Google Gemini | Text generation + chat |
| **LLM (optional)** | Ollama | Local self-hosted LLM |
| **NLP** | spaCy | Entity extraction for smart search |
| **ML** | scikit-learn | Trust scoring classifier |

---

## ⚡ Quick Start

### Prerequisites

Make sure you have these installed:

- **Python 3.11+** — [python.org](https://python.org)
- **Node.js 18+** — [nodejs.org](https://nodejs.org)
- **Git** — [git-scm.com](https://git-scm.com)
- **A Supabase account** — [supabase.com](https://supabase.com) (free tier works)
- **A Gemini API key** — [aistudio.google.com](https://aistudio.google.com/app/apikey) (free tier available)

---

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/HackNima.git
cd HackNima
```

---

### 2. Backend Setup (FastAPI)

```bash
cd opportunity-ecosystem-api

# Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt

# Copy the environment file
cp .env.example .env
```

Now open `.env` and fill in your values (see [Environment Variables](#-environment-variables) section below).

```bash
# Download the spaCy language model (required for smart search)
python -m spacy download en_core_web_sm
```

---

### 3. Frontend Setup (Next.js)

```bash
cd opportunity-ecosystem-web

# Install dependencies
npm install

# The .env.local file is already created — just fill in your Supabase keys
nano .env.local
```

---

### 4. Supabase Setup

#### Step 1 — Create a Supabase Project
1. Go to [supabase.com](https://supabase.com) → **New Project**
2. Choose a name, region, and database password
3. Wait ~2 minutes for provisioning

#### Step 2 — Run Database Migrations
Go to your Supabase project → **SQL Editor** and run each migration file **in order**:

| Order | File | What it creates |
|-------|------|-----------------|
| 1 | `migrations/V001__enable_extensions.sql` | pgvector, uuid-ossp, citext |
| 2 | `migrations/V002__students_and_opportunities.sql` | Core tables + enums |
| 3 | `migrations/V003__events.sql` | Events table |
| 4 | `migrations/V004__trust_scores.sql` | Trust score table |
| 5 | `migrations/V005__teams_and_members.sql` | Teams + members |
| 6 | `migrations/V006__applications.sql` | Applications table |
| 7 | `migrations/V007__vector_indexes.sql` | IVFFlat cosine indexes |
| 8 | `migrations/V008__rls_policies.sql` | Row Level Security |
| 9 | `migrations/V009__views_and_functions.sql` | RPCs for vector search |
| 10 | `migrations/V010__team_finder_invites.sql` | Team invite system |
| 11 | `migrations/V011__admins_and_settings.sql` | Admins table + app settings |

> **Optional dev seed data:** Run `migrations/seed.sql` to populate sample opportunities.

#### Step 3 — Get Your API Keys
Go to **Settings → API** in your Supabase dashboard:

| Key | Location |
|-----|----------|
| Project URL | Settings → API → Project URL |
| anon key | Settings → API → Project API keys → `anon` |
| service_role key | Settings → API → Project API keys → `service_role` |
| JWT Secret | Settings → API → JWT Settings → JWT Secret |

#### Step 4 — Enable Google OAuth *(for Google Sign-In)*
1. Go to [Google Cloud Console](https://console.cloud.google.com) → **APIs & Services → Credentials**
2. Create an **OAuth 2.0 Client ID** (Web application)
3. Add Authorized redirect URI: `https://YOUR_PROJECT_REF.supabase.co/auth/v1/callback`
4. In Supabase: **Authentication → Providers → Google** → paste Client ID + Secret

---

### 5. Run Both Servers

**Terminal 1 — Backend:**
```bash
cd opportunity-ecosystem-api
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd opportunity-ecosystem-web
npm run dev
```

| Service | URL |
|---------|-----|
| 🌐 Frontend | http://localhost:3000 |
| ⚙️ Backend API | http://localhost:8000 |
| 📖 API Docs (Swagger) | http://localhost:8000/docs |
| 📘 API Docs (ReDoc) | http://localhost:8000/redoc |
| 💚 Health Check | http://localhost:8000/health |

---

## 🔑 Environment Variables

### Backend — `opportunity-ecosystem-api/.env`

```env
# ── App ─────────────────────────────────────────
APP_NAME="OpporSphere API"
APP_ENV=development
DEBUG=true
SECRET_KEY=your-random-secret-key-here

# ── CORS ────────────────────────────────────────
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# ── Supabase ────────────────────────────────────
SUPABASE_URL=https://xxxxxxxxxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIs...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIs...
SUPABASE_JWT_SECRET=your-jwt-secret

# ── Gemini (Default LLM) ────────────────────────
# Get free key: https://aistudio.google.com/app/apikey
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.0-flash

# ── Ollama (Optional Local LLM) ─────────────────
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b

# ── LLM Provider (default, overridable via DB) ──
# Values: "gemini" | "ollama"
LLM_PROVIDER=gemini

# ── JWT ─────────────────────────────────────────
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30
```

### Frontend — `opportunity-ecosystem-web/.env.local`

```env
NEXT_PUBLIC_SUPABASE_URL=https://xxxxxxxxxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIs...
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🗄️ Database Migrations

The `migrations/` folder contains numbered SQL files that must be run **in order**. See the full guide in [`migrations/README.md`](opportunity-ecosystem-api/migrations/README.md).

```bash
# Quick reference — run in Supabase SQL Editor, in this order:
V001 → V002 → V003 → V004 → V005 → V006 → V007 → V008 → V009 → V010 → V011
```

After all migrations, optionally seed sample data:
```sql
-- In Supabase SQL Editor:
-- Paste contents of: migrations/seed.sql
```

---

## 🔐 Authentication

This platform supports two sign-in methods:

### Google OAuth (Recommended)
```
1. User clicks "Sign in with Google"
2. Frontend calls: GET /api/v1/auth/google
3. Backend returns Google OAuth URL from Supabase
4. User is redirected → signs in with Google
5. Supabase handles callback → tokens returned to frontend
6. Frontend sends tokens to: POST /api/v1/auth/google/session
7. Backend returns app-level JWT tokens
```

### Email / Password
```
POST /api/v1/auth/register   → register new user
POST /api/v1/auth/login      → login and get tokens
POST /api/v1/auth/refresh    → refresh expired access token
GET  /api/v1/auth/me         → get current user profile
```

---

## 🤖 AI & LLM Configuration

### Gemini (Default — Cloud)
- Powers: Copilot chat, content generation, AI summaries
- Free tier available at [aistudio.google.com](https://aistudio.google.com/app/apikey)
- Models: `gemini-2.0-flash` (fast), `gemini-1.5-pro` (powerful)

### Ollama (Optional — Fully Local & Private)
- Run AI completely offline with no API costs
- Install: [ollama.com](https://ollama.com)
- Pull a model: `ollama pull llama3.2:3b`
- Start server: `ollama serve`

### Switching LLM Provider (Live, No Restart!)
Admins can switch the LLM provider live from Supabase without restarting the server:

```sql
-- In Supabase SQL Editor or Table Editor:

-- Switch to Ollama (local, free, private)
UPDATE app_settings 
SET value = 'ollama', updated_by = 'admin@example.com' 
WHERE key = 'LLM_PROVIDER';

-- Switch back to Gemini
UPDATE app_settings 
SET value = 'gemini', updated_by = 'admin@example.com' 
WHERE key = 'LLM_PROVIDER';

-- Change Ollama model
UPDATE app_settings 
SET value = 'mistral:7b', updated_by = 'admin@example.com' 
WHERE key = 'OLLAMA_MODEL';
```

### Embeddings (Always Local — Free)
- **Model:** `all-MiniLM-L6-v2` (SentenceTransformers)
- **Dimensions:** 384-dim vectors
- **Cost:** $0 — runs locally, downloaded once automatically
- Used for: student-opportunity matching, semantic search, team finder

---

## 👑 Admin Management

Admins are stored in the **`admins` Supabase table** — not in environment variables. This means you can add/remove admins without restarting the server.

### Adding an Admin
In Supabase → **Table Editor → admins** → **Insert row**:

```sql
INSERT INTO admins (email, role, added_by)
VALUES ('admin@example.com', 'admin', 'super_admin@example.com');
```

### Admin Roles

| Role | Permissions |
|------|-------------|
| `admin` | Create/update opportunities, manage content |
| `super_admin` | All admin permissions + manage other admins |

### Disabling an Admin
```sql
UPDATE admins SET is_active = false WHERE email = 'admin@example.com';
```

---

## 📚 API Documentation

The full interactive API documentation is available at runtime:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Key Endpoints at a Glance

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Liveness probe |
| `POST` | `/api/v1/auth/register` | Register with email/password |
| `POST` | `/api/v1/auth/login` | Login with email/password |
| `GET` | `/api/v1/auth/google` | Get Google OAuth URL |
| `POST` | `/api/v1/auth/google/session` | Exchange OAuth tokens |
| `GET` | `/api/v1/students/me` | Get own student profile |
| `PATCH` | `/api/v1/students/me` | Update own profile |
| `GET` | `/api/v1/opportunities` | List opportunities (with filters) |
| `POST` | `/api/v1/opportunities` | Create opportunity *(admin only)* |
| `GET` | `/api/v1/match/recommendations` | Get AI-matched opportunities |
| `POST` | `/api/v1/match/` | Match profile to opportunities |
| `POST` | `/api/v1/discovery/` | Smart NLP search |
| `POST` | `/api/v1/copilot/chat` | Chat with AI copilot (RAG) |
| `POST` | `/api/v1/copilot/stream` | Streaming copilot chat (SSE) |
| `GET` | `/api/v1/trust/{user_id}` | Get trust score |
| `POST` | `/api/v1/trust/endorse` | Endorse a user |
| `POST` | `/api/v1/team-finder/` | Find team matches |
| `POST` | `/api/v1/content-gen/` | Generate AI content |

---

## 📁 Project Structure

```
HackNima/
├── opportunity-ecosystem-api/          # FastAPI Backend
│   ├── app/
│   │   ├── api/                        # Route handlers
│   │   │   ├── auth.py                 # Auth + Google OAuth
│   │   │   ├── copilot.py              # AI chat routes
│   │   │   ├── discovery.py            # Smart search routes
│   │   │   ├── match.py                # Matching routes
│   │   │   ├── opportunities.py        # Opportunity CRUD
│   │   │   ├── students.py             # Student profiles
│   │   │   ├── team_finder.py          # Team matching
│   │   │   ├── trust.py                # Trust scoring
│   │   │   ├── content_gen.py          # AI content gen
│   │   │   └── deps.py                 # Auth dependencies
│   │   ├── core/
│   │   │   ├── config.py               # Settings (pydantic-settings)
│   │   │   └── supabase_client.py      # Supabase client factory
│   │   ├── ml/
│   │   │   ├── embeddings.py           # SentenceTransformer embedder
│   │   │   └── llm_client.py           # Gemini + Ollama unified client
│   │   ├── models/                     # Pydantic schemas
│   │   ├── services/                   # Business logic
│   │   └── main.py                     # FastAPI app factory
│   ├── migrations/                     # SQL migration files (V001–V011)
│   ├── tests/                          # Test suite
│   ├── .env.example                    # Environment template
│   ├── requirements.txt                # Python dependencies
│   └── seed.py                         # Data seeding script
│
└── opportunity-ecosystem-web/          # Next.js Frontend
    ├── src/
    │   ├── app/
    │   │   ├── page.tsx                # Landing page
    │   │   ├── dashboard/              # Student dashboard
    │   │   ├── discovery/              # Smart search page
    │   │   ├── opportunities/          # Opportunity listings
    │   │   ├── team-finder/            # Team matching page
    │   │   ├── profile/                # Student profile
    │   │   ├── login/                  # Login page
    │   │   └── signup/                 # Registration page
    │   ├── components/                 # Reusable UI components
    │   ├── context/                    # React context (Auth)
    │   └── lib/                        # API client, utilities
    ├── .env.local                      # Frontend environment
    └── package.json                    # Node.js dependencies
```

---

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/your-feature-name`
3. **Make** your changes and commit: `git commit -m "feat: add your feature"`
4. **Push** to your fork: `git push origin feature/your-feature-name`
5. **Open** a Pull Request

### Development Tips

```bash
# Run backend tests
cd opportunity-ecosystem-api
pytest tests/ -v

# Run frontend tests
cd opportunity-ecosystem-web
npm test

# Lint frontend
npm run lint
```

### Commit Convention
We use [Conventional Commits](https://conventionalcommits.org):
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `refactor:` Code refactoring
- `test:` Adding tests

---

## 🙋 FAQ

**Q: Do I need an OpenAI API key?**
> No! We use Google Gemini (free tier available) for text generation and a local SentenceTransformer model (no API key, runs offline) for embeddings.

**Q: Can I run the AI completely offline / locally?**
> Yes! Set `LLM_PROVIDER=ollama` in Supabase `app_settings` and install [Ollama](https://ollama.com). Pull any model like `llama3.2:3b` or `mistral:7b`.

**Q: How do I add myself as an admin?**
> After running the migrations, insert your email into the `admins` table in Supabase: `INSERT INTO admins (email, role) VALUES ('your@email.com', 'admin');`

**Q: The AI model download takes a long time on first start — is that normal?**
> Yes! The `all-MiniLM-L6-v2` model (~80MB) is downloaded once from HuggingFace on first startup and then cached locally. Subsequent starts are instant.

**Q: Can I use a different Gemini model?**
> Yes! Update `GEMINI_MODEL` in your `.env` file or in the Supabase `app_settings` table. Available models: `gemini-2.0-flash`, `gemini-1.5-pro`, `gemini-1.5-flash`.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built with ❤️ for students, by students**

*If this project helped you, please consider giving it a ⭐ on GitHub!*

[![GitHub Stars](https://img.shields.io/github/stars/YOUR_USERNAME/HackNima?style=social)](https://github.com/YOUR_USERNAME/HackNima)

</div>
