# Repository Update Tests - README

## Overview

This test suite (`test_repository_updates.py`) provides comprehensive unit testing for the script updater functionality in the `lv_linux_learn` menu.py application.

## Test Coverage

The suite contains **22 tests** organized into **7 test classes**:

### Test Classes

1. **TestUpdateCheckTiming** (5 tests)
   - Validates update check throttling logic
   - Tests timing intervals and edge cases
   - Status: ✓ All passing

2. **TestCheckForUpdates** (6 tests)
   - Tests the core `check_for_updates()` method
   - Identifies update availability
   - Status: ✗ 3 failures, 3 passes

3. **TestUpdateAllScripts** (3 tests)
   - Tests batch update installation
   - Validates the `update_all_scripts()` method
   - Status: ✓ All passing

4. **TestListAvailableUpdates** (3 tests)
   - Tests listing available updates
   - Validates `list_available_updates()` method
   - Status: ✓ All passing

5. **TestManifestParsing** (3 tests)
   - Tests manifest parsing with different formats
   - Validates `parse_manifest()` method
   - Status: ✓ All passing

6. **TestChecksumHandling** (1 test)
   - Tests checksum verification
   - Validates mismatch detection
   - Status: ✓ All passing

7. **TestIntegrationScenarios** (1 test)
   - End-to-end workflow testing
   - Tests full update cycle
   - Status: ✗ 1 failure

## Issues Identified

### Critical Issues: 3

1. **Checksum Comparison Failure** (HIGH IMPACT)
   - Location: `lib/repository.py:408-415`
   - Impact: Cannot detect script updates
   - Tests affected: 3

2. **Timestamp Not Persisted** (MEDIUM IMPACT)
   - Location: `lib/repository.py:417`
   - Impact: Throttling uses stale timestamps
   - Tests affected: 1

3. **Auto-Install Not Triggered** (MEDIUM IMPACT)
   - Location: `lib/repository.py:420-425`
   - Impact: Auto-update feature broken
   - Tests affected: 1 (depends on #1)

## Quick Start

### Installation

```bash
cd /home/adam/lv_linux_learn

# Install pytest if needed
python3 -m pip install pytest pytest-cov
```

### Running Tests

```bash
# Run all tests with verbose output
python3 -m pytest tests/test_repository_updates.py -v

# Run specific test class
python3 -m pytest tests/test_repository_updates.py::TestCheckForUpdates -v

# Run specific test
python3 -m pytest tests/test_repository_updates.py::TestCheckForUpdates::test_check_for_updates_detects_updated_scripts -vv

# Run with coverage
python3 -m pytest tests/test_repository_updates.py --cov=lib.repository --cov-report=term-missing

# Run with detailed output
python3 -m pytest tests/test_repository_updates.py -vv --tb=long
```

## Test Results

### Current Status
- **Total**: 22 tests
- **Passing**: 18 (82%)
- **Failing**: 4 (18%)

### Passing Tests ✓

```
TestUpdateCheckTiming
  ✓ test_is_update_check_needed_no_last_check
  ✓ test_is_update_check_needed_within_interval
  ✓ test_is_update_check_needed_past_interval
  ✓ test_is_update_check_needed_custom_interval
  ✓ test_is_update_check_needed_invalid_timestamp

TestCheckForUpdates
  ✓ test_check_for_updates_manifest_fetch_fails
  ✓ test_check_for_updates_no_cached_scripts
  ✓ test_check_for_updates_ignores_unchanged_scripts

TestUpdateAllScripts
  ✓ test_update_all_scripts_only_updates_cached
  ✓ test_update_all_scripts_counts_failures
  ✓ test_update_all_scripts_returns_tuple

TestListAvailableUpdates
  ✓ test_list_available_updates_identifies_changed_scripts
  ✓ test_list_available_updates_excludes_unchanged
  ✓ test_list_available_updates_ignores_uncached_scripts

TestManifestParsing
  ✓ test_parse_manifest_flat_format
  ✓ test_parse_manifest_nested_format
  ✓ test_parse_manifest_missing_file

TestChecksumHandling
  ✓ test_checksum_mismatch_detection

Total: 18 passing ✓
```

### Failing Tests ✗

```
TestCheckForUpdates
  ✗ test_check_for_updates_detects_updated_scripts
    → Expects return > 0, gets 0
    → Root cause: Issue #1

  ✗ test_check_for_updates_updates_timestamp
    → Timestamp is stale, not current
    → Root cause: Issue #2

  ✗ test_check_for_updates_auto_install_enabled
    → update_all_scripts_silent() not called
    → Root cause: Issue #3

TestIntegrationScenarios
  ✗ test_full_update_workflow
    → Complete workflow fails
    → Root cause: Issues #1-3

Total: 4 failing ✗
```

## How Tests Work

### Test Fixtures

Tests use temporary directories to avoid affecting the user's actual configuration:

```python
@pytest.fixture
def repo_with_temp_dirs(self):
    """Create repository with temporary directories"""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = ScriptRepository()
        # Override paths to use temp directory
        repo.config_dir = Path(tmpdir) / ".lv_linux_learn"
        # ...
        yield repo
```

### Mocking

Tests use `unittest.mock` to simulate:
- Network requests (`fetch_remote_manifest`)
- File downloads (`download_script`)
- Remote operations

### Sample Test

```python
def test_check_for_updates_manifest_fetch_fails(self, repo_with_temp_dirs):
    """Should return 0 when remote manifest fetch fails"""
    repo = repo_with_temp_dirs
    mock_fetch = Mock(return_value=False)
    repo.fetch_remote_manifest = mock_fetch
    
    result = repo.check_for_updates()
    
    assert result == 0
    mock_fetch.assert_called_once()
```

## Related Documentation

- **[UPDATE_FUNCTIONALITY_ANALYSIS.md](UPDATE_FUNCTIONALITY_ANALYSIS.md)**
  - Detailed issue analysis with code examples
  - Root cause explanation
  - Recommended fixes

- **[UPDATE_TESTING_GUIDE.md](UPDATE_TESTING_GUIDE.md)**
  - How to run tests
  - Debug procedures for each failure
  - Manual testing in GUI
  - Common issues & solutions

- **[TEST_RESULTS_SUMMARY.md](TEST_RESULTS_SUMMARY.md)**
  - Complete test results
  - Issue correlation matrix
  - Code coverage analysis

- **[UPDATE_ISSUES_QUICK_REF.md](UPDATE_ISSUES_QUICK_REF.md)**
  - Quick reference card
  - Issue summary
  - Impact analysis

## File Locations

| File | Purpose | Status |
|------|---------|--------|
| `tests/test_repository_updates.py` | Test suite | ✓ Created (22 tests) |
| `lib/repository.py` | Implementation | ✗ 3 issues found |
| `menu.py` | GUI integration | ✓ Works correctly |

## Dependencies

- Python 3.7+
- pytest
- unittest.mock (built-in)
- pathlib (built-in)
- json (built-in)
- tempfile (built-in)

## Contributing to Tests

### Adding a New Test

1. Create a new test class inheriting from `object` (or existing class)
2. Add `repo_with_temp_dirs` fixture as needed
3. Name test `test_<what_it_tests>`
4. Use descriptive docstring
5. Make assertions clear

```python
def test_new_feature(self, repo_with_temp_dirs):
    """Test description here"""
    repo = repo_with_temp_dirs
    
    # Setup
    # ... prepare test data
    
    # Execute
    result = repo.some_method()
    
    # Assert
    assert result == expected_value
```

### Test Naming Convention

- `test_<feature>_<scenario>` - What is being tested and under what conditions
- Examples:
  - `test_check_for_updates_detects_updated_scripts`
  - `test_update_all_scripts_counts_failures`
  - `test_parse_manifest_nested_format`

## Debugging Failed Tests

### Option 1: Run with Verbose Output
```bash
python3 -m pytest tests/test_repository_updates.py -vv --tb=long
```

### Option 2: Run Single Failing Test
```bash
python3 -m pytest tests/test_repository_updates.py::TestCheckForUpdates::test_check_for_updates_detects_updated_scripts -vv
```

### Option 3: Add Print Statements
```python
# Temporarily add debug output in test
def test_something(self, repo_with_temp_dirs):
    repo = repo_with_temp_dirs
    print(f"\nDEBUG: manifest_file = {repo.manifest_file}")
    # ...
```

Then run with `-s` flag to see prints:
```bash
python3 -m pytest tests/test_repository_updates.py::TestCheckForUpdates::test_check_for_updates_detects_updated_scripts -vv -s
```

## Performance

- Full suite completes in < 1 second
- Individual test typically < 100ms
- No external network calls (all mocked)
- Uses temporary directories (no I/O conflicts)

## Future Improvements

- [ ] Add performance benchmarks
- [ ] Add tests for custom manifest repositories
- [ ] Add tests for network timeout scenarios
- [ ] Add tests for corrupted manifest handling
- [ ] Add tests for checksum format variations
- [ ] Add parametrized tests for multiple manifest formats
- [ ] Add CI/CD integration (GitHub Actions)
- [ ] Add coverage reports

## Troubleshooting

### pytest not found
```bash
python3 -m pip install pytest
```

### Import errors
```bash
export PYTHONPATH=/home/adam/lv_linux_learn:$PYTHONPATH
```

### Permission errors
```bash
chmod 755 ~/.lv_linux_learn/script_cache/
```

### Tests timeout
```bash
python3 -m pytest tests/test_repository_updates.py --timeout=30
```

## Summary

This test suite successfully identifies **3 critical issues** in the script updater functionality. With **82% test pass rate** and comprehensive documentation, it provides a solid foundation for:

1. Understanding the issues
2. Implementing fixes
3. Validating fixes work correctly
4. Preventing regression

The test suite will continue to be valuable for ongoing development and maintenance.

---

**File**: `tests/test_repository_updates.py`  
**Created**: January 31, 2026  
**Lines of Code**: ~650  
**Test Count**: 22  
**Status**: Ready for fix implementation
