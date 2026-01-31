# Test Suite Quick Reference

## Current Status ✅
- **Total Tests**: 90
- **Passing**: 85 (94%)
- **Failing**: 5 (mostly pre-existing or test infrastructure)

## Test Organization

```
tests/
├── unit/                    # Fast, single-component tests (54 tests)
│   ├── test_checksums.py   # Checksum retry logic (8/8 ✅)
│   ├── test_manifest.py    # Manifest caching (2/2 ✅)
│   ├── test_repository.py  # Repository ops (23/24, 1 pre-existing)
│   └── test_script_execution.py  # Script execution (20/20 ✅)
├── integration/            # Component integration tests (25 tests)
│   └── test_install_duckstation.py  # Duckstation workflow (25/25 ✅)
├── e2e/                    # End-to-end workflows (11 tests)
│   └── test_workflows.py   # Complete workflows (7/11, 4 test setup issues)
└── conftest.py            # 16 shared pytest fixtures
```

## Running Tests

```bash
# All tests
pytest tests/

# By category
pytest tests/unit/          # ~0.1s - fastest, best for development
pytest tests/integration/   # ~0.05s - workflow validation
pytest tests/e2e/          # ~0.15s - complete workflows

# Specific test
pytest tests/unit/test_checksums.py::TestChecksumRetry::test_retry_on_hash_mismatch

# With options
pytest tests/unit/ -v       # Verbose
pytest tests/unit/ -x       # Stop on first failure
pytest tests/unit/ -k keyword  # Filter by name
```

## Key Files

| File | Purpose | Status |
|------|---------|--------|
| `conftest.py` | Shared fixtures (16) | ✅ Working |
| `unit/test_checksums.py` | Checksum retry tests | ✅ 8/8 passing |
| `unit/test_repository.py` | Repository operations | ⚠️ 23/24 (1 pre-existing) |
| `integration/test_install_duckstation.py` | Full workflow tests | ✅ 25/25 passing |
| `e2e/test_workflows.py` | E2E workflows | ⚠️ 7/11 (test setup issues) |

## Fixtures (from conftest.py)

Common fixtures available in all tests:

```python
# Directories
temp_dir              # Temporary test directory
mock_cache_dir        # Mock script cache
mock_config_dir       # Mock config directory

# Repositories
repo_with_temp_dirs   # Repository with temp dirs
repo_with_manifest    # Repository with test manifest
repo_with_cached_scripts  # Repository with cached scripts

# Helpers
TestHelpers           # Utility functions
create_mock_script()  # Create mock script file
create_mock_manifest()  # Create mock manifest
```

## Common Test Patterns

### Unit Test
```python
def test_something(repo_with_manifest):
    """Test a single component"""
    result = repo_with_manifest.some_method()
    assert result == expected
```

### Integration Test  
```python
def test_workflow(repo_with_cached_scripts, temp_dir):
    """Test multiple components together"""
    script = repo_with_cached_scripts.fetch()
    output = repo_with_cached_scripts.execute(script)
    assert output_is_valid(output)
```

### E2E Test
```python
def test_complete_flow():
    """Test full application workflow"""
    # Create repository
    # Fetch script
    # Cache script
    # Execute script
    # Verify results
```

## Known Issues

### 1. Pre-existing Failure
- **Test**: `test_is_update_check_needed_no_last_check`
- **Location**: `tests/unit/test_repository.py`
- **Status**: Pre-existing, not blocking refactoring

### 2. E2E Test Setup Issues
- **Tests**: 4 of 11 E2E tests fail
- **Cause**: Test fixtures use deprecated function signatures
- **Status**: Test infrastructure, not app bugs

## Development Workflow

1. **Write new test** in appropriate directory:
   ```bash
   # For new unit tests
   tests/unit/test_myfeature.py
   
   # For integration tests
   tests/integration/test_myfeature.py
   ```

2. **Use fixtures from conftest.py**:
   ```python
   def test_feature(repo_with_manifest, temp_dir):
       # Tests use shared fixtures
   ```

3. **Run tests**:
   ```bash
   pytest tests/unit/ -v    # Full unit tests
   pytest tests/unit/test_myfeature.py  # Specific test
   ```

4. **Before committing**:
   ```bash
   pytest tests/ -q         # Quick validation
   ```

## Performance

- Unit tests: **~100ms total** (best for rapid iteration)
- Integration tests: **~50ms total**
- E2E tests: **~150ms total**
- Full suite: **~450ms**

Recommendation: Run `pytest tests/unit/` during development for fast feedback loop.

## Maintenance

### When adding new tests:
1. Follow directory structure (unit/integration/e2e)
2. Use fixtures from conftest.py to reduce duplication
3. Keep unit tests fast (< 1s each)
4. Use descriptive test names

### When debugging failures:
```bash
pytest tests/ -v --tb=short    # Verbose + short traceback
pytest tests/ -x               # Stop on first failure
pytest tests/ -k testname      # Run specific test
```

### When modifying fixtures:
- Update conftest.py
- All tests automatically use new fixture version
- No need to update individual test files

---

Generated: 2025-01-31
Phase 2 Refactoring: Complete ✅
