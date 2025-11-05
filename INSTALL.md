# GuardianVault Installation Guide

This project uses **Poetry** for dependency management, providing better dependency resolution and reproducible builds.

## Prerequisites

- Python 3.9 or higher
- Poetry (Python package manager)

## Installing Poetry

### macOS / Linux / WSL

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

### Windows (PowerShell)

```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
```

### Alternative: Using pip

```bash
pip install poetry
```

Verify installation:

```bash
poetry --version
```

## Installation Options

### Option 1: Install GuardianVault Library Only

If you only need the core library:

```bash
# Install dependencies
poetry install

# Or install without dev dependencies
poetry install --only main
```

### Option 2: Install with Development Tools

Includes testing, linting, and type checking:

```bash
poetry install --with dev
```

### Option 3: Install Coordination Server

To run the coordination server:

```bash
cd coordination-server
poetry install
```

### Option 4: Install Everything (Development Setup)

For full development environment:

```bash
# Install guardianvault library
poetry install --with dev,test

# Install coordination server
cd coordination-server
poetry install --with dev

# Return to root
cd ..
```

## Using Poetry Virtual Environment

Poetry automatically creates and manages virtual environments:

```bash
# Activate the virtual environment
poetry shell

# Run commands without activating
poetry run python examples/complete_mpc_workflow.py

# Run tests
poetry run pytest

# Add a new dependency
poetry add requests

# Add a dev dependency
poetry add --group dev black
```

## Migration from requirements.txt

If you need the old requirements.txt format:

```bash
# Export current environment
poetry export -f requirements.txt --output requirements.txt

# Export without dev dependencies
poetry export -f requirements.txt --output requirements.txt --only main

# Export with hashes for security
poetry export -f requirements.txt --output requirements.txt --with-credentials
```

## Running the Project

### Run Examples

```bash
# With activated environment
poetry shell
python examples/complete_mpc_workflow.py

# Or without activating
poetry run python examples/complete_mpc_workflow.py
```

### Run Coordination Server

```bash
cd coordination-server
poetry run python -m app.main

# Or with hot reload (development)
poetry run uvicorn app.main:app --reload
```

### Run Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov

# Run specific test file
poetry run pytest tests/test_coordination_server.py
```

## Development Tools

Poetry includes several development tools:

```bash
# Code formatting (Black)
poetry run black guardianvault/

# Linting (Ruff)
poetry run ruff check guardianvault/

# Type checking (MyPy)
poetry run mypy guardianvault/
```

## Updating Dependencies

```bash
# Update all dependencies to latest compatible versions
poetry update

# Update specific dependency
poetry update ecdsa

# Show outdated dependencies
poetry show --outdated
```

## Troubleshooting

### Poetry not found after installation

Add Poetry to your PATH:

```bash
# macOS/Linux
export PATH="$HOME/.local/bin:$PATH"

# Add to ~/.bashrc or ~/.zshrc to make permanent
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
```

### Clear Poetry cache

```bash
poetry cache clear pypi --all
```

### Regenerate lock file

```bash
poetry lock --no-update
```

### Use specific Python version

```bash
poetry env use python3.11
poetry env use /usr/local/bin/python3.11
```

## Additional Resources

- [Poetry Documentation](https://python-poetry.org/docs/)
- [Poetry Commands Reference](https://python-poetry.org/docs/cli/)
- [Managing Dependencies](https://python-poetry.org/docs/managing-dependencies/)

## Why Poetry?

Benefits over pip + requirements.txt:

- **Better dependency resolution** - Resolves conflicts automatically
- **Lock files** - Ensures reproducible builds with `poetry.lock`
- **Virtual environment management** - No need for manual venv setup
- **Build and publish** - Easy package distribution to PyPI
- **Modern standard** - Uses `pyproject.toml` (PEP 518)
- **Development groups** - Separate dev, test, and production dependencies
