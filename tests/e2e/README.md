# End-to-End (E2E) Tests

This directory contains end-to-end tests that verify complete user workflows and system functionality.

## Purpose

E2E tests verify:
- **Complete workflows** - Full user scenarios from start to finish
- **Real environments** - Tests against actual components (not mocks)
- **User experience** - Functionality from user perspective
- **Integration** - All system components working together

## Contents

End-to-end test files for:
- Script repository workflows
- Installation and configuration
- User interactions with CLI/GUI
- Full lifecycle operations

## Test Scenarios

E2E tests cover scenarios like:
1. **User installs lv_linux_learn** → Can run menu.py → See script list
2. **User downloads a script** → Script appears in cache → Can execute it
3. **User configures custom repository** → Scripts available → Can run them
4. **User updates scripts** → Checks remote manifest → Downloads updates

## Running Tests

### Run All E2E Tests
```bash
pytest tests/e2e/ -v
```

### Run with Extended Output
```bash
pytest tests/e2e/ -vvs
```

### Run Specific E2E Test
```bash
pytest tests/e2e/test_workflow.py::test_full_installation -v
```

### Run with Markers
```bash
pytest tests/e2e/ -m "smoke"
```

## Test Execution Time

E2E tests take longer than unit/integration tests due to:
- Real file I/O
- Network operations
- Environment setup/teardown
- Full component initialization

## Comparison: Test Pyramid

```
       E2E Tests (10)
      /            \
    Integration    (30)
   /                \
Unit Tests      (90+)
```

## Related Directories

- **../unit/** - Unit tests
- **../integration/** - Integration tests
- **../../lib/** - Library code being tested
- **../../tests/** - Parent test directory

## Status

✅ Active - E2E tests verify critical user workflows
