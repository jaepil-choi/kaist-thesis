# Tests Directory

Unit tests and integration tests for the TNIC module.

## Structure

```
tests/
├── __init__.py              # Test package initialization
├── conftest.py              # Pytest configuration and shared fixtures
├── README.md                # This file
└── test_*.py                # Test files (to be added)
```

## Running Tests

### Basic Usage

```bash
# Run all tests
poetry run pytest tests/

# Run with verbose output
poetry run pytest tests/ -v

# Run with coverage report
poetry run pytest tests/ --cov=tnic --cov-report=html

# Run specific test file
poetry run pytest tests/test_korean_text_processor.py

# Run tests matching pattern
poetry run pytest tests/ -k "korean"
```

### Markers

Tests can be marked with custom markers:

```bash
# Skip slow tests
poetry run pytest tests/ -m "not slow"

# Run only integration tests
poetry run pytest tests/ -m "integration"

# Skip tests requiring MongoDB
poetry run pytest tests/ -m "not requires_mongodb"
```

### Available Markers

- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.requires_mongodb` - Tests requiring MongoDB connection
- `@pytest.mark.requires_kiwi` - Tests requiring kiwipiepy Korean tokenizer

## Writing Tests

### Test File Naming

- Test files should start with `test_`
- Example: `test_korean_text_processor.py`, `test_binary_matrix.py`

### Test Function Naming

- Test functions should start with `test_`
- Use descriptive names: `test_tokenize_korean_text_returns_nouns()`

### Example Test

```python
import pytest
from tnic.korean_text_processor import KoreanTextProcessor

def test_tokenize_korean_text(sample_korean_text):
    """Test that Korean text is properly tokenized."""
    processor = KoreanTextProcessor()
    tokens = processor.tokenize(sample_korean_text)

    assert isinstance(tokens, list)
    assert len(tokens) > 0
    assert all(isinstance(token, str) for token in tokens)

@pytest.mark.slow
def test_large_corpus_processing(temp_data_dir):
    """Test processing of large corpus (marked as slow)."""
    # ... test implementation ...
    pass
```

### Using Fixtures

Fixtures are defined in `conftest.py` and available to all tests:

```python
def test_with_sample_data(sample_korean_text, temp_data_dir):
    """Test using fixtures from conftest.py."""
    # sample_korean_text and temp_data_dir are automatically provided
    output_file = temp_data_dir / "output.txt"
    # ... test implementation ...
```

## Test Coverage

Generate HTML coverage report:

```bash
poetry run pytest tests/ --cov=tnic --cov-report=html
```

View report:
```bash
open htmlcov/index.html  # macOS/Linux
start htmlcov\index.html # Windows
```

## Continuous Integration

Tests should be run:
- Before committing code
- In CI/CD pipeline
- Before merging pull requests

## Test Data

- Use fixtures from `conftest.py` for sample data
- Use `temp_data_dir` fixture for temporary file operations
- Never commit test data to repository (use fixtures instead)

## Best Practices

1. **One assertion per test** (when possible)
2. **Use descriptive test names** that explain what is being tested
3. **Test edge cases** (empty input, invalid input, boundary conditions)
4. **Keep tests independent** (no test should depend on another)
5. **Use markers** to categorize tests (slow, integration, etc.)
6. **Mock external dependencies** (MongoDB, file system, etc.)

## Future Test Files

As we build the `tnic` module, we'll add test files:

- `test_korean_text_processor.py` - Korean text processing tests
- `test_corpus_builder.py` - Corpus building tests
- `test_binary_matrix.py` - Binary matrix construction tests
- `test_similarity.py` - Similarity computation tests
- `test_peer_groups.py` - TNIC peer group tests
- `test_integration.py` - End-to-end integration tests

## Troubleshooting

### Tests not found

Make sure:
- Test files start with `test_`
- Test functions start with `test_`
- Tests are in the `tests/` directory

### Import errors

Make sure:
- Poetry environment is activated: `poetry shell`
- Module is installed in development mode: `poetry install`
- Python path includes project root

### Fixture not found

Check:
- Fixture is defined in `conftest.py`
- Fixture name matches function parameter
- No typos in fixture name
