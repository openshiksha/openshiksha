# Setting Up OpenShiksha Modernization Branch

## Current Situation

- **Git Repository**: `OpenShiksha/openshiksha/` (the inner directory)
- **Current Branch**: `qa`
- **Existing Branches**: `qa`, `prod`
- **Created Files**: Currently in `OpenShiksha/` parent directory

## Strategy

We'll create a `modernization` branch in the actual git repo and move the modern structure there, keeping legacy code untouched.

## Step-by-Step Setup

### Step 1: Create Modernization Branch

```bash
# Navigate to git repository
cd "c:\Users\shara\OneDrive\Desktop\My Stuff\Work\Dev\OpenShiksha\openshiksha"

# Create modernization branch from qa
git checkout -b modernization

# Verify branch created
git branch
```

### Step 2: Reorganize Structure

The goal is this structure in the git repo:

```
openshiksha/  (git repository root)
├── legacy/                    # Move old code here for reference
│   ├── core/
│   ├── edge/
│   ├── cabinet/
│   └── ... (all current Django 1.11 code)
│
├── backend/                   # NEW: Modern Django backend
├── frontend/                  # NEW: Modern React frontend
├── docker-compose.yml
├── LOCAL_DEVELOPMENT.md
├── CHEAT_SHEET.md
├── GIT_STRATEGY.md
└── README.md
```

### Step 3: Move Files to Git Repository

```bash
# Still in openshiksha/ directory

# Copy modern files from parent directory
cp -r ../openshiksha-modern/backend ./
cp -r ../openshiksha-modern/frontend ./
cp ../openshiksha-modern/docker-compose.yml ./
cp ../openshiksha-modern/README.md ./README_MODERN.md
cp ../LOCAL_DEVELOPMENT.md ./
cp ../CHEAT_SHEET.md ./
cp ../GIT_STRATEGY.md ./

# Create legacy directory and move old code there
mkdir legacy
mv core legacy/
mv edge legacy/
mv cabinet legacy/
mv focus legacy/
mv ink legacy/
mv lodge legacy/
mv concierge legacy/
mv challenge legacy/
mv croupier legacy/
mv grader legacy/
mv pylon legacy/
mv sphinx legacy/
mv spider legacy/
mv frontend legacy/frontend_old
mv openshiksha legacy/openshiksha_old

# Keep necessary root files
# manage.py stays at root for now
```

**OR** (Cleaner approach - don't move legacy, just add new):

```bash
# Don't move legacy code, just add new structure alongside
cd "c:\Users\shara\OneDrive\Desktop\My Stuff\Work\Dev\OpenShiksha\openshiksha"

# Copy new modern structure
cp -r ../openshiksha-modern/backend ./
cp -r ../openshiksha-modern/frontend ./
cp ../openshiksha-modern/docker-compose.yml ./
cp ../LOCAL_DEVELOPMENT.md ./
cp ../CHEAT_SHEET.md ./
cp ../GIT_STRATEGY.md ./

# Update README
echo "# OpenShiksha - Modernization Branch" > README_MODERNIZATION.md
cat ../openshiksha-modern/README.md >> README_MODERNIZATION.md
```

### Step 4: Update .gitignore

```bash
# Create/update .gitignore in repository root
cat >> .gitignore << 'EOF'

# Modern Backend
backend/venv/
backend/.env
backend/logs/
backend/media/
backend/staticfiles/
backend/__pycache__/
backend/*.pyc
backend/db.sqlite3

# Modern Frontend
frontend/node_modules/
frontend/dist/
frontend/.env
frontend/.env.local

# Docker
docker-compose.override.yml

# Temporary directory
../openshiksha-modern/

# IDEs
.vscode/
.idea/

EOF
```

### Step 5: Commit Modern Structure

```bash
# Check what's new
git status

# Add new files
git add backend/
git add frontend/
git add docker-compose.yml
git add LOCAL_DEVELOPMENT.md
git add CHEAT_SHEET.md
git add GIT_STRATEGY.md
git add README_MODERNIZATION.md
git add .gitignore

# Commit
git commit -m "Phase 0: Initialize modern Django 4.2 + React 18 structure

- Add backend/ with Django 4.2 + DRF setup
- Add frontend/ with React 18 + TypeScript + Vite
- Add Docker Compose for local development
- Add comprehensive development documentation
- Keep legacy code in place for reference

This is the beginning of the 30-week modernization plan.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# Push to remote
git push -u origin modernization
```

### Step 6: Verify Setup

```bash
# Check branch
git branch

# Should show:
#   qa
# * modernization

# Check files
ls -la

# Should see both legacy and new:
# - core/, edge/, cabinet/ (legacy Django 1.11 apps)
# - backend/ (new Django 4.2)
# - frontend/ (new React 18)
```

## Alternative: Feature Branch Approach

If you want to be extra safe, create a feature branch first:

```bash
cd "c:\Users\shara\OneDrive\Desktop\My Stuff\Work\Dev\OpenShiksha\openshiksha"

# Create feature branch from qa
git checkout qa
git checkout -b feature/phase-0-modernization-setup

# Add modern structure
# ... (copy files as above)

# Commit
git add .
git commit -m "Phase 0: Add modern project structure"

# Push
git push -u origin feature/phase-0-modernization-setup

# Create PR on GitHub:
# feature/phase-0-modernization-setup → qa (or create modernization branch first)
```

## Cleaning Up

After files are in git repo, remove temporary directory:

```bash
# From parent directory
cd "c:\Users\shara\OneDrive\Desktop\My Stuff\Work\Dev\OpenShiksha"
rm -rf openshiksha-modern/
```

## Directory Structure After Setup

```
OpenShiksha/
├── openshiksha/  (git repo - on modernization branch)
│   ├── core/              # Legacy Django 1.11 (untouched)
│   ├── edge/              # Legacy analytics
│   ├── cabinet/           # Legacy cabinet
│   ├── ... (other legacy apps)
│   ├── backend/           # NEW: Modern Django 4.2
│   │   ├── openshiksha/
│   │   ├── apps/
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── frontend/          # NEW: Modern React 18
│   │   ├── src/
│   │   ├── package.json
│   │   └── Dockerfile
│   ├── docker-compose.yml
│   ├── LOCAL_DEVELOPMENT.md
│   ├── CHEAT_SHEET.md
│   ├── GIT_STRATEGY.md
│   └── README_MODERNIZATION.md
│
└── .claude/
    └── plans/
        ├── proud-knitting-sonnet.md
        ├── IMPLEMENTATION_TRACKER.md
        └── ...
```

## Quick Commands

```bash
# Navigate to git repo
cd "c:\Users\shara\OneDrive\Desktop\My Stuff\Work\Dev\OpenShiksha\openshiksha"

# Create modernization branch
git checkout -b modernization

# Copy modern files (PowerShell)
Copy-Item -Recurse ..\openshiksha-modern\backend .
Copy-Item -Recurse ..\openshiksha-modern\frontend .
Copy-Item ..\openshiksha-modern\docker-compose.yml .
Copy-Item ..\LOCAL_DEVELOPMENT.md .
Copy-Item ..\CHEAT_SHEET.md .
Copy-Item ..\GIT_STRATEGY.md .

# Commit and push
git add backend/ frontend/ *.yml *.md
git commit -m "Phase 0: Initialize modern structure"
git push -u origin modernization
```

## Next Steps

1. ✅ Create modernization branch
2. ✅ Add modern structure
3. ✅ Push to GitHub
4. Continue with Phase 0: Set up Django project
5. Create feature branches for each task

---

**Remember**: Work happens in `openshiksha/` directory (the git repo), not the parent!
