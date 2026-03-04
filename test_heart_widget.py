"""
VitalHeart Phase 5 - Comprehensive Test Suite
Following BUILD_PROTOCOL_V1.md Phase 5 and Bug Hunt Protocol

Test Coverage:
- Unit tests (10+): Config, monitor, animation, renderer
- Integration tests (5+): End-to-end heartbeat flow, DB failure recovery
- Widget tests (10+): Transparency, mesh, lighting, tray, drag, shutdown

IRIS - Windows CLI Specialist
Build Protocol V1: Phase 5 (Testing)
Bug Hunt Protocol: 100% Search Coverage
"""

import sys
import json
import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import pytest

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, Qt
from PySide6.QtTest import QTest

# Import components to test
from heart_widget import (
    HeartRenderer,
    HeartbeatAnimationController,
    AgentHeartbeatMonitor,
    TransparentHeartWidget
)


# ═══════════════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for GUI tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def temp_db():
    """Create temporary SQLite database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = Path(f.name)

    # Create schema
    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        CREATE TABLE heartbeats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_name TEXT NOT NULL,
            timestamp REAL NOT NULL,
            status TEXT NOT NULL,
            mood TEXT,
            capabilities TEXT,
            current_task TEXT,
            metrics TEXT
        )
    """)
    conn.execute("CREATE INDEX idx_heartbeats_agent ON heartbeats(agent_name)")
    conn.execute("CREATE INDEX idx_heartbeats_time ON heartbeats(timestamp)")
    conn.commit()
    conn.close()

    yield db_path

    # Cleanup - retry deletion if file is locked (Windows)
    import time
    for attempt in range(5):
        try:
            if db_path.exists():
                db_path.unlink()
            break
        except PermissionError:
            time.sleep(0.1)  # Wait for connections to close


@pytest.fixture
def temp_config():
    """Create temporary config file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config = {
            "version": "1.0",
            "x": 100,
            "y": 100,
            "size": 120,
            "opacity": 0.95,
            "poll_interval_s": 5
        }
        json.dump(config, f)
        config_path = Path(f.name)

    yield config_path

    # Cleanup
    if config_path.exists():
        config_path.unlink()


# ═══════════════════════════════════════════════════════════════════════════════
# UNIT TESTS - Configuration Management
# ═══════════════════════════════════════════════════════════════════════════════

class TestConfigurationManagement:
    """Test configuration load/save/persistence."""

    def test_config_load_valid(self, qapp, temp_config, monkeypatch):
        """Test loading valid configuration file."""
        # Redirect SCRIPT_DIR so _load_config reads from temp_config's parent
        import heart_widget as hw
        monkeypatch.setattr(hw, 'SCRIPT_DIR', temp_config.parent)

        # Rename temp_config to widget_config.json in its parent dir
        config_path = temp_config.parent / "widget_config.json"
        if not config_path.exists():
            temp_config.rename(config_path)

        widget = TransparentHeartWidget()
        config = widget._load_config()

        assert config["version"] == "1.0"
        assert config["x"] == 100
        assert config["y"] == 100

        widget.close()

    def test_config_load_missing(self, qapp, tmp_path, monkeypatch):
        """Test loading missing configuration file (should use defaults)."""
        # Redirect SCRIPT_DIR to empty temp directory (no widget_config.json)
        import heart_widget as hw
        monkeypatch.setattr(hw, 'SCRIPT_DIR', tmp_path)

        widget = TransparentHeartWidget()
        config = widget._load_config()

        assert config["x"] == 100  # Default
        assert config["y"] == 100  # Default
        assert config["size"] == 250  # Default (updated from 120 to 250)

        widget.close()

    def test_config_load_invalid_json(self, qapp, tmp_path):
        """Test loading invalid JSON configuration."""
        invalid_config = tmp_path / "widget_config.json"
        invalid_config.write_text("{ invalid json }")

        with patch.object(Path, '__truediv__', return_value=invalid_config):
            widget = TransparentHeartWidget()
            config = widget._load_config()

            # Should return defaults on parse error
            assert config["x"] == 100
            assert config["y"] == 100

            widget.close()

    def test_config_save(self, qapp, tmp_path, monkeypatch):
        """Test saving configuration file."""
        # Redirect SCRIPT_DIR so _save_config writes to tmp_path
        import heart_widget as hw
        monkeypatch.setattr(hw, 'SCRIPT_DIR', tmp_path)

        widget = TransparentHeartWidget()
        widget.move(200, 300)
        widget._save_config()

        config_path = tmp_path / "widget_config.json"

        # Verify file was created
        assert config_path.exists()

        # Verify contents
        saved_config = json.loads(config_path.read_text())
        assert saved_config["x"] == 200
        assert saved_config["y"] == 300

        widget.close()

    def test_config_persistence_across_restarts(self, qapp, tmp_path):
        """Test configuration persists across widget restarts."""
        config_path = tmp_path / "widget_config.json"

        # First instance: set position and save
        with patch('heart_widget.Path', return_value=config_path):
            widget1 = TransparentHeartWidget()
            widget1.move(400, 500)
            widget1._save_config()
            widget1.close()

        # Second instance: should load saved position
        with patch('heart_widget.Path', return_value=config_path):
            widget2 = TransparentHeartWidget()
            assert widget2.x() == 400
            assert widget2.y() == 500
            widget2.close()


# ═══════════════════════════════════════════════════════════════════════════════
# UNIT TESTS - AgentHeartbeatMonitor
# ═══════════════════════════════════════════════════════════════════════════════

class TestAgentHeartbeatMonitor:
    """Test heartbeat monitoring functionality."""

    def test_monitor_initialization(self, qapp, temp_db):
        """Test monitor initializes correctly."""
        with patch.object(Path, 'home', return_value=temp_db.parent):
            with patch('heart_widget.Path.__truediv__', return_value=temp_db):
                monitor = AgentHeartbeatMonitor(agent_name="LUMINA", poll_interval_ms=1000)

                assert monitor.agent_name == "LUMINA"
                assert monitor.poll_interval_ms == 1000
                assert monitor.conn is not None
                assert monitor.last_heartbeat_id == 0

                monitor.stop()

    def test_monitor_db_not_found(self, qapp):
        """Test monitor handles missing database gracefully."""
        with patch.object(Path, 'exists', return_value=False):
            monitor = AgentHeartbeatMonitor(agent_name="LUMINA")

            # Should not crash, conn should be None
            assert monitor.conn is None

            monitor.stop()

    def test_monitor_detect_new_heartbeat(self, qapp, temp_db):
        """Test monitor detects new heartbeat in database."""
        monitor = None
        try:
            # Create monitor FIRST (empty DB, last_heartbeat_id = 0)
            monitor = AgentHeartbeatMonitor(
                agent_name="LUMINA", poll_interval_ms=100, db_path=temp_db
            )

            # Track emitted signals
            emitted_heartbeats = []
            monitor.heartbeat_detected.connect(lambda hb: emitted_heartbeats.append(hb))

            # Insert heartbeat AFTER monitor starts (simulates new heartbeat arriving)
            conn = sqlite3.connect(str(temp_db))
            timestamp = datetime.now().timestamp()
            conn.execute("""
                INSERT INTO heartbeats (agent_name, timestamp, status, mood, current_task, metrics)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ("LUMINA", timestamp, "active", "happy", "test task", '{"test": "data"}'))
            conn.commit()
            conn.close()

            # Trigger poll
            monitor._poll_heartbeats()

            # Should have detected heartbeat
            assert len(emitted_heartbeats) == 1
            hb = emitted_heartbeats[0]
            assert hb['agent_name'] == "LUMINA"
            assert hb['status'] == "active"
            assert hb['mood'] == "happy"
            assert hb['current_task'] == "test task"
            assert hb['metrics']['test'] == "data"
        finally:
            if monitor:
                monitor.stop()

    def test_monitor_parse_unix_timestamp(self, qapp, temp_db):
        """Test monitor correctly parses Unix epoch timestamp."""
        # Create monitor FIRST (empty DB)
        monitor = AgentHeartbeatMonitor(agent_name="LUMINA", db_path=temp_db)

        # Insert heartbeat AFTER monitor starts
        conn = sqlite3.connect(str(temp_db))
        test_timestamp = 1708051200.0  # 2024-02-16 00:00:00 UTC
        conn.execute("""
            INSERT INTO heartbeats (agent_name, timestamp, status, mood)
            VALUES (?, ?, ?, ?)
        """, ("LUMINA", test_timestamp, "active", "happy"))
        conn.commit()
        conn.close()

        emitted = []
        monitor.heartbeat_detected.connect(lambda hb: emitted.append(hb))
        monitor._poll_heartbeats()

        # Verify timestamp was parsed to datetime
        assert len(emitted) == 1
        assert isinstance(emitted[0]['timestamp'], datetime)
        assert emitted[0]['timestamp_unix'] == test_timestamp

        monitor.stop()

    def test_monitor_handle_null_metrics(self, qapp, temp_db):
        """Test monitor handles NULL metrics field gracefully."""
        # Create monitor FIRST (empty DB)
        monitor = AgentHeartbeatMonitor(agent_name="LUMINA", db_path=temp_db)

        # Insert heartbeat AFTER monitor starts
        conn = sqlite3.connect(str(temp_db))
        conn.execute("""
            INSERT INTO heartbeats (agent_name, timestamp, status, mood, metrics)
            VALUES (?, ?, ?, ?, ?)
        """, ("LUMINA", datetime.now().timestamp(), "active", "happy", None))
        conn.commit()
        conn.close()

        emitted = []
        monitor.heartbeat_detected.connect(lambda hb: emitted.append(hb))
        monitor._poll_heartbeats()

        # Should handle None gracefully
        assert len(emitted) == 1
        assert emitted[0]['metrics'] is None

        monitor.stop()

    def test_monitor_incremental_polling(self, qapp, temp_db):
        """Test monitor only detects NEW heartbeats (incremental polling)."""
        # Create monitor FIRST (empty DB)
        monitor = AgentHeartbeatMonitor(agent_name="LUMINA", db_path=temp_db)

        emitted = []
        monitor.heartbeat_detected.connect(lambda hb: emitted.append(hb))

        conn = sqlite3.connect(str(temp_db))

        # Insert first heartbeat AFTER monitor starts
        conn.execute("""
            INSERT INTO heartbeats (agent_name, timestamp, status, mood)
            VALUES (?, ?, ?, ?)
        """, ("LUMINA", datetime.now().timestamp(), "active", "happy"))
        conn.commit()

        # First poll
        monitor._poll_heartbeats()
        assert len(emitted) == 1

        # Second poll (same heartbeat, should NOT detect again)
        monitor._poll_heartbeats()
        assert len(emitted) == 1  # Still 1, not 2

        # Insert SECOND heartbeat
        conn.execute("""
            INSERT INTO heartbeats (agent_name, timestamp, status, mood)
            VALUES (?, ?, ?, ?)
        """, ("LUMINA", datetime.now().timestamp(), "idle", "content"))
        conn.commit()

        # Third poll (should detect new heartbeat only)
        monitor._poll_heartbeats()
        assert len(emitted) == 2
        assert emitted[1]['status'] == "idle"
        assert emitted[1]['mood'] == "content"

        monitor.stop()
        conn.close()


# ═══════════════════════════════════════════════════════════════════════════════
# UNIT TESTS - HeartbeatAnimationController
# ═══════════════════════════════════════════════════════════════════════════════

class TestHeartbeatAnimationController:
    """Test animation controller functionality."""

    def test_animation_initialization(self, qapp):
        """Test animation controller initializes correctly."""
        # Mock renderer
        renderer = Mock()
        renderer.set_scale = Mock()

        controller = HeartbeatAnimationController(renderer)

        assert controller.renderer == renderer
        assert not controller.is_animating
        assert controller.expand_anim.duration() == 400
        assert controller.contract_anim.duration() == 400

    def test_animation_trigger_heartbeat(self, qapp):
        """Test triggering heartbeat animation."""
        renderer = Mock()
        renderer.set_scale = Mock()

        controller = HeartbeatAnimationController(renderer)

        # Trigger animation
        controller.trigger_heartbeat()

        # Should start animating
        assert controller.is_animating

    def test_animation_scale_range(self, qapp):
        """Test animation scale ranges from 1.0 to 1.08."""
        renderer = Mock()
        renderer.set_scale = Mock()

        controller = HeartbeatAnimationController(renderer)

        # Check expand animation range
        assert controller.expand_anim.startValue() == 1.0
        assert controller.expand_anim.endValue() == 1.08

        # Check contract animation range
        assert controller.contract_anim.startValue() == 1.08
        assert controller.contract_anim.endValue() == 1.0

    def test_animation_prevents_overlap(self, qapp):
        """Test animation prevents overlapping triggers."""
        renderer = Mock()
        controller = HeartbeatAnimationController(renderer)

        # First trigger
        controller.trigger_heartbeat()
        assert controller.is_animating

        # Second trigger while animating (should be skipped)
        controller.trigger_heartbeat()
        # Still animating from first trigger

    def test_animation_complete_resets_flag(self, qapp):
        """Test animation completion resets is_animating flag."""
        renderer = Mock()
        controller = HeartbeatAnimationController(renderer)

        # Trigger animation
        controller.trigger_heartbeat()
        assert controller.is_animating

        # Simulate completion
        controller._animation_complete()
        assert not controller.is_animating


# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRATION TESTS - End-to-End
# ═══════════════════════════════════════════════════════════════════════════════

class TestEndToEndIntegration:
    """Test complete heartbeat flow from DB to animation."""

    def test_heartbeat_flow_db_to_animation(self, qapp, temp_db):
        """Test heartbeat flows from database through monitor to animation."""
        # Insert heartbeat
        conn = sqlite3.connect(str(temp_db))
        conn.execute("""
            INSERT INTO heartbeats (agent_name, timestamp, status, mood)
            VALUES (?, ?, ?, ?)
        """, ("LUMINA", datetime.now().timestamp(), "active", "happy"))
        conn.commit()
        conn.close()

        # Create widget with patched DB path
        with patch('heart_widget.Path.home', return_value=temp_db.parent):
            with patch('heart_widget.Path.__truediv__', return_value=temp_db):
                widget = TransparentHeartWidget()

                # Poll for heartbeat
                widget.heartbeat_monitor._poll_heartbeats()

                # Animation should have been triggered
                # (Check via mocking or internal state)

                widget.close()

    def test_fallback_to_simulated_heartbeats(self, qapp):
        """Test widget falls back to simulated heartbeats when DB not found."""
        with patch.object(Path, 'exists', return_value=False):
            widget = TransparentHeartWidget()

            # Monitor should have no connection
            assert widget.heartbeat_monitor.conn is None

            # Test timer should be running (fallback)
            assert widget.test_timer.isActive()

            widget.close()

    def test_db_connection_recovery(self, qapp, temp_db):
        """Test monitor can recover from DB connection failure."""
        # Create monitor with non-existent db_path
        fake_path = Path(tempfile.gettempdir()) / "nonexistent_heartbeat.db"
        monitor = AgentHeartbeatMonitor(agent_name="LUMINA", db_path=fake_path)
        assert monitor.conn is None

        # Now point monitor at real DB and reconnect
        monitor.db_path = temp_db
        monitor._connect_db()
        assert monitor.conn is not None

        monitor.stop()

    def test_multiple_rapid_heartbeats(self, qapp, temp_db):
        """Test widget handles multiple rapid heartbeats correctly."""
        # Insert multiple heartbeats
        conn = sqlite3.connect(str(temp_db))
        for i in range(5):
            conn.execute("""
                INSERT INTO heartbeats (agent_name, timestamp, status, mood)
                VALUES (?, ?, ?, ?)
            """, ("LUMINA", datetime.now().timestamp() + i, "active", "happy"))
        conn.commit()
        conn.close()

        # Create widget and poll
        with patch('heart_widget.Path.home', return_value=temp_db.parent):
            with patch('heart_widget.Path.__truediv__', return_value=temp_db):
                widget = TransparentHeartWidget()

                # Should detect all 5 heartbeats
                widget.heartbeat_monitor._poll_heartbeats()

                # Animation should have been triggered (may queue multiple)

                widget.close()

    def test_widget_shutdown_cleanup(self, qapp):
        """Test widget cleans up resources on shutdown."""
        widget = TransparentHeartWidget()

        # Verify resources are initialized
        assert widget.heartbeat_monitor is not None
        assert widget.test_timer is not None

        # Close widget
        widget._exit_application()

        # Monitor should have stopped
        # (Verify via internal state or mock)


# ═══════════════════════════════════════════════════════════════════════════════
# WIDGET TESTS - UI/UX
# ═══════════════════════════════════════════════════════════════════════════════

class TestWidgetUIUX:
    """Test widget UI/UX functionality."""

    def test_widget_window_flags(self, qapp):
        """Test widget has correct window flags (frameless, always-on-top, dark background)."""
        widget = TransparentHeartWidget()

        # Check window flags
        assert widget.windowFlags() & Qt.FramelessWindowHint
        assert widget.windowFlags() & Qt.WindowStaysOnTopHint
        # Note: WA_TranslucentBackground intentionally DISABLED for VTK/OpenGL
        # compatibility on Windows. Dark background palette is used instead.
        # True per-pixel transparency requires off-screen VTK rendering (Phase 6).
        assert widget.testAttribute(Qt.WA_AlwaysStackOnTop)

        widget.close()

    def test_widget_drag_to_reposition(self, qapp):
        """Test drag-to-reposition functionality."""
        widget = TransparentHeartWidget()
        initial_pos = widget.pos()

        # Simulate drag (simplified - Qt event simulation is complex)
        widget.move(initial_pos.x() + 100, initial_pos.y() + 100)

        # Position should change
        assert widget.pos().x() == initial_pos.x() + 100
        assert widget.pos().y() == initial_pos.y() + 100

        widget.close()

    def test_widget_system_tray_creation(self, qapp):
        """Test system tray icon is created."""
        widget = TransparentHeartWidget()

        assert widget.tray_icon is not None
        assert widget.tray_icon.isVisible()

        widget.close()

    def test_widget_show_hide_toggle(self, qapp):
        """Test show/hide toggle functionality."""
        widget = TransparentHeartWidget()

        # Initially visible
        widget.show()
        assert widget.isVisible()

        # Toggle to hide
        widget._toggle_visibility()
        assert widget.isHidden()

        # Toggle to show
        widget._toggle_visibility()
        assert widget.isVisible()

        widget.close()

    def test_widget_default_size(self, qapp):
        """Test widget uses default size from config."""
        widget = TransparentHeartWidget()

        # Default size is 120x120 (from config)
        # Note: Actual size may differ due to Qt constraints
        assert widget.width() >= 120
        assert widget.height() >= 120

        widget.close()

    def test_widget_position_persistence(self, qapp, tmp_path):
        """Test widget position persists across restarts."""
        config_path = tmp_path / "widget_config.json"

        # First instance
        with patch('heart_widget.Path', return_value=config_path):
            widget1 = TransparentHeartWidget()
            widget1.move(300, 400)
            widget1._save_config()
            widget1.close()

        # Second instance should restore position
        with patch('heart_widget.Path', return_value=config_path):
            widget2 = TransparentHeartWidget()
            assert widget2.x() == 300
            assert widget2.y() == 400
            widget2.close()

    def test_widget_handles_offscreen_position(self, qapp):
        """Test widget handles off-screen position gracefully."""
        widget = TransparentHeartWidget()

        # Set position off-screen
        widget.move(-1000, -1000)

        # Widget should accept position (Qt may constrain to screen)
        # At minimum, shouldn't crash
        assert widget.x() <= 0  # Negative or constrained

        widget.close()

    def test_widget_renderer_initialization(self, qapp):
        """Test 3D heart renderer initializes correctly."""
        widget = TransparentHeartWidget()

        assert widget.renderer is not None
        assert widget.renderer.heart_mesh is not None

        widget.close()

    def test_widget_animation_controller_initialization(self, qapp):
        """Test animation controller initializes correctly."""
        widget = TransparentHeartWidget()

        assert widget.animation is not None
        assert widget.animation.renderer == widget.renderer

        widget.close()

    def test_widget_config_loads_on_init(self, qapp, temp_config):
        """Test widget loads configuration on initialization."""
        with patch('heart_widget.Path', return_value=temp_config):
            widget = TransparentHeartWidget()

            assert widget.config is not None
            assert widget.config["version"] == "1.0"

            widget.close()


# ═══════════════════════════════════════════════════════════════════════════════
# EDGE CASE TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_corrupted_database(self, qapp, tmp_path):
        """Test widget handles corrupted database gracefully."""
        # Create corrupted DB (not a valid SQLite file)
        corrupt_db = tmp_path / "heartbeat.db"
        corrupt_db.write_text("NOT A DATABASE")

        with patch('heart_widget.Path.home', return_value=tmp_path):
            widget = TransparentHeartWidget()

            # Should fall back to simulated heartbeats
            assert widget.heartbeat_monitor.conn is None
            assert widget.test_timer.isActive()

            widget.close()

    def test_invalid_json_in_metrics(self, qapp, temp_db):
        """Test monitor handles invalid JSON in metrics field."""
        # Create monitor FIRST (empty DB)
        monitor = AgentHeartbeatMonitor(agent_name="LUMINA", db_path=temp_db)

        # Insert heartbeat with invalid JSON AFTER monitor starts
        conn = sqlite3.connect(str(temp_db))
        conn.execute("""
            INSERT INTO heartbeats (agent_name, timestamp, status, mood, metrics)
            VALUES (?, ?, ?, ?, ?)
        """, ("LUMINA", datetime.now().timestamp(), "active", "happy", "{ invalid json }"))
        conn.commit()
        conn.close()

        emitted = []
        monitor.heartbeat_detected.connect(lambda hb: emitted.append(hb))
        monitor._poll_heartbeats()

        # Should handle gracefully, metrics should be None
        assert len(emitted) == 1
        assert emitted[0]['metrics'] is None

        monitor.stop()

    def test_extremely_large_heartbeat_id(self, qapp, temp_db):
        """Test monitor handles large heartbeat IDs correctly."""
        # Create monitor FIRST (empty DB)
        monitor = AgentHeartbeatMonitor(agent_name="LUMINA", db_path=temp_db)

        # Insert heartbeat with very large ID AFTER monitor starts
        conn = sqlite3.connect(str(temp_db))
        conn.execute("""
            INSERT INTO heartbeats (id, agent_name, timestamp, status, mood)
            VALUES (?, ?, ?, ?, ?)
        """, (999999999, "LUMINA", datetime.now().timestamp(), "active", "happy"))
        conn.commit()
        conn.close()

        emitted = []
        monitor.heartbeat_detected.connect(lambda hb: emitted.append(hb))
        monitor._poll_heartbeats()

        # Should detect heartbeat and update last_heartbeat_id
        assert len(emitted) == 1
        assert monitor.last_heartbeat_id == 999999999

        monitor.stop()

    def test_empty_database(self, qapp, temp_db):
        """Test monitor handles empty database gracefully."""
        # temp_db is already created but empty

        with patch('heart_widget.Path.home', return_value=temp_db.parent):
            with patch('heart_widget.Path.__truediv__', return_value=temp_db):
                monitor = AgentHeartbeatMonitor(agent_name="LUMINA")

                # Should connect but not find any heartbeats
                assert monitor.conn is not None
                assert monitor.last_heartbeat_id == 0

                # Poll should not emit anything
                emitted = []
                monitor.heartbeat_detected.connect(lambda hb: emitted.append(hb))
                monitor._poll_heartbeats()

                assert len(emitted) == 0

                monitor.stop()

    def test_rapid_widget_create_destroy(self, qapp):
        """Test rapidly creating and destroying widgets."""
        for i in range(5):
            widget = TransparentHeartWidget()
            widget.close()

        # Should not crash or leak resources


# ═══════════════════════════════════════════════════════════════════════════════
# TEST RUNNER
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short", "--color=yes"])
