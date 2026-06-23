# OpenShiksha - Local Development Setup Guide

Complete guide for running the modernized OpenShiksha platform locally on your machine.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Backend Setup](#backend-setup)
- [Frontend Setup](#frontend-setup)
- [Database Setup](#database-setup)
- [Running Everything](#running-everything)
- [Common Commands](#common-commands)
- [Troubleshooting](#troubleshooting)
- [Environment Variables](#environment-variables)

---

## Prerequisites

### Required Software

Install these before starting:

1. **Python 3.11+**
   ```bash
   # Check version
   python --version
   # Should show: Python 3.11.x or higher
   ```

2. **Node.js 18+**
   ```bash
   # Check version
   node --version
   # Should show: v18.x.x or higher

   npm --version
   # Should show: 9.x.x or higher
   ```

3. **PostgreSQL 15+**
   ```bash
   # Check version
   psql --version
   # Should show: psql (PostgreSQL) 15.x
   ```

4. **Redis 7+**
   ```bash
   # Check version
   redis-server --version
   # Should show: Redis server v=7.x.x
   ```

5. **Git**
   ```bash
   git --version
   ```

### Optional but Recommended

- **Docker Desktop** (for containerized services)
- **VS Code** with Python and TypeScript extensions
- **Postman** or **Thunder Client** for API testing

---

## Quick Start

### Option 1: Using Docker Compose (Recommended)

```bash
# Clone repository
cd c:\Users\shara\OneDrive\Desktop\My Stuff\Work\Dev\OpenShiksha

# Start all services
docker-compose up

# Access:
# - Backend API: http://localhost:8000
# - Frontend: http://localhost:5173
# - PostgreSQL: localhost:5432
# - Redis: localhost:6379
```

### Option 2: Manual Setup

See detailed sections below for [Backend](#backend-setup) and [Frontend](#frontend-setup).

---

## Backend Setup

### 1. Create Virtual Environment

```bash
# Navigate to project root
cd c:\Users\shara\OneDrive\Desktop\My Stuff\Work\Dev\OpenShiksha

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Verify activation (should show path to venv)
which python
```

### 2. Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install backend dependencies
pip install -r backend/requirements.txt

# Verify installation
pip list
```

**Key packages installed:**
- Django 4.2
- djangorestframework 3.14
- psycopg2-binary (PostgreSQL adapter)
- celery 5.3
- redis 7.0
- djangorestframework-simplejwt
- django-cors-headers
- pydantic
- channels (WebSockets)

### 3. Configure Environment Variables

```bash
# Copy example environment file
cp backend/.env.example backend/.env

# Edit backend/.env with your settings
notepad backend\.env
```

**Required variables:**
```env
# Django
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://openshiksha:password@localhost:5432/openshiksha_dev

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1

# Cabinet Service
CABINET_API_URL=http://localhost:9000
CABINET_API_KEY=your-cabinet-api-key

# Email (for development)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# JWT Settings
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ACCESS_TOKEN_LIFETIME=3600  # 1 hour in seconds
JWT_REFRESH_TOKEN_LIFETIME=604800  # 7 days in seconds
```

### 4. Initialize Database

```bash
# Navigate to backend directory
cd backend

# Run migrations
python manage.py migrate

# Create superuser (admin account)
python manage.py createsuperuser
# Follow prompts to set username, email, password

# Load initial data (optional)
python manage.py loaddata fixtures/initial_data.json
```

### 5. Run Backend Server

```bash
# Development server (auto-reload on code changes)
python manage.py runserver

# Or specify port
python manage.py runserver 8000

# Server will be available at: http://localhost:8000
```

**Backend is ready when you see:**
```
Performing system checks...
System check identified no issues (0 silenced).
January 04, 2026 - 10:00:00
Django version 4.2.x, using settings 'openshiksha.settings.development'
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

---

## Frontend Setup

### 1. Install Dependencies

```bash
# Navigate to frontend directory
cd frontend

# Install npm packages
npm install

# This installs:
# - React 18
# - TypeScript
# - Vite
# - React Query
# - Recharts
# - Tailwind CSS
# - Axios
# - React Router
# - KaTeX
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env
notepad .env
```

**Required variables:**
```env
# API Configuration
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_API_TIMEOUT=30000

# WebSocket
VITE_WS_URL=ws://localhost:8000/ws

# Cabinet
VITE_CABINET_URL=http://localhost:9000

# Feature Flags
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_NOTIFICATIONS=true

# Environment
VITE_ENV=development
```

### 3. Run Frontend Development Server

```bash
# Start Vite dev server
npm run dev

# Frontend will be available at: http://localhost:5173
```

**Frontend is ready when you see:**
```
  VITE v5.x.x  ready in 500 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h to show help
```

### 4. Build for Production (Optional)

```bash
# Create production build
npm run build

# Preview production build
npm run preview
```

---

## Database Setup

### PostgreSQL Database

#### Create Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE openshiksha_dev;

# Create user
CREATE USER openshiksha WITH PASSWORD 'your-password-here';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE openshiksha_dev TO openshiksha;

# Exit psql
\q
```

#### Restore from Backup (if available)

```bash
# Restore MySQL backup to PostgreSQL
pgloader mysql://user:pass@localhost/openshiksha_old \
         postgresql://openshiksha:password@localhost/openshiksha_dev

# Or restore from PostgreSQL dump
pg_restore -U openshiksha -d openshiksha_dev backup.dump
```

#### Reset Database

```bash
# Drop and recreate (WARNING: Deletes all data)
psql -U postgres
DROP DATABASE openshiksha_dev;
CREATE DATABASE openshiksha_dev;
GRANT ALL PRIVILEGES ON DATABASE openshiksha_dev TO openshiksha;
\q

# Run migrations again
cd backend
python manage.py migrate
```

---

## Running Everything

### Start All Services Manually

**Terminal 1: PostgreSQL** (if not running as service)
```bash
# Windows
pg_ctl -D "C:\Program Files\PostgreSQL\15\data" start

# Linux/Mac
sudo systemctl start postgresql
```

**Terminal 2: Redis** (if not running as service)
```bash
# Windows
redis-server

# Linux/Mac
redis-server /usr/local/etc/redis.conf
```

**Terminal 3: Backend Django Server**
```bash
cd c:\Users\shara\OneDrive\Desktop\My Stuff\Work\Dev\OpenShiksha\backend
venv\Scripts\activate
python manage.py runserver
```

**Terminal 4: Celery Worker** (for background tasks)
```bash
cd c:\Users\shara\OneDrive\Desktop\My Stuff\Work\Dev\OpenShiksha\backend
venv\Scripts\activate
celery -A openshiksha worker -l info
```

**Terminal 5: Celery Beat** (for scheduled tasks)
```bash
cd c:\Users\shara\OneDrive\Desktop\My Stuff\Work\Dev\OpenShiksha\backend
venv\Scripts\activate
celery -A openshiksha beat -l info
```

**Terminal 6: Frontend Dev Server**
```bash
cd c:\Users\shara\OneDrive\Desktop\My Stuff\Work\Dev\OpenShiksha\frontend
npm run dev
```

### Using Docker Compose (Easier)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: openshiksha_dev
      POSTGRES_USER: openshiksha
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    ports:
      - "6379:6379"

  backend:
    build: ./backend
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - ./backend:/app
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    environment:
      - DATABASE_URL=postgresql://openshiksha:password@postgres:5432/openshiksha_dev
      - REDIS_URL=redis://redis:6379/0

  celery:
    build: ./backend
    command: celery -A openshiksha worker -l info
    volumes:
      - ./backend:/app
    depends_on:
      - postgres
      - redis
    environment:
      - DATABASE_URL=postgresql://openshiksha:password@postgres:5432/openshiksha_dev
      - REDIS_URL=redis://redis:6379/0

  frontend:
    build: ./frontend
    command: npm run dev -- --host
    volumes:
      - ./frontend:/app
      - /app/node_modules
    ports:
      - "5173:5173"
    environment:
      - VITE_API_BASE_URL=http://localhost:8000/api/v1

volumes:
  postgres_data:
```

**Start everything:**
```bash
docker-compose up
```

**Stop everything:**
```bash
docker-compose down
```

---

## Common Commands

### Backend Commands

```bash
# Activate virtual environment
venv\Scripts\activate

# Run development server
python manage.py runserver

# Run migrations
python manage.py migrate

# Create new migration
python manage.py makemigrations

# Create superuser
python manage.py createsuperuser

# Run tests
python manage.py test

# Run specific test
python manage.py test core.tests.test_constraints

# Django shell
python manage.py shell

# Database shell
python manage.py dbshell

# Collect static files
python manage.py collectstatic

# Load fixtures
python manage.py loaddata fixtures/sample_data.json

# Create fixtures
python manage.py dumpdata core.Question --indent 2 > fixtures/questions.json

# Check for issues
python manage.py check

# Show migrations
python manage.py showmigrations

# Run Celery worker
celery -A openshiksha worker -l info

# Run Celery beat (scheduler)
celery -A openshiksha beat -l info

# Monitor Celery
celery -A openshiksha flower  # Access at http://localhost:5555
```

### Frontend Commands

```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run linter
npm run lint

# Fix linting issues
npm run lint:fix

# Run type checking
npm run type-check

# Run tests
npm run test

# Run tests in watch mode
npm run test:watch

# Run E2E tests
npm run test:e2e

# Format code
npm run format

# Clean node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Database Commands

```bash
# Connect to PostgreSQL
psql -U openshiksha -d openshiksha_dev

# List databases
\l

# Connect to database
\c openshiksha_dev

# List tables
\dt

# Describe table
\d core_question

# Run SQL query
SELECT * FROM core_question LIMIT 10;

# Exit psql
\q

# Backup database
pg_dump -U openshiksha openshiksha_dev > backup_$(date +%Y%m%d).sql

# Restore database
psql -U openshiksha openshiksha_dev < backup_20260104.sql
```

### Redis Commands

```bash
# Connect to Redis CLI
redis-cli

# Check connection
PING  # Should return PONG

# List all keys
KEYS *

# Get value
GET key_name

# Delete key
DEL key_name

# Flush all data (WARNING: Deletes everything)
FLUSHALL

# Monitor Redis commands
MONITOR

# Exit Redis CLI
exit
```

### Git Commands

```bash
# Check status
git status

# Create feature branch
git checkout -b feature/phase-0-setup

# Add files
git add .

# Commit with message
git commit -m "Phase 0: Set up project structure"

# Push to remote
git push origin feature/phase-0-setup

# Pull latest changes
git pull origin main

# View commit history
git log --oneline

# View changes
git diff
```

---

## Troubleshooting

### Backend Issues

#### "Port 8000 already in use"
```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process (Windows)
taskkill /PID <PID> /F

# Or use different port
python manage.py runserver 8001
```

#### "No module named 'xyz'"
```bash
# Ensure virtual environment is activated
venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt

# Or install specific package
pip install package-name
```

#### "Database connection error"
```bash
# Check PostgreSQL is running
pg_isready

# Check connection settings in .env
# Verify DATABASE_URL is correct

# Test connection manually
psql -U openshiksha -d openshiksha_dev
```

#### "Redis connection error"
```bash
# Check Redis is running
redis-cli ping  # Should return PONG

# Start Redis if not running
redis-server

# Check REDIS_URL in .env
```

### Frontend Issues

#### "npm install fails"
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and package-lock.json
rm -rf node_modules package-lock.json

# Reinstall
npm install

# If still fails, try with legacy peer deps
npm install --legacy-peer-deps
```

#### "Port 5173 already in use"
```bash
# Kill process on port 5173 (Windows)
netstat -ano | findstr :5173
taskkill /PID <PID> /F

# Or use different port
npm run dev -- --port 5174
```

#### "CORS errors"
```bash
# Ensure django-cors-headers is installed
pip install django-cors-headers

# Check settings.py has CORS configuration
# CORS_ALLOWED_ORIGINS = ['http://localhost:5173']
```

#### "API requests fail"
```bash
# Check VITE_API_BASE_URL in frontend/.env
# Should be: http://localhost:8000/api/v1

# Check backend is running
curl http://localhost:8000/api/v1/health

# Check browser console for errors
# Open DevTools (F12) > Console tab
```

### Database Issues

#### "Too many connections"
```bash
# Check active connections
psql -U postgres
SELECT count(*) FROM pg_stat_activity;

# Kill idle connections
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle';
```

#### "Migrations out of sync"
```bash
# Reset migrations (WARNING: Development only)
python manage.py migrate --fake core zero
python manage.py migrate
```

---

## Environment Variables

### Backend (.env)

```env
# Django Core
DEBUG=True
SECRET_KEY=django-insecure-dev-key-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
DJANGO_SETTINGS_MODULE=openshiksha.settings.development

# Database
DATABASE_URL=postgresql://openshiksha:password@localhost:5432/openshiksha_dev
DB_CONN_MAX_AGE=600

# Redis & Celery
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Cabinet Service
CABINET_API_URL=http://localhost:9000
CABINET_API_KEY=dev-cabinet-key-12345
CABINET_TIMEOUT=30

# JWT Authentication
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_LIFETIME=3600
JWT_REFRESH_TOKEN_LIFETIME=604800

# Email
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=localhost
EMAIL_PORT=25

# Logging
LOG_LEVEL=DEBUG
LOG_FILE=logs/openshiksha.log

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# Media & Static Files
MEDIA_URL=/media/
MEDIA_ROOT=media/
STATIC_URL=/static/
STATIC_ROOT=staticfiles/

# Feature Flags
ENABLE_DEBUG_TOOLBAR=True
ENABLE_SILK_PROFILER=False
```

### Frontend (.env)

```env
# API
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_API_TIMEOUT=30000

# WebSocket
VITE_WS_URL=ws://localhost:8000/ws

# Cabinet
VITE_CABINET_URL=http://localhost:9000

# Authentication
VITE_JWT_STORAGE_KEY=openshiksha_jwt_token
VITE_REFRESH_TOKEN_STORAGE_KEY=openshiksha_refresh_token

# Features
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_NOTIFICATIONS=true
VITE_ENABLE_DEBUG_MODE=true

# Environment
VITE_ENV=development
VITE_APP_NAME=OpenShiksha
VITE_APP_VERSION=2.0.0-dev

# Sentry (error tracking - optional)
VITE_SENTRY_DSN=
VITE_SENTRY_ENVIRONMENT=development
```

---

## Health Checks

### Backend Health

```bash
# API health endpoint
curl http://localhost:8000/api/v1/health

# Expected response:
# {"status": "healthy", "database": "connected", "redis": "connected"}

# Admin interface
# Open: http://localhost:8000/admin
# Login with superuser credentials
```

### Frontend Health

```bash
# Frontend should load at
# http://localhost:5173

# Check console for errors
# Open browser DevTools (F12)
```

### Database Health

```bash
# Check PostgreSQL
pg_isready

# Connect and query
psql -U openshiksha -d openshiksha_dev -c "SELECT COUNT(*) FROM core_user;"
```

### Redis Health

```bash
# Check Redis
redis-cli ping
# Should return: PONG
```

---

## Next Steps

1. **Verify all services are running**
2. **Access backend admin**: http://localhost:8000/admin
3. **Access frontend**: http://localhost:5173
4. **Create test data** using admin interface
5. **Test API endpoints** using Postman/Thunder Client
6. **Start development** following the implementation plan

---

## Useful URLs

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:5173 | React application |
| Backend API | http://localhost:8000/api/v1 | REST API endpoints |
| Admin Interface | http://localhost:8000/admin | Django admin |
| API Documentation | http://localhost:8000/api/docs | Swagger/OpenAPI docs |
| Celery Flower | http://localhost:5555 | Task queue monitoring |

---

## Getting Help

If you encounter issues:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review error logs:
   - Backend: `backend/logs/openshiksha.log`
   - Frontend: Browser console (F12)
3. Ask Claude Code for help with specific errors
4. Check the implementation tracker for known issues

---

**You're ready to develop! 🚀**

For the next steps, see the [Implementation Tracker](C:\Users\shara\.claude\plans\IMPLEMENTATION_TRACKER.md).
