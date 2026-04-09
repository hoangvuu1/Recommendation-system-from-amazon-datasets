# Docker & Deployment Guide

## Quick Start with Docker (Recommended)

### 1. Build Docker Image

```bash
docker build -t recommendation-system:latest .
```

### 2. Run Container

```bash
docker run -p 8000:8000 recommendation-system:latest
```

Access at: `http://localhost:8000`

---

## Manual Installation

### Prerequisites
- Python 3.8+
- pip or conda

### Setup

```bash
# 1. Navigate to web directory
cd web

# 2. Create virtual environment
python -m venv venv

# Activate it
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 3. Install dependencies
pip install -r backend/requirements.txt

# 4. Run backend
python run.py
```

---

## Production Deployment

### Using Gunicorn + Supervisor (Linux)

```bash
pip install gunicorn

# Run with 4 workers
gunicorn -w 4 -b 0.0.0.0:8000 backend.main:app
```

### Using PM2 (Node.js)

```bash
npm install -g pm2

pm2 start "python run.py" --name "recommendation-api"
pm2 startup
pm2 save
```

### Using systemd (Linux)

Create `/etc/systemd/system/recommendation-system.service`:

```ini
[Unit]
Description=Recommendation System API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/project/web
Environment="PATH=/path/to/project/web/venv/bin"
ExecStart=/path/to/project/web/venv/bin/python run.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:

```bash
sudo systemctl enable recommendation-system
sudo systemctl start recommendation-system
```

---

## Nginx Reverse Proxy (Production)

Create `/etc/nginx/sites-available/recommendation-system`:

```nginx
server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable:

```bash
sudo ln -s /etc/nginx/sites-available/recommendation-system /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## AWS Deployment (EC2)

```bash
# 1. Launch EC2 instance (Ubuntu 20.04)

# 2. Install dependencies
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv

# 3. Clone repo
git clone <repo-url>
cd Recommendation-system-from-amazon-datasets-main/web

# 4. Setup
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# 5. Run with systemd (see above)

# 6. Setup security group (allow ports 80, 443, 8000)
```

---

## Docker Compose (Multi-container)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app/backend
      - ./frontend:/app/frontend
    environment:
      - API_HOST=0.0.0.0
      - API_PORT=8000
      - DEBUG=False

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - api
```

Run:

```bash
docker-compose up
```

---

## Environment Variables

Set these for production:

```bash
# .env file
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False
RELOAD=False

# CORS - restrict to your domain
CORS_ORIGINS=https://yourdomain.com

# Feature flags
LOAD_METADATA=True
CONTENT_BASED_ENABLED=True
```

---

## Monitoring & Logging

### Using ELK Stack (Elasticsearch, Logstash, Kibana)

```python
# In main.py
import logging
from pythonjsonlogger import jsonlogger

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
handler.setFormatter(formatter)
logger.addHandler(handler)
```

### Using Datadog

```bash
pip install datadog

# Configure in main.py
from datadog import api, initialize

initialize(api_key="YOUR_API_KEY", app_key="YOUR_APP_KEY")
```

---

## Performance Optimization

### 1. Enable Caching

```python
from fastapi_cache2 import FastAPICache2
from fastapi_cache2.backends.redis import RedisBackend

FastAPICache2.init(RedisBackend(url="redis://localhost"), prefix="fastapi-cache")
```

### 2. Database Connection Pooling

```python
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40
)
```

### 3. Load Testing

```bash
pip install locust

# Create locustfile.py and run
locust -f locustfile.py --host=http://localhost:8000
```

---

## SSL/TLS (HTTPS)

### Let's Encrypt with Certbot

```bash
sudo apt-get install certbot python3-certbot-nginx

sudo certbot --nginx -d yourdomain.com

# Auto-renew
sudo systemctl enable certbot.timer
```

---

## Troubleshooting

### Port 8000 already in use
```bash
# Kill process on port 8000
# Linux/Mac
lsof -ti:8000 | xargs kill -9

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Memory issues
```bash
# Check memory usage
python -m memory_profiler main.py

# Use streaming for large files
```

### Connection errors
- Check firewall settings
- Verify API_HOST and API_PORT
- Check CORS configuration

---

## Monitoring Checklist

- [ ] CPU usage < 70%
- [ ] Memory usage < 80%
- [ ] Response time < 1s
- [ ] Error rate < 1%
- [ ] Uptime > 99.9%
- [ ] API documentation accessible
- [ ] HTTPS enabled
- [ ] Backups configured
