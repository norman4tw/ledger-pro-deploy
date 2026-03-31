# Ledger Pro Backend API

Flask + PostgreSQL REST API for project management with Google Sheets integration.

## Features

- ✅ User authentication (JWT)
- ✅ Project management
- ✅ Phase management (Gantt chart)
- ✅ Task management
- ✅ Google Sheets sync
- ✅ Monday.com ready

## Quick Start

### Local Development

```bash
# Clone the repository
git clone <your-repo-url>
cd ledger-pro-backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your settings

# Run the application
python run.py
```

### Docker

```bash
docker build -t ledger-pro-api .
docker run -p 5000:5000 -e DATABASE_URL=postgresql://... ledger-pro-api
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | ✅ |
| `SECRET_KEY` | Flask secret key | ✅ |
| `JWT_SECRET_KEY` | JWT signing key | ✅ |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to Google service account JSON | For Sheets sync |

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login
- `POST /api/auth/refresh` - Refresh token
- `GET /api/auth/me` - Get current user

### Projects
- `GET /api/projects` - List all projects
- `POST /api/projects` - Create project
- `GET /api/projects/<id>` - Get project with phases
- `PUT /api/projects/<id>` - Update project
- `DELETE /api/projects/<id>` - Delete project

### Phases
- `GET /api/projects/<id>/phases` - List phases
- `POST /api/projects/<id>/phases` - Create phase
- `PUT /api/phases/<id>` - Update phase
- `DELETE /api/phases/<id>` - Delete phase

### Tasks
- `GET /api/tasks` - List tasks
- `POST /api/tasks` - Create task
- `PUT /api/tasks/<id>` - Update task
- `DELETE /api/tasks/<id>` - Delete task

### Google Sheets
- `GET /api/sheets/configs` - List configurations
- `POST /api/sheets/configs` - Create configuration
- `POST /api/sheets/verify` - Verify connection
- `POST /api/sheets/sync/<id>` - Sync data

## Deploy to Zeebur

1. Push this code to GitHub
2. In Zeebur Dashboard, create new project
3. Select "Deploy from GitHub"
4. Choose this repository
5. Zeebur will auto-detect Python/Flask
6. Add environment variables in Zeebur:
   - `DATABASE_URL`
   - `SECRET_KEY`
   - `JWT_SECRET_KEY`
7. Deploy!

## Google Sheets Setup

1. Create Google Cloud project
2. Enable Google Sheets API
3. Create Service Account
4. Download JSON key
5. Share your spreadsheet with the service account email
6. Set `GOOGLE_APPLICATION_CREDENTIALS` to the key path

## License

MIT
