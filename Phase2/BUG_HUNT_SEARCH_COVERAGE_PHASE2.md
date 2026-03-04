# Bug Hunt Search Coverage Plan: InferencePulse Phase 2

**Date:** February 13, 2026  
**Builder:** ATLAS (C_Atlas)  
**Protocol:** Bug Hunt Protocol (100% MANDATORY)  
**Phase:** Phase 2 - InferencePulse Testing

---

## 100% SEARCH COVERAGE PLAN

### What Are We Testing?

**Phase 2 InferencePulse** extends Phase 1 (OllamaGuard) with:
1. **ChatResponseHook** - Log file monitoring for Lumina chat responses
2. **MoodAnalyzer** - Emotional texture extraction from responses
3. **BaselineLearner** - Performance baseline calculation from historical data
4. **AnomalyDetector** - Deviation detection vs baselines
5. **UKEConnector** - Batched event indexing to UKE database
6. **EnhancedHeartbeatEmitter** - Extended metrics to AgentHeartbeat
7. **InferencePulseDaemon** - Orchestrator extending Phase 1

### Where Could Bugs Hide?

**Critical Areas (Must Test 100%):**
- [ ] Phase 1 regression (all 72 Phase 1 tests must still pass)
- [ ] Chat hook log file parsing (malformed logs, missing files)
- [ ] Mood analysis failures (timeouts, crashes, unknown moods)
- [ ] Baseline calculation errors (insufficient data, division by zero, edge cases)
- [ ] Anomaly detection false positives/negatives (threshold tuning, edge cases)
- [ ] UKE database operations (connection failures, batch writes, fallback)
- [ ] Enhanced heartbeat emission (schema changes, null values)
- [ ] Thread safety (Phase 1 + Phase 2 running concurrently)
- [ ] Configuration validation (missing sections, invalid values)
- [ ] Error recovery (graceful degradation when Phase 2 features fail)

---

## CATEGORY 1: PHASE 1 REGRESSION TESTS

**Philosophy:** Phase 2 must NOT break Phase 1

### Tests to Run:
1. **All 72 Phase 1 tests** (from `test_ollamaguard.py`)
   - Expected: 100% pass rate
   - If ANY fail: CRITICAL regression, must fix before proceeding

---

## CATEGORY 2: CHAT RESPONSE HOOK TESTS

**Philosophy:** Log parsing is fragile, expect malformed data

### Unit Tests (5 tests):
1. `test_chat_hook_parse_valid_log_line` - Parse well-formed log line
2. `test_chat_hook_parse_missing_fields` - Handle incomplete log lines
3. `test_chat_hook_log_file_not_found` - Handle missing log file gracefully
4. `test_chat_hook_queue_operations` - Queue thread safety
5. `test_chat_hook_stop_monitoring` - Clean shutdown

### Edge Cases:
- Empty log file
- Very large log file (>1GB)
- Log file with unicode/emoji
- Log lines with malformed JSON
- Rapid log rotation during monitoring

---

## CATEGORY 3: MOOD ANALYZER TESTS

**Philosophy:** External tool integration, expect failures

### Unit Tests (6 tests):
1. `test_mood_analyzer_simple_text` - Analyze basic mood
2. `test_mood_analyzer_empty_text` - Handle empty input
3. `test_mood_analyzer_very_long_text` - Handle >10k characters
4. `test_mood_analyzer_timeout` - Respect timeout config
5. `test_mood_analyzer_disabled` - Skip when disabled
6. `test_mood_analyzer_exception_handling` - Return UNKNOWN on crash

### Edge Cases:
- Text with only emojis
- Text in non-English languages
- Text with special characters (&lt;>&")
- Null/None text input

---

## CATEGORY 4: BASELINE LEARNER TESTS

**Philosophy:** Statistics can fail spectacularly with edge cases

### Unit Tests (8 tests):
1. `test_baseline_learner_insufficient_data` - Handle N < min_samples
2. `test_baseline_learner_calculate_baseline_valid` - Correct statistics
3. `test_baseline_learner_division_by_zero` - Handle all-zero values
4. `test_baseline_learner_single_value` - Handle N=1 (std_dev=0)
5. `test_baseline_learner_outliers` - Robust to extreme values
6. `test_baseline_learner_update_interval` - Periodic updates work
7. `test_baseline_learner_db_connection_failure` - Handle DB errors
8. `test_baseline_learner_empty_result_set` - Handle no historical data

### Edge Cases:
- All values identical (std_dev = 0)
- All values negative
- Values with extreme range (0.001 to 1000000)
- Corrupted database
- Missing AgentHeartbeat table

---

## CATEGORY 5: ANOMALY DETECTOR TESTS

**Philosophy:** False positives are costly, false negatives are dangerous

### Unit Tests (10 tests):
1. `test_anomaly_detector_no_baseline` - Skip detection when no baseline
2. `test_anomaly_detector_high_latency` - Detect latency spike
3. `test_anomaly_detector_low_tokens` - Detect token rate drop
4. `test_anomaly_detector_high_vram` - Detect VRAM pressure
5. `test_anomaly_detector_threshold_tuning` - Respect multiplier config
6. `test_anomaly_detector_severity_calculation` - Correct severity levels
7. `test_anomaly_detector_multiple_anomalies` - Handle concurrent anomalies
8. `test_anomaly_detector_disabled` - Skip when disabled
9. `test_anomaly_detector_false_positive_rate` - Validate <5% false positives
10. `test_anomaly_detector_edge_case_zero_baseline` - Handle zero baseline

### Edge Cases:
- Current value exactly at threshold
- Negative current values
- Baseline mean = 0
- Current value = baseline (no deviation)

---

## CATEGORY 6: UKE CONNECTOR TESTS

**Philosophy:** Database writes can fail, must have fallback

### Unit Tests (8 tests):
1. `test_uke_connector_batch_write_success` - Write batch to UKE
2. `test_uke_connector_batch_size_trigger` - Flush at batch size
3. `test_uke_connector_batch_timeout_trigger` - Flush at timeout
4. `test_uke_connector_db_not_found` - Fallback to JSONL file
5. `test_uke_connector_db_write_failure` - Fallback to JSONL file
6. `test_uke_connector_fallback_file_write` - Verify fallback works
7. `test_uke_connector_table_creation` - Create table if not exists
8. `test_uke_connector_disabled` - Skip when disabled

### Edge Cases:
- UKE database locked by another process
- Disk full (fallback fails)
- Very large event payload (>1MB)
- Rapid-fire events (>100/second)

---

## CATEGORY 7: ENHANCED HEARTBEAT EMITTER TESTS

**Philosophy:** Schema changes can break AgentHeartbeat integration

### Unit Tests (5 tests):
1. `test_enhanced_heartbeat_emit_with_chat_metrics` - Full emission
2. `test_enhanced_heartbeat_missing_chat_data` - Handle null chat data
3. `test_enhanced_heartbeat_missing_mood_data` - Handle null mood data
4. `test_enhanced_heartbeat_anomaly_count_daily_reset` - Reset at midnight
5. `test_enhanced_heartbeat_baseline_confidence_calculation` - Correct average

### Edge Cases:
- All metrics null
- Negative values
- Infinity/NaN values
- Missing baselines

---

## CATEGORY 8: INFERENCEPULSE DAEMON TESTS

**Philosophy:** Integration is where everything breaks

### Integration Tests (10 tests):
1. `test_daemon_phase1_thread_starts` - Phase 1 runs in thread
2. `test_daemon_phase2_loop_starts` - Phase 2 loop runs
3. `test_daemon_chat_response_end_to_end` - Full chat processing
4. `test_daemon_baseline_update_periodic` - Baselines update on schedule
5. `test_daemon_graceful_shutdown` - Stop cleanly
6. `test_daemon_phase1_phase2_concurrent` - No race conditions
7. `test_daemon_config_loading` - Load Phase 2 config correctly
8. `test_daemon_phase2_disabled` - Phase 1 only when disabled
9. `test_daemon_heartbeat_emission_rate` - Not overwhelming AgentHeartbeat
10. `test_daemon_error_recovery_phase2_failure` - Phase 1 continues on Phase 2 crash

### Edge Cases:
- Start/stop/start cycle
- Multiple daemons running (should error or coordinate)
- Config file missing
- All Phase 2 features disabled

---

## CATEGORY 9: TOOL INTEGRATION TESTS

**Philosophy:** External tools can disappear or change APIs

### Tool Integration Tests (4 tests):
1. `test_tool_emotionaltextureanalyzer_available` - Verify tool exists
2. `test_tool_agentheartbeat_schema_compatible` - Schema supports Phase 2 metrics
3. `test_tool_uke_db_accessible` - UKE database path valid
4. `test_tool_taskqueuepro_available` - TaskQueuePro importable (future)

---

## CATEGORY 10: PERFORMANCE TESTS

**Philosophy:** Phase 2 must NOT degrade Phase 1 performance

### Performance Tests (5 tests):
1. `test_performance_chat_hook_overhead` - Overhead <50ms
2. `test_performance_mood_analysis_timeout` - Respects 5s timeout
3. `test_performance_baseline_calculation` - Calculates in <2s
4. `test_performance_anomaly_detection` - Detects in <100ms
5. `test_performance_uke_batch_write` - Writes in <500ms

### Benchmarks:
- Phase 1 check cycle: <100ms (baseline)
- Phase 2 chat processing: <200ms total overhead
- Memory: <60MB total (Phase 1 + Phase 2)
- CPU idle: <0.5%

---

## TOTAL TEST PLAN

**Test Categories:**
1. Phase 1 Regression: 72 tests (MUST PASS 100%)
2. Chat Response Hook: 5 unit + 5 edge = 10 tests
3. Mood Analyzer: 6 unit + 4 edge = 10 tests
4. Baseline Learner: 8 unit + 5 edge = 13 tests
5. Anomaly Detector: 10 unit + 4 edge = 14 tests
6. UKE Connector: 8 unit + 4 edge = 12 tests
7. Enhanced Heartbeat: 5 unit + 4 edge = 9 tests
8. InferencePulse Daemon: 10 integration + 4 edge = 14 tests
9. Tool Integration: 4 tests
10. Performance: 5 tests

**TOTAL PHASE 2 TESTS:** 72 (Phase 1) + 91 (Phase 2) = **163 tests**

**Target Pass Rate:** 100% (with Bug Hunt Protocol root cause analysis for any failures)

---

## BUG HUNT PROTOCOL RULES

### Root Cause Analysis (MANDATORY)
For EVERY failing test:
1. **Symptom:** What failed? (assertion, exception, timeout)
2. **Root Cause:** Why did it fail? (not "it crashed", but "division by zero on line X because baseline_mean=0 when...")
3. **Fix:** Precise code change to address root cause
4. **Verification:** Re-run test, confirm fix

### Severity Levels
- **CRITICAL:** Phase 1 regression, data loss, crash
- **HIGH:** Incorrect metrics, missed anomalies, UKE write failure
- **MEDIUM:** Poor error messages, performance regression >20%
- **LOW:** Edge case handling, cosmetic issues

---

✅ **Bug Hunt Search Coverage Plan: COMPLETE**

**Next:** Execute test suite, document bugs in BUG_HUNT_REPORT_PHASE2.md

---

**Prepared by:** ATLAS (C_Atlas)  
**Date:** February 13, 2026  
**Protocol:** Bug Hunt Protocol - 100% Compliance

*Root causes, not symptoms. Always.* 🔬⚛️
