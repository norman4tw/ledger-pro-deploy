# Frontend already built - just serve static files + proxy API
FROM python:3.11-slim

WORKDIR /app

# Install nginx and micro (tiny web server for static files)
RUN apt-get update && apt-get install -y \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Copy backend
COPY backend/ ./backend/
WORKDIR /app/backend

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy frontend build
COPY frontend/ ./frontend/

# Copy nginx config
COPY nginx/nginx.conf /etc/nginx/nginx.conf

# Set environment variables
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8080

# Run: start nginx in daemon mode, then run gunicorn
CMD nginx -g 'daemon off;' & \
    gunicorn --bind 0.0.0.0:5000 --workers 2 --threads 4 run:app
