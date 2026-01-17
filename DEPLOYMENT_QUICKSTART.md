# Deployment Quick Start Guide

Quick reference for deploying Sangre Signal to PyPI and COPR as user `davdunc`.

## PyPI Deployment (pip install sangre-signal)

### One-Time Setup

1. **Get PyPI API Token**
   - Login to https://pypi.org/ as `davdunc`
   - Go to Account Settings → API tokens
   - Create token named "sangre-signal-upload"
   - Save token (starts with `pypi-`)

2. **Configure Local Credentials**

   Create `~/.pypirc`:
   ```ini
   [distutils]
   index-servers =
       pypi
       testpypi

   [pypi]
   username = __token__
   password = pypi-YOUR_TOKEN_HERE

   [testpypi]
   repository = https://test.pypi.org/legacy/
   username = __token__
   password = pypi-YOUR_TEST_TOKEN_HERE
   ```

3. **Install Build Tools**
   ```bash
   pip install --upgrade build twine
   ```

### Publishing New Version

#### Option 1: Automated (Recommended)

```bash
# 1. Update version
#    - Edit pyproject.toml line 7: version = "2.1.0"
#    - Edit sangre_signal/__init__.py line 16: __version__ = "2.1.0"

# 2. Commit and tag
git add .
git commit -m "Release v2.1.0"
git tag v2.1.0
git push && git push --tags

# GitHub Actions automatically:
# - Builds package
# - Publishes to Test PyPI
# - Publishes to PyPI
# - Creates GitHub release
```

#### Option 2: Manual

```bash
# 1. Update version numbers (same as above)

# 2. Build
rm -rf dist/
python -m build

# 3. Check
twine check dist/*

# 4. Test on Test PyPI
twine upload --repository testpypi dist/*

# 5. Upload to PyPI
twine upload dist/*

# 6. Tag release
git tag v2.1.0
git push --tags
```

### Verify

```bash
pip install sangre-signal
sangre-signal --ticker AAPL
```

View on PyPI: https://pypi.org/project/sangre-signal/

---

## COPR Deployment (Fedora/RHEL: sudo dnf install sangre-signal)

### One-Time Setup

1. **Get COPR API Token**
   - Login to https://copr.fedorainfracloud.org/ as `tradingasbuddies`
   - Go to API → Generate token
   - Save to `~/.config/copr`:
   ```ini
   [copr-cli]
   login = tradingasbuddies
   username = tradingasbuddies
   token = YOUR_TOKEN_HERE
   copr_url = https://copr.fedorainfracloud.org
   ```

2. **Install COPR CLI**
   ```bash
   sudo dnf install copr-cli
   ```

3. **Create Repository** (one-time)
   ```bash
   copr-cli create sangre-signal \
       --chroot fedora-39-x86_64 \
       --chroot fedora-40-x86_64 \
       --chroot fedora-41-x86_64 \
       --chroot fedora-rawhide-x86_64 \
       --description "Sangre Signal - Advanced stock analysis tool"
   ```

### Building New Version

```bash
# 1. Update sangre-signal.spec:
#    - Line 2: Version: 2.1.0
#    - Line 3: Release: 1%{?dist}
#    - Add changelog entry at bottom

# 2. Commit and tag
git add .
git commit -m "Release v2.1.0"
git tag v2.1.0
git push && git push --tags

# 3. Build on COPR
copr-cli buildscm sangre-signal \
    --clone-url https://github.com/TradingAsBuddies/sangre-signal \
    --committish v2.1.0 \
    --spec sangre-signal.spec \
    --type git \
    --method make_srpm

# 4. Monitor build
copr-cli list-builds sangre-signal
```

### Verify

```bash
sudo dnf copr enable tradingasbuddies/sangre-signal
sudo dnf install sangre-signal
sangre-signal --ticker AAPL
```

View on COPR: https://copr.fedorainfracloud.org/coprs/tradingasbuddies/sangre-signal/

---

## Release Checklist

For each new version:

- [ ] Update version in `pyproject.toml`
- [ ] Update version in `sangre_signal/__init__.py`
- [ ] Update `sangre-signal.spec` (version, release, changelog)
- [ ] Update `CHANGELOG.md` (if exists)
- [ ] Commit: `git commit -m "Release vX.Y.Z"`
- [ ] Tag: `git tag vX.Y.Z`
- [ ] Push: `git push && git push --tags`
- [ ] PyPI: Automatic via GitHub Actions OR manual `twine upload`
- [ ] COPR: `copr-cli buildscm sangre-signal ...`
- [ ] Test installations:
  - `pip install sangre-signal`
  - `sudo dnf copr enable tradingasbuddies/sangre-signal && sudo dnf install sangre-signal`

---

## URLs

- **PyPI**: https://pypi.org/project/sangre-signal/
- **COPR**: https://copr.fedorainfracloud.org/coprs/tradingasbuddies/sangre-signal/
- **GitHub**: https://github.com/TradingAsBuddies/sangre-signal
- **GitHub Actions**: https://github.com/TradingAsBuddies/sangre-signal/actions

---

## Detailed Documentation

- **PyPI**: See [PYPI_DEPLOYMENT.md](PYPI_DEPLOYMENT.md)
- **COPR**: See [COPR_SETUP.md](COPR_SETUP.md)
- **RPM**: See [RPM_PACKAGING.md](RPM_PACKAGING.md)

---

## Contact

David Duncan <tradingasbuddies@davidduncan.org>
