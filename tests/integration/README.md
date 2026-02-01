# Integration Tests

This directory contains integration tests that verify components work together correctly.

## Purpose

Integration tests verify:
- **Component interaction** - Multiple components working together
- **System workflows** - Complete feature workflows
- **Dependency management** - Correct dependency injection
- **State management** - State changes across components

## Contents

Integration test files for:
- Repository and manifest interaction
- Script download and caching workflows
- Configuration and environment setup
- UI component integration

## Running Tests

### Run All Integration Tests
```bash
pytest tests/integration/ -v
```

### Run with Coverage
```bash
pytest tests/integration/ --cov=lib --cov-report=html
```

### Run with Markers
```bash
pytest tests/integration/ -m "not slow"
```

## Test Patterns

Integration tests typically:
1. Create realistic test data
2. Set up multiple components
3. Execute workflows
4. Verify state changes
5. Check side effects

Example:
```python
def test_script_download_and_cache():
    repo = ScriptRepository()
    manifest = repo.fetch_remote_manifest()
    
    script = repo.download_script(manifest.scripts[0])
    
    assert script.cached
    assert script.path.exists()
```

## Difference from Unit Tests

| Unit Tests | Integration Tests |
|-----------|------------------|
| Test single component | Test multiple components |
| Fast execution | Slower execution |
| Isolated (mocked) | Real dependencies |
| High test count | Lower test count |
| test_component.py | component_integration.py |

## Related Directories

- **../unit/** - Unit tests
- **../e2e/** - End-to-end tests
- **../../lib/** - Library code being tested
- **../../tests/** - Parent test directory

## Status

✅ Active - Integration tests run with unit tests
