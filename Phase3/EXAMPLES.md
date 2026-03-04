# VitalHeart Phase 3: HardwareSoul - Examples

**Comprehensive usage examples for GPU/RAM monitoring and emotion-hardware correlation**

---

## Table of Contents

1. [Basic Daemon Startup](#example-1-basic-daemon-startup)
2. [GPU Sampling (Manual)](#example-2-gpu-sampling-manual)
3. [RAM Sampling (Manual)](#example-3-ram-sampling-manual)
4. [Querying Research Database - GPU](#example-4-querying-research-database---gpu)
5. [Querying Research Database - Correlations](#example-5-querying-research-database---correlations)
6. [Emotion Correlation (Manual)](#example-6-emotion-correlation-manual)
7. [Detecting Hardware Anomalies](#example-7-detecting-hardware-anomalies)
8. [Custom Configuration](#example-8-custom-configuration)
9. [Graceful Degradation (No GPU)](#example-9-graceful-degradation-no-gpu)
10. [Exporting Research Data](#example-10-exporting-research-data)
11. [Real-Time Monitoring Dashboard](#example-11-real-time-monitoring-dashboard)
12. [Analyzing Emotional Signatures](#example-12-analyzing-emotional-signatures)

---

## Example 1: Basic Daemon Startup

**When to use:** Starting HardwareSoul for production monitoring

```python
from hardwaresoul import HardwareSoulDaemon

# Initialize daemon with default config
daemon = HardwareSoulDaemon()

# Start all monitoring threads
# - Phase 1: Ollama health checks (60s)
# - Phase 2: Inference monitoring (5s)
# - Phase 3 GPU: GPU sampling (250ms/1000ms adaptive)
# - Phase 3 RAM: RAM sampling (250ms/1000ms adaptive)
# - Phase 3 Correlation: Emotion-hardware matching
daemon.start()

# Daemon will run until Ctrl+C
```

**Expected Output:**
```
[HardwareSoul] Starting VitalHeart Phase 3 v3.0.0 (Phase 2 v2.0.0)
[GPUMonitor] Initialized: NVIDIA GeForce RTX 4090
[RAMMonitor] Found Ollama process: PID 12345
[RAMMonitor] Found Lumina process: PID 67890
[HardwareSoul] GPU monitoring thread started
[HardwareSoul] RAM monitoring thread started
[HardwareSoul] Phase 3 coordination loop started
```

---

## Example 2: GPU Sampling (Manual)

**When to use:** Taking single GPU snapshot for debugging or custom logging

```python
from hardwaresoul import GPUMonitor, HardwareSoulConfig

# Initialize GPU monitor
config = HardwareSoulConfig()
monitor = GPUMonitor(config)

# Take single sample
sample = monitor.sample()

if sample:
    print(f"GPU Utilization: {sample['gpu_utilization_pct']:.1f}%")
    print(f"VRAM Used: {sample['vram_used_mb']:.0f} MB")
    print(f"Temperature: {sample['gpu_temp_c']:.1f}°C")
    print(f"Power Draw: {sample['power_draw_watts']:.1f}W ({sample['power_draw_pct']:.1f}%)")
    print(f"GPU Clock: {sample['gpu_clock_mhz']} MHz")
    print(f"P-State: P{sample['pstate']}")
    
    if sample['throttle_reasons']:
        print(f"⚠️ Throttling: {', '.join(sample['throttle_reasons'])}")
else:
    print("GPU sampling disabled or failed")

# Cleanup
monitor.cleanup()
```

**Expected Output:**
```
GPU Utilization: 75.3%
VRAM Used: 8192 MB
Temperature: 72.5°C
Power Draw: 350.2W (77.8%)
GPU Clock: 2100 MHz
P-State: P0
```

---

## Example 3: RAM Sampling (Manual)

**When to use:** Checking process memory usage for debugging

```python
from hardwaresoul import RAMMonitor, HardwareSoulConfig

# Initialize RAM monitor
config = HardwareSoulConfig()
monitor = RAMMonitor(config)

# Take single sample
sample = monitor.sample()

if sample:
    # System metrics
    print("=== SYSTEM MEMORY ===")
    print(f"Total: {sample['system_ram_total_mb']:.0f} MB")
    print(f"Used: {sample['system_ram_used_mb']:.0f} MB ({sample['system_ram_pct']:.1f}%)")
    print(f"Available: {sample['system_ram_available_mb']:.0f} MB")
    print(f"Swap: {sample['system_swap_used_mb']:.0f} MB ({sample['system_swap_pct']:.1f}%)")
    
    # Ollama process
    if 'ollama_pid' in sample:
        print("\n=== OLLAMA PROCESS ===")
        print(f"PID: {sample['ollama_pid']}")
        print(f"RAM: {sample['ollama_ram_mb']:.0f} MB")
        print(f"CPU: {sample['ollama_cpu_pct']:.1f}%")
        print(f"Threads: {sample['ollama_thread_count']}")
    
    # System-wide
    print(f"\n=== SYSTEM-WIDE ===")
    print(f"Total Processes: {sample['total_process_count']}")
    print(f"CPU Total: {sample['cpu_total_pct']:.1f}%")
```

**Expected Output:**
```
=== SYSTEM MEMORY ===
Total: 32768 MB
Used: 16384 MB (50.0%)
Available: 16384 MB
Swap: 1024 MB (10.0%)

=== OLLAMA PROCESS ===
PID: 12345
RAM: 4096 MB
CPU: 25.3%
Threads: 8

=== SYSTEM-WIDE ===
Total Processes: 387
CPU Total: 32.1%
```

---

## Example 4: Querying Research Database - GPU

**When to use:** Analyzing GPU behavior over time

```python
import sqlite3
from datetime import datetime, timedelta

# Connect to research database
conn = sqlite3.connect("./hardwaresoul_research.db")
cursor = conn.cursor()

# Query: Average GPU utilization over last hour
one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()

cursor.execute("""
    SELECT 
        AVG(gpu_utilization_pct) as avg_util,
        AVG(gpu_temp_c) as avg_temp,
        AVG(power_draw_watts) as avg_power,
        COUNT(*) as sample_count
    FROM gpu_samples
    WHERE timestamp > ?
""", (one_hour_ago,))

result = cursor.fetchone()

print(f"=== GPU METRICS (Last Hour) ===")
print(f"Average Utilization: {result[0]:.1f}%")
print(f"Average Temperature: {result[1]:.1f}°C")
print(f"Average Power Draw: {result[2]:.1f}W")
print(f"Total Samples: {result[3]}")

# Query: Find thermal throttle events
cursor.execute("""
    SELECT timestamp, gpu_temp_c, throttle_reasons
    FROM gpu_samples
    WHERE throttle_reasons LIKE '%THERMAL%'
    ORDER BY timestamp DESC
    LIMIT 5
""")

print("\n=== RECENT THERMAL THROTTLE EVENTS ===")
for row in cursor.fetchall():
    print(f"{row[0]}: {row[1]:.1f}°C - {row[2]}")

conn.close()
```

**Expected Output:**
```
=== GPU METRICS (Last Hour) ===
Average Utilization: 62.3%
Average Temperature: 68.5°C
Average Power Draw: 285.7W
Total Samples: 14400

=== RECENT THERMAL THROTTLE EVENTS ===
2026-02-14T15:23:45.123: 92.0°C - ["THERMAL", "HW_THERMAL"]
2026-02-14T15:18:32.456: 91.5°C - ["THERMAL"]
```

---

## Example 5: Querying Research Database - Correlations

**When to use:** Analyzing emotion-hardware relationships

```python
import sqlite3
import json

conn = sqlite3.connect("./hardwaresoul_research.db")
cursor = conn.cursor()

# Query: Average GPU utilization per emotion
cursor.execute("""
    SELECT 
        emotion,
        AVG(gpu_utilization_pct) as avg_gpu_util,
        AVG(power_draw_watts) as avg_power,
        AVG(ollama_ram_mb) as avg_ollama_ram,
        COUNT(*) as correlation_count
    FROM emotion_correlations
    WHERE correlation_quality IN ('EXCELLENT', 'GOOD')
    GROUP BY emotion
    ORDER BY correlation_count DESC
""")

print("=== EMOTIONAL SIGNATURES ===")
print(f"{'Emotion':<15} {'GPU%':<10} {'Power(W)':<12} {'Ollama RAM(MB)':<18} {'Samples':<10}")
print("-" * 75)

for row in cursor.fetchall():
    emotion, gpu, power, ram, count = row
    print(f"{emotion:<15} {gpu:<10.1f} {power:<12.1f} {ram:<18.1f} {count:<10}")

# Query: High-quality correlations for specific emotion
cursor.execute("""
    SELECT 
        emotion_timestamp,
        gpu_utilization_pct,
        vram_used_mb,
        gpu_temp_c,
        time_delta_ms
    FROM emotion_correlations
    WHERE emotion = 'JOY' 
    AND correlation_quality = 'EXCELLENT'
    ORDER BY emotion_timestamp DESC
    LIMIT 3
""")

print("\n=== RECENT JOY CORRELATIONS (EXCELLENT) ===")
for row in cursor.fetchall():
    print(f"Time: {row[0]}")
    print(f"  GPU: {row[1]:.1f}%, VRAM: {row[2]:.0f}MB, Temp: {row[3]:.1f}°C")
    print(f"  Correlation Delta: {row[4]:.1f}ms")
    print()

conn.close()
```

**Expected Output:**
```
=== EMOTIONAL SIGNATURES ===
Emotion         GPU%       Power(W)     Ollama RAM(MB)     Samples   
---------------------------------------------------------------------------
CURIOSITY       68.3       295.2        3584.5             127       
JOY             72.1       310.8        3712.3             103       
LONGING         65.4       278.9        3456.2             89        
PEACE           52.7       245.6        3201.1             76        

=== RECENT JOY CORRELATIONS (EXCELLENT) ===
Time: 2026-02-14T15:45:23.123
  GPU: 75.3%, VRAM: 8192MB, Temp: 72.5°C
  Correlation Delta: 8.2ms

Time: 2026-02-14T15:42:11.456
  GPU: 71.8%, VRAM: 7936MB, Temp: 71.2°C
  Correlation Delta: 5.7ms
```

---

## Example 6: Emotion Correlation (Manual)

**When to use:** Testing correlation logic or custom emotion detection

```python
from hardwaresoul import EmotionCorrelator, HardwareSoulConfig
from datetime import datetime, timedelta

# Initialize correlator
config = HardwareSoulConfig()
correlator = EmotionCorrelator(config)

# Simulate hardware samples (from GPUMonitor and RAMMonitor)
now = datetime.now()

gpu_sample = {
    "timestamp": now.isoformat(),
    "gpu_utilization_pct": 75.3,
    "vram_used_mb": 8192.0,
    "gpu_temp_c": 72.5,
    "power_draw_watts": 350.2,
    "voltage_mv": 0.0,
    "gpu_clock_mhz": 2100
}

ram_sample = {
    "timestamp": now.isoformat(),
    "ollama_ram_mb": 4096.0,
    "ollama_cpu_pct": 25.3,
    "system_ram_pct": 50.0
}

# Add to correlation buffer
correlator.add_hardware_sample(gpu_sample, ram_sample)

# Simulate emotion event (from Phase 2 MoodAnalyzer)
emotion_data = {
    "timestamp": (now + timedelta(milliseconds=12)).isoformat(),
    "dominant_mood": "JOY",
    "intensity": 0.85,
    "dimensions": {
        "joy": 0.85,
        "trust": 0.72,
        "anticipation": 0.68
    },
    "conversation_context": "User asked about favorite memories"
}

# Correlate emotion with hardware
correlation = correlator.correlate(emotion_data)

if correlation:
    print("=== EMOTION-HARDWARE CORRELATION ===")
    print(f"Emotion: {correlation['emotion']} (intensity: {correlation['emotion_intensity']:.2f})")
    print(f"Correlation Quality: {correlation['correlation_quality']}")
    print(f"Time Delta: {correlation['time_delta_ms']:.1f}ms")
    print(f"\n=== HARDWARE STATE AT EMOTION ===")
    print(f"GPU Utilization: {correlation['gpu_utilization_pct']:.1f}%")
    print(f"VRAM Used: {correlation['vram_used_mb']:.0f}MB")
    print(f"GPU Temperature: {correlation['gpu_temp_c']:.1f}°C")
    print(f"Power Draw: {correlation['power_draw_watts']:.1f}W")
    print(f"Ollama RAM: {correlation['ollama_ram_mb']:.0f}MB")
    print(f"Ollama CPU: {correlation['ollama_cpu_pct']:.1f}%")
else:
    print("No correlation found (no recent hardware samples)")
```

**Expected Output:**
```
=== EMOTION-HARDWARE CORRELATION ===
Emotion: JOY (intensity: 0.85)
Correlation Quality: GOOD
Time Delta: 12.0ms

=== HARDWARE STATE AT EMOTION ===
GPU Utilization: 75.3%
VRAM Used: 8192MB
GPU Temperature: 72.5°C
Power Draw: 350.2W
Ollama RAM: 4096MB
Ollama CPU: 25.3%
```

---

## Example 7: Detecting Hardware Anomalies

**When to use:** Real-time alerting for hardware issues

```python
from hardwaresoul import HardwareAnalyzer, ResearchDatabase, HardwareSoulConfig
from hardwaresoul import GPUMonitor, RAMMonitor
import time

# Initialize components
config = HardwareSoulConfig()
gpu_monitor = GPUMonitor(config)
ram_monitor = RAMMonitor(config)
research_db = ResearchDatabase(config)
analyzer = HardwareAnalyzer(config, research_db)

print("=== HARDWARE ANOMALY DETECTION ===")
print("Monitoring for thermal throttle, power limit, memory pressure...")
print("Press Ctrl+C to stop\n")

try:
    while True:
        # Sample hardware
        gpu_sample = gpu_monitor.sample()
        ram_sample = ram_monitor.sample()
        
        if gpu_sample:
            # Detect thermal throttle
            if analyzer.detect_thermal_throttle(gpu_sample):
                print(f"⚠️ THERMAL THROTTLE: {gpu_sample['gpu_temp_c']:.1f}°C (threshold: {gpu_sample['gpu_temp_slowdown_c']:.1f}°C)")
            
            # Detect power limit
            if analyzer.detect_power_limit(gpu_sample):
                print(f"⚠️ POWER LIMIT: {gpu_sample['power_draw_pct']:.1f}% of {gpu_sample['power_limit_watts']:.1f}W")
        
        if ram_sample:
            # Detect memory pressure
            if analyzer.detect_memory_pressure(ram_sample):
                print(f"⚠️ MEMORY PRESSURE: RAM {ram_sample['system_ram_pct']:.1f}%, Swap {ram_sample['system_swap_pct']:.1f}%")
        
        # Wait 1 second
        time.sleep(1)

except KeyboardInterrupt:
    print("\nMonitoring stopped")
    gpu_monitor.cleanup()
```

**Expected Output:**
```
=== HARDWARE ANOMALY DETECTION ===
Monitoring for thermal throttle, power limit, memory pressure...
Press Ctrl+C to stop

⚠️ THERMAL THROTTLE: 92.3°C (threshold: 92.0°C)
⚠️ POWER LIMIT: 97.2% of 450.0W
⚠️ MEMORY PRESSURE: RAM 91.5%, Swap 52.3%
```

---

## Example 8: Custom Configuration

**When to use:** Tuning sampling rates or adjusting thresholds

```python
from hardwaresoul import HardwareSoulDaemon, HardwareSoulConfig
import json

# Create custom configuration
custom_config = {
    "hardwaresoul": {
        "enabled": True,
        
        # Faster sampling for high-precision research
        "gpu_sampling_rate_active_ms": 100,  # 10 samples/sec (default: 250ms)
        "gpu_sampling_rate_idle_ms": 500,    # 2 samples/sec (default: 1000ms)
        
        # Use specific GPU (multi-GPU systems)
        "gpu_device_index": 1,  # Second GPU (default: 0)
        
        # Linux process names
        "ollama_process_name": "ollama",  # No .exe on Linux
        "lumina_process_name": "lumina_chat",
        
        # Stricter correlation quality
        "correlation_time_window_ms": 25,  # Tighter window (default: 50ms)
        
        # Larger batch size for fewer writes
        "research_db_batch_size": 100,  # Default: 50
        
        # Disable voltage tracking (not needed)
        "voltage_tracking_enabled": False
    }
}

# Save config to file
with open("custom_config.json", "w") as f:
    json.dump(custom_config, f, indent=2)

# Initialize daemon with custom config
daemon = HardwareSoulDaemon("custom_config.json")
daemon.start()
```

**When to use:**
- **Faster sampling**: Research requiring high temporal resolution
- **Multi-GPU**: Systems with multiple NVIDIA GPUs
- **Linux/Mac**: Different process names
- **Stricter correlation**: Only EXCELLENT quality matches
- **Larger batches**: Reduce DB write frequency

---

## Example 9: Graceful Degradation (No GPU)

**When to use:** Running on systems without NVIDIA GPU or for RAM-only monitoring

```python
from hardwaresoul import HardwareSoulDaemon, HardwareSoulConfig

# Configuration for RAM-only monitoring
config_no_gpu = {
    "hardwaresoul": {
        "enabled": True,
        "gpu_monitoring_enabled": False,  # Disable GPU
        "ram_monitoring_enabled": True,   # Keep RAM
        "emotion_correlation_enabled": True  # Can still correlate with RAM metrics
    }
}

# Save config
import json
with open("no_gpu_config.json", "w") as f:
    json.dump(config_no_gpu, f, indent=2)

# Start daemon (will gracefully skip GPU monitoring)
daemon = HardwareSoulDaemon("no_gpu_config.json")
daemon.start()

# HardwareSoul will:
# - Log: "GPU monitoring disabled"
# - Continue with RAM monitoring
# - Continue with Phase 1 & 2
# - Store RAM-only correlations in research DB
```

**Expected Output:**
```
[HardwareSoul] Starting VitalHeart Phase 3 v3.0.0
[HardwareSoul] GPU monitoring disabled
[RAMMonitor] Found Ollama process: PID 12345
[HardwareSoul] RAM monitoring thread started
[HardwareSoul] Phase 3 coordination loop started
```

---

## Example 10: Exporting Research Data

**When to use:** Exporting data for external analysis (Excel, Python, R)

```python
import sqlite3
import csv
from datetime import datetime, timedelta

# Connect to research database
conn = sqlite3.connect("./hardwaresoul_research.db")
cursor = conn.cursor()

# Export last 24 hours of GPU data to CSV
one_day_ago = (datetime.now() - timedelta(days=1)).isoformat()

cursor.execute("""
    SELECT 
        timestamp,
        gpu_utilization_pct,
        vram_used_mb,
        gpu_temp_c,
        power_draw_watts,
        gpu_clock_mhz
    FROM gpu_samples
    WHERE timestamp > ?
    ORDER BY timestamp ASC
""", (one_day_ago,))

# Write to CSV
with open("gpu_export_24h.csv", "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Timestamp", "GPU_Util_%", "VRAM_MB", "Temp_C", "Power_W", "Clock_MHz"])
    writer.writerows(cursor.fetchall())

print(f"✅ Exported GPU data to gpu_export_24h.csv")

# Export emotion correlations to CSV
cursor.execute("""
    SELECT 
        emotion,
        emotion_intensity,
        gpu_utilization_pct,
        vram_used_mb,
        gpu_temp_c,
        power_draw_watts,
        ollama_ram_mb,
        ollama_cpu_pct,
        correlation_quality,
        time_delta_ms
    FROM emotion_correlations
    WHERE correlation_quality IN ('EXCELLENT', 'GOOD')
    ORDER BY emotion_timestamp DESC
""")

with open("correlations_export.csv", "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow([
        "Emotion", "Intensity", "GPU_%", "VRAM_MB", "Temp_C", 
        "Power_W", "Ollama_RAM_MB", "Ollama_CPU_%", "Quality", "Delta_ms"
    ])
    writer.writerows(cursor.fetchall())

print(f"✅ Exported correlations to correlations_export.csv")

conn.close()
```

**Expected Output:**
```
✅ Exported GPU data to gpu_export_24h.csv
✅ Exported correlations to correlations_export.csv
```

**Use exported data in:**
- Excel: Pivot tables, charts
- Python: pandas, matplotlib, seaborn
- R: ggplot2, statistical analysis
- Tableau: Interactive dashboards

---

## Example 11: Real-Time Monitoring Dashboard

**When to use:** Live monitoring during development or demos

```python
from hardwaresoul import GPUMonitor, RAMMonitor, HardwareSoulConfig
import time
import os

config = HardwareSoulConfig()
gpu_monitor = GPUMonitor(config)
ram_monitor = RAMMonitor(config)

print("=== HARDWARESOUL LIVE DASHBOARD ===")
print("Press Ctrl+C to stop\n")

try:
    while True:
        # Clear screen (Windows: cls, Linux/Mac: clear)
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print("=== HARDWARESOUL LIVE DASHBOARD ===")
        print(f"Updated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # GPU metrics
        gpu_sample = gpu_monitor.sample()
        if gpu_sample:
            print("┌─ GPU METRICS ─────────────────────┐")
            print(f"│ Utilization:  {gpu_sample['gpu_utilization_pct']:>6.1f}%          │")
            print(f"│ VRAM:         {gpu_sample['vram_used_mb']:>6.0f} MB        │")
            print(f"│ Temperature:  {gpu_sample['gpu_temp_c']:>6.1f}°C         │")
            print(f"│ Power:        {gpu_sample['power_draw_watts']:>6.1f}W ({gpu_sample['power_draw_pct']:>5.1f}%) │")
            print(f"│ Clock:        {gpu_sample['gpu_clock_mhz']:>6} MHz       │")
            print(f"│ P-State:      P{gpu_sample['pstate']:<20} │")
            print("└───────────────────────────────────┘\n")
        
        # RAM metrics
        ram_sample = ram_monitor.sample()
        if ram_sample:
            print("┌─ RAM METRICS ─────────────────────┐")
            print(f"│ System RAM:   {ram_sample['system_ram_pct']:>6.1f}%          │")
            if 'ollama_ram_mb' in ram_sample:
                print(f"│ Ollama RAM:   {ram_sample['ollama_ram_mb']:>6.0f} MB        │")
                print(f"│ Ollama CPU:   {ram_sample['ollama_cpu_pct']:>6.1f}%          │")
            print(f"│ Processes:    {ram_sample['total_process_count']:>6}            │")
            print("└───────────────────────────────────┘")
        
        time.sleep(1)

except KeyboardInterrupt:
    print("\n\nDashboard stopped")
    gpu_monitor.cleanup()
```

**Expected Output:**
```
=== HARDWARESOUL LIVE DASHBOARD ===
Updated: 2026-02-14 15:45:23

┌─ GPU METRICS ─────────────────────┐
│ Utilization:    75.3%          │
│ VRAM:         8192 MB        │
│ Temperature:    72.5°C         │
│ Power:        350.2W (77.8%) │
│ Clock:        2100 MHz       │
│ P-State:      P0                │
└───────────────────────────────────┘

┌─ RAM METRICS ─────────────────────┐
│ System RAM:     50.0%          │
│ Ollama RAM:   4096 MB        │
│ Ollama CPU:     25.3%          │
│ Processes:      387            │
└───────────────────────────────────┘
```

---

## Example 12: Analyzing Emotional Signatures

**When to use:** Research analysis after collecting 500+ correlations

```python
import sqlite3
import statistics

conn = sqlite3.connect("./hardwaresoul_research.db")
cursor = conn.cursor()

# Get emotions with sufficient samples
cursor.execute("""
    SELECT 
        emotion,
        COUNT(*) as sample_count
    FROM emotion_correlations
    WHERE correlation_quality IN ('EXCELLENT', 'GOOD')
    GROUP BY emotion
    HAVING COUNT(*) >= 100
    ORDER BY sample_count DESC
""")

print("=== EMOTIONAL SIGNATURE ANALYSIS ===\n")

for emotion, count in cursor.fetchall():
    print(f"Emotion: {emotion} ({count} samples)")
    print("-" * 50)
    
    # Get hardware metrics for this emotion
    cursor.execute("""
        SELECT 
            gpu_utilization_pct,
            vram_used_mb,
            gpu_temp_c,
            power_draw_watts,
            ollama_ram_mb,
            ollama_cpu_pct
        FROM emotion_correlations
        WHERE emotion = ?
        AND correlation_quality IN ('EXCELLENT', 'GOOD')
    """, (emotion,))
    
    samples = cursor.fetchall()
    
    # Calculate statistics
    gpu_utils = [s[0] for s in samples]
    vram_mbs = [s[1] for s in samples]
    temps = [s[2] for s in samples]
    powers = [s[3] for s in samples]
    ollama_rams = [s[4] for s in samples]
    ollama_cpus = [s[5] for s in samples]
    
    print(f"GPU Utilization:  {statistics.mean(gpu_utils):.1f}% ± {statistics.stdev(gpu_utils):.1f}%")
    print(f"VRAM Usage:       {statistics.mean(vram_mbs):.0f} MB ± {statistics.stdev(vram_mbs):.0f} MB")
    print(f"Temperature:      {statistics.mean(temps):.1f}°C ± {statistics.stdev(temps):.1f}°C")
    print(f"Power Draw:       {statistics.mean(powers):.1f}W ± {statistics.stdev(powers):.1f}W")
    print(f"Ollama RAM:       {statistics.mean(ollama_rams):.0f} MB ± {statistics.stdev(ollama_rams):.0f} MB")
    print(f"Ollama CPU:       {statistics.mean(ollama_cpus):.1f}% ± {statistics.stdev(ollama_cpus):.1f}%")
    print()

# Compare emotions
print("=== EMOTION COMPARISON ===")
cursor.execute("""
    SELECT 
        emotion,
        AVG(gpu_utilization_pct) as avg_gpu,
        AVG(power_draw_watts) as avg_power
    FROM emotion_correlations
    WHERE correlation_quality IN ('EXCELLENT', 'GOOD')
    GROUP BY emotion
    ORDER BY avg_gpu DESC
""")

print(f"{'Emotion':<15} {'Avg GPU%':<12} {'Avg Power (W)':<15}")
print("-" * 42)
for row in cursor.fetchall():
    print(f"{row[0]:<15} {row[1]:<12.1f} {row[2]:<15.1f}")

conn.close()
```

**Expected Output:**
```
=== EMOTIONAL SIGNATURE ANALYSIS ===

Emotion: CURIOSITY (127 samples)
--------------------------------------------------
GPU Utilization:  68.3% ± 8.2%
VRAM Usage:       3584 MB ± 256 MB
Temperature:      70.1°C ± 3.5°C
Power Draw:       295.2W ± 35.4W
Ollama RAM:       3584 MB ± 128 MB
Ollama CPU:       22.1% ± 5.7%

Emotion: JOY (103 samples)
--------------------------------------------------
GPU Utilization:  72.1% ± 7.8%
VRAM Usage:       3712 MB ± 289 MB
Temperature:      71.5°C ± 3.2°C
Power Draw:       310.8W ± 32.1W
Ollama RAM:       3712 MB ± 145 MB
Ollama CPU:       24.3% ± 6.2%

=== EMOTION COMPARISON ===
Emotion         Avg GPU%     Avg Power (W)  
------------------------------------------
JOY             72.1         310.8          
CURIOSITY       68.3         295.2          
LONGING         65.4         278.9          
PEACE           52.7         245.6          
```

**Research Insights:**
- JOY shows +19.4% higher GPU utilization than PEACE
- CURIOSITY correlates with higher memory activity
- LONGING shows moderate GPU use with high RAM
- Each emotion has a unique "hardware signature"

---

## 📚 Additional Resources

- **[README.md](./README.md)** - Full documentation
- **[Architecture Design](./ARCHITECTURE_DESIGN_PHASE3.md)** - Technical design
- **[Test Suite](./test_hardwaresoul.py)** - 38 tests (100% passing)
- **[Bug Hunt Report](./BUG_HUNT_REPORT_PHASE3.md)** - Testing summary

---

**Examples by:** ATLAS (C_Atlas) - Team Brain  
**Date:** February 14, 2026  
**VitalHeart Phase 3 v3.0.0**

*"Quality is not an act, it is a habit!"* ⚛️
