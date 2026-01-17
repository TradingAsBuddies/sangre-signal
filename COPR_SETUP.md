# COPR Setup and Build Guide

Quick guide to build Sangre Signal on COPR for easy Fedora installation.

## Prerequisites

```bash
# Install COPR CLI
sudo dnf install copr-cli
```

## Configure COPR CLI

1. Get your API token from: https://copr.fedorainfracloud.org/api/
2. Save to `~/.config/copr`:

```ini
[copr-cli]
login = YOUR_USERNAME
username = YOUR_USERNAME
token = YOUR_API_TOKEN
copr_url = https://copr.fedorainfracloud.org
```

## Create COPR Repository

```bash
# Create the repository (only need to do this once)
copr-cli create sangre-signal \
    --chroot fedora-39-x86_64 \
    --chroot fedora-40-x86_64 \
    --chroot fedora-41-x86_64 \
    --chroot fedora-rawhide-x86_64 \
    --description "Sangre Signal - Advanced stock analysis tool with risk factor detection" \
    --instructions "Installation: sudo dnf copr enable tradingasbuddies/sangre-signal && sudo dnf install sangre-signal"
```

## Build from GitHub

### Option 1: Build from Latest Commit

```bash
copr-cli buildscm sangre-signal \
    --clone-url https://github.com/TradingAsBuddies/sangre-signal \
    --spec sangre-signal.spec \
    --type git \
    --method make_srpm
```

### Option 2: Build from Specific Tag/Release

```bash
copr-cli buildscm sangre-signal \
    --clone-url https://github.com/TradingAsBuddies/sangre-signal \
    --committish v2.0.0 \
    --spec sangre-signal.spec \
    --type git \
    --method make_srpm
```

## Monitor Build Status

```bash
# Check build status
copr-cli list-builds sangre-signal

# Watch build log
copr-cli watch-build BUILD_ID
```

## Testing the Build

Once the build completes:

```bash
# Enable the repository
sudo dnf copr enable tradingasbuddies/sangre-signal

# Install the package
sudo dnf install sangre-signal

# Test it
sangre-signal --ticker AAPL
```

## Updating for New Releases

When you push a new version:

1. Update version in `pyproject.toml` and `sangre_signal/__init__.py`
2. Update `sangre-signal.spec`:
   - Bump `Version:`
   - Reset `Release:` to 1
   - Add changelog entry
3. Commit and tag:
   ```bash
   git add .
   git commit -m "Release v2.1.0"
   git tag v2.1.0
   git push && git push --tags
   ```
4. Rebuild on COPR:
   ```bash
   copr-cli buildscm sangre-signal \
       --clone-url https://github.com/TradingAsBuddies/sangre-signal \
       --committish v2.1.0 \
       --spec sangre-signal.spec \
       --type git \
       --method make_srpm
   ```

## Enable Auto-Rebuilds (Optional)

You can set up webhooks to auto-rebuild on git push:

1. Go to: https://copr.fedorainfracloud.org/coprs/tradingasbuddies/sangre-signal/settings/
2. Enable "Build on push"
3. Add GitHub webhook URL to your repository

## Repository Information

Once built, users can install with:

```bash
# Enable repository
sudo dnf copr enable tradingasbuddies/sangre-signal

# Install
sudo dnf install sangre-signal
```

Repository URL: https://copr.fedorainfracloud.org/coprs/tradingasbuddies/sangre-signal/

## Troubleshooting

### Build Fails

Check build logs:
```bash
copr-cli get-build-details BUILD_ID
```

Common issues:
- Missing BuildRequires in spec file
- Source tarball generation issues
- Dependency version conflicts

### Dependency Not Available

If a Python dependency isn't in Fedora repos:
1. Check alternative package names (e.g., `python3-beautifulsoup4` vs `python3-bs4`)
2. Consider packaging the dependency in COPR too
3. Use versioned dependencies carefully

### Failed to Enable Repository

Make sure repository is public:
```bash
copr-cli modify sangre-signal --unlisted-on-hp off
```

## COPR Badge for README

Once built, add this badge to README.md:

```markdown
[![COPR](https://copr.fedorainfracloud.org/coprs/tradingasbuddies/sangre-signal/package/sangre-signal/status_image/last_build.png)](https://copr.fedorainfracloud.org/coprs/tradingasbuddies/sangre-signal/)
```

## Useful Commands

```bash
# List your repositories
copr-cli list

# Get package info
copr-cli get-package sangre-signal --name sangre-signal

# Delete a build (if needed)
copr-cli delete-build BUILD_ID

# Cancel ongoing build
copr-cli cancel-build BUILD_ID
```

## Need Help?

- COPR Documentation: https://docs.pagure.org/copr.copr/
- Fedora Packaging: https://docs.fedoraproject.org/en-US/packaging-guidelines/
- Contact: David Duncan <tradingasbuddies@davidduncan.org>
