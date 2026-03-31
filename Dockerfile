# Frontend already built - just serve static files + proxy API
FROM python:3.11-slim

WORKDIR /app

# Install nginx
RUN apt-get update && apt-get install -y \
    nginx \
    && rm -rf /var/lib/apt/lists/* \
    && chown -R root:root /app

# Copy frontend FIRST
COPY frontend/ /app/frontend/

# Copy backend
COPY backend/ /app/backend/
WORKDIR /app/backend

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy nginx config
COPY nginx/nginx.conf /etc/nginx/nginx.conf

# Ensure nginx can read files
RUN chmod -R 755 /app/frontend

# Set environment variables
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8080

# Run: start nginx, then gunicorn
CMD nginx & \
    sleep 1 && \
    gunicorn --bind 0.0.0.0:5000 --workers 2 --threads 4 run:app
