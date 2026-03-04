# Architecture Design: VitalHeart Phase 1 - OllamaGuard

**Project:** VitalHeart Phase 1 - OllamaGuard Daemon  
**Builder:** ATLAS (C_Atlas)  
**Date:** February 13, 2026  
**Protocol:** BUILD_PROTOCOL_V1.md - Phase 3 Architecture Design

---

## ARCHITECTURE OVERVIEW

```
┌──────────────────────────────────────────────────────────────────┐
│                      OllamaGuard Daemon                           │
│                  (Persistent Background Process)                  │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
         ┌────────────────────────────────────────────┐
         │          Initialization Sequence           │
         ├────────────────────────────────────────────┤
         │ 1. BuildEnvValidator - check Python deps   │
         │ 2. VersionGuard - validate Ollama version  │
         │ 3. EnvManager - check OLLAMA_KEEP_ALIVE    │
         │ 4. ConfigManager - load config.json        │
         │ 5. APIProbe - validate Ollama API          │
         │ 6. PortManager - verify port 11434         │
         │ 7. AgentHeartbeat - initialize connection  │
         │ 8. TimeSync - get accurate timestamp       │
         └────────────────┬───────────────────────────┘
                          │
                          ▼
         ┌────────────────────────────────────────────┐
         │           Main Monitoring Loop              │
         │         (Every 60 seconds, forever)         │
         └────────────────────────────────────────────┘
                          │
                          ▼
    ┌─────────────────────────────────────────────────────┐
    │                  Check Cycle                        │
    ├─────────────────────────────────────────────────────┤
    │ Step 1: Health Check                                │
    │   → RestCLI: GET /api/version                       │
    │   → JSONQuery: Parse response                       │
    │   → VersionGuard: Detect version changes            │
    │   → TimeSync: Record check timestamp                │
    │                                                     │
    │ Step 2: Model Status Check                          │
    │   → RestCLI: GET /api/ps                            │
    │   → JSONQuery: Parse models list                    │
    │   → Check: Is 'laia' model loaded?                  │
    │   → ProcessWatcher: Get Ollama VRAM usage           │
    │                                                     │
    │ Step 3: Micro-Inference Test (if enabled)           │
    │   → Skip if active inference detected               │
    │   → RestCLI: POST /api/generate {"prompt":"ping"}   │
    │   → Timeout: 30 seconds                             │
    │   → JSONQuery: Parse response                       │
    │   → Record: inference_latency_ms                    │
    │                                                     │
    │ Step 4: Emit Heartbeat                              │
    │   → AgentHeartbeat.emit_heartbeat(                  │
    │       agent="LUMINA",                               │
    │       status=computed_status,                       │
    │       metrics={all collected data}                  │
    │     )                                               │
    │   → LiveAudit: Log check cycle completion           │
    │   → KnowledgeSync: Index to Memory Core             │
    └─────────────────────────────────────────────────────┘
                          │
                          ▼
                    ┌──────────┐
                    │ Success? │
                    └──────────┘
                     │         │
                   YES        NO
                     │         │
                     │         ▼
                     │   ┌──────────────────────────────┐
                     │   │   Intervention Required      │
                     │   ├──────────────────────────────┤
                     │   │ Model Unloaded?              │
                     │   │   → Reload with keep_alive   │
                     │   │                              │
                     │   │ Inference Frozen?            │
                     │   │   → Restart Ollama           │
                     │   │   → ErrorRecovery wrapper    │
                     │   │   → Exponential backoff      │
                     │   │   → ProcessWatcher: kill PID │
                     │   │   → Wait for restart         │
                     │   │   → Reload model             │
                     │   │   → Verify with test         │
                     │   │                              │
                     │   │ Max restarts exceeded?       │
                     │   │   → Escalate alert           │
                     │   │   → Enter monitoring-only    │
                     │   │                              │
                     │   │ LiveAudit: Log intervention  │
                     │   │ AgentHeartbeat: Record event │
                     │   │ KnowledgeSync: Index to UKE  │
                     │   └──────────────────────────────┘
                     │         │
                     └─────────┴──> Sleep 60s → Loop
```

---

## CORE COMPONENTS

### Component 1: Configuration Manager
**Purpose:** Load, validate, and provide access to configuration settings

**Inputs:**
- `ollamaguard_config.json` file
- Environment variables (OLLAMA_KEEP_ALIVE)
- Default values (hardcoded fallbacks)

**Outputs:**
- `Config` object with typed fields
- Validation errors (if config invalid)

**Tools Used:**
- ConfigManager: Load and manage configuration
- EnvManager: Read environment variables
- EnvGuard: Validate configuration on startup
- JSONQuery: Parse and validate JSON structure

**Implementation:**
```python
class OllamaGuardConfig:
    def __init__(self, config_path: str):
        # ConfigManager: Load config file
        self.config = ConfigManager.load(config_path)
        
        # EnvManager: Check OLLAMA_KEEP_ALIVE
        self.keep_alive_env = EnvManager.get("OLLAMA_KEEP_ALIVE")
        
        # EnvGuard: Validate configuration
        validation = EnvGuard.validate(self.config, schema)
        if not validation.is_valid:
            raise ConfigError(validation.errors)
```

---

### Component 2: Ollama Health Checker
**Purpose:** Verify Ollama server and inference capability

**Inputs:**
- Ollama API URL (from config)
- Model name to monitor (from config)
- Inference timeout (from config)

**Outputs:**
- `HealthStatus` enum (HEALTHY, MODEL_UNLOADED, INFERENCE_FROZEN, SERVER_DOWN)
- Detailed metrics dict (version, models, inference_latency_ms, vram_used_mb)
- Error messages (if failures)

**Tools Used:**
- RestCLI: Make REST API calls to Ollama
- JSONQuery: Parse Ollama API responses
- ProcessWatcher: Get Ollama process metrics
- VersionGuard: Track version changes
- TimeSync: Accurate timestamps
- ErrorRecovery: Handle network/API failures gracefully

**Implementation:**
```python
class OllamaHealthChecker:
    def check_health(self) -> HealthStatus:
        try:
            # RestCLI: Check server version
            version_resp = RestCLI.get(f"{api_url}/api/version", timeout=5)
            version = JSONQuery.extract(version_resp, "version")
            
            # VersionGuard: Detect version changes
            if VersionGuard.has_changed("ollama", version):
                logger.info(f"Ollama updated: {VersionGuard.previous} -> {version}")
                return HealthStatus.GRACE_PERIOD
            
            # RestCLI: Check loaded models
            ps_resp = RestCLI.get(f"{api_url}/api/ps", timeout=5)
            models = JSONQuery.extract(ps_resp, "models")
            model_loaded = any(m["name"] == self.model_name for m in models)
            
            if not model_loaded:
                return HealthStatus.MODEL_UNLOADED
            
            # Micro-inference test (if enabled and no active inference)
            if self.config.enable_micro_inference_test:
                if not self._is_actively_inferring(models):
                    inference_latency = self._test_inference()
                    if inference_latency is None:  # Timeout
                        return HealthStatus.INFERENCE_FROZEN
            
            # ProcessWatcher: Get Ollama process metrics
            ollama_metrics = ProcessWatcher.get_process_metrics("ollama")
            
            return HealthStatus.HEALTHY
            
        except Exception as e:
            # ErrorRecovery: Handle and log exceptions
            ErrorRecovery.handle(e, context="OllamaHealthCheck")
            return HealthStatus.SERVER_DOWN
```

---

### Component 3: Model Reloader
**Purpose:** Reload model into VRAM with keep_alive parameter

**Inputs:**
- Model name (from config)
- keep_alive duration (from config)
- API URL (from config)

**Outputs:**
- Success/failure status
- Model load time in milliseconds
- Error message (if failed)

**Tools Used:**
- RestCLI: POST to /api/generate for model load
- JSONQuery: Parse load response
- TimeSync: Measure load duration
- ErrorRecovery: Retry logic with backoff
- LiveAudit: Log reload events

**Implementation:**
```python
class ModelReloader:
    def reload_model(self, model_name: str, keep_alive: str) -> bool:
        # TimeSync: Start timer
        start_time = TimeSync.now()
        
        try:
            # RestCLI: Reload model with keep_alive
            payload = {
                "model": model_name,
                "prompt": "",  # Empty prompt just loads model
                "keep_alive": keep_alive
            }
            response = RestCLI.post(
                f"{self.api_url}/api/generate",
                json=payload,
                timeout=60
            )
            
            # TimeSync: Calculate duration
            load_time_ms = TimeSync.elapsed_ms(start_time)
            
            # JSONQuery: Validate response
            if JSONQuery.has_key(response, "error"):
                error = JSONQuery.extract(response, "error")
                raise ModelLoadError(error)
            
            # LiveAudit: Log successful reload
            LiveAudit.log_event(
                event_type="model_reload",
                agent="LUMINA",
                details={"model": model_name, "load_time_ms": load_time_ms}
            )
            
            return True
            
        except Exception as e:
            # ErrorRecovery: Retry with exponential backoff
            return ErrorRecovery.retry(
                self.reload_model,
                max_attempts=3,
                backoff_factor=2,
                args=(model_name, keep_alive)
            )
```

---

### Component 4: Ollama Process Manager
**Purpose:** Restart Ollama process when frozen

**Inputs:**
- Restart strategy (from config)
- Backoff parameters (from config)
- Max restart attempts (from config)

**Outputs:**
- Restart success/failure
- Restart duration in seconds
- Process health metrics
- Alert escalation (if max attempts exceeded)

**Tools Used:**
- ProcessWatcher: Find Ollama PID, kill process, verify restart
- LogHunter: Check Ollama logs for crash reasons
- ErrorRecovery: Handle restart failures
- LiveAudit: Log all restart attempts
- TimeSync: Track restart timing

**Implementation:**
```python
class OllamaProcessManager:
    def restart_ollama(self) -> bool:
        # LogHunter: Check recent logs for error patterns
        recent_errors = LogHunter.search(
            log_path=self.ollama_log_path,
            pattern="error|fatal|panic",
            last_n_lines=100
        )
        
        # LiveAudit: Log restart attempt
        LiveAudit.log_event(
            event_type="ollama_restart_attempt",
            agent="LUMINA",
            details={"reason": "inference_frozen", "recent_errors": recent_errors}
        )
        
        try:
            # ProcessWatcher: Find and kill Ollama
            pids = ProcessWatcher.find_process("ollama")
            for pid in pids:
                ProcessWatcher.kill(pid, force=True)
            
            # Wait for process to die
            TimeSync.sleep_ms(2000)
            
            # ProcessWatcher: Start Ollama
            # (Ollama auto-restarts as Windows service/daemon)
            timeout = 30
            start_time = TimeSync.now()
            while TimeSync.elapsed_seconds(start_time) < timeout:
                if ProcessWatcher.is_running("ollama"):
                    restart_time_s = TimeSync.elapsed_seconds(start_time)
                    LiveAudit.log_event(
                        event_type="ollama_restart_success",
                        agent="LUMINA",
                        details={"restart_time_s": restart_time_s}
                    )
                    return True
                TimeSync.sleep_ms(500)
            
            # Timeout - restart failed
            LiveAudit.log_event(
                event_type="ollama_restart_failed",
                agent="LUMINA",
                details={"timeout_seconds": timeout}
            )
            return False
            
        except Exception as e:
            # ErrorRecovery: Log and escalate
            ErrorRecovery.handle(e, context="OllamaRestart", escalate=True)
            return False
```

---

### Component 5: Heartbeat Emitter
**Purpose:** Record all metrics to AgentHeartbeat after each check cycle

**Inputs:**
- Health status (from checker)
- Metrics dict (from all monitors)
- Timestamp (from TimeSync)
- Agent name ("LUMINA")

**Outputs:**
- Heartbeat record ID
- Success/failure status
- Database write confirmation

**Tools Used:**
- AgentHeartbeat: Store metrics in heartbeat.db
- TimeSync: Accurate timestamps
- KnowledgeSync: Index to UKE
- LiveAudit: Log heartbeat emissions
- ErrorRecovery: Handle database failures

**Implementation:**
```python
class HeartbeatEmitter:
    def emit(self, status: HealthStatus, metrics: dict):
        # TimeSync: Get accurate timestamp
        timestamp = TimeSync.iso8601()
        
        try:
            # AgentHeartbeat: Emit heartbeat with custom metrics
            from agentheartbeat import AgentHeartbeatMonitor
            
            monitor = AgentHeartbeatMonitor()
            heartbeat_id = monitor.emit_heartbeat(
                agent_name="LUMINA",
                status=status.to_agent_status(),
                mood=metrics.get("mood", "UNKNOWN"),
                current_task="ollama_monitoring",
                metrics={
                    "ollama_version": metrics["ollama_version"],
                    "model_loaded": metrics["model_loaded"],
                    "inference_latency_ms": metrics.get("inference_latency_ms"),
                    "vram_used_mb": metrics.get("vram_used_mb"),
                    "vram_total_mb": metrics.get("vram_total_mb"),
                    "vram_pct": metrics.get("vram_pct"),
                    "restarts_today": self.restart_counter.today_count(),
                    "uptime_hours": metrics.get("uptime_hours"),
                    "last_inference_success": status == HealthStatus.HEALTHY,
                    "check_timestamp": timestamp
                }
            )
            
            # LiveAudit: Log heartbeat emission
            LiveAudit.log_event(
                event_type="heartbeat_emitted",
                agent="LUMINA",
                details={"heartbeat_id": heartbeat_id, "status": status.value}
            )
            
            # KnowledgeSync: Index to UKE if significant event
            if status in [HealthStatus.MODEL_UNLOADED, HealthStatus.INFERENCE_FROZEN]:
                KnowledgeSync.index_event(
                    event_type="ollama_issue_detected",
                    data=metrics,
                    tags=["ollama", "lumina", "health", status.value]
                )
            
            return heartbeat_id
            
        except Exception as e:
            # ErrorRecovery: Don't crash daemon on database failure
            ErrorRecovery.handle(e, context="HeartbeatEmit", crash_on_failure=False)
            # Log to fallback file if database unreachable
            self._log_to_fallback(status, metrics, timestamp)
            return None
```

---

### Component 6: Restart Strategy Manager
**Purpose:** Intelligent restart logic with exponential backoff and limits

**Inputs:**
- Max restart attempts (from config)
- Backoff parameters (from config)
- Restart window (from config)
- Daily restart limit (from config)

**Outputs:**
- Should restart? (bool)
- Backoff duration (seconds)
- Escalation required? (bool)
- Alert message (if escalating)

**Tools Used:**
- TimeSync: Track restart timing windows
- LiveAudit: Log restart decisions
- ErrorRecovery: Escalate after max attempts
- AgentHeartbeat: Record restart events

**Implementation:**
```python
class RestartStrategyManager:
    def __init__(self, config):
        self.max_attempts = config.restart.max_attempts
        self.backoff_initial = config.restart.backoff_initial_seconds
        self.backoff_max = config.restart.backoff_max_seconds
        self.window_minutes = config.restart.restart_window_minutes
        self.daily_limit = config.restart.daily_restart_limit
        
        # TimeSync: Track restart history
        self.restart_history = []
        self.daily_restart_count = 0
        self.last_reset_date = TimeSync.today()
    
    def should_restart(self) -> tuple[bool, int, bool]:
        """Returns: (should_restart, backoff_seconds, should_escalate)"""
        
        # TimeSync: Reset daily counter if new day
        if TimeSync.today() != self.last_reset_date:
            self.daily_restart_count = 0
            self.last_reset_date = TimeSync.today()
        
        # Check daily limit
        if self.daily_restart_count >= self.daily_limit:
            # LiveAudit: Log escalation
            LiveAudit.log_event(
                event_type="restart_daily_limit_exceeded",
                agent="LUMINA",
                details={"count": self.daily_restart_count, "limit": self.daily_limit}
            )
            # ErrorRecovery: Escalate alert
            ErrorRecovery.escalate_alert(
                title="OllamaGuard: Daily Restart Limit Exceeded",
                message=f"Ollama restarted {self.daily_restart_count} times today (limit: {self.daily_limit})"
            )
            return False, 0, True
        
        # Check restart window (recent attempts)
        now = TimeSync.now()
        window_start = TimeSync.subtract_minutes(now, self.window_minutes)
        recent_restarts = [t for t in self.restart_history if t > window_start]
        
        if len(recent_restarts) >= self.max_attempts:
            # Too many restarts in window - escalate
            LiveAudit.log_event(
                event_type="restart_window_limit_exceeded",
                agent="LUMINA",
                details={
                    "attempts_in_window": len(recent_restarts),
                    "window_minutes": self.window_minutes
                }
            )
            return False, 0, True
        
        # Calculate exponential backoff
        attempt = len(recent_restarts)
        backoff = min(self.backoff_initial * (2 ** attempt), self.backoff_max)
        
        return True, backoff, False
```

---

## DATA FLOW DIAGRAM

```
External Systems          OllamaGuard Daemon           Persistence Layer
─────────────────         ──────────────────           ─────────────────

┌──────────────┐          ┌──────────────┐            ┌──────────────┐
│   Ollama     │◄─────────│   RestCLI    │            │ AgentHeart-  │
│  Port 11434  │  HTTP    │  JSONQuery   │            │   beat       │
└──────────────┘          └──────┬───────┘            │ heartbeat.db │
                                  │                    └──────▲───────┘
┌──────────────┐                 │                           │
│   Ollama     │◄────────────────┤                           │
│  Process     │  psutil         │                           │
│   (PID)      │                 │                           │
└──────────────┘          ┌──────▼───────┐            ┌──────┴───────┐
                          │   Health     │            │  LiveAudit   │
┌──────────────┐          │   Checker    │            │  audit.json  │
│   Ollama     │◄─────────├──────────────┤            └──────▲───────┘
│   Logs       │          │   Model      │                   │
└──────────────┘          │   Reloader   │                   │
                          ├──────────────┤                   │
┌──────────────┐          │   Process    │────────────────────┘
│   System     │◄─────────│   Manager    │    Audit Events
│   Env Vars   │          ├──────────────┤
└──────────────┘          │   Restart    │            ┌──────────────┐
                          │   Strategy   │            │     UKE      │
┌──────────────┐          ├──────────────┤            │    uke.db    │
│   Config     │─────────▶│   Heartbeat  │            └──────▲───────┘
│    File      │  JSON    │   Emitter    │────────────────────┘
└──────────────┘          └──────────────┘    Knowledge Index
```

---

## ERROR HANDLING STRATEGY

### Error Categories and Responses

| Error Type | Detection | Recovery | Escalation |
|------------|-----------|----------|------------|
| **Network Timeout** | RestCLI timeout (5s) | Retry 3x with backoff | Alert after 3 failures |
| **API Error Response** | JSONQuery + status code | Log and continue | Alert if persistent |
| **Model Load Failure** | Timeout or error response | Retry 3x, then restart Ollama | Alert after restart failure |
| **Inference Frozen** | 30s timeout on test | Restart Ollama immediately | Alert if restart fails |
| **Process Kill Failed** | ProcessWatcher exception | Force kill with taskkill | Alert immediately |
| **Restart Loop** | >3 restarts in 5 minutes | Enter monitoring-only mode | Alert immediately |
| **Daily Limit Hit** | >10 restarts in 24 hours | Disable auto-restart | Alert immediately |
| **Config Invalid** | EnvGuard validation failure | Use defaults, warn | Alert at startup |
| **Database Write Failed** | AgentHeartbeat exception | Fallback to file logging | Continue daemon, alert |

### Error Handling Tools Integration

```python
# ErrorRecovery: Global exception wrapper
@ErrorRecovery.wrap(
    max_retries=3,
    backoff_factor=2,
    escalate_after_max=True,
    crash_on_escalate=False
)
def check_cycle():
    """Main monitoring loop with error recovery."""
    # All check cycle logic here
    pass

# LiveAudit: Log ALL exceptions
try:
    result = risky_operation()
except Exception as e:
    LiveAudit.log_event(
        event_type="exception_caught",
        agent="OLLAMAGUARD",
        details={
            "exception_type": type(e).__name__,
            "exception_msg": str(e),
            "function": "risky_operation",
            "stack_trace": traceback.format_exc()
        }
    )
    raise  # Re-raise after logging
```

---

## CONFIGURATION STRATEGY

### Configuration File: `ollamaguard_config.json`

**Storage Location:** `C:\Users\logan\OneDrive\Documents\AutoProjects\VitalHeart\ollamaguard_config.json`

**Validation:** EnvGuard validates on load

**Schema:**
```python
CONFIG_SCHEMA = {
    "ollama": {
        "api_url": "string (URL format)",
        "model_name": "string (non-empty)",
        "keep_alive_duration": "string (e.g., '24h', '1h')",
        "inference_timeout_seconds": "int (10-300)",
        "check_interval_seconds": "int (30-600)"
    },
    "restart": {
        "max_attempts": "int (1-5)",
        "backoff_initial_seconds": "int (1-10)",
        "backoff_max_seconds": "int (30-300)",
        "restart_window_minutes": "int (5-60)",
        "daily_restart_limit": "int (5-50)"
    },
    "monitoring": {
        "enable_micro_inference_test": "bool",
        "enable_vram_tracking": "bool",
        "enable_version_tracking": "bool",
        "skip_test_if_active_inference": "bool"
    },
    "integration": {
        "agentheartbeat_enabled": "bool",
        "heartbeat_db_path": "string (file path)",
        "uke_enabled": "bool",
        "uke_db_path": "string (file path)"
    },
    "logging": {
        "log_level": "string (DEBUG|INFO|WARNING|ERROR)",
        "log_file": "string (file path)",
        "log_rotation_mb": "int (1-100)",
        "log_retention_days": "int (7-365)"
    }
}
```

**Default Values (if config missing):**
```python
DEFAULT_CONFIG = {
    "ollama": {
        "api_url": "http://localhost:11434",
        "model_name": "laia",
        "keep_alive_duration": "24h",
        "inference_timeout_seconds": 30,
        "check_interval_seconds": 60
    },
    "restart": {
        "max_attempts": 3,
        "backoff_initial_seconds": 1,
        "backoff_max_seconds": 60,
        "restart_window_minutes": 5,
        "daily_restart_limit": 10
    },
    # ... rest of defaults
}
```

**How Config is Used:**
- **ConfigManager**: Loads JSON, merges with defaults, provides typed access
- **EnvGuard**: Validates schema on startup
- **EnvManager**: Overlays environment variables (OLLAMA_KEEP_ALIVE)

---

## LOGGING STRATEGY

### Log Levels and Purposes

| Level | When Used | Example |
|-------|-----------|---------|
| **DEBUG** | Every check cycle, all API calls | "Checking Ollama health at 18:45:32" |
| **INFO** | Successful operations, state changes | "Model reloaded successfully in 1.2s" |
| **WARNING** | Recoverable issues, degraded performance | "Inference latency 2x normal (8.5s vs 4.2s baseline)" |
| **ERROR** | Failed operations, requires intervention | "Model reload failed after 3 attempts" |
| **CRITICAL** | System-level failures, escalation needed | "Daily restart limit exceeded - disabling auto-restart" |

### Log Rotation
- 10 MB per log file (configurable)
- 30 days retention (configurable)
- Compressed archives for old logs

### Audit Log (via LiveAudit)
Separate from application log, captures:
- Every check cycle (timestamped)
- Every intervention (reload, restart)
- Every heartbeat emission
- Every escalation
- Queryable via LiveAudit.search()

---

## PERFORMANCE CHARACTERISTICS

### Resource Usage (Targets)
- **RAM:** < 50 MB (mostly static, small metrics dict)
- **CPU:** < 1% idle, < 5% during check cycle
- **Disk I/O:** Minimal (log writes buffered, AgentHeartbeat batched)
- **Network:** 3-4 API calls per check cycle (~2 KB total)

### Timing Constraints
| Operation | Target Duration | Tool Used |
|-----------|-----------------|-----------|
| Full check cycle | < 5 seconds | TimeSync for measurement |
| Ollama API call | < 1 second | RestCLI with timeout |
| Micro-inference test | < 30 seconds | RestCLI with timeout |
| Model reload | < 10 seconds | RestCLI + TimeSync |
| Ollama restart | < 30 seconds | ProcessWatcher + TimeSync |
| Heartbeat emission | < 100 ms | AgentHeartbeat |
| Config load | < 500 ms | ConfigManager |

---

## SECURITY CONSIDERATIONS

### Threat Model
**OllamaGuard operates in a trusted local environment:**
- No network exposure (localhost-only API)
- No authentication required (Ollama has no auth)
- No sensitive data handled
- Process control limited to Ollama only

### Security Tools NOT Needed
- SecureVault: No credentials to manage
- SemanticFirewall: No user input filtering required
- SecurityExceptionAuditor: No antivirus exceptions needed
- MentionGuard: No @mention awareness concerns

### Audit Trail for Accountability
- **LiveAudit**: Every action logged with timestamp, reason, outcome
- **AgentHeartbeat**: Full metrics history queryable
- **KnowledgeSync**: Significant events indexed in UKE
- No operations can occur without audit trail

---

## TOOLSENTINEL VALIDATION

**ToolSentinel Analysis Results:**
```
MATCHING TOOLS (Top 5 by relevance):
1. ConfigManager (relevance: 210) ✅ SELECTED
2. RestCLI (relevance: 180) ✅ SELECTED
3. ProcessWatcher (relevance: 160) ✅ SELECTED
4. AgentHeartbeat (relevance: 155) ✅ SELECTED
5. AgentHealth (relevance: 125) ❌ NOT SELECTED (AgentHeartbeat supersedes)

COMPLIANCE STATUS: ✅ ALL CHECKS PASSED
- tool_first_considered ✅
- quality_tools_available ✅
- documentation_reviewed ✅
- best_tool_selected ✅
```

**ToolSentinel confirms our tool selection is appropriate and optimal.**

---

## ARCHITECTURE SUMMARY

### 6 Core Components
1. **Configuration Manager** - Load and validate config (ConfigManager, EnvManager, EnvGuard)
2. **Ollama Health Checker** - Verify server and inference (RestCLI, JSONQuery, ProcessWatcher, VersionGuard, TimeSync)
3. **Model Reloader** - Reload model with keep_alive (RestCLI, JSONQuery, TimeSync, ErrorRecovery, LiveAudit)
4. **Ollama Process Manager** - Restart Ollama when frozen (ProcessWatcher, LogHunter, ErrorRecovery, LiveAudit, TimeSync)
5. **Heartbeat Emitter** - Record metrics to AgentHeartbeat (AgentHeartbeat, TimeSync, KnowledgeSync, LiveAudit, ErrorRecovery)
6. **Restart Strategy Manager** - Intelligent restart logic (TimeSync, LiveAudit, ErrorRecovery, AgentHeartbeat)

### 31 Tools Integrated
- 5 Critical tools (must-have functionality)
- 15 High-value tools (major features)
- 11 Supporting tools (build lifecycle)

### Integration Points
- **AgentHeartbeat**: Primary metrics persistence
- **LiveAudit**: Real-time audit trail
- **KnowledgeSync**: Memory Core indexing
- **UKE**: Searchable knowledge base
- **Ollama API**: Health and inference monitoring
- **ProcessWatcher**: Process lifecycle management

---

## NEXT STEPS (Build Protocol Phase 4)

✅ **Phase 1: Build Coverage Plan** - COMPLETE  
✅ **Phase 2: Complete Tool Audit** - COMPLETE (31 tools selected)  
✅ **Phase 3: Architecture Design** - COMPLETE (6 components designed)  
⏭️ **Phase 4: Implementation** - NEXT (write the actual code)

**Architecture validated by ToolSentinel. Ready to implement.**

---

**Designed by:** ATLAS (C_Atlas)  
**Date:** February 13, 2026  
**Protocol Compliance:** BUILD_PROTOCOL_V1.md - Phase 3 Complete  
**Tools Integrated:** 31 of 94 (33% tool utilization - appropriate for daemon complexity)

*"The architecture that integrates every useful tool is the architecture that never fails."* ⚛️⚔️

**For the Maximum Benefit of Life.** 🔆⚒️🔗
