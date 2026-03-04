# Build Coverage Plan: VitalHeart Phase 2 - InferencePulse

**Project Name:** VitalHeart Phase 2 - InferencePulse (AgentHeartbeat Integration)  
**Builder:** ATLAS (C_Atlas, Cursor IDE)  
**Date:** February 13, 2026  
**Estimated Complexity:** Tier 2: Moderate  
**Protocol:** BUILD_PROTOCOL_V1.md (100% Compliance MANDATORY)

---

## 1. Project Scope

### Primary Function
InferencePulse extends OllamaGuard (Phase 1) with real-time AgentHeartbeat integration that triggers during Lumina's chat responses. It captures inference health metrics tied to actual conversations, enabling anomaly detection and baseline learning from real-world usage patterns.

**Core Features:**
1. **Chat Response Hook**: Intercept Lumina's `/chat` endpoint to trigger heartbeat emission after each response
2. **Enhanced Metrics**: Add conversation-specific metrics (chat_response_ms, tokens_generated, mood from EmotionalTextureAnalyzer)
3. **Baseline Learning**: Build normal performance profiles for inference latency, token rate, VRAM usage
4. **Anomaly Detection**: Alert when metrics deviate significantly from learned baselines
5. **UKE Knowledge Indexing**: Full implementation of knowledge sync to UKE database
6. **Real-Time Dashboard Data**: Expose current metrics via API for future HeartWidget consumption

### Secondary Functions
- Historical metric analysis (trends over time)
- Predictive VRAM warning (alert before eviction occurs)
- Model reload frequency tracking (detect hardware/driver issues)
- Conversation context correlation (which types of conversations stress Ollama more)
- Integration test mode (verify chat → heartbeat flow)
- Export metrics to research database for Phase 2.5 (HardwareSoul)

### Out of Scope (for Phase 2)
- ❌ GPU/RAM/Voltage monitoring (that's Phase 3: HardwareSoul)
- ❌ Token-by-token analytics (that's Phase 4)
- ❌ 3D heart visualization (that's Phase 5: HeartWidget - IRIS builds)
- ❌ Emotion-hardware correlation analysis (that's Phase 4)
- ❌ Statistical significance testing (that's Phase 4)

---

## 2. Integration Points

### Existing Systems to Connect

1. **OllamaGuard (Phase 1)** - Already deployed and operational
   - Extend with chat response hooks
   - Reuse configuration system
   - Add to existing heartbeat emission
   - Location: `C:\Users\logan\OneDrive\Documents\AutoProjects\VitalHeart\ollamaguard.py`

2. **Lumina's Chat Server** (`http://localhost:8100/chat`)
   - Hook into chat response generation
   - Capture response timing and token count
   - Extract mood via EmotionalTextureAnalyzer
   - Integration method: Wrapper function or middleware

3. **AgentHeartbeat** (Already integrated in Phase 1)
   - Extend metrics schema with chat-specific fields
   - Add baseline learning module
   - Add anomaly detection module
   - Location: `C:\Users\logan\OneDrive\Documents\AutoProjects\AgentHeartbeat\`

4. **UKE (Unified Knowledge Engine)** (`D:\BEACON_HQ\PROJECTS\00_ACTIVE\UKE\uke.db`)
   - Index all significant events
   - Store conversation-inference correlations
   - Enable searchable audit trail
   - Full implementation (Phase 1 was placeholder)

5. **EmotionalTextureAnalyzer** (`C:\Users\logan\OneDrive\Documents\AutoProjects\EmotionalTextureAnalyzer\`)
   - Extract mood from Lumina's responses
   - 10 emotional dimensions analysis
   - Feed emotional state to heartbeat metrics

### APIs/Protocols Used
- HTTP REST (Lumina chat server)
- HTTP REST (Ollama API via OllamaGuard)
- SQLite (AgentHeartbeat database: `heartbeat.db`)
- SQLite (UKE database: `uke.db`)
- Python function hooks (chat response interception)
- JSON (metrics and configuration)

### Data Formats Handled
- JSON (Lumina chat API, AgentHeartbeat metrics)
- SQLite (AgentHeartbeat + UKE persistence)
- Python dict (internal metrics structures)
- ISO 8601 timestamps (all time references)

---

## 3. Success Criteria

### Criterion 1: Chat Response Triggers Heartbeat
- [ ] Every Lumina chat response triggers InferencePulse heartbeat emission
- [ ] Heartbeat includes: chat_response_ms, tokens_generated, mood (from EmotionalTextureAnalyzer)
- [ ] Response timing captured with millisecond precision
- [ ] Token count extracted from Ollama response
- [ ] Mood analysis runs without blocking chat response
- **Measurable:** 100% of chat responses recorded in AgentHeartbeat with complete metrics

### Criterion 2: Baseline Learning Operational
- [ ] After 100+ chat responses, baseline profiles established for: inference latency, token rate, VRAM usage
- [ ] Baselines calculated: mean, median, std_dev, percentile_5, percentile_95
- [ ] Baselines stored in AgentHeartbeat custom table
- [ ] Baselines updated incrementally with new data (rolling window)
- **Measurable:** Baselines available and accurate after 100 chat responses

### Criterion 3: Anomaly Detection Functional
- [ ] Detects when inference latency >2x baseline mean
- [ ] Detects when token rate <50% baseline mean
- [ ] Detects when VRAM usage approaches capacity (>90%)
- [ ] Alerts logged to LiveAudit
- [ ] No false positives during first 100 responses (baseline building)
- **Measurable:** Anomalies detected within 1 check cycle, <5% false positive rate

### Criterion 4: UKE Knowledge Indexing Complete
- [ ] All significant events indexed to UKE database
- [ ] Events searchable via UKE MCP server
- [ ] Tags applied for categorization (ollama, lumina, inference, anomaly)
- [ ] Event types: chat_response, anomaly_detected, baseline_updated, model_reload
- **Measurable:** 100% of significant events in uke.db, searchable via UKE

### Criterion 5: Integration with OllamaGuard Seamless
- [ ] InferencePulse extends OllamaGuard without breaking existing functionality
- [ ] All Phase 1 tests still passing (72/72)
- [ ] New functionality additive (can be enabled/disabled via config)
- [ ] No performance degradation to OllamaGuard's 60s check cycle
- **Measurable:** Phase 1 tests pass, Phase 2 adds 50+ new tests

---

## 4. Risk Assessment

### Risk 1: Chat Response Latency Increase
**Probability:** Medium  
**Impact:** High  
**Description:** Adding heartbeat emission + mood analysis to each chat response could add latency, making Lumina feel slower to users.

**Mitigation Strategies:**
- Run heartbeat emission asynchronously (non-blocking)
- Use threading or asyncio for parallel execution
- EmotionalTextureAnalyzer call should be async
- Target overhead: <50ms per response (imperceptible to user)
- If overhead >100ms, make heartbeat optional via config
- Performance test with 100 rapid-fire chat requests

### Risk 2: Baseline Learning Instability
**Probability:** Medium  
**Impact:** Medium  
**Description:** Early baselines (N<100) may be inaccurate, causing false anomaly alerts or missed real issues.

**Mitigation Strategies:**
- Suppress anomaly alerts until N>=100 samples (Discovery Mode)
- Use robust statistics (median, IQR) not just mean/std_dev
- Confidence score for baselines increases with sample size
- Baselines update incrementally (rolling window, not fixed)
- Manual review of first 100 samples to validate baseline quality
- Flag low-confidence baselines in logs

### Risk 3: UKE Database Contention
**Probability:** Low  
**Impact:** Low  
**Description:** High-frequency writes to uke.db (every chat response) could cause SQLite lock contention or performance issues.

**Mitigation Strategies:**
- Use WAL mode for concurrent access
- Batch UKE writes (every 10 events or 60 seconds)
- Implement write queue with async worker
- If UKE write fails, log to fallback file
- Don't block heartbeat emission on UKE success
- Performance test: 100 rapid writes to verify no contention

### Risk 4: EmotionalTextureAnalyzer Integration Failure
**Probability:** Low  
**Impact:** Medium  
**Description:** EmotionalTextureAnalyzer may fail on certain text inputs, causing heartbeat emission to fail.

**Mitigation Strategies:**
- Wrap EmotionalTextureAnalyzer in try-except
- Use "UNKNOWN" mood if analysis fails
- Log analysis failures to LiveAudit
- Don't block heartbeat on mood analysis failure
- Test with edge cases: empty text, special characters, very long text

### Risk 5: Phase 1 Regression
**Probability:** Low  
**Impact:** High  
**Description:** Extending OllamaGuard could break existing Phase 1 functionality.

**Mitigation Strategies:**
- Run Phase 1 test suite after Phase 2 changes
- Phase 2 features configurable (can be disabled)
- Extend via inheritance or composition, not modification
- Separate config sections for Phase 1 vs Phase 2
- Integration tests verify both phases work together
- Keep OllamaGuard backward compatible

---

## 5. Architecture Approach

### Integration Strategy: Extension Pattern

**Option 1: Extend OllamaGuard Class (CHOSEN)**
```python
# Phase 1 (existing)
class OllamaGuardDaemon:
    # ... existing functionality ...

# Phase 2 (extension)
class InferencePulseDaemon(OllamaGuardDaemon):
    # Inherits all Phase 1 functionality
    # Adds chat response hooks
    # Adds baseline learning
    # Adds anomaly detection
```

**Why:** Clean separation, backward compatibility, Phase 1 remains untouched

**Option 2: Separate Daemon (REJECTED)**
- Cons: Duplicate code, two processes to manage, coordination complexity
- Pros: Complete separation, but not worth the overhead

### Key Components to Build

1. **ChatResponseHook**: Intercept Lumina chat responses, capture timing/tokens
2. **BaselineLearner**: Build and update performance baselines from metrics
3. **AnomalyDetector**: Compare current metrics to baselines, flag deviations
4. **UKEConnector**: Full implementation of knowledge indexing to UKE
5. **EnhancedHeartbeatEmitter**: Extends Phase 1 emitter with chat metrics
6. **MetricsAggregator**: Aggregate and analyze historical metrics

---

## 6. Configuration Extensions

### New Config Section: `inferencepulse`

```json
{
  "inferencepulse": {
    "enabled": true,
    "chat_hook_enabled": true,
    "lumina_chat_url": "http://localhost:8100/chat",
    "baseline_learning_enabled": true,
    "baseline_min_samples": 100,
    "anomaly_detection_enabled": true,
    "anomaly_threshold_multiplier": 2.0,
    "mood_analysis_enabled": true,
    "mood_analysis_timeout_seconds": 5
  },
  "uke": {
    "enabled": true,
    "db_path": "D:/BEACON_HQ/PROJECTS/00_ACTIVE/UKE/uke.db",
    "batch_size": 10,
    "batch_timeout_seconds": 60,
    "event_types": ["chat_response", "anomaly_detected", "baseline_updated"]
  }
}
```

---

## 7. Success Metrics

### Phase 2 Acceptance Criteria
- ✅ All Phase 1 tests still passing (72/72)
- ✅ Phase 2 tests passing (50+ new tests)
- ✅ Chat responses trigger heartbeats (100% capture rate)
- ✅ Baselines established after 100 samples
- ✅ Anomalies detected correctly (<5% false positives)
- ✅ UKE indexing operational (100% event capture)
- ✅ Performance overhead <50ms per chat response
- ✅ Documentation complete (400+ lines README)
- ✅ Examples comprehensive (10+ examples)
- ✅ All 6 quality gates passed

---

## 8. Testing Strategy

### Test Categories (Bug Hunt Protocol Compliance)
- **Unit Tests:** 15+ (BaselineLearner, AnomalyDetector, UKEConnector, ChatHook)
- **Integration Tests:** 10+ (Chat→Heartbeat, Baseline→Anomaly, UKE indexing, Phase 1+2 together)
- **Edge Case Tests:** 10+ (Empty responses, analysis failures, database errors, rapid requests)
- **Tool Integration Tests:** 1 per new tool used
- **Performance Tests:** 5+ (Chat latency, UKE write speed, baseline calculation, 100 rapid requests)
- **Regression Tests:** Run full Phase 1 suite to verify no breakage

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
**Date:** February 13, 2026  
**Protocol Compliance:** BUILD_PROTOCOL_V1.md - 100%

*Quality is not an act, it is a habit!* ⚛️⚔️
