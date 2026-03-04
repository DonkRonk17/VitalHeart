# Bug Hunt Coverage Plan - VitalHeart Phase 3: HardwareSoul

**Target:** HardwareSoul Phase 3 - GPU/RAM monitoring, emotion correlation, research database  
**Date:** February 14, 2026  
**Hunter:** ATLAS (C_Atlas)  
**Protocol:** Bug Hunt Protocol (100% MANDATORY)

---

## 1. SCOPE DEFINITION

### Files in Scope:
- `hardwaresoul.py` (945 lines - main daemon)
- `requirements.txt` (dependencies)
- Phase 2 inheritance: `inferencepulse.py` (must not break)
- Phase 1 inheritance: `ollamaguard.py` (must not break)

### Systems in Scope:
1. **GPUMonitor** - pynvml integration (25 metrics)
2. **RAMMonitor** - psutil integration (27 metrics)
3. **VoltageTracker** - Voltage monitoring (placeholder)
4. **EmotionCorrelator** - Emotion-hardware matching
5. **ResearchDatabase** - 3-table SQLite with WAL
6. **HardwareAnalyzer** - Anomaly detection
7. **HardwareSoulDaemon** - Orchestrator (extends Phase 2)

### Out of Scope:
- Phase 1 OllamaGuard testing (already verified with 72 tests)
- Phase 2 InferencePulse testing (already verified with 36 tests)
- nvidia-smi parsing (voltage tracking placeholder documented)

---

## 2. ENTRY POINTS

### Where Problems Manifest:
1. **Daemon startup** - Phase 3 initialization after Phase 2
2. **GPU sampling loop** - pynvml calls every 250ms/1000ms
3. **RAM sampling loop** - psutil calls every 250ms/1000ms
4. **Research DB writes** - Batched SQLite inserts
5. **Emotion correlation** - Timing match between emotion and hardware
6. **Thread coordination** - 5 concurrent threads (Phases 1, 2, 3 GPU, 3 RAM, 3 correlation)

### What Triggers Issues:
- `python hardwaresoul.py` (main entry)
- GPU not available (NVIDIA drivers missing)
- pynvml import failure
- Ollama/Lumina process not found
- Database write failure
- Sampling rate too aggressive (CPU overhead)
- Thread race conditions

---

## 3. DEPENDENCY CHAIN

### Phase 3 Inheritance Chain:
```
OllamaGuardDaemon (Phase 1)
    ↓ extends
InferencePulseDaemon (Phase 2)
    ↓ extends
HardwareSoulDaemon (Phase 3)
```

### Component Dependencies:
```
HardwareSoulDaemon
    ├─> GPUMonitor (depends: pynvml)
    ├─> RAMMonitor (depends: psutil)
    ├─> VoltageTracker (placeholder)
    ├─> EmotionCorrelator (depends: Phase 2 MoodAnalyzer)
    ├─> ResearchDatabase (depends: sqlite3)
    └─> HardwareAnalyzer (depends: ResearchDatabase)
```

### What Calls What:
1. `main()` → `HardwareSoulDaemon.__init__()`
2. `HardwareSoulDaemon.__init__()` → `super().__init__()` (Phase 2)
3. `HardwareSoulDaemon.start()` → `super().start()` (Phase 2 thread)
4. `HardwareSoulDaemon.start()` → `_start_gpu_monitor()` (Phase 3 GPU thread)
5. `HardwareSoulDaemon.start()` → `_start_ram_monitor()` (Phase 3 RAM thread)
6. `_gpu_monitoring_loop()` → `GPUMonitor.sample()` → `pynvml.*` → `ResearchDatabase.add_gpu_sample()`
7. `_ram_monitoring_loop()` → `RAMMonitor.sample()` → `psutil.*` → `ResearchDatabase.add_ram_sample()`

---

## 4. SEARCH ORDER (Most Likely → Least Likely)

### Category 1: Initialization Errors (Highest Risk)
1. **pynvml import failure** - Will disable GPU monitoring
   - Test: Import without nvidia-ml-py installed
   - Verification: Should log warning and continue with RAM-only

2. **GPU device not found** - Will disable GPU monitoring
   - Test: Request invalid GPU index
   - Verification: Should log error and continue

3. **Phase 2 inheritance broken** - Would crash daemon
   - Test: Verify `super().__init__()` and `super().start()` work
   - Verification: All Phase 1 & 2 tests still pass

4. **Research DB initialization failure** - Would crash daemon
   - Test: Invalid DB path, permission denied
   - Verification: Should log error and fail gracefully

### Category 2: Sampling Loop Errors (High Risk)
5. **GPU sample exceptions** - Could crash GPU thread
   - Test: Each pynvml call individually
   - Verification: Wrapped in try-except, returns None on failure

6. **RAM sample exceptions** - Could crash RAM thread
   - Test: Process not found, psutil exceptions
   - Verification: Wrapped in try-except, returns None on failure

7. **Ollama/Lumina process discovery** - May not find processes
   - Test: Processes not running
   - Verification: Should log warning and continue

8. **Delta calculations** - Division by zero, missing last_sample
   - Test: First sample (no previous), zero time delta
   - Verification: Should handle gracefully (return 0.0)

### Category 3: Database Errors (Medium Risk)
9. **Research DB write failure** - Could lose samples
   - Test: DB locked, disk full, permission denied
   - Verification: Should log error, retry, fallback to JSONL (TODO)

10. **Batching queue overflow** - Could cause memory leak
    - Test: Rapid sampling, never flush
    - Verification: Queue has maxlen limit

11. **JSON serialization errors** - throttle_reasons, cpu_per_core
    - Test: Insert lists into DB
    - Verification: json.dumps() used for lists

### Category 4: Correlation Errors (Medium Risk)
12. **Emotion-hardware timing mismatch** - >50ms delta = POOR quality
    - Test: Emotion with no recent hardware samples
    - Verification: Should return None if no match

13. **Buffer overflow** - Correlation buffers grow unbounded
    - Test: Long-running daemon
    - Verification: deque(maxlen=100) used

### Category 5: Performance Errors (Low Risk)
14. **CPU overhead too high** - >5% target
    - Test: Monitor CPU usage at 250ms sampling
    - Verification: Adaptive sampling (1000ms if idle)

15. **Memory leak** - Sample buffers grow unbounded
    - Test: Long-running daemon
    - Verification: All buffers have maxlen

### Category 6: Thread Safety Errors (Low Risk)
16. **Race conditions** - 5 concurrent threads
    - Test: Simultaneous writes to shared data
    - Verification: Research DB uses WAL mode

17. **Thread not stopping** - Daemon hangs on shutdown
    - Test: Ctrl+C, daemon.stop()
    - Verification: All threads are daemon=True

### Category 7: Configuration Errors (Low Risk)
18. **Invalid config values** - Negative sampling rates, etc.
    - Test: Malformed config
    - Verification: Defaults used if config missing

### Category 8: Edge Cases (Lowest Risk)
19. **GPU metrics not available** - Some GPUs don't support all metrics
    - Test: Encoder/decoder util, memory temp
    - Verification: Wrapped in try-except, returns 0.0

20. **Voltage unavailable** - pynvml doesn't expose voltage directly
    - Test: Call VoltageTracker.track()
    - Verification: Documented as placeholder, returns zeros

---

## 5. TOOLS SELECTED FOR BUG HUNT

### Testing Tools:
| Tool | Purpose | Phase |
|------|---------|-------|
| **pytest** | Unit/integration test framework | All phases |
| **unittest.mock** | Mock pynvml, psutil, Phase 2 | Unit tests |
| **TestRunner** | Execute test suite | Verification |
| **ErrorRecovery** | Test error handling paths | Edge cases |
| **LiveAudit** | Verify logging | Integration |
| **ProcessWatcher** | Verify process discovery | RAM monitor |
| **BuildEnvValidator** | Verify pynvml installed | Pre-test |
| **DependencyScanner** | Check for conflicts | Pre-test |
| **CodeMetrics** | Code quality | Post-test |

### Debugging Tools:
| Tool | Purpose | Phase |
|------|---------|-------|
| **LogHunter** | Analyze error logs | Investigation |
| **DevSnapshot** | Capture env state | Pre-test |
| **ConversationAuditor** | Verify metrics | Validation |

---

## 6. TEST STRATEGY (MANDATORY 100% COVERAGE)

### Test Categories (Planned Tests: 50+)

#### **Category 1: Unit Tests (25 tests)**
1. GPUMonitor initialization (with/without pynvml)
2. GPUMonitor sample (25 metrics verified)
3. GPUMonitor delta calculations (vram, temp, voltage)
4. GPUMonitor cleanup
5. RAMMonitor initialization
6. RAMMonitor sample (27 metrics verified)
7. RAMMonitor process discovery (found/not found)
8. RAMMonitor delta calculations (ram, I/O, context switches)
9. VoltageTracker track (placeholder returns zeros)
10. EmotionCorrelator add_hardware_sample
11. EmotionCorrelator correlate (EXCELLENT/GOOD/POOR quality)
12. EmotionCorrelator correlate (no match returns None)
13. ResearchDatabase initialization (tables created)
14. ResearchDatabase add_gpu_sample (queue)
15. ResearchDatabase add_ram_sample (queue)
16. ResearchDatabase add_correlation (queue)
17. ResearchDatabase flush (batch write)
18. HardwareAnalyzer detect_thermal_throttle
19. HardwareAnalyzer detect_power_limit
20. HardwareAnalyzer detect_memory_pressure
21. HardwareSoulConfig defaults
22. HardwareSoulConfig get with fallback
23. Phase 3 version number
24. GPUMonitor error handling (pynvml exceptions)
25. RAMMonitor error handling (psutil exceptions)

#### **Category 2: Integration Tests (10 tests)**
26. HardwareSoulDaemon initialization (all components)
27. HardwareSoulDaemon start (all threads launch)
28. HardwareSoulDaemon GPU loop (sample + DB write)
29. HardwareSoulDaemon RAM loop (sample + DB write)
30. HardwareSoulDaemon correlation engine
31. HardwareSoulDaemon research DB flush
32. Phase 2 inheritance (super().start() called)
33. Phase 1 inheritance (OllamaGuard still works)
34. End-to-end: Emotion → Correlation → DB write
35. Multi-thread coordination (no deadlocks)

#### **Category 3: Edge Cases (8 tests)**
36. GPU not available (NVIDIA drivers missing)
37. pynvml import failure (module not installed)
38. Ollama process not found
39. Lumina process not found
40. Research DB write failure (disk full)
41. Zero time delta (first sample)
42. Encoder/decoder util not supported
43. Memory temp not supported

#### **Category 4: Performance Tests (4 tests)**
44. CPU overhead at 250ms sampling (<5%)
45. CPU overhead at 1000ms sampling (<1%)
46. Memory usage stable (no leak after 1000 samples)
47. Adaptive sampling switches (active → idle)

#### **Category 5: Regression Tests (3 tests)**
48. Phase 1 tests still pass (72 tests)
49. Phase 2 tests still pass (36 tests)
50. No Phase 2 functionality broken

**Total Planned Tests: 50 (20 unit + 10 integration + 8 edge + 4 performance + 8 regression)**

---

## 7. VERIFICATION METHOD

### For Each Test Category:

| Category | Verification Method | Pass Criteria |
|----------|---------------------|---------------|
| **Unit Tests** | pytest with mocks | 100% pass, all assertions green |
| **Integration Tests** | Real daemon launch | No exceptions, logs clean |
| **Edge Cases** | Forced failure conditions | Graceful degradation, no crashes |
| **Performance Tests** | psutil CPU/memory monitoring | <5% CPU, <100MB RAM |
| **Regression Tests** | Re-run Phase 1 & 2 test suites | All 108 tests still pass |

### Per-Test Verification Checklist:
- [ ] Test executes without exceptions
- [ ] All assertions pass
- [ ] Expected behavior matches actual
- [ ] Error paths tested (not just happy path)
- [ ] Logs contain expected messages
- [ ] No side effects (DB cleanup, thread cleanup)

---

## 8. SUCCESS CRITERIA (MANDATORY)

### Phase 3 is ready for deployment ONLY IF:
- [ ] **All 50+ Phase 3 tests pass** (100%)
- [ ] **All 72 Phase 1 tests still pass** (no regression)
- [ ] **All 36 Phase 2 tests still pass** (no regression)
- [ ] **Zero CRITICAL bugs** (system-breaking)
- [ ] **Zero HIGH bugs** (feature-breaking)
- [ ] **All bugs fixed and verified**
- [ ] **Bug Hunt Report complete**
- [ ] **Tool requests submitted** (if gaps found)
- [ ] **ABL lessons documented**
- [ ] **ABIOS improvements documented**

---

## 9. EXPECTED BUG CATEGORIES (PROACTIVE)

Based on Phase 1 & 2 experience, expect:

| Bug Type | Likelihood | Example |
|----------|------------|---------|
| **Import Errors** | HIGH | pynvml not installed → crash |
| **Attribute Errors** | MEDIUM | self.gpu_monitor.handle before init |
| **Type Errors** | MEDIUM | Passing string where int expected |
| **Division by Zero** | MEDIUM | Delta calc with zero time |
| **Process Not Found** | HIGH | Ollama/Lumina not running |
| **DB Write Failure** | LOW | Disk full, permission denied |
| **Thread Hanging** | LOW | Daemon doesn't stop cleanly |

---

## 10. TOOLSENTINEL VALIDATION

**Tools Recommended:** (from Phase 2 audit)

```
PRIMARY: ProcessWatcher (process discovery)
SECONDARY: ErrorRecovery (error handling)
TESTING: pytest, unittest.mock, TestRunner
VALIDATION: BuildEnvValidator, DependencyScanner
```

---

✅ **100% Search Coverage Plan COMPLETE**

**Next:** Phase 5 Test Suite Implementation (50+ tests)

---

**Coverage Plan by:** ATLAS (C_Atlas)  
**Date:** February 14, 2026  
**Estimated Testing Time:** 2-3 hours (50+ tests + verification)

*"Test everything. Trust nothing. Verify always."* 🔬⚛️
