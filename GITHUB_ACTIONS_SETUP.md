# GitHub Actions Setup for Monorepo

## 🔧 **Issues Fixed**

### **Issue 1: Incorrect Workflow Location** ❌ → ✅
- **Problem**: GitHub workflows were in `shared-auth/.github/workflows/`
- **Solution**: Moved to repository root `.github/workflows/`
- **Why**: GitHub Actions **must** be at the repository root, not in subdirectories

### **Issue 2: Wrong Branch Configuration** ❌ → ✅
- **Problem**: Workflows configured for `main` branch
- **Solution**: Changed to trigger on `dev` branch
- **Why**: Your development branch is `dev`, not `main`

## 📁 **New Workflow Structure**

```
resume_match_pro_v2/
├── .github/
│   └── workflows/
│       └── shared-auth-release.yml   # Single comprehensive workflow
├── shared-auth/
│   ├── src/
│   ├── tests/
│   ├── VERSION                       # Single version file (e.g., "0.1.0")
│   └── pyproject.toml
└── other-services/
```

## 🚀 **Single Comprehensive Workflow**

### **Shared Auth CI/CD** (`shared-auth-release.yml`)
- **Triggers**: 
  - Push to `dev` branch (auto-publish)
  - Pull requests to `dev` (test only)
  - Manual dispatch (with options)
- **Jobs**:
  1. **Test**: Linting, testing, coverage (Python 3.11 & 3.12)
  2. **Build & Publish**: Version bump, build, publish (only on push/manual)
- **Versioning**: Single `VERSION` file with full semantic version

## 🎯 **How to Use**

### **Automatic Triggers**
```bash
# This will trigger workflows automatically:
git add .
git commit -m "feat: add new authentication feature"
git push origin dev
```

### **Manual Triggers**
Go to GitHub → Actions → Select workflow → "Run workflow"

### **Version Management Options**

#### **Option A: Simple Versioning**
- Uses `shared-auth-publish.yml`
- Choose patch/minor/major bump manually
- Version stored in `pyproject.toml`

#### **Option B: Hybrid Versioning** (Your Current System)
- Uses `shared-auth-release.yml`
- Major version in `MAJOR_VERSION` file (manual)
- Minor version auto-increments on each release
- Patch version always 0

## 🔍 **Troubleshooting**

### **Workflows Not Running?**
1. ✅ Check workflows are in `.github/workflows/` at repo root
2. ✅ Check branch name matches (`dev` not `main`)
3. ✅ Check file paths in trigger conditions
4. ✅ Verify GitHub Actions are enabled in repo settings

### **Publishing Issues?**
1. **PyPI**: Add `PYPI_API_TOKEN` secret in GitHub repo settings
2. **GitHub Packages**: Uses `GITHUB_TOKEN` (automatic)
3. **Permissions**: Workflows have `contents: write` and `packages: write`

### **Path Filtering**
Workflows only trigger when files in `shared-auth/` change:
```yaml
paths:
  - 'shared-auth/**'
```

## 📦 **Package Publishing**

### **Where Packages Go**
- **PyPI**: `pip install resume-match-shared-auth`
- **GitHub Packages**: Configure pip to use GitHub registry

### **Installation After Publishing**
```bash
# From PyPI
pip install resume-match-shared-auth==0.1.0

# From GitHub Packages  
pip install --index-url https://pypi.org/simple/ resume-match-shared-auth==0.1.0
```

## ✅ **Next Steps**

1. **Commit these workflow files**:
   ```bash
   git add .github/
   git commit -m "fix: move GitHub Actions to repository root for monorepo"
   git push origin dev
   ```

2. **Check GitHub Actions tab** in your repository

3. **Add PyPI token** (optional):
   - Go to GitHub repo → Settings → Secrets → Actions
   - Add `PYPI_API_TOKEN` if you want to publish to PyPI

4. **Test the workflow**:
   - Make a small change to `shared-auth/`
   - Commit and push to `dev`
   - Check GitHub Actions tab for running workflows

The workflows should now trigger correctly when you push changes to the `shared-auth/` directory on the `dev` branch! 🎉
