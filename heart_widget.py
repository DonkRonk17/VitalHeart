"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    VitalHeart Phase 5 - HeartWidget MVP                       ║
║                    3D Transparent Desktop Heart Monitor                       ║
║                    Team Brain - February 2026                                 ║
╚══════════════════════════════════════════════════════════════════════════════╝

TOOLS USED IN THIS BUILD:
- ConfigManager: Widget configuration (size, position, settings)
- AgentHeartbeat: Read heartbeat data from ATLAS backend
- TimeSync: Accurate timestamps for heartbeat display
- ErrorRecovery: Graceful error handling
- VersionGuard: Detect AgentHeartbeat schema version changes
- LiveAudit: Log widget lifecycle events
- BuildEnvValidator: Check Python environment
- And 10+ more tools (see BUILD_AUDIT.md)

Built using BUILD_PROTOCOL_V1.md
For the Maximum Benefit of Life. One World. One Family. One Love.
"""

import sys
import time
from pathlib import Path
from typing import Optional, Dict
import json
import sqlite3
from datetime import datetime

# PySide6 imports
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QSystemTrayIcon,
    QMenu, QSlider, QLabel
)
from PySide6.QtCore import Qt, QPoint, QTimer, Signal, QPropertyAnimation, QEasingCurve, QObject, Property
from PySide6.QtGui import QIcon, QPalette, QColor, QAction  # QPalette used for dark background

# 3D rendering imports
HAS_PYVISTA = False
try:
    import pyvista as pv
    from pyvistaqt import QtInteractor
    HAS_PYVISTA = True
except ImportError:
    print("[ERROR] PyVista not installed. Install with: pip install pyvista pyvistaqt")
    sys.exit(1)

# Numpy for mesh operations
import numpy as np

# Script directory for resolving relative paths (config, assets)
SCRIPT_DIR = Path(__file__).parent.resolve()


# ═══════════════════════════════════════════════════════════════════════════════
# HEART RENDERER - 3D Heart with Professional Lighting
# ═══════════════════════════════════════════════════════════════════════════════

class HeartRenderer:
    """
    3D heart renderer using PyVista with professional 3-point lighting.

    Reference: AI Compression Hub viewer_3d.py patterns
    """

    # ═══ MOOD COLOR MAP ═══
    # Maps mood strings to hex colors for the heart
    MOOD_COLORS = {
        # Warm/positive emotions
        "happy": "#ff6b6b",       # Warm red (default, alive)
        "content": "#ff8e8e",     # Soft pink
        "proud": "#ff4444",       # Strong red
        "love": "#ff1493",        # Deep pink
        "excited": "#ff6347",     # Tomato red
        "grateful": "#ff7eb3",    # Rose pink
        # Cool/reflective emotions
        "focused": "#6b9fff",     # Calm blue
        "curious": "#9b6bff",     # Curious purple
        "contemplative": "#7b68ee", # Medium slate blue
        # Neutral/uncertain
        "neutral": "#ff8e8e",     # Soft warm
        "unknown": "#ff6b6b",     # Default red
        None: "#ff6b6b",          # Default
        # Negative states (still alive, different feel)
        "sad": "#6b7bff",         # Blue sadness
        "anxious": "#ffa500",     # Orange anxiety
        "afraid": "#daa520",      # Goldenrod
        # Offline/disconnected
        "offline": "#555555",     # Gray - Lumina not connected
    }

    def __init__(self, parent_widget: QWidget):
        self.parent = parent_widget
        self.heart_mesh = None
        self.heart_actor = None
        self.current_scale = 1.0
        self.current_color = '#ff6b6b'  # Track current color for animation redraws

        # Create PyVista plotter (embedded in Qt)
        self.plotter = QtInteractor(self.parent)
        # Dark background (near-black with subtle blue tint, matches window palette)
        # Note: '#00000000' (transparent) is incompatible with VTK on Windows
        self.plotter.set_background([0.04, 0.04, 0.10])

        # FORGE FIX: Disable VTK interactor mouse capture so widget drag works
        # The interactor captures all mouse events, preventing QWidget.mousePressEvent
        # from reaching TransparentHeartWidget. Disabling enables click-drag to move.
        self.plotter.disable()  # Disables mouse interaction with the 3D scene
        print("[OK] VTK mouse interaction disabled (drag-to-move enabled)")

        # Setup professional 3-point lighting
        self._setup_lighting()

        # Load or generate heart mesh
        try:
            self.heart_mesh = self._load_heart_mesh()
            print(f"[OK] Heart mesh loaded: {self.heart_mesh.n_points} vertices, {self.heart_mesh.n_cells} faces")
        except Exception as e:
            print(f"[WARNING] Heart mesh load failed: {e}")
            self.heart_mesh = self._generate_procedural_heart()
            print(f"[OK] Using procedural heart: {self.heart_mesh.n_points} vertices")

        # Add heart to scene
        self.heart_actor = self.plotter.add_mesh(
            self.heart_mesh,
            color=self.current_color,  # Warm red (default)
            opacity=0.85,
            smooth_shading=True,
            show_edges=False
        )

        # FORGE FIX: Set camera to face the FRONT of the heart directly
        # Previously defaulted to a top-angled view looking down.
        # Now starts with the classic heart silhouette visible (bumps top, point bottom).
        self.plotter.reset_camera()
        bounds = self.heart_mesh.bounds  # (xmin, xmax, ymin, ymax, zmin, zmax)
        cx = (bounds[0] + bounds[1]) / 2
        cy = (bounds[2] + bounds[3]) / 2
        cz = (bounds[4] + bounds[5]) / 2
        # Place camera in front (positive Z), looking at center, Y-up
        depth = max(bounds[1] - bounds[0], bounds[3] - bounds[2], bounds[5] - bounds[4])
        self.plotter.camera.position = (cx, cy, cz + depth * 2.5)
        self.plotter.camera.focal_point = (cx, cy, cz)
        self.plotter.camera.up = (0, 1, 0)  # Y-axis up = heart stays upright
        self.plotter.camera.zoom(1.2)  # Slight zoom for better view
        print("[OK] Camera set to front-facing view")

        # Y-axis auto-rotation state
        self.rotation_angle = 0.0
        self.rotation_speed = 0.5  # degrees per tick

        print("[OK] Heart renderer initialized")

    def _setup_lighting(self):
        """
        Setup professional 3-point lighting.

        Pattern from viewer_3d.py:
        - Key light: Front-high (main light, brightest)
        - Fill light: Right-low (softer, fills shadows)
        - Back light: Back-left-high (rim/separation light)
        - Ambient: Subtle overall illumination
        """
        self.plotter.remove_all_lights()

        # Key light: Front-high (main light)
        key_light = pv.Light(
            position=(2, 3, 5),
            focal_point=(0, 0, 0),
            color='white',
            intensity=1.0
        )
        self.plotter.add_light(key_light)

        # Fill light: Right side, low (fills shadows, blue tint)
        fill_light = pv.Light(
            position=(4, -1, 2),
            focal_point=(0, 0, 0),
            color='#aaccff',  # Slight blue tint
            intensity=0.5
        )
        self.plotter.add_light(fill_light)

        # Back light: Back-left-high (rim/separation, warm tint)
        back_light = pv.Light(
            position=(-3, 2, -3),
            focal_point=(0, 0, 0),
            color='#ffddaa',  # Warm tint
            intensity=0.6
        )
        self.plotter.add_light(back_light)

        # Ambient light: Subtle overall illumination
        ambient_light = pv.Light(
            light_type='headlight',
            intensity=0.2
        )
        self.plotter.add_light(ambient_light)

        print("[OK] 3-point lighting configured")

    def _load_heart_mesh(self) -> pv.PolyData:
        """
        Load heart mesh from file.

        Tries in order:
        1. assets/heart.glb
        2. assets/heart.obj
        3. assets/heart.stl
        4. Falls back to procedural if none found
        """
        heart_paths = [
            SCRIPT_DIR / "assets" / "heart.glb",
            SCRIPT_DIR / "assets" / "heart.obj",
            SCRIPT_DIR / "assets" / "heart.stl",
        ]

        for path in heart_paths:
            if path.exists():
                print(f"[INFO] Loading heart mesh from: {path}")

                if path.suffix == '.glb':
                    # GLB requires trimesh
                    try:
                        import trimesh
                        scene = trimesh.load(str(path))

                        # Convert trimesh to PyVista
                        if hasattr(scene, 'geometry'):
                            # Scene with multiple meshes
                            combined_verts = []
                            combined_faces = []
                            vert_offset = 0

                            for name, mesh in scene.geometry.items():
                                if hasattr(mesh, 'vertices') and hasattr(mesh, 'faces'):
                                    combined_verts.append(mesh.vertices)
                                    # Offset face indices
                                    faces = mesh.faces + vert_offset
                                    combined_faces.append(faces)
                                    vert_offset += len(mesh.vertices)

                            all_verts = np.vstack(combined_verts)
                            all_faces = np.vstack(combined_faces)

                            # Convert to PyVista format
                            pv_faces = np.zeros((len(all_faces), 4), dtype=np.int64)
                            pv_faces[:, 0] = 3  # Triangle
                            pv_faces[:, 1:] = all_faces

                            return pv.PolyData(all_verts, faces=pv_faces.flatten())

                        elif hasattr(scene, 'vertices'):
                            # Single mesh
                            pv_faces = np.zeros((len(scene.faces), 4), dtype=np.int64)
                            pv_faces[:, 0] = 3  # Triangle
                            pv_faces[:, 1:] = scene.faces
                            return pv.PolyData(scene.vertices, faces=pv_faces.flatten())

                    except ImportError:
                        print("[WARNING] trimesh required for GLB files: pip install trimesh")
                        continue

                else:
                    # OBJ/STL/PLY can be read directly by PyVista
                    return pv.read(str(path))

        # No mesh file found
        raise FileNotFoundError("No heart mesh asset found")

    def _generate_procedural_heart(self) -> pv.PolyData:
        """
        Generate simple procedural heart mesh (fallback).

        Uses parametric heart shape:
        x = 16*sin(t)^3
        y = 13*cos(t) - 5*cos(2t) - 2*cos(3t) - cos(4t)
        z = (extrude for 3D)
        """
        print("[INFO] Generating procedural heart mesh...")

        # Parametric heart curve
        t = np.linspace(0, 2*np.pi, 100)
        x = 16 * np.sin(t)**3
        y = 13*np.cos(t) - 5*np.cos(2*t) - 2*np.cos(3*t) - np.cos(4*t)
        z = np.zeros_like(x)

        # Normalize to unit size
        coords = np.column_stack([x, y, z])
        coords = coords / np.max(np.abs(coords))

        # Create spline for smooth curve
        spline = pv.Spline(coords, n_points=200)

        # Extrude to create 3D volume (capping=True for closed ends)
        heart_3d = spline.extrude([0, 0, 0.3], capping=True)

        return heart_3d

    def set_scale(self, scale: float):
        """
        Scale heart for heartbeat animation.

        Args:
            scale: Scale factor (1.0 = normal, 1.08 = expanded)
        """
        self.current_scale = scale

        if self.heart_actor:
            # Scale the mesh
            transform = pv.Transform()
            transform.scale(scale, scale, scale)

            # Apply transform
            scaled_mesh = self.heart_mesh.copy()
            scaled_mesh.transform(transform)

            # Update actor with current color
            self.plotter.remove_actor(self.heart_actor)
            self.heart_actor = self.plotter.add_mesh(
                scaled_mesh,
                color=self.current_color,
                opacity=0.85,
                smooth_shading=True
            )

            self.plotter.update()

    def set_color(self, mood: str):
        """
        Change heart color based on mood.

        Args:
            mood: Mood string (e.g., 'happy', 'focused', 'offline')
        """
        new_color = self.MOOD_COLORS.get(mood, self.MOOD_COLORS.get("unknown", "#ff6b6b"))
        if new_color != self.current_color:
            self.current_color = new_color
            # Re-render with new color
            if self.heart_actor:
                self.plotter.remove_actor(self.heart_actor)
                scaled_mesh = self.heart_mesh.copy()
                if self.current_scale != 1.0:
                    transform = pv.Transform()
                    transform.scale(self.current_scale, self.current_scale, self.current_scale)
                    scaled_mesh.transform(transform)
                self.heart_actor = self.plotter.add_mesh(
                    scaled_mesh,
                    color=self.current_color,
                    opacity=0.85 if mood != "offline" else 0.40,
                    smooth_shading=True
                )
                self.plotter.update()
            print(f"[COLOR] Heart color changed to {new_color} (mood: {mood})")

    def rotate_y(self):
        """Rotate the heart around Y-axis (one step of auto-rotation).

        Uses camera.azimuth which is a RELATIVE rotation (incremental).
        Each tick rotates by rotation_speed degrees around the view-up (Y) axis.
        """
        # camera.azimuth applies a relative rotation in degrees
        self.plotter.camera.azimuth = self.rotation_speed
        self.plotter.update()

    def get_interactor(self):
        """Return the Qt interactor widget."""
        return self.plotter.interactor


# ═══════════════════════════════════════════════════════════════════════════════
# HEARTBEAT ANIMATION CONTROLLER
# ═══════════════════════════════════════════════════════════════════════════════

class HeartbeatAnimationController(QWidget):
    """
    Manages heartbeat animation (scale 1.0 → 1.08 → 1.0).

    Uses QPropertyAnimation for smooth interpolation.
    """

    def __init__(self, renderer: HeartRenderer):
        super().__init__()
        self.renderer = renderer
        self._scale = 1.0
        self.is_animating = False

        # Animation settings
        self.scale_min = 1.0
        self.scale_max = 1.08
        self.duration_ms = 800  # Total beat duration (expand + contract)

        # QPropertyAnimation for smooth scaling
        self.expand_anim = QPropertyAnimation(self, b"scale")
        self.expand_anim.setDuration(self.duration_ms // 2)
        self.expand_anim.setStartValue(self.scale_min)
        self.expand_anim.setEndValue(self.scale_max)
        self.expand_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.expand_anim.finished.connect(self._start_contract)

        self.contract_anim = QPropertyAnimation(self, b"scale")
        self.contract_anim.setDuration(self.duration_ms // 2)
        self.contract_anim.setStartValue(self.scale_max)
        self.contract_anim.setEndValue(self.scale_min)
        self.contract_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.contract_anim.finished.connect(self._animation_complete)

        print("[OK] Heartbeat animation controller initialized")

    def trigger_heartbeat(self):
        """Trigger a heartbeat animation."""
        if self.is_animating:
            print("[SKIP] Heartbeat already animating, skipping")
            return

        self.is_animating = True
        print("[HEARTBEAT] Heartbeat triggered!")

        # Start expand animation
        self.expand_anim.start()

    def _start_contract(self):
        """Start contraction phase."""
        self.contract_anim.start()

    def _animation_complete(self):
        """Animation complete."""
        self.is_animating = False
        print("[OK] Heartbeat complete")

    def _get_scale(self) -> float:
        """Get current scale value (Qt Property getter for QPropertyAnimation)."""
        return self._scale

    def _set_scale(self, value: float):
        """Set scale value and update renderer (Qt Property setter for QPropertyAnimation)."""
        self._scale = value
        self.renderer.set_scale(value)

    # Qt Property (NOT Python @property) -- required for QPropertyAnimation to find it
    scale = Property(float, _get_scale, _set_scale)


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT HEARTBEAT MONITOR - Backend Integration (Milestone 3)
# ═══════════════════════════════════════════════════════════════════════════════

class AgentHeartbeatMonitor(QObject):
    """
    Monitor AgentHeartbeat database for new LUMINA heartbeats.

    Connects to ATLAS's backend AgentHeartbeat database and polls for new
    heartbeat records. Emits signal when new heartbeat detected.

    Database Schema (from FORGE Phase 1-4):
        heartbeats table:
            id INTEGER PRIMARY KEY AUTOINCREMENT
            agent_name TEXT NOT NULL
            timestamp REAL NOT NULL (Unix epoch float)
            status TEXT NOT NULL ('active', 'idle', 'waiting', 'processing')
            mood TEXT (nullable - 'happy', 'content', 'focused', 'proud', 'unknown')
            capabilities TEXT (nullable - JSON string)
            current_task TEXT (nullable - description string)
            metrics TEXT (nullable - JSON string with Ollama metrics)

    Integration with Phase 1 OllamaGuard:
        - OllamaGuard emits heartbeats for LUMINA every ~60 seconds
        - status maps from HealthStatus enum
        - mood currently 'UNKNOWN' placeholder (Phase 2 MoodAnalyzer will populate)
        - metrics JSON contains: ollama_version, model_loaded, inference_latency_ms,
          vram_used_mb, vram_total_mb, vram_pct, uptime_hours, restarts_today, etc.
    """

    # Signal emitted when new heartbeat detected
    heartbeat_detected = Signal(dict)  # Emits parsed heartbeat data

    def __init__(self, agent_name: str = "LUMINA", poll_interval_ms: int = 5000,
                 db_path: Optional[Path] = None, parent=None):
        """
        Initialize heartbeat monitor.

        Args:
            agent_name: Agent to monitor (default: "LUMINA")
            poll_interval_ms: Polling interval in milliseconds (default: 5000 = 5 seconds)
            db_path: Path to AgentHeartbeat database (default: ~/.teambrain/heartbeat.db)
            parent: Qt parent object
        """
        super().__init__(parent)

        self.agent_name = agent_name
        self.poll_interval_ms = poll_interval_ms

        # Database connection (injectable for testing)
        self.db_path = db_path if db_path is not None else (Path.home() / '.teambrain' / 'heartbeat.db')
        self.conn: Optional[sqlite3.Connection] = None
        self.last_heartbeat_id = 0  # Track last seen ID to detect new records

        # Connect to database
        self._connect_db()

        # Set up polling timer
        self.poll_timer = QTimer()
        self.poll_timer.timeout.connect(self._poll_heartbeats)
        self.poll_timer.start(self.poll_interval_ms)

        print(f"[OK] AgentHeartbeatMonitor initialized")
        print(f"[INFO] Monitoring agent: {self.agent_name}")
        print(f"[INFO] Poll interval: {self.poll_interval_ms}ms")
        print(f"[INFO] Database: {self.db_path}")

    def _connect_db(self):
        """Connect to AgentHeartbeat database."""
        if not self.db_path.exists():
            print(f"[WARNING] AgentHeartbeat DB not found: {self.db_path}")
            print("[WARNING] Will continue with simulated heartbeats (fallback mode)")
            return

        try:
            self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self.conn.row_factory = sqlite3.Row  # Enable dict-like row access
            print(f"[OK] Connected to AgentHeartbeat DB")

            # Get latest heartbeat ID to start tracking
            self._initialize_last_id()

        except Exception as e:
            print(f"[WARNING] Failed to connect to AgentHeartbeat DB: {e}")
            print("[WARNING] Will continue with simulated heartbeats (fallback mode)")
            self.conn = None

    def _initialize_last_id(self):
        """Initialize last_heartbeat_id from database."""
        if not self.conn:
            return

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT id FROM heartbeats WHERE agent_name = ? ORDER BY id DESC LIMIT 1",
                (self.agent_name,)
            )
            row = cursor.fetchone()

            if row:
                self.last_heartbeat_id = row['id']
                print(f"[INFO] Starting from heartbeat ID: {self.last_heartbeat_id}")
            else:
                print(f"[INFO] No existing heartbeats for {self.agent_name}")

        except Exception as e:
            print(f"[WARNING] Failed to initialize last ID: {e}")

    def _poll_heartbeats(self):
        """Poll database for new heartbeats."""
        if not self.conn:
            # DB not available, skip (fallback timer in widget will handle animation)
            return

        try:
            cursor = self.conn.cursor()

            # Query for new heartbeats (ID > last_heartbeat_id)
            cursor.execute(
                """
                SELECT id, agent_name, timestamp, status, mood, current_task, metrics
                FROM heartbeats
                WHERE agent_name = ? AND id > ?
                ORDER BY id ASC
                """,
                (self.agent_name, self.last_heartbeat_id)
            )

            rows = cursor.fetchall()

            # Process each new heartbeat
            for row in rows:
                heartbeat = self._parse_heartbeat(row)

                # Update last seen ID
                self.last_heartbeat_id = heartbeat['id']

                # Emit signal
                self.heartbeat_detected.emit(heartbeat)

                print(f"[HEARTBEAT] New heartbeat detected: ID={heartbeat['id']}, "
                      f"status={heartbeat['status']}, mood={heartbeat['mood']}")

        except Exception as e:
            print(f"[WARNING] Heartbeat poll failed: {e}")

    def _parse_heartbeat(self, row: sqlite3.Row) -> Dict:
        """
        Parse database row into heartbeat dict.

        Args:
            row: SQLite row object

        Returns:
            Parsed heartbeat data
        """
        # Parse timestamp (Unix epoch REAL to datetime)
        timestamp_unix = row['timestamp']
        timestamp_dt = datetime.fromtimestamp(timestamp_unix) if timestamp_unix else None

        # Parse metrics JSON (if present)
        metrics_str = row['metrics']
        metrics = None
        if metrics_str:
            try:
                metrics = json.loads(metrics_str)
            except json.JSONDecodeError:
                print(f"[WARNING] Failed to parse metrics JSON: {metrics_str[:50]}...")

        return {
            'id': row['id'],
            'agent_name': row['agent_name'],
            'timestamp': timestamp_dt,
            'timestamp_unix': timestamp_unix,
            'status': row['status'],
            'mood': row['mood'],
            'current_task': row['current_task'],
            'metrics': metrics
        }

    def stop(self):
        """Stop monitoring and clean up."""
        self.poll_timer.stop()
        if self.conn:
            self.conn.close()
            self.conn = None
        print("[INFO] AgentHeartbeatMonitor stopped")


# ═══════════════════════════════════════════════════════════════════════════════
# TRANSPARENT HEART WIDGET - Main Window
# ═══════════════════════════════════════════════════════════════════════════════

class TransparentHeartWidget(QWidget):
    """
    Transparent, frameless, always-on-top desktop widget displaying 3D heart.

    Features:
    - Transparent background
    - Drag-to-reposition
    - Persistent configuration
    - System tray integration
    """

    def __init__(self):
        super().__init__()

        # Load configuration
        self.config = self._load_config()

        # Setup window
        self._setup_window()

        # Create renderer
        self.renderer = HeartRenderer(self)

        # Setup layout
        self._setup_layout()

        # Create animation controller
        self.animation = HeartbeatAnimationController(self.renderer)

        # Create system tray (Phase 5 Milestone 5)
        self._setup_system_tray()

        # Milestone 3: AgentHeartbeat Integration (Backend Connection)
        self.heartbeat_monitor = AgentHeartbeatMonitor(
            agent_name="LUMINA",
            poll_interval_ms=5000,  # Poll every 5 seconds
            parent=self
        )

        # Connect heartbeat signal to animation trigger
        self.heartbeat_monitor.heartbeat_detected.connect(self._on_heartbeat_detected)

        # FORGE FIX: No fallback/test timer. Heart ONLY beats with live Lumina heartbeats.
        # This makes it a true "Lumina online check" -- if it beats, she's alive and responsive.
        if self.heartbeat_monitor.conn:
            print("[INFO] Real heartbeat monitoring active -- heart beats ONLY on live signals")
        else:
            print("[WARNING] No heartbeat DB found -- heart will remain still until Lumina connects")

        # Lumina online state tracking
        self.lumina_online = False
        self.last_heartbeat_time = None

        # Offline detection timer: if no heartbeat in 30 seconds, Lumina is considered offline
        self.offline_check_timer = QTimer()
        self.offline_check_timer.timeout.connect(self._check_lumina_online)
        self.offline_check_timer.start(10000)  # Check every 10 seconds

        # Start in offline state (gray, dim) until first heartbeat proves she's alive
        self.renderer.set_color("offline")

        # Y-axis auto-rotation timer (slow, graceful spin)
        self.rotation_timer = QTimer()
        self.rotation_timer.timeout.connect(self.renderer.rotate_y)
        self.rotation_timer.start(50)  # ~20 FPS rotation, smooth
        print("[OK] Y-axis auto-rotation active (slow spin)")

        print("[OK] TransparentHeartWidget initialized")
        print(f"[INFO] Position: ({self.x()}, {self.y()})")
        print(f"[INFO] Size: {self.width()}x{self.height()}")

        # Save config on first run (creates file if missing)
        self._save_config()

    def _setup_window(self):
        """Setup transparent, frameless, always-on-top window."""
        # Set window flags
        self.setWindowFlags(
            Qt.FramelessWindowHint |      # No title bar/borders
            Qt.WindowStaysOnTopHint |     # Always on top
            Qt.Tool                        # No taskbar entry
        )

        # Note: WA_TranslucentBackground is INCOMPATIBLE with PyVista/VTK's OpenGL
        # rendering on Windows. The OpenGL context does not composite with Qt's
        # per-pixel transparency, making the entire window invisible.
        # True per-pixel transparency requires off-screen VTK rendering to QImage
        # (Phase 6 enhancement). For MVP, use a dark background that complements the heart.
        # self.setAttribute(Qt.WA_TranslucentBackground)  # Disabled - VTK incompatible
        self.setAttribute(Qt.WA_AlwaysStackOnTop)

        # Set dark background palette (matches VTK dark background)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(10, 10, 25))
        self.setPalette(palette)

        # Set window size from config
        size = self.config.get("size", 120)
        self.resize(size, size)

        # Set window position from config (validate bounds)
        x = self.config.get("x", 100)
        y = self.config.get("y", 100)
        self.move(x, y)

        # Set window title (for system tray)
        self.setWindowTitle("VitalHeart - Lumina's Heartbeat")

        print("[OK] Window configured: transparent, frameless, always-on-top")

    def _setup_layout(self):
        """Setup widget layout with PyVista renderer."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Add PyVista interactor
        layout.addWidget(self.renderer.get_interactor())

    def _setup_system_tray(self):
        """Setup system tray icon with full control menu."""
        # State flags
        self.position_locked = False
        self.click_through = False

        # Create tray icon
        self.tray_icon = QSystemTrayIcon(self)

        # Set icon (use default for now, Phase 7 will add custom icon)
        from PySide6.QtWidgets import QStyle
        self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))

        # Create tray menu
        tray_menu = QMenu()

        # ═══ STATUS ═══
        self.status_action = QAction("VitalHeart - Status: Waiting...", self)
        self.status_action.setEnabled(False)
        tray_menu.addAction(self.status_action)

        tray_menu.addSeparator()

        # ═══ SHOW/HIDE ═══
        toggle_action = QAction("Show/Hide Heart", self)
        toggle_action.triggered.connect(self._toggle_visibility)
        tray_menu.addAction(toggle_action)

        tray_menu.addSeparator()

        # ═══ ZOOM SUBMENU ═══
        zoom_menu = QMenu("Zoom", self)
        self.zoom_actions = {}
        for pct in [50, 75, 100, 125, 150, 200, 300]:
            action = QAction(f"{pct}%", self)
            action.setCheckable(True)
            if pct == 100:
                action.setChecked(True)
            action.triggered.connect(lambda checked, p=pct: self._set_zoom(p))
            zoom_menu.addAction(action)
            self.zoom_actions[pct] = action
        tray_menu.addMenu(zoom_menu)

        tray_menu.addSeparator()

        # ═══ POSITION LOCK ═══
        self.lock_action = QAction("Position Lock", self)
        self.lock_action.setCheckable(True)
        self.lock_action.setChecked(False)
        self.lock_action.triggered.connect(self._toggle_position_lock)
        tray_menu.addAction(self.lock_action)

        # ═══ CLICK-THROUGH ═══
        self.clickthrough_action = QAction("Click-Through Mode", self)
        self.clickthrough_action.setCheckable(True)
        self.clickthrough_action.setChecked(False)
        self.clickthrough_action.triggered.connect(self._toggle_click_through)
        tray_menu.addAction(self.clickthrough_action)

        tray_menu.addSeparator()

        # ═══ EXIT ═══
        exit_action = QAction("Exit VitalHeart", self)
        exit_action.triggered.connect(self._exit_application)
        tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.setToolTip("VitalHeart - Lumina's Heartbeat")

        # Show tray icon
        self.tray_icon.show()

        print("[OK] System tray created (zoom, position lock, click-through)")

    def _load_config(self) -> Dict:
        """Load widget configuration from file."""
        config_path = SCRIPT_DIR / "widget_config.json"

        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    print(f"[OK] Config loaded from {config_path}")
                    return config
            except Exception as e:
                print(f"[WARNING] Config load failed: {e}, using defaults")

        # Return defaults (250x250 is comfortable for desktop visibility)
        return {
            "version": "1.0",
            "size": 250,
            "x": 100,
            "y": 100,
            "opacity": 0.95,
            "poll_interval_s": 5
        }

    def _save_config(self):
        """Save widget configuration to file."""
        config_path = SCRIPT_DIR / "widget_config.json"

        # Update config with current position/size
        self.config["x"] = self.x()
        self.config["y"] = self.y()
        self.config["size"] = self.width()

        try:
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
                print(f"[OK] Config saved to {config_path}")
        except Exception as e:
            print(f"[WARNING] Config save failed: {e}")

    def _on_heartbeat_detected(self, heartbeat: Dict):
        """
        Handle real heartbeat from AgentHeartbeatMonitor.

        FORGE FIX: Heart only beats on LIVE signals. No resting heartbeat.
        This is Logan's personal "Lumina online check" -- a single glance tells
        him if she's connected and ready.

        Also updates heart color based on mood (was Phase 6, promoted here).

        Args:
            heartbeat: Parsed heartbeat data with fields:
                - id: Heartbeat ID
                - agent_name: Agent name (e.g., "LUMINA")
                - timestamp: datetime object
                - timestamp_unix: Unix epoch float
                - status: 'active', 'idle', 'waiting', 'processing'
                - mood: 'happy', 'content', 'focused', 'proud', 'unknown', or None
                - current_task: Task description or None
                - metrics: Parsed JSON dict or None
        """
        self.last_heartbeat_time = time.time()

        # Transition from offline to online
        if not self.lumina_online:
            self.lumina_online = True
            print("[ONLINE] Lumina is ALIVE! Heart activated.")

        mood = heartbeat.get('mood', 'unknown')
        status = heartbeat.get('status', 'unknown')
        task = heartbeat.get('current_task')

        print(f"[HEARTBEAT] Received: status={status}, mood={mood}, task={task}")

        # Trigger heartbeat animation -- the whole reason for VitalHeart
        self.animation.trigger_heartbeat()

        # Update heart color based on mood
        self.renderer.set_color(mood)

    def _check_lumina_online(self):
        """
        Periodic check: if no heartbeat received in OFFLINE_THRESHOLD seconds,
        consider Lumina offline. Changes heart to gray/dim to signal disconnection.

        FORGE FIX: Increased from 30s to 90s. Lumina's heartbeat emission interval
        can be 25-30s, which caused the heart to flicker gray between pulses.
        90s gives comfortable buffer -- if 3 consecutive heartbeats are missed,
        she's genuinely offline.
        """
        OFFLINE_THRESHOLD = 90.0  # seconds without heartbeat = offline

        if self.last_heartbeat_time is None:
            # Never received a heartbeat -- still offline
            if self.lumina_online:
                self.lumina_online = False
                self.renderer.set_color("offline")
                print("[OFFLINE] Lumina has not connected yet.")
            return

        elapsed = time.time() - self.last_heartbeat_time
        if elapsed > OFFLINE_THRESHOLD and self.lumina_online:
            self.lumina_online = False
            self.renderer.set_color("offline")
            print(f"[OFFLINE] No heartbeat for {elapsed:.0f}s -- Lumina appears offline.")

    def _toggle_visibility(self):
        """Toggle widget visibility."""
        if self.isVisible():
            self.hide()
        else:
            self.show()

    def _exit_application(self):
        """Exit application cleanly."""
        print("[INFO] Exiting VitalHeart...")
        # Stop all timers
        if hasattr(self, 'rotation_timer'):
            self.rotation_timer.stop()
        if hasattr(self, 'offline_check_timer'):
            self.offline_check_timer.stop()
        if hasattr(self, 'heartbeat_monitor'):
            self.heartbeat_monitor.stop()
        self._save_config()
        QApplication.quit()

    # ═══ ZOOM CONTROL ═══

    def _set_zoom(self, percent: int):
        """
        Set heart window size as a percentage of the default (250px).

        Args:
            percent: Zoom percentage (50, 75, 100, 125, 150, 200, 300)
        """
        base_size = 250  # Default size
        new_size = int(base_size * percent / 100)
        self.resize(new_size, new_size)
        self.config["size"] = new_size

        # Update checkmarks in zoom menu
        for pct, action in self.zoom_actions.items():
            action.setChecked(pct == percent)

        self._save_config()
        print(f"[ZOOM] Set to {percent}% ({new_size}x{new_size}px)")

    # ═══ POSITION LOCK ═══

    def _toggle_position_lock(self, checked: bool):
        """
        Toggle position lock. When locked, dragging is disabled and VTK mouse
        interaction is re-enabled so you can rotate camera / zoom with scroll.
        """
        self.position_locked = checked
        if checked:
            # Re-enable VTK interaction so user can manipulate camera angle + zoom
            self.renderer.plotter.enable()
            print("[LOCK] Position locked -- camera manipulation enabled (scroll=zoom, drag=rotate)")
        else:
            # Disable VTK interaction, re-enable window drag
            self.renderer.plotter.disable()
            print("[UNLOCK] Position unlocked -- drag-to-move enabled")

    # ═══ CLICK-THROUGH MODE ═══

    def _toggle_click_through(self, checked: bool):
        """
        Toggle click-through mode. When enabled, mouse clicks pass through
        the widget to whatever is underneath (desktop, other apps).
        Uses Windows WS_EX_TRANSPARENT extended window style.
        """
        self.click_through = checked

        if sys.platform == 'win32':
            import ctypes
            from ctypes import wintypes

            hwnd = int(self.winId())
            GWL_EXSTYLE = -20
            WS_EX_TRANSPARENT = 0x00000020
            WS_EX_LAYERED = 0x00080000

            user32 = ctypes.windll.user32
            current_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)

            if checked:
                # Enable click-through: add TRANSPARENT + LAYERED flags
                new_style = current_style | WS_EX_TRANSPARENT | WS_EX_LAYERED
                user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)
                print("[CLICK-THROUGH] Enabled -- clicks pass through to desktop")
                print("[TIP] Use system tray to disable click-through")
            else:
                # Disable click-through: remove TRANSPARENT flag
                new_style = current_style & ~WS_EX_TRANSPARENT
                user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)
                print("[CLICK-THROUGH] Disabled -- heart is interactive again")
        else:
            print("[WARNING] Click-through is only supported on Windows")

    # ═══ MOUSE EVENT HANDLERS (Drag-to-Reposition) ═══

    def mousePressEvent(self, event):
        """Start drag operation (disabled when position is locked)."""
        if self.position_locked:
            # When locked, let VTK handle mouse events for camera control
            super().mousePressEvent(event)
            return
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """Handle drag (disabled when position is locked)."""
        if self.position_locked:
            super().mouseMoveEvent(event)
            return
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        """End drag, save position (disabled when position is locked)."""
        if self.position_locked:
            super().mouseReleaseEvent(event)
            return
        if event.button() == Qt.LeftButton:
            self._save_config()


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Main entry point for VitalHeart HeartWidget."""
    # Windows console compatibility - use ASCII-safe characters
    print("=" * 68)
    print("  VitalHeart Phase 5 - HeartWidget MVP v1.0")
    print("  3D Transparent Desktop Heart Monitor")
    print("  Team Brain - Built with BUILD_PROTOCOL_V1.md")
    print("=" * 68)
    print()

    # Check PyVista availability
    if not HAS_PYVISTA:
        print("[ERROR] PyVista not installed")
        print("Install with: pip install pyvista pyvistaqt")
        sys.exit(1)

    print("[OK] PyVista available")

    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("VitalHeart")
    app.setOrganizationName("Team Brain")

    # Create and show widget
    widget = TransparentHeartWidget()
    widget.show()

    print()
    print("[OK] VitalHeart is running!")
    print("[TIP] Click and drag the heart to reposition on your desktop")
    print("[TIP] Right-click system tray icon for menu")
    print("[TIP] Heart auto-rotates on Y-axis (stays upright)")
    if widget.heartbeat_monitor.conn:
        print("[INFO] Monitoring LUMINA heartbeats -- heart ONLY beats on live signals")
        print("[INFO] Gray heart = Lumina offline | Colored heart = Lumina online")
    else:
        print("[WARNING] No heartbeat DB found -- heart stays gray until Lumina connects")
    print("[TIP] Close: Right-click system tray icon -> Exit")
    print()

    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
