# sangre-signal — Component Spec

_Spec v1 · 2026-06-14 · living doc · MIT, public (PyPI/COPR)._

## Purpose
Standalone advanced stock-analysis tool. Distinct from the core Falcon trading loop — a
publicly distributed analysis utility (its own license, packaging, and release pipeline).

## Responsibilities
- `sangre_signal.main:main` — CLI entry point for analysis runs.
- Stock analysis / signal computation (technical + statistical) as a self-contained package.

## Interfaces
- Console script: `sangre-signal` (`sangre_signal.main:main`).
- Distributed as a Python package (PyPI) and Fedora COPR build; runnable as a container
  (`Containerfile`).

## Packaging / release (this repo's emphasis)
- `pyproject.toml` (`[project.scripts]`), `Containerfile`, COPR setup (`COPR_SETUP.md`),
  PyPI deployment (`PYPI_DEPLOYMENT.md`, `MANUAL_PUBLISH.sh/.bat`),
  GitHub Actions secrets (`GITHUB_SECRETS_SETUP.md`), `DEPLOYMENT_QUICKSTART.md`.
- MIT licensed, `CONTRIBUTING.md` / `CONTRIBUTORS.md` — open-source posture.

## Dependencies
Self-contained (standard scientific Python stack); not coupled to falcon-core's DB/quadlet stack.

## Status / notes
- Lives in the TradingAsBuddies org but is an independent, releasable tool rather than a
  always-on Falcon service. Integration with the Falcon pipeline (as a signal source) is a
  possible future tie-in, not a current dependency.
