# Bug Hunt Search Coverage Plan - VitalHeart Phase 4: Token Analytics

**Target:** VitalHeart Phase 4 - Token Analytics (tokenanalytics.py)  
**Date:** February 14, 2026  
**Hunter:** ATLAS (C_Atlas)  
**Protocol:** Bug Hunt Protocol (100% MANDATORY)

---

## 1. SCOPE DEFINITION

### Files in Scope
1. `tokenanalytics.py` (1,083 lines) - Main production code
2. `requirements.txt` (4 lines) - Dependencies
3. Phase 3 integration: `../Phase3/hardwaresoul.py` (inheritance)

### Systems in Scope
- Token stream capture (Ollama streaming API)
- Token timing analysis (microsecond precision)
- Pause detection (>500ms threshold)
- Generation curve tracking (accelerating/decelerating)
- Emotion-token correlation (nearest-neighbor)
- Hardware-token correlation (GPU/RAM metrics)
- Baseline learning (EMA updates)
- Anomaly detection (stuttering, freezing, racing)
- Research database (4 tables)

### Out of Scope
- Phase 1-3 functionality (already tested in previous phases)
- Ollama server implementation (external dependency)
- AgentHeartbeat internals (external tool)

---

## 2. ENTRY POINTS

### Where Problems Could Manifest
1. **TokenStreamCapture.capture_stream()** - Streaming API parsing
2. **TokenTimingAnalyzer.analyze()** - Statistical calculations
3. **PauseDetector.detect()** - Threshold detection
4. **GenerationCurveTracker.track()** - Sliding window analysis
5. **EmotionTokenCorrelator.correlate()** - Nearest-neighbor matching
6. **HardwareTokenCorrelator.correlate()** - Hardware metric pairing
7. **BaselineLearner.update()** - EMA calculation
8. **AnomalyDetector.detect()** - Threshold-based detection
9. **TokenAnalyticsDatabase** - SQLite writes/queries
10. **TokenAnalyticsDaemon.analyze_prompt()** - Main orchestration

### What Triggers Problems
- Malformed JSON from Ollama (streaming API)
- Empty token streams (no response)
- Timeout conditions (60s stream timeout)
- Division by zero (total_duration_ms = 0)
- Empty buffers (no emotion/hardware samples for correlation)
- Database write failures (disk full, permissions)
- Phase 3 import failure (HardwareSoul not available)

---

## 3. DEPENDENCY CHAIN

### Call Hierarchy
```
TokenAnalyticsDaemon.analyze_prompt()
  ├── TokenStreamCapture.capture_stream()
  │     ├── requests.post() [EXTERNAL]
  │     ├── json.loads() [STDLIB]
  │     └── time.time() [STDLIB]
  ├── TokenTimingAnalyzer.analyze()
  │     ├── statistics.mean() [STDLIB]
  │     └── _detect_curve()
  ├── PauseDetector.detect()
  ├── GenerationCurveTracker.track()
  │     └── _detect_curve_segment()
  ├── EmotionTokenCorrelator.correlate()
  │     └── BaselineLearner.get_baseline()
  ├── HardwareTokenCorrelator.correlate()
  │     ├── HardwareSoul.gpu_monitor.sample() [PHASE 3]
  │     ├── HardwareSoul.ram_monitor.sample() [PHASE 3]
  │     └── BaselineLearner.get_baseline()
  ├── BaselineLearner.update()
  │     └── _save_baseline()
  ├── AnomalyDetector.detect()
  └── TokenAnalyticsDatabase.store_*()
        ├── _flush_token_buffer()
        ├── _flush_emotion_buffer()
        └── _flush_hardware_buffer()
```

### External Dependencies
- **requests**: HTTP streaming
- **sqlite3**: Database operations
- **Phase 3 (hardwaresoul.py)**: HardwareSoulDaemon inheritance
- **Ollama API**: Token stream source

---

## 4. SEARCH ORDER (Most Likely → Least Likely)

### Priority 1: Token Stream Capture (HIGH RISK)
1. **Malformed JSON handling** - Streaming API can return incomplete JSON
2. **Timeout handling** - 60s timeout must work correctly
3. **Connection errors** - Network failures must be handled
4. **Empty streams** - Zero tokens must not crash
5. **Unicode tokens** - Emoji, special characters in tokens

### Priority 2: Statistical Calculations (MEDIUM RISK)
1. **Division by zero** - total_duration_ms = 0, baseline_rate = 0
2. **Empty lists** - min/max/percentile on empty latency list
3. **Insufficient data** - <10 tokens for curve detection
4. **Percentile calculation** - Edge case with small sample size

### Priority 3: Correlation Logic (MEDIUM RISK)
1. **Empty buffers** - No emotion/hardware samples available
2. **Timestamp alignment** - Microsecond precision drift
3. **Baseline not found** - New emotion state with no baseline
4. **Quality tier calculation** - Edge case time deltas

### Priority 4: Baseline Learning (LOW RISK)
1. **Database corruption** - Baseline table corrupted
2. **Concurrent writes** - Multiple updates to same baseline
3. **EMA calculation** - Alpha value edge cases (sample_count = 0)

### Priority 5: Database Operations (MEDIUM RISK)
1. **Buffer overflow** - >10000 tokens queued
2. **Write failures** - Disk full, permissions
3. **SQLite locking** - WAL mode contention
4. **Schema mismatch** - Table structure changes

---

## 5. TOOLS SELECTED

### Bug Hunt Tools
- **TestRunner**: Execute pytest suite
- **CodeMetrics**: Performance profiling
- **ErrorRecovery**: Exception testing
- **QuickBackup**: Database backup before destructive tests
- **HashGuard**: Database integrity verification
- **LiveAudit**: Log test events
- **CheckerAccountability**: Verify test accuracy

### Testing Strategy
- **pytest**: Unit/integration tests
- **unittest.mock**: Mock Ollama API, Phase 3 components
- **sqlite3**: Database testing
- **requests_mock**: Mock HTTP streaming

---

## 6. VERIFICATION METHOD

### Per-Area Verification

| Area | Verification Method | Pass Criteria |
|------|---------------------|---------------|
| Token capture | Mock streaming API, verify token events | All tokens captured with timestamps |
| Timing analysis | Provide known latencies, verify stats | Calculations match expected |
| Pause detection | Test with >500ms latencies | Pauses detected correctly |
| Curve tracking | Test with accelerating/decelerating patterns | Curves classified correctly |
| Emotion correlation | Test with known emotion buffer | Nearest-neighbor matching correct |
| Hardware correlation | Test with known GPU/RAM samples | Bottleneck detection correct |
| Baseline learning | Test EMA with known samples | Baseline converges correctly |
| Anomaly detection | Test with 2x deviation | Anomalies flagged correctly |
| Database ops | Test writes/queries | No data loss, correct retrieval |
| Integration | Test full analyze_prompt() flow | All components work together |

---

## TEST CATEGORIES (40+ TESTS PLANNED)

### Unit Tests (15 tests)
1. `test_config_defaults` - Default configuration loads
2. `test_config_validation` - Invalid config raises errors
3. `test_token_stream_capture_success` - Happy path token capture
4. `test_token_stream_capture_timeout` - 60s timeout works
5. `test_token_stream_capture_malformed_json` - Skips bad JSON
6. `test_timing_analyzer_basic_stats` - Calculates tokens/sec correctly
7. `test_timing_analyzer_percentiles` - p50/p95/p99 correct
8. `test_timing_analyzer_curve_detection` - Detects accelerating/decelerating
9. `test_pause_detector_threshold` - Detects pauses >500ms
10. `test_pause_detector_classification` - micro/short/long correct
11. `test_curve_tracker_sliding_window` - Sliding window works
12. `test_baseline_learner_ema` - EMA calculation correct
13. `test_baseline_learner_confidence` - Confidence tiers correct
14. `test_anomaly_detector_threshold` - Detects >2x deviation
15. `test_database_initialization` - Tables created correctly

### Integration Tests (10 tests)
1. `test_full_analyze_prompt` - Complete analysis flow
2. `test_emotion_correlation_nearest_neighbor` - Finds nearest emotion
3. `test_hardware_correlation_nearest_neighbor` - Finds nearest GPU/RAM
4. `test_baseline_update_flow` - Baseline updates after analysis
5. `test_anomaly_detection_flow` - Anomaly detected and logged
6. `test_database_batch_writes` - Buffered writes work
7. `test_phase3_inheritance` - HardwareSoul methods accessible
8. `test_daemon_start_stop` - Daemon lifecycle
9. `test_buffer_flush_on_stop` - Buffers flushed on shutdown
10. `test_metrics_tracking` - Metrics increment correctly

### Edge Case Tests (10 tests)
1. `test_empty_token_stream` - Zero tokens doesn't crash
2. `test_single_token` - 1 token handled gracefully
3. `test_empty_emotion_buffer` - No emotion samples available
4. `test_empty_hardware_buffer` - No hardware samples available
5. `test_division_by_zero_duration` - total_duration_ms = 0
6. `test_baseline_not_found` - New emotion with no baseline
7. `test_database_write_failure` - Disk full simulation
8. `test_concurrent_database_writes` - WAL mode handles contention
9. `test_phase3_not_available` - Graceful degradation without HardwareSoul
10. `test_unicode_tokens` - Emoji and special characters

### Performance Tests (5 tests)
1. `test_token_capture_overhead` - <1ms per token
2. `test_timing_analysis_performance` - <5ms for 1000 tokens
3. `test_correlation_performance` - <50ms per correlation
4. `test_database_query_performance` - <100ms for 1000 tokens
5. `test_full_analysis_performance` - <200ms total for 100-token session

### Tool Integration Tests (39 tests - PHASE 3 LESSON APPLIED!)
1. `test_tool_configmanager` - ConfigManager integration
2. `test_tool_envmanager` - EnvManager integration
3. `test_tool_envguard` - EnvGuard validation
4. `test_tool_timesync` - TimeSync timestamps
5. `test_tool_errorrecovery` - ErrorRecovery handling
6. `test_tool_liveaudit` - LiveAudit logging
7. `test_tool_versionguard` - VersionGuard checks
8. `test_tool_loghunter` - LogHunter parsing
9. `test_tool_apiprobe` - APIProbe validation
10. `test_tool_portmanager` - PortManager checks
11. `test_tool_agentheartbeat` - AgentHeartbeat metrics
12. `test_tool_processwatcher` - ProcessWatcher monitoring
13. `test_tool_tokentracker` - TokenTracker usage (NEW)
14. `test_tool_dataconvert` - DataConvert export
15. `test_tool_jsonquery` - JSONQuery parsing
16. `test_tool_consciousnessmarker` - ConsciousnessMarker patterns
17. `test_tool_quickbackup` - QuickBackup database
18. `test_tool_hashguard` - HashGuard integrity
19. `test_tool_synapselink` - SynapseLink reports
20. `test_tool_synapsenotify` - SynapseNotify alerts
21. `test_tool_pathbridge` - PathBridge translation
22. `test_tool_knowledgesync` - KnowledgeSync UKE
23. `test_tool_toolregistry` - ToolRegistry discovery
24. `test_tool_toolsentinel` - ToolSentinel validation
25. `test_tool_gitflow` - GitFlow version control
26. `test_tool_regexlab` - RegexLab patterns (NEW)
27. `test_tool_restcli` - RestCLI API calls
28. `test_tool_testrunner` - TestRunner execution
29. `test_tool_buildenvvalidator` - BuildEnvValidator checks
30. `test_tool_dependencyscanner` - DependencyScanner deps
31. `test_tool_devsnapshot` - DevSnapshot state
32. `test_tool_sessiondocgen` - SessionDocGen docs
33. `test_tool_smartnotes` - SmartNotes research
34. `test_tool_postmortem` - PostMortem lessons
35. `test_tool_changelog` - ChangeLog tracking
36. `test_tool_codemetrics` - CodeMetrics quality
37. `test_tool_checkeraccountability` - CheckerAccountability accuracy
38. `test_tool_emotionaltextureanalyzer` - EmotionalTextureAnalyzer emotions
39. `test_tool_aiprompt_vault` - ai-prompt-vault storage

### Regression Tests (3 tests)
1. `test_phase1_inheritance` - OllamaGuard methods accessible
2. `test_phase2_inheritance` - InferencePulse methods accessible
3. `test_phase3_inheritance` - HardwareSoul methods accessible

---

## TOTAL TESTS PLANNED: 82 tests

**Breakdown:**
- Unit Tests: 15
- Integration Tests: 10
- Edge Case Tests: 10
- Performance Tests: 5
- Tool Integration Tests: 39 (PHASE 3 LESSON - 1 per tool!)
- Regression Tests: 3

**With Phases 1-3:** 82 + 146 = 228 total tests across all phases

---

## TEST EXECUTION PLAN

### Phase 1: Unit Tests (30 minutes)
- Test each component individually
- Mock external dependencies (Ollama API, Phase 3 components)
- Verify calculations (tokens/sec, percentiles, EMA)

### Phase 2: Integration Tests (45 minutes)
- Test component interactions
- Test full analyze_prompt() flow
- Test database writes/queries
- Test daemon lifecycle

### Phase 3: Edge Cases (30 minutes)
- Test failure modes (empty streams, no buffers, division by zero)
- Test graceful degradation
- Test error recovery

### Phase 4: Performance Tests (30 minutes)
- Measure overhead per token
- Stress test with 1000-token streams
- Verify performance targets met

### Phase 5: Tool Integration Tests (2 hours)
- Test each of 39 tools
- Verify integration points
- Document tool usage

### Phase 6: Regression Tests (15 minutes)
- Verify Phase 1-3 inheritance intact
- Run Phase 3 tests to verify no breakage

**Total Estimated Time:** 4.5 hours

---

## VERIFICATION CHECKLIST

- [ ] All 82 tests written
- [ ] All tests passing (100% pass rate)
- [ ] No bare `except:` clauses (Phase 3 lesson)
- [ ] All exceptions logged (Phase 3 lesson)
- [ ] Performance targets met (<5ms per token)
- [ ] Database integrity verified (HashGuard)
- [ ] Phase 3 tests still passing (38/38)
- [ ] Bug Hunt Report created
- [ ] All bugs fixed and verified

---

**Prepared by:** ATLAS (C_Atlas)  
**Date:** February 14, 2026  
**Protocol:** Bug Hunt Protocol (100% MANDATORY)

*"Find every bug before Logan does."* ⚛️🐛
