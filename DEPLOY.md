# CyberCafe POS Pro - Deployment Guide

This guide covers multiple deployment options for the CyberCafe POS Pro system.

## Table of Contents

1. [Local Development Setup](#local-development-setup)
2. [Docker Deployment (Recommended)](#docker-deployment-recommended)
3. [Render Deployment (Cloud)](#render-deployment-cloud)
4. [Manual VPS Deployment](#manual-vps-deployment)
5. [Production Checklist](#production-checklist)

---

## Local Development Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+ (optional for development)

### Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Create and activate virtual environment**:
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**:
   ```bash
   copy .env.example .env  # Windows
   cp .env.example .env    # Linux/Mac
   ```

   Edit `.env` and set:
   ```env
   DATABASE_URL=postgresql://postgres:password@localhost:5432/cybercafe_pos
   REDIS_URL=redis://localhost:6379
   SECRET_KEY=your-secret-key-min-32-characters-long
   CORS_ORIGINS=http://localhost:5173,http://localhost:3000
   ```

5. **Create database**:
   ```bash
   # Using psql
   psql -U postgres
   CREATE DATABASE cybercafe_pos;
   \q
   ```

6. **Run migrations**:
   ```bash
   alembic upgrade head
   ```

7. **Seed initial data**:
   ```bash
   python -m app.seed
   ```

8. **Start the server**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

   Backend will be available at `http://localhost:8000`
   API docs at `http://localhost:8000/docs`

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Configure environment**:
   ```bash
   copy .env.example .env  # Windows
   cp .env.example .env    # Linux/Mac
   ```

   Edit `.env`:
   ```env
   VITE_API_URL=http://localhost:8000
   VITE_WS_URL=ws://localhost:8000
   ```

4. **Start development server**:
   ```bash
   npm run dev
   ```

   Frontend will be available at `http://localhost:5173`

---

## Docker Deployment (Recommended)

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+

### Quick Start

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd pos
   ```

2. **Create environment file**:
   ```bash
   copy .env.example .env  # Windows
   cp .env.example .env    # Linux/Mac
   ```

3. **Edit `.env` file**:
   ```env
   DB_PASSWORD=your_secure_database_password
   SECRET_KEY=your_secret_key_minimum_32_characters_long
   CORS_ORIGINS=http://localhost:3000
   API_URL=http://localhost:8000
   WS_URL=ws://localhost:8000
   DEBUG=False
   ```

4. **Start all services**:
   ```bash
   docker-compose up -d
   ```

5. **Run migrations and seed data**:
   ```bash
   docker-compose exec backend alembic upgrade head
   docker-compose exec backend python -m app.seed
   ```

6. **Access the application**:
   - Frontend: `http://localhost:3000`
   - Backend API: `http://localhost:8000`
   - API Docs: `http://localhost:8000/docs`

### Docker Commands

```bash
# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes database)
docker-compose down -v

# Rebuild containers
docker-compose up -d --build

# Access backend shell
docker-compose exec backend bash

# Access database
docker-compose exec postgres psql -U postgres -d cybercafe_pos
```

---

## Render Deployment (Cloud)

Render provides free PostgreSQL and Redis instances, making it ideal for cloud deployment.

### Step 1: Create PostgreSQL Database

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **New** → **PostgreSQL**
3. Configure:
   - **Name**: `cybercafe-pos-db`
   - **Database**: `cybercafe_pos`
   - **User**: `cybercafe_user`
   - **Region**: Choose closest to your users
   - **Plan**: Free or Starter
4. Click **Create Database**
5. Copy the **Internal Database URL** (starts with `postgresql://`)

### Step 2: Create Redis Instance

1. Click **New** → **Redis**
2. Configure:
   - **Name**: `cybercafe-pos-redis`
   - **Region**: Same as database
   - **Plan**: Free
3. Click **Create Redis**
4. Copy the **Internal Redis URL** (starts with `redis://`)

### Step 3: Deploy Backend

1. Click **New** → **Web Service**
2. Connect your GitHub repository
3. Configure:
   - **Name**: `cybercafe-pos-backend`
   - **Region**: Same as database
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**:
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command**:
     ```bash
     alembic upgrade head && python -m app.seed && uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```
   - **Plan**: Free or Starter

4. **Add Environment Variables**:
   - `DATABASE_URL`: (Paste Internal Database URL from Step 1)
   - `REDIS_URL`: (Paste Internal Redis URL from Step 2)
   - `SECRET_KEY`: (Generate: `openssl rand -hex 32`)
   - `CORS_ORIGINS`: `https://your-frontend-name.onrender.com`
   - `DEBUG`: `False`

5. Click **Create Web Service**

6. Wait for deployment to complete. Copy the service URL (e.g., `https://cybercafe-pos-backend.onrender.com`)

### Step 4: Deploy Frontend

1. Click **New** → **Static Site**
2. Connect your GitHub repository
3. Configure:
   - **Name**: `cybercafe-pos-frontend`
   - **Branch**: `main`
   - **Root Directory**: `frontend`
   - **Build Command**:
     ```bash
     npm install && npm run build
     ```
   - **Publish Directory**: `dist`

4. **Add Environment Variables**:
   - `VITE_API_URL`: (Paste backend URL from Step 3)
   - `VITE_WS_URL`: (Replace `https://` with `wss://` in backend URL)

5. Click **Create Static Site**

6. Wait for deployment. Your app will be live at `https://your-frontend-name.onrender.com`

### Step 5: Update CORS

1. Go to backend service on Render
2. Update `CORS_ORIGINS` environment variable with your actual frontend URL
3. Save changes (service will redeploy)

### Important Notes for Render

- **Free tier limitations**:
  - Services spin down after 15 minutes of inactivity
  - First request after spin-down takes 30-60 seconds
  - Database limited to 1GB
  
- **Upgrade to paid plan** for:
  - Always-on services
  - More database storage
  - Better performance

---

## Manual VPS Deployment

For deploying to a VPS (DigitalOcean, AWS EC2, Linode, etc.)

### Prerequisites
- Ubuntu 22.04 LTS (or similar)
- Root or sudo access
- Domain name (optional but recommended)

### Step 1: Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.11 python3.11-venv python3-pip nodejs npm postgresql postgresql-contrib redis-server nginx certbot python3-certbot-nginx

# Start services
sudo systemctl start postgresql
sudo systemctl start redis-server
sudo systemctl enable postgresql
sudo systemctl enable redis-server
```

### Step 2: Database Setup

```bash
# Create database and user
sudo -u postgres psql
CREATE DATABASE cybercafe_pos;
CREATE USER cybercafe_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE cybercafe_pos TO cybercafe_user;
\q
```

### Step 3: Deploy Backend

```bash
# Create app directory
sudo mkdir -p /var/www/cybercafe-pos
cd /var/www/cybercafe-pos

# Clone repository
git clone <your-repo-url> .

# Setup backend
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
DATABASE_URL=postgresql://cybercafe_user:your_secure_password@localhost:5432/cybercafe_pos
REDIS_URL=redis://localhost:6379
SECRET_KEY=$(openssl rand -hex 32)
CORS_ORIGINS=https://yourdomain.com
DEBUG=False
EOF

# Run migrations and seed
alembic upgrade head
python -m app.seed
```

### Step 4: Setup Systemd Service

```bash
# Create backend service
sudo nano /etc/systemd/system/cybercafe-backend.service
```

Add:
```ini
[Unit]
Description=CyberCafe POS Backend
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/cybercafe-pos/backend
Environment="PATH=/var/www/cybercafe-pos/backend/venv/bin"
ExecStart=/var/www/cybercafe-pos/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000

[Install]
WantedBy=multi-user.target
```

```bash
# Start backend service
sudo systemctl daemon-reload
sudo systemctl start cybercafe-backend
sudo systemctl enable cybercafe-backend
```

### Step 5: Deploy Frontend

```bash
cd /var/www/cybercafe-pos/frontend

# Create .env
cat > .env << EOF
VITE_API_URL=https://api.yourdomain.com
VITE_WS_URL=wss://api.yourdomain.com
EOF

# Build
npm install
npm run build
```

### Step 6: Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/cybercafe-pos
```

Add:
```nginx
# Backend API
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Frontend
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    root /var/www/cybercafe-pos/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/cybercafe-pos /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 7: Setup SSL (Let's Encrypt)

```bash
# Get SSL certificates
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com -d api.yourdomain.com

# Auto-renewal
sudo systemctl enable certbot.timer
```

---

## Production Checklist

Before going live, ensure:

### Security
- [ ] Changed all default passwords
- [ ] Set strong `SECRET_KEY` (min 32 characters)
- [ ] Enabled HTTPS/SSL
- [ ] Configured proper CORS origins
- [ ] Set `DEBUG=False`
- [ ] Reviewed user permissions
- [ ] Enabled firewall (ufw/iptables)

### Database
- [ ] Configured automated backups
- [ ] Set up database connection pooling
- [ ] Optimized PostgreSQL settings
- [ ] Created database indexes

### Monitoring
- [ ] Set up error logging
- [ ] Configure uptime monitoring
- [ ] Set up performance monitoring
- [ ] Configure alerts for critical errors

### Backup
- [ ] Database backup strategy
- [ ] File backup strategy
- [ ] Tested restore procedures
- [ ] Documented backup locations

### Performance
- [ ] Enabled gzip compression
- [ ] Configured caching headers
- [ ] Optimized database queries
- [ ] Load tested the application

### Documentation
- [ ] Documented deployment process
- [ ] Created runbook for common issues
- [ ] Documented backup/restore procedures
- [ ] Created user training materials

---

## Troubleshooting

### Backend won't start
```bash
# Check logs
docker-compose logs backend
# or
sudo journalctl -u cybercafe-backend -f

# Common issues:
# - Database connection: Check DATABASE_URL
# - Redis connection: Check REDIS_URL
# - Port already in use: Change port or kill process
```

### Frontend can't connect to backend
```bash
# Check CORS settings in backend .env
# Verify VITE_API_URL in frontend .env
# Check browser console for errors
```

### Database migration errors
```bash
# Reset migrations (WARNING: deletes data)
alembic downgrade base
alembic upgrade head

# Or create new migration
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Permission errors
```bash
# Fix ownership
sudo chown -R www-data:www-data /var/www/cybercafe-pos

# Fix permissions
sudo chmod -R 755 /var/www/cybercafe-pos
```

---

## Support

For issues or questions:
- Check logs first
- Review this deployment guide
- Check the main README.md
- Contact: support@cybercafe.com

## Updates

To update the application:

```bash
# Pull latest code
git pull origin main

# Backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
sudo systemctl restart cybercafe-backend

# Frontend
cd ../frontend
npm install
npm run build
sudo systemctl reload nginx
```
