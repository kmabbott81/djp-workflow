# Release Management Guide

Comprehensive guide for cutting releases, building artifacts, and managing the release lifecycle for DJP Workflow Platform.

## Overview

The release process follows semantic versioning (SemVer) with automated CI/CD pipelines for build, test, and deployment.

**Release types:**
- **Patch** (x.y.Z): Bug fixes, security patches
- **Minor** (x.Y.0): New features, backward compatible
- **Major** (X.0.0): Breaking changes, API incompatibilities

## Release Roles & Responsibilities

**Release Manager:**
- Coordinates release process
- Creates version tags
- Publishes GitHub releases
- Communicates with stakeholders

**Developers:**
- Submit pull requests
- Fix release-blocking bugs
- Write tests
- Update documentation

**QA/Testing:**
- Run full test suites
- Validate smoke tests
- Verify upgrade paths
- Report release-blocking issues

**DevOps:**
- Build Docker images
- Push to registry
- Deploy to environments
- Monitor deployments

## Release Versioning

### Semantic Versioning

Format: `MAJOR.MINOR.PATCH`

**Examples:**
- `1.0.0` → `1.0.1` (patch: bug fix)
- `1.0.1` → `1.1.0` (minor: new feature)
- `1.1.0` → `2.0.0` (major: breaking change)

### Version Files

Version numbers are maintained in:
- `pyproject.toml` - Python package version
- `src/__init__.py` - Runtime version
- `CHANGELOG.md` - Release history

### Version Script

Use the version script to update all version files consistently:

```bash
# Patch release: 1.0.0 → 1.0.1
python scripts/version.py --patch

# Minor release: 1.0.1 → 1.1.0
python scripts/version.py --minor

# Major release: 1.1.0 → 2.0.0
python scripts/version.py --major

# Set specific version
python scripts/version.py --set 2.5.3
```

**Automatic updates:**
- Updates `pyproject.toml`
- Updates `src/__init__.py`
- Creates placeholder in `CHANGELOG.md`
- Commits changes with message `chore(release): bump version to X.Y.Z`

## Release Preparation

### 1. Create Release Branch

For major/minor releases, create a release branch:

```bash
# Create release branch
git checkout -b release/v1.1.0

# Push to remote
git push origin release/v1.1.0
```

For patch releases, work directly on `main` or cherry-pick fixes.

### 2. Update Version

```bash
# Bump version (patch/minor/major)
python scripts/version.py --minor

# Verify version updated
grep '^version' pyproject.toml
grep '__version__' src/__init__.py
```

### 3. Update CHANGELOG.md

Edit `CHANGELOG.md` with release notes:

```markdown
## [1.1.0] - 2025-10-15

### Added
- Multi-connector support for Slack, Teams, Outlook
- Unified Resource Graph (URG) for cross-platform search
- Natural language commanding system

### Changed
- Improved RBAC with collaborative governance
- Enhanced observability and monitoring

### Fixed
- Circuit breaker state persistence in Slack connector
- URG test isolation issues

### Security
- Encryption key rotation procedures
- API key management improvements
```

**Changelog format:**
- Follow [Keep a Changelog](https://keepachangelog.com/)
- Organize by: Added, Changed, Deprecated, Removed, Fixed, Security
- Use clear, user-focused language
- Link to relevant documentation

### 4. Generate Release Notes

Generate detailed release notes:

```bash
# Generate from CHANGELOG
python scripts/release_notes.py --latest --output .release_notes_v1.1.0.md

# Review generated notes
cat .release_notes_v1.1.0.md
```

**Release notes include:**
- Summary of changes
- Breaking changes (if any)
- Upgrade instructions
- Known issues
- Contributors

### 5. Run Pre-Release Checks

Execute all quality gates:

```bash
# 1. Linting and formatting
pre-commit run --all-files

# 2. Type checking
mypy src/

# 3. Unit tests
pytest tests/ -v

# 4. Integration tests
pytest tests_integration/ -v

# 5. Smoke tests
pytest -m e2e

# 6. Schema validation
python scripts/validate_artifacts.py

# 7. Configuration validation
python -m src.config.validate

# 8. Security scan (if available)
bandit -r src/
```

**All checks must pass before proceeding.**

### 6. Update Documentation

Review and update documentation:

```bash
# Check for TODO/FIXME in docs
grep -r "TODO\|FIXME" docs/

# Verify all links work
markdown-link-check docs/**/*.md

# Update version references in docs
grep -r "0.34" docs/ | grep -v UPGRADE.md
# (Update any references to old version)
```

### 7. Build and Test Packages

Build distribution packages:

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info/

# Build packages
python -m build

# Verify build output
ls -lh dist/
# Expected:
#   djp_workflow-1.1.0.tar.gz (source distribution)
#   djp_workflow-1.1.0-py3-none-any.whl (wheel)
```

**Test packages:**

```bash
# Create temporary virtual environment
python -m venv .tmp-venv
source .tmp-venv/bin/activate  # Linux/macOS
# .tmp-venv\Scripts\activate    # Windows

# Install wheel
pip install dist/djp_workflow-1.1.0-py3-none-any.whl

# Verify version
python -c "import src; print('Version:', src.__version__)"
# Expected: Version: 1.1.0

# Test import
python -c "from src.run_workflow import main; print('Import successful')"

# Deactivate and cleanup
deactivate
rm -rf .tmp-venv
```

## Cutting a Release

### 1. Merge Release Branch

Merge release branch to `main`:

```bash
# Switch to main
git checkout main

# Merge release branch
git merge --no-ff release/v1.1.0 -m "Release v1.1.0"

# Push to remote
git push origin main
```

### 2. Create Version Tag

Tag the release commit:

```bash
# Create annotated tag
git tag -a v1.1.0 -m "Release v1.1.0

Highlights:
- Multi-connector support
- Unified Resource Graph
- Natural language commanding
- Enhanced RBAC and governance

Full changelog: https://github.com/kmabbott81/djp-workflow/blob/main/CHANGELOG.md
"

# Verify tag
git tag -l -n5 v1.1.0

# Push tag to remote
git push origin v1.1.0
```

**Tag naming convention:**
- Format: `vX.Y.Z` (with 'v' prefix)
- Examples: `v1.0.0`, `v1.1.0`, `v2.0.0`

### 3. GitHub Actions Workflow

Pushing the tag triggers the automated release workflow (`.github/workflows/release.yml`):

**Workflow steps:**
1. Checkout code with full history
2. Set up Python 3.11 environment
3. Install build dependencies
4. Install project dependencies
5. Run full test suite (pytest)
6. Build sdist and wheel packages
7. Validate distributions (twine check)
8. Upload build artifacts (30-day retention)
9. Generate release notes from CHANGELOG
10. Create draft GitHub Release with:
    - Release notes
    - Attached sdist and wheel files
    - Version tag reference
    - Pre-release flag (if applicable)

**Monitor workflow:**
- Visit: `https://github.com/kmabbott81/djp-workflow/actions`
- Check for green ✅ (success) or red ❌ (failure)
- Review logs if workflow fails

### 4. Review Draft Release

Navigate to GitHub Releases:

```
https://github.com/kmabbott81/djp-workflow/releases
```

**Verify draft release:**
- [ ] Correct version number in title
- [ ] Release notes accurate and complete
- [ ] Attached files present:
  - [ ] `djp_workflow-X.Y.Z.tar.gz` (source distribution)
  - [ ] `djp_workflow-X.Y.Z-py3-none-any.whl` (Python wheel)
- [ ] Tag points to correct commit
- [ ] Target branch is `main`
- [ ] Pre-release flag correct (if beta/rc)

**Edit if needed:**
- Click "Edit" to modify release notes
- Add additional context or breaking changes
- Fix formatting issues

### 5. Publish Release

Once verified, publish the release:

1. Click "Publish release" button
2. Release becomes public immediately
3. GitHub sends notifications to watchers
4. Release appears in repository sidebar
5. Tag is permanently associated with release

## Building Docker Images

### 1. Build Images

Build Docker images for the release:

```bash
# Navigate to docker directory
cd docker

# Build app image
docker build -f Dockerfile.app -t djp-workflow-app:1.1.0 ..

# Build worker image
docker build -f Dockerfile.worker -t djp-workflow-worker:1.1.0 ..

# Tag as latest
docker tag djp-workflow-app:1.1.0 djp-workflow-app:latest
docker tag djp-workflow-worker:1.1.0 djp-workflow-worker:latest
```

### 2. Test Images

Test Docker images locally:

```bash
# Start services with new images
docker-compose -f docker/docker-compose.yml up -d --scale worker=2

# Check services
docker-compose -f docker/docker-compose.yml ps

# Test health endpoints
curl http://localhost:8080/health
# Expected: {"status": "healthy", "version": "1.1.0"}

curl http://localhost:8080/ready
# Expected: {"status": "ready", ...}

# Test workflow execution
docker-compose -f docker/docker-compose.yml exec app \
  python -m src.run_workflow --task "Test Docker image"

# Check logs
docker-compose -f docker/docker-compose.yml logs app
docker-compose -f docker/docker-compose.yml logs worker

# Stop services
docker-compose -f docker/docker-compose.yml down
```

### 3. Push to Registry

Push images to Docker registry:

**Docker Hub:**
```bash
# Login to Docker Hub
docker login -u username

# Tag images
docker tag djp-workflow-app:1.1.0 username/djp-workflow-app:1.1.0
docker tag djp-workflow-app:1.1.0 username/djp-workflow-app:latest
docker tag djp-workflow-worker:1.1.0 username/djp-workflow-worker:1.1.0
docker tag djp-workflow-worker:1.1.0 username/djp-workflow-worker:latest

# Push images
docker push username/djp-workflow-app:1.1.0
docker push username/djp-workflow-app:latest
docker push username/djp-workflow-worker:1.1.0
docker push username/djp-workflow-worker:latest
```

**Private Registry:**
```bash
# Login to private registry
docker login registry.example.com

# Tag images
docker tag djp-workflow-app:1.1.0 registry.example.com/djp-workflow-app:1.1.0
docker tag djp-workflow-app:1.1.0 registry.example.com/djp-workflow-app:latest

# Push images
docker push registry.example.com/djp-workflow-app:1.1.0
docker push registry.example.com/djp-workflow-app:latest
```

**AWS ECR:**
```bash
# Authenticate with ECR
aws ecr get-login-password --region us-west-2 | \
  docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-west-2.amazonaws.com

# Tag images
docker tag djp-workflow-app:1.1.0 \
  123456789012.dkr.ecr.us-west-2.amazonaws.com/djp-workflow-app:1.1.0

# Push images
docker push 123456789012.dkr.ecr.us-west-2.amazonaws.com/djp-workflow-app:1.1.0
```

### 4. Verify Registry Push

Verify images are available:

```bash
# Docker Hub
docker pull username/djp-workflow-app:1.1.0

# Private registry
docker pull registry.example.com/djp-workflow-app:1.1.0

# AWS ECR
docker pull 123456789012.dkr.ecr.us-west-2.amazonaws.com/djp-workflow-app:1.1.0
```

## Post-Release Tasks

### 1. Verify Installation

Test installation from published release:

```bash
# Install from GitHub Release
pip install https://github.com/kmabbott81/djp-workflow/releases/download/v1.1.0/djp_workflow-1.1.0-py3-none-any.whl

# Verify version
python -c "import src; print('Version:', src.__version__)"
# Expected: Version: 1.1.0

# Test workflow execution
python -m src.run_workflow --task "Post-release verification" --dry-run
```

### 2. Update Documentation Website

If hosting documentation separately:

```bash
# Build documentation
cd docs
mkdocs build

# Deploy to GitHub Pages
mkdocs gh-deploy

# Or deploy to custom host
rsync -avz site/ user@docs.example.com:/var/www/docs/
```

### 3. Announce Release

**Internal announcement:**
```markdown
Subject: DJP Workflow v1.1.0 Released

Team,

DJP Workflow v1.1.0 is now available!

**Highlights:**
- Multi-connector support (Slack, Teams, Outlook, Gmail, Notion)
- Unified Resource Graph for cross-platform search
- Natural language commanding system
- Enhanced RBAC with collaborative governance

**Upgrade:**
See upgrade guide: https://github.com/kmabbott81/djp-workflow/blob/main/docs/UPGRADE.md

**Documentation:**
- Release notes: https://github.com/kmabbott81/djp-workflow/releases/tag/v1.1.0
- Changelog: https://github.com/kmabbott81/djp-workflow/blob/main/CHANGELOG.md

Please report any issues on GitHub.

Thanks,
Release Team
```

**External announcement:**
- Post on project website
- Share on social media (if applicable)
- Notify dependent projects
- Update integration partners

### 4. Monitor Release

Monitor release adoption and issues:

```bash
# Track GitHub Release downloads
curl -s https://api.github.com/repos/kmabbott81/djp-workflow/releases/tags/v1.1.0 | \
  jq '.assets[] | {name: .name, downloads: .download_count}'

# Monitor issues for release-related bugs
# Visit: https://github.com/kmabbott81/djp-workflow/issues?q=is%3Aissue+label%3Av1.1.0

# Check Docker Hub pull stats (if applicable)
docker pull username/djp-workflow-app:1.1.0
```

### 5. Update Dependent Projects

Notify projects that depend on DJP Workflow:

```markdown
Subject: DJP Workflow v1.1.0 Available

The DJP Workflow team is pleased to announce v1.1.0.

**Key Changes:**
- Multi-connector support
- Unified Resource Graph
- Natural language commanding

**Breaking Changes:** None

**Upgrade Instructions:**
See: https://github.com/kmabbott81/djp-workflow/blob/main/docs/UPGRADE.md

**Contact:**
For questions, contact: support@example.com
```

## Hotfix Process

For critical bugs requiring immediate patch release:

### 1. Create Hotfix Branch

```bash
# Create hotfix branch from tag
git checkout -b hotfix/v1.1.1 v1.1.0

# Or from main if recent
git checkout -b hotfix/v1.1.1 main
```

### 2. Fix Bug

```bash
# Make fix
# Edit files...

# Add tests
# tests/test_hotfix.py

# Run tests
pytest tests/test_hotfix.py -v

# Commit fix
git add .
git commit -m "fix: critical bug in connector authentication

Fixes #123"
```

### 3. Bump Patch Version

```bash
# Bump to 1.1.1
python scripts/version.py --patch

# Update CHANGELOG.md
```

Edit `CHANGELOG.md`:
```markdown
## [1.1.1] - 2025-10-16

### Fixed
- Critical bug in connector authentication (#123)
```

### 4. Merge and Tag

```bash
# Merge to main
git checkout main
git merge --no-ff hotfix/v1.1.1 -m "Hotfix v1.1.1"

# Create tag
git tag -a v1.1.1 -m "Hotfix v1.1.1: Fix connector authentication"

# Push
git push origin main
git push origin v1.1.1
```

### 5. Fast-Track Release

- Automated release workflow triggers
- Review draft release
- Publish immediately (hotfixes skip extended review)
- Notify users of critical fix

## Rollback Procedures

If a release has critical issues:

### 1. Assess Severity

**Critical issues requiring rollback:**
- Data corruption or loss
- Security vulnerabilities
- Complete service outage
- Breaking changes in patch release

**Issues NOT requiring rollback:**
- Minor bugs with workarounds
- Non-critical feature issues
- Documentation errors

### 2. Rollback GitHub Release

```bash
# Mark release as pre-release (hides from latest)
gh release edit v1.1.0 --prerelease

# Or delete release entirely
gh release delete v1.1.0 --yes

# Delete tag
git tag -d v1.1.0
git push origin :refs/tags/v1.1.0
```

### 3. Rollback Docker Images

```bash
# Re-tag previous stable version as latest
docker tag djp-workflow-app:1.0.0 djp-workflow-app:latest
docker push username/djp-workflow-app:latest

# Or delete problematic tags from registry
# (Registry-specific commands)
```

### 4. Communicate Rollback

```markdown
Subject: URGENT: DJP Workflow v1.1.0 Rollback

Team,

We are rolling back v1.1.0 due to [critical issue].

**Action Required:**
- Do NOT upgrade to v1.1.0
- If already upgraded, rollback to v1.0.0
- Rollback instructions: [link]

**Next Steps:**
- Issue will be fixed in v1.1.1
- Expected release: [date]

Apologies for the inconvenience.

Release Team
```

### 5. Fix and Re-Release

```bash
# Fix issue
# Create hotfix branch
git checkout -b hotfix/v1.1.1 v1.0.0

# Apply fixes
# ...

# Release v1.1.1 (skip v1.1.0)
python scripts/version.py --set 1.1.1
# Follow hotfix process above
```

## Release Checklist

### Pre-Release
- [ ] Version bumped (`python scripts/version.py`)
- [ ] CHANGELOG.md updated
- [ ] Release notes generated
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Pre-commit hooks pass
- [ ] Packages built and tested
- [ ] Security scan completed

### Release
- [ ] Release branch merged to main
- [ ] Version tag created (`git tag -a vX.Y.Z`)
- [ ] Tag pushed to GitHub (`git push origin vX.Y.Z`)
- [ ] GitHub Actions workflow succeeded
- [ ] Draft release reviewed

### Publish
- [ ] GitHub Release published
- [ ] Docker images built
- [ ] Docker images pushed to registry
- [ ] Installation verified
- [ ] Upgrade path tested

### Post-Release
- [ ] Documentation website updated
- [ ] Release announced (internal/external)
- [ ] Dependent projects notified
- [ ] Monitoring for issues
- [ ] Release retrospective scheduled

## Release Metrics

Track release health with these metrics:

**Lead time:**
```bash
# Time from first commit to release
git log --reverse --pretty=format:"%ai" v1.0.0..v1.1.0 | head -1
git log --pretty=format:"%ai" v1.1.0 | head -1
```

**Deployment frequency:**
```bash
# Number of releases per month
git tag -l | grep -E "v[0-9]+\.[0-9]+\.[0-9]+" | wc -l
```

**Change failure rate:**
```bash
# Hotfixes / Total releases
HOTFIXES=$(git tag -l | grep -E "\.1$|\.2$|\.3$" | wc -l)
TOTAL=$(git tag -l | grep -E "v[0-9]+\.[0-9]+\.[0-9]+" | wc -l)
echo "Failure rate: $(($HOTFIXES * 100 / $TOTAL))%"
```

**Time to restore:**
```bash
# Time from issue report to hotfix release
# (Track manually in issue tracker)
```

## Troubleshooting

### Build Failures

**Error:** `pytest failed with exit code 1`

**Solution:**
```bash
# Run tests locally
pytest tests/ -v

# Fix failing tests
# ...

# Rerun tests
pytest tests/ -v

# Commit fixes
git add .
git commit -m "fix: resolve test failures"
git push
```

### Tag Already Exists

**Error:** `fatal: tag 'v1.1.0' already exists`

**Solution:**
```bash
# Delete local tag
git tag -d v1.1.0

# Delete remote tag
git push origin :refs/tags/v1.1.0

# Recreate tag
git tag -a v1.1.0 -m "Release v1.1.0"
git push origin v1.1.0
```

### Docker Build Fails

**Error:** `failed to build image`

**Solution:**
```bash
# Clean Docker cache
docker system prune -a

# Rebuild with no cache
docker build --no-cache -f docker/Dockerfile.app -t djp-workflow-app:1.1.0 .

# Check Dockerfile syntax
docker build --dry-run -f docker/Dockerfile.app .
```

### GitHub Actions Workflow Fails

**Error:** Workflow fails at specific step

**Solution:**
1. Check workflow logs on GitHub Actions tab
2. Identify failing step
3. Reproduce issue locally
4. Fix issue and push
5. Re-trigger workflow (delete and recreate tag)

## Related Documentation

- **CHANGELOG.md**: Release history
- **docs/INSTALL.md**: Installation guide
- **docs/UPGRADE.md**: Upgrade procedures
- **docs/OPERATIONS.md**: Operational runbooks
- **docs/RELEASE_CHECKLIST.md**: Quick reference checklist

## References

- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github)
- [Docker Hub](https://docs.docker.com/docker-hub/)
- [Python Packaging](https://packaging.python.org/)

---

**Release with confidence!**
