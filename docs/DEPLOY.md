# VarhadCrop Deployment Guide

This guide describes how to run and deploy the VarhadCrop platform (Flask API backend + Vite/React frontend) locally, via Docker, and on Northflank.

---

## 1. Environment Variables

| Variable | Scope | Default | Description |
| :--- | :--- | :--- | :--- |
| `PORT` | Backend | `5000` | Port for Flask / Gunicorn server. Automatically assigned by Northflank. |
| `HOST` | Backend | `0.0.0.0` | Binding host address. |
| `CORS_ORIGIN` | Backend | `*` | Allowed CORS origins (e.g. `https://varhadcrop.org`). |
| `VITE_API_BASE` | Frontend | `""` (empty for same-origin proxy) | Base URL for API requests in production. |
| `VITE_API_TARGET` | Frontend (Vite dev) | `http://127.0.0.1:5000` | Proxy target for local Vite development. |

No API secrets, private keys, or paid credentials are required. All datasets (ICRISAT DLD, NASA POWER) are open access under Creative Commons and Public Domain.

---

## 2. Local Execution

### Windows PowerShell

```powershell
# 1. Clone repository and navigate to root
cd D:\Projects\VarhadCrop

# 2. Set up Python environment
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .

# 3. Optional: Rebuild pipeline artifacts from raw data
python -m scripts.build_all

# 4. Start the backend API server (runs on port 5000)
python -m backend.app

# 5. In a second PowerShell window, start the frontend (port 5173)
cd frontend
npm ci
npm run dev
```

Visit `http://localhost:5173` in your browser.

---

### Linux / macOS Bash

```bash
# 1. Clone repository and navigate to root
cd /path/to/VarhadCrop

# 2. Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .

# 3. Optional: Rebuild pipeline artifacts from raw data
python3 -m scripts.build_all

# 4. Start the backend API server (runs on port 5000)
python3 -m backend.app

# 5. In a second terminal window, start the frontend (port 5173)
cd frontend
npm ci
npm run dev
```

Visit `http://localhost:5173` in your browser.

---

## 3. Containerized Deployment (Multi-Stage Docker)

The repository provides a multi-stage `Dockerfile`:
- **Stage 1 (Node 22):** Installs frontend dependencies and compiles the React SPA into static assets (`frontend/dist/`).
- **Stage 2 (Python 3.12):** Installs LightGBM and Python dependencies, copies backend code and pre-compiled frontend assets, and launches Gunicorn.

This produces a single, self-contained container image serving both the REST API and the frontend dashboard.

```bash
# Build the unified container image
docker build -t varhadcrop:latest .

# Run container locally
docker run -d -p 5000:5000 \
  -e PORT=5000 \
  -e CORS_ORIGIN="*" \
  --name varhadcrop-app \
  varhadcrop:latest
```

Verify status:
```bash
# API healthcheck
curl http://localhost:5000/api/health

# Web client
curl -I http://localhost:5000/
```

---

## 4. Deploying to Northflank

Northflank allows you to deploy either using their CLI tool from your terminal or by connecting your GitHub repository.

### Method A: Deploying via Northflank Web UI (Git Integration)

1. **Log in to Northflank:** Navigate to [app.northflank.com](https://app.northflank.com).
2. **Create or Open a Project:**
   - Click **Create Project**, name it `varhadcrop` (select your preferred region, e.g. Europe or US).
3. **Create a Combined Service:**
   - Click **Create Service** -> **Combined Service** (Deployment + Build).
   - Name your service: `varhadcrop-app`.
   - Under **Build Source**, select **Version Control** -> **GitHub**.
   - Choose repository: `ishanvaidya01/VarhadCrop`.
   - Branch: `main`.
   - Build Type: **Dockerfile**.
   - Dockerfile path: `/Dockerfile`.
   - Build Context: `/`.
4. **Configure Ports & Networking:**
   - Protocol: `HTTP`.
   - Internal Port: `5000` (Northflank maps this to an external public HTTPS domain automatically).
   - Health check path: `/api/health`.
5. **Environment Variables:**
   - `PORT`: `5000` (Northflank passes this automatically).
   - `PYTHONUNBUFFERED`: `1`.
   - `CORS_ORIGIN`: `*`.
6. **Deploy:**
   - Click **Create Service**. Northflank will clone the repository, run the multi-stage Docker build, and deploy the container.

---

### Method B: Deploying via Northflank CLI from Terminal

You can execute the entire deployment from your terminal using the official Northflank CLI:

```bash
# 1. Install Northflank CLI globally (requires Node.js)
npm install -g @northflank/cli

# 2. Log in to Northflank via terminal
northflank login

# 3. Create a project
northflank create project --name varhadcrop --description "VarhadCrop agroclimatic decision support"

# 4. Create a Combined Service using the repository Dockerfile
northflank create service combined \
  --project varhadcrop \
  --name varhadcrop-app \
  --vcsProvider github \
  --vcsRepository ishanvaidya01/VarhadCrop \
  --vcsBranch main \
  --buildType dockerfile \
  --dockerfilePath /Dockerfile \
  --dockerContext / \
  --port 5000 \
  --protocol HTTP \
  --public \
  --healthCheckType http \
  --healthCheckPath /api/health

# 5. Follow live build and deployment logs
northflank logs --project varhadcrop --service varhadcrop-app --follow
```

Once the build finishes, Northflank provides a public HTTPS URL (e.g. `https://varhadcrop-app--[user-hash].northflank.app`) serving both the interactive web dashboard and all `/api/*` endpoints.
