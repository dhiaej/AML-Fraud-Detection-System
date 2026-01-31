# GitHub Setup Guide

## Quick Start

### 1. Initialize Git Repository (if not already done)
```bash
cd money-laundering-detection
git init
```

### 2. Add All Files
```bash
git add .
```

### 3. Create Initial Commit
```bash
git commit -m "Initial commit: AML Fraud Detection System"
```

### 4. Create GitHub Repository
1. Go to https://github.com/new
2. Repository name: `aml-fraud-detection` (or your preferred name)
3. Description: Use the description provided below
4. Choose Public or Private
5. **DO NOT** initialize with README, .gitignore, or license (we already have these)
6. Click "Create repository"

### 5. Connect and Push
```bash
git remote add origin https://github.com/YOUR_USERNAME/aml-fraud-detection.git
git branch -M main
git push -u origin main
```

## Repository Title
**AML Fraud Detection System**

## Repository Description
```
A high-fidelity Anti-Money Laundering (AML) detection platform powered by Graph Neural Networks (GNNs) with real-time transaction monitoring, risk scoring, and explainable AI decision support. Built with FastAPI, React, TypeScript, and PyTorch Geometric.
```

## Tags/Topics (add these on GitHub)
- `anti-money-laundering`
- `fraud-detection`
- `graph-neural-networks`
- `fastapi`
- `react`
- `typescript`
- `machine-learning`
- `financial-technology`
- `aml-compliance`
- `transaction-monitoring`

## Files to Remove Before Pushing

The `.gitignore` file will automatically exclude:
- `__pycache__/` directories
- `*.db` database files
- `node_modules/`
- `*.log` files
- Other temporary files

**Manual cleanup (optional):**
```bash
# Remove old documentation if desired
# rm PROJECT_DOCUMENTATION.txt

# Remove redundant seed script if desired
# rm data/seed_database.py
```

## Verify Before Pushing

1. Check what will be committed:
   ```bash
   git status
   ```

2. Review the .gitignore is working:
   ```bash
   git status --ignored
   ```

3. Make sure sensitive data is not included:
   - No `.env` files
   - No database files with real data
   - No API keys or secrets

## After Pushing

1. Add a repository description on GitHub
2. Add topics/tags
3. Enable GitHub Pages (optional) for documentation
4. Set up branch protection (optional)
5. Add collaborators (optional)
