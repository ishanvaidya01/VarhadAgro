# VarhadCrop Deployment Guide

This guide describes how to run and deploy the VarhadCrop platform (Flask API backend + Vite/React frontend).

---

## 1. Environment Variables

| Variable | Scope | Default | Description |
| :--- | :--- | :--- | :--- |
| `PORT` | Backend | `5000` | Port for Flask / Gunicorn server. |
| `HOST` | Backend | `0.0.0.0` | Binding host address. |
| `CORS_ORIGIN` | Backend | `*` | Allowed CORS origins (e.g. `https://varhadcrop.org`). |
| `VITE_API_BASE` | Frontend | `""` (empty for proxy) | Base URL for API requests in production. |
| `VITE_API_TARGET` | Frontend (Vite dev) | `http://127.0.0.1:5000` | Proxy target for local Vite development. |

No API secrets, private keys, or credentials are required in the repository. All datasets (ICRISAT DLD, NASA POWER) are open access under Creative Commons and Public Domain.

---

## 2. Local Execution

### Windows PowerShell

```powershell
# 1. Clone repository and navigate to root
cd D:\Projects\BioTech-AI

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
cd /path/to/BioTech-AI

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

## 3. Containerized Deployment (Docker)

### Build and Run Backend

```bash
# Build Docker image
docker build -t varhadcrop-backend .

# Run container
docker run -d -p 5000:5000 \
  -e PORT=5000 \
  -e CORS_ORIGIN="*" \
  --name varhadcrop-api \
  varhadcrop-backend
```

Test health check:
```bash
curl http://localhost:5000/api/health
```

---

## 4. Production Static Frontend Hosting

The React frontend compiles into a standalone static bundle with zero server dependencies:

```bash
cd frontend
npm ci
npm run build
```

The output in `frontend/dist/` can be served directly from:
- Cloudflare Pages
- Vercel / Netlify
- AWS S3 + CloudFront
- Nginx / Caddy

Set `VITE_API_BASE` during build if the API is hosted on a separate domain:
```bash
VITE_API_BASE=https://api.varhadcrop.org npm run build
```
