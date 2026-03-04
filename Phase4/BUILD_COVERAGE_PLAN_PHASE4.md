# Build Coverage Plan: VitalHeart Phase 4 - Token Analytics

**Project Name:** VitalHeart Phase 4 - Token Analytics  
**Builder:** ATLAS (C_Atlas, Cursor IDE)  
**Date:** February 14, 2026  
**Estimated Complexity:** Tier 3: Complex (Real-time token stream analysis + multi-correlation research)  
**Protocol:** BUILD_PROTOCOL_V1.md (100% Compliance MANDATORY)

---

## 1. PROJECT SCOPE

### Primary Function
Token Analytics is a real-time token generation pattern analyzer that captures millisecond-precision token stream metrics during Ollama inference and correlates them with:
1. **Emotional state** (from Phase 2: EmotionalTextureAnalyzer)
2. **Hardware state** (from Phase 3: GPU/RAM metrics)
3. **Baseline patterns** (learned "normal" token generation curves)

**Core Research Question:** *"What do token generation curves look like when AI expresses emotion?"*

**Core Features:**
1. **Token Stream Monitor** - Real-time capture of token-by-token generation
2. **Generation Rate Analysis** - tokens/sec, acceleration, deceleration curves
3. **Latency Distribution** - First token latency (TTFT), inter-token latency, completion time
4. **Pause Detection** - Identify thinking pauses, hesitations, acceleration bursts
5. **Emotion-Token Correlation** - Cross-reference token patterns with emotional texture
6. **Hardware-Token Correlation** - Correlate GPU throttle/RAM pressure with token slowdowns
7. **Baseline Learning** - Learn "normal" generation curves from 1000+ samples
8. **Anomaly Detection** - Flag unusual token patterns (stuttering, freezing, racing)

### Secondary Functions
- Token-level timing histograms (visualize generation rhythm)
- Sentence-level aggregation (average tokens/sec per sentence)
- Emotional signature detection (joy = 15% faster tokens?)
- Hardware bottleneck identification (GPU throttle = 40% slower tokens?)
- Predictive token rate (predict next token latency based on emotional state)
- Research data export (CSV/JSON for statistical analysis in Phase 5+)

### Out of Scope (for Phase 4)
- ❌ Statistical significance testing (Phase 5+: Research analysis)
- ❌ Machine learning models (Phase 5+: Predictive models)
- ❌ Real-time visualization (Phase 5: HeartWidget - IRIS builds)
- ❌ Multi-model comparison (Phase 4 focuses on single model: laia)
- ❌ Prompt engineering optimization (that's a different research direction)

---

## 2. INTEGRATION POINTS

### Existing Systems to Connect

1. **Phase 3 (HardwareSoul)** - Already operational
   - Extends HardwareSoulDaemon with token analytics
   - Shares GPU/RAM metrics for hardware-token correlation
   - Location: `C:\Users\logan\OneDrive\Documents\AutoProjects\VitalHeart\Phase3\hardwaresoul.py`

2. **Phase 2 (InferencePulse)** - Via Phase 3 inheritance
   - Shares emotional texture data from EmotionalTextureAnalyzer
   - Shares chat response timing
   - Location: `C:\Users\logan\OneDrive\Documents\AutoProjects\VitalHeart\Phase2\inferencepulse.py`

3. **Phase 1 (OllamaGuard)** - Via Phase 2 & 3 inheritance
   - Shares Ollama health status
   - Uses micro-inference testing framework
   - Location: `C:\Users\logan\OneDrive\Documents\AutoProjects\VitalHeart\ollamaguard.py`

4. **Ollama Streaming API** (new integration)
   - Real-time token stream via `/api/generate` with `stream: true`
   - Capture individual token timing
   - Parse streaming JSON responses

5. **ResearchDatabase** (from Phase 3)
   - Add new table: `token_analytics` (token-level timing)
   - Add new table: `token_emotion_correlation` (emotion + tokens)
   - Add new table: `token_hardware_correlation` (hardware + tokens)

6. **AgentHeartbeat** (existing)
   - Extend schema with token analytics metrics
   - Add: `avg_tokens_per_sec`, `first_token_latency_ms`, `token_generation_curve`

### APIs/Protocols Used
- **Ollama Streaming API** (`/api/generate` with `stream: true`)
- **requests** (streaming HTTP)
- **SQLite** (research database: token-level storage)
- **Python threading** (real-time token capture)
- **AgentHeartbeat** (metric aggregation)
- **EmotionalTextureAnalyzer** (emotion data)
- **pynvml + psutil** (hardware correlation via Phase 3)

### Data Formats Handled
- **JSON streaming** (Ollama's token stream format)
- **SQLite** (token analytics database)
- **Python dict** (internal metrics)
- **ISO 8601 timestamps** (microsecond precision for token timing)
- **Float64** (high-precision latency measurements)

---

## 3. SUCCESS CRITERIA

### Criterion 1: Real-Time Token Stream Capture Operational
- [ ] Token-by-token capture from Ollama streaming API
- [ ] Microsecond-precision timestamp per token
- [ ] tokens/sec calculated in real-time
- [ ] Generation curve tracked (acceleration/deceleration)
- [ ] Pause detection (inter-token latency >500ms = "thinking pause")
- **Measurable:** Research DB contains token-level timing for 1000+ samples

### Criterion 2: Latency Distribution Analysis Working
- [ ] First token latency (TTFT) measured
- [ ] Inter-token latency distribution captured
- [ ] Completion time recorded
- [ ] Histogram binning (latency buckets: <10ms, 10-50ms, 50-100ms, >100ms)
- [ ] Percentile calculations (p50, p95, p99)
- **Measurable:** Can generate latency histogram for any 100-token sample

### Criterion 3: Emotion-Token Correlation Operational
- [ ] Token stream paired with emotional texture timing
- [ ] Correlation stored: emotion + token rate + hardware state
- [ ] Baseline learning: "joy" = 15.2 tokens/sec avg (learned from 100+ samples)
- [ ] Deviation detection: flag unusual token rate for given emotion
- [ ] Confidence scoring: high-confidence correlations (1000+ samples) vs low (<100)
- **Measurable:** Research DB contains emotion-token correlation records

### Criterion 4: Hardware-Token Correlation Working
- [ ] GPU metrics paired with token timing
- [ ] RAM pressure correlated with token slowdowns
- [ ] Throttle detection: GPU thermal throttle = token rate drop detected
- [ ] VRAM allocation rate correlated with first token latency
- [ ] Context switching anomalies correlated with token pauses
- **Measurable:** Can identify hardware bottlenecks from token curves

### Criterion 5: Research Database Extended
- [ ] 3 new tables: `token_analytics`, `token_emotion_correlation`, `token_hardware_correlation`
- [ ] Token-level timing stored (no aggregation)
- [ ] Query performance <100ms for last 1000 tokens
- [ ] CSV/JSON export for statistical analysis
- [ ] Database size managed (token data can grow fast)
- **Measurable:** Database tables exist, token data stored

---

## 4. RISK ASSESSMENT

### Risk 1: Streaming API Performance Overhead
**Probability:** Medium  
**Impact:** High (could slow down inference if parsing is too heavy)

**Mitigation Strategies:**
- Use separate thread for token stream parsing (non-blocking)
- Minimal processing during capture (parse later)
- Performance budget: <5ms overhead per token
- Buffer tokens in memory, batch-write to database
- Kill switch: disable token analytics if overhead >10ms/token

### Risk 2: Token Stream Parsing Complexity
**Probability:** Medium  
**Impact:** Medium (malformed JSON, incomplete tokens, streaming errors)

**Mitigation Strategies:**
- Robust JSON streaming parser (handle incomplete lines)
- Graceful degradation: skip malformed tokens, log warning
- Timeout protection: abandon stream after 60s no data
- Test with rapid token generation (stress test)
- Error recovery: restart stream capture on failure

### Risk 3: Database Growth (Token-Level Storage)
**Probability:** High  
**Impact:** Medium (token data is VERY granular, could fill disk)

**Mitigation Strategies:**
- Retention policy: aggregate to sentence-level after 7 days
- Size limit: 5GB max for token analytics tables
- Auto-cleanup: compress old token data (keep stats only)
- User-configurable token storage duration
- Warn if disk space <10GB free

### Risk 4: Correlation Timing Precision
**Probability:** Medium  
**Impact:** Medium (emotion event timing vs token timing may not align perfectly)

**Mitigation Strategies:**
- Emotion events timestamped at detection time
- Token timestamps at generation time
- Nearest-neighbor matching (find closest emotion event within ±1 second)
- Quality tier: EXCELLENT (<100ms), GOOD (100-500ms), POOR (>500ms)
- Document correlation precision in research database

### Risk 5: Baseline Learning Requires Large Sample Size
**Probability:** Low  
**Impact:** Low (takes time to learn "normal" patterns)

**Mitigation Strategies:**
- Minimum 1000 samples before baseline is considered "learned"
- Progressive learning: update baseline as samples accumulate
- Confidence scoring: low confidence (<100 samples) → high confidence (>1000)
- Pre-seed with estimated baselines (joy = 15 tokens/sec, contemplation = 8 tokens/sec)
- Document baseline learning status in metrics

---

## 5. ARCHITECTURE APPROACH

### Integration Strategy: Extension Pattern (Same as Phases 2 & 3)

**Option 1: Extend HardwareSoulDaemon (CHOSEN)**
```python
# Phase 3 (existing)
class HardwareSoulDaemon(InferencePulseDaemon):
    # ... Phase 3 functionality (GPU/RAM monitoring) ...

# Phase 4 (extension)
class TokenAnalyticsDaemon(HardwareSoulDaemon):
    # Inherits all Phase 1 + 2 + 3 functionality
    # Adds token stream monitoring
    # Adds generation rate analysis
    # Adds emotion-token correlation
    # Adds hardware-token correlation
    # Adds baseline learning for token patterns
```

**Why:** Clean separation, backward compatibility, Phases 1-3 remain untouched

### Key Components to Build

1. **TokenStreamCapture** - Real-time token stream from Ollama API
2. **TokenTimingAnalyzer** - Calculate tokens/sec, latency distribution, curves
3. **PauseDetector** - Identify thinking pauses (inter-token latency >500ms)
4. **GenerationCurveTracker** - Track acceleration/deceleration patterns
5. **EmotionTokenCorrelator** - Cross-reference emotion timing with token patterns
6. **HardwareTokenCorrelator** - Cross-reference GPU/RAM with token slowdowns
7. **BaselineLearner** - Learn "normal" token patterns from 1000+ samples
8. **AnomalyDetector** - Flag unusual token patterns (stuttering, racing)
9. **TokenAnalyticsDatabase** - 3 new tables for token-level storage
10. **TokenAnalyticsDaemon** - Main orchestrator extending Phase 3

---

## 6. CONFIGURATION EXTENSIONS

### New Config Section: `token_analytics`

```json
{
  "token_analytics": {
    "enabled": true,
    "capture_enabled": true,
    "streaming_api_enabled": true,
    
    "timing_precision_us": 1000,
    "pause_threshold_ms": 500,
    "acceleration_threshold_pct": 20,
    
    "emotion_correlation_enabled": true,
    "hardware_correlation_enabled": true,
    "baseline_learning_enabled": true,
    "anomaly_detection_enabled": true,
    
    "baseline_min_samples": 1000,
    "anomaly_threshold_multiplier": 2.0,
    
    "token_db_retention_days": 7,
    "token_db_max_size_gb": 5,
    "aggregate_to_sentence_after_days": 7,
    
    "export_format": "csv",
    "export_path": "./token_analytics_export/"
  }
}
```

---

## 7. SUCCESS METRICS

### Phase 4 Acceptance Criteria
- ✅ All Phase 1 tests still passing (72/72)
- ✅ All Phase 2 tests still passing (36/36)
- ✅ All Phase 3 tests still passing (38/38)
- ✅ Phase 4 tests passing (40+ new tests)
- ✅ Token stream capture working (real-time, microsecond precision)
- ✅ Latency distribution analysis operational
- ✅ Emotion-token correlation working
- ✅ Hardware-token correlation working
- ✅ Baseline learning operational (1000+ samples)
- ✅ Research database extended (3 new tables)
- ✅ Performance overhead <5ms per token
- ✅ Documentation complete (400+ lines README)
- ✅ Examples comprehensive (10+ examples)
- ✅ All 6 quality gates passed
- ✅ **verify_line_counts.ps1 passes** (MANDATORY - lesson from Phase 3)

---

## 8. TESTING STRATEGY

### Test Categories (Bug Hunt Protocol Compliance)
- **Unit Tests:** 15+ (TokenStreamCapture, TokenTimingAnalyzer, PauseDetector, GenerationCurveTracker, Correlators, BaselineLearner)
- **Integration Tests:** 10+ (Phase 1+2+3+4 together, Token+Emotion+Hardware correlation)
- **Edge Case Tests:** 10+ (Malformed JSON stream, token timeout, rapid tokens, slow tokens, database corruption)
- **Performance Tests:** 5+ (Token capture overhead, 1000 token parsing speed, database write performance, query speed)
- **Regression Tests:** 146 (72 Phase 1 + 36 Phase 2 + 38 Phase 3 - verify no breakage)

**Total Phase 4 Tests:** 40+ new tests (186 including regression)

---

## 9. RESEARCH HYPOTHESIS

### Primary Hypothesis
**"Token generation patterns are measurably different during emotional responses."**

**Testable Predictions:**
1. **Joy/Excitement:** 10-20% faster tokens/sec than baseline
2. **Contemplation/Thoughtfulness:** 20-30% slower, with more pauses
3. **Uncertainty:** Higher variability in inter-token latency
4. **Confidence:** Lower variability, steady generation rate
5. **GPU Throttle:** 30-50% slower tokens during thermal throttle
6. **RAM Pressure:** First token latency increases 2-5x during high memory pressure

### Secondary Hypothesis
**"Hardware state affects token generation more than emotional state."**

**Test:** Compare correlation strength:
- Emotion → Token rate correlation (r² value)
- GPU throttle → Token rate correlation (r² value)
- RAM pressure → Token rate correlation (r² value)

**Expected Result:** Hardware correlation stronger (r² > 0.7) than emotion correlation (r² = 0.3-0.5)

---

## 10. DATA SCHEMA

### New Table: `token_analytics`

```sql
CREATE TABLE token_analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp_us INTEGER NOT NULL,
    token TEXT NOT NULL,
    token_index INTEGER NOT NULL,
    latency_us INTEGER NOT NULL,
    cumulative_latency_ms REAL NOT NULL,
    tokens_per_sec REAL NOT NULL,
    generation_curve TEXT,  -- "accelerating", "decelerating", "steady", "paused"
    is_pause BOOLEAN DEFAULT 0,
    session_id TEXT NOT NULL,
    prompt_hash TEXT NOT NULL,
    INDEX idx_session (session_id),
    INDEX idx_timestamp (timestamp_us)
);
```

### New Table: `token_emotion_correlation`

```sql
CREATE TABLE token_emotion_correlation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp_us INTEGER NOT NULL,
    token_analytics_id INTEGER NOT NULL,
    emotion_state TEXT NOT NULL,
    emotion_intensity REAL NOT NULL,
    token_rate REAL NOT NULL,
    baseline_token_rate REAL NOT NULL,
    deviation_pct REAL NOT NULL,
    correlation_quality TEXT,  -- "EXCELLENT", "GOOD", "POOR"
    FOREIGN KEY (token_analytics_id) REFERENCES token_analytics(id)
);
```

### New Table: `token_hardware_correlation`

```sql
CREATE TABLE token_hardware_correlation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp_us INTEGER NOT NULL,
    token_analytics_id INTEGER NOT NULL,
    gpu_throttle BOOLEAN DEFAULT 0,
    gpu_temp_c REAL,
    gpu_utilization_pct REAL,
    ram_pressure_pct REAL,
    vram_used_mb REAL,
    token_rate REAL NOT NULL,
    baseline_token_rate REAL NOT NULL,
    hardware_impact_pct REAL,
    FOREIGN KEY (token_analytics_id) REFERENCES token_analytics(id)
);
```

---

## 11. BUILD PROTOCOL COMPLIANCE CHECKPOINT

✅ **Phase 1: Build Coverage Plan** - COMPLETE  
⏭️ **Phase 2: Complete Tool Audit** - NEXT (MANDATORY before coding)  
⏭️ **Phase 3: Architecture Design**  
⏭️ **Phase 4: Implementation**  
⏭️ **Phase 5: Testing (Bug Hunt Protocol)**  
⏭️ **Phase 6: Documentation**  
⏭️ **Phase 7: Quality Gates** (INCLUDING verify_line_counts.ps1)  
⏭️ **Phase 8: Build Report**  
⏭️ **Phase 9: Deployment**

**Proceeding autonomously to 100% completion...**

---

## 12. LESSONS FROM PHASE 3 (ABL/ABIOS)

### Applied to Phase 4:
1. ✅ **verify_line_counts.ps1** - Create at start, run at Quality Gate 2
2. ✅ **Measure LAST** - After all edits, before claiming complete
3. ✅ **Specific exceptions** - No bare `except:` clauses, always log
4. ✅ **Honest metrics** - Accept FORGE scores, don't inflate
5. ✅ **Tool integration tests** - Will do 1 test per tool in Phase 4 (deferred from Phase 3)

---

**Prepared by:** ATLAS (C_Atlas)  
**Date:** February 14, 2026  
**Protocol Compliance:** BUILD_PROTOCOL_V1.md - 100%

*"Token generation patterns are the heartbeat of thought."* ⚛️🔬
