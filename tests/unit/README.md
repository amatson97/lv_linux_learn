# Unit Tests

This directory contains unit tests for individual components of the lv_linux_learn library.

## Contents

### Core Module Tests
- **test_repository.py** - ScriptRepository class tests
- **test_manifest.py** - ManifestLoader class tests
- **test_script_execution.py** - Script execution environment tests

### Additional Tests
- **test_repository_enhanced.py** - Enhanced repository functionality tests
- **test_config.py** - Configuration management tests

## Test Coverage

Current coverage includes:
- ✅ Repository operations (download, cache, update)
- ✅ Manifest parsing (local and remote)
- ✅ Script validation and execution
- ✅ Configuration handling
- ✅ Error handling and edge cases

## Running Tests

### Run All Unit Tests
```bash
pytest tests/unit/ -v
```

### Run Specific Test File
```bash
pytest tests/unit/test_repository.py -v
```

### Run Specific Test Class
```bash
pytest tests/unit/test_repository.py::TestRepository -v
```

### Run Specific Test
```bash
pytest tests/unit/test_repository.py::TestRepository::test_method_name -v
```

### Generate Coverage Report
```bash
pytest tests/unit/ --cov=lib --cov-report=html
```

## Test Structure

Each test file follows this structure:
```python
class TestComponent:
    """Test component functionality"""
    
    def setup_method(self):
        """Setup before each test"""
        pass
    
    def teardown_method(self):
        """Cleanup after each test"""
        pass
    
    def test_functionality(self):
        """Test specific functionality"""
        pass
```

## Mocking & Fixtures

Tests use:
- **pytest fixtures** - Reusable test setup
- **unittest.mock** - Mock objects and patches
- **conftest.py** - Shared fixtures

## Best Practices

1. **One assertion per test** - When possible
2. **Descriptive names** - Test name explains what it does
3. **Setup/teardown** - Clean test isolation
4. **No side effects** - Tests don't affect each other
5. **Fast execution** - Unit tests should be quick

## Related Directories

- **../integration/** - Integration tests
- **../e2e/** - End-to-end tests
- **../../lib/** - Library code being tested
- **../../tests/** - Parent test directory

## Status

✅ 90+ tests passing - Comprehensive test coverage
