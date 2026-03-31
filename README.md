# Ledger Pro - Full Stack Deployment

Flask + PostgreSQL + React + Nginx

## Architecture

```
User → Nginx (port 8080)
         ├── /          → React Frontend (static files)
         ├── /api/*     → Flask Backend (proxy to port 5000)
         └── /health    → Health check
```

## Deploy to Zeebur

1. Push to GitHub
2. Connect to Zeebur from GitHub
3. Zeebur auto-detects Dockerfile
4. Add environment variables:
   - `DATABASE_URL`
   - `SECRET_KEY`
   - `JWT_SECRET_KEY`
5. Deploy!

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | Flask secret key |
| `JWT_SECRET_KEY` | JWT signing key |

## Local Development

```bash
# Backend only
cd backend
pip install -r requirements.txt
python run.py

# Frontend
cd frontend
npm install
npm run dev
```

## Docker Build

```bash
docker build -t ledger-pro .
docker run -p 8080:8080 -e DATABASE_URL=... ledger-pro
```
