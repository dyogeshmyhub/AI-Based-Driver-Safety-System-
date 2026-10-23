# ByteArray — Intelligent Driver Safety System

An AI-based driver monitoring project developed as a final-year B.Tech Computer Science and Engineering (CSE) project.

## Project Overview

The **Intelligent Driver Safety System Using AI-Based Drowsiness Detection** aims to improve driver safety by monitoring driver behaviour through a laptop webcam. The system is designed to detect signs of drowsiness and distraction and provide appropriate visual and audio alerts.

This is a **software-only implementation** that uses the laptop's built-in or externally connected webcam as its camera input. No Raspberry Pi or dedicated hardware controller is required.

## Project Objectives

- Monitor the driver using a webcam.
- Detect facial features and eye closure.
- Identify signs of drowsiness, such as prolonged eye closure and yawning.
- Estimate driver attention using head orientation and facial behaviour.
- Generate audio alerts when configured safety conditions are detected.
- Display monitoring information through a real-time web dashboard.
- Record monitoring sessions and safety events when supported by the implemented backend.

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | React, Vite, JavaScript, CSS |
| Backend | Python, FastAPI |
| AI and computer vision | Python-based detection modules |
| Database | SQLite |
| API communication | REST API and WebSocket, where implemented |
| Camera input | Laptop webcam |
| Testing | Pytest and frontend tests, where configured |
| Development environment | Visual Studio Code |

## Project Structure

```text
driver-safety-system/
├── ai/
│   ├── monitoring.py
│   ├── safety_engine.py
│   ├── test_face_detection.py
│   └── yawn_detector.py
├── backend/
│   └── app/
├── database/
├── docs/
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── sounds/
├── tests/
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

*Note: The listed structure represents the main project components. Individual files may vary as development progresses.*

## Prerequisites

Install the following before running the project:

- Python 3.10 or a compatible version required by the dependencies.
- Node.js and npm.
- Visual Studio Code or another code editor.
- A laptop webcam.
- Git, if you want to clone or update the repository.

## Installation and Setup

### 1. Open the project directory

Open the project folder in VS Code and select **Terminal → New Terminal**.

```powershell
cd driver-safety-system
```

Run this command from the parent directory containing `driver-safety-system` if you are not already inside the project folder.

### 2. Set up the Python virtual environment

```powershell
python -m venv .venv
```

Install the backend dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. Configure environment variables

Create a local `.env` file based on `.env.example` and configure the required values.

Keep `.env` private. Do not commit API secrets, credentials, or production keys to GitHub.

### 4. Start the backend

From the project root, run:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

The backend should be available at:

- API base URL: `http://127.0.0.1:8000`
- API documentation: `http://127.0.0.1:8000/docs`

Keep this terminal running.

### 5. Start the frontend

Open a **second terminal** in VS Code:

```powershell
cd frontend
npm install
npm run dev
```

Open the local development URL printed by Vite in your terminal. The default URL is usually:

`http://localhost:5173`

Keep the frontend terminal running as well.

## Running Tests

From the project root, run the backend health test:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_backend_health.py -q
```

Run the available backend test suite:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

For frontend tests, use the test script configured in `frontend/package.json`, if available.

## Dashboard Features

The web dashboard is designed to display:

- Camera and monitoring status.
- Driver face and eye-state information.
- Eye Aspect Ratio (EAR) metrics.
- Blink and yawn counts.
- Driver attention and drowsiness indicators.
- Safety score and current risk status.
- Visual and audio safety alerts.
- Session history and safety events, where implemented.
- Light and dark appearance modes with a Liquid Glass-inspired interface.

The availability and accuracy of individual features depend on the current implementation and whether the backend, camera, and detection modules are running correctly.

## Camera and Monitoring

1. Start the backend.
2. Start the frontend.
3. Open the dashboard in your browser.
4. Allow camera access if the browser requests permission.
5. Select **Start monitoring**.
6. Check the camera status, detection results, and alert behaviour.

If the dashboard displays `Offline`, `Reconnecting`, `N/A`, or `Failed to fetch`, check that the backend is running, the configured API URL is correct, and the required endpoints are responding.

## Development Phases

- **Phase 1 — Foundation:** Project structure, environment setup, backend and frontend scaffolding, database configuration, and basic tests.
- **Phase 2 — Core integration:** Connect the frontend, backend, and database.
- **Phase 3 — Driver monitoring:** Implement and validate webcam-based facial and eye-state detection.
- **Phase 4 — Safety analysis:** Develop and validate drowsiness and distraction detection.
- **Phase 5 — Alert system:** Integrate and test audio alerts for configured safety conditions.
- **Phase 6 — Dashboard and validation:** Refine the dashboard, verify session/event handling, test failure cases, and document the results.

*These phases describe the intended development roadmap; mark each phase complete only after its functionality has been tested.*

## Important Notes

- This project uses a laptop webcam and software-based processing.
- No Raspberry Pi is required for the described implementation.
- The backend and frontend must both be running for features that depend on their communication.
- Webcam access may require browser permission.
- Detection results are estimates and should not be treated as a replacement for attentive driving or certified vehicle safety equipment.
- Do not use the development server as a production deployment without appropriate security and configuration changes.

## Project Status

The project is being developed incrementally, starting with the foundation and progressing through monitoring, safety analysis, alert handling, and dashboard validation.

**Project title:** Intelligent Driver Safety System Using AI-Based Drowsiness Detection  
**Platform:** Web application  
**Input device:** Laptop webcam  
**Frontend:** React + Vite  
**Backend:** Python + FastAPI  
**Database:** SQLite  
**Repository:** [AI-Based Driver Safety System on GitHub](https://github.com/dyogeshmyhub/AI-Based-Driver-Safety-System-)

---

Developed as a final-year B.Tech CSE project.
