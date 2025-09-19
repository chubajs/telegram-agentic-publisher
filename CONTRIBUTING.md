# Contributing to Telegram Agentic Publisher

Thank you for your interest in contributing to Telegram Agentic Publisher! We welcome contributions from the community.

## Code of Conduct

Please be respectful and constructive in all interactions.

## How to Contribute

### Reporting Bugs

1. Check if the issue already exists in [GitHub Issues](https://github.com/sergebulaev/telegram-agentic-publisher/issues)
2. Create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - System information (Python version, OS)

### Suggesting Features

1. Check existing issues for similar suggestions
2. Open a new issue with the `enhancement` label
3. Describe the feature and its use case

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests if applicable
5. Run tests: `pytest tests/`
6. Commit with clear messages (`git commit -m 'Add amazing feature'`)
7. Push to your branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Development Setup

```bash
# Clone the repository
git clone https://github.com/sergebulaev/telegram-agentic-publisher.git
cd telegram-agentic-publisher

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .[dev]

# Run tests
pytest tests/
```

### Code Style

- Follow PEP 8
- Use type hints where appropriate
- Add docstrings to functions and classes
- Keep functions focused and under 50 lines
- Use meaningful variable names

### Testing

- Write tests for new features
- Ensure existing tests pass
- Aim for good test coverage
- Test error cases

### Documentation

- Update README.md if needed
- Add docstrings to new code
- Include usage examples
- Update CHANGELOG.md

## Questions?

Feel free to:
- Open an issue for discussion
- Contact the author: serge@bulaev.net
- Visit [https://bulaev.net](https://bulaev.net)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Author

Serge Bulaev - [https://bulaev.net](https://bulaev.net)