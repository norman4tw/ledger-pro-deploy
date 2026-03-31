# Frontend already built - just copy static files
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Copy backend
COPY backend/ ./backend/
WORKDIR /app/backend
RUN pip install --no-cache-dir -r requirements.txt

# Copy frontend build (already built, no need to rebuild)
COPY frontend/ ./frontend/

# Copy nginx config
COPY nginx/nginx.conf /etc/nginx/nginx.conf

# Set environment variables
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8080

# Start nginx and gunicorn
CMD service nginx start && \
    gunicorn --bind 0.0.0.0:5000 --workers 2 --threads 4 run:app
