# Commit and Push to Dev

## Overview
Commit changes and push to the development branch following project conventions and security best practices.

## Steps
1. **Review changes**
   - Check git status for modified files
   - Review diffs to ensure no secrets
   - Verify tests pass locally

2. **Stage changes**
   - Stage all: `git add .`
   - Stage specific: `git add <files>`
   - Stage by service: `git add shared-auth/`

3. **Commit with message**
   - Use conventional commits format
   - Include clear description
   - Reference issue numbers if applicable

4. **Push to dev**
   - Push changes: `git push origin dev`
   - Handle conflicts if needed
   - Monitor GitHub Actions

## Commit Message Format
```
<type>: <description>

[optional body]
[optional footer]
```

**Types:**
- `feat:` - New features
- `fix:` - Bug fixes  
- `docs:` - Documentation
- `refactor:` - Code restructuring
- `test:` - Adding tests
- `security:` - Security improvements
- `chore:` - Maintenance

## Pre-Commit Checklist
- [ ] No secrets (API keys, passwords, tokens)
- [ ] Tests pass (`pytest` for affected services)
- [ ] Code formatted (Black, isort)
- [ ] Linting clean (flake8, mypy)
- [ ] Documentation updated
- [ ] Proper commit message format
- [ ] Changes reviewed with `git diff`

## Quick Commands
```bash
# Full workflow
git add . && git commit -m "feat: description" && git push origin dev

# Check what's staged
git diff --cached

# Amend last commit
git commit --amend -m "updated message"

# Handle push rejection
git pull origin dev && git push origin dev
```

## Troubleshooting
**Push rejected:** Pull latest changes first
```bash
git pull origin dev
git push origin dev
```

**Merge conflicts:** Resolve manually, then commit
```bash
# Edit conflicted files
git add <resolved-files>
git commit -m "merge: resolve conflicts"
git push origin dev
```

**Undo last commit:** Keep changes but undo commit
```bash
git reset --soft HEAD~1
```