# Testing Guide for lv_linux_learn

## Overview

Business logic has been extracted from UI code into testable modules to enable automated testing and improve code quality.

## Test Structure

```
tests/
├── __init__.py                    # Makes tests a package
├── test_script_execution.py       # Tests for lib/script_execution.py
└── conftest.py                    # Shared pytest fixtures (to be added)
```

## Extracted Modules

### `lib/script_execution.py`

Pure business logic separated from GTK UI concerns:

- **ScriptEnvironmentManager**: Environment variable detection, validation, and export generation
- **ScriptExecutionContext**: Script type determination and command building
- **ScriptValidator**: Path and execution readiness validation
- **Convenience functions**: High-level APIs for common operations

### Benefits of Extraction

1. **Testable**: Pure functions without GTK dependencies
2. **Reusable**: Logic can be used by both GUI and CLI
3. **Maintainable**: Clear separation of concerns
4. **Documented**: Self-contained with clear interfaces

## Running Tests

### Install Dependencies

```bash
# Install pytest
pip install pytest pytest-cov pytest-mock

# Or using apt (Ubuntu)
sudo apt install python3-pytest
```

### Run All Tests

```bash
# From tests directory
cd tests && pytest

# With coverage
cd tests && pytest --cov=../lib --cov-report=term-missing

# Verbose output
cd tests && pytest -v

# Specific test file
cd tests && pytest test_script_execution.py

# Specific test class
cd tests && pytest test_script_execution.py::TestScriptEnvironmentManager

# Specific test
cd tests && pytest test_script_execution.py::TestScriptEnvironmentManager::test_validate_env_var_zerotier_valid
```

### Test Markers

Tests can be marked for selective execution:

```bash
# Run only unit tests
cd tests && pytest -m unit

# Run only integration tests
cd tests && pytest -m integration

# Skip slow tests
cd tests && pytest -m "not slow"
```

## Writing Tests

### Example: Testing Environment Variable Validation

```python
def test_validate_env_var_zerotier_valid():
    """Valid ZeroTier network IDs should pass validation"""
    manager = ScriptEnvironmentManager()
    
    # Test valid input
    is_valid, error = manager.validate_env_var(
        'ZEROTIER_NETWORK_ID', 
        '8bd5124fd60a971f'
    )
    
    assert is_valid is True
    assert error == ""
```

### Example: Testing Command Building

```python
def test_build_execution_command_with_env_exports():
    """Environment exports should be prepended to command"""
    context = ScriptExecutionContext()
    
    command = context.build_execution_command(
        script_path='/home/user/script.sh',
        script_type='local',
        source_type='custom_local',
        env_exports="export VAR1='val1'; ",
        use_source=True
    )
    
    assert command.startswith("export VAR1='val1'; ")
    assert 'source' in command
```

## Test Coverage Goals

- **Unit Tests**: >80% coverage of business logic
- **Integration Tests**: Key workflows (download → cache → execute)
- **Edge Cases**: Invalid inputs, missing files, permission errors

## Current Test Status

✅ **Implemented:**
- ScriptEnvironmentManager validation tests
- ScriptExecutionContext command building tests
- ScriptValidator path validation tests
- Convenience function integration tests

🔄 **To Add:**
- menu.sh bash function tests (using bats)
- GTK UI interaction tests (using pytest-gtk)
- Full workflow integration tests
- Performance/load tests

## Continuous Integration

### GitHub Actions Example

```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y python3-pytest
          pip install pytest pytest-cov
      
      - name: Run tests
        run: |
          pytest --cov=lib --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Testing Best Practices

1. **One Assertion per Test**: Keep tests focused
2. **Descriptive Names**: Test names should describe what they verify
3. **Arrange-Act-Assert**: Structure tests clearly
4. **Use Fixtures**: Share common setup via pytest fixtures
5. **Mock External Dependencies**: Isolate units being tested
6. **Test Edge Cases**: Empty inputs, invalid data, boundary conditions

## Adding New Tests

When adding new functionality:

1. **Extract business logic** to `lib/` modules
2. **Write tests first** (TDD approach)
3. **Implement logic** to pass tests
4. **Integrate with UI** (menu.py or menu.sh)
5. **Add integration test** for full workflow

## Debugging Tests

```bash
# Print output during tests
pytest -s

# Drop into debugger on failure
pytest --pdb

# Run last failed tests
pytest --lf

# Show local variables on failure
pytest -l
```

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/)
- [Test-Driven Development](https://en.wikipedia.org/wiki/Test-driven_development)
