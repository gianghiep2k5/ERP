# macOS Setup

## Verify tools
```bash
git --version
python3 --version
node --version
npm --version
python3 scripts/verify_database.py
```

## Antigravity IDE
Open Antigravity IDE → Open Folder → choose this folder. Start with the default/review-first security preset and keep access limited to the workspace. Paste Phase 0 from `PROMPTS_ANTIGRAVITY.md`.

## VS Code integration
Antigravity IDE and VS Code can open the same folder; no bridge is needed. In VS Code press Cmd+Shift+P and run `Shell Command: Install 'code' command in PATH`, restart Terminal, then run:
```bash
code .
```
Do not edit the same file in both applications simultaneously.

Recommended VS Code extensions: Python, Pylance, ESLint, Prettier, SQLite Viewer, REST Client or Thunder Client.

## Backend (after Antigravity scaffolds it)
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Check `http://127.0.0.1:8000/api/health` and `http://127.0.0.1:8000/docs`.

## Frontend
```bash
cd frontend
npm install
npm run dev
```
Open the local URL printed by Vite.

## Demo credentials
All users use `Demo@123`: warehouse.staff, warehouse.manager, planner, quality.manager, branch.manager.

## Browser verification
Start both servers and ask Antigravity: `/browser Open the local frontend, log in as warehouse.manager, execute the expiry-risk approval flow, and capture screenshots.`

## Git checkpoints
```bash
git init
git add .
git commit -m "Initial V-IMS AI seed pack"
```
Commit after each completed phase.
