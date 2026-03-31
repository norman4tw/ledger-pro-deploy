# Frontend already built - just serve static files + proxy API
FROM python:3.11-slim

WORKDIR /app

# Install nginx
RUN apt-get install -y nginx && rm -rf /var/lib/apt/lists/*

# Copy frontend FIRST
COPY frontend/ /app/frontend/

# Copy backend
COPY backend/ /app/backend/
WORKDIR /app/backend

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy nginx config
COPY nginx/nginx.conf /etc/nginx/nginx.conf

# Ensure files are readable
RUN chmod -R 755 /app/frontend && chmod 755 /app

# Environment variables
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Expose port (Zeebur will map external port to this)
EXPOSE 8080

# Start nginx in background, then gunicorn
CMD nginx & \
    sleep 2 && \
    gunicorn --bind 0.0.0.0:5000 --workers 2 --threads 4 run:app
