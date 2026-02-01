# Test Suite Refactoring Plan

## Current State Analysis

### Existing Test Files
1. **test_repository_updates.py** (730 lines) - Repository update logic
2. **test_checksum_retry_and_updates.py** (454 lines) - Checksum verification
3. **test_install_duckstation.py** (342 lines) - Specific install script
4. **test_script_execution.py** (332 lines) - Script execution logic
5. **test_manifest_cache.py** (78 lines) - Manifest caching
6. **run_tests.py** (222 lines) - Legacy test runner

**Total: ~2,158 lines across 6 files**

### Test Coverage Gaps
- ✅ Repository operations (well covered)
- ✅ Script execution (well covered)
- ✅ Checksum handling (well covered)
- ⚠️  UI integration (minimal - only specific scripts)
- ❌ End-to-end workflows (missing)
- ❌ Multi-component integration (missing)
- ❌ GTK UI components (no coverage)
- ❌ Configuration persistence (partial)

---

## Refactoring Strategy

### Phase 1: Centralize Fixtures ✅ COMPLETE
- [x] Create `conftest.py` with shared fixtures
- [x] Move common setup code from individual tests
- [x] Add helper classes for test data generation
- [x] Create GTK mocking infrastructure

**Benefits:**
- Reduced code duplication (~30% reduction potential)
- Consistent test setup across files
- Easier to add new tests

### Phase 2: Add End-to-End Tests ✅ COMPLETE
- [x] Create `test_e2e_integration.py`
- [x] Test complete user workflows
- [x] Test cross-component interactions
- [x] Add performance benchmarks

**Coverage Added:**
- Full lifecycle: fetch → cache → update → execute
- Error recovery scenarios
- Multi-repository workflows
- Configuration persistence
- CDN cache-busting flow

### Phase 3: Consolidate & Organize (RECOMMENDED NEXT)
```
tests/
├── conftest.py                 # Shared fixtures (DONE)
├── test_e2e_integration.py     # E2E tests (DONE)
│
├── unit/                       # Unit tests (pure logic)
│   ├── test_repository.py      # Consolidate repository_updates.py
│   ├── test_script_execution.py  # Already good
│   ├── test_manifest.py        # Consolidate manifest_cache.py
│   └── test_checksums.py       # From checksum_retry_and_updates.py
│
├── integration/                # Integration tests
│   ├── test_repository_cache.py
│   ├── test_script_install_flows.py
│   └── test_duckstation.py     # Move from root
│
└── ui/                         # UI-specific tests (future)
    ├── test_menu_window.py
    ├── test_tab_management.py
    └── test_terminal_integration.py
```

### Phase 4: UI Testing Infrastructure (FUTURE)
```python
# Planned additions to conftest.py
@pytest.fixture
def mock_menu_app():
    """Mock complete menu.py application"""
    pass

@pytest.fixture  
def mock_tab_manager():
    """Mock GTK tab management"""
    pass

# New test file: tests/ui/test_menu_integration.py
class TestMenuAppLifecycle:
    def test_app_initialization(self, mock_gtk):
        """Test menu.py startup sequence"""
        pass
    
    def test_tab_creation_all_categories(self, mock_gtk):
        """Test all tabs created correctly"""
        pass
    
    def test_script_selection_and_execution(self, mock_gtk, mock_terminal):
        """Test clicking script → execution flow"""
        pass
```

---

## Refactoring Execution Plan

### Step 1: Run Current Test Suite Baseline
```bash
pytest tests/ -v --tb=short > baseline_results.txt
pytest tests/ --cov=lib --cov-report=html
```

### Step 2: Move Tests to New Structure
```bash
# Create new directories
mkdir -p tests/{unit,integration,ui}

# Move existing tests
mv tests/test_repository_updates.py tests/unit/test_repository.py
mv tests/test_checksum_retry_and_updates.py tests/unit/test_checksums.py
mv tests/test_manifest_cache.py tests/unit/test_manifest.py
mv tests/test_install_duckstation.py tests/integration/

# Update imports in moved files
```

### Step 3: Refactor Individual Test Files

#### tests/unit/test_repository.py
```python
# Remove duplicate fixtures (use conftest.py)
- @pytest.fixture repo_with_temp_dirs  # Use from conftest
+ Use shared fixtures

# Consolidate similar tests
- test_check_for_updates_no_cached_scripts
- test_check_for_updates_detects_updated_scripts
+ test_check_for_updates_various_states (parametrized)
```

#### tests/unit/test_checksums.py
```python
# Keep focused on checksum logic
# Remove integration aspects (move to integration/)
@pytest.mark.parametrize("scenario", [
    "stale_cdn_cache",
    "corrupted_local_file",
    "missing_checksum",
    "sha256_prefix_handling"
])
def test_checksum_verification(scenario, repo_with_temp_dirs):
    # Parametrized test covering all scenarios
    pass
```

### Step 4: Add Missing Test Coverage

```python
# tests/integration/test_script_install_flows.py
class TestCompleteInstallFlow:
    """Integration test for complete script installation"""
    
    def test_install_docker_full_flow(self):
        """Test Docker install from manifest → cache → desktop launcher"""
        pass
    
    def test_install_chrome_with_dependencies(self):
        """Test Chrome install including dependency checks"""
        pass
```

### Step 5: Validate Refactoring
```bash
# Run full suite
pytest tests/ -v

# Check coverage improved
pytest tests/ --cov=lib --cov-report=term-missing

# Run only E2E tests
pytest tests/ -m e2e -v

# Run fast unit tests
pytest tests/unit/ -v
```

---

## Test Organization Principles

### Test Naming Convention
```python
# Unit tests
def test_<function>_<scenario>_<expected_result>():
    """test_download_script_checksum_mismatch_raises_error"""
    pass

# Integration tests  
def test_<component>_<component>_<workflow>():
    """test_repository_cache_update_workflow"""
    pass

# E2E tests
def test_<user_action>_<complete_flow>():
    """test_install_script_from_manifest_to_execution"""
    pass
```

### Fixture Hierarchy
```
conftest.py (root fixtures)
  ├── temp_dir
  ├── repo_with_temp_dirs
  │   ├── repo_with_manifest
  │   │   └── repo_with_cached_scripts
  │   └── repo_with_config
  └── mock_gtk
      └── mock_menu_app
```

### Marker Strategy
```ini
[pytest.ini]
markers =
    unit: Fast, isolated unit tests (< 0.1s each)
    integration: Multi-component integration (< 1s each)
    e2e: Complete workflows (< 5s each)
    ui: Requires GTK mocking
    slow: Tests taking > 5s
    network: Requires network access (skipped in CI)
```

---

## Migration Checklist

### Immediate Actions (Next PR)
- [ ] Run baseline test suite and record results
- [ ] Apply conftest.py (DONE ✅)
- [ ] Add e2e_integration.py (DONE ✅)
- [ ] Run tests, ensure all pass
- [ ] Create unit/ directory
- [ ] Move test_repository_updates.py → unit/test_repository.py
- [ ] Update imports, run tests
- [ ] Move test_script_execution.py → unit/ (already clean)
- [ ] Move remaining unit tests

### Short-term (1-2 weeks)
- [ ] Create integration/ directory structure
- [ ] Move test_install_duckstation.py → integration/
- [ ] Create test_script_install_flows.py
- [ ] Add parametrized tests to reduce duplication
- [ ] Consolidate similar test methods
- [ ] Document test patterns in README

### Long-term (Future Sprints)
- [ ] Add UI testing infrastructure
- [ ] Create tests/ui/ directory
- [ ] Mock GTK components for menu.py testing
- [ ] Add visual regression tests (if needed)
- [ ] Set up CI/CD test automation
- [ ] Add performance regression tests

---

## Expected Outcomes

### Code Quality Metrics
- **Code Duplication:** -30% (through shared fixtures)
- **Test Execution Time:** -20% (better organization, parallel execution)
- **Coverage:** +15% (E2E tests cover integration gaps)
- **Maintainability:** +40% (clearer organization, less redundancy)

### Developer Experience
- ✅ Easier to find relevant tests
- ✅ Faster to add new tests (fixtures ready)
- ✅ Better test failure isolation
- ✅ Clearer test documentation

### Test Pyramid Balance
```
Current:              Target:
      E2E: 0%              E2E: 10% (e2e tests)
Integration: 30%   Integration: 30% (unchanged)
       Unit: 70%          Unit: 60% (consolidated)
```

---

## Running Refactored Tests

### All Tests
```bash
pytest tests/
```

### By Category
```bash
pytest tests/unit/          # Fast unit tests
pytest tests/integration/   # Integration tests
pytest tests/e2e_integration.py  # E2E workflows
```

### By Marker
```bash
pytest -m unit              # Only unit tests
pytest -m "e2e and not slow"  # E2E excluding slow tests
pytest -m "not ui"          # Skip UI tests (for headless CI)
```

### With Coverage
```bash
pytest tests/ --cov=lib --cov=menu --cov-report=html
# Opens htmlcov/index.html for detailed report
```

### Debug Single Test
```bash
pytest tests/unit/test_repository.py::TestCheckForUpdates::test_detects_updates -vv -s
```

---

## Next Steps

1. **Review and approve** this refactoring plan
2. **Run baseline** tests and record current state
3. **Execute Phase 3** (Consolidate & Organize)
4. **Measure improvement** against baseline
5. **Plan Phase 4** (UI testing) based on Phase 3 results
