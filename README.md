# Intelligent Driver Safety System

This is the Phase 1 foundation for the final-year B.Tech CSE project titled "Intelligent Driver Safety System Using AI-Based Drowsiness Detection".

## Phase 1 included

- Project folder structure
- Python virtual environment setup
- FastAPI backend foundation
- React + Vite frontend foundation
- SQLite configuration scaffold
- Environment template and gitignore
- Basic verification tests

## Project structure

```text
driver-safety-system/
├── backend/
│   └── app/
├── frontend/
├── database/
├── docs/
├── sounds/
├── tests/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
└── .venv/
```

## Backend run command

```bash
cd driver-safety-system
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

## Frontend run command

```bash
cd driver-safety-system/frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

## Testing

```bash
cd driver-safety-system
.\.venv\Scripts\python -m pytest tests/test_backend_health.py -q
```

## Notes

This is a software-only implementation using the laptop webcam as the hardware input. The AI module and full driver-monitoring logic will be implemented in later phases after this foundation is validated.
