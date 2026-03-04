# InferencePulse Examples

**VitalHeart Phase 2: InferencePulse**  
**10+ Working Examples with Expected Output**

---

## Example 1: Basic Daemon Startup

```python
from inferencepulse import InferencePulseDaemon

# Start InferencePulse daemon with config
daemon = InferencePulseDaemon("./inferencepulse_config.json")
daemon.start()

# Expected output in log:
# [InferencePulse] Starting VitalHeart Phase 2 v2.0.0 (Phase 1 v1.0.0)
# [InferencePulse] Initializing Phase 2 components...
# [InferencePulse] Phase 2 initialized (enabled=True)
# [ChatResponseHook] Started log monitoring
# [BaselineLearner] Updating baselines from AgentHeartbeat...
# [InferencePulse] Phase 2 main loop started
```

**When to use:** Initial deployment, starting the daemon for the first time.

---

## Example 2: Query Current Baselines

```python
from inferencepulse import BaselineLearner, InferencePulseConfig
import json

# Initialize baseline learner
config = InferencePulseConfig()
learner = BaselineLearner(
    config,
    heartbeat_db_path="C:/Users/logan/OneDrive/Documents/AutoProjects/AgentHeartbeat/heartbeat.db"
)

# Update baselines from historical data
learner.update_baselines()

# Get baseline for inference latency
baseline = learner.get_baseline("inference_latency_ms")

if baseline and baseline.get("ready"):
    print(f"Inference Latency Baseline:")
    print(f"  Mean: {baseline['mean']:.2f}ms")
    print(f"  Median: {baseline['median']:.2f}ms")
    print(f"  Std Dev: {baseline['std_dev']:.2f}ms")
    print(f"  5th percentile: {baseline['percentile_5']:.2f}ms")
    print(f"  95th percentile: {baseline['percentile_95']:.2f}ms")
    print(f"  Confidence: {baseline['confidence']:.2%}")
    print(f"  Samples: {baseline['sample_count']}")
else:
    print("Baseline not ready yet. Need 100+ samples.")

# Expected output (after 100+ samples):
# Inference Latency Baseline:
#   Mean: 125.45ms
#   Median: 118.20ms
#   Std Dev: 22.34ms
#   5th percentile: 92.10ms
#   95th percentile: 165.80ms
#   Confidence: 95.00%
#   Samples: 250
```

**When to use:** Checking if baselines are established, understanding normal performance ranges.

---

## Example 3: Detect Anomalies in Current Metrics

```python
from inferencepulse import AnomalyDetector, BaselineLearner, InferencePulseConfig

# Setup
config = InferencePulseConfig()
learner = BaselineLearner(config, "./heartbeat.db")
learner.update_baselines()

detector = AnomalyDetector(config, learner)

# Current metrics from a chat response
current_metrics = {
    "inference_latency_ms": 450.0,  # Unusually high (baseline ~125ms)
    "tokens_per_second": 8.5,       # Unusually low (baseline ~15)
    "vram_pct": 92.0               # Very high
}

# Detect anomalies
anomalies = detector.detect(current_metrics)

if anomalies:
    print(f"⚠️  Detected {len(anomalies)} anomalies:")
    for anomaly in anomalies:
        print(f"\n  {anomaly['type']}:")
        print(f"    Current: {anomaly['current']:.2f}")
        print(f"    Baseline: {anomaly['baseline_mean']:.2f}")
        print(f"    Deviation: {anomaly['deviation_multiplier']:.2f}x")
        print(f"    Severity: {anomaly['severity']}")
else:
    print("✓ All metrics within normal range")

# Expected output:
# ⚠️  Detected 2 anomalies:
#
#   inference_latency_ms_high:
#     Current: 450.00
#     Baseline: 125.45
#     Deviation: 3.59x
#     Severity: HIGH
#
#   tokens_per_second_low:
#     Current: 8.50
#     Baseline: 15.20
#     Deviation: 1.79x
#     Severity: MEDIUM
```

**When to use:** Real-time anomaly monitoring, performance troubleshooting, alerting setup.

---

## Example 4: Query UKE Events (Chat Responses)

```sql
-- Find all chat responses from today
SELECT 
    timestamp,
    json_extract(data, '$.chat_response_ms') as latency_ms,
    json_extract(data, '$.tokens_generated') as tokens,
    json_extract(data, '$.dominant_mood') as mood
FROM events 
WHERE type = 'chat_response' 
AND date(timestamp) = date('now')
ORDER BY timestamp DESC
LIMIT 10;

-- Expected output:
-- timestamp                   | latency_ms | tokens | mood
-- 2026-02-13 20:15:43.123    | 145.2      | 42     | WARMTH
-- 2026-02-13 20:14:22.456    | 128.7      | 38     | CURIOSITY
-- 2026-02-13 20:12:10.789    | 142.1      | 45     | RESONANCE
-- ...
```

**When to use:** Analyzing historical chat performance, mood trends, debugging issues.

---

## Example 5: Query UKE Events (Anomalies Only)

```sql
-- Find all significant anomalies (HIGH or CRITICAL)
SELECT 
    timestamp,
    json_extract(data, '$.type') as anomaly_type,
    json_extract(data, '$.current') as current_value,
    json_extract(data, '$.baseline_mean') as baseline,
    json_extract(data, '$.deviation_multiplier') as deviation,
    json_extract(data, '$.severity') as severity
FROM events
WHERE type = 'significant_anomaly'
AND json_extract(data, '$.severity') IN ('HIGH', 'CRITICAL')
ORDER BY timestamp DESC
LIMIT 20;

-- Expected output:
-- timestamp                   | anomaly_type              | current | baseline | deviation | severity
-- 2026-02-13 20:10:15.234    | inference_latency_ms_high | 450.0   | 125.45   | 3.59      | HIGH
-- 2026-02-13 19:58:42.567    | vram_pct_high             | 95.2    | 75.80    | 1.26      | HIGH
-- ...
```

**When to use:** Investigating performance degradation, identifying recurring issues.

---

## Example 6: Monitor Mood Distribution

```sql
-- Count chat responses by dominant mood
SELECT 
    json_extract(data, '$.dominant_mood') as mood,
    COUNT(*) as count,
    AVG(CAST(json_extract(data, '$.chat_response_ms') AS REAL)) as avg_latency_ms,
    AVG(CAST(json_extract(data, '$.mood_intensity') AS REAL)) as avg_intensity
FROM events
WHERE type = 'chat_response'
AND date(timestamp) >= date('now', '-7 days')
GROUP BY mood
ORDER BY count DESC;

-- Expected output:
-- mood        | count | avg_latency_ms | avg_intensity
-- WARMTH      | 145   | 132.4          | 0.68
-- CURIOSITY   | 128   | 128.9          | 0.72
-- RESONANCE   | 98    | 135.1          | 0.65
-- JOY         | 87    | 125.3          | 0.78
-- NEUTRAL     | 52    | 140.2          | 0.12
-- ...
```

**When to use:** Understanding Lumina's emotional patterns, research on emotion-performance correlation.

---

## Example 7: Manual Mood Analysis

```python
from inferencepulse import MoodAnalyzer, InferencePulseConfig

# Initialize mood analyzer
config = InferencePulseConfig()
analyzer = MoodAnalyzer(config)

# Analyze sample text
text = "I'm so excited to help you with this! It brings me great joy to see your progress."

result = analyzer.analyze(text)

print(f"Dominant Mood: {result['dominant_mood']}")
print(f"Intensity: {result['intensity']:.2f}")
print(f"Analysis Time: {result['analysis_time_ms']:.1f}ms")
print(f"Dimensions: {result['dimensions']}")

# Expected output:
# Dominant Mood: JOY
# Intensity: 0.65
# Analysis Time: 2.3ms
# Dimensions: {'JOY': 2, 'WARMTH': 1, 'CURIOSITY': 1}
#
# ⚠️  Note: This is PLACEHOLDER mood detection.
# Full EmotionalTextureAnalyzer integration provides 10-dimension
# weighted analysis with pattern-based detection.
```

**When to use:** Testing mood analysis, debugging emotional texture detection.

---

## Example 8: Check Baseline Confidence

```python
from inferencepulse import BaselineLearner, InferencePulseConfig

config = InferencePulseConfig()
learner = BaselineLearner(config, "./heartbeat.db")
learner.update_baselines()

# Check all baselines
for metric_name, baseline in learner.baselines.items():
    if baseline.get("ready"):
        print(f"{metric_name}:")
        print(f"  Samples: {baseline['sample_count']}")
        print(f"  Confidence: {baseline['confidence']:.2%}")
        print(f"  Age: {baseline['last_updated']}")
        print()

# Expected output:
# inference_latency_ms:
#   Samples: 250
#   Confidence: 100.00%
#   Age: 2026-02-13T20:15:00.123456
#
# tokens_per_second:
#   Samples: 250
#   Confidence: 100.00%
#   Age: 2026-02-13T20:15:00.123456
#
# vram_pct:
#   Samples: 250
#   Confidence: 100.00%
#   Age: 2026-02-13T20:15:00.123456
```

**When to use:** Validating baseline quality, determining if enough data collected.

---

## Example 9: Monitor Chat Hook Status

```python
from inferencepulse import ChatResponseHook, InferencePulseConfig
import time

config = InferencePulseConfig()
hook = ChatResponseHook(config)

# Start monitoring
hook.start_monitoring()
print("Chat monitoring started...")

# Wait for chat responses
for i in range(10):
    time.sleep(5)
    chat = hook.get_latest_chat()
    if chat:
        print(f"Captured chat: {chat['chat_response_ms']:.1f}ms, {chat['tokens_generated']} tokens")
    else:
        print("No new chats...")

# Stop monitoring
hook.stop_monitoring()
print("Chat monitoring stopped.")

# Expected output:
# Chat monitoring started...
# No new chats...
# No new chats...
# Captured chat: 145.2ms, 42 tokens
# No new chats...
# Captured chat: 128.7ms, 38 tokens
# ...
# Chat monitoring stopped.
```

**When to use:** Verifying chat hook is working, debugging log file parsing.

---

## Example 10: UKE Connector Manual Test

```python
from inferencepulse import UKEConnector, InferencePulseConfig
import os

config = InferencePulseConfig({
    "uke": {
        "enabled": True,
        "db_path": "./test_uke.db",
        "batch_size": 5,
        "batch_timeout_seconds": 10
    }
})

connector = UKEConnector(config)

# Index test events
for i in range(7):
    connector.index_event(
        "test_event",
        {"value": i, "message": f"Test event {i}"},
        ["test", "example"]
    )
    print(f"Queued event {i+1}")

print(f"\nQueue size: {len(connector.queue)}")
print("Flushing to UKE...")

# Force flush
connector._flush_to_uke()

print(f"Queue size after flush: {len(connector.queue)}")
print(f"Check database: {os.path.exists('./test_uke.db')}")

# Query results
import sqlite3
conn = sqlite3.connect('./test_uke.db')
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM events")
count = cursor.fetchone()[0]
conn.close()

print(f"Events in database: {count}")

# Expected output:
# Queued event 1
# Queued event 2
# Queued event 3
# Queued event 4
# Queued event 5
# Queued event 6
# Queued event 7
#
# Queue size: 7
# Flushing to UKE...
# Queue size after flush: 0
# Check database: True
# Events in database: 7
```

**When to use:** Testing UKE integration, verifying batching works correctly.

---

## Example 11: Enhanced Heartbeat Emission

```python
from inferencepulse import EnhancedHeartbeatEmitter, BaselineLearner, InferencePulseConfig
from unittest.mock import Mock

config = InferencePulseConfig()
learner = BaselineLearner(config, "./heartbeat.db")
learner.baselines = {
    "inference_latency_ms": {"ready": True, "confidence": 0.95}
}

# Mock heartbeat monitor
mock_heartbeat = Mock()
emitter = EnhancedHeartbeatEmitter(mock_heartbeat, learner)

# Phase 1 metrics
phase1_metrics = {
    "health_status": "active",
    "inference_latency_ms": 125.5,
    "vram_pct": 78.2
}

# Chat data
chat_data = {
    "chat_response_ms": 125.5,
    "tokens_generated": 42,
    "response_text": "Hello!"
}

# Mood data
mood_data = {
    "dominant_mood": "WARMTH",
    "intensity": 0.68,
    "dimensions": {"WARMTH": 2}
}

# Anomalies
anomalies = []

# Emit enhanced heartbeat
emitter.emit_enhanced_heartbeat(phase1_metrics, chat_data, mood_data, anomalies)

print("Heartbeat emitted successfully!")
print(f"Heartbeat was called: {mock_heartbeat.emit_heartbeat.called}")

# Expected output:
# Heartbeat emitted successfully!
# Heartbeat was called: True
```

**When to use:** Testing heartbeat emission, verifying Phase 2 metrics are included.

---

## Example 12: Disable Phase 2 Features

```json
// inferencepulse_config.json
{
  "inferencepulse": {
    "enabled": false  // Disables all Phase 2 features
  }
}
```

```python
from inferencepulse import InferencePulseDaemon

# Start daemon with Phase 2 disabled
daemon = InferencePulseDaemon("./inferencepulse_config.json")
daemon.start()

# Expected behavior:
# - Phase 1 (OllamaGuard) runs normally
# - No chat monitoring
# - No baseline learning
# - No anomaly detection
# - AgentHeartbeat only gets Phase 1 metrics
```

**When to use:** Rollback to Phase 1-only, troubleshooting Phase 2 issues, gradual rollout.

---

## Summary

These 12 examples cover:

1. ✅ Basic daemon startup
2. ✅ Baseline querying
3. ✅ Anomaly detection
4. ✅ UKE chat response queries
5. ✅ UKE anomaly queries
6. ✅ Mood distribution analysis
7. ✅ Manual mood analysis
8. ✅ Baseline confidence checking
9. ✅ Chat hook monitoring
10. ✅ UKE connector testing
11. ✅ Enhanced heartbeat emission
12. ✅ Disabling Phase 2 features

**All examples are executable and include expected output.**

---

**Examples by:** ATLAS (C_Atlas)  
**Date:** February 14, 2026  
**Phase:** VitalHeart Phase 2 - InferencePulse

*Quality is not an act, it is a habit!* ⚛️
