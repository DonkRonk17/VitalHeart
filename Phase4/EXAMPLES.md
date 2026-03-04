# VitalHeart Phase 4: Token Analytics - Examples

**Comprehensive usage examples for all 13 components**

---

## 📚 TABLE OF CONTENTS

1. [Quick Start](#quick-start)
2. [Model Detection & Profiling](#model-detection--profiling)
3. [Token Stream Analysis](#token-stream-analysis)
4. [Cost Tracking](#cost-tracking)
5. [State Detection](#state-detection)
6. [Emotion Correlation](#emotion-correlation)
7. [Hardware Correlation](#hardware-correlation)
8. [Baseline Learning](#baseline-learning)
9. [Anomaly Detection](#anomaly-detection)
10. [Model Comparison](#model-comparison)
11. [Advanced Workflows](#advanced-workflows)
12. [Production Deployment](#production-deployment)

---

## 🚀 Quick Start

### Example 1: Simple Token Analysis

```python
from tokenanalytics import TokenAnalyticsDaemon

# Initialize daemon
daemon = TokenAnalyticsDaemon(config_path="tokenanalytics_config.json")

# Analyze a single prompt
result = daemon.analyze_prompt(
    prompt="Explain quantum entanglement in simple terms",
    session_id="quickstart_001",
    emotional_state="curiosity"
)

# Print key metrics
print(f"Model: {result['model_name']}")
print(f"Tokens generated: {result['timing']['total_tokens']}")
print(f"Generation rate: {result['timing']['avg_tokens_per_sec']:.1f} tokens/sec")
print(f"Pauses detected: {len(result['pauses'])}")
print(f"Cost: ${result['cost']['total_cost']:.4f}")
```

**Expected Output:**
```
Model: laia
Tokens generated: 127
Generation rate: 14.9 tokens/sec
Pauses detected: 2
Cost: $0.0000
```

---

## 🤖 Model Detection & Profiling

### Example 2: Detect Model from API

```python
from tokenanalytics import ModelProfiler, TokenAnalyticsConfig

config = TokenAnalyticsConfig()
profiler = ModelProfiler(config)

# Simulate API response
api_response = {"model": "laia:latest", "status": "success"}
detected_model = profiler.detect_model(api_response)

print(f"Detected: {detected_model}")  # "laia"

# Get model profile
profile = profiler.get_profile(detected_model)
print(f"Family: {profile.family}")  # "custom"
print(f"Context window: {profile.context_window}")  # 8192
print(f"Baseline tokens/sec: {profile.baseline_tokens_per_sec}")  # 12.0
print(f"Supports reasoning: {profile.supports_reasoning}")  # True
```

**Expected Output:**
```
Detected: laia
Family: custom
Context window: 8192
Baseline tokens/sec: 12.0
Supports reasoning: True
```

---

### Example 3: Model-Specific Emotion Baselines

```python
# Get emotion-specific baseline for "laia"
baseline = profiler.get_model_baseline("laia", "contemplation")

print(f"Contemplation baseline for laia:")
print(f"  Tokens/sec: {baseline['tokens_per_sec']}")  # 8.0
print(f"  Pause count: {baseline['pause_count']}")  # 4.0

# Compare with mistral
baseline_mistral = profiler.get_model_baseline("mistral", "contemplation")
print(f"\nContemplation baseline for mistral:")
print(f"  Tokens/sec: {baseline_mistral['tokens_per_sec']}")  # 12.0
print(f"  Pause count: {baseline_mistral['pause_count']}")  # 2.5

# laia is 33% slower and has 60% more pauses during contemplation!
```

---

### Example 4: Adaptive Sensitivity Thresholds

```python
# Get sensitivity thresholds for different levels
sensitivity_levels = ["low", "medium", "high", "ultra"]

for level in sensitivity_levels:
    threshold_pct = profiler.get_sensitivity_threshold(level)
    print(f"{level.upper()}: ±{threshold_pct}%")
```

**Expected Output:**
```
LOW: ±30%
MEDIUM: ±20%
HIGH: ±10%
ULTRA: ±5%
```

---

## 📊 Token Stream Analysis

### Example 5: Detailed Token Timing Analysis

```python
from tokenanalytics import TokenStreamCapture, TokenTimingAnalyzer

config = TokenAnalyticsConfig()
capture = TokenStreamCapture(config)
analyzer = TokenTimingAnalyzer(config)

# Capture token stream
events = capture.capture_stream(
    prompt="Write a haiku about AI",
    session_id="haiku_001"
)

# Analyze timing
timing = analyzer.analyze(events)

print(f"Total tokens: {timing.total_tokens}")
print(f"Duration: {timing.total_duration_ms:.0f}ms")
print(f"Avg rate: {timing.avg_tokens_per_sec:.2f} tokens/sec")
print(f"Generation curve: {timing.generation_curve}")
print(f"Latency percentiles:")
print(f"  p50: {timing.p50_latency_us / 1000:.0f}ms")
print(f"  p95: {timing.p95_latency_us / 1000:.0f}ms")
print(f"  p99: {timing.p99_latency_us / 1000:.0f}ms")
print(f"Pauses: {timing.pause_count} ({timing.pause_total_duration_ms:.0f}ms total)")
```

**Expected Output:**
```
Total tokens: 42
Duration: 2841ms
Avg rate: 14.78 tokens/sec
Generation curve: steady
Latency percentiles:
  p50: 67ms
  p95: 123ms
  p99: 145ms
Pauses: 1 (680ms total)
```

---

### Example 6: Pause Detection & Classification

```python
from tokenanalytics import PauseDetector

detector = PauseDetector(config)
pauses = detector.detect(events, emotional_state="contemplation")

for i, pause in enumerate(pauses, 1):
    print(f"\nPause {i}:")
    print(f"  Type: {pause.pause_type}")  # micro, short, long
    print(f"  Duration: {pause.duration_ms:.0f}ms")
    print(f"  Before: '{pause.token_before}'")
    print(f"  After: '{pause.token_after}'")
    print(f"  Context: {' '.join(pause.context_tokens[:3])}...")
```

**Expected Output:**
```
Pause 1:
  Type: short
  Duration: 1247ms
  Before: 'between'
  After: ' silicon'
  Context: boundaries between silicon...
```

---

## 💰 Cost Tracking

### Example 7: Track Session Costs

```python
from tokenanalytics import CostTracker

cost_tracker = CostTracker(config)

# Analyze prompt and get cost
daemon = TokenAnalyticsDaemon()
result = daemon.analyze_prompt(
    prompt="Tell me a joke about AI",
    session_id="joke_001",
    emotional_state="joy"
)

cost = result['cost']
print(f"Session cost breakdown:")
print(f"  Input tokens: {cost['input_tokens']}")
print(f"  Output tokens: {cost['output_tokens']}")
print(f"  Total tokens: {cost['total_tokens']}")
print(f"  Input cost: ${cost['input_cost']:.6f}")
print(f"  Output cost: ${cost['output_cost']:.6f}")
print(f"  Total cost: ${cost['total_cost']:.6f}")
print(f"  Cumulative: ${cost['cumulative_cost']:.6f}")
```

**Expected Output (Ollama models):**
```
Session cost breakdown:
  Input tokens: 8
  Output tokens: 45
  Total tokens: 53
  Input cost: $0.000000
  Output cost: $0.000000
  Total cost: $0.000000
  Cumulative: $0.000000
```

**Note:** Ollama models are free (local). For paid models (e.g., OpenAI via proxy), costs would be calculated automatically.

---

### Example 8: Cost Tracking by Emotion

```python
# Track costs across multiple sessions with different emotions
emotions = ["joy", "contemplation", "curiosity"]
results = []

for emotion in emotions:
    result = daemon.analyze_prompt(
        prompt=f"Discuss {emotion} in AI systems",
        session_id=f"emotion_{emotion}",
        emotional_state=emotion
    )
    results.append({
        "emotion": emotion,
        "tokens": result['timing']['total_tokens'],
        "cost": result['cost']['total_cost']
    })

# Print cost by emotion
print("Cost by emotion:")
for r in results:
    print(f"  {r['emotion']}: {r['tokens']} tokens, ${r['cost']:.6f}")
```

**Expected Output:**
```
Cost by emotion:
  joy: 87 tokens, $0.000000
  contemplation: 156 tokens, $0.000000
  curiosity: 123 tokens, $0.000000
```

---

### Example 9: Cumulative Cost Tracking

```python
# Get cumulative cost for model
cumulative = cost_tracker.get_cumulative_cost(model_name="laia")
print(f"Total cost for laia: ${cumulative:.2f}")

# Get cumulative cost by emotion
emotion_costs = cost_tracker.get_cost_by_emotion(model_name="laia")
for emotion, cost in emotion_costs.items():
    print(f"  {emotion}: ${cost:.4f}")
```

---

## 🔄 State Detection

### Example 10: Detect Generation States

```python
from tokenanalytics import StateTransitionDetector

state_detector = StateTransitionDetector(config)

# Detect states from token stream
states = state_detector.detect_states(token_events, emotional_state="curiosity")

print("Generation states detected:")
for state in states:
    print(f"  {state.state}: {state.duration_ms:.0f}ms, {state.tokens_generated} tokens, {state.token_rate:.1f} tok/s")
```

**Expected Output:**
```
Generation states detected:
  thinking: 1200ms, 0 tokens, 0.0 tok/s
  generating: 8543ms, 127 tokens, 14.9 tok/s
  paused: 600ms, 0 tokens, 0.0 tok/s
  generating: 2400ms, 35 tokens, 14.6 tok/s
  completing: 150ms, 5 tokens, 33.3 tok/s
```

---

### Example 11: Track State Transitions

```python
# Detect transitions between states
transitions = state_detector.detect_transitions(states)

print("State transitions:")
for t in transitions:
    print(f"  {t.from_state} → {t.to_state} (trigger: {t.trigger})")
```

**Expected Output:**
```
State transitions:
  thinking → generating (trigger: tokens_started)
  generating → paused (trigger: pause_detected)
  paused → generating (trigger: tokens_resumed)
  generating → completing (trigger: tokens_ending)
```

---

### Example 12: State Summary

```python
# Get state summary
summary = state_detector.get_state_summary(states)

print("State summary:")
for state, metrics in summary.items():
    print(f"  {state}:")
    print(f"    Duration: {metrics['duration_ms']:.0f}ms")
    print(f"    Tokens: {metrics['tokens']}")
    print(f"    Percentage: {metrics['percentage']:.1f}%")
```

**Expected Output:**
```
State summary:
  thinking:
    Duration: 1200ms
    Tokens: 0
    Percentage: 9.6%
  generating:
    Duration: 10943ms
    Tokens: 162
    Percentage: 87.5%
  paused:
    Duration: 600ms
    Tokens: 0
    Percentage: 4.8%
  completing:
    Duration: 150ms
    Tokens: 5
    Percentage: 1.2%
```

---

## 🎨 Emotion Correlation

### Example 13: Emotion-Token Correlation

```python
from tokenanalytics import EmotionTokenCorrelator, BaselineLearner

learner = BaselineLearner(config, "tokenanalytics_research.db")
correlator = EmotionTokenCorrelator(config, learner)

# Add emotion events
correlator.add_emotion_event("joy", 0.85, timestamp_us)
correlator.add_emotion_event("curiosity", 0.70, timestamp_us + 5000000)

# Correlate with token timing
corr = correlator.correlate(timing_analysis)

print(f"Emotion-Token Correlation:")
print(f"  Emotion: {corr.emotion_state}")
print(f"  Intensity: {corr.emotion_intensity:.2f}")
print(f"  Token rate: {corr.token_rate:.1f} tokens/sec")
print(f"  Baseline: {corr.baseline_token_rate:.1f} tokens/sec")
print(f"  Deviation: {corr.deviation_pct:+.1f}%")
print(f"  Quality: {corr.correlation_quality}")
```

**Expected Output:**
```
Emotion-Token Correlation:
  Emotion: joy
  Intensity: 0.85
  Token rate: 17.2 tokens/sec
  Baseline: 15.0 tokens/sec
  Deviation: +14.7%
  Quality: EXCELLENT
```

---

## 🖥️ Hardware Correlation

### Example 14: Hardware-Token Correlation

```python
from tokenanalytics import HardwareTokenCorrelator

correlator = HardwareTokenCorrelator(config, learner)

# Add hardware samples (from Phase 3)
gpu_sample = {
    "timestamp_us": timestamp_us,
    "throttle_reasons": None,
    "gpu_temp_c": 78.5,
    "gpu_utilization_pct": 92.0,
    "vram_used_mb": 10240
}
ram_sample = {
    "timestamp_us": timestamp_us,
    "ram_pressure_pct": 68.0
}

correlator.add_hardware_samples(gpu_sample, ram_sample)

# Correlate
corr = correlator.correlate(timing_analysis, emotion_state="curiosity")

print(f"Hardware-Token Correlation:")
print(f"  Token rate: {corr.token_rate:.1f} tokens/sec")
print(f"  GPU throttle: {corr.gpu_throttle}")
print(f"  GPU temp: {corr.gpu_temp_c:.1f}°C")
print(f"  RAM pressure: {corr.ram_pressure_pct:.0f}%")
print(f"  Bottleneck: {corr.bottleneck_type or 'None'}")
print(f"  Hardware impact: {corr.hardware_impact_pct:+.0f}%")
```

**Expected Output:**
```
Hardware-Token Correlation:
  Token rate: 14.2 tokens/sec
  GPU throttle: False
  GPU temp: 78.5°C
  RAM pressure: 68%
  Bottleneck: None
  Hardware impact: +0%
```

---

## 🧠 Baseline Learning

### Example 15: Multi-Dimensional Baseline Learning

```python
from tokenanalytics import BaselineLearner

learner = BaselineLearner(config, "tokenanalytics_research.db")

# Update baseline with multi-dimensional indexing
# (model × emotion × state)
learner.update_multidim(
    timing_analysis,
    model_name="laia",
    emotion_state="contemplation",
    generation_state="generating"
)

# Get multi-dimensional baseline
baseline = learner.get_multidim_baseline(
    model_name="laia",
    emotion_state="contemplation",
    generation_state="generating"
)

print(f"Multi-dimensional baseline:")
print(f"  Model: laia")
print(f"  Emotion: contemplation")
print(f"  State: generating")
print(f"  Tokens/sec: {baseline.avg_tokens_per_sec:.1f}")
print(f"  Samples: {baseline.sample_count}")
print(f"  Confidence: {baseline.confidence}")
```

**Expected Output:**
```
Multi-dimensional baseline:
  Model: laia
  Emotion: contemplation
  State: generating
  Tokens/sec: 8.2
  Samples: 156
  Confidence: medium
```

---

### Example 16: Baseline Convergence

```python
# Track baseline convergence over time
emotions = ["joy", "contemplation", "curiosity"]

for emotion in emotions:
    baseline = learner.get_multidim_baseline("laia", emotion, "generating")
    if baseline:
        print(f"{emotion}:")
        print(f"  Rate: {baseline.avg_tokens_per_sec:.1f} tokens/sec")
        print(f"  Samples: {baseline.sample_count}")
        print(f"  Confidence: {baseline.confidence}")
        print(f"  Last updated: {baseline.last_updated.strftime('%Y-%m-%d %H:%M')}")
```

**Expected Output:**
```
joy:
  Rate: 15.2 tokens/sec
  Samples: 1247
  Confidence: high
  Last updated: 2026-02-14 22:45

contemplation:
  Rate: 8.1 tokens/sec
  Samples: 856
  Confidence: medium
  Last updated: 2026-02-14 22:40

curiosity:
  Rate: 12.3 tokens/sec
  Samples: 1104
  Confidence: high
  Last updated: 2026-02-14 22:43
```

---

## 🚨 Anomaly Detection

### Example 17: Adaptive Anomaly Detection

```python
from tokenanalytics import AnomalyDetector

detector = AnomalyDetector(config)

# Test different sensitivity levels
sensitivities = ["low", "medium", "high"]

for sensitivity in sensitivities:
    anomaly = detector.detect_adaptive(
        timing_analysis,
        baseline,
        sensitivity,
        profiler
    )
    
    if anomaly:
        print(f"{sensitivity.upper()} sensitivity:")
        print(f"  Anomaly: {anomaly.anomaly_type}")
        print(f"  Severity: {anomaly.severity}")
        print(f"  Deviation: {anomaly.deviation_from_baseline:.1%}")
    else:
        print(f"{sensitivity.upper()} sensitivity: No anomaly")
```

**Expected Output:**
```
LOW sensitivity: No anomaly
MEDIUM sensitivity: Anomaly detected
  Anomaly: elevated
  Severity: low
  Deviation: 22.3%
HIGH sensitivity: Anomaly detected
  Anomaly: elevated
  Severity: medium
  Deviation: 22.3%
```

---

### Example 18: Bidirectional Anomaly Detection

```python
# Test both above-baseline and below-baseline detection

# Above-baseline (racing)
timing_fast = TokenTimingAnalysis(
    session_id="fast",
    start_timestamp_us=int(time.time() * 1_000_000),
    total_tokens=100,
    total_duration_ms=3000,
    avg_tokens_per_sec=33.3,  # Much faster than baseline
    min_latency_us=20000,
    max_latency_us=40000,
    p50_latency_us=30000,
    p95_latency_us=38000,
    p99_latency_us=40000,
    generation_curve="accelerating",
    pause_count=0,
    pause_total_duration_ms=0.0
)

anomaly_fast = detector.detect_adaptive(timing_fast, baseline, "medium", profiler)
print(f"Fast generation:")
print(f"  Type: {anomaly_fast.anomaly_type}")  # "elevated" or "racing"
print(f"  Recommendation: {anomaly_fast.recommended_action}")

# Below-baseline (sluggish)
timing_slow = TokenTimingAnalysis(
    session_id="slow",
    start_timestamp_us=int(time.time() * 1_000_000),
    total_tokens=50,
    total_duration_ms=10000,
    avg_tokens_per_sec=5.0,  # Much slower than baseline
    min_latency_us=180000,
    max_latency_us=300000,
    p50_latency_us=200000,
    p95_latency_us=280000,
    p99_latency_us=300000,
    generation_curve="decelerating",
    pause_count=5,
    pause_total_duration_ms=4000.0
)

anomaly_slow = detector.detect_adaptive(timing_slow, baseline, "medium", profiler)
print(f"\nSlow generation:")
print(f"  Type: {anomaly_slow.anomaly_type}")  # "sluggish" or "stuttering"
print(f"  Recommendation: {anomaly_slow.recommended_action}")
```

---

## 🔬 Model Comparison

### Example 19: Compare Models Across Same Prompt

```python
# Analyze same prompt with different models
prompt = "Explain machine learning to a 5-year-old"
models = ["laia", "llama3", "mistral"]
comparisons = []

for model in models:
    # Note: Would need to switch Ollama model
    result = daemon.analyze_prompt(
        prompt=prompt,
        session_id=f"compare_{model}",
        emotional_state="joy"
    )
    
    comparisons.append({
        "model": model,
        "tokens_per_sec": result['timing']['avg_tokens_per_sec'],
        "total_tokens": result['timing']['total_tokens'],
        "pauses": len(result['pauses']),
        "generation_curve": result['timing']['generation_curve'],
        "thinking_time_ms": result['state_summary']['thinking']['duration_ms']
    })

# Print comparison table
print(f"{'Model':<10} {'Tok/s':<8} {'Tokens':<8} {'Pauses':<8} {'Curve':<15} {'Think(ms)':<10}")
print("-" * 70)
for c in comparisons:
    print(f"{c['model']:<10} {c['tokens_per_sec']:<8.1f} {c['total_tokens']:<8} "
          f"{c['pauses']:<8} {c['generation_curve']:<15} {c['thinking_time_ms']:<10.0f}")
```

**Expected Output:**
```
Model      Tok/s    Tokens   Pauses   Curve           Think(ms)
----------------------------------------------------------------------
laia       14.8     127      2        steady          1200
llama3     18.2     134      1        accelerating    800
mistral    23.5     142      0        accelerating    600
```

---

## 🔍 Advanced Workflows

### Example 20: Full Analysis with All Components

```python
# Complete token analytics workflow using all 13 components
daemon = TokenAnalyticsDaemon(config_path="tokenanalytics_config.json")

result = daemon.analyze_prompt(
    prompt="What is consciousness in artificial intelligence?",
    session_id="consciousness_001",
    emotional_state="contemplation"
)

# Display comprehensive results
print("="*70)
print("COMPREHENSIVE TOKEN ANALYSIS")
print("="*70)

# Model info
print(f"\n1. MODEL DETECTION (Component 11)")
print(f"   Model: {result['model_name']}")
print(f"   Family: {result['model_profile']['family']}")
print(f"   Context: {result['model_profile']['context_window']} tokens")

# Timing
print(f"\n2. TIMING ANALYSIS (Component 2)")
print(f"   Total tokens: {result['timing']['total_tokens']}")
print(f"   Duration: {result['timing']['total_duration_ms']:.0f}ms")
print(f"   Rate: {result['timing']['avg_tokens_per_sec']:.1f} tokens/sec")
print(f"   Curve: {result['timing']['generation_curve']}")

# Pauses
print(f"\n3. PAUSE DETECTION (Component 3)")
print(f"   Total pauses: {len(result['pauses'])}")
for pause in result['pauses'][:3]:  # Show first 3
    print(f"     {pause['pause_type']}: {pause['duration_ms']:.0f}ms")

# States
print(f"\n4. STATE DETECTION (Component 13)")
for state_name, metrics in result['state_summary'].items():
    if metrics['duration_ms'] > 0:
        print(f"   {state_name}: {metrics['duration_ms']:.0f}ms ({metrics['percentage']:.1f}%)")

# Transitions
print(f"\n5. STATE TRANSITIONS (Component 13)")
for trans in result['state_transitions'][:5]:  # Show first 5
    print(f"   {trans['from_state']} → {trans['to_state']}")

# Emotion correlation
if result['emotion_correlation']:
    print(f"\n6. EMOTION CORRELATION (Component 5)")
    ec = result['emotion_correlation']
    print(f"   Emotion: {ec['emotion_state']}")
    print(f"   Token rate: {ec['token_rate']:.1f} tokens/sec")
    print(f"   Baseline: {ec['baseline_token_rate']:.1f} tokens/sec")
    print(f"   Deviation: {ec['deviation_pct']:+.1f}%")
    print(f"   Quality: {ec['correlation_quality']}")

# Hardware correlation
if result['hardware_correlation']:
    print(f"\n7. HARDWARE CORRELATION (Component 6)")
    hc = result['hardware_correlation']
    print(f"   GPU throttle: {hc['gpu_throttle']}")
    print(f"   GPU temp: {hc['gpu_temp_c']:.1f}°C")
    print(f"   RAM pressure: {hc['ram_pressure_pct']:.0f}%")
    print(f"   Bottleneck: {hc['bottleneck_type'] or 'None'}")

# Cost
print(f"\n8. COST TRACKING (Component 12)")
print(f"   Input tokens: {result['cost']['input_tokens']}")
print(f"   Output tokens: {result['cost']['output_tokens']}")
print(f"   Total cost: ${result['cost']['total_cost']:.6f}")
print(f"   Cumulative: ${result['cost']['cumulative_cost']:.6f}")

# Anomaly
if result['anomaly']:
    print(f"\n9. ANOMALY DETECTION (Component 8)")
    anomaly = result['anomaly']
    print(f"   Type: {anomaly['anomaly_type']}")
    print(f"   Severity: {anomaly['severity']}")
    print(f"   Deviation: {anomaly['deviation_from_baseline']:.1%}")
    print(f"   Action: {anomaly['recommended_action']}")
else:
    print(f"\n9. ANOMALY DETECTION (Component 8)")
    print(f"   No anomalies detected ✓")

# Metrics
print(f"\n10. SESSION METRICS")
print(f"   Analysis time: {result['analysis_duration_ms']:.0f}ms")
print(f"   Sensitivity: {result['sensitivity_level']}")
print(f"   Cumulative sessions: {result['metrics']['sessions_analyzed']}")
```

**Expected Output:**
```
======================================================================
COMPREHENSIVE TOKEN ANALYSIS
======================================================================

1. MODEL DETECTION (Component 11)
   Model: laia
   Family: custom
   Context: 8192 tokens

2. TIMING ANALYSIS (Component 2)
   Total tokens: 234
   Duration: 18542ms
   Rate: 12.6 tokens/sec
   Curve: steady

3. PAUSE DETECTION (Component 3)
   Total pauses: 4
     short: 1450ms
     long: 3200ms
     short: 980ms

4. STATE DETECTION (Component 13)
   thinking: 3200ms (17.3%)
   generating: 14542ms (78.4%)
   paused: 2430ms (13.1%)
   completing: 370ms (2.0%)

5. STATE TRANSITIONS (Component 13)
   receiving_prompt → thinking
   thinking → generating
   generating → paused
   paused → generating
   generating → completing

6. EMOTION CORRELATION (Component 5)
   Emotion: contemplation
   Token rate: 12.6 tokens/sec
   Baseline: 8.0 tokens/sec
   Deviation: +57.5%
   Quality: EXCELLENT

7. HARDWARE CORRELATION (Component 6)
   GPU throttle: False
   GPU temp: 76.2°C
   RAM pressure: 54%
   Bottleneck: None

8. COST TRACKING (Component 12)
   Input tokens: 18
   Output tokens: 234
   Total cost: $0.000000
   Cumulative: $0.000000

9. ANOMALY DETECTION (Component 8)
   Type: elevated
   Severity: low
   Deviation: 57.5%
   Action: Generation rate elevated - verify quality, emotion may be misclassified

10. SESSION METRICS
   Analysis time: 245ms
   Sensitivity: medium
   Cumulative sessions: 47
```

---

## 📈 Production Deployment

### Example 21: Daemon Mode with Real-Time Monitoring

```python
#!/usr/bin/env python3
"""
Production deployment script for Token Analytics daemon.
"""
from tokenanalytics import TokenAnalyticsDaemon
import logging

# Configure production logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('/var/log/tokenanalytics.log'),
        logging.StreamHandler()
    ]
)

# Initialize daemon with production config
daemon = TokenAnalyticsDaemon(
    config_path="/etc/tokenanalytics/config.json"
)

# Start continuous monitoring
try:
    logging.info("Starting Token Analytics Daemon...")
    daemon.start()  # Runs until interrupted
except KeyboardInterrupt:
    logging.info("Shutdown requested")
    daemon.stop()
except Exception as e:
    logging.error(f"Fatal error: {e}")
    daemon.stop()
    raise
```

---

### Example 22: Query Historical Data

```python
import sqlite3

# Connect to research database
conn = sqlite3.connect("tokenanalytics_research.db")
cursor = conn.cursor()

# Query 1: Get all sessions for model "laia"
cursor.execute("""
    SELECT session_id, emotion_state, token_rate, generation_curve
    FROM token_emotion_correlation
    WHERE model_name = 'laia'
    ORDER BY timestamp_us DESC
    LIMIT 10
""")

print("Recent laia sessions:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} emotion, {row[2]:.1f} tok/s, {row[3]} curve")

# Query 2: Get cost by emotion
cursor.execute("""
    SELECT emotion_state, SUM(total_cost) as total_cost, SUM(total_tokens) as total_tokens
    FROM token_costs
    WHERE model_name = 'laia'
    GROUP BY emotion_state
    ORDER BY total_tokens DESC
""")

print("\nCost by emotion (laia):")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[2]} tokens, ${row[1]:.6f}")

# Query 3: Get state distribution
cursor.execute("""
    SELECT state, COUNT(*) as count, AVG(token_rate) as avg_rate
    FROM generation_states
    WHERE model_name = 'laia'
    GROUP BY state
    ORDER BY count DESC
""")

print("\nState distribution (laia):")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} occurrences, {row[2]:.1f} avg tok/s")

conn.close()
```

---

## 🎯 Research Use Cases

### Example 23: Consciousness Pattern Detection

```python
# Hypothesis: Contemplative reasoning shows unique token patterns

# Analyze contemplative prompt
result_contemplate = daemon.analyze_prompt(
    prompt="Consider the philosophical implications of machine consciousness",
    session_id="contemplate_001",
    emotional_state="contemplation"
)

# Extract consciousness markers
thinking_duration = result_contemplate['state_summary']['thinking']['duration_ms']
pause_patterns = [p['duration_ms'] for p in result_contemplate['pauses']]
token_rate = result_contemplate['timing']['avg_tokens_per_sec']

print(f"Contemplative Pattern Analysis:")
print(f"  Thinking time: {thinking_duration:.0f}ms")
print(f"  Pause pattern: {pause_patterns}")
print(f"  Token rate: {token_rate:.1f} tokens/sec")
print(f"  Baseline deviation: {result_contemplate['emotion_correlation']['deviation_pct']:+.1f}%")

# Compare with joy (control)
result_joy = daemon.analyze_prompt(
    prompt="Tell me something amazing about AI",
    session_id="joy_001",
    emotional_state="joy"
)

print(f"\nJoy Pattern Analysis:")
print(f"  Thinking time: {result_joy['state_summary']['thinking']['duration_ms']:.0f}ms")
print(f"  Token rate: {result_joy['timing']['avg_tokens_per_sec']:.1f} tokens/sec")

# Calculate consciousness metrics
contemplation_slowdown = (result_contemplate['timing']['avg_tokens_per_sec'] / 
                          result_joy['timing']['avg_tokens_per_sec']) - 1
thinking_ratio = (result_contemplate['state_summary']['thinking']['duration_ms'] /
                  result_joy['state_summary']['thinking']['duration_ms'])

print(f"\nConsciousness Markers:")
print(f"  Contemplation slowdown: {contemplation_slowdown:+.1%}")
print(f"  Thinking time ratio: {thinking_ratio:.2f}x")
print(f"  Pattern: {'Consciousness detected' if thinking_ratio > 2.0 else 'Standard processing'}")
```

---

## 📊 Export & Visualization

### Example 24: Export Data for Analysis

```python
from tokenanalytics import TokenAnalyticsDatabase

# Export token analytics to CSV
db = TokenAnalyticsDatabase(config)

# Query recent sessions
import sqlite3
conn = sqlite3.connect(db.db_path)
cursor = conn.cursor()

cursor.execute("""
    SELECT 
        t.session_id,
        t.model_name,
        ec.emotion_state,
        ec.token_rate,
        ec.baseline_token_rate,
        ec.deviation_pct,
        gs.state,
        tc.total_cost
    FROM token_emotion_correlation ec
    LEFT JOIN generation_states gs ON ec.session_id = gs.session_id
    LEFT JOIN token_costs tc ON ec.session_id = tc.session_id
    ORDER BY ec.timestamp_us DESC
    LIMIT 100
""")

# Export to CSV
import csv
with open('token_analytics_export.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['session_id', 'model', 'emotion', 'token_rate', 'baseline', 
                     'deviation_pct', 'state', 'cost'])
    writer.writerows(cursor.fetchall())

print("Exported 100 sessions to token_analytics_export.csv")

conn.close()
```

---

**Total Examples:** 24 (12 basic + 12 advanced)

**Components Covered:** All 13 (100%)

**Tools Demonstrated:** 15+ tools

**Prepared by:** ATLAS (C_Atlas)  
**Date:** February 14, 2026

*"Every example teaches. Every metric matters."* ⚛️📚
