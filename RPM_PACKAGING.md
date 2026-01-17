# RPM Packaging Guide for Sangre Signal

This guide explains how to build and package Sangre Signal for Fedora/RHEL-based distributions.

## Prerequisites

### Install RPM Build Tools

```bash
# On Fedora
sudo dnf install rpm-build rpmdevtools rpmlint

# On RHEL/CentOS
sudo yum install rpm-build rpmdevtools rpmlint
```

### Set Up RPM Build Environment

```bash
# Create RPM build directory structure
rpmdev-setuptree

# This creates:
# ~/rpmbuild/
#   ├── BUILD/
#   ├── RPMS/
#   ├── SOURCES/
#   ├── SPECS/
#   └── SRPMS/
```

## Building the RPM Package

### 1. Create Source Tarball

From the project root directory:

```bash
# Create a tarball from git
git archive --format=tar.gz --prefix=sangre-signal-2.0.0/ v2.0.0 > ~/rpmbuild/SOURCES/sangre-signal-2.0.0.tar.gz

# Or create from current directory
tar czf ~/rpmbuild/SOURCES/sangre-signal-2.0.0.tar.gz \
    --transform 's,^\.,sangre-signal-2.0.0,' \
    --exclude='.git*' \
    --exclude='venv' \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='*.egg-info' \
    --exclude='dist' \
    --exclude='build' \
    .
```

### 2. Copy Spec File

```bash
cp sangre-signal.spec ~/rpmbuild/SPECS/
```

### 3. Install Build Dependencies

```bash
# Install dependencies listed in the spec file
sudo dnf builddep ~/rpmbuild/SPECS/sangre-signal.spec
```

### 4. Build the RPM

```bash
# Build both source and binary RPMs
rpmbuild -ba ~/rpmbuild/SPECS/sangre-signal.spec

# Or build only binary RPM
rpmbuild -bb ~/rpmbuild/SPECS/sangre-signal.spec

# Or build only source RPM
rpmbuild -bs ~/rpmbuild/SPECS/sangre-signal.spec
```

### 5. Check for Issues

```bash
# Lint the spec file
rpmlint ~/rpmbuild/SPECS/sangre-signal.spec

# Lint the built RPM
rpmlint ~/rpmbuild/RPMS/noarch/sangre-signal-2.0.0-1.*.noarch.rpm
```

## Installing the Built RPM

### Install Locally

```bash
# Install the RPM (will pull in dependencies)
sudo dnf install ~/rpmbuild/RPMS/noarch/sangre-signal-2.0.0-1.*.noarch.rpm
```

### Verify Installation

```bash
# Check installed files
rpm -ql sangre-signal

# Verify the package
rpm -V sangre-signal

# Run the application
sangre-signal --ticker AAPL
```

## Testing the Package

### Basic Functionality Test

```bash
# Test CLI
sangre-signal --ticker AAPL

# Test Python module
python3 -m sangre_signal --ticker TSLA

# Check version
rpm -qi sangre-signal
```

### Uninstall

```bash
sudo dnf remove sangre-signal
```

## Submitting to Fedora Repositories

If you want to submit this to official Fedora repositories:

### 1. Join the Fedora Package Maintainers

- Create a [Fedora Account](https://accounts.fedoraproject.org/)
- Join the [packager group](https://fedoraproject.org/wiki/Join_the_package_collection_maintainers)
- Complete the [package review process](https://fedoraproject.org/wiki/Package_Review_Process)

### 2. Submit Package Review Request

```bash
# Upload your SRPM to a public location
# Create a bug in Fedora's Bugzilla:
# https://bugzilla.redhat.com/enter_bug.cgi?product=Fedora&component=Package%20Review
```

### 3. Package Review Guidelines

Your package must follow:
- [Fedora Packaging Guidelines](https://docs.fedoraproject.org/en-US/packaging-guidelines/)
- [Python Packaging Guidelines](https://docs.fedoraproject.org/en-US/packaging-guidelines/Python/)

## Creating a COPR Repository

For easier distribution before official Fedora inclusion, use COPR.

**See [COPR_SETUP.md](COPR_SETUP.md) for complete COPR setup and build instructions.**

Quick overview:

### 1. Install and Configure COPR CLI

```bash
sudo dnf install copr-cli
# Configure with API token from https://copr.fedorainfracloud.org/api/
```

### 2. Create Repository and Build

```bash
# Create repository (one time)
copr-cli create sangre-signal --chroot fedora-40-x86_64 ...

# Build from GitHub
copr-cli buildscm sangre-signal \
    --clone-url https://github.com/TradingAsBuddies/sangre-signal \
    --spec sangre-signal.spec \
    --type git
```

### 3. Users Install with

```bash
sudo dnf copr enable tradingasbuddies/sangre-signal
sudo dnf install sangre-signal
```

## Updating the Package

When releasing a new version:

### 1. Update Version

Edit `sangre-signal.spec`:
```spec
Version:        2.1.0
Release:        1%{?dist}
```

### 2. Add Changelog Entry

```spec
%changelog
* Wed Jan 15 2025 David Duncan <tradingasbuddies@davidduncan.org> - 2.1.0-1
- Update to version 2.1.0
- Add new features: XYZ
- Fix bugs: ABC
```

### 3. Rebuild

```bash
# Create new tarball
git archive --format=tar.gz --prefix=sangre-signal-2.1.0/ v2.1.0 > ~/rpmbuild/SOURCES/sangre-signal-2.1.0.tar.gz

# Rebuild RPM
rpmbuild -ba ~/rpmbuild/SPECS/sangre-signal.spec
```

## Troubleshooting

### Missing Dependencies

If dependencies aren't available in Fedora repos:

1. Check if they exist with different names
2. Package the dependency first
3. Use COPR for testing

### Build Failures

```bash
# Check build logs
less ~/rpmbuild/BUILD/sangre-signal-2.0.0/build.log

# Use mock for clean environment testing
mock -r fedora-40-x86_64 ~/rpmbuild/SRPMS/sangre-signal-2.0.0-1.*.src.rpm
```

### rpmlint Warnings

Common warnings and fixes:

- `no-documentation`: Add %doc README.md
- `no-license-file`: Add %license LICENSE
- `unstripped-binary-or-object`: Normal for Python packages (noarch)

## Additional Resources

- [Fedora Packaging Tutorial](https://docs.fedoraproject.org/en-US/package-maintainers/Packaging_Tutorial_GNU_Hello/)
- [Fedora Python Guidelines](https://docs.fedoraproject.org/en-US/packaging-guidelines/Python/)
- [RPM Packaging Guide](https://rpm-packaging-guide.github.io/)
- [COPR Documentation](https://docs.pagure.org/copr.copr/user_documentation.html)

## Questions?

Contact: David Duncan <tradingasbuddies@davidduncan.org>
