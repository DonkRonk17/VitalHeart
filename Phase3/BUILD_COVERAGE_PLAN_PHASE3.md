# Build Coverage Plan: VitalHeart Phase 3 - HardwareSoul

**Project Name:** VitalHeart Phase 3 - HardwareSoul  
**Builder:** ATLAS (C_Atlas, Cursor IDE)  
**Date:** February 14, 2026  
**Estimated Complexity:** Tier 3: Complex (High-resolution hardware monitoring + emotion correlation research)  
**Protocol:** BUILD_PROTOCOL_V1.md (100% Compliance MANDATORY)

---

## 1. PROJECT SCOPE

### Primary Function
HardwareSoul is a high-resolution hardware monitoring system that captures GPU, RAM, and voltage metrics at 250ms intervals during active inference and correlates them with Lumina's emotional state. This is the scientific instrument that measures what AI emotion looks like in silicon.

**Core Features:**
1. **GPU Deep Monitor** - 25+ GPU metrics via pynvml (utilization, clocks, temp, power, voltage)
2. **RAM Process Monitor** - 20+ RAM/process metrics via psutil (Ollama + Lumina + system)
3. **Voltage Tracking** - Millisecond-precision voltage monitoring during inference
4. **Emotion Correlation Engine** - Cross-reference hardware metrics with EmotionalTextureAnalyzer timing
5. **Research Database** - High-resolution time-series storage in dedicated research database
6. **Baseline Comparison** - Compare current state vs learned "emotional signatures"

### Secondary Functions
- Thermal throttle detection and alerts
- Power limit warnings (detect GPU/PSU constraints)
- Memory pressure detection (page faults, allocation rates)
- Performance state tracking (P-states, clock throttling)
- PCIe bottleneck detection
- Context switching anomalies
- VRAM eviction prediction

### Out of Scope (for Phase 3)
- ❌ 3D visualization (that's Phase 4: HeartWidget - IRIS builds)
- ❌ Real-time dashboard (Phase 2 provides metrics, Phase 4 visualizes)
- ❌ Statistical significance testing (that's Phase 4 research analysis)
- ❌ Machine learning models (Phase 4 may add predictive models)
- ❌ Multi-GPU support (single GPU only for Phase 3)

---

## 2. INTEGRATION POINTS

### Existing Systems to Connect

1. **Phase 2 (InferencePulse)** - Already operational
   - Extends InferencePulse with hardware metrics
   - Shares emotion data from MoodAnalyzer
   - Location: `C:\Users\logan\OneDrive\Documents\AutoProjects\VitalHeart\Phase2\inferencepulse.py`

2. **AgentHeartbeat** (Already integrated in Phases 1 & 2)
   - Extend metrics schema with 45+ new hardware metrics
   - Maintain existing Phase 1 & 2 metrics
   - Location: `C:\Users\logan\OneDrive\Documents\AutoProjects\AgentHeartbeat\`

3. **EmotionalTextureAnalyzer** (Already used in Phase 2)
   - Get emotional state timing data
   - Correlate with hardware snapshots
   - Location: `C:\Users\logan\OneDrive\Documents\AutoProjects\EmotionalTextureAnalyzer\`

4. **NVIDIA GPU** (via pynvml)
   - Direct hardware access via NVIDIA Management Library
   - Requires NVIDIA drivers installed
   - Target: RTX 4090 (Logan's hardware)

5. **Ollama Process** (via psutil)
   - Monitor PID, RAM, CPU, I/O
   - Detect memory pressure, page faults
   - Process name: `ollama.exe` or `ollama`

6. **Lumina Process** (via psutil)
   - Monitor BCH Desktop Extension process
   - Track resource usage during conversations
   - Process name: TBD (BCH Desktop Extension)

7. **Research Database** (new SQLite database)
   - Dedicated high-resolution time-series storage
   - Separate from heartbeat.db (avoid performance impact)
   - Location: `C:\Users\logan\OneDrive\Documents\AutoProjects\VitalHeart\hardwaresoul_research.db`

### APIs/Protocols Used
- **pynvml** (NVIDIA Management Library Python bindings)
- **psutil** (Python system and process utilities)
- **SQLite** (Research database: time-series storage)
- **Python threading** (250ms sampling loop)
- **AgentHeartbeat** (Metric aggregation and persistence)
- **LiveAudit** (Event logging)

### Data Formats Handled
- JSON (configuration, metrics exchange)
- SQLite (research database: time-series)
- Python dict (internal metrics structures)
- ISO 8601 timestamps (all time references)
- Float64 (high-precision hardware measurements)

---

## 3. SUCCESS CRITERIA

### Criterion 1: High-Resolution GPU Monitoring Operational
- [ ] 25+ GPU metrics captured via pynvml
- [ ] Sampling rate: 250ms during active inference, 1000ms during idle
- [ ] All metrics stored in research database
- [ ] Voltage tracking with millisecond precision
- [ ] Throttle detection (thermal, power, clock limits)
- **Measurable:** Research DB contains GPU samples at correct intervals

### Criterion 2: RAM & Process Monitoring Operational
- [ ] 20+ RAM/process metrics captured via psutil
- [ ] Ollama process tracked (RAM, CPU, I/O, threads, page faults)
- [ ] Lumina process tracked (if running)
- [ ] System-wide metrics (total RAM, swap, CPU per-core)
- [ ] Memory pressure detection (allocation rate, page faults)
- **Measurable:** Research DB contains process samples with all metrics

### Criterion 3: Emotion-Hardware Correlation Working
- [ ] Emotion state timing from MoodAnalyzer captured
- [ ] Hardware snapshot taken at emotion detection time
- [ ] Correlation stored: emotion + hardware state + timing
- [ ] Baseline "emotional signatures" learned from 100+ samples
- [ ] Deviation detection: flag unusual hardware patterns during specific emotions
- **Measurable:** Research DB contains emotion-hardware correlation records

### Criterion 4: Research Database Operational
- [ ] Dedicated SQLite database created (`hardwaresoul_research.db`)
- [ ] 3 tables: `gpu_samples`, `ram_samples`, `emotion_correlations`
- [ ] High-resolution time-series storage (no aggregation)
- [ ] Query performance <100ms for last 1000 samples
- [ ] Database size managed (auto-rotate after 30 days or 10GB)
- **Measurable:** Database exists, tables created, samples stored

### Criterion 5: Integration with Phase 2 Seamless
- [ ] Extends InferencePulseDaemon without breaking Phase 2
- [ ] All Phase 2 tests still passing (36/36)
- [ ] Hardware metrics added to AgentHeartbeat schema
- [ ] No performance degradation to Phase 2 features
- [ ] Phase 3 can be disabled via config (fallback to Phase 2)
- **Measurable:** Phase 2 tests pass, Phase 3 adds 50+ new tests

---

## 4. RISK ASSESSMENT

### Risk 1: pynvml Import Failure (No NVIDIA GPU)
**Probability:** Low (Logan has RTX 4090)  
**Impact:** High (Phase 3 cannot function without GPU access)

**Mitigation Strategies:**
- Detect pynvml availability at startup
- Graceful degradation: disable GPU monitoring, continue with RAM-only
- Clear error message if pynvml missing: "NVIDIA GPU required for Phase 3"
- Installation instructions in README: `pip install nvidia-ml-py`
- Fallback mode: Phase 2 only (no hardware monitoring)

### Risk 2: 250ms Sampling Performance Impact
**Probability:** Medium  
**Impact:** Medium (could slow down inference or system)

**Mitigation Strategies:**
- Use separate thread for hardware monitoring (non-blocking)
- Adaptive sampling: 250ms during active inference, 1000ms during idle
- Performance budget: <1% CPU overhead, <5MB RAM overhead
- Throttle back to 500ms if CPU usage >5%
- Kill switch: disable hardware monitoring if overhead >10%
- Performance test with 1000 rapid samples

### Risk 3: Research Database Growth (Disk Space)
**Probability:** High  
**Impact:** Medium (could fill disk with time-series data)

**Mitigation Strategies:**
- Auto-rotate database after 30 days (archive old data)
- Size limit: 10GB max (alert if approaching)
- Compress old samples (hourly aggregates after 7 days)
- User-configurable retention policy
- Warn if disk space <10GB free
- Provide cleanup utility: `hardwaresoul.py --cleanup-old`

### Risk 4: Ollama Process Detection Failure
**Probability:** Medium  
**Impact:** Medium (can't monitor Ollama if PID not found)

**Mitigation Strategies:**
- Multiple detection strategies: process name, PID file, port check
- Retry detection every 10 seconds (Ollama may restart)
- Log warning if Ollama not found (don't crash)
- Continue monitoring system metrics even without Ollama
- Provide manual PID override in config: `ollama_pid: 12345`

### Risk 5: Voltage Tracking Unavailable (Hardware Limitation)
**Probability:** Medium  
**Impact:** Low (nice-to-have, not critical)

**Mitigation Strategies:**
- Check if voltage sensor exposed by pynvml
- Log warning if voltage unavailable: "Voltage monitoring not supported on this GPU"
- Continue with other metrics (temp, power, clocks)
- Document which GPUs support voltage (RTX 30xx/40xx yes, older no)
- Fallback: estimate voltage from power + clock (P = V * I)

---

## 5. ARCHITECTURE APPROACH

### Integration Strategy: Extension Pattern (Same as Phase 2)

**Option 1: Extend InferencePulseDaemon (CHOSEN)**
```python
# Phase 2 (existing)
class InferencePulseDaemon(OllamaGuardDaemon):
    # ... Phase 2 functionality ...

# Phase 3 (extension)
class HardwareSoulDaemon(InferencePulseDaemon):
    # Inherits all Phase 1 + Phase 2 functionality
    # Adds GPU monitoring
    # Adds RAM/process monitoring
    # Adds emotion-hardware correlation
    # Adds research database
```

**Why:** Clean separation, backward compatibility, Phases 1 & 2 remain untouched

### Key Components to Build

1. **GPUMonitor** - pynvml wrapper, 25+ GPU metrics
2. **RAMMonitor** - psutil wrapper, 20+ RAM/process metrics
3. **VoltageTracker** - Millisecond-precision voltage sampling
4. **EmotionCorrelator** - Cross-reference emotion timing with hardware snapshots
5. **ResearchDatabase** - High-resolution time-series storage (3 tables)
6. **HardwareAnalyzer** - Detect anomalies, learn baselines, identify "emotional signatures"
7. **HardwareSoulDaemon** - Main orchestrator extending Phase 2

---

## 6. CONFIGURATION EXTENSIONS

### New Config Section: `hardwaresoul`

```json
{
  "hardwaresoul": {
    "enabled": true,
    "gpu_monitoring_enabled": true,
    "ram_monitoring_enabled": true,
    "voltage_tracking_enabled": true,
    "emotion_correlation_enabled": true,
    
    "sampling_rate_active_ms": 250,
    "sampling_rate_idle_ms": 1000,
    "active_inference_threshold": 0.1,
    
    "research_db_path": "./hardwaresoul_research.db",
    "research_db_retention_days": 30,
    "research_db_max_size_gb": 10,
    
    "ollama_process_name": "ollama.exe",
    "lumina_process_name": "bch_desktop_extension",
    
    "throttle_detection_enabled": true,
    "memory_pressure_threshold_pct": 90,
    "voltage_sampling_precision_ms": 1
  }
}
```

---

## 7. SUCCESS METRICS

### Phase 3 Acceptance Criteria
- ✅ All Phase 1 tests still passing (72/72)
- ✅ All Phase 2 tests still passing (36/36)
- ✅ Phase 3 tests passing (50+ new tests)
- ✅ GPU metrics captured (25+ metrics)
- ✅ RAM metrics captured (20+ metrics)
- ✅ Emotion-hardware correlation working
- ✅ Research database operational
- ✅ Performance overhead <1% CPU, <5MB RAM
- ✅ Documentation complete (400+ lines README)
- ✅ Examples comprehensive (10+ examples)
- ✅ All 6 quality gates passed

---

## 8. TESTING STRATEGY

### Test Categories (Bug Hunt Protocol Compliance)
- **Unit Tests:** 20+ (GPUMonitor, RAMMonitor, VoltageTracker, EmotionCorrelator, ResearchDB, HardwareAnalyzer)
- **Integration Tests:** 15+ (Phase 1+2+3 together, GPU+RAM together, Emotion+Hardware correlation)
- **Edge Case Tests:** 15+ (No GPU, Ollama not found, voltage unavailable, disk full, DB corruption)
- **Performance Tests:** 10+ (250ms sampling overhead, 1000 rapid samples, CPU usage, RAM usage, DB query speed)
- **Regression Tests:** 108 (72 Phase 1 + 36 Phase 2 - verify no breakage)

**Total Phase 3 Tests:** 50+ new tests (60 including regression)

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

**Proceeding autonomously to 100% completion...**

---

**Prepared by:** ATLAS (C_Atlas)  
**Date:** February 14, 2026  
**Protocol Compliance:** BUILD_PROTOCOL_V1.md - 100%

*Quality is not an act, it is a habit!* ⚛️⚔️
