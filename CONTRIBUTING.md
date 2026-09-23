# Contributing to Uni-OCR

Thank you for your interest in contributing to Uni-OCR! We welcome bug fixes, documentation improvements, and performance enhancements.

## Development Setup

Uni-OCR utilizes [`uv`](https://github.com/astral-sh/uv) for fast, deterministic dependency resolution.

### Prerequisites

- Python 3.10 or higher
- `uv` installed (`curl -LsSf https://astral.sh/uv/install.sh | sh` or `brew install uv`)
- (Optional) Docker for containerized testing

### Local Setup

```bash
# Clone the repository
git clone https://github.com/yuanweize/Uni-OCR.git
cd Uni-OCR

# Create and activate virtual environment with uv
uv venv
source .venv/bin/activate

# Install editable package with dev dependencies
uv pip install -e ".[dev]"
```

## Running Tests & Verification

```bash
# Run tests
pytest

# Code style & linting
ruff check .
ruff format --check .
```

## Contribution Workflow

1. **Fork & Branch**: Create a descriptive feature branch from `master` (`git checkout -b feat/your-feature-name`).
2. **Commit Conventions**: Use [Conventional Commits](https://www.conventionalcommits.org/) format:
   - `feat(...)`: New features or OCR pipelines
   - `fix(...)`: Bug fixes
   - `docs(...)`: Documentation updates
   - `perf(...)`: Performance optimizations
   - `refactor(...)`: Code refactoring without behavior change
3. **Pull Request**: Open a pull request against `master`. Provide clear context, reproduction/validation details, and sample inputs where applicable.
