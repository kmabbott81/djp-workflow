# Release Checklist

Quick reference for maintainers creating a new release of djp-workflow.

## Pre-Release Steps

### 1. Version Bump

Update version numbers using the version script:

```bash
# For patch releases (bug fixes): 1.0.0 → 1.0.1
python scripts/version.py --patch

# For minor releases (new features): 1.0.0 → 1.1.0
python scripts/version.py --minor

# For major releases (breaking changes): 1.0.0 → 2.0.0
python scripts/version.py --major
```

This automatically updates:
- `src/__init__.py`
- `pyproject.toml`
- Creates placeholder in `CHANGELOG.md`

### 2. Update CHANGELOG.md

Edit `CHANGELOG.md` and add release notes under the new version heading:

```markdown
## [1.1.0] - 2025-XX-XX

### Added
- New feature X
- New feature Y

### Changed
- Updated behavior Z

### Fixed
- Bug fix A
- Bug fix B

### Security
- Security fix C (if applicable)
```

### 3. Generate and Review Release Notes

```bash
python scripts/release_notes.py --latest --output .release_notes_vX.Y.Z.md
```

Review the generated notes for accuracy and completeness.

### 4. Quality Gates

Run all quality checks:

```bash
# Run pre-commit hooks
python -m pre_commit run --all-files

# Run full test suite
python -m pytest -q

# Validate schemas
python scripts/validate_artifacts.py
```

All checks must pass before proceeding.

### 5. Build Packages

Build distribution packages:

```bash
python -m build
```

Expected output:
- `dist/djp_workflow-X.Y.Z.tar.gz` (source distribution)
- `dist/djp_workflow-X.Y.Z-py3-none-any.whl` (wheel)

### 6. Smoke Test (Optional but Recommended)

Test the wheel in a clean virtual environment:

```bash
# Create temp venv
python -m venv .tmp-venv
.tmp-venv\Scripts\activate  # Windows
# source .tmp-venv/bin/activate  # Linux/Mac

# Install wheel
pip install dist/djp_workflow-X.Y.Z-py3-none-any.whl

# Verify version
python -c "import src; print('Version:', src.__version__)"

# Deactivate and cleanup
deactivate
rm -rf .tmp-venv
```

## Release Execution

### 7. Commit and Tag

Commit all changes and create a version tag:

```bash
# Stage all changes
git add -A

# Commit release
git commit -m "chore(release): vX.Y.Z"

# Create version tag
git tag vX.Y.Z

# Push commits and tag
git push origin main
git push origin vX.Y.Z
```

**Note:** Pushing the tag triggers the automated release workflow on GitHub Actions.

### 8. GitHub Actions Workflow

The `.github/workflows/release.yml` workflow will automatically:

1. **Checkout** code with full history
2. **Setup** Python 3.11 environment
3. **Install** build and project dependencies
4. **Run** full test suite
5. **Build** sdist and wheel packages
6. **Validate** distributions with twine
7. **Upload** build artifacts (30-day retention)
8. **Generate** release notes from CHANGELOG
9. **Create** draft GitHub Release with:
   - Release notes from CHANGELOG
   - Attached sdist and wheel files
   - Version tag reference

### 9. Review and Publish Release

1. Go to GitHub repository → **Releases** tab
2. Find the **draft release** created by the workflow
3. Review:
   - Release notes accuracy
   - Attached artifacts (should have .tar.gz and .whl)
   - Version number is correct
4. **Publish release** (or edit if changes needed)

## Post-Release (Optional)

### 10. Verify Release

```bash
# Test installation from GitHub Release
pip install https://github.com/yourusername/djp-workflow/releases/download/vX.Y.Z/djp_workflow-X.Y.Z-py3-none-any.whl

# Verify version
python -c "import src; print(src.__version__)"
```

### 11. Update Documentation

If major changes:
- Update README.md with new features
- Update docs/OPERATIONS.md if operational changes
- Add migration guide if breaking changes

### 12. Announce Release

- Post release notes to project channels
- Update project dependencies if needed
- Notify users of breaking changes (if major version)

## Troubleshooting

### Build Fails

```bash
# Clean build artifacts
rm -rf dist/ build/ *.egg-info/

# Rebuild
python -m build
```

### Version Mismatch

```bash
# Check current versions
grep __version__ src/__init__.py
grep '^version =' pyproject.toml

# If mismatch, manually edit or re-run version script
```

### Pre-commit Hook Fails

```bash
# Fix automatically
python -m pre_commit run --all-files

# Add fixes and retry commit
git add -A
git commit --amend --no-edit
```

### Test Failures

```bash
# Run tests with verbose output
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_specific.py -v
```

### GitHub Actions Workflow Fails

1. Check workflow logs on GitHub Actions tab
2. Common issues:
   - Test failures (fix tests and re-tag)
   - Missing dependencies (update requirements)
   - Invalid release notes format (fix CHANGELOG.md)
3. Delete failed release draft
4. Delete tag: `git tag -d vX.Y.Z && git push origin :refs/tags/vX.Y.Z`
5. Fix issues and retry from step 7

## Reference Links

- **Operations Guide**: [docs/OPERATIONS.md](./OPERATIONS.md)
- **Contributing**: [../CONTRIBUTING.md](../CONTRIBUTING.md)
- **Changelog Format**: [Keep a Changelog](https://keepachangelog.com/)
- **Semantic Versioning**: [SemVer](https://semver.org/)

---

**Quick Command Summary** (for copy-paste):

```bash
# 1. Version bump
python scripts/version.py --patch  # or --minor or --major

# 2. Edit CHANGELOG.md (manual)

# 3. Generate release notes
python scripts/release_notes.py --latest --output .release_notes_vX.Y.Z.md

# 4. Quality gates
python -m pre_commit run --all-files
python -m pytest -q
python scripts/validate_artifacts.py

# 5. Build
python -m build

# 6. Commit and tag
git add -A
git commit -m "chore(release): vX.Y.Z"
git tag vX.Y.Z
git push origin main
git push origin vX.Y.Z

# 7. Review draft release on GitHub and publish
```

---

## Post-Tag Steps

After pushing the tag, the GitHub Actions release workflow automatically runs. Follow these steps:

### 1. Monitor GitHub Actions (~2-3 minutes)

Visit: `https://github.com/kmabbott81/djp-workflow/actions`

**Watch for:**
- "Release" workflow run for your version tag
- Green ✅ checkmark indicating success
- Red ❌ indicates failure - check logs

### 2. Inspect Draft Release

Visit: `https://github.com/kmabbott81/djp-workflow/releases`

**Verify the draft release contains:**
- ✅ Correct version number in title
- ✅ Release notes (auto-generated from workflow)
- ✅ Attached distribution files:
  - `djp_workflow-X.Y.Z.tar.gz` (source distribution)
  - `djp_workflow-X.Y.Z-py3-none-any.whl` (Python wheel)
- ✅ Tag points to correct commit
- ✅ Target branch is `main`

**If artifacts are missing:**
- Check GitHub Actions logs for build failures
- Verify workflow completed successfully
- Re-run workflow if needed

### 3. Publish Release

Once verified:
1. Click on the draft release
2. Review all details one final time
3. Click **"Publish release"** button
4. Release becomes public immediately

**After publishing:**
- Release appears in repository sidebar
- GitHub sends notifications to watchers
- Users can download packages
- Tag is permanently associated with release

### 4. Verify Installation (Optional but Recommended)

Test the published release:

```bash
# Install from GitHub Release
pip install https://github.com/kmabbott81/djp-workflow/releases/download/vX.Y.Z/djp_workflow-X.Y.Z-py3-none-any.whl

# Verify version
python -c "import src; print('Version:', src.__version__)"
# Should output: Version: X.Y.Z
```

### 5. Post-Publication

**Update documentation** (if needed):
- Update README.md with new features
- Add migration notes if breaking changes
- Update installation instructions

**Announce release** (optional):
- Share release URL with team/users
- Post in relevant channels
- Update dependent projects

**Monitor feedback:**
- Watch GitHub Issues for bug reports
- Respond to user questions
- Track installation problems

---

## Troubleshooting Post-Tag Issues

### Workflow Fails

**Symptom:** Red ❌ in GitHub Actions

**Solutions:**
1. Check workflow logs for specific error
2. Common issues:
   - Build failures: Check dependencies in `requirements.txt`
   - Test failures: Review failing test output
   - Artifact upload fails: Check file paths in workflow
3. Fix issues and re-trigger:
   ```bash
   git tag -d vX.Y.Z
   git push origin :refs/tags/vX.Y.Z
   # Fix issues, commit
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```

### Draft Release Not Created

**Symptom:** No draft appears after workflow succeeds

**Solutions:**
1. Check workflow permissions: `contents: write` required
2. Verify GitHub token has release permissions
3. Check workflow logs for release creation step
4. Manually create release if needed:
   - Go to Releases → "Draft a new release"
   - Choose tag: vX.Y.Z
   - Add release notes
   - Upload artifacts from workflow artifacts

### Wrong Files Attached

**Symptom:** Missing or incorrect distribution files

**Solutions:**
1. Check `dist/` directory was created during build
2. Verify workflow `files:` section matches build output
3. Re-run workflow or manually upload correct files

```
