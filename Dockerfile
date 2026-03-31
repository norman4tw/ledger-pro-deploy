# Simple Flask + Nginx setup
FROM python:3.11-slim

WORKDIR /app

# Install nginx
RUN apt-get update && apt-get install -y nginx && rm -rf /var/lib/apt/lists/*

# Copy frontend to /var/www/html
COPY frontend/ /var/www/html/

# Copy backend
COPY backend/ /app/backend/
WORKDIR /app/backend
RUN pip install --no-cache-dir -r requirements.txt

# Copy nginx config to sites-available
COPY nginx/nginx.conf /etc/nginx/sites-available/default

# Enable the site by linking to sites-enabled
RUN rm -f /etc/nginx/sites-enabled/default && \
    ln -s /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default

ENV FLASK_ENV=production
EXPOSE 8080

CMD nginx && sleep 1 && gunicorn --bind 0.0.0.0:5000 --workers 2 run:app
