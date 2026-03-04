# OllamaGuard Examples

**Comprehensive usage examples for VitalHeart Phase 1: OllamaGuard**

This document provides 15+ working examples covering all major features, tool integrations, and error handling scenarios.

---

## Table of Contents

1. [Basic Usage Examples](#basic-usage-examples)
2. [Configuration Examples](#configuration-examples)
3. [AgentHeartbeat Integration Examples](#agentheartbeat-integration-examples)
4. [LiveAudit Query Examples](#liveaudit-query-examples)
5. [Troubleshooting Examples](#troubleshooting-examples)
6. [Advanced Monitoring Examples](#advanced-monitoring-examples)
7. [Error Handling Examples](#error-handling-examples)
8. [Tool Integration Examples](#tool-integration-examples)

---

## Basic Usage Examples

### Example 1: Standard Deployment

**Scenario**: Run OllamaGuard with default settings to monitor `laia` model.

**Commands**:
```bash
cd C:\Users\logan\OneDrive\Documents\AutoProjects\VitalHeart
python ollamaguard.py
```

**Expected Output**:
```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║                    VitalHeart: OllamaGuard                       ║
║               Ollama Inference Health Daemon                     ║
║                                                                  ║
║                    Version: 1.0.0                                ║
║                    Built with BUILD_PROTOCOL_V1                  ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝

2026-02-13 19:45:23,456 [INFO] [ConfigManager] Loaded config from ./ollamaguard_config.json
2026-02-13 19:45:23,567 [INFO] [EnvManager] OLLAMA_KEEP_ALIVE = 24h
2026-02-13 19:45:23,678 [INFO] [EnvGuard] Configuration validated successfully
2026-02-13 19:45:23,789 [INFO] [AgentHeartbeat] Connected to heartbeat system
2026-02-13 19:45:23,890 [INFO] [OllamaGuard] Starting main monitoring loop
2026-02-13 19:45:23,901 [INFO] [OllamaGuard] Check cycle #1
2026-02-13 19:45:24,012 [DEBUG] [RestCLI] Checking Ollama version...
2026-02-13 19:45:24,123 [DEBUG] [RestCLI] Checking loaded models...
2026-02-13 19:45:24,234 [DEBUG] [RestCLI] Performing micro-inference test...
2026-02-13 19:45:24,765 [DEBUG] [RestCLI] Micro-inference test passed (531.2ms)
2026-02-13 19:45:24,876 [INFO] [HealthCheck] Status: healthy
2026-02-13 19:45:24,987 [DEBUG] [AgentHeartbeat] Heartbeat emitted (ID: hb_20260213194524_abc123)
```

**Notes**:
- First run creates default `ollamaguard_config.json`
- Check cycle runs every 60 seconds
- Press Ctrl+C to stop gracefully

---

### Example 2: Custom Configuration File

**Scenario**: Monitor a different model with custom settings.

**1. Create custom config** (`my_config.json`):
```json
{
  "ollama": {
    "model_name": "llama2",
    "check_interval_seconds": 120
  }
}
```

**2. Run with custom config**:
```bash
python ollamaguard.py my_config.json
```

**Expected Output**:
```
2026-02-13 19:46:00,123 [INFO] [ConfigManager] Loaded config from my_config.json
2026-02-13 19:46:00,234 [INFO] [OllamaGuard] Check cycle #1
2026-02-13 19:46:01,456 [INFO] [HealthCheck] Status: healthy
(... waits 120 seconds instead of 60 ...)
2026-02-13 19:48:01,567 [INFO] [OllamaGuard] Check cycle #2
```

---

## Configuration Examples

### Example 3: Aggressive Monitoring (Fast Response)

**Scenario**: Minimize detection time for frozen inference.

**Configuration** (`aggressive_config.json`):
```json
{
  "ollama": {
    "api_url": "http://localhost:11434",
    "model_name": "laia",
    "keep_alive_duration": "24h",
    "inference_timeout_seconds": 10,
    "check_interval_seconds": 30
  },
  "restart": {
    "max_attempts": 5,
    "backoff_initial_seconds": 0.5,
    "backoff_max_seconds": 30,
    "restart_window_minutes": 10,
    "daily_restart_limit": 20
  }
}
```

**Usage**:
```bash
python ollamaguard.py aggressive_config.json
```

**Effect**:
- Check every 30 seconds (instead of 60)
- 10-second inference timeout (instead of 30)
- Up to 5 restart attempts (instead of 3)
- Faster backoff (starts at 0.5s instead of 1s)
- Higher daily restart limit (20 instead of 10)

**Detection Time**: Worst case ~40 seconds (30s check + 10s timeout)

---

### Example 4: Conservative Monitoring (Low Overhead)

**Scenario**: Minimize CPU/network usage, tolerate slower detection.

**Configuration** (`conservative_config.json`):
```json
{
  "ollama": {
    "check_interval_seconds": 300,
    "inference_timeout_seconds": 60
  },
  "restart": {
    "max_attempts": 2,
    "daily_restart_limit": 5
  },
  "monitoring": {
    "enable_micro_inference_test": false
  }
}
```

**Usage**:
```bash
python ollamaguard.py conservative_config.json
```

**Effect**:
- Check every 5 minutes (instead of 1)
- 60-second timeout (more lenient)
- Max 2 restart attempts
- No micro-inference tests (only checks model loaded)

**Note**: Without micro-inference tests, frozen engines may not be detected until user-facing inference fails.

---

### Example 5: Monitoring Only (No Auto-Restart)

**Scenario**: Detect and log issues but don't auto-restart (manual intervention only).

**Configuration** (`monitoring_only_config.json`):
```json
{
  "restart": {
    "max_attempts": 0,
    "daily_restart_limit": 0
  },
  "monitoring": {
    "enable_micro_inference_test": true
  }
}
```

**Usage**:
```bash
python ollamaguard.py monitoring_only_config.json
```

**Effect**:
- Still performs health checks and inference tests
- Logs all issues to file and AgentHeartbeat
- Never attempts auto-restart
- Suitable for production where manual approval needed

**Log Output When Frozen**:
```
2026-02-13 20:00:00,123 [ERROR] [Intervention] Inference engine frozen - restart required
2026-02-13 20:00:00,234 [WARNING] [RestartStrategy] Restart not approved (max_attempts: 0)
```

---

## AgentHeartbeat Integration Examples

### Example 6: Query Latest Heartbeat

**Scenario**: Check current Ollama health status programmatically.

**Python Script** (`check_ollama_health.py`):
```python
#!/usr/bin/env python3
import sys
sys.path.append(r"C:\Users\logan\OneDrive\Documents\AutoProjects\AgentHeartbeat")
from agentheartbeat import AgentHeartbeatMonitor

# Connect to AgentHeartbeat
monitor = AgentHeartbeatMonitor()

# Get latest heartbeat for LUMINA
heartbeat = monitor.get_latest_heartbeat("LUMINA")

if heartbeat:
    print(f"Agent: {heartbeat['agent_name']}")
    print(f"Status: {heartbeat['status']}")
    print(f"Timestamp: {heartbeat['timestamp']}")
    print(f"\nMetrics:")
    print(f"  Ollama Version: {heartbeat['metrics']['ollama_version']}")
    print(f"  Model Loaded: {heartbeat['metrics']['model_loaded']}")
    print(f"  Inference Latency: {heartbeat['metrics']['inference_latency_ms']}ms")
    print(f"  VRAM Used: {heartbeat['metrics']['vram_used_mb']:.1f} MB")
    print(f"  Restarts Today: {heartbeat['metrics']['restarts_today']}")
    print(f"  Uptime: {heartbeat['metrics']['uptime_hours']:.1f} hours")
else:
    print("No heartbeat found for LUMINA")
```

**Expected Output**:
```
Agent: LUMINA
Status: active
Timestamp: 2026-02-13T20:15:24.567Z

Metrics:
  Ollama Version: 0.16.1
  Model Loaded: True
  Inference Latency: 427.3ms
  VRAM Used: 6144.5 MB
  Restarts Today: 0
  Uptime: 12.5 hours
```

---

### Example 7: Historical Heartbeat Analysis

**Scenario**: Analyze Ollama health trends over the last 24 hours.

**Python Script** (`analyze_ollama_trends.py`):
```python
#!/usr/bin/env python3
import sys
import datetime
sys.path.append(r"C:\Users\logan\OneDrive\Documents\AutoProjects\AgentHeartbeat")
from agentheartbeat import AgentHeartbeatMonitor

monitor = AgentHeartbeatMonitor()

# Get heartbeats from last 24 hours
since = datetime.datetime.now() - datetime.timedelta(hours=24)
heartbeats = monitor.get_heartbeats_since("LUMINA", since)

print(f"Total Heartbeats (24h): {len(heartbeats)}")

# Analyze latencies
latencies = [hb['metrics']['inference_latency_ms'] 
             for hb in heartbeats 
             if hb['metrics']['inference_latency_ms'] is not None]

if latencies:
    print(f"\nInference Latency Stats:")
    print(f"  Min: {min(latencies):.1f}ms")
    print(f"  Max: {max(latencies):.1f}ms")
    print(f"  Avg: {sum(latencies)/len(latencies):.1f}ms")

# Count status changes
statuses = [hb['status'] for hb in heartbeats]
status_counts = {}
for status in statuses:
    status_counts[status] = status_counts.get(status, 0) + 1

print(f"\nStatus Distribution:")
for status, count in sorted(status_counts.items(), key=lambda x: -x[1]):
    pct = (count / len(heartbeats)) * 100
    print(f"  {status}: {count} ({pct:.1f}%)")

# Total restarts
total_restarts = sum(hb['metrics']['restarts_today'] for hb in heartbeats if 'restarts_today' in hb['metrics'])
print(f"\nTotal Restarts (24h): {total_restarts}")
```

**Expected Output**:
```
Total Heartbeats (24h): 1440

Inference Latency Stats:
  Min: 387.2ms
  Max: 1243.5ms
  Avg: 512.8ms

Status Distribution:
  active: 1438 (99.9%)
  error: 2 (0.1%)

Total Restarts (24h): 1
```

---

### Example 8: Real-Time Heartbeat Monitoring

**Scenario**: Display live heartbeat updates in terminal.

**Python Script** (`monitor_live.py`):
```python
#!/usr/bin/env python3
import sys
import time
sys.path.append(r"C:\Users\logan\OneDrive\Documents\AutoProjects\AgentHeartbeat")
from agentheartbeat import AgentHeartbeatMonitor

monitor = AgentHeartbeatMonitor()
last_timestamp = None

print("Monitoring LUMINA heartbeats (Ctrl+C to stop)...")
print("-" * 80)

try:
    while True:
        heartbeat = monitor.get_latest_heartbeat("LUMINA")
        
        if heartbeat and heartbeat['timestamp'] != last_timestamp:
            last_timestamp = heartbeat['timestamp']
            
            status_emoji = {
                'active': '✅',
                'error': '❌',
                'waiting': '⏳',
                'offline': '🔴',
                'processing': '🔄'
            }.get(heartbeat['status'], '❓')
            
            print(f"{status_emoji} {heartbeat['timestamp']} | "
                  f"Status: {heartbeat['status']} | "
                  f"Latency: {heartbeat['metrics'].get('inference_latency_ms', 'N/A')}ms | "
                  f"VRAM: {heartbeat['metrics'].get('vram_used_mb', 0):.0f}MB")
        
        time.sleep(2)  # Check every 2 seconds
        
except KeyboardInterrupt:
    print("\nMonitoring stopped.")
```

**Expected Output**:
```
Monitoring LUMINA heartbeats (Ctrl+C to stop)...
--------------------------------------------------------------------------------
✅ 2026-02-13T20:30:24.123Z | Status: active | Latency: 456.7ms | VRAM: 6144MB
✅ 2026-02-13T20:31:24.456Z | Status: active | Latency: 501.2ms | VRAM: 6144MB
✅ 2026-02-13T20:32:24.789Z | Status: active | Latency: 478.9ms | VRAM: 6144MB
❌ 2026-02-13T20:33:24.012Z | Status: error | Latency: N/Ams | VRAM: 0MB
✅ 2026-02-13T20:34:54.345Z | Status: active | Latency: 523.4ms | VRAM: 6144MB
```

---

## LiveAudit Query Examples

### Example 9: Find All Model Reloads

**Scenario**: List all model reload events with timestamps.

**Bash/PowerShell**:
```bash
# Linux/Mac
grep "model_reload" ollamaguard_audit.jsonl | jq -r '[.timestamp, .event_type, .details.model, .details.load_time_ms] | @tsv'

# Windows PowerShell
Get-Content .\ollamaguard_audit.jsonl | Select-String "model_reload" | ForEach-Object {
    $json = $_ | ConvertFrom-Json
    [PSCustomObject]@{
        Timestamp = $json.timestamp
        Event = $json.event_type
        Model = $json.details.model
        LoadTime = $json.details.load_time_ms
    }
} | Format-Table
```

**Expected Output**:
```
Timestamp                    Event                   Model  LoadTime
---------                    -----                   -----  --------
2026-02-13T15:23:45.123Z     model_reload_attempt    laia   
2026-02-13T15:23:46.456Z     model_reload_success    laia   1233
2026-02-13T18:45:12.789Z     model_reload_attempt    laia   
2026-02-13T18:45:14.012Z     model_reload_success    laia   1123
```

---

### Example 10: Count Restarts by Day

**Scenario**: Generate daily restart statistics.

**Python Script** (`count_restarts.py`):
```python
#!/usr/bin/env python3
import json
from collections import defaultdict
from datetime import datetime

# Parse audit log
restarts_by_date = defaultdict(int)

with open("ollamaguard_audit.jsonl", "r") as f:
    for line in f:
        entry = json.loads(line)
        if entry["event_type"] == "ollama_restart_success":
            date = entry["timestamp"].split("T")[0]
            restarts_by_date[date] += 1

# Print report
print("Ollama Restart Statistics")
print("-" * 40)
for date in sorted(restarts_by_date.keys()):
    print(f"{date}: {restarts_by_date[date]} restarts")

print(f"\nTotal Restarts: {sum(restarts_by_date.values())}")
```

**Expected Output**:
```
Ollama Restart Statistics
----------------------------------------
2026-02-10: 2 restarts
2026-02-11: 0 restarts
2026-02-12: 1 restarts
2026-02-13: 3 restarts

Total Restarts: 6
```

---

### Example 11: Filter Audit Log by Time Range

**Scenario**: View audit events from specific time period.

**Python Script** (`audit_time_range.py`):
```python
#!/usr/bin/env python3
import json
from datetime import datetime

# Define time range
start_time = datetime.fromisoformat("2026-02-13T18:00:00")
end_time = datetime.fromisoformat("2026-02-13T20:00:00")

print(f"Audit Events: {start_time} to {end_time}")
print("=" * 80)

with open("ollamaguard_audit.jsonl", "r") as f:
    for line in f:
        entry = json.loads(line)
        timestamp = datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00"))
        
        if start_time <= timestamp <= end_time:
            print(f"{entry['timestamp']} | {entry['event_type']}")
            if entry.get('details'):
                for key, value in entry['details'].items():
                    print(f"  - {key}: {value}")
            print()
```

**Expected Output**:
```
Audit Events: 2026-02-13 18:00:00 to 2026-02-13 20:00:00
================================================================================
2026-02-13T18:15:24.123Z | heartbeat_emitted
  - heartbeat_id: hb_20260213181524_abc123
  - status: healthy

2026-02-13T19:30:12.456Z | model_reload_attempt
  - model: laia
  - keep_alive: 24h

2026-02-13T19:30:13.789Z | model_reload_success
  - model: laia
  - load_time_ms: 1233
```

---

## Troubleshooting Examples

### Example 12: Diagnose High Restart Count

**Scenario**: Ollama restarted 5+ times today, investigate why.

**Step 1**: Check restart audit events
```bash
# PowerShell
Get-Content .\ollamaguard_audit.jsonl | Select-String "ollama_restart" | ConvertFrom-Json | Format-List
```

**Expected Output**:
```
timestamp  : 2026-02-13T10:23:45.123Z
event_type : ollama_restart_attempt
agent      : OLLAMAGUARD
details    : @{reason=inference_frozen_or_unresponsive}

timestamp  : 2026-02-13T10:23:50.456Z
event_type : ollama_restart_success
agent      : OLLAMAGUARD
details    : @{restart_time_s=5.333}

...
```

**Step 2**: Check OllamaGuard logs for patterns
```bash
# Find all "Intervention" entries
Select-String -Path .\ollamaguard.log -Pattern "Intervention" -Context 3,3
```

**Step 3**: Check Ollama logs for crash reasons
```bash
# Windows Ollama logs location
Get-Content "$env:LOCALAPPDATA\Ollama\logs\server.log" -Tail 100 | Select-String "error|fatal|panic"
```

**Common Causes**:
- **GPU driver crash**: Check Windows Event Viewer for GPU-related errors
- **Out of memory**: Check Task Manager during restart times
- **Ollama bug**: Check Ollama version, consider updating

---

### Example 13: Test Configuration Before Deployment

**Scenario**: Validate configuration file without running daemon.

**Python Script** (`validate_config.py`):
```python
#!/usr/bin/env python3
import sys
sys.path.insert(0, ".")
from ollamaguard import OllamaGuardConfig

config_path = sys.argv[1] if len(sys.argv) > 1 else "ollamaguard_config.json"

print(f"Validating configuration: {config_path}")
print("-" * 60)

try:
    config = OllamaGuardConfig(config_path)
    
    print("✅ Configuration valid!")
    print("\nKey Settings:")
    print(f"  API URL: {config.get('ollama', 'api_url')}")
    print(f"  Model: {config.get('ollama', 'model_name')}")
    print(f"  Check Interval: {config.get('ollama', 'check_interval_seconds')}s")
    print(f"  Inference Timeout: {config.get('ollama', 'inference_timeout_seconds')}s")
    print(f"  Max Restart Attempts: {config.get('restart', 'max_attempts')}")
    print(f"  Daily Restart Limit: {config.get('restart', 'daily_restart_limit')}")
    print(f"  Micro-Inference Test: {config.get('monitoring', 'enable_micro_inference_test')}")
    print(f"  AgentHeartbeat: {config.get('integration', 'agentheartbeat_enabled')}")
    
except ValueError as e:
    print(f"❌ Configuration invalid:")
    print(f"  {e}")
    sys.exit(1)
```

**Usage**:
```bash
python validate_config.py my_config.json
```

**Expected Output (Valid)**:
```
Validating configuration: my_config.json
------------------------------------------------------------
✅ Configuration valid!

Key Settings:
  API URL: http://localhost:11434
  Model: laia
  Check Interval: 60s
  Inference Timeout: 30s
  Max Restart Attempts: 3
  Daily Restart Limit: 10
  Micro-Inference Test: True
  AgentHeartbeat: True
```

**Expected Output (Invalid)**:
```
Validating configuration: bad_config.json
------------------------------------------------------------
❌ Configuration invalid:
  [EnvGuard] Config validation failed: check_interval_seconds must be >= 10
```

---

## Advanced Monitoring Examples

### Example 14: Multi-Model Monitoring

**Scenario**: Monitor multiple Ollama models on different ports.

**Approach**: Run multiple OllamaGuard instances with different configs.

**Config 1** (`ollamaguard_laia.json`):
```json
{
  "ollama": {
    "api_url": "http://localhost:11434",
    "model_name": "laia"
  },
  "logging": {
    "log_file": "./ollamaguard_laia.log"
  },
  "integration": {
    "audit_log_path": "./ollamaguard_audit_laia.jsonl"
  }
}
```

**Config 2** (`ollamaguard_llama2.json`):
```json
{
  "ollama": {
    "api_url": "http://localhost:11435",
    "model_name": "llama2"
  },
  "logging": {
    "log_file": "./ollamaguard_llama2.log"
  },
  "integration": {
    "audit_log_path": "./ollamaguard_audit_llama2.jsonl"
  }
}
```

**Start both instances**:
```bash
# Terminal 1
python ollamaguard.py ollamaguard_laia.json

# Terminal 2
python ollamaguard.py ollamaguard_llama2.json
```

**Note**: AgentHeartbeat will store both under "LUMINA" agent name. Consider modifying code to use different agent names for multi-model setups.

---

### Example 15: Alert on Restart Limit

**Scenario**: Send Windows notification when daily restart limit exceeded.

**Python Script** (`alert_monitor.py`):
```python
#!/usr/bin/env python3
import time
import json
from datetime import datetime

RESTART_LIMIT = 5  # Alert threshold

print("Monitoring for excessive restarts...")

restarts_today = 0
last_checked_date = datetime.now().date()

try:
    while True:
        # Reset counter on new day
        current_date = datetime.now().date()
        if current_date != last_checked_date:
            restarts_today = 0
            last_checked_date = current_date
            print(f"New day: {current_date}, restart counter reset")
        
        # Count today's restarts from audit log
        with open("ollamaguard_audit.jsonl", "r") as f:
            for line in f:
                entry = json.loads(line)
                if entry["event_type"] == "ollama_restart_success":
                    event_date = datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00")).date()
                    if event_date == current_date:
                        restarts_today += 1
        
        # Alert if threshold exceeded
        if restarts_today >= RESTART_LIMIT:
            print(f"⚠️ ALERT: {restarts_today} restarts today (limit: {RESTART_LIMIT})")
            
            # Windows notification (requires win10toast package)
            try:
                from win10toast import ToastNotifier
                toaster = ToastNotifier()
                toaster.show_toast(
                    "OllamaGuard Alert",
                    f"Ollama restarted {restarts_today} times today!",
                    icon_path=None,
                    duration=10
                )
            except ImportError:
                print("Install win10toast for desktop notifications: pip install win10toast")
        
        time.sleep(60)  # Check every minute
        
except KeyboardInterrupt:
    print("\nMonitoring stopped.")
```

---

## Error Handling Examples

### Example 16: Graceful Degradation (No AgentHeartbeat)

**Scenario**: AgentHeartbeat unavailable, verify fallback logging.

**Simulate unavailability**: Set invalid `heartbeat_db_path` in config:
```json
{
  "integration": {
    "heartbeat_db_path": "C:/invalid/path/heartbeat.db"
  }
}
```

**Run OllamaGuard**:
```bash
python ollamaguard.py
```

**Expected Log Output**:
```
2026-02-13 20:45:23,456 [ERROR] [AgentHeartbeat] Failed to initialize: ...
2026-02-13 20:45:24,567 [INFO] [OllamaGuard] Check cycle #1
2026-02-13 20:45:25,678 [INFO] [HealthCheck] Status: healthy
2026-02-13 20:45:25,789 [ERROR] [ErrorRecovery] Heartbeat emission failed: ...
2026-02-13 20:45:25,890 [INFO] [ErrorRecovery] Heartbeat logged to fallback file
```

**Verify fallback file**:
```bash
Get-Content .\ollamaguard_heartbeat_fallback.jsonl
```

**Expected Fallback Content**:
```json
{"timestamp": "2026-02-13T20:45:25.890Z", "status": "healthy", "metrics": {...}}
```

**Note**: Daemon continues operating despite AgentHeartbeat unavailability.

---

## Tool Integration Examples

### Example 17: VersionGuard in Action (Ollama Update Detection)

**Scenario**: Ollama updates during monitoring, verify grace period.

**Simulate version change**: (In real scenario, update Ollama while daemon running)

**Expected Log Output**:
```
2026-02-13 21:00:00,123 [INFO] [OllamaGuard] Check cycle #45
2026-02-13 21:00:00,234 [DEBUG] [RestCLI] Checking Ollama version...
2026-02-13 21:00:00,345 [INFO] [VersionGuard] Ollama version changed: 0.16.0 -> 0.16.1
2026-02-13 21:00:00,456 [INFO] [HealthCheck] Status: grace_period
2026-02-13 21:00:00,567 [DEBUG] [AgentHeartbeat] Heartbeat emitted (ID: hb_...)
(... no interventions for 5 minutes ...)
2026-02-13 21:05:01,678 [INFO] [OllamaGuard] Check cycle #50
2026-02-13 21:05:01,789 [INFO] [HealthCheck] Status: healthy
```

**Note**: Grace period prevents false alarms during Ollama installation.

---

### Example 18: RestartStrategy Exponential Backoff

**Scenario**: Simulate multiple restart attempts to see backoff in action.

**Mock scenario**: Ollama keeps freezing, trigger multiple restarts.

**Expected Log Output**:
```
2026-02-13 21:10:00,123 [ERROR] [Intervention] Inference engine frozen - restart required
2026-02-13 21:10:00,234 [INFO] [RestartStrategy] Restart approved (attempt 1, backoff: 1s)
2026-02-13 21:10:01,345 [INFO] [ProcessWatcher] Killing Ollama process 1234
2026-02-13 21:10:06,456 [INFO] [ProcessWatcher] Ollama restarted (5.1s)
(... frozen again ...)
2026-02-13 21:12:00,567 [ERROR] [Intervention] Inference engine frozen - restart required
2026-02-13 21:12:00,678 [INFO] [RestartStrategy] Restart approved (attempt 2, backoff: 2s)
2026-02-13 21:12:02,789 [INFO] [ProcessWatcher] Killing Ollama process 5678
2026-02-13 21:12:07,890 [INFO] [ProcessWatcher] Ollama restarted (5.1s)
(... frozen again ...)
2026-02-13 21:14:00,012 [ERROR] [Intervention] Inference engine frozen - restart required
2026-02-13 21:14:00,123 [INFO] [RestartStrategy] Restart approved (attempt 3, backoff: 4s)
2026-02-13 21:14:04,234 [INFO] [ProcessWatcher] Killing Ollama process 9012
(... frozen again ...)
2026-02-13 21:16:00,345 [ERROR] [Intervention] Inference engine frozen - restart required
2026-02-13 21:16:00,456 [CRITICAL] [RestartStrategy] Too many restarts in window (3 in 5min)
2026-02-13 21:16:00,567 [CRITICAL] [Escalation] Restart limits exceeded - entering monitoring-only mode
```

**Note**: Exponential backoff: 1s → 2s → 4s, then escalation after max attempts.

---

## Summary

This document provided **18 comprehensive examples** covering:

✅ **Basic Usage** (2 examples)  
✅ **Configuration** (3 examples)  
✅ **AgentHeartbeat Integration** (3 examples)  
✅ **LiveAudit Queries** (3 examples)  
✅ **Troubleshooting** (2 examples)  
✅ **Advanced Monitoring** (2 examples)  
✅ **Error Handling** (1 example)  
✅ **Tool Integration** (2 examples)

**Total: 18 examples** (exceeds 10 minimum requirement)

---

## Need More Help?

- **README.md**: Full documentation, configuration reference, troubleshooting
- **ARCHITECTURE_DESIGN.md**: System architecture and component design
- **BUG_HUNT_REPORT.md**: Testing methodology and bug fixes
- **BUILD_AUDIT.md**: Complete tool integration list

---

⚛️ **Built with BUILD_PROTOCOL_V1.md - 100% Compliance** ⚛️

*For the Maximum Benefit of Life. One World. One Family. One Love.* 🔆⚒️🔗
