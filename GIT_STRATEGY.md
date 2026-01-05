# OpenShiksha Modernization - Git Branching Strategy

## Overview

The modernization will happen on a dedicated `modernization` branch, keeping the legacy Python 2.7 code on `main` branch until the modern version is production-ready.

## Branch Structure

```
main (legacy Django 1.11/Python 2.7)
  │
  └── modernization (Django 4.2/Python 3.11 + React 18)
       │
       ├── feature/phase-0-setup
       ├── feature/phase-1-api
       ├── feature/phase-2-student-frontend
       └── ... (feature branches for each phase)
```

## Branching Strategy

### Main Branches

1. **`main`** (protected)
   - Legacy codebase (Django 1.11/Python 2.7)
   - Keep for reference and emergency hotfixes
   - **DO NOT delete or modify** during modernization
   - Read-only during modernization period

2. **`modernization`** (protected)
   - Base branch for all modern development
   - Django 4.2 + Python 3.11 + React 18
   - All new code goes here
   - Will eventually replace `main` when complete

### Feature Branches

Create feature branches off `modernization` for each phase/task:

```bash
# Pattern: feature/phase-X-description
feature/phase-0-setup
feature/phase-1-auth
feature/phase-1-questions
feature/phase-2-student-ui
feature/phase-3-teacher-ui
etc.
```

## Initial Setup

### Step 1: Check Current Branch

```bash
cd "c:\Users\shara\OneDrive\Desktop\My Stuff\Work\Dev\OpenShiksha"
git status
git branch -a
```

### Step 2: Create Modernization Branch

```bash
# Create and switch to modernization branch
git checkout -b modernization

# Verify you're on the new branch
git branch
```

### Step 3: Set Up Modern Structure

The modern structure will coexist with legacy:

```
OpenShiksha/
├── openshiksha/          # Legacy code (untouched on modernization branch)
├── backend/              # NEW: Modern Django backend
├── frontend/             # NEW: Modern React frontend
├── docker-compose.yml    # NEW: Docker setup
├── .env.example          # NEW: Environment template
├── LOCAL_DEVELOPMENT.md  # NEW: Dev guide
├── CHEAT_SHEET.md        # NEW: Quick reference
└── README.md             # UPDATE: Point to modernization
```

### Step 4: Add New Files

```bash
# Check what's new
git status

# Add new files (do NOT add openshiksha-modern directory)
git add backend/
git add frontend/
git add docker-compose.yml
git add LOCAL_DEVELOPMENT.md
git add CHEAT_SHEET.md
git add GIT_STRATEGY.md

# Commit
git commit -m "Phase 0: Initialize modern project structure

- Add Django 4.2 backend setup
- Add React 18 + TypeScript frontend setup
- Add Docker Compose configuration
- Add development documentation

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# Push to remote
git push -u origin modernization
```

## Development Workflow

### Starting New Work

```bash
# Always start from modernization branch
git checkout modernization
git pull origin modernization

# Create feature branch
git checkout -b feature/phase-0-docker-setup

# Work on your feature...
# Make commits...

# Push feature branch
git push -u origin feature/phase-0-docker-setup
```

### Committing Changes

Follow this commit message format:

```
Phase X: Brief description

- Detailed change 1
- Detailed change 2
- Detailed change 3

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

### Merging Features

```bash
# From feature branch, update with latest modernization
git checkout feature/phase-0-docker-setup
git pull origin modernization
git merge modernization

# Resolve any conflicts
# Run tests
# Push

# Create Pull Request: feature/phase-0-docker-setup → modernization
```

### Pull Request Process

1. **Create PR** from feature branch → `modernization`
2. **Review** changes
3. **Run tests** (CI/CD will auto-run)
4. **Merge** to modernization
5. **Delete** feature branch

## Directory Structure on Modernization Branch

```
OpenShiksha/
│
├── openshiksha/                    # LEGACY (reference only)
│   ├── core/
│   ├── edge/
│   ├── cabinet/
│   └── ... (old Django 1.11 code)
│
├── backend/                        # NEW: Modern Django backend
│   ├── openshiksha/               # Django project
│   │   ├── settings/
│   │   │   ├── base.py
│   │   │   ├── development.py
│   │   │   └── production.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── apps/                      # Django apps
│   │   ├── core/                  # Modernized core
│   │   ├── edge/                  # Modernized analytics
│   │   ├── cabinet/               # Modernized cabinet integration
│   │   └── api/                   # REST API
│   ├── manage.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── frontend/                       # NEW: React frontend
│   ├── src/
│   │   ├── features/
│   │   │   ├── assignments/
│   │   │   ├── analytics/
│   │   │   ├── questions/
│   │   │   └── auth/
│   │   ├── shared/
│   │   ├── types/
│   │   └── App.tsx
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── Dockerfile
│   └── .env.example
│
├── docs/                           # Documentation
├── scripts/                        # Utility scripts
├── .github/                        # CI/CD workflows
├── docker-compose.yml
├── .gitignore
├── LOCAL_DEVELOPMENT.md
├── CHEAT_SHEET.md
├── GIT_STRATEGY.md
└── README.md                       # Updated for modernization
```

## Important Rules

### ✅ DO

- Create all new code in `backend/` and `frontend/` directories
- Work on feature branches off `modernization`
- Keep `openshiksha/` legacy directory untouched (reference only)
- Update tracker after each task
- Write clear commit messages with phase context
- Push regularly to backup work

### ❌ DON'T

- **Don't modify** legacy `openshiksha/` code on modernization branch
- **Don't merge** modernization into main until fully complete
- **Don't delete** legacy code (keep for reference)
- **Don't work directly** on modernization branch (use feature branches)
- **Don't force push** to protected branches

## Migration to Production

When modernization is complete (Phase 6):

### Option 1: Replace Main (Recommended)

```bash
# Backup old main
git checkout main
git tag legacy-backup
git push origin legacy-backup

# Replace main with modernization
git checkout modernization
git merge -s ours main  # Keep modernization code
git checkout main
git merge modernization
git push origin main

# Archive legacy
git tag legacy-django-1.11
git push origin legacy-django-1.11
```

### Option 2: Parallel Deployment

Keep both branches and deploy from `modernization`:

```bash
# Production deploys from modernization branch
git checkout modernization
git pull origin modernization
# Deploy...

# Legacy remains on main for emergency reference
```

## .gitignore Updates

Make sure `.gitignore` includes:

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
.env
*.log

# Django
db.sqlite3
/media/
/staticfiles/
/logs/

# Node
node_modules/
dist/
build/
.npm
*.log

# IDEs
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Docker
docker-compose.override.yml

# Temporary
*.tmp
*.bak
openshiksha-modern/  # Remove this temp directory
```

## Emergency Rollback

If something goes wrong:

```bash
# List all branches
git branch -a

# Switch back to legacy
git checkout main

# Or restore from backup
git checkout legacy-backup
```

## Branch Protection Rules (GitHub)

Configure on GitHub repository settings:

### `main` branch:
- ✅ Require pull request reviews
- ✅ Require status checks to pass
- ✅ Require branches to be up to date
- ✅ Include administrators
- ❌ Allow force pushes

### `modernization` branch:
- ✅ Require pull request reviews
- ✅ Require status checks to pass
- ✅ Require branches to be up to date
- ✅ Include administrators
- ❌ Allow force pushes

## Quick Reference

```bash
# Start new feature
git checkout modernization && git pull
git checkout -b feature/phase-X-name

# Daily work
git add .
git commit -m "Phase X: Description"
git push

# Update from modernization
git pull origin modernization

# Create PR (on GitHub)
feature/phase-X-name → modernization

# After merge
git checkout modernization
git pull
git branch -d feature/phase-X-name
```

## Current Status

- **Active Branch**: `modernization`
- **Current Phase**: Phase 0 - Preparation
- **Next**: Create feature branch for Phase 0 setup

---

**Remember**: Legacy code stays on `main`, all modern code goes on `modernization` branch! 🚀
