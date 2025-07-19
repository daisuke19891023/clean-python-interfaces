# Development Guide

## Setup

1. Clone the repository
2. Install dependencies: `uv pip install -e ".[dev]"`
3. Install pre-commit hooks: `pre-commit install`

## Development Workflow

### Code Quality

```bash
# Run all quality checks
nox -s all_checks

# Run specific checks
nox -s lint      # Linting
nox -s format_code  # Formatting
nox -s typing    # Type checking
nox -s test      # Tests
nox -s security  # Security checks
```

### Pre-commit Hooks

The project uses pre-commit hooks to ensure code quality:

-   Ruff for linting and formatting
-   Black for code formatting
-   isort for import sorting
-   Bandit for security checks
-   Commitizen for conventional commits

### Testing

```bash
# Run tests with coverage
nox -s test

# Run tests in parallel
pytest -n auto

# Run specific test markers
pytest -m "not slow"
```

### Documentation

```bash
# Build documentation
nox -s docs

# Serve documentation locally
mkdocs serve
```

## Contributing

1. Create a feature branch
2. Make your changes
3. Run quality checks: `nox -s all_checks`
4. Commit using conventional commits: `cz commit`
5. Create a pull request

## Release Process

1. Use conventional commits for all changes
2. Run `cz bump` to create a new version
3. Push tags: `git push --tags`
4. GitHub Actions will automatically publish to PyPI
