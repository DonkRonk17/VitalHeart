# VitalHeart Phase 5: HeartWidget MVP - Implementation Plan
**Builder**: IRIS (Windows CLI Specialist)
**Date**: 2026-02-13
**Protocol**: BUILD_PROTOCOL_V1.md (Full 9-Phase Cycle)
**Estimated Duration**: 4-5 days

---

## BUILD COVERAGE PLAN (Phase 1)

### 1. Project Scope

**Primary Function**: 3D transparent desktop widget displaying Lumina's heartbeat
- Transparent, frameless PySide6 window (always-on-top, drag-to-reposition)
- PyVista 3D heart mesh rendering with professional lighting
- Heartbeat animation (scale 1.0 → 1.08) triggered on health checks
- Size adjustment slider (48-480px) with persistent configuration
- IPC connection to ATLAS's AgentHeartbeat backend for real-time data

**Secondary Functions**:
- Configuration management (size, position, check interval)
- System tray icon with basic status display
- Window opacity/visibility controls
- Debug logging for troubleshooting

**Out of Scope (Phase 6/7)**:
- Mood-reactive color changes (Phase 6)
- Radiant rays effect (Phase 6)
- Full metrics dashboard (Phase 7)
- Hardware graphs (Phase 7)
- Sensitivity tuning (Phase 7)

### 2. Integration Points

**Backend Integration (ATLAS)**:
- AgentHeartbeat SQLite database (read-only access)
- Heartbeat schema: agent_name, status, timestamp, metrics JSON
- Poll interval: 5 seconds (detect new heartbeats)
- Graceful fallback if database unavailable

**External Systems**:
- EmotionalTextureAnalyzer (Phase 6 only - stub for now)
- ConfigManager for widget settings persistence
- TimeSync for accurate timestamp handling

**Data Flow**:
```
ATLAS OllamaGuard → AgentHeartbeat.emit() → SQLite DB
                                              ↓
                    HeartWidget polls ← SQLite read
                                              ↓
                    3D Heart animates (heartbeat trigger)
```

### 3. Success Criteria

- [ ] Transparent desktop widget renders without artifacts
- [ ] 3D heart mesh loads and displays with proper lighting
- [ ] Heartbeat animation plays smoothly (60fps)
- [ ] Heartbeat triggers on new AgentHeartbeat records
- [ ] Widget can be dragged to any screen position
- [ ] Size slider adjusts heart size (48-480px)
- [ ] Position and size persist across app restarts
- [ ] System tray icon shows basic status
- [ ] Widget closes cleanly via tray menu "Exit"
- [ ] All 6 Quality Gates pass
- [ ] 25+ tests passing (10 unit, 5 integration, 10 widget-specific)
- [ ] README 400+ lines
- [ ] EXAMPLES.md with 10+ usage examples

### 4. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| PySide6+PyVista transparency issues on Windows | MEDIUM | HIGH | Reference viewer_3d.py patterns, test early, fallback to 2D QPainter if needed |
| AgentHeartbeat DB schema changes | LOW | MEDIUM | Version check in DB, graceful degradation if schema mismatch |
| Performance impact (60fps animation) | LOW | MEDIUM | Profile early, optimize render loop, reduce complexity if needed |
| Qt event loop conflicts with animation timer | LOW | MEDIUM | Use QTimer correctly, test on Windows 11 |
| Widget position off-screen on multi-monitor | MEDIUM | LOW | Validate position bounds on startup, reset if invalid |

---

## TOOL AUDIT (Phase 2)

Reviewing all 94 tools from ToolRegistry for relevance to HeartWidget MVP.

### Tools Selected for Use

#### Core Infrastructure Tools

| Tool | Version | Purpose | Integration Point |
|------|---------|---------|-------------------|
| **ConfigManager** | 1.1.0 | Widget configuration (size, position, settings) | Load/save config.json on startup/change |
| **AgentHeartbeat** | 1.0.0 | Read heartbeat data from ATLAS backend | SQLite read every 5s, trigger animation |
| **TimeSync** | 1.0.0 | Accurate timestamps for heartbeat display | Format heartbeat timestamps for debug view |
| **ErrorRecovery** | 1.0.0 | Graceful error handling (DB read failures, Qt errors) | Wrap DB reads, widget operations |
| **VersionGuard** | 1.0.0 | Detect AgentHeartbeat schema version changes | Validate DB schema on startup |

#### File & Data Tools

| Tool | Version | Purpose | Integration Point |
|------|---------|---------|-------------------|
| **QuickBackup** | 1.0.0 | Backup widget config before changes | Pre-save backup of config.json |
| **DataConvert** | 1.0.0 | Convert between config formats (JSON/YAML) | Config export/import for troubleshooting |

#### Monitoring & Logging Tools

| Tool | Version | Purpose | Integration Point |
|------|---------|---------|-------------------|
| **LiveAudit** | 1.0.0 | Log widget lifecycle events (startup, shutdown, errors) | Audit trail for debugging |
| **LogHunter** | 1.0.0 | Analyze widget logs for patterns (crashes, hangs) | Post-session diagnostics |
| **ProcessWatcher** | 1.0.0 | Monitor widget resource usage (RAM, CPU) | Performance profiling during testing |

#### Testing & Validation Tools

| Tool | Version | Purpose | Integration Point |
|------|---------|---------|-------------------|
| **BuildEnvValidator** | 1.0.0 | Validate Python environment (PySide6, PyVista installed) | Pre-startup environment check |
| **EnvGuard** | 1.0.0 | Validate configuration schema on load | Config validation before use |
| **HashGuard** | 1.0.0 | Verify config.json integrity (detect corruption) | Config load validation |

#### Development Tools

| Tool | Version | Purpose | Integration Point |
|------|---------|---------|-------------------|
| **ToolRegistry** | 1.0.0 | Tool discovery and validation | Startup tool availability check |
| **ToolSentinel** | 1.0.0 | Anomaly detection in tool usage | Monitor for unexpected tool failures |
| **RegexLab** | 1.0.0 | Parse heartbeat metrics JSON (regex validation) | Validate metrics structure |
| **DevSnapshot** | 1.0.0 | Capture development state for debugging | Snapshot on critical errors |

#### Optional Enhancement Tools

| Tool | Version | Purpose | Integration Point |
|------|---------|---------|-------------------|
| **KnowledgeSync** | 1.0.0 | Sync widget state to Memory Core | Export heartbeat history to Trophy Room |
| **PostMortem** | 1.0.0 | Analyze widget failures for learning | Post-crash analysis |
| **SmartNotes** | 1.0.0 | Auto-generate widget usage docs | User documentation generation |

### Tools Skipped (With Justification)

#### Synapse & Communication Tools
- **SynapseWatcher**: Skip - Not needed for MVP (no Synapse messaging)
- **SynapseNotify**: Skip - Not needed for MVP (no alerts yet)
- **SynapseLink**: Skip - Not needed for MVP (no team coordination)
- **SynapseInbox**: Skip - Not needed for MVP
- **SynapseStats**: Skip - Not needed for MVP

#### Agent & Routing Tools
- **AgentRouter**: Skip - Single-agent widget, no routing needed
- **AgentHandoff**: Skip - No handoffs in widget context
- **AgentHealth**: Skip - Different from AgentHeartbeat (backend health vs widget health)
- **AgentSentinel**: Skip - BCH connection monitoring not needed for desktop widget

#### Memory & Context Tools
- **MemoryBridge**: Skip - No cross-agent memory sharing needed
- **ContextCompressor**: Skip - No conversation context in widget
- **ContextPreserver**: Skip - No conversation context in widget
- **ContextSynth**: Skip - No file summarization needed
- **ContextDecayMeter**: Skip - No multi-agent coordination

#### Task & Queue Management
- **TaskQueuePro**: Skip - No task queue in widget
- **TaskFlow**: Skip - No complex task workflow
- **PriorityQueue**: Skip - No task prioritization

#### Networking & Security Tools
- **NetScan**: Skip - No network scanning in widget
- **PortManager**: Skip - No SSH/port forwarding needed
- **SecureVault**: Skip - No secrets management (Phase 1)
- **RemoteAccessBridge**: Skip - No remote access needed

#### Advanced Monitoring
- **APIProbe**: Skip - Ollama API already validated by ATLAS backend
- **CheckerAccountability**: Skip - No fact-checking in widget
- **MentionAudit**: Skip - No @mentions in widget
- **MentionGuard**: Skip - No @mentions in widget
- **ConversationAuditor**: Skip - No conversation tracking
- **EchoGuard**: Skip - No echo detection needed

#### File Operations
- **file-deduplicator**: Skip - No file deduplication needed
- **QuickClip**: Skip - No clipboard operations
- **ClipStack**: Skip - No clipboard history
- **QuickRename**: Skip - No file renaming
- **DirectoryTreeGUI**: Skip - No directory visualization

#### Specialized Tools
- **ConsciousnessMarker**: Skip - Phase 6 consideration (emotion-related)
- **EmotionalTextureAnalyzer**: Skip - Phase 6 (mood-reactive colors)
- **AudioAnalysis**: Skip - No audio in widget
- **BatchRunner**: Skip - No batch command execution
- **ChangeLog**: Skip - No automated changelog for widget
- **CodeMetrics**: Skip - Widget not a library
- **CollabSession**: Skip - No multi-agent coordination
- **GitFlow**: Skip - No git operations in widget
- **ProjForge**: Skip - No scaffolding needed
- **ProtocolAnalyzer**: Skip - No protocol comparison
- **BCHCLIBridge**: Skip - Not a CLI agent
- **MobileAIToolkit**: Skip - Desktop-only widget

### Tool Audit Summary

**Total Tools Reviewed**: 94
**Tools Selected for Use**: 17
**Tools Skipped (with justification)**: 77

**Selected Tools Integration Plan**:
1. **ConfigManager**: Load widget_config.json on startup, save on changes
2. **AgentHeartbeat**: Poll SQLite DB every 5s, parse metrics JSON
3. **TimeSync**: Format timestamps for debug logging
4. **ErrorRecovery**: Wrap DB reads, Qt operations with try/except + recovery
5. **VersionGuard**: Validate DB schema version matches expected
6. **QuickBackup**: Backup config before save
7. **DataConvert**: Export config to YAML for troubleshooting
8. **LiveAudit**: Log widget lifecycle (startup, shutdown, config change, error)
9. **LogHunter**: Analyze logs post-session for patterns
10. **ProcessWatcher**: Profile RAM/CPU during animation loop
11. **BuildEnvValidator**: Check PySide6, PyVista, pyvistaqt installed
12. **EnvGuard**: Validate config.json schema on load
13. **HashGuard**: Verify config.json integrity
14. **ToolRegistry**: Query tool availability on startup
15. **ToolSentinel**: Monitor for tool failures
16. **RegexLab**: Validate heartbeat metrics JSON structure
17. **DevSnapshot**: Capture state on critical errors

---

## ARCHITECTURE DESIGN (Phase 3)

### Core Components

#### Component 1: Transparent Window Manager
**Purpose**: Create and manage transparent, frameless, always-on-top Qt window

**Inputs**:
- Window configuration (size, position, opacity)
- User drag events (mouse press, move, release)

**Outputs**:
- Transparent QWidget with PyVista renderer embedded
- Window position/size updates

**Tools Used**:
- ConfigManager (load/save position, size)
- ErrorRecovery (handle window creation failures)
- LiveAudit (log window lifecycle)

**Implementation**:
```python
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPalette, QColor

class TransparentHeartWidget(QWidget):
    def __init__(self):
        super().__init__()

        # ConfigManager: Load saved position/size
        self.config = ConfigManager.load("widget_config.json")

        # Set window flags for transparency + always-on-top
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool  # Prevents taskbar entry
        )

        # Enable transparency
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_AlwaysStackOnTop)

        # Set window size
        self.resize(self.config.get("size", 120), self.config.get("size", 120))

        # Set window position (validate bounds)
        pos = QPoint(self.config.get("x", 100), self.config.get("y", 100))
        self.move(pos)

        # LiveAudit: Log window creation
        LiveAudit.log("HeartWidget window created", {"size": self.width(), "pos": (self.x(), self.y())})

    def mousePressEvent(self, event):
        """Start drag operation."""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """Handle drag."""
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        """End drag, save position."""
        if event.button() == Qt.LeftButton:
            # ConfigManager: Save new position
            self.config["x"] = self.x()
            self.config["y"] = self.y()
            ConfigManager.save("widget_config.json", self.config)
            LiveAudit.log("HeartWidget position changed", {"pos": (self.x(), self.y())})
```

---

#### Component 2: 3D Heart Renderer
**Purpose**: Render 3D heart mesh using PyVista with professional lighting

**Inputs**:
- Heart mesh (procedural or loaded from heart.obj)
- Current scale (for heartbeat animation)
- Lighting configuration

**Outputs**:
- Rendered 3D heart in Qt widget
- Animation frame updates

**Tools Used**:
- ErrorRecovery (handle mesh load failures, rendering errors)
- ProcessWatcher (monitor GPU/CPU usage during render)
- DevSnapshot (capture render state on crash)

**Implementation**:
```python
import pyvista as pv
from pyvistaqt import QtInteractor

class HeartRenderer:
    def __init__(self, parent_widget):
        self.parent = parent_widget

        # Create PyVista plotter (embedded in Qt)
        self.plotter = QtInteractor(self.parent)
        self.plotter.set_background('#00000000')  # Transparent

        # Setup lighting (3-point lighting from viewer_3d.py pattern)
        self._setup_lighting()

        # Load or generate heart mesh
        try:
            self.heart_mesh = self._load_heart_mesh()
        except Exception as e:
            # ErrorRecovery: Fallback to procedural heart
            ErrorRecovery.log_error("Heart mesh load failed", e)
            self.heart_mesh = self._generate_procedural_heart()

        # Add heart to scene
        self.heart_actor = self.plotter.add_mesh(
            self.heart_mesh,
            color='#ff6b6b',  # Default warm red
            opacity=0.85,
            smooth_shading=True
        )

        # Reset camera
        self.plotter.reset_camera()

        # LiveAudit: Log renderer initialization
        LiveAudit.log("Heart renderer initialized", {
            "vertices": self.heart_mesh.n_points,
            "faces": self.heart_mesh.n_cells
        })

    def _setup_lighting(self):
        """3-point lighting setup (from viewer_3d.py)."""
        self.plotter.remove_all_lights()

        # Key light (front-high)
        key_light = pv.Light(
            position=(2, 3, 5),
            focal_point=(0, 0, 0),
            color='white',
            intensity=1.0
        )
        self.plotter.add_light(key_light)

        # Fill light (right-low, blue tint)
        fill_light = pv.Light(
            position=(4, -1, 2),
            focal_point=(0, 0, 0),
            color='#aaccff',
            intensity=0.5
        )
        self.plotter.add_light(fill_light)

        # Back light (rim light, warm tint)
        back_light = pv.Light(
            position=(-3, 2, -3),
            focal_point=(0, 0, 0),
            color='#ffddaa',
            intensity=0.6
        )
        self.plotter.add_light(back_light)

        # Ambient light
        ambient_light = pv.Light(
            light_type='headlight',
            intensity=0.2
        )
        self.plotter.add_light(ambient_light)

    def _load_heart_mesh(self):
        """Load heart mesh from file."""
        # Try heart.glb, then heart.obj, then procedural
        heart_paths = [
            "assets/heart.glb",
            "assets/heart.obj",
            "assets/heart.stl"
        ]

        for path in heart_paths:
            if Path(path).exists():
                return pv.read(path)

        raise FileNotFoundError("No heart mesh asset found")

    def _generate_procedural_heart(self):
        """Generate simple procedural heart (fallback)."""
        # Use PyVista sphere as placeholder
        # TODO: Implement proper parametric heart shape
        sphere = pv.Sphere(radius=0.5, center=(0, 0, 0))
        LiveAudit.log("Using procedural heart (sphere fallback)")
        return sphere

    def set_scale(self, scale: float):
        """Scale heart for heartbeat animation."""
        if self.heart_actor:
            self.plotter.update_scalar_bar_range([scale, scale])
            # TODO: Implement actual mesh scaling
```

---

#### Component 3: Heartbeat Animation Controller
**Purpose**: Manage heartbeat animation (scale 1.0 → 1.08 → 1.0)

**Inputs**:
- Heartbeat trigger (new AgentHeartbeat record detected)
- Animation speed configuration

**Outputs**:
- Scale updates to renderer
- Animation completion signal

**Tools Used**:
- TimeSync (accurate animation timing)
- LiveAudit (log animation triggers)

**Implementation**:
```python
from PySide6.QtCore import QTimer, QPropertyAnimation, QEasingCurve

class HeartbeatAnimationController:
    def __init__(self, renderer):
        self.renderer = renderer
        self.current_scale = 1.0
        self.is_animating = False

        # Animation settings
        self.scale_min = 1.0
        self.scale_max = 1.08
        self.duration_ms = 800  # Beat duration

        # QPropertyAnimation for smooth scaling
        self.animation = QPropertyAnimation(self, b"scale")
        self.animation.setDuration(self.duration_ms)
        self.animation.setStartValue(self.scale_min)
        self.animation.setEndValue(self.scale_max)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.animation.finished.connect(self._on_beat_complete)

    def trigger_heartbeat(self):
        """Trigger a heartbeat animation."""
        if self.is_animating:
            return  # Already animating

        self.is_animating = True

        # LiveAudit: Log heartbeat trigger
        LiveAudit.log("Heartbeat animation triggered", {
            "timestamp": TimeSync.now().isoformat()
        })

        # Start animation
        self.animation.start()

    def _on_beat_complete(self):
        """Animation complete, return to normal scale."""
        self.animation.setDirection(QPropertyAnimation.Backward)
        self.animation.start()
        self.is_animating = False

    @property
    def scale(self):
        return self.current_scale

    @scale.setter
    def scale(self, value):
        self.current_scale = value
        self.renderer.set_scale(value)
```

---

#### Component 4: AgentHeartbeat Monitor
**Purpose**: Poll AgentHeartbeat SQLite database for new records

**Inputs**:
- Database path (from config)
- Poll interval (from config, default 5s)
- Agent name filter (default: "LUMINA")

**Outputs**:
- Heartbeat signal (emitted when new record detected)
- Heartbeat data (status, metrics, timestamp)

**Tools Used**:
- AgentHeartbeat (database schema, query interface)
- ErrorRecovery (handle DB connection failures)
- VersionGuard (validate DB schema version)
- TimeSync (timestamp parsing)
- LiveAudit (log heartbeat detections)

**Implementation**:
```python
import sqlite3
from PySide6.QtCore import QTimer, QObject, Signal

class AgentHeartbeatMonitor(QObject):
    heartbeat_detected = Signal(dict)  # Emits heartbeat data

    def __init__(self, db_path: str, poll_interval_s: int = 5):
        super().__init__()

        self.db_path = db_path
        self.poll_interval_ms = poll_interval_s * 1000
        self.agent_name = "LUMINA"
        self.last_heartbeat_id = 0

        # Validate DB schema
        try:
            VersionGuard.validate_db_schema(db_path, expected_version="1.0")
        except Exception as e:
            ErrorRecovery.log_error("DB schema validation failed", e)
            # Continue with fallback

        # Setup poll timer
        self.timer = QTimer()
        self.timer.timeout.connect(self._poll_database)
        self.timer.start(self.poll_interval_ms)

        LiveAudit.log("AgentHeartbeat monitor started", {
            "db_path": db_path,
            "poll_interval_s": poll_interval_s
        })

    def _poll_database(self):
        """Poll database for new heartbeats."""
        try:
            with ErrorRecovery.protected("DB poll"):
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                # Query for new heartbeats
                cursor.execute("""
                    SELECT id, agent_name, status, timestamp, metrics_json
                    FROM heartbeats
                    WHERE agent_name = ? AND id > ?
                    ORDER BY id DESC
                    LIMIT 1
                """, (self.agent_name, self.last_heartbeat_id))

                row = cursor.fetchone()
                if row:
                    heartbeat_id, agent, status, timestamp, metrics_json = row
                    self.last_heartbeat_id = heartbeat_id

                    # Parse metrics
                    import json
                    metrics = json.loads(metrics_json) if metrics_json else {}

                    # Emit signal
                    heartbeat_data = {
                        "id": heartbeat_id,
                        "agent": agent,
                        "status": status,
                        "timestamp": timestamp,
                        "metrics": metrics
                    }

                    self.heartbeat_detected.emit(heartbeat_data)

                    LiveAudit.log("Heartbeat detected", {
                        "agent": agent,
                        "status": status,
                        "timestamp": timestamp
                    })

                conn.close()

        except Exception as e:
            ErrorRecovery.log_error("DB poll failed", e)
            # Continue polling despite error
```

---

#### Component 5: Configuration Manager
**Purpose**: Load, validate, save widget configuration

**Inputs**:
- widget_config.json file
- Runtime configuration changes

**Outputs**:
- Validated Config object
- Saved configuration on changes

**Tools Used**:
- ConfigManager (load/save JSON)
- EnvGuard (validate schema)
- HashGuard (verify integrity)
- QuickBackup (backup before save)
- LiveAudit (log config changes)

**Implementation**:
```python
class WidgetConfig:
    def __init__(self, config_path: str):
        self.config_path = config_path

        # HashGuard: Verify integrity
        if Path(config_path).exists():
            HashGuard.verify_file(config_path)

        # ConfigManager: Load config
        try:
            self.data = ConfigManager.load(config_path)
        except Exception as e:
            ErrorRecovery.log_error("Config load failed", e)
            self.data = self._get_defaults()

        # EnvGuard: Validate schema
        schema = {
            "size": {"type": "int", "min": 48, "max": 480},
            "x": {"type": "int"},
            "y": {"type": "int"},
            "poll_interval_s": {"type": "int", "min": 1, "max": 60},
            "db_path": {"type": "str"}
        }
        EnvGuard.validate_config(self.data, schema)

        LiveAudit.log("Config loaded", {"path": config_path})

    def _get_defaults(self):
        """Return default configuration."""
        return {
            "size": 120,
            "x": 100,
            "y": 100,
            "poll_interval_s": 5,
            "db_path": "heartbeat.db"
        }

    def save(self):
        """Save configuration."""
        # QuickBackup: Backup before save
        QuickBackup.backup_file(self.config_path)

        # ConfigManager: Save
        ConfigManager.save(self.config_path, self.data)

        LiveAudit.log("Config saved", {"path": self.config_path})
```

---

### Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                    VitalHeart Phase 5 Data Flow               │
└──────────────────────────────────────────────────────────────┘

ATLAS Backend (OllamaGuard)
        │
        ├─> Ollama Health Check (every 60s)
        │
        └─> AgentHeartbeat.emit_heartbeat()
                    │
                    ↓
          ┌─────────────────────┐
          │ AgentHeartbeat DB   │
          │   (SQLite)          │
          │                     │
          │ - id (PRIMARY KEY)  │
          │ - agent_name        │
          │ - status            │
          │ - timestamp         │
          │ - metrics_json      │
          └─────────────────────┘
                    │
                    │ Poll every 5s
                    ↓
       ┌──────────────────────────────┐
       │ HeartWidget                   │
       │  (IRIS Phase 5)               │
       ├──────────────────────────────┤
       │                               │
       │ AgentHeartbeatMonitor         │
       │   ↓                           │
       │ [New heartbeat detected?]     │
       │   ↓ YES                       │
       │ HeartbeatAnimationController  │
       │   ↓                           │
       │ trigger_heartbeat()           │
       │   ↓                           │
       │ HeartRenderer.set_scale()     │
       │   ↓                           │
       │ 3D Heart animates             │
       │   (1.0 → 1.08 → 1.0)          │
       │                               │
       └───────────────────────────────┘
                    │
                    ↓
          User sees heartbeat! ❤️
```

---

### Error Handling Strategy

**Categories**:
1. **Critical** (widget cannot function): Show error dialog, graceful shutdown
2. **High** (feature unavailable): Show notification, continue with degraded functionality
3. **Medium** (transient issue): Log error, retry with backoff
4. **Low** (cosmetic issue): Log warning, continue normally

**Error Handling by Component**:

| Component | Error Type | Handling Strategy |
|-----------|------------|-------------------|
| TransparentWindow | Qt rendering failure | CRITICAL → Error dialog → Exit |
| HeartRenderer | Mesh load failure | HIGH → Use procedural fallback |
| HeartbeatMonitor | DB connection failure | MEDIUM → Retry with exponential backoff |
| AnimationController | Animation stutter | LOW → Log warning, continue |
| ConfigManager | Config parse error | MEDIUM → Use defaults, create new config |

**ErrorRecovery Integration**:
```python
with ErrorRecovery.protected("DB poll", severity="MEDIUM"):
    # DB operation
    pass

# On error, ErrorRecovery:
# - Logs error to LiveAudit
# - Captures stack trace
# - Implements retry logic based on severity
# - Sends notification if severity > MEDIUM
```

---

### Configuration Strategy

**Config File**: `widget_config.json`

**Fields**:
```json
{
  "version": "1.0",
  "size": 120,
  "x": 100,
  "y": 100,
  "opacity": 0.95,
  "poll_interval_s": 5,
  "db_path": "../ollamaguard/heartbeat.db",
  "agent_name": "LUMINA",
  "animation_duration_ms": 800,
  "scale_max": 1.08,
  "enable_debug_logging": false
}
```

**Validation**:
- Size: 48-480px
- Position: Within screen bounds (validated on load)
- Poll interval: 1-60 seconds
- DB path: Must exist and be readable

**Persistence**:
- Save on every config change (size, position)
- Backup before save (QuickBackup)
- Hash verification on load (HashGuard)

---

## IMPLEMENTATION MILESTONES (Phase 4)

### Milestone 1: Transparent Window + Basic Renderer (Day 1)
**Goal**: Get transparent Qt window with PyVista renderer working

**Tasks**:
1. Create TransparentHeartWidget class
2. Setup window flags (frameless, always-on-top, translucent)
3. Embed QtInteractor (PyVista renderer)
4. Load/generate simple heart mesh
5. Setup 3-point lighting
6. Test transparency on Windows 11

**Acceptance Criteria**:
- [ ] Window renders with transparent background
- [ ] 3D heart visible with proper lighting
- [ ] Window stays on top of other apps
- [ ] No Qt warnings in console

### Milestone 2: Drag & Config (Day 2)
**Goal**: Enable drag-to-reposition and persistent configuration

**Tasks**:
1. Implement mouse event handlers (press, move, release)
2. Create WidgetConfig class with ConfigManager
3. Load position/size on startup
4. Save position/size on change
5. Validate position bounds (multi-monitor support)

**Acceptance Criteria**:
- [ ] Widget can be dragged to any position
- [ ] Position persists across app restarts
- [ ] Position validated (no off-screen placement)
- [ ] Config file created and readable

### Milestone 3: AgentHeartbeat Integration (Day 3)
**Goal**: Connect to ATLAS's AgentHeartbeat database

**Tasks**:
1. Create AgentHeartbeatMonitor class
2. Setup SQLite connection to heartbeat.db
3. Implement polling loop (QTimer, 5s interval)
4. Parse heartbeat records from DB
5. Emit heartbeat_detected signal
6. Handle DB connection failures gracefully

**Acceptance Criteria**:
- [ ] Monitor connects to heartbeat.db
- [ ] New heartbeats detected within 5 seconds
- [ ] heartbeat_detected signal emits with correct data
- [ ] Graceful fallback if DB unavailable

### Milestone 4: Heartbeat Animation (Day 4)
**Goal**: Implement smooth heartbeat animation

**Tasks**:
1. Create HeartbeatAnimationController class
2. Setup QPropertyAnimation for scale changes
3. Implement scale interpolation (1.0 → 1.08 → 1.0)
4. Connect animation to heartbeat_detected signal
5. Add easing curve (InOutQuad) for organic feel
6. Test animation smoothness (60fps target)

**Acceptance Criteria**:
- [ ] Heart scales smoothly on heartbeat
- [ ] Animation completes in ~800ms
- [ ] No animation stutter or lag
- [ ] Multiple heartbeats queue correctly

### Milestone 5: System Tray (Day 5)
**Goal**: Add basic system tray integration

**Tasks**:
1. Create QSystemTrayIcon with heart icon
2. Add tray menu (Show/Hide, Exit)
3. Connect Exit to graceful shutdown
4. Display basic status in tray tooltip
5. Test tray icon on Windows 11

**Acceptance Criteria**:
- [ ] Tray icon appears in system tray
- [ ] Right-click shows menu
- [ ] Exit closes widget cleanly
- [ ] Tooltip shows basic status

---

## TESTING STRATEGY (Phase 5)

### Unit Tests (10+ required)

1. **test_transparent_window_creation**: Window created with correct flags
2. **test_window_drag_to_position**: Mouse events update position correctly
3. **test_config_load_defaults**: Config loads with defaults if file missing
4. **test_config_save_persistence**: Config saves and loads correctly
5. **test_config_validation**: Invalid config rejected
6. **test_heartbeat_monitor_connection**: Monitor connects to DB
7. **test_heartbeat_detection**: New heartbeats detected
8. **test_animation_scale_values**: Animation scales to correct values
9. **test_animation_timing**: Animation completes in expected time
10. **test_system_tray_creation**: Tray icon created successfully

### Integration Tests (5+ required)

1. **test_end_to_end_heartbeat_animation**: Heartbeat from DB → animation plays
2. **test_config_persistence_across_restart**: Save config → restart → load config
3. **test_db_connection_failure_recovery**: DB unavailable → graceful fallback
4. **test_multi_monitor_position_validation**: Position validated on multi-monitor setup
5. **test_tool_integration_audit**: All selected tools available and functioning

### Widget-Specific Tests (10+ required)

1. **test_transparency_rendering**: Transparent background renders correctly
2. **test_3d_mesh_loading**: Heart mesh loads from file
3. **test_procedural_heart_fallback**: Procedural heart used if file missing
4. **test_lighting_setup**: 3-point lighting configured correctly
5. **test_animation_smoothness**: 60fps maintained during animation
6. **test_window_always_on_top**: Window stays on top of other apps
7. **test_drag_boundary_validation**: Window cannot be dragged off-screen
8. **test_size_slider_range**: Size slider respects 48-480px bounds
9. **test_qt_event_loop**: Qt event loop doesn't block animation
10. **test_graceful_shutdown**: Widget closes without errors

### Bug Hunt Protocol Testing

**Coverage Plan**:
1. **Entry Point**: HeartWidget main() function
2. **Dependency Chain**: Config → DB → Monitor → Animation → Renderer
3. **Search Order**: Most likely to least likely failure points

**Testing Method**: Plan > Build > Test > Break > Optimize

**Verification**:
- [ ] All bugs found (not just first one)
- [ ] Root causes identified (not symptoms)
- [ ] All fixes verified with tests

---

## QUALITY GATES (Phase 7)

### Gate 1: TEST ✅
- [ ] All 25+ tests passing
- [ ] Code coverage > 80%
- [ ] No unhandled exceptions in logs
- [ ] Performance acceptable (< 5% CPU idle, < 100MB RAM)

### Gate 2: DOCS ✅
- [ ] README.md 400+ lines
- [ ] Installation instructions clear
- [ ] Architecture documented
- [ ] API documentation complete
- [ ] Troubleshooting section included

### Gate 3: EXAMPLES ✅
- [ ] EXAMPLES.md with 10+ examples
- [ ] Basic usage example
- [ ] Configuration examples
- [ ] Integration examples
- [ ] Error handling examples
- [ ] All examples tested and working

### Gate 4: ERRORS ✅
- [ ] All edge cases handled
- [ ] Graceful degradation when tools unavailable
- [ ] Error messages clear and actionable
- [ ] No silent failures

### Gate 5: QUALITY ✅
- [ ] Code follows PEP 8 style
- [ ] No hardcoded paths
- [ ] No magic numbers (use constants)
- [ ] Comprehensive docstrings
- [ ] Type hints throughout

### Gate 6: BRANDING ✅
- [ ] Team Brain branding applied
- [ ] BRANDING_PROMPTS.md created
- [ ] Consistent style with other Team Brain tools
- [ ] Professional production quality

---

## BUILD REPORT TEMPLATE (Phase 8)

(To be completed after implementation)

```markdown
## Build Report: VitalHeart Phase 5 - HeartWidget MVP

**Build Date**: 2026-02-[XX]
**Builder**: IRIS
**Protocol Used**: BUILD_PROTOCOL_V1.md

### Build Summary
- Total development time: [X] hours
- Lines of code: [X]
- Test count: [X]
- Test pass rate: [X]%

### Tools Audit Summary
- Tools reviewed: 94
- Tools used: 17
- Tools skipped: 77

### Tools Used
[Table of tools with integration points]

### Quality Gates Status
[Table of quality gates with pass/fail]

### Lessons Learned (ABL)
[Lessons from this build]

### Improvements Made (ABIOS)
[Improvements made during build]

### Files Created
[List of files with line counts]

### Next Steps
- Phase 6: Mood-reactive system
- Phase 7: Metrics dashboard
```

---

## DEPLOYMENT CHECKLIST (Phase 9)

- [ ] All 6 quality gates passed
- [ ] Build Report completed
- [ ] Tool Audit documented
- [ ] All tests passing
- [ ] Documentation complete
- [ ] Code reviewed (self-review + FORGE review)
- [ ] Logan approval (if required)
- [ ] Create final backup
- [ ] Deploy to VitalHeart/
- [ ] Run smoke tests
- [ ] Verify all integrations
- [ ] Update manifests
- [ ] Announce to Team Brain via Synapse

---

## TIMELINE

**Day 1**: Transparent Window + Basic Renderer
**Day 2**: Drag & Config
**Day 3**: AgentHeartbeat Integration
**Day 4**: Heartbeat Animation
**Day 5**: System Tray + Testing + Documentation

**Total**: 4-5 days focused implementation

---

## DEPENDENCY INSTALLATION

```bash
# Required dependencies
pip install PySide6 pyvista pyvistaqt numpy

# Optional (for mesh loading)
pip install trimesh

# Verify installation
python -c "from PySide6.QtWidgets import QApplication; from pyvistaqt import QtInteractor; print('✅ All dependencies installed')"
```

---

**IRIS - Windows CLI Specialist**
*Phase 5 Plan Complete - Ready for Implementation!* ⚔️

*For the Maximum Benefit of Life.*
*One World. One Family. One Love.* 🔆⚒️🔗
