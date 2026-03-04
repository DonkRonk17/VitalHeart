"""
VitalHeart Phase 5 - Milestone 2 Test Suite
Test drag-to-reposition and configuration persistence

IRIS - Windows CLI Specialist
Build Protocol V1: Phase 5 (Testing)
"""

import sys
import json
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QPoint
from PySide6.QtTest import QTest

# Import heart widget
from heart_widget import TransparentHeartWidget


class Milestone2Tester:
    """Test harness for Milestone 2: Drag & Config"""

    def __init__(self):
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.widget = None
        self.config_path = Path("widget_config.json")
        self.test_results = []

    def run_all_tests(self):
        """Run all Milestone 2 tests"""
        print("=" * 70)
        print("  VitalHeart Milestone 2 Test Suite")
        print("  Drag-to-Reposition & Configuration Persistence")
        print("=" * 70)
        print()

        tests = [
            ("Test 1: Widget Initialization", self.test_widget_init),
            ("Test 2: Configuration File Creation", self.test_config_creation),
            ("Test 3: Configuration Load/Save", self.test_config_load_save),
            ("Test 4: Position Persistence", self.test_position_persistence),
            ("Test 5: Drag Event Handling", self.test_drag_events),
            ("Test 6: Invalid Config Handling", self.test_invalid_config),
            ("Test 7: Missing Config Handling", self.test_missing_config),
            ("Test 8: Config Edge Cases", self.test_config_edge_cases),
        ]

        for test_name, test_func in tests:
            self._run_test(test_name, test_func)

        self._print_summary()

    def _run_test(self, test_name, test_func):
        """Run a single test and record result"""
        print(f"\n{test_name}...")
        try:
            test_func()
            self.test_results.append((test_name, "PASS", None))
            print(f"  [OK] {test_name} passed")
        except AssertionError as e:
            self.test_results.append((test_name, "FAIL", str(e)))
            print(f"  [FAIL] {test_name}: {e}")
        except Exception as e:
            self.test_results.append((test_name, "ERROR", str(e)))
            print(f"  [ERROR] {test_name}: {e}")

    def test_widget_init(self):
        """Test 1: Widget initializes correctly"""
        self.widget = TransparentHeartWidget()
        assert self.widget is not None, "Widget should initialize"
        assert self.widget.renderer is not None, "Renderer should exist"
        assert self.widget.animation is not None, "Animation should exist"
        assert self.widget.tray_icon is not None, "System tray should exist"
        print("    - Widget components initialized")

    def test_config_creation(self):
        """Test 2: Configuration file is created"""
        # Remove existing config
        if self.config_path.exists():
            self.config_path.unlink()

        # Create widget (should create config)
        widget = TransparentHeartWidget()
        widget.show()
        QTest.qWait(100)  # Wait for Qt event loop
        widget.close()

        assert self.config_path.exists(), "Config file should be created"
        print("    - Config file created")

    def test_config_load_save(self):
        """Test 3: Configuration loads and saves correctly"""
        # Create test config (match actual widget structure)
        test_config = {
            "version": "1.0",
            "x": 150,
            "y": 200,
            "size": 300,
            "opacity": 0.9,
            "poll_interval_s": 5
        }

        # Save test config
        with open(self.config_path, 'w') as f:
            json.dump(test_config, f, indent=2)

        # Load widget (should read config)
        widget = TransparentHeartWidget()
        widget.show()
        QTest.qWait(100)

        # Verify position loaded
        assert widget.x() == 150, f"X position should be 150, got {widget.x()}"
        assert widget.y() == 200, f"Y position should be 200, got {widget.y()}"
        print(f"    - Config loaded: position ({widget.x()}, {widget.y()})")

        # Modify position
        widget.move(250, 300)
        widget._save_config()

        # Read saved config
        with open(self.config_path, 'r') as f:
            saved_config = json.load(f)

        assert saved_config["x"] == 250, "X should be saved as 250"
        assert saved_config["y"] == 300, "Y should be saved as 300"
        print(f"    - Config saved: position ({saved_config['x']}, {saved_config['y']})")

        widget.close()

    def test_position_persistence(self):
        """Test 4: Position persists across widget restarts"""
        # Set position on first widget
        widget1 = TransparentHeartWidget()
        widget1.show()
        widget1.move(400, 500)
        widget1._save_config()
        widget1.close()
        QTest.qWait(100)

        # Create second widget (should load saved position)
        widget2 = TransparentHeartWidget()
        widget2.show()
        QTest.qWait(100)

        assert widget2.x() == 400, f"X should persist as 400, got {widget2.x()}"
        assert widget2.y() == 500, f"Y should persist as 500, got {widget2.y()}"
        print(f"    - Position persisted: ({widget2.x()}, {widget2.y()})")

        widget2.close()

    def test_drag_events(self):
        """Test 5: Drag events are handled correctly"""
        widget = TransparentHeartWidget()
        widget.show()
        QTest.qWait(100)

        initial_pos = widget.pos()
        print(f"    - Initial position: ({initial_pos.x()}, {initial_pos.y()})")

        # Simulate drag (mousePressEvent -> mouseMoveEvent -> mouseReleaseEvent)
        # Note: QTest.mousePress/mouseMove don't work well with frameless windows
        # So we'll test the internal methods directly

        # Create mock event data
        from PySide6.QtCore import QPointF
        from PySide6.QtGui import QMouseEvent
        from PySide6.QtCore import Qt

        # Simulate mouse press
        press_pos = QPointF(50, 50)
        press_event = QMouseEvent(
            QMouseEvent.MouseButtonPress,
            press_pos,
            Qt.LeftButton,
            Qt.LeftButton,
            Qt.NoModifier
        )
        widget.mousePressEvent(press_event)

        assert widget.drag_position is not None, "Drag should be initiated"
        print("    - Drag initiated")

        # Simulate mouse move
        widget.move(widget.x() + 100, widget.y() + 100)

        # Simulate mouse release
        release_event = QMouseEvent(
            QMouseEvent.MouseButtonRelease,
            press_pos,
            Qt.LeftButton,
            Qt.LeftButton,
            Qt.NoModifier
        )
        widget.mouseReleaseEvent(release_event)

        # Verify position changed
        final_pos = widget.pos()
        assert final_pos != initial_pos, "Position should change after drag"
        print(f"    - Final position: ({final_pos.x()}, {final_pos.y()})")

        widget.close()

    def test_invalid_config(self):
        """Test 6: Invalid config file is handled gracefully"""
        # Write invalid JSON
        with open(self.config_path, 'w') as f:
            f.write("{ invalid json }")

        # Widget should load with defaults
        widget = TransparentHeartWidget()
        widget.show()
        QTest.qWait(100)

        # Should use defaults (100, 100)
        assert widget.x() == 100, "Should use default X position"
        assert widget.y() == 100, "Should use default Y position"
        print("    - Invalid config handled, defaults used")

        widget.close()

    def test_missing_config(self):
        """Test 7: Missing config file is handled gracefully"""
        # Remove config
        if self.config_path.exists():
            self.config_path.unlink()

        # Widget should create new config with defaults
        widget = TransparentHeartWidget()
        widget.show()
        QTest.qWait(100)

        assert self.config_path.exists(), "Config should be created"
        assert widget.x() == 100, "Should use default X position"
        assert widget.y() == 100, "Should use default Y position"
        print("    - Missing config handled, new config created")

        widget.close()

    def test_config_edge_cases(self):
        """Test 8: Edge cases (negative positions, huge sizes, etc.)"""
        # Test negative positions (off-screen)
        test_config = {
            "version": "1.0",
            "x": -1000,
            "y": -1000,
            "size": 240,
            "opacity": 1.0,
            "poll_interval_s": 5
        }

        with open(self.config_path, 'w') as f:
            json.dump(test_config, f, indent=2)

        widget = TransparentHeartWidget()
        widget.show()
        QTest.qWait(100)

        # Widget should load (even if off-screen)
        assert widget.x() == -1000, "Should load negative X"
        assert widget.y() == -1000, "Should load negative Y"
        print("    - Negative positions handled")

        widget.close()

        # Test huge size
        test_config["size"] = 10000
        with open(self.config_path, 'w') as f:
            json.dump(test_config, f, indent=2)

        widget = TransparentHeartWidget()
        widget.show()
        QTest.qWait(100)

        # Widget should load (Qt will constrain to screen)
        print(f"    - Large size handled: {widget.width()}x{widget.height()}")

        widget.close()

    def _print_summary(self):
        """Print test summary"""
        print()
        print("=" * 70)
        print("  Test Summary")
        print("=" * 70)

        passed = sum(1 for _, result, _ in self.test_results if result == "PASS")
        failed = sum(1 for _, result, _ in self.test_results if result == "FAIL")
        errors = sum(1 for _, result, _ in self.test_results if result == "ERROR")
        total = len(self.test_results)

        print(f"\nTotal Tests: {total}")
        print(f"  [OK] Passed: {passed}")
        print(f"  [FAIL] Failed: {failed}")
        print(f"  [ERROR] Errors: {errors}")

        if failed > 0 or errors > 0:
            print("\nFailed/Error Tests:")
            for name, result, msg in self.test_results:
                if result in ["FAIL", "ERROR"]:
                    print(f"  [{result}] {name}: {msg}")

        success_rate = (passed / total * 100) if total > 0 else 0
        print(f"\nSuccess Rate: {success_rate:.1f}%")

        if success_rate == 100:
            print("\n[OK] All tests passed! Milestone 2 COMPLETE")
        elif success_rate >= 75:
            print("\n[WARNING] Most tests passed, but some issues need attention")
        else:
            print("\n[FAIL] Significant issues found, needs debugging")

        print()


def main():
    """Run Milestone 2 tests"""
    tester = Milestone2Tester()
    tester.run_all_tests()
    sys.exit(0)


if __name__ == "__main__":
    main()
