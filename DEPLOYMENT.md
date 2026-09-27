# RecallAI — Production Deployment Guide

This guide details the minimal, production-ready deployment instructions for RecallAI.

---

## 1. Required Environment Variables

Copy `.env.example` to `.env` and configure credentials:

```bash
# Core LLM Engines (At least one key required for AI processing)
GEMINI_API_KEY=your_gemini_api_key_here
MISTRAL_API_KEY=your_mistral_api_key_here
LLM_PROVIDER=auto

# Embeddings & Vector Storage
EMBEDDING_PROVIDER=local

# Server Host & Production CORS
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=https://app.yourdomain.com,http://localhost:3000

# Optional Phase 6: Real-time Voice (LiveKit)
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_livekit_api_key_here
LIVEKIT_API_SECRET=your_livekit_api_secret_here

# Optional STT/TTS overrides
DEEPGRAM_API_KEY=your_deepgram_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

### Frontend Environment Variables (`frontend/.env.local` or container build ARG):

```bash
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

---

## 2. Docker Deployment (Recommended)

### Using Docker Compose

Run the full stack with backend, frontend, and persistent storage:

```bash
# 1. Start backend and frontend
docker compose up -d

# 2. View logs
docker compose logs -f

# 3. Include the optional LiveKit voice agent worker
docker compose --profile voice up -d
```

Services exposed:
- **Frontend**: `http://localhost:3000`
- **Backend API**: `http://localhost:8000` (docs: `/docs`, health: `/api/v1/health`)

---

## 3. Standalone Manual Deployment

### Backend (FastAPI)

Prerequisites: Python 3.11+, FFmpeg installed on system.

```bash
# 1. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run production server with Uvicorn
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 2
```

### Frontend (Next.js)

Prerequisites: Node.js 20+

```bash
cd frontend

# 1. Install dependencies
npm ci

# 2. Build production assets with your production API URL
NEXT_PUBLIC_API_URL=https://api.yourdomain.com npm run build

# 3. Start standalone production server
npm start  # or: node .next/standalone/server.js
```

### LiveKit Voice Worker (Phase 6)

```bash
# Ensure LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET are set in .env
python voice_agent.py start
```

---

## 4. Health Checks & Verification

- **System Diagnostics**: `GET /api/v1/health`  
  Returns component status (LLM, embeddings, ChromaDB, FFmpeg, LiveKit) without exposing secrets.
- **Root Info**: `GET /`  
  Returns API status and version string.
- **Frontend Health**: Checks backend health live on `/settings` page.
