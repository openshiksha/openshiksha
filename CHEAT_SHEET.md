# OpenShiksha - Quick Reference Cheat Sheet

Essential commands for daily development. Keep this handy!

## 🚀 Start Everything (Choose One Method)

### Option 1: Docker Compose (Easiest)
```bash
docker-compose up          # Start all services
docker-compose down        # Stop all services
docker-compose logs -f     # View logs
```

### Option 2: Manual (6 Terminals)

**Terminal 1** - PostgreSQL
```bash
# Usually runs as background service, nothing needed
```

**Terminal 2** - Redis
```bash
redis-server
```

**Terminal 3** - Django Backend
```bash
cd backend
venv\Scripts\activate
python manage.py runserver
```

**Terminal 4** - Celery Worker
```bash
cd backend
venv\Scripts\activate
celery -A openshiksha worker -l info
```

**Terminal 5** - Celery Beat
```bash
cd backend
venv\Scripts\activate
celery -A openshiksha beat -l info
```

**Terminal 6** - React Frontend
```bash
cd frontend
npm run dev
```

---

## 🔥 Most Used Commands

### Backend (Django)
```bash
# Daily workflow
python manage.py runserver              # Start server
python manage.py makemigrations         # Create migrations
python manage.py migrate                # Apply migrations
python manage.py test                   # Run tests
python manage.py shell                  # Django shell

# Common tasks
python manage.py createsuperuser        # Create admin
python manage.py loaddata fixtures/*.json   # Load test data
python manage.py dbshell                # Database shell
```

### Frontend (React)
```bash
# Daily workflow
npm run dev                 # Start dev server
npm run build               # Build for production
npm run test                # Run tests
npm run lint                # Check code style

# Fixes
npm run lint:fix            # Auto-fix linting
npm run format              # Format code
```

### Database (PostgreSQL)
```bash
# Connect
psql -U openshiksha -d openshiksha_dev

# Useful queries (in psql)
\dt                         # List tables
\d core_question            # Describe table
SELECT * FROM core_user LIMIT 10;   # Query data
\q                          # Quit

# Backup/Restore
pg_dump openshiksha_dev > backup.sql    # Backup
psql openshiksha_dev < backup.sql       # Restore
```

### Redis
```bash
redis-cli                   # Connect to Redis
PING                        # Test (should return PONG)
KEYS *                      # List all keys
FLUSHALL                    # Clear all data (careful!)
exit                        # Quit
```

---

## 📦 Package Management

### Python
```bash
pip install package-name            # Install package
pip install -r requirements.txt    # Install all deps
pip freeze > requirements.txt      # Save current deps
pip list                            # List installed
```

### Node.js
```bash
npm install                     # Install all deps
npm install package-name        # Install package
npm install -D package-name     # Install dev dependency
npm update                      # Update packages
npm list --depth=0              # List installed
```

---

## 🔍 Debugging

### View Logs
```bash
# Backend logs
tail -f backend/logs/openshiksha.log

# Frontend (browser console)
# Open DevTools: F12 > Console tab

# Celery logs
# Shown in terminal where celery worker runs
```

### Check Service Status
```bash
# PostgreSQL
pg_isready

# Redis
redis-cli ping

# Backend API
curl http://localhost:8000/api/v1/health

# Frontend
# Open http://localhost:5173 in browser
```

### Kill Stuck Processes
```bash
# Windows
netstat -ano | findstr :8000        # Find PID
taskkill /PID <number> /F           # Kill process

# Linux/Mac
lsof -ti:8000 | xargs kill -9       # Kill port 8000
```

---

## 🧪 Testing

### Backend Tests
```bash
# All tests
python manage.py test

# Specific app
python manage.py test core

# Specific test file
python manage.py test core.tests.test_constraints

# With coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Creates htmlcov/index.html
```

### Frontend Tests
```bash
# Unit tests
npm run test

# Watch mode
npm run test:watch

# E2E tests
npm run test:e2e

# Coverage
npm run test:coverage
```

---

## 🗃️ Database Operations

### Migrations
```bash
# Create migration
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show migration status
python manage.py showmigrations

# Rollback one migration
python manage.py migrate core 0003  # Roll back to migration 0003

# Reset app migrations (DANGER!)
python manage.py migrate core zero
python manage.py migrate core
```

### Data Management
```bash
# Export data
python manage.py dumpdata core.Question --indent 2 > questions.json

# Import data
python manage.py loaddata questions.json

# Flush database (DANGER! Deletes all data)
python manage.py flush

# Create sample data
python manage.py shell < scripts/create_sample_data.py
```

---

## 🔐 User Management

### Django Admin
```bash
# Create superuser
python manage.py createsuperuser

# Change password
python manage.py changepassword username

# Create user via shell
python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> user = User.objects.create_user('john', 'john@example.com', 'password123')
```

---

## 🌐 API Testing

### Using cURL
```bash
# Health check
curl http://localhost:8000/api/v1/health

# Login (get JWT token)
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Authenticated request
curl http://localhost:8000/api/v1/assignments/ \
  -H "Authorization: Bearer <your-token-here>"

# POST data
curl -X POST http://localhost:8000/api/v1/questions/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Question"}'
```

---

## 🔧 Configuration

### Environment Files
```bash
# Backend
backend/.env

# Frontend
frontend/.env

# Docker
.env (root level for docker-compose)
```

### Quick Edit
```bash
# Edit backend env
notepad backend\.env

# Edit frontend env
notepad frontend\.env
```

---

## 📊 Monitoring

### Celery Tasks
```bash
# View active tasks
celery -A openshiksha inspect active

# View scheduled tasks
celery -A openshiksha inspect scheduled

# Purge all tasks
celery -A openshiksha purge

# Flower monitoring (web UI)
celery -A openshiksha flower
# Access at: http://localhost:5555
```

### Database Performance
```bash
# Connect to psql
psql -U openshiksha -d openshiksha_dev

# View active queries
SELECT pid, query, state, query_start
FROM pg_stat_activity
WHERE state = 'active';

# View table sizes
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## 🐛 Common Fixes

### "Module not found" (Python)
```bash
venv\Scripts\activate
pip install -r requirements.txt
```

### "Module not found" (Node)
```bash
rm -rf node_modules package-lock.json
npm install
```

### "Port already in use"
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Or use different port
python manage.py runserver 8001
npm run dev -- --port 5174
```

### "Database locked" (SQLite) / Connection issues (PostgreSQL)
```bash
# Restart PostgreSQL
# Windows: Services > PostgreSQL > Restart
# Linux: sudo systemctl restart postgresql

# Check connections
psql -U postgres
SELECT count(*) FROM pg_stat_activity;
```

### "CORS errors"
```bash
# Check backend CORS settings
# settings.py should have:
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
]

# Restart backend server
```

### "Redis connection refused"
```bash
# Start Redis
redis-server

# Or check if running
redis-cli ping  # Should return PONG
```

---

## 🎯 URLs to Bookmark

| What | URL |
|------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000/api/v1 |
| Django Admin | http://localhost:8000/admin |
| API Docs | http://localhost:8000/api/docs |
| Celery Monitor | http://localhost:5555 |

---

## 💡 Pro Tips

### Backend
- Use `python manage.py shell_plus` for enhanced shell (if django-extensions installed)
- Add `import pdb; pdb.set_trace()` for debugging
- Use `python manage.py runserver_plus` for better error pages
- Check `backend/logs/` for detailed error logs

### Frontend
- Use React DevTools browser extension
- Use Redux DevTools for state debugging (if using Redux)
- Check Network tab in browser DevTools for API calls
- Use `console.log()` liberally, remove before commit

### Database
- Always backup before major operations
- Use transactions for data modifications
- Index frequently queried fields
- Monitor query performance with `EXPLAIN ANALYZE`

### Git
- Commit often with clear messages
- Create feature branches: `git checkout -b feature/name`
- Update tracker after each task completion
- Push to backup: `git push origin feature/name`

---

## 🆘 Emergency Commands

### Stop Everything
```bash
# Docker
docker-compose down

# Manual
# Press Ctrl+C in all terminal windows

# Kill all Python processes (NUCLEAR OPTION)
# Windows: taskkill /IM python.exe /F
# Linux: pkill -9 python
```

### Reset Everything (Development Only!)
```bash
# Stop all services
docker-compose down -v  # -v removes volumes

# Delete database
psql -U postgres -c "DROP DATABASE openshiksha_dev;"
psql -U postgres -c "CREATE DATABASE openshiksha_dev;"

# Flush Redis
redis-cli FLUSHALL

# Reinstall dependencies
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser

cd ../frontend
rm -rf node_modules
npm install
```

---

## 📖 More Help

- **Full guide**: [LOCAL_DEVELOPMENT.md](./LOCAL_DEVELOPMENT.md)
- **Implementation plan**: [C:\Users\shara\.claude\plans\proud-knitting-sonnet.md](C:\Users\shara\.claude\plans\proud-knitting-sonnet.md)
- **Task tracker**: [C:\Users\shara\.claude\plans\IMPLEMENTATION_TRACKER.md](C:\Users\shara\.claude\plans\IMPLEMENTATION_TRACKER.md)

---

**Print this and keep it next to your monitor! 📌**
