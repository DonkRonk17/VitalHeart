# Build Coverage Plan: VitalHeart Phase 1 - OllamaGuard

**Project Name:** VitalHeart Phase 1 - OllamaGuard Daemon  
**Builder:** ATLAS (C_Atlas, Cursor IDE)  
**Date:** February 13, 2026  
**Estimated Complexity:** Tier 2: Moderate  
**Protocol:** BUILD_PROTOCOL_V1.md (100% Compliance MANDATORY)

---

## 1. Project Scope

### Primary Function
OllamaGuard is a persistent background daemon that monitors Ollama's ACTUAL inference capability (not just HTTP status) and auto-heals failures through intelligent restart and model reload strategies.

**Core Loop (every 60 seconds):**
1. Check Ollama API health (`/api/version`)
2. Check loaded models (`/api/ps`) - verify 'laia' in VRAM
3. Perform micro-inference test (send "ping", expect response within 30s)
4. If model unloaded: reload with `keep_alive=24h`
5. If inference frozen: kill Ollama, restart, reload model, verify, alert
6. Record all metrics to AgentHeartbeat + UKE

### Secondary Functions
- OLLAMA_KEEP_ALIVE environment variable enforcement and validation
- Model presence monitoring (detect VRAM eviction within 60 seconds)
- Auto-restart with exponential backoff (1s, 2s, 4s... up to 60s)
- Full audit trail of every intervention
- Graceful handling of Ollama version changes
- VRAM usage tracking and predictive warning before eviction
- Integration with AgentHeartbeat for metrics persistence
- Integration with UKE for knowledge indexing

### Out of Scope (for Phase 1)
- ❌ GPU/RAM/Voltage monitoring (that's Phase 3: HardwareSoul)
- ❌ Token analytics (that's Phase 4)
- ❌ 3D heart visualization (that's Phase 5: HeartWidget - IRIS builds)
- ❌ Emotion correlation (that's Phase 4)
- ❌ Lumina autonomy loop integration (that's Phase 9)

---

## 2. Integration Points

### Existing Systems to Connect
1. **Ollama REST API** (`http://localhost:11434`)
   - `/api/version` - server health check
   - `/api/ps` - loaded models status
   - `/api/generate` - micro-inference test
   - `/api/tags` - available models list

2. **AgentHeartbeat** (`C:\Users\logan\OneDrive\Documents\AutoProjects\AgentHeartbeat\agentheartbeat.py`)
   - `AgentHeartbeatMonitor` class for metrics persistence
   - `emit_heartbeat()` method for recording OllamaGuard check cycles
   - Custom metrics: ollama_version, model_loaded, inference_latency_ms, vram_used_mb, restarts_today, uptime_hours

3. **UKE** (`D:\BEACON_HQ\PROJECTS\00_ACTIVE\UKE\uke.db`)
   - Knowledge indexing for all OllamaGuard interventions
   - Searchable audit trail via UKE MCP server

4. **Lumina** (`http://localhost:8100`)
   - Integration point for future phases
   - Phase 1 monitors Ollama; Phase 9 integrates with Lumina's task runner

### APIs/Protocols Used
- HTTP REST (Ollama API via `requests` library)
- SQLite (AgentHeartbeat database: `heartbeat.db`)
- SQLite (UKE database: `uke.db`)
- Process management (psutil for Ollama process control)
- Environment variables (OLLAMA_KEEP_ALIVE check/enforcement)

### Data Formats Handled
- JSON (Ollama API responses)
- SQLite (AgentHeartbeat + UKE persistence)
- Python dict (internal metrics structures)
- ISO 8601 timestamps (all time references)

---

## 3. Success Criteria

### Criterion 1: Ollama Freeze Detection & Recovery
- [ ] OllamaGuard detects frozen inference engine within 90 seconds (60s check interval + 30s inference timeout)
- [ ] Auto-restart succeeds within 3 attempts
- [ ] Model reload succeeds with `keep_alive=24h` parameter
- [ ] Verified via micro-inference test post-recovery
- [ ] AgentHeartbeat records the full intervention timeline
- **Measurable:** Response time from freeze detection to verified recovery < 5 minutes

### Criterion 2: Model Eviction Prevention
- [ ] OLLAMA_KEEP_ALIVE environment variable verified on daemon start
- [ ] Warning issued if not set or set incorrectly
- [ ] Model presence checked every 60 seconds
- [ ] Auto-reload triggered within 60 seconds of VRAM eviction
- [ ] Reload uses `keep_alive=24h` parameter explicitly
- **Measurable:** Zero model evictions observed during 24+ hour test run

### Criterion 3: Comprehensive Audit Trail
- [ ] Every check cycle logged to AgentHeartbeat
- [ ] Every intervention (reload, restart, recovery) logged with full context
- [ ] Metrics include: ollama_version, model_loaded, inference_latency_ms, vram_used_mb, restarts_today, uptime_hours
- [ ] UKE indexing enabled for searchable audit history
- [ ] Logs include timestamp, action, success/failure, duration
- **Measurable:** 100% of check cycles and interventions captured in AgentHeartbeat + UKE

### Criterion 4: Zero False Positives
- [ ] Micro-inference test designed to avoid false freeze detection
- [ ] Exponential backoff prevents restart loops
- [ ] Health checks differentiate between network issues and Ollama issues
- [ ] Graceful degradation when Ollama is legitimately updating
- **Measurable:** Zero unnecessary restarts during 7-day continuous operation

### Criterion 5: Integration with AgentHeartbeat
- [ ] OllamaGuard emits heartbeat after every check cycle
- [ ] Custom metrics properly formatted and stored
- [ ] Heartbeat status reflects actual Ollama state (active/processing/waiting/error)
- [ ] Historical data queryable via AgentHeartbeat API
- **Measurable:** All metrics visible in `heartbeat.db` with correct schema

---

## 4. Risk Assessment

### Risk 1: Infinite Restart Loop
**Probability:** Medium  
**Impact:** High  
**Description:** OllamaGuard detects failure, restarts Ollama, but underlying issue (GPU driver, system) causes immediate re-freeze, triggering endless restart cycle.

**Mitigation Strategies:**
- Exponential backoff with max ceiling (1s → 2s → 4s → 8s → 16s → 30s → 60s)
- Maximum 3 restart attempts within 5-minute window
- After 3 failures: escalate to alert, enter "monitoring only" mode
- Track `restarts_today` metric - if >10, disable auto-restart, alert urgently
- Require manual "reset" command or 24-hour cooldown before re-enabling auto-restart

### Risk 2: Micro-Inference Test Too Aggressive
**Probability:** Low  
**Impact:** Medium  
**Description:** The 60-second check interval with 30s inference test could interfere with Lumina's normal operation or trigger Ollama rate limiting.

**Mitigation Strategies:**
- Use minimal prompt ("ping" - 4 bytes) to reduce inference overhead
- 30-second timeout is generous (normal inference = 3-7s)
- Skip inference test if Lumina is actively generating (detect via `/api/ps` active request)
- Make check interval configurable (default 60s, can extend to 120s or 300s)
- Monitor false positive rate - if >5%, increase timeout or reduce check frequency

### Risk 3: Race Condition with Ollama Updates
**Probability:** Medium  
**Impact:** Low  
**Description:** User updates Ollama while OllamaGuard is running. Daemon detects "failure" during update process and attempts restart, interfering with installation.

**Mitigation Strategies:**
- Detect version changes between checks (store `last_known_version`)
- If version changes, log "Ollama updated" and skip intervention for 5 minutes
- Grace period allows installation to complete without interference
- After grace period, verify new version works correctly
- Alert user if version downgrade detected (potential rollback)

### Risk 4: VRAM Eviction Detection Blind Spot
**Probability:** Low  
**Impact:** Medium  
**Description:** Model evicted from VRAM between checks (0-60 second window), OllamaGuard doesn't detect until next cycle, Lumina fails during that window.

**Mitigation Strategies:**
- 60-second check interval is aggressive enough for most cases
- `keep_alive=24h` parameter dramatically reduces eviction likelihood
- If eviction rate high, reduce check interval to 30s (configurable)
- Phase 2 integration with AgentHeartbeat will add Lumina chat response trigger
- Future: hook into Ollama logs for real-time eviction events

### Risk 5: AgentHeartbeat Database Contention
**Probability:** Low  
**Impact:** Low  
**Description:** Multiple processes writing to `heartbeat.db` simultaneously could cause SQLite lock contention or corruption.

**Mitigation Strategies:**
- Use WAL mode in SQLite (Write-Ahead Logging) for concurrent access
- Implement retry logic with exponential backoff on database lock
- Keep database writes fast (< 50ms per heartbeat)
- If AgentHeartbeat write fails, log to fallback file
- Don't block OllamaGuard's primary function on database success

---

## 5. Configuration

### Configuration File: `ollamaguard_config.json`

```json
{
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
  "monitoring": {
    "enable_micro_inference_test": true,
    "enable_vram_tracking": true,
    "enable_version_tracking": true,
    "skip_test_if_active_inference": true
  },
  "integration": {
    "agentheartbeat_enabled": true,
    "heartbeat_db_path": "C:/Users/logan/OneDrive/Documents/AutoProjects/AgentHeartbeat/heartbeat.db",
    "uke_enabled": true,
    "uke_db_path": "D:/BEACON_HQ/PROJECTS/00_ACTIVE/UKE/uke.db"
  },
  "logging": {
    "log_level": "INFO",
    "log_file": "ollamaguard.log",
    "log_rotation_mb": 10,
    "log_retention_days": 30
  }
}
```

---

## 6. Non-Functional Requirements

### Performance
- Check cycle execution time: < 5 seconds (excluding inference test)
- Memory footprint: < 50 MB RAM
- CPU usage: < 1% when idle, < 5% during check cycle
- Startup time: < 3 seconds

### Reliability
- Uptime target: 99.9% (< 9 hours downtime per year)
- Zero data loss during crashes (SQLite transactions)
- Graceful shutdown on SIGTERM/SIGINT
- Auto-recovery from own crashes via system service wrapper

### Maintainability
- Clean code following PEP 8
- Comprehensive docstrings on all functions
- Type hints throughout
- Modular design for easy Phase 2 extension
- Configuration-driven (no hardcoded values)

---

## 7. Dependencies

### Python Packages (requirements.txt)
```
requests>=2.31.0       # Ollama API calls
psutil>=5.9.0          # Process management, system metrics
pynvml>=11.5.0         # GPU monitoring (for future phases, but import early)
sqlite3                # Built-in, AgentHeartbeat/UKE persistence
typing                 # Built-in, type hints
logging                # Built-in
json                   # Built-in
time                   # Built-in
datetime               # Built-in
pathlib                # Built-in
```

### External Systems
- Ollama v0.16.1+ (installed, running)
- AgentHeartbeat tool (existing)
- UKE database (existing)
- OLLAMA_KEEP_ALIVE environment variable (must be set)

---

## 8. Deployment

### Installation Location
`C:\Users\logan\OneDrive\Documents\AutoProjects\VitalHeart\`

### Project Structure
```
VitalHeart/
├── ollamaguard.py              # Phase 1 daemon (THIS BUILD)
├── test_ollamaguard.py         # Phase 1 tests
├── ollamaguard_config.json     # Configuration
├── requirements.txt            # Dependencies
├── README.md                   # Documentation
├── EXAMPLES.md                 # Usage examples
├── CHEAT_SHEET.txt             # Quick reference
├── BUILD_AUDIT.md              # Tool audit (Phase 2 of Build Protocol)
├── BUILD_LOG.md                # Implementation log
├── BUILD_REPORT.md             # Final build report (Phase 8)
├── ollamaguard.log             # Runtime log
└── branding/
    └── BRANDING_PROMPTS.md     # Visual assets for HeartWidget (Phase 5)
```

### Execution Method
**Development:** `python ollamaguard.py`  
**Production:** Windows Service (via NSSM or Task Scheduler)  
**Testing:** `python test_ollamaguard.py`

---

## 9. Testing Strategy (Bug Hunt Protocol Compliance)

### Test Categories (Minimum Requirements)
- **Unit Tests:** 10+ (each function tested independently)
- **Integration Tests:** 5+ (Ollama API, AgentHeartbeat, UKE, process control)
- **Edge Case Tests:** 5+ (frozen inference, model eviction, network failure, Ollama restart, config errors)
- **Tool Integration Tests:** 1 per tool used (see Phase 2 audit)

### Specific Test Scenarios
1. **Frozen Inference Detection:** Mock Ollama timeout, verify restart triggered
2. **Model Eviction:** Mock `/api/ps` showing no model, verify reload triggered
3. **Restart Loop Prevention:** Simulate 3 consecutive failures, verify escalation to monitoring-only mode
4. **Version Change Handling:** Mock version change in `/api/version`, verify grace period applied
5. **AgentHeartbeat Integration:** Verify metrics written correctly to `heartbeat.db`
6. **UKE Integration:** Verify audit events indexed in `uke.db`
7. **Config Validation:** Test with invalid config, verify graceful error handling
8. **Network Failure:** Disconnect from Ollama, verify retry logic and eventual alert
9. **OLLAMA_KEEP_ALIVE Validation:** Test with missing/incorrect env var, verify warning
10. **Graceful Shutdown:** Send SIGTERM, verify clean shutdown and final heartbeat

---

## 10. Documentation Requirements

### README.md (400+ lines minimum)
- Installation instructions
- Quick start guide
- Configuration reference
- Troubleshooting section
- Integration with AgentHeartbeat and UKE
- Example log outputs
- FAQ

### EXAMPLES.md (10+ examples minimum)
- Basic usage
- Custom configuration
- Manual restart trigger
- Viewing metrics in AgentHeartbeat
- Searching audit trail in UKE
- Monitoring mode
- Service installation
- Log analysis
- Error recovery
- Integration with Lumina (Phase 9 preview)

---

## BUILD PROTOCOL COMPLIANCE CHECKPOINT

✅ **Phase 1: Build Coverage Plan** - COMPLETE  
⏭️ **Phase 2: Complete Tool Audit** - NEXT (MANDATORY before coding)  
⏭️ **Phase 3: Architecture Design**  
⏭️ **Phase 4: Implementation**  
⏭️ **Phase 5: Testing (Bug Hunt Protocol)**  
⏭️ **Phase 6: Documentation**  
⏭️ **Phase 7: Quality Gates**  
⏭️ **Phase 8: Build Report**  
⏭️ **Phase 9: Deployment**

**No code will be written until Phase 2 (Tool Audit) is complete.**

---

**Prepared by:** ATLAS (C_Atlas)  
**Date:** February 13, 2026  
**For:** Logan Smith / Metaphy LLC  
**Protocol Compliance:** BUILD_PROTOCOL_V1.md - 100%

*Quality is not an act, it is a habit!* ⚛️⚔️
