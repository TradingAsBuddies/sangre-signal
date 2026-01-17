# Contributing to Super Signal

Thank you for your interest in contributing to Super Signal! We welcome contributions from the community.

## Project Maintainer

**David Duncan**
Email: tradingasbuddies@davidduncan.org
GitHub: [@TradingAsBuddies](https://github.com/TradingAsBuddies)

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue on GitHub with:
- A clear description of the problem
- Steps to reproduce the issue
- Expected vs actual behavior
- Your environment (OS, Python version, etc.)
- Any relevant error messages or logs

### Suggesting Enhancements

We love new ideas! To suggest an enhancement:
- Open an issue with the label "enhancement"
- Describe the feature and its benefits
- Explain how it would work
- Include any relevant examples or mockups

### Pull Requests

1. **Fork the repository**
   ```bash
   git clone https://github.com/TradingAsBuddies/super-signal.git
   cd super-signal
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Set up development environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e ".[dev]"
   ```

4. **Make your changes**
   - Write clear, documented code
   - Add type hints where applicable
   - Follow the existing code style
   - Add tests for new features

5. **Test your changes**
   ```bash
   # Run syntax checks
   python -m py_compile super_signal/**/*.py

   # Run tests (if available)
   pytest

   # Format code
   black super_signal/

   # Check types
   mypy super_signal/
   ```

6. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add feature: brief description"
   ```

   Use clear, descriptive commit messages. Follow this format:
   - `Add feature: description` - for new features
   - `Fix: description` - for bug fixes
   - `Update: description` - for improvements to existing features
   - `Docs: description` - for documentation changes

7. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

8. **Open a Pull Request**
   - Go to the original repository on GitHub
   - Click "New Pull Request"
   - Select your feature branch
   - Fill out the PR template with:
     - Description of changes
     - Motivation and context
     - Testing performed
     - Screenshots (if applicable)

## Development Guidelines

### Code Style

- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Write Google-style docstrings for all functions and classes
- Keep functions focused and single-purpose
- Maximum line length: 88 characters (Black default)

### Project Structure

When adding new features, place them in the appropriate module:
- **New risk checks** → `super_signal/analyzers/risk_analyzer.py`
- **New data sources** → Create new file in `super_signal/fetchers/`
- **Display changes** → `super_signal/formatters/display.py`
- **Configuration** → `super_signal/config.py`
- **Data models** → `super_signal/models.py`

### Documentation

- Update README.md if your changes affect usage
- Add docstrings to all new functions and classes
- Update CHANGELOG.md (if it exists) with your changes
- Include code examples for new features

### Testing

While we're building out our test suite, please:
- Test your changes manually with multiple stock tickers
- Verify edge cases (invalid tickers, network errors, etc.)
- Check that logging works correctly
- Ensure no existing functionality is broken

## Areas for Contribution

We especially welcome contributions in these areas:

### High Priority
- [ ] Unit tests and test coverage
- [ ] Additional data sources beyond Yahoo Finance and FinViz
- [ ] GUI development (tkinter or PyQt5)
- [ ] CSV/Excel export functionality
- [ ] Batch processing for multiple tickers

### Medium Priority
- [ ] Additional risk analysis metrics
- [ ] Database integration for historical data
- [ ] Caching layer for API calls
- [ ] Performance optimizations
- [ ] Enhanced error handling

### Nice to Have
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Docker containerization
- [ ] Web dashboard interface
- [ ] Real-time price alerts
- [ ] Portfolio tracking features

## Code of Conduct

### Our Standards

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Respect differing viewpoints and experiences
- Accept responsibility and apologize for mistakes

### Unacceptable Behavior

- Harassment, discrimination, or trolling
- Personal attacks or insults
- Publishing others' private information
- Spam or off-topic comments

## Questions?

If you have questions about contributing, feel free to:
- Open an issue with the "question" label
- Email David Duncan at tradingasbuddies@davidduncan.org
- Check existing issues and discussions

## License

By contributing to Super Signal, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Super Signal! 🚀📈
