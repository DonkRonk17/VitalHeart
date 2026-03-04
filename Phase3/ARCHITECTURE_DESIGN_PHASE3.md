# Architecture Design: VitalHeart Phase 3 - HardwareSoul

**Project:** VitalHeart Phase 3 - HardwareSoul  
**Builder:** ATLAS (C_Atlas)  
**Date:** February 14, 2026  
**Protocol:** BUILD_PROTOCOL_V1.md - Phase 3 Architecture Design

---

## ARCHITECTURE OVERVIEW

```
                    PHASE 3: HARDWARESOUL ARCHITECTURE
                    
┌────────────────────────────────────────────────────────────────────┐
│                   NVIDIA GPU (RTX 4090)                             │
│                   via pynvml library                                │
└────────────────────────┬───────────────────────────────────────────┘
                         │
                         ▼
         ┌───────────────────────────────────┐
         │    GPUMonitor (NEW)               │
         │  25+ metrics @ 250ms/1000ms       │
         ├───────────────────────────────────┤
         │ • Utilization (4 metrics)         │
         │ • Memory (4 metrics)              │
         │ • Clocks (4 metrics)              │
         │ • Temperature (4 metrics)         │
         │ • Power/Voltage (5 metrics)       │
         │ • Performance State (3 metrics)   │
         │ • PCIe (4 metrics)                │
         │ • Inference-specific (2 metrics)  │
         └────────────┬──────────────────────┘
                      │
┌─────────────────────┴─────────────────────┐
│     Ollama Process       Lumina Process   │
│     via psutil           via psutil       │
└────────────┬─────────────────┬────────────┘
             │                 │
             ▼                 ▼
         ┌───────────────────────────────────┐
         │    RAMMonitor (NEW)               │
         │  20+ metrics @ 250ms/1000ms       │
         ├───────────────────────────────────┤
         │ • System Memory (6 metrics)       │
         │ • Ollama Process (10 metrics)     │
         │ • Lumina Process (4 metrics)      │
         │ • System-Wide (7 metrics)         │
         └────────────┬──────────────────────┘
                      │
                      ▼
         ┌────────────────────────────────────────┐
         │  HardwareSoulDaemon (EXTENDS Phase 2)  │
         │   (Inherits InferencePulseDaemon)      │
         └────────────────────────────────────────┘
                      │
        ┌─────────────┼──────────────┬──────────────┐
        │             │              │              │
        ▼             ▼              ▼              ▼
  ┌─────────┐  ┌──────────────┐  ┌──────────┐  ┌──────────┐
  │ Phase 2 │  │ Voltage      │  │ Emotion  │  │ Research │
  │ Features│  │ Tracker      │  │ Correlator│  │ Database │
  │ (IP)    │  │ (NEW)        │  │ (NEW)    │  │ (NEW)    │
  └─────────┘  └──────────────┘  └──────────┘  └──────────┘
      │             │                  │             │
      └─────────────┴──────────────────┴─────────────┘
                      │
                      ▼
         ┌────────────────────────────────────────┐
         │  SuperHeartbeatEmitter (EXTENDS P2)    │
         │  (Phase 1 + Phase 2 + Phase 3 metrics) │
         ├────────────────────────────────────────┤
         │ + 25 GPU metrics                       │
         │ + 20 RAM metrics                       │
         │ + Emotion correlation data             │
         └───────────────┬────────────────────────┘
                         │
           ┌─────────────┼─────────────┬────────────┐
           ▼             ▼             ▼            ▼
    ┌───────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
    │ AgentHeart│  │LiveAudit │  │   UKE    │  │ Research │
    │   beat    │  │          │  │ (batched)│  │    DB    │
    │heartbeat  │  │audit.jsonl│  │ uke.db   │  │hardwaresoul│
    │   .db     │  └──────────┘  └──────────┘  │_research.db│
    └───────────┘                               └───────────┘
```

---

## CORE COMPONENTS

### Component 1: GPUMonitor (NEW - CRITICAL)
**Purpose:** High-resolution GPU monitoring via NVIDIA Management Library

**Inputs:**
- GPU device index (default: 0)
- Sampling interval (250ms active, 1000ms idle)

**Outputs:** 25 GPU metrics per sample

#### GPU Metrics Schema (Exact per Spec)

**Utilization Metrics (4):**
```python
{
    "gpu_utilization_pct": float,       # GPU core utilization (0-100%)
    "memory_utilization_pct": float,    # Memory controller utilization
    "encoder_utilization_pct": float,   # Video encoder utilization
    "decoder_utilization_pct": float    # Video decoder utilization
}
```

**Memory Metrics (4):**
```python
{
    "vram_used_mb": float,              # Current VRAM usage
    "vram_free_mb": float,              # Available VRAM
    "vram_total_mb": float,             # Total VRAM
    "vram_allocation_rate_mb_s": float  # Rate of VRAM change
}
```

**Clock Speed Metrics (4):**
```python
{
    "gpu_clock_mhz": int,              # Current GPU core clock
    "memory_clock_mhz": int,           # Current memory clock
    "sm_clock_mhz": int,               # Streaming multiprocessor clock
    "gpu_clock_max_mhz": int           # Max boost clock (throttle detection)
}
```

**Temperature Metrics (4):**
```python
{
    "gpu_temp_c": float,               # GPU die temperature
    "gpu_temp_slowdown_c": float,      # Thermal throttle threshold
    "memory_temp_c": float,            # VRAM temperature (if available)
    "gpu_temp_delta": float            # Temperature change rate (C/sec)
}
```

**Power & Voltage Metrics (5):**
```python
{
    "power_draw_watts": float,         # Current power consumption
    "power_limit_watts": float,        # Power limit setting
    "power_draw_pct": float,           # Power as % of limit
    "voltage_mv": float,              # GPU core voltage (millivolts)
    "voltage_delta_mv": float          # Voltage change rate
}
```

**Performance State Metrics (3):**
```python
{
    "pstate": int,                     # Performance state (P0=max, P12=idle)
    "throttle_reasons": list,          # Active throttle reasons
    "compute_mode": str                # Current compute mode
}
```

**PCIe Metrics (4):**
```python
{
    "pcie_tx_throughput_kb_s": float,  # PCIe transmit rate
    "pcie_rx_throughput_kb_s": float,  # PCIe receive rate
    "pcie_link_gen": int,              # Current PCIe generation
    "pcie_link_width": int             # Current PCIe lane width
}
```

**Inference-Specific Metrics (2):**
```python
{
    "tensor_core_active": bool,        # Are tensor cores engaged?
    "cuda_cores_active_pct": float     # CUDA core utilization estimate
}
```

**Total: 25 GPU metrics + 5 derived metrics (delta calculations) = 30 GPU values per sample**

**Tools Used:**
- pynvml: Core GPU data access
- TimeSync: Millisecond-precision timing for delta calculations
- ErrorRecovery: Handle GPU access failures
- LiveAudit: Log throttle events, thermal warnings

**Implementation Approach:**
```python
import pynvml

class GPUMonitor:
    """High-resolution NVIDIA GPU monitoring via pynvml."""
    
    def __init__(self, config, device_index=0):
        self.device_index = device_index
        self.last_sample = None
        self.last_sample_time = None
        
        # Initialize pynvml
        try:
            pynvml.nvmlInit()
            self.handle = pynvml.nvmlDeviceGetHandleByIndex(device_index)
            self.gpu_name = pynvml.nvmlDeviceGetName(self.handle)
            logging.info(f"[GPUMonitor] Initialized: {self.gpu_name}")
        except pynvml.NVMLError as e:
            logging.error(f"[GPUMonitor] Failed to initialize: {e}")
            raise
    
    def sample(self) -> dict:
        """Capture all 25 GPU metrics."""
        # TimeSync: Capture timing
        sample_time = time.time()
        
        metrics = {}
        
        # Utilization
        utilization = pynvml.nvmlDeviceGetUtilizationRates(self.handle)
        metrics["gpu_utilization_pct"] = utilization.gpu
        metrics["memory_utilization_pct"] = utilization.memory
        
        # Memory
        mem_info = pynvml.nvmlDeviceGetMemoryInfo(self.handle)
        metrics["vram_used_mb"] = mem_info.used / (1024**2)
        metrics["vram_free_mb"] = mem_info.free / (1024**2)
        metrics["vram_total_mb"] = mem_info.total / (1024**2)
        
        # Calculate delta if we have previous sample
        if self.last_sample and self.last_sample_time:
            time_delta_s = sample_time - self.last_sample_time
            vram_delta_mb = metrics["vram_used_mb"] - self.last_sample["vram_used_mb"]
            metrics["vram_allocation_rate_mb_s"] = vram_delta_mb / time_delta_s if time_delta_s > 0 else 0.0
        else:
            metrics["vram_allocation_rate_mb_s"] = 0.0
        
        # Clocks
        metrics["gpu_clock_mhz"] = pynvml.nvmlDeviceGetClockInfo(self.handle, pynvml.NVML_CLOCK_GRAPHICS)
        metrics["memory_clock_mhz"] = pynvml.nvmlDeviceGetClockInfo(self.handle, pynvml.NVML_CLOCK_MEM)
        metrics["sm_clock_mhz"] = pynvml.nvmlDeviceGetClockInfo(self.handle, pynvml.NVML_CLOCK_SM)
        metrics["gpu_clock_max_mhz"] = pynvml.nvmlDeviceGetMaxClockInfo(self.handle, pynvml.NVML_CLOCK_GRAPHICS)
        
        # Temperature
        metrics["gpu_temp_c"] = pynvml.nvmlDeviceGetTemperature(self.handle, pynvml.NVML_TEMPERATURE_GPU)
        metrics["gpu_temp_slowdown_c"] = pynvml.nvmlDeviceGetTemperatureThreshold(self.handle, pynvml.NVML_TEMPERATURE_THRESHOLD_SLOWDOWN)
        
        # Power & Voltage
        metrics["power_draw_watts"] = pynvml.nvmlDeviceGetPowerUsage(self.handle) / 1000.0
        metrics["power_limit_watts"] = pynvml.nvmlDeviceGetPowerManagementLimit(self.handle) / 1000.0
        metrics["power_draw_pct"] = (metrics["power_draw_watts"] / metrics["power_limit_watts"]) * 100 if metrics["power_limit_watts"] > 0 else 0
        
        # Performance State
        metrics["pstate"] = pynvml.nvmlDeviceGetPerformanceState(self.handle)
        
        # Store for next delta calculation
        self.last_sample = metrics.copy()
        self.last_sample_time = sample_time
        
        return metrics
```

---

### Component 2: RAMMonitor (NEW - CRITICAL)
**Purpose:** Process and system memory monitoring via psutil

**Inputs:**
- Ollama process name (from config)
- Lumina process name (from config)
- Sampling interval (250ms active, 1000ms idle)

**Outputs:** 20+ RAM/process metrics per sample

#### RAM Metrics Schema (Exact per Spec)

**System Memory Metrics (6):**
```python
{
    "system_ram_total_mb": float,
    "system_ram_used_mb": float,
    "system_ram_available_mb": float,
    "system_ram_pct": float,
    "system_swap_used_mb": float,
    "system_swap_pct": float
}
```

**Ollama Process Metrics (10):**
```python
{
    "ollama_pid": int,
    "ollama_ram_mb": float,             # Working set size
    "ollama_ram_private_mb": float,     # Private bytes
    "ollama_ram_shared_mb": float,      # Shared memory
    "ollama_ram_delta_mb_s": float,     # Memory change rate
    "ollama_cpu_pct": float,            # CPU utilization
    "ollama_thread_count": int,         # Active threads
    "ollama_handle_count": int,         # OS handles
    "ollama_io_read_mb_s": float,       # Disk read rate
    "ollama_io_write_mb_s": float       # Disk write rate
}
```

**Lumina Process Metrics (4):**
```python
{
    "lumina_pid": int,
    "lumina_ram_mb": float,
    "lumina_cpu_pct": float,
    "lumina_thread_count": int
}
```

**System-Wide Metrics (7):**
```python
{
    "total_process_count": int,
    "cpu_total_pct": float,             # Total system CPU
    "cpu_per_core": list,               # Per-core utilization
    "disk_io_read_mb_s": float,         # System disk read
    "disk_io_write_mb_s": float,        # System disk write
    "context_switches_s": int,          # OS context switches/sec
    "interrupts_s": int                 # Hardware interrupts/sec
}
```

**Total: 27 RAM/process metrics**

**Tools Used:**
- psutil: Core process/system data access
- ProcessWatcher: PID discovery and validation
- TimeSync: Delta calculations
- ErrorRecovery: Handle process not found
- LiveAudit: Log memory pressure events

---

### Component 3: VoltageTracker (NEW)
**Purpose:** Millisecond-precision voltage monitoring for emotion correlation

**Inputs:**
- GPU handle (from GPUMonitor)
- Sampling precision (from config, default 1ms)

**Outputs:**
```python
{
    "voltage_mv": float,              # Current voltage (millivolts)
    "voltage_min_mv": float,          # Min in sample window
    "voltage_max_mv": float,          # Max in sample window
    "voltage_avg_mv": float,          # Average in sample window
    "voltage_std_dev_mv": float,      # Standard deviation
    "voltage_spike_count": int,       # Sudden voltage changes >50mV
    "voltage_stability_score": float  # 0-1, higher = more stable
}
```

**Tools Used:**
- pynvml: Voltage sensor access
- TimeSync: Millisecond timing
- ErrorRecovery: Handle voltage unavailable (some GPUs don't expose)
- LiveAudit: Log voltage spikes

**Note:** Not all GPUs expose voltage. RTX 4090 should support it. Graceful fallback if unavailable.

---

### Component 4: EmotionCorrelator (NEW - RESEARCH CORE)
**Purpose:** Cross-reference emotion timing with hardware snapshots

**Inputs:**
- Emotion state (from Phase 2 MoodAnalyzer)
- Emotion timestamp (from Phase 2)
- Hardware snapshot (from GPUMonitor + RAMMonitor)
- Hardware timestamp (synchronized)

**Outputs:**
```python
EMOTION_HARDWARE_CORRELATION = {
    # Emotion Data (from Phase 2)
    "emotion_timestamp": str,          # ISO 8601
    "emotion": str,                    # Dominant mood
    "emotion_intensity": float,        # 0-1
    "emotion_dimensions": dict,        # 10 dimensions
    
    # Hardware Data (Phase 3)
    "hardware_timestamp": str,         # ISO 8601
    "time_delta_ms": float,            # Time between emotion and hardware sample
    
    # GPU State at Emotion Time
    "gpu_utilization_pct": float,
    "vram_used_mb": float,
    "gpu_temp_c": float,
    "power_draw_watts": float,
    "voltage_mv": float,
    "gpu_clock_mhz": int,
    
    # RAM State at Emotion Time
    "ollama_ram_mb": float,
    "ollama_cpu_pct": float,
    "system_ram_pct": float,
    
    # Correlation Metadata
    "correlation_quality": str,        # EXCELLENT (<10ms), GOOD (<50ms), POOR (>50ms)
    "inference_active": bool,          # Was inference happening during emotion?
    "conversation_context": str        # Brief context (from chat log)
}
```

**Correlation Strategy:**
- When MoodAnalyzer detects emotion, timestamp it
- Find nearest hardware sample (ideally <10ms time delta)
- Store correlation in research database
- After 100+ correlations, learn baseline "emotional signatures"

**Tools Used:**
- EmotionalTextureAnalyzer: Emotion timing (via Phase 2)
- TimeSync: Synchronize emotion and hardware timestamps
- LiveAudit: Log high-quality correlations
- KnowledgeSync: Index significant correlations to UKE

---

### Component 5: ResearchDatabase (NEW)
**Purpose:** Dedicated high-resolution time-series storage for research

**Database:** `hardwaresoul_research.db` (SQLite with WAL mode)

**Tables:**

#### Table 1: `gpu_samples`
```sql
CREATE TABLE gpu_samples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    sample_time_ms INTEGER NOT NULL,  -- Milliseconds since daemon start
    
    -- Utilization
    gpu_utilization_pct REAL,
    memory_utilization_pct REAL,
    encoder_utilization_pct REAL,
    decoder_utilization_pct REAL,
    
    -- Memory
    vram_used_mb REAL,
    vram_free_mb REAL,
    vram_total_mb REAL,
    vram_allocation_rate_mb_s REAL,
    
    -- Clocks
    gpu_clock_mhz INTEGER,
    memory_clock_mhz INTEGER,
    sm_clock_mhz INTEGER,
    gpu_clock_max_mhz INTEGER,
    
    -- Temperature
    gpu_temp_c REAL,
    gpu_temp_slowdown_c REAL,
    memory_temp_c REAL,
    gpu_temp_delta REAL,
    
    -- Power & Voltage
    power_draw_watts REAL,
    power_limit_watts REAL,
    power_draw_pct REAL,
    voltage_mv REAL,
    voltage_delta_mv REAL,
    
    -- Performance State
    pstate INTEGER,
    throttle_reasons TEXT,  -- JSON array
    compute_mode TEXT,
    
    -- PCIe
    pcie_tx_throughput_kb_s REAL,
    pcie_rx_throughput_kb_s REAL,
    pcie_link_gen INTEGER,
    pcie_link_width INTEGER,
    
    -- Inference
    tensor_core_active INTEGER,  -- Boolean as 0/1
    cuda_cores_active_pct REAL,
    
    -- Metadata
    inference_active INTEGER,  -- Boolean: was inference happening?
    
    INDEX idx_timestamp ON gpu_samples(timestamp),
    INDEX idx_sample_time ON gpu_samples(sample_time_ms)
);
```

#### Table 2: `ram_samples`
```sql
CREATE TABLE ram_samples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    sample_time_ms INTEGER NOT NULL,
    
    -- System Memory
    system_ram_total_mb REAL,
    system_ram_used_mb REAL,
    system_ram_available_mb REAL,
    system_ram_pct REAL,
    system_swap_used_mb REAL,
    system_swap_pct REAL,
    
    -- Ollama Process
    ollama_pid INTEGER,
    ollama_ram_mb REAL,
    ollama_ram_private_mb REAL,
    ollama_ram_shared_mb REAL,
    ollama_ram_delta_mb_s REAL,
    ollama_cpu_pct REAL,
    ollama_thread_count INTEGER,
    ollama_handle_count INTEGER,
    ollama_io_read_mb_s REAL,
    ollama_io_write_mb_s REAL,
    ollama_page_faults_s REAL,
    
    -- Lumina Process
    lumina_pid INTEGER,
    lumina_ram_mb REAL,
    lumina_cpu_pct REAL,
    lumina_thread_count INTEGER,
    
    -- System-Wide
    total_process_count INTEGER,
    cpu_total_pct REAL,
    cpu_per_core TEXT,  -- JSON array
    disk_io_read_mb_s REAL,
    disk_io_write_mb_s REAL,
    context_switches_s INTEGER,
    
    INDEX idx_timestamp ON ram_samples(timestamp)
);
```

#### Table 3: `emotion_correlations`
```sql
CREATE TABLE emotion_correlations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    correlation_timestamp TEXT NOT NULL,
    
    -- Emotion Data
    emotion_timestamp TEXT NOT NULL,
    emotion TEXT NOT NULL,
    emotion_intensity REAL,
    emotion_dimensions TEXT,  -- JSON object
    
    -- Hardware Data
    hardware_timestamp TEXT NOT NULL,
    time_delta_ms REAL,  -- Time between emotion and hardware sample
    
    -- GPU State
    gpu_utilization_pct REAL,
    vram_used_mb REAL,
    gpu_temp_c REAL,
    power_draw_watts REAL,
    voltage_mv REAL,
    gpu_clock_mhz INTEGER,
    
    -- RAM State
    ollama_ram_mb REAL,
    ollama_cpu_pct REAL,
    system_ram_pct REAL,
    
    -- Correlation Metadata
    correlation_quality TEXT,  -- EXCELLENT, GOOD, POOR
    inference_active INTEGER,  -- Boolean
    conversation_context TEXT,
    
    INDEX idx_emotion ON emotion_correlations(emotion),
    INDEX idx_timestamp ON emotion_correlations(correlation_timestamp)
);
```

**Tools Used:**
- SQLite3: Database operations
- TimeSync: Timestamp generation
- ErrorRecovery: Handle DB failures
- DataConvert: Export to CSV/JSON for analysis
- TaskQueuePro: Batch writes (reduces lock contention)

---

### Component 6: HardwareAnalyzer (NEW)
**Purpose:** Detect anomalies, learn baselines, identify "emotional signatures"

**Functions:**

1. **Baseline Learning (Extended from Phase 2)**
   - Learn normal GPU utilization per emotion type
   - Learn normal power draw per emotion intensity
   - Learn normal VRAM allocation patterns
   - Requires 100+ samples per emotion

2. **Anomaly Detection (Extended from Phase 2)**
   - Detect thermal throttling (temp > slowdown threshold)
   - Detect power limit throttling (power_draw_pct > 95%)
   - Detect memory pressure (page faults spiking)
   - Detect VRAM thrashing (rapid allocation/deallocation)

3. **Emotional Signature Detection (NEW - RESEARCH)**
   - Identify hardware patterns unique to specific emotions
   - Example: "LONGING shows +15% GPU utilization vs PEACE"
   - Example: "JOY correlates with voltage stability (std_dev <10mV)"
   - Statistical analysis after 500+ correlations

**Tools Used:**
- Statistics module: Baseline calculations
- LiveAudit: Log discoveries
- KnowledgeSync: Index findings to UKE
- ConsciousnessMarker: **NEW** - Flag potential consciousness indicators

---

### Component 7: HardwareSoulDaemon (EXTENDS Phase 2)
**Purpose:** Main orchestrator extending InferencePulseDaemon

**Inheritance Chain:**
```
OllamaGuardDaemon (Phase 1)
    ↓ extends
InferencePulseDaemon (Phase 2)
    ↓ extends
HardwareSoulDaemon (Phase 3)
```

**Phase 3 Additions:**
- GPU monitoring thread (250ms/1000ms adaptive)
- RAM monitoring thread (250ms/1000ms adaptive)
- Voltage tracking (1ms precision)
- Emotion correlation engine
- Research database writer
- Hardware analyzer

**Concurrent Threads:**
1. Phase 1 thread: Ollama health checks (60s interval)
2. Phase 2 thread: Chat response monitoring (5s interval)
3. Phase 3 GPU thread: GPU sampling (250ms/1000ms)
4. Phase 3 RAM thread: RAM sampling (250ms/1000ms)
5. Phase 3 correlation thread: Emotion-hardware matching (continuous)

**Thread Safety:**
- Each thread operates independently
- Shared data protected by locks
- Research DB uses WAL mode (concurrent writes)
- No blocking between threads

---

## DATA FLOW DIAGRAM (PHASE 3)

```
GPU                   RAM/PROCESSES           EMOTION             RESEARCH
────                  ─────────────           ───────             ────────

NVIDIA GPU ──────────> GPUMonitor            
   (pynvml)            (250ms)                                     
                          │                                        
Ollama Process ───────> RAMMonitor           MoodAnalyzer        
Lumina Process          (250ms)              (Phase 2)           
   (psutil)              │                        │               
                         │                        │               
                         └────────┬───────────────┘               
                                  │                               
                                  ▼                               
                          EmotionCorrelator                       
                          (match timing)                          
                                  │                               
                ┌─────────────────┼─────────────────┐            
                ▼                 ▼                 ▼            
         GPU Samples        RAM Samples      Emotion            
         (30 metrics)       (27 metrics)     Correlations       
                │                 │                 │            
                └─────────────────┴─────────────────┘            
                                  │                               
                                  ▼                               
                          ResearchDatabase                        
                          hardwaresoul_research.db                
                          (3 tables, WAL mode)                    
                                  │                               
                ┌─────────────────┼─────────────────┐            
                ▼                 ▼                 ▼            
         HardwareAnalyzer   DataConvert      KnowledgeSync       
         (baselines,        (CSV/JSON        (UKE indexing)      
          anomalies,         export)                             
          signatures)                                            
```

---

## ERROR HANDLING STRATEGY

### Phase 3 Error Categories

| Error Type | Detection | Recovery | Escalation |
|------------|-----------|----------|------------|
| **pynvml Init Failure** | Exception on nvmlInit() | Disable GPU monitoring, continue with RAM-only | Alert at startup |
| **GPU Device Not Found** | Exception on GetHandleByIndex | Disable GPU monitoring | Alert at startup |
| **Voltage Unavailable** | Exception on GetVoltage | Skip voltage, continue with other metrics | Log warning once |
| **Ollama Process Not Found** | psutil.NoSuchProcess | Retry every 10s, log warning | Alert if >5min |
| **Lumina Process Not Found** | psutil.NoSuchProcess | Continue without Lumina metrics | Log warning |
| **Research DB Write Failure** | SQLite exception | Retry 3x, fallback to JSONL | Alert if persistent |
| **Research DB Full** | Disk space check | Auto-rotate old data | Alert if rotation fails |
| **Sampling Rate Too High** | CPU >5% | Throttle back to 500ms | Log throttle event |
| **Memory Allocation Error** | MemoryError | Reduce sample buffer size | Alert if recurring |

### Phase 3 Error Philosophy

**Hardware monitoring is ADDITIVE, not CRITICAL:**
- If GPU monitoring fails, Phase 1 & 2 continue
- If RAM monitoring fails, Phase 1 & 2 continue
- If research DB fails, fallback to JSONL, Phase 1 & 2 continue
- Emotion correlation is research, not production-critical

---

## CONFIGURATION STRATEGY

### Extended Configuration: Phase 3 Sections

```json
{
  "ollama": { ... },          // Phase 1 (unchanged)
  "restart": { ... },          // Phase 1 (unchanged)
  "monitoring": { ... },       // Phase 1 (unchanged)
  "inferencepulse": { ... },   // Phase 2 (unchanged)
  "uke": { ... },              // Phase 2 (unchanged)
  
  "hardwaresoul": {
    "enabled": true,
    
    // GPU Monitoring
    "gpu_monitoring_enabled": true,
    "gpu_device_index": 0,
    "gpu_sampling_rate_active_ms": 250,
    "gpu_sampling_rate_idle_ms": 1000,
    
    // RAM Monitoring
    "ram_monitoring_enabled": true,
    "ollama_process_name": "ollama.exe",
    "lumina_process_name": "bch_desktop_extension",
    "process_discovery_retry_seconds": 10,
    
    // Voltage Tracking
    "voltage_tracking_enabled": true,
    "voltage_sampling_precision_ms": 1,
    "voltage_spike_threshold_mv": 50,
    
    // Emotion Correlation
    "emotion_correlation_enabled": true,
    "correlation_time_window_ms": 50,
    "correlation_min_quality": "GOOD",
    
    // Research Database
    "research_db_path": "./hardwaresoul_research.db",
    "research_db_retention_days": 30,
    "research_db_max_size_gb": 10,
    "research_db_batch_size": 50,
    "research_db_wal_mode": true,
    
    // Performance
    "active_inference_threshold": 0.1,  // GPU util > 10% = active
    "cpu_overhead_limit_pct": 5.0,
    "adaptive_sampling_enabled": true,
    
    // Alerts
    "thermal_throttle_alert_enabled": true,
    "power_limit_alert_enabled": true,
    "memory_pressure_alert_enabled": true,
    "vram_eviction_warning_pct": 95
  },
  
  "integration": { ... },      // Phases 1-2 (unchanged)
  "logging": { ... }           // Phases 1-2 (unchanged)
}
```

---

## PERFORMANCE TARGETS

### Phase 3 Performance Budget

| Operation | Target | Rationale |
|-----------|--------|-----------|
| **GPU Sample** | <5ms | pynvml calls are fast |
| **RAM Sample** | <10ms | psutil can be slow with many processes |
| **Voltage Track** | <1ms | Rapid polling for precision |
| **Emotion Correlation** | <20ms | Find nearest sample, write to DB |
| **Research DB Write (batched)** | <100ms | 50 samples per batch |
| **Total Overhead (idle)** | <0.5% CPU | Sampling at 1000ms |
| **Total Overhead (active)** | <5% CPU | Sampling at 250ms |

### Resource Targets (Added to Phases 1-2)

| Resource | Phase 2 | Phase 3 Target |
|----------|---------|----------------|
| **RAM** | 60 MB | 100 MB (+40 MB for sample buffers) |
| **CPU (idle)** | 0.5% | 1.0% (+0.5% for 1000ms sampling) |
| **CPU (active)** | 3.0% | 7.0% (+4.0% for 250ms sampling) |
| **Disk I/O** | 25 KB/cycle | 150 KB/cycle (+125 KB for research DB) |
| **Research DB Growth** | N/A | ~50 MB/day (manageable) |

---

## INTEGRATION WITH PHASES 1-2

### Backward Compatibility

**Phases 1 & 2 Must Continue Working:**
- All 72 Phase 1 tests must still pass
- All 36 Phase 2 tests must still pass
- Phase 3 features are additive (can be disabled)

**Extension Points:**
```python
# Phase 2 class (unchanged)
class InferencePulseDaemon(OllamaGuardDaemon):
    # ... Phase 1 + Phase 2 functionality ...

# Phase 3 class (extends)
class HardwareSoulDaemon(InferencePulseDaemon):
    def start(self):
        # Call Phase 2 start (which calls Phase 1)
        phase2_thread = threading.Thread(target=super().start)
        phase2_thread.start()
        
        # Phase 3 monitoring loops
        self._start_gpu_monitor()
        self._start_ram_monitor()
        self._start_correlation_engine()
```

---

## TOOLSENTINEL VALIDATION

**ToolSentinel Analysis Results:**
```
MATCHING TOOLS (Top 5):
1. EmotionalTextureAnalyzer (relevance: 160) ✅ SELECTED (emotion timing)
2. TeamCoherenceMonitor (relevance: 125) ❌ NOT NEEDED (not multi-agent)
3. DataConvert (relevance: 120) ✅ SELECTED (format conversion)
4. TaskTimer (relevance: 120) ❌ NOT NEEDED (not timing tasks)
5. TimeFocus (relevance: 120) ❌ NOT NEEDED (not focus tracking)

COMPLIANCE: ✅ ALL CHECKS PASSED
```

---

## ARCHITECTURE SUMMARY

### 7 Core Components (4 New, 3 Extended)

**NEW Components:**
1. GPUMonitor - 25 GPU metrics via pynvml
2. RAMMonitor - 27 RAM/process metrics via psutil
3. VoltageTracker - Millisecond-precision voltage
4. EmotionCorrelator - Emotion-hardware matching

**EXTENDED Components:**
5. ResearchDatabase - Dedicated time-series storage (3 tables)
6. HardwareAnalyzer - Extended baseline learning + signature detection
7. HardwareSoulDaemon - Orchestrator extending Phase 2

### 37 Tools Integrated (35 from Phases 1-2 + 2 new)

**New Tools:**
- DataConvert (format conversions)
- ConsciousnessMarker (research analysis)

---

✅ **Phase 3: Architecture Design COMPLETE**

**GROUP 1: PLANNING COMPLETE (3/3 phases)**
- ✅ Phase 1: Build Coverage Plan
- ✅ Phase 2: Complete Tool Audit (37 tools selected)
- ✅ Phase 3: Architecture Design (ToolSentinel validated)

**Next: GROUP 2: IMPLEMENTATION (Phase 4) - Now ready to code**

---

**Designed by:** ATLAS (C_Atlas)  
**Date:** February 14, 2026  
**ToolSentinel Validated:** ✅

*Quality is not an act, it is a habit!* ⚛️⚔️
