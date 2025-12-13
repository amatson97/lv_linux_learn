## Description

Briefly describe what this PR accomplishes.

## Type of Change

- [ ] 🆕 New script (installation, tool, exercise, uninstaller)
- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📚 Documentation update
- [ ] 🔧 Refactoring (no functional changes)

## Script Details (if applicable)

**Script Name:** `example_script.sh`  
**Category:** install/tools/exercises/uninstall  
**Sudo Required:** Yes/No  
**Dependencies:** List any required packages or tools  

## Testing Checklist

- [ ] ✅ Tested on Ubuntu 24.04.3 LTS
- [ ] ✅ Script is idempotent (safe to run multiple times)
- [ ] ✅ Script appears correctly in menu
- [ ] ✅ No hardcoded secrets or credentials
- [ ] ✅ Proper error handling and user feedback
- [ ] ✅ Uninstaller tested (if applicable)
- [ ] ✅ Follows [Contributing Guidelines](https://github.com/amatson97/lv_linux_learn/blob/main/CONTRIBUTING.md)

## Security Review

- [ ] 🔒 No hardcoded API keys, tokens, or passwords
- [ ] 🔒 Uses environment variables or prompts for credentials
- [ ] 🔒 Input validation implemented
- [ ] 🔒 Sudo usage documented and justified
- [ ] 🔒 No network services exposed to 0.0.0.0 without warnings

## Documentation

- [ ] 📝 Added proper script header with Description
- [ ] 📝 Updated README.md (if major feature)
- [ ] 📝 Updated relevant docs/ files
- [ ] 📝 Added inline comments for complex logic

## Screenshots (if applicable)

Add screenshots showing:
- Menu integration
- Installation process
- Final result

## Additional Notes

Any additional information, dependencies, or context reviewers should know.

## Closes Issues

Closes #(issue_number)

---

### For Maintainers

- [ ] Manifest generation tested
- [ ] Both menu.sh and menu.py compatibility verified
- [ ] GitHub Actions workflow passes
- [ ] Security implications reviewed
- [ ] Community standards impact assessed