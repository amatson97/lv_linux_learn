"""
Unit tests for install_duckstation.sh script

Tests script logic including:
- Wrapper script creation for X11/Wayland compatibility
- Desktop file generation
- Icon extraction and setup
- Environment variable handling

Run with: python3 tests/test_install_duckstation.py
"""

"""
Unit tests for install_duckstation.sh script

Tests script logic including:
- Wrapper script creation for X11/Wayland compatibility
- Desktop file generation
- Icon extraction and setup
- Environment variable handling

Run with: python3 tests/test_install_duckstation.py
"""

import sys
import os
from pathlib import Path


class SimpleTestRunner:
    """Simple test runner without pytest dependency"""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def assert_true(self, condition, msg=""):
        if not condition:
            self.errors.append(f"✗ {msg}")
            self.failed += 1
            return False
        self.passed += 1
        return True
    
    def assert_in(self, needle, haystack, msg=""):
        if needle not in haystack:
            self.errors.append(f"✗ {msg}\n    '{needle}' not found")
            self.failed += 1
            return False
        self.passed += 1
        return True
    
    def assert_not_in(self, needle, haystack, msg=""):
        if needle in haystack:
            self.errors.append(f"✗ {msg}\n    '{needle}' should not be present")
            self.failed += 1
            return False
        self.passed += 1
        return True
    
    def print_results(self):
        print("\n" + "="*70)
        print(f"Test Results: {self.passed} passed, {self.failed} failed")
        print("="*70)
        if self.errors:
            print("\nFailures:")
            for error in self.errors:
                print(f"  {error}")
        return self.failed == 0


# Initialize test runner
runner = SimpleTestRunner()


class TestDuckStationWrapperScript:
    """Test wrapper script generation for X11/Wayland support"""
    
    @staticmethod
    def get_script_content():
        script_path = Path(__file__).parent.parent / "scripts" / "install_ducksation.sh"
        with open(script_path) as f:
            return f.read()
    
    @staticmethod
    def get_wrapper_content():
        """Extract wrapper script content from install script"""
        content = TestDuckStationWrapperScript.get_script_content()
        start = content.find("cat > \"$WRAPPER_SCRIPT\" << 'WRAPPER_EOF'")
        start = content.find("#!/usr/bin/env bash", start)
        end = content.find("WRAPPER_EOF", start)
        
        if start == -1 or end == -1:
            return None
        
        return content[start:end].strip()
    
    def test_wrapper_script_x11_detection(self):
        wrapper = self.get_wrapper_content()
        runner.assert_true(wrapper is not None, "Wrapper script should exist")
        runner.assert_in("XDG_SESSION_TYPE", wrapper, "Should detect XDG_SESSION_TYPE")
        runner.assert_in("x11", wrapper, "Should reference x11")
        
    def test_wrapper_script_wayland_support(self):
        wrapper = self.get_wrapper_content()
        runner.assert_true(wrapper is not None, "Wrapper script should exist")
        runner.assert_in('== "wayland"', wrapper, "Should check for Wayland")
        runner.assert_in('QT_QPA_PLATFORM="wayland"', wrapper, "Should set QT platform for Wayland")
        runner.assert_in("QT_QPA_PLATFORM_PLUGIN_PATH", wrapper, "Should set plugin path")
    
    def test_wrapper_script_executes_appimage(self):
        wrapper = self.get_wrapper_content()
        runner.assert_true(wrapper is not None, "Wrapper script should exist")
        runner.assert_in('exec "$APPIMAGE_DIR/$APPIMAGE_NAME"', wrapper, "Should execute AppImage")
    
    def test_wrapper_script_is_bash(self):
        wrapper = self.get_wrapper_content()
        runner.assert_true(wrapper is not None, "Wrapper script should exist")
        runner.assert_in("#!/usr/bin/env bash", wrapper, "Should use bash shebang")


class TestDuckStationDesktopFile:
    """Test desktop file generation"""
    
    @staticmethod
    def get_desktop_file_template():
        """Extract desktop file template from install script"""
        script_path = Path(__file__).parent.parent / "scripts" / "install_ducksation.sh"
        with open(script_path) as f:
            content = f.read()
        
        start = content.find('cat > "$DESKTOP_TARGET" << EOF')
        start = content.find("[Desktop Entry]", start)
        end = content.find("EOF", start)
        
        if start == -1 or end == -1:
            return None
        
        return content[start:end].strip()
    
    def test_desktop_file_has_required_fields(self):
        desktop = self.get_desktop_file_template()
        runner.assert_true(desktop is not None, "Desktop file template should exist")
        runner.assert_in("[Desktop Entry]", desktop, "Should have Desktop Entry header")
        runner.assert_in("Version=1.0", desktop, "Should have Version field")
        runner.assert_in("Type=Application", desktop, "Should have Type field")
        runner.assert_in("Name=DuckStation", desktop, "Should have Name field")
        runner.assert_in("Comment=Fast PlayStation 1 Emulator", desktop, "Should have Comment field")
    
    def test_desktop_file_uses_wrapper_script(self):
        desktop = self.get_desktop_file_template()
        runner.assert_true(desktop is not None, "Desktop file template should exist")
        runner.assert_in("Exec=$WRAPPER_SCRIPT", desktop, "Should use wrapper script")
        runner.assert_not_in("Exec=$APPIMAGE_DIR/$APPIMAGE_NAME", desktop, "Should not reference AppImage directly")
    
    def test_desktop_file_has_startupwmclass(self):
        desktop = self.get_desktop_file_template()
        runner.assert_true(desktop is not None, "Desktop file template should exist")
        runner.assert_in("StartupWMClass=AppRun.wrapped", desktop, "Should have correct StartupWMClass")
    
    def test_desktop_file_has_categories(self):
        desktop = self.get_desktop_file_template()
        runner.assert_true(desktop is not None, "Desktop file template should exist")
        runner.assert_in("Categories=Game;Emulator;", desktop, "Should have Game and Emulator categories")
    
    def test_desktop_file_is_not_terminal(self):
        desktop = self.get_desktop_file_template()
        runner.assert_true(desktop is not None, "Desktop file template should exist")
        runner.assert_in("Terminal=false", desktop, "Should not run in terminal")


class TestDuckStationConfiguration:
    """Test script configuration and paths"""
    
    @staticmethod
    def get_script_content():
        script_path = Path(__file__).parent.parent / "scripts" / "install_ducksation.sh"
        with open(script_path) as f:
            return f.read()
    
    def test_appimage_variables_defined(self):
        content = self.get_script_content()
        runner.assert_in('APPIMAGE_DIR="$HOME/Applications"', content, "Should define APPIMAGE_DIR")
        runner.assert_in('APPIMAGE_NAME="DuckStation-x64.AppImage"', content, "Should define APPIMAGE_NAME")
        runner.assert_in('APPIMAGE_URL=', content, "Should define APPIMAGE_URL")
    
    def test_installation_directories_created(self):
        content = self.get_script_content()
        runner.assert_in('mkdir -p "$ICON_DIR"', content, "Should create icon directory")
        runner.assert_in('mkdir -p "$HOME/.local/share/applications"', content, "Should create applications directory")
        runner.assert_in('mkdir -p "$HOME/.local/share/pixmaps"', content, "Should create pixmaps directory")
    
    def test_icon_directories_follow_xdg_spec(self):
        content = self.get_script_content()
        runner.assert_in("$HOME/.local/share/icons/hicolor", content, "Should use XDG icons directory")
        runner.assert_in("$HOME/.local/share/pixmaps", content, "Should use XDG pixmaps directory")
        runner.assert_in("$HOME/.local/share/applications", content, "Should use XDG applications directory")


class TestDuckStationSafety:
    """Test script safety and error handling"""
    
    @staticmethod
    def get_script_content():
        script_path = Path(__file__).parent.parent / "scripts" / "install_ducksation.sh"
        with open(script_path) as f:
            return f.read()
    
    def test_script_has_strict_mode(self):
        content = self.get_script_content()
        runner.assert_in("set -euo pipefail", content, "Should enable strict bash mode")
    
    def test_script_has_proper_shebang(self):
        content = self.get_script_content()
        runner.assert_true(content.startswith("#!/usr/bin/env bash"), "Should have bash shebang")
    
    def test_temp_directory_cleanup(self):
        content = self.get_script_content()
        runner.assert_in('trap "rm -rf $TMP_DIR" EXIT', content, "Should have trap for cleanup")
        runner.assert_in('TMP_DIR=$(mktemp -d)', content, "Should create temp directory")
    
    def test_script_sources_shared_helpers(self):
        content = self.get_script_content()
        runner.assert_in('source "$repo_root/includes/main.sh"', content, "Should source shared helpers")
        runner.assert_in('green_echo', content, "Should use green_echo helper")


class TestDuckStationIconHandling:
    """Test icon extraction and setup logic"""
    
    @staticmethod
    def get_script_content():
        script_path = Path(__file__).parent.parent / "scripts" / "install_ducksation.sh"
        with open(script_path) as f:
            return f.read()
    
    def test_icon_search_strategy(self):
        content = self.get_script_content()
        runner.assert_in("*512x512*", content, "Should search 512x512 icons first")
        runner.assert_in("duck|logo", content, "Should search for branded icons")
        runner.assert_in("*/pixmaps/*", content, "Should search pixmaps")
        runner.assert_in("*/icons/*", content, "Should search icons")
    
    def test_icon_fallback_handling(self):
        content = self.get_script_content()
        runner.assert_in("applications-games", content, "Should have fallback icon")
    
    def test_icon_installed_to_multiple_locations(self):
        content = self.get_script_content()
        runner.assert_in('cp "$ICON_FILE" "$ICON_DIR/duckstation.png"', content, "Should copy to icon directory")
        runner.assert_in('cp "$ICON_FILE" "$HOME/.local/share/pixmaps/duckstation.png"', content, "Should copy to pixmaps")


class TestDuckStationIntegration:
    """Test desktop integration steps"""
    
    @staticmethod
    def get_script_content():
        script_path = Path(__file__).parent.parent / "scripts" / "install_ducksation.sh"
        with open(script_path) as f:
            return f.read()
    
    def test_desktop_file_trusted_by_gnome(self):
        content = self.get_script_content()
        runner.assert_in('gio set "$DESKTOP_TARGET" metadata::trusted true', content, "Should mark desktop file as trusted")
    
    def test_desktop_file_validation(self):
        content = self.get_script_content()
        runner.assert_in("desktop-file-validate", content, "Should validate desktop file")
        runner.assert_in("command -v desktop-file-validate", content, "Should check for validator availability")
    
    def test_cache_updates(self):
        content = self.get_script_content()
        runner.assert_in("update-desktop-database", content, "Should update desktop database")
        runner.assert_in("gtk-update-icon-cache", content, "Should update icon cache")
    
    def test_gnome_cache_clearing(self):
        content = self.get_script_content()
        runner.assert_in("$HOME/.cache/gnome-shell/", content, "Should clear GNOME Shell cache")
        runner.assert_in("$HOME/.local/share/recently-used.xbel", content, "Should clear recently-used cache")


class TestDuckStationDocumentation:
    """Test script documentation and user guidance"""
    
    @staticmethod
    def get_script_content():
        script_path = Path(__file__).parent.parent / "scripts" / "install_ducksation.sh"
        with open(script_path) as f:
            return f.read()
    
    def test_script_has_description(self):
        content = self.get_script_content()
        runner.assert_in("# Description:", content, "Should have description comment")
        runner.assert_in("DuckStation", content, "Description should mention DuckStation")
    
    def test_script_provides_help_message(self):
        content = self.get_script_content()
        runner.assert_in("Alt+F2", content, "Should mention Alt+F2 restart")
        runner.assert_in("log out and log back in", content, "Should mention log out/in")


def run_all_tests():
    """Run all test classes"""
    test_classes = [
        TestDuckStationWrapperScript,
        TestDuckStationDesktopFile,
        TestDuckStationConfiguration,
        TestDuckStationSafety,
        TestDuckStationIconHandling,
        TestDuckStationIntegration,
        TestDuckStationDocumentation,
    ]
    
    print("Running DuckStation Installer Tests")
    print("="*70)
    
    for test_class in test_classes:
        print(f"\n{test_class.__name__}:")
        test_instance = test_class()
        
        # Get all test methods
        test_methods = [method for method in dir(test_instance) 
                       if method.startswith('test_') and callable(getattr(test_instance, method))]
        
        for method_name in test_methods:
            try:
                method = getattr(test_instance, method_name)
                method()
                print(f"  ✓ {method_name}")
            except Exception as e:
                runner.failed += 1
                runner.errors.append(f"✗ {test_class.__name__}.{method_name}: {e}")
                print(f"  ✗ {method_name}: {e}")
    
    return runner.print_results()


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
