# V-IMS AI Prototype — Local Installation & Setup Guide

This guide provides step-by-step instructions for installing, configuring, running, and troubleshooting the V-IMS AI prototype on a local workstation (macOS / Linux / Windows).

---

## 1. System Prerequisites

- **Python**: Version 3.9 or higher (`python3 --version`).
- **Node.js**: Version 18 or higher (`node --version`).
- **npm**: Version 9 or higher (`npm --version`).
- **Git**: For repository access.

---

## 2. Step-by-Step Installation

### Step 1: Clone Repository & Navigate to Workspace
```bash
git clone <repository_url> vims-ai-demo
cd vims-ai-demo
```

### Step 2: Backend Virtual Environment Setup
```bash
cd backend

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows PowerShell:
# .venv\Scripts\Activate.ps1

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Copy `.env.example` to `.env` inside `backend/`:
```bash
cp .env.example .env
```
*(Optionally adjust `JWT_SECRET` in `.env` if desired for local testing).*

### Step 4: Frontend Installation
```bash
cd ../frontend

# Install Node dependencies
npm install
```

---

## 3. Database Verification & Reset

Before launching the servers, verify database integrity:

```bash
# 1. Verify database tables and foreign keys
python3 scripts/verify_database.py

# 2. Run read-only final validation check
python3 scripts/final_validate.py

# 3. (Optional) Reset database to clean initial seed state:
python3 scripts/reset_demo_state.py --confirm
```

---

## 4. Running the Application Servers

You will need **two open terminal windows** to run the local development servers simultaneously:

### Terminal 1: Start Backend Server (FastAPI)
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```
- API Base URL: `http://localhost:8000/`
- Interactive OpenAPI Docs: `http://localhost:8000/docs`

### Terminal 2: Start Frontend Dev Server (Vite + React)
```bash
cd frontend
npm run dev
```
- App UI URL: `http://localhost:5173/`

---

## 5. Troubleshooting & Port Conflicts

| Problem | Cause | Resolution |
|---|---|---|
| `Port 8000 in use` | Another process is using port 8000 | Kill process: `lsof -i :8000 \| awk 'NR>1 {print $2}' \| xargs kill -9` |
| `Port 5173 in use` | Another Vite dev server is running | Kill process: `lsof -i :5173 \| awk 'NR>1 {print $2}' \| xargs kill -9` |
| `ModuleNotFoundError: No module named 'app'` | Python virtual environment not activated | Run `source .venv/bin/activate` or set `PYTHONPATH=.` |
| `HTTP 401 Unauthorized` | Missing or expired token | Re-login at `http://localhost:5173/login` |
