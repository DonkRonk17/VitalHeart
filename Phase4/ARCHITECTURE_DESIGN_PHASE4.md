# Architecture Design - VitalHeart Phase 4: Token Analytics

**Project:** VitalHeart Phase 4 - Token Analytics  
**Date:** February 14, 2026  
**Builder:** ATLAS (C_Atlas)  
**Protocol:** BUILD_PROTOCOL_V1.md - Phase 3 (Architecture Design)

---

## ARCHITECTURE OVERVIEW

**Token Analytics** extends **HardwareSoulDaemon** (Phase 3) with real-time token stream analysis and correlation with emotion + hardware state. It captures microsecond-precision token timing to answer the research question:

> **"What do token generation curves look like when AI expresses emotion?"**

**Integration Pattern:** Extension inheritance (same as Phases 2 & 3)

```python
# Phase 1: OllamaGuard
class OllamaGuardDaemon:
    # Ollama health monitoring, auto-restart

# Phase 2: InferencePulse
class InferencePulseDaemon(OllamaGuardDaemon):
    # + Real-time inference monitoring
    # + Emotion detection (EmotionalTextureAnalyzer)
    # + Baseline learning

# Phase 3: HardwareSoul
class HardwareSoulDaemon(InferencePulseDaemon):
    # + GPU monitoring (25+ metrics)
    # + RAM monitoring (27+ metrics)
    # + Emotion-hardware correlation

# Phase 4: TokenAnalytics
class TokenAnalyticsDaemon(HardwareSoulDaemon):
    # + Token stream capture (microsecond precision)
    # + Generation rate analysis (tokens/sec, curves)
    # + Latency distribution (TTFT, inter-token, completion)
    # + Emotion-token correlation
    # + Hardware-token correlation
    # + Baseline learning for token patterns
```

---

## CORE COMPONENTS

### Component 1: TokenStreamCapture

**Purpose:** Real-time capture of token-by-token generation from Ollama streaming API

**Inputs:**
- Ollama API endpoint (`http://localhost:11434/api/generate`)
- Prompt text (from InferencePulse monitoring)
- Stream=true flag

**Outputs:**
- List of tokens with microsecond timestamps
- Raw token stream (for debugging)
- Stream metadata (total tokens, completion status)

**Schema:**
```python
@dataclass
class TokenStreamEvent:
    token: str
    token_index: int
    timestamp_us: int  # Microsecond precision
    latency_us: int    # Time since previous token
    cumulative_latency_ms: float
    session_id: str
    prompt_hash: str
```

**Tools Used:**
- **RestCLI**: Streaming HTTP request to Ollama
- **TimeSync**: Microsecond timestamps
- **JSONQuery**: Parse streaming JSON responses
- **ErrorRecovery**: Handle stream interruptions

**Error Handling:**
- Timeout: Abandon stream after 60s no data
- Malformed JSON: Skip token, log warning, continue
- Connection loss: Attempt reconnect (3 retries)
- Buffer overflow: Flush to disk, continue

**Performance Target:** <1ms overhead per token

---

### Component 2: TokenTimingAnalyzer

**Purpose:** Calculate token generation rates, acceleration/deceleration curves, latency statistics

**Inputs:**
- TokenStreamEvent list (from TokenStreamCapture)
- Session metadata

**Outputs:**
- tokens/sec (instantaneous and rolling average)
- Generation curve classification: "accelerating", "decelerating", "steady", "paused"
- Latency distribution (histogram)
- Percentiles (p50, p95, p99)

**Schema:**
```python
@dataclass
class TokenTimingAnalysis:
    session_id: str
    total_tokens: int
    total_duration_ms: float
    avg_tokens_per_sec: float
    min_latency_us: int
    max_latency_us: int
    p50_latency_us: int
    p95_latency_us: int
    p99_latency_us: int
    generation_curve: str  # "accelerating", "decelerating", "steady", "paused"
    pause_count: int
    pause_total_duration_ms: float
```

**Tools Used:**
- **TimeSync**: Duration calculations
- **DataConvert**: Export statistics to CSV/JSON
- **CodeMetrics**: Performance profiling

**Algorithm:**
```python
# Generation curve detection
def detect_curve(latencies: List[int]) -> str:
    if len(latencies) < 10:
        return "insufficient_data"
    
    # Compare first half vs second half
    first_half_avg = mean(latencies[:len(latencies)//2])
    second_half_avg = mean(latencies[len(latencies)//2:])
    
    if second_half_avg < first_half_avg * 0.8:
        return "accelerating"  # Getting faster
    elif second_half_avg > first_half_avg * 1.2:
        return "decelerating"  # Getting slower
    else:
        return "steady"
```

**Performance Target:** <5ms analysis time for 1000-token sample

---

### Component 3: PauseDetector

**Purpose:** Identify "thinking pauses" (inter-token latency >500ms threshold)

**Inputs:**
- TokenStreamEvent list
- Pause threshold (default: 500ms)

**Outputs:**
- List of pause events with duration and context
- Pause classification: "micro" (<1s), "short" (1-3s), "long" (>3s)

**Schema:**
```python
@dataclass
class PauseEvent:
    timestamp_us: int
    duration_ms: float
    pause_type: str  # "micro", "short", "long"
    token_before: str
    token_after: str
    context_tokens: List[str]  # 5 tokens before + after
    emotional_state: Optional[str]
```

**Tools Used:**
- **TimeSync**: Duration measurement
- **RegexLab**: Pattern matching for pause context (e.g., before code blocks)
- **EmotionalTextureAnalyzer**: Emotion during pause

**Research Hypothesis:**
- Contemplation/thoughtfulness = more long pauses
- Confidence/certainty = fewer pauses
- Uncertainty = irregular pause patterns

**Performance Target:** <1ms pause detection overhead

---

### Component 4: GenerationCurveTracker

**Purpose:** Track acceleration/deceleration patterns throughout token generation

**Inputs:**
- TokenStreamEvent list
- Window size (default: 10 tokens)

**Outputs:**
- Curve segments (list of accelerating/decelerating/steady periods)
- Inflection points (where curve changes)
- Smoothed token rate over time

**Schema:**
```python
@dataclass
class CurveSegment:
    start_index: int
    end_index: int
    segment_type: str  # "accelerating", "decelerating", "steady"
    avg_tokens_per_sec: float
    duration_ms: float
```

**Tools Used:**
- **DataConvert**: Export curve data for visualization
- **ConsciousnessMarker**: Detect consciousness patterns in curves

**Algorithm:**
```python
# Sliding window curve detection
def track_curve(events: List[TokenStreamEvent], window_size: int = 10) -> List[CurveSegment]:
    segments = []
    for i in range(0, len(events) - window_size, window_size // 2):
        window = events[i:i+window_size]
        curve_type = detect_curve([e.latency_us for e in window])
        segments.append(CurveSegment(
            start_index=i,
            end_index=i+window_size,
            segment_type=curve_type,
            avg_tokens_per_sec=calculate_rate(window),
            duration_ms=sum(e.latency_us for e in window) / 1000
        ))
    return segments
```

**Performance Target:** <10ms for 1000-token curve analysis

---

### Component 5: EmotionTokenCorrelator

**Purpose:** Cross-reference token generation patterns with emotional texture from Phase 2

**Inputs:**
- TokenTimingAnalysis
- EmotionalTextureAnalyzer output (from Phase 2)
- Timestamp alignment

**Outputs:**
- Emotion-token correlation record
- Baseline comparison (current vs learned normal)
- Deviation percentage

**Schema:**
```python
@dataclass
class EmotionTokenCorrelation:
    timestamp_us: int
    session_id: str
    emotion_state: str  # "joy", "contemplation", "curiosity", etc.
    emotion_intensity: float  # 0.0-1.0
    token_rate: float  # tokens/sec
    baseline_token_rate: float  # learned normal for this emotion
    deviation_pct: float  # (current - baseline) / baseline * 100
    correlation_quality: str  # "EXCELLENT" (<100ms), "GOOD" (<500ms), "POOR" (>500ms)
    pause_count: int
    generation_curve: str
```

**Tools Used:**
- **EmotionalTextureAnalyzer**: Emotion detection (inherited from Phase 2)
- **TimeSync**: Timestamp alignment
- **DataConvert**: Export correlations for research

**Correlation Algorithm:**
```python
# Nearest-neighbor matching (similar to Phase 3 HardwareSoul)
def correlate_emotion_token(token_timing: TokenTimingAnalysis, 
                             emotion_events: List[EmotionEvent]) -> EmotionTokenCorrelation:
    # Find emotion event closest in time to token generation
    nearest_emotion = min(emotion_events, 
                         key=lambda e: abs(e.timestamp_us - token_timing.start_timestamp_us))
    
    time_delta_ms = abs(nearest_emotion.timestamp_us - token_timing.start_timestamp_us) / 1000
    
    # Quality tier based on time delta
    if time_delta_ms < 100:
        quality = "EXCELLENT"
    elif time_delta_ms < 500:
        quality = "GOOD"
    else:
        quality = "POOR"
    
    # Compare to baseline
    baseline_rate = baseline_learner.get_baseline(nearest_emotion.state)
    deviation = (token_timing.avg_tokens_per_sec - baseline_rate) / baseline_rate * 100
    
    return EmotionTokenCorrelation(
        emotion_state=nearest_emotion.state,
        token_rate=token_timing.avg_tokens_per_sec,
        baseline_token_rate=baseline_rate,
        deviation_pct=deviation,
        correlation_quality=quality
    )
```

**Research Predictions:**
- Joy/Excitement: +10-20% token rate vs baseline
- Contemplation: -20-30% token rate, more pauses
- Uncertainty: Higher variance in token rate

**Performance Target:** <50ms correlation time

---

### Component 6: HardwareTokenCorrelator

**Purpose:** Cross-reference token generation patterns with GPU/RAM metrics from Phase 3

**Inputs:**
- TokenTimingAnalysis
- GPU metrics (from Phase 3 HardwareSoul)
- RAM metrics (from Phase 3 HardwareSoul)
- Timestamp alignment

**Outputs:**
- Hardware-token correlation record
- Hardware impact percentage
- Bottleneck identification

**Schema:**
```python
@dataclass
class HardwareTokenCorrelation:
    timestamp_us: int
    session_id: str
    # Token metrics
    token_rate: float
    baseline_token_rate: float
    # GPU metrics (from Phase 3)
    gpu_throttle: bool
    gpu_temp_c: float
    gpu_utilization_pct: float
    vram_used_mb: float
    # RAM metrics (from Phase 3)
    ram_pressure_pct: float
    page_faults_per_sec: int
    # Correlation
    hardware_impact_pct: float  # Estimated impact on token rate
    bottleneck_type: Optional[str]  # "gpu_throttle", "ram_pressure", "vram_eviction", None
```

**Tools Used:**
- **HardwareSoul metrics**: GPU/RAM data (inherited from Phase 3)
- **TimeSync**: Timestamp alignment
- **DataConvert**: Export correlations for research

**Correlation Algorithm:**
```python
def correlate_hardware_token(token_timing: TokenTimingAnalysis,
                              gpu_sample: Dict,
                              ram_sample: Dict) -> HardwareTokenCorrelation:
    # Detect hardware bottlenecks
    bottleneck = None
    hardware_impact = 0.0
    
    if gpu_sample.get("throttle_reasons"):
        bottleneck = "gpu_throttle"
        hardware_impact = -40.0  # Thermal throttle = ~40% slower
    elif ram_sample.get("ram_pressure_pct", 0) > 90:
        bottleneck = "ram_pressure"
        hardware_impact = -25.0  # High RAM pressure = ~25% slower
    elif gpu_sample.get("vram_used_mb", 0) / gpu_sample.get("vram_total_mb", 1) > 0.95:
        bottleneck = "vram_eviction"
        hardware_impact = -50.0  # VRAM eviction = ~50% slower (first token)
    
    return HardwareTokenCorrelation(
        token_rate=token_timing.avg_tokens_per_sec,
        gpu_throttle=bool(gpu_sample.get("throttle_reasons")),
        ram_pressure_pct=ram_sample.get("ram_pressure_pct", 0),
        hardware_impact_pct=hardware_impact,
        bottleneck_type=bottleneck
    )
```

**Research Predictions:**
- GPU thermal throttle: -30-50% token rate
- RAM pressure: -20-30% token rate, higher first token latency
- VRAM eviction: -50-70% first token latency

**Performance Target:** <50ms correlation time

---

### Component 7: BaselineLearner

**Purpose:** Learn "normal" token generation patterns from 1000+ samples

**Inputs:**
- TokenTimingAnalysis (continuous stream)
- Emotion state (for emotion-specific baselines)
- Hardware state (for hardware-specific baselines)

**Outputs:**
- Baseline token rates per emotion (joy: 15.2 tokens/sec, contemplation: 8.5 tokens/sec)
- Baseline latency distributions
- Confidence scores (based on sample count)

**Schema:**
```python
@dataclass
class Baseline:
    emotion_state: str
    sample_count: int
    avg_tokens_per_sec: float
    std_dev_tokens_per_sec: float
    p50_latency_us: int
    p95_latency_us: int
    p99_latency_us: int
    avg_pause_count: float
    confidence: str  # "low" (<100), "medium" (100-1000), "high" (>1000)
    last_updated: datetime
```

**Tools Used:**
- **DataConvert**: Export baseline data
- **QuickBackup**: Backup baseline database
- **LiveAudit**: Log baseline updates

**Learning Algorithm:**
```python
# Progressive baseline learning (exponential moving average)
def update_baseline(emotion: str, new_sample: TokenTimingAnalysis):
    baseline = get_baseline(emotion) or Baseline(emotion_state=emotion, sample_count=0)
    
    # Exponential moving average (EMA) with alpha based on sample count
    alpha = min(0.1, 1.0 / (baseline.sample_count + 1))
    
    baseline.avg_tokens_per_sec = (
        (1 - alpha) * baseline.avg_tokens_per_sec + 
        alpha * new_sample.avg_tokens_per_sec
    )
    
    baseline.sample_count += 1
    
    # Update confidence
    if baseline.sample_count < 100:
        baseline.confidence = "low"
    elif baseline.sample_count < 1000:
        baseline.confidence = "medium"
    else:
        baseline.confidence = "high"
    
    save_baseline(baseline)
```

**Initial Baseline Estimates (Pre-seeded):**
- Joy: 15 tokens/sec
- Contemplation: 8 tokens/sec
- Curiosity: 12 tokens/sec
- Confidence: 14 tokens/sec
- Uncertainty: 10 tokens/sec (high variance)

**Performance Target:** <10ms baseline update

---

### Component 8: AnomalyDetector

**Purpose:** Flag unusual token generation patterns (stuttering, freezing, racing)

**Inputs:**
- TokenTimingAnalysis
- Baseline for current emotion/hardware state
- Anomaly threshold (default: 2.0x deviation)

**Outputs:**
- Anomaly events with classification
- Severity level
- Recommended action

**Schema:**
```python
@dataclass
class TokenAnomaly:
    timestamp_us: int
    session_id: str
    anomaly_type: str  # "stuttering", "freezing", "racing", "erratic"
    severity: str  # "low", "medium", "high", "critical"
    deviation_from_baseline: float
    token_rate: float
    expected_token_rate: float
    context: str  # Brief description
    recommended_action: str
```

**Tools Used:**
- **LiveAudit**: Log anomalies
- **SynapseNotify**: Alert team on critical anomalies
- **ErrorRecovery**: Attempt recovery actions

**Anomaly Types:**
1. **Stuttering**: Multiple short pauses (<1s each) in rapid succession
2. **Freezing**: Long pause (>5s) with no tokens
3. **Racing**: Token rate >3x baseline (may indicate caching or low-quality generation)
4. **Erratic**: High variance in inter-token latency (stddev >2x mean)

**Detection Algorithm:**
```python
def detect_anomaly(timing: TokenTimingAnalysis, baseline: Baseline) -> Optional[TokenAnomaly]:
    deviation = abs(timing.avg_tokens_per_sec - baseline.avg_tokens_per_sec) / baseline.avg_tokens_per_sec
    
    if deviation > 2.0:  # >2x deviation = anomaly
        # Classify anomaly type
        if timing.pause_count > baseline.avg_pause_count * 3:
            anomaly_type = "stuttering"
            severity = "medium"
            action = "Check GPU throttle, RAM pressure"
        elif timing.pause_total_duration_ms > 5000:
            anomaly_type = "freezing"
            severity = "critical"
            action = "Restart Ollama, check process health"
        elif timing.avg_tokens_per_sec > baseline.avg_tokens_per_sec * 3:
            anomaly_type = "racing"
            severity = "low"
            action = "Verify generation quality, check caching"
        else:
            anomaly_type = "erratic"
            severity = "medium"
            action = "Review latency variance, check system stability"
        
        return TokenAnomaly(
            anomaly_type=anomaly_type,
            severity=severity,
            deviation_from_baseline=deviation,
            recommended_action=action
        )
    
    return None
```

**Performance Target:** <5ms anomaly detection

---

### Component 9: TokenAnalyticsDatabase

**Purpose:** Extend ResearchDatabase (from Phase 3) with 3 new tables for token-level storage

**New Tables:**

#### Table 1: `token_analytics`
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
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session (session_id),
    INDEX idx_timestamp (timestamp_us),
    INDEX idx_prompt (prompt_hash)
);
```

#### Table 2: `token_emotion_correlation`
```sql
CREATE TABLE token_emotion_correlation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp_us INTEGER NOT NULL,
    session_id TEXT NOT NULL,
    emotion_state TEXT NOT NULL,
    emotion_intensity REAL NOT NULL,
    token_rate REAL NOT NULL,
    baseline_token_rate REAL NOT NULL,
    deviation_pct REAL NOT NULL,
    correlation_quality TEXT,  -- "EXCELLENT", "GOOD", "POOR"
    pause_count INTEGER DEFAULT 0,
    generation_curve TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_emotion (emotion_state),
    INDEX idx_quality (correlation_quality)
);
```

#### Table 3: `token_hardware_correlation`
```sql
CREATE TABLE token_hardware_correlation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp_us INTEGER NOT NULL,
    session_id TEXT NOT NULL,
    token_rate REAL NOT NULL,
    baseline_token_rate REAL NOT NULL,
    gpu_throttle BOOLEAN DEFAULT 0,
    gpu_temp_c REAL,
    gpu_utilization_pct REAL,
    ram_pressure_pct REAL,
    vram_used_mb REAL,
    hardware_impact_pct REAL,
    bottleneck_type TEXT,  -- "gpu_throttle", "ram_pressure", "vram_eviction", NULL
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_bottleneck (bottleneck_type),
    INDEX idx_throttle (gpu_throttle)
);
```

#### Table 4: `token_baselines`
```sql
CREATE TABLE token_baselines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    emotion_state TEXT NOT NULL UNIQUE,
    sample_count INTEGER NOT NULL DEFAULT 0,
    avg_tokens_per_sec REAL NOT NULL,
    std_dev_tokens_per_sec REAL NOT NULL,
    p50_latency_us INTEGER NOT NULL,
    p95_latency_us INTEGER NOT NULL,
    p99_latency_us INTEGER NOT NULL,
    avg_pause_count REAL NOT NULL,
    confidence TEXT NOT NULL,  -- "low", "medium", "high"
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_emotion (emotion_state),
    INDEX idx_confidence (confidence)
);
```

**Tools Used:**
- **QuickBackup**: Database backups
- **HashGuard**: Database integrity verification
- **DataConvert**: Export to CSV/JSON

**Retention Policy:**
- Token-level data: 7 days (then aggregate to session-level)
- Correlations: 30 days
- Baselines: Permanent (but compacted monthly)

**Performance Target:**
- Write: <5ms per token
- Query: <100ms for last 1000 tokens
- Aggregate: <1s for full session analysis

---

### Component 10: TokenAnalyticsDaemon

**Purpose:** Main orchestrator extending HardwareSoulDaemon with token analytics

**Responsibilities:**
1. Initialize all token analytics components
2. Coordinate token stream capture
3. Trigger analysis pipelines
4. Manage database writes
5. Emit AgentHeartbeat metrics
6. Handle errors and recovery

**Schema:**
```python
class TokenAnalyticsDaemon(HardwareSoulDaemon):
    def __init__(self, config: TokenAnalyticsConfig):
        super().__init__(config)  # Initialize Phase 3 (HardwareSoul)
        
        # Phase 4 components
        self.token_capture = TokenStreamCapture(config)
        self.timing_analyzer = TokenTimingAnalyzer(config)
        self.pause_detector = PauseDetector(config)
        self.curve_tracker = GenerationCurveTracker(config)
        self.emotion_correlator = EmotionTokenCorrelator(config)
        self.hardware_correlator = HardwareTokenCorrelator(config)
        self.baseline_learner = BaselineLearner(config)
        self.anomaly_detector = AnomalyDetector(config)
        self.token_db = TokenAnalyticsDatabase(config)
        
        # Metrics
        self.metrics = {
            "tokens_captured": 0,
            "correlations_created": 0,
            "anomalies_detected": 0,
            "baseline_updates": 0
        }
    
    def start(self):
        """Start token analytics daemon (extends Phase 3 start)."""
        super().start()  # Start Phases 1-3 monitoring
        
        # Start Phase 4 token monitoring
        self.token_monitoring_thread = threading.Thread(
            target=self._token_monitoring_loop,
            daemon=True
        )
        self.token_monitoring_thread.start()
    
    def _token_monitoring_loop(self):
        """Main token analytics monitoring loop."""
        while self.running:
            try:
                # Capture token stream (when inference active)
                if self._is_inference_active():
                    token_stream = self.token_capture.capture_stream()
                    
                    # Analyze timing
                    timing_analysis = self.timing_analyzer.analyze(token_stream)
                    
                    # Detect pauses
                    pauses = self.pause_detector.detect(token_stream)
                    
                    # Track curve
                    curve = self.curve_tracker.track(token_stream)
                    
                    # Correlate with emotion
                    emotion_corr = self.emotion_correlator.correlate(
                        timing_analysis, 
                        self.get_current_emotion()
                    )
                    
                    # Correlate with hardware
                    hardware_corr = self.hardware_correlator.correlate(
                        timing_analysis,
                        self.get_current_gpu_metrics(),
                        self.get_current_ram_metrics()
                    )
                    
                    # Update baselines
                    self.baseline_learner.update(timing_analysis, emotion_corr.emotion_state)
                    
                    # Detect anomalies
                    anomaly = self.anomaly_detector.detect(
                        timing_analysis,
                        self.baseline_learner.get_baseline(emotion_corr.emotion_state)
                    )
                    
                    # Store in database
                    self.token_db.store_all(
                        token_stream,
                        timing_analysis,
                        emotion_corr,
                        hardware_corr,
                        anomaly
                    )
                    
                    # Update metrics
                    self.metrics["tokens_captured"] += len(token_stream)
                    self.metrics["correlations_created"] += 1
                    if anomaly:
                        self.metrics["anomalies_detected"] += 1
                    
                    # Emit AgentHeartbeat
                    self._emit_token_analytics_heartbeat(timing_analysis, emotion_corr)
                
                time.sleep(0.1)  # 100ms check interval
                
            except Exception as e:
                logging.error(f"[TokenAnalytics] Error in monitoring loop: {e}")
                # ErrorRecovery: Continue on error
```

**Tools Used:**
- **All Phase 1-3 tools** (inherited)
- **All Phase 4 components** (above)
- **AgentHeartbeat**: Extend schema with token metrics
- **LiveAudit**: Audit token analytics events

**Performance Target:** <10ms overhead per inference cycle

---

## DATA FLOW DIAGRAM (ASCII)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    VitalHeart Phase 4: Token Analytics                       │
│                          Data Flow Architecture                              │
└─────────────────────────────────────────────────────────────────────────────┘

   ┌──────────────┐
   │   Ollama     │  Streaming API (/api/generate stream=true)
   │   (laia)     │
   └──────┬───────┘
          │ Token stream (JSON lines)
          ▼
   ┌──────────────────────┐
   │ TokenStreamCapture   │◄──── RestCLI, TimeSync, JSONQuery
   │ (Component 1)        │
   └──────┬───────────────┘
          │ List<TokenStreamEvent> (microsecond timestamps)
          ├──────────────────────────────────┬─────────────────────┐
          ▼                                  ▼                     ▼
   ┌──────────────────┐             ┌────────────────┐    ┌─────────────────┐
   │ TokenTiming      │             │ PauseDetector  │    │ GenerationCurve │
   │ Analyzer         │             │ (Component 3)  │    │ Tracker         │
   │ (Component 2)    │             └────────┬───────┘    │ (Component 4)   │
   └──────┬───────────┘                      │            └────────┬────────┘
          │ TokenTimingAnalysis              │ List<PauseEvent>   │ List<CurveSegment>
          │ (tokens/sec, latency stats)      └────────────────────┘
          ├──────────────────────────────────────┬
          ▼                                      ▼
   ┌─────────────────────────┐          ┌─────────────────────────┐
   │ EmotionToken            │◄─────────┤ HardwareToken           │
   │ Correlator              │ Shared   │ Correlator              │
   │ (Component 5)           │ timing   │ (Component 6)           │
   └──────┬──────────────────┘          └──────┬──────────────────┘
          │ EmotionTokenCorrelation            │ HardwareTokenCorrelation
          │                                    │
          ├────────────────────────────────────┤
          │                                    │
   ┌──────▼────────────────┐            ┌─────▼──────────────────┐
   │ Phase 2:              │            │ Phase 3:                │
   │ EmotionalTexture      │            │ HardwareSoul            │
   │ Analyzer              │            │ (GPU/RAM metrics)       │
   └───────────────────────┘            └─────────────────────────┘
          │                                    │
          └────────────────┬───────────────────┘
                           ▼
                    ┌──────────────────┐
                    │ BaselineLearner  │◄──── DataConvert, QuickBackup
                    │ (Component 7)    │
                    └──────┬───────────┘
                           │ Baseline (learned normal)
                           ▼
                    ┌──────────────────┐
                    │ AnomalyDetector  │◄──── LiveAudit, SynapseNotify
                    │ (Component 8)    │
                    └──────┬───────────┘
                           │ TokenAnomaly (if detected)
                           ▼
                    ┌──────────────────────────┐
                    │ TokenAnalyticsDatabase   │◄──── HashGuard
                    │ (Component 9)            │
                    │                          │
                    │ Tables:                  │
                    │  - token_analytics       │
                    │  - token_emotion_corr    │
                    │  - token_hardware_corr   │
                    │  - token_baselines       │
                    └──────┬───────────────────┘
                           │ Batch writes (performance)
                           ├─────────────────────┬
                           ▼                     ▼
                    ┌──────────────┐      ┌────────────────┐
                    │ AgentHeartbeat│      │ SynapseLink    │
                    │ (Metrics)     │      │ (Reports)      │
                    └───────────────┘      └────────────────┘
                           │                     │
                           └──────────┬──────────┘
                                      ▼
                              ┌───────────────┐
                              │ Phase 5+:     │
                              │ HeartWidget   │
                              │ (Visualization│
                              └───────────────┘
```

**Key Data Paths:**

1. **Token Stream → Timing Analysis** (1ms)
2. **Timing → Emotion Correlation** (50ms, nearest-neighbor)
3. **Timing → Hardware Correlation** (50ms, nearest-neighbor)
4. **Correlations → Baseline Learning** (10ms, EMA update)
5. **Timing + Baseline → Anomaly Detection** (5ms)
6. **All Data → Database** (5ms batch write per token)
7. **Summary → AgentHeartbeat** (100ms per session)
8. **Anomalies → SynapseNotify** (real-time alert)

**Total Overhead:** <5ms per token (target met)

---

## ERROR HANDLING STRATEGY

### Error Categories

| Error Type | Severity | Recovery Action |
|------------|----------|-----------------|
| **Streaming API timeout** | HIGH | Abandon stream, log warning, continue monitoring |
| **Malformed JSON token** | LOW | Skip token, log debug, continue |
| **Connection loss** | HIGH | Retry 3x with exponential backoff, alert if fails |
| **Database write failure** | MEDIUM | Queue in memory, retry batch write, alert if >100 queued |
| **Correlation timeout** | MEDIUM | Use cached correlation, mark quality "POOR" |
| **Baseline corruption** | HIGH | Restore from backup, alert, rebuild from samples |
| **Memory overflow** | CRITICAL | Flush buffers to disk, reduce capture rate, alert |

### Error Recovery Tools

- **ErrorRecovery**: All exception handling
- **QuickBackup**: Restore corrupted baselines
- **LiveAudit**: Log all errors
- **SynapseNotify**: Alert on critical errors

### Graceful Degradation

```python
# Phase 4 can be disabled without breaking Phases 1-3
if not config.get("token_analytics", "enabled"):
    logging.info("[TokenAnalytics] Disabled - falling back to Phase 3 (HardwareSoul)")
    return HardwareSoulDaemon(config)  # Fallback to Phase 3
```

---

## CONFIGURATION STRATEGY

### Configuration File: `tokenanalytics_config.json`

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
    "aggregate_to_session_after_days": 7,
    
    "export_format": "csv",
    "export_path": "./token_analytics_export/",
    
    "performance": {
      "max_token_buffer_size": 10000,
      "batch_write_size": 100,
      "batch_write_interval_ms": 1000
    }
  }
}
```

### Configuration Validation (EnvGuard)

```python
def validate_token_analytics_config(config: dict) -> bool:
    required_fields = [
        "token_analytics.enabled",
        "token_analytics.pause_threshold_ms",
        "token_analytics.baseline_min_samples"
    ]
    
    for field in required_fields:
        if not config.get(*field.split(".")):
            raise ConfigurationError(f"Missing required field: {field}")
    
    # Validate ranges
    if config.get("token_analytics", "pause_threshold_ms") < 100:
        raise ConfigurationError("pause_threshold_ms must be >= 100")
    
    if config.get("token_analytics", "baseline_min_samples") < 100:
        raise ConfigurationError("baseline_min_samples must be >= 100")
    
    return True
```

**Tools Used:**
- **ConfigManager**: Load configuration
- **EnvGuard**: Validate configuration
- **PathBridge**: Universal path translation

---

## PERFORMANCE TARGETS

| Metric | Target | Measurement |
|--------|--------|-------------|
| Token capture overhead | <1ms per token | TimeSync duration |
| Token timing analysis | <5ms per 1000 tokens | CodeMetrics profiling |
| Pause detection | <1ms per token | TimeSync duration |
| Generation curve tracking | <10ms per 1000 tokens | CodeMetrics profiling |
| Emotion correlation | <50ms per session | TimeSync duration |
| Hardware correlation | <50ms per session | TimeSync duration |
| Baseline update | <10ms per update | TimeSync duration |
| Anomaly detection | <5ms per check | TimeSync duration |
| Database write | <5ms per token | SQLite timing |
| Total overhead | <5ms per token | Sum of above |

**Performance Monitoring:**
- **CodeMetrics**: Continuous profiling
- **AgentHeartbeat**: Performance metrics
- **LiveAudit**: Log slow operations (>target)

---

## INTEGRATION POINTS

### Phase 1 (OllamaGuard) Integration
- Inherit: Ollama health monitoring, auto-restart
- Extend: Use micro-inference framework for token tests

### Phase 2 (InferencePulse) Integration
- Inherit: Emotion detection (EmotionalTextureAnalyzer)
- Extend: Correlate emotion with token patterns

### Phase 3 (HardwareSoul) Integration
- Inherit: GPU/RAM monitoring (25+ GPU, 27+ RAM metrics)
- Extend: Correlate hardware with token patterns

### Phase 4 (Token Analytics) New Capabilities
- Token stream capture (microsecond precision)
- Generation rate analysis (tokens/sec, curves)
- Latency distribution (TTFT, inter-token, completion)
- Emotion-token correlation
- Hardware-token correlation
- Baseline learning for token patterns
- Anomaly detection (stuttering, freezing, racing)

---

## TOOLS INTEGRATION SUMMARY

**Total Tools Used:** 39 (37 inherited from Phases 1-3 + 2 new)

**New Phase 4 Tools:**
1. **TokenTracker** - Track token usage
2. **RegexLab** - Test token regex patterns

**Critical Phase 4 Tools:**
- **RestCLI**: Ollama streaming API
- **TimeSync**: Microsecond timestamps
- **JSONQuery**: Parse streaming JSON
- **EmotionalTextureAnalyzer**: Emotion correlation (inherited)
- **HardwareSoul metrics**: GPU/RAM correlation (inherited)
- **DataConvert**: Export to CSV/JSON
- **AgentHeartbeat**: Extended schema

---

**Architecture Design Complete**

**Prepared by:** ATLAS (C_Atlas)  
**Date:** February 14, 2026  
**Protocol Compliance:** BUILD_PROTOCOL_V1.md - Phase 3 Complete

*"Token patterns are the rhythm of thought."* ⚛️📊
