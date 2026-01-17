# PyPI Deployment Guide

Guide for publishing Sangre Signal to PyPI as user `davdunc`.

## Prerequisites

### 1. Install Build Tools

```bash
pip install --upgrade build twine
```

### 2. Create PyPI Account

- Main PyPI: https://pypi.org/account/register/
- Test PyPI: https://test.pypi.org/account/register/

### 3. Create API Tokens

#### For PyPI (Production)
1. Go to: https://pypi.org/manage/account/
2. Scroll to "API tokens"
3. Click "Add API token"
4. Name: `sangre-signal-upload`
5. Scope: "Project: sangre-signal" (after first upload) or "Entire account"
6. Save the token (starts with `pypi-`)

#### For Test PyPI (Testing)
1. Go to: https://test.pypi.org/manage/account/
2. Create token: `sangre-signal-test`
3. Save the token

### 4. Configure PyPI Credentials

Create `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR_PRODUCTION_TOKEN_HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR_TEST_TOKEN_HERE
```

**Important**: Keep your tokens secret! Don't commit `~/.pypirc` to git.

## Manual Upload Process

### 1. Update Version

Before each release, update version in:
- `pyproject.toml` (line 7: `version = "2.0.0"`)
- `sangre_signal/__init__.py` (line 16: `__version__ = "2.0.0"`)

Use semantic versioning: MAJOR.MINOR.PATCH

### 2. Build Distribution

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build source distribution and wheel
python -m build
```

This creates:
- `dist/sangre_signal-2.0.0.tar.gz` (source distribution)
- `dist/sangre_signal-2.0.0-py3-none-any.whl` (wheel)

### 3. Check Distribution

```bash
# Check the package
twine check dist/*
```

Should show: `Checking dist/... PASSED`

### 4. Test on Test PyPI First

```bash
# Upload to Test PyPI
twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ sangre-signal
```

Note: `--extra-index-url` allows dependencies from regular PyPI.

### 5. Upload to Production PyPI

```bash
# Upload to PyPI
twine upload dist/*
```

You'll see: `Uploading sangre_signal-2.0.0-py3-none-any.whl` and success message.

### 6. Verify

```bash
# Install from PyPI
pip install sangre-signal

# Test it
sangre-signal --ticker AAPL
```

View on PyPI: https://pypi.org/project/sangre-signal/

## Automated Publishing with GitHub Actions

See `.github/workflows/publish-pypi.yml` for automated publishing on git tags.

### Setup GitHub Secrets

1. Go to: https://github.com/TradingAsBuddies/sangre-signal/settings/secrets/actions
2. Add secrets:
   - `PYPI_API_TOKEN`: Your PyPI production token
   - `TEST_PYPI_API_TOKEN`: Your Test PyPI token

### Publish New Release

```bash
# 1. Update version in code
# 2. Commit changes
git add .
git commit -m "Release v2.1.0"

# 3. Create and push tag
git tag v2.1.0
git push && git push --tags

# GitHub Actions will automatically:
# - Build the package
# - Run tests
# - Upload to Test PyPI
# - Upload to PyPI (on approval)
```

## Version Management

Follow semantic versioning:

- **MAJOR** (2.x.x): Breaking changes
- **MINOR** (x.1.x): New features, backwards compatible
- **PATCH** (x.x.1): Bug fixes

Examples:
- `2.0.0` → Initial release
- `2.0.1` → Bug fix
- `2.1.0` → New feature added
- `3.0.0` → Breaking API change

## Updating Existing Package

### 1. Make Changes

```bash
# Make code changes
# Update CHANGELOG.md
# Update version numbers
```

### 2. Build and Upload

```bash
# Clean and build
rm -rf dist/
python -m build

# Check
twine check dist/*

# Upload
twine upload dist/*
```

### 3. Tag Release

```bash
git tag v2.1.0
git push --tags
```

## Troubleshooting

### "File already exists"

PyPI doesn't allow re-uploading the same version. Solutions:
- Bump the version number
- Use a post-release: `2.0.0.post1`
- Delete and re-upload only works on Test PyPI

### "Invalid distribution"

```bash
# Check your package
twine check dist/*

# Verify pyproject.toml is valid
python -c "import tomli; tomli.load(open('pyproject.toml', 'rb'))"
```

### Missing Dependencies

Ensure all dependencies are listed in `pyproject.toml`:
```toml
dependencies = [
    "yfinance>=0.2.28",
    "requests>=2.31.0",
    ...
]
```

### Import Errors After Install

Check package structure:
```bash
# After install, verify imports
python -c "from sangre_signal import StockInfo"
python -c "from sangre_signal.cli import run_cli"
```

## Best Practices

1. **Always test on Test PyPI first**
2. **Use version tags in git**
3. **Keep a CHANGELOG.md**
4. **Test installation in clean virtualenv**
5. **Don't upload from main branch** (use tags/releases)
6. **Check package with `twine check`** before upload

## Package Information

- **Package name**: `sangre-signal`
- **Import name**: `sangre_signal`
- **PyPI URL**: https://pypi.org/project/sangre-signal/
- **Maintainer**: davdunc (David Duncan)
- **License**: MIT

## Useful Commands

```bash
# View package info
pip show sangre-signal

# List files in package
tar tzf dist/sangre_signal-2.0.0.tar.gz

# Check wheel contents
unzip -l dist/sangre_signal-2.0.0-py3-none-any.whl

# Install in editable mode for development
pip install -e .

# Build and upload in one go (careful!)
python -m build && twine upload dist/*
```

## Resources

- PyPI Help: https://pypi.org/help/
- Packaging Guide: https://packaging.python.org/
- Twine Documentation: https://twine.readthedocs.io/
- Semantic Versioning: https://semver.org/

## Contact

Questions? Email: David Duncan <tradingasbuddies@davidduncan.org>
