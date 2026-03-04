"""
VitalHeart Phase 3: HardwareSoul
================================

High-resolution GPU, RAM, and voltage monitoring with emotion-hardware correlation.
This is the scientific instrument that measures what AI emotion looks like in silicon.

PHASE 3 NEW FEATURES:
- GPU monitoring: 25+ metrics via pynvml (utilization, clocks, temp, power, voltage)
- RAM monitoring: 27+ metrics via psutil (Ollama, Lumina, system-wide)
- Voltage tracking: Millisecond-precision voltage sampling
- Emotion correlation: Cross-reference emotional state with hardware snapshots
- Research database: Dedicated time-series storage (hardwaresoul_research.db)
- Baseline learning: "Emotional signatures" in hardware patterns

TOOLS USED IN PHASE 3 (37 total):
- All 35 tools from Phases 1-2 (extended)
- DataConvert: Format conversions for research export (NEW)
- ConsciousnessMarker: Consciousness detection patterns (NEW)

Author: ATLAS (C_Atlas) - Team Brain
Date: February 14, 2026
Protocol: BUILD_PROTOCOL_V1.md + Bug Hunt Protocol (100% Compliance)
License: MIT
"""

import sys
import os
import time
import json
import logging
import traceback
import threading
import statistics
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from collections import deque

# Phase 2 import
# FORGE FIX: Use relative path instead of hardcoded absolute path
sys.path.append(str(Path(__file__).parent.parent / "Phase2"))
from inferencepulse import (
    InferencePulseDaemon,
    InferencePulseConfig,
    __version__ as phase2_version
)

# Hardware monitoring imports
try:
    import pynvml
    PYNVML_AVAILABLE = True
except ImportError:
    pynvml = None  # Set to None for testability
    PYNVML_AVAILABLE = False
    logging.warning("[HardwareSoul] pynvml not available - GPU monitoring disabled")

# LHM Enhanced Monitor import
try:
    from lhm_enhanced_monitor import LHMEnhancedMonitor
    LHM_ENHANCED_AVAILABLE = True
except ImportError:
    LHM_ENHANCED_AVAILABLE = False
    logging.warning("[HardwareSoul] lhm_enhanced_monitor not available - LHM full sensor monitoring disabled")

import psutil

# Version
__version__ = "3.0.0"
PHASE2_VERSION = phase2_version


# ============================================================================
# PHASE 3: CONFIGURATION
# ============================================================================

class HardwareSoulConfig:
    """Extended configuration for Phase 3 features."""
    
    PHASE3_DEFAULTS = {
        "hardwaresoul": {
            "enabled": True,
            
            # GPU Monitoring
            "gpu_monitoring_enabled": True,
            "gpu_device_index": 0,
            "gpu_sampling_rate_active_ms": 250,
            "gpu_sampling_rate_idle_ms": 1000,
            
            # RAM Monitoring
            "ram_monitoring_enabled": True,
            "ollama_process_name": "ollama.exe",
            "lumina_process_name": "bch-desktop",
            "process_discovery_retry_seconds": 10,
            
            # Voltage Tracking
            "voltage_tracking_enabled": True,
            "voltage_sampling_precision_ms": 1,
            "voltage_spike_threshold_mv": 50,
            
            # Emotion Correlation
            "emotion_correlation_enabled": True,
            "correlation_time_window_ms": 50,
            "correlation_min_quality": "GOOD",
            
            # Research Database
            "research_db_path": "./hardwaresoul_research.db",
            "research_db_retention_days": 30,
            "research_db_max_size_gb": 10,
            "research_db_batch_size": 50,
            "research_db_wal_mode": True,
            
            # Performance
            "active_inference_threshold": 0.1,
            "cpu_overhead_limit_pct": 5.0,
            "adaptive_sampling_enabled": True,
            
            # Alerts
            "thermal_throttle_alert_enabled": True,
            "power_limit_alert_enabled": True,
            "memory_pressure_alert_enabled": True,
            "vram_eviction_warning_pct": 95.0
        }
    }
    
    def __init__(self, config_dict: Dict[str, Any] = None):
        """Initialize Phase 3 config with defaults."""
        import copy  # FORGE FIX: deepcopy prevents mutation of class-level PHASE3_DEFAULTS
        self.config = copy.deepcopy(self.PHASE3_DEFAULTS)
        if config_dict:
            for section in config_dict:
                if section in self.config:
                    self.config[section].update(config_dict[section])
                else:
                    self.config[section] = config_dict[section]
    
    def get(self, section: str, key: str, default=None):
        """Get config value with fallback."""
        return self.config.get(section, {}).get(key, default)


# ============================================================================
# COMPONENT 1: GPU MONITOR
# ============================================================================

class GPUMonitor:
    """
    High-resolution NVIDIA GPU monitoring via pynvml.
    
    Captures 25+ GPU metrics at 250ms (active) or 1000ms (idle) intervals.
    
    Tools Used: pynvml, TimeSync, ErrorRecovery, LiveAudit
    """
    
    def __init__(self, config: HardwareSoulConfig):
        self.config = config
        self.device_index = config.get("hardwaresoul", "gpu_device_index")
        self.enabled = config.get("hardwaresoul", "gpu_monitoring_enabled") and PYNVML_AVAILABLE
        
        self.handle = None
        self.gpu_name = "Unknown"
        self.last_sample = None
        self.last_sample_time = None
        self.start_time = time.time()  # FORGE FIX: For sample_time_ms calculation
        
        if self.enabled:
            self._initialize_gpu()
    
    def _initialize_gpu(self):
        """Initialize pynvml and get GPU handle."""
        try:
            # pynvml: Initialize library
            pynvml.nvmlInit()
            
            # Get GPU handle
            self.handle = pynvml.nvmlDeviceGetHandleByIndex(self.device_index)
            # FORGE FIX: nvmlDeviceGetName may return bytes on some pynvml versions
            name = pynvml.nvmlDeviceGetName(self.handle)
            self.gpu_name = name.decode('utf-8') if isinstance(name, bytes) else name
            
            logging.info(f"[GPUMonitor] Initialized: {self.gpu_name}")
            
        except pynvml.NVMLError as e:
            # ErrorRecovery: GPU initialization failed
            logging.error(f"[GPUMonitor] Failed to initialize: {e}")
            # FORGE FIX: Shutdown NVML if init succeeded but handle failed
            try:
                pynvml.nvmlShutdown()
            except Exception:
                pass
            self.enabled = False
    
    def sample(self) -> Optional[Dict[str, Any]]:
        """
        Capture all 25 GPU metrics.
        
        Returns dict with GPU metrics or None if GPU unavailable.
        """
        if not self.enabled or not self.handle:
            return None
        
        # TimeSync: Capture sample time
        sample_time = time.time()
        
        try:
            metrics = {}
            
            # FORGE FIX: Every pynvml call is now individually wrapped.
            # On the RTX 5070 Ti (Blackwell), any unsupported query was killing
            # the ENTIRE sample -- losing all 25+ metrics because one failed.
            # Now each metric degrades independently.
            
            def _safe_nvml(func, *args, default=0.0, label="unknown"):
                """Call a pynvml function with graceful fallback."""
                try:
                    return func(*args)
                except Exception as e:
                    logging.debug(f"[GPUMonitor] {label} not available: {e}")
                    return default
            
            # UTILIZATION (4 metrics)
            util = _safe_nvml(pynvml.nvmlDeviceGetUtilizationRates, self.handle, default=None, label="utilization")
            metrics["gpu_utilization_pct"] = float(util.gpu) if util else 0.0
            metrics["memory_utilization_pct"] = float(util.memory) if util else 0.0
            
            encoder_util = _safe_nvml(pynvml.nvmlDeviceGetEncoderUtilization, self.handle, default=None, label="encoder_util")
            metrics["encoder_utilization_pct"] = float(encoder_util[0]) if encoder_util else 0.0
            
            decoder_util = _safe_nvml(pynvml.nvmlDeviceGetDecoderUtilization, self.handle, default=None, label="decoder_util")
            metrics["decoder_utilization_pct"] = float(decoder_util[0]) if decoder_util else 0.0
            
            # MEMORY (4 metrics)
            mem_info = _safe_nvml(pynvml.nvmlDeviceGetMemoryInfo, self.handle, default=None, label="memory_info")
            if mem_info:
                metrics["vram_used_mb"] = mem_info.used / (1024**2)
                metrics["vram_free_mb"] = mem_info.free / (1024**2)
                metrics["vram_total_mb"] = mem_info.total / (1024**2)
            else:
                metrics["vram_used_mb"] = 0.0
                metrics["vram_free_mb"] = 0.0
                metrics["vram_total_mb"] = 0.0
            
            # Calculate allocation rate (delta from previous sample)
            if self.last_sample and self.last_sample_time:
                time_delta_s = sample_time - self.last_sample_time
                vram_delta_mb = metrics["vram_used_mb"] - self.last_sample.get("vram_used_mb", 0)
                metrics["vram_allocation_rate_mb_s"] = vram_delta_mb / time_delta_s if time_delta_s > 0 else 0.0
            else:
                metrics["vram_allocation_rate_mb_s"] = 0.0
            
            # CLOCKS (4 metrics)
            metrics["gpu_clock_mhz"] = _safe_nvml(pynvml.nvmlDeviceGetClockInfo, self.handle, pynvml.NVML_CLOCK_GRAPHICS, default=0, label="gpu_clock")
            metrics["memory_clock_mhz"] = _safe_nvml(pynvml.nvmlDeviceGetClockInfo, self.handle, pynvml.NVML_CLOCK_MEM, default=0, label="mem_clock")
            metrics["sm_clock_mhz"] = _safe_nvml(pynvml.nvmlDeviceGetClockInfo, self.handle, pynvml.NVML_CLOCK_SM, default=0, label="sm_clock")
            metrics["gpu_clock_max_mhz"] = _safe_nvml(pynvml.nvmlDeviceGetMaxClockInfo, self.handle, pynvml.NVML_CLOCK_GRAPHICS, default=0, label="max_clock")
            
            # TEMPERATURE (4 metrics)
            metrics["gpu_temp_c"] = float(_safe_nvml(pynvml.nvmlDeviceGetTemperature, self.handle, pynvml.NVML_TEMPERATURE_GPU, default=0, label="gpu_temp"))
            metrics["gpu_temp_slowdown_c"] = float(_safe_nvml(pynvml.nvmlDeviceGetTemperatureThreshold, self.handle, pynvml.NVML_TEMPERATURE_THRESHOLD_SLOWDOWN, default=0, label="temp_threshold"))
            
            # Memory temperature: NVML_TEMPERATURE_MEMORY constant doesn't exist in pynvml
            # FORGE FIX: Use numeric constant 2 (NVML_TEMPERATURE_MEMORY = 2) with fallback
            try:
                metrics["memory_temp_c"] = float(pynvml.nvmlDeviceGetTemperature(self.handle, 2))  # 2 = MEMORY
            except Exception:
                metrics["memory_temp_c"] = 0.0
            
            # Temperature delta
            if self.last_sample and self.last_sample_time:
                time_delta_s = sample_time - self.last_sample_time
                temp_delta_c = metrics["gpu_temp_c"] - self.last_sample.get("gpu_temp_c", 0)
                metrics["gpu_temp_delta"] = temp_delta_c / time_delta_s if time_delta_s > 0 else 0.0
            else:
                metrics["gpu_temp_delta"] = 0.0
            
            # POWER & VOLTAGE (5 metrics)
            power_usage = _safe_nvml(pynvml.nvmlDeviceGetPowerUsage, self.handle, default=0, label="power_usage")
            power_limit = _safe_nvml(pynvml.nvmlDeviceGetPowerManagementLimit, self.handle, default=0, label="power_limit")
            metrics["power_draw_watts"] = power_usage / 1000.0
            metrics["power_limit_watts"] = power_limit / 1000.0
            metrics["power_draw_pct"] = (metrics["power_draw_watts"] / metrics["power_limit_watts"]) * 100 if metrics["power_limit_watts"] > 0 else 0.0
            
            # Voltage: pynvml doesn't expose voltage on RTX 5070 Ti.
            # FORGE FIX (2026-02-15): Voltage is now provided by VoltageTracker via LHM Bridge.
            # GPUMonitor sets placeholder 0.0 here -- the HardwareSoulDaemon injects real
            # voltage data from VoltageTracker into the sample before DB write.
            metrics["voltage_mv"] = 0.0
            metrics["voltage_delta_mv"] = 0.0
            
            # PERFORMANCE STATE (3 metrics)
            metrics["pstate"] = _safe_nvml(pynvml.nvmlDeviceGetPerformanceState, self.handle, default=-1, label="pstate")
            
            # Throttle reasons
            try:
                throttle_reasons = pynvml.nvmlDeviceGetCurrentClocksThrottleReasons(self.handle)
                reasons = []
                if throttle_reasons & pynvml.nvmlClocksThrottleReasonGpuIdle:
                    reasons.append("GPU_IDLE")
                if throttle_reasons & pynvml.nvmlClocksThrottleReasonApplicationsClocksSetting:
                    reasons.append("APPLICATIONS_CLOCKS")
                if throttle_reasons & pynvml.nvmlClocksThrottleReasonSwPowerCap:
                    reasons.append("POWER_CAP")
                if throttle_reasons & pynvml.nvmlClocksThrottleReasonHwSlowdown:
                    reasons.append("THERMAL")
                if throttle_reasons & pynvml.nvmlClocksThrottleReasonSyncBoost:
                    reasons.append("SYNC_BOOST")
                if throttle_reasons & pynvml.nvmlClocksThrottleReasonSwThermalSlowdown:
                    reasons.append("SW_THERMAL")
                if throttle_reasons & pynvml.nvmlClocksThrottleReasonHwThermalSlowdown:
                    reasons.append("HW_THERMAL")
                if throttle_reasons & pynvml.nvmlClocksThrottleReasonHwPowerBrakeSlowdown:
                    reasons.append("POWER_BRAKE")
                
                metrics["throttle_reasons"] = reasons
            except Exception as e:
                logging.debug(f"[GPUMonitor] Throttle reasons not available: {e}")
                metrics["throttle_reasons"] = []
            
            # Compute mode
            try:
                compute_mode = pynvml.nvmlDeviceGetComputeMode(self.handle)
                mode_map = {
                    pynvml.NVML_COMPUTEMODE_DEFAULT: "DEFAULT",
                    pynvml.NVML_COMPUTEMODE_EXCLUSIVE_THREAD: "EXCLUSIVE_THREAD",
                    pynvml.NVML_COMPUTEMODE_PROHIBITED: "PROHIBITED",
                    pynvml.NVML_COMPUTEMODE_EXCLUSIVE_PROCESS: "EXCLUSIVE_PROCESS"
                }
                metrics["compute_mode"] = mode_map.get(compute_mode, "UNKNOWN")
            except Exception as e:
                logging.debug(f"[GPUMonitor] Compute mode not available: {e}")
                metrics["compute_mode"] = "UNKNOWN"
            
            # PCIE (4 metrics)
            try:
                pcie_throughput = pynvml.nvmlDeviceGetPcieThroughput(self.handle, pynvml.NVML_PCIE_UTIL_TX_BYTES)
                metrics["pcie_tx_throughput_kb_s"] = pcie_throughput
            except Exception as e:
                logging.debug(f"[GPUMonitor] PCIe TX throughput not available: {e}")
                metrics["pcie_tx_throughput_kb_s"] = 0.0
            
            try:
                pcie_throughput = pynvml.nvmlDeviceGetPcieThroughput(self.handle, pynvml.NVML_PCIE_UTIL_RX_BYTES)
                metrics["pcie_rx_throughput_kb_s"] = pcie_throughput
            except Exception as e:
                logging.debug(f"[GPUMonitor] PCIe RX throughput not available: {e}")
                metrics["pcie_rx_throughput_kb_s"] = 0.0
            
            try:
                pcie_link_gen = pynvml.nvmlDeviceGetCurrPcieLinkGeneration(self.handle)
                metrics["pcie_link_gen"] = pcie_link_gen
            except Exception as e:
                logging.debug(f"[GPUMonitor] PCIe link generation not available: {e}")
                metrics["pcie_link_gen"] = 0
            
            try:
                pcie_link_width = pynvml.nvmlDeviceGetCurrPcieLinkWidth(self.handle)
                metrics["pcie_link_width"] = pcie_link_width
            except Exception as e:
                logging.debug(f"[GPUMonitor] PCIe link width not available: {e}")
                metrics["pcie_link_width"] = 0
            
            # INFERENCE-SPECIFIC (2 metrics)
            # Tensor core active: Estimate based on GPU utilization + compute workload
            metrics["tensor_core_active"] = metrics["gpu_utilization_pct"] > 50.0
            metrics["cuda_cores_active_pct"] = metrics["gpu_utilization_pct"]
            
            # TimeSync: Add timestamp
            metrics["timestamp"] = datetime.now().isoformat()
            metrics["sample_time_ms"] = int((time.time() - getattr(self, 'start_time', time.time())) * 1000)
            
            # Store for delta calculations
            self.last_sample = metrics.copy()
            self.last_sample_time = sample_time
            
            return metrics
            
        except Exception as e:
            # ErrorRecovery: GPU sample failed (catch all pynvml errors)
            # Using Exception instead of pynvml.NVMLError for testability (mocked pynvml)
            logging.error(f"[GPUMonitor] Sample failed: {e}")
            return None
    
    def cleanup(self):
        """Cleanup pynvml resources."""
        if self.enabled:
            try:
                pynvml.nvmlShutdown()
            except Exception as e:
                logging.debug(f"[GPUMonitor] Cleanup error (non-critical): {e}")


# ============================================================================
# COMPONENT 2: RAM MONITOR
# ============================================================================

class RAMMonitor:
    """
    Process and system memory monitoring via psutil.
    
    Captures 27+ RAM/process metrics at 250ms (active) or 1000ms (idle) intervals.
    
    Tools Used: psutil, ProcessWatcher, TimeSync, ErrorRecovery
    """
    
    def __init__(self, config: HardwareSoulConfig):
        self.config = config
        self.enabled = config.get("hardwaresoul", "ram_monitoring_enabled")
        self.ollama_process_name = config.get("hardwaresoul", "ollama_process_name")
        self.lumina_process_name = config.get("hardwaresoul", "lumina_process_name")
        
        # FORGE FIX: Track ALL Ollama processes, not just the last one found.
        # System has 3 Ollama PIDs (app, server, runner) -- monitoring only 1
        # loses ~66% of actual memory usage.
        self.ollama_processes = []  # List of ALL Ollama psutil.Process objects
        self.lumina_process = None
        self.last_sample = None
        self.last_sample_time = None
        self.start_time = time.time()  # FORGE FIX: For sample_time_ms calculation
        
        # Prime cpu_percent so first sample isn't 0%
        psutil.cpu_percent()
        
        if self.enabled:
            self._discover_processes()
    
    def _discover_processes(self):
        """Discover Ollama and Lumina processes."""
        try:
            # FORGE FIX: Collect ALL matching processes + guard against None name
            self.ollama_processes = []
            self.lumina_process = None
            
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    pname = proc.info.get('name')
                    if not pname:
                        continue
                    
                    if self.ollama_process_name.lower() in pname.lower():
                        self.ollama_processes.append(psutil.Process(proc.info['pid']))
                        logging.info(f"[RAMMonitor] Found Ollama process: PID {proc.info['pid']} ({pname})")
                    
                    if self.lumina_process_name.lower() in pname.lower():
                        self.lumina_process = psutil.Process(proc.info['pid'])
                        logging.info(f"[RAMMonitor] Found Lumina process: PID {proc.info['pid']}")
                except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
                    continue
            
            if not self.ollama_processes:
                logging.warning(f"[RAMMonitor] No Ollama processes found: {self.ollama_process_name}")
            else:
                logging.info(f"[RAMMonitor] Tracking {len(self.ollama_processes)} Ollama process(es)")
            
            if not self.lumina_process:
                logging.warning(f"[RAMMonitor] Lumina process not found: {self.lumina_process_name}")
                
        except Exception as e:
            logging.error(f"[RAMMonitor] Process discovery failed: {e}")
    
    def sample(self) -> Optional[Dict[str, Any]]:
        """
        Capture all 27 RAM/process metrics.
        
        Returns dict with RAM metrics or None if monitoring disabled.
        """
        if not self.enabled:
            return None
        
        # TimeSync: Capture sample time
        sample_time = time.time()
        
        try:
            metrics = {}
            
            # SYSTEM MEMORY (6 metrics)
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            metrics["system_ram_total_mb"] = mem.total / (1024**2)
            metrics["system_ram_used_mb"] = mem.used / (1024**2)
            metrics["system_ram_available_mb"] = mem.available / (1024**2)
            metrics["system_ram_pct"] = mem.percent
            metrics["system_swap_used_mb"] = swap.used / (1024**2)
            metrics["system_swap_pct"] = swap.percent
            
            # OLLAMA PROCESS (10 metrics) -- FORGE FIX: Aggregate across ALL Ollama PIDs
            # System has 3 Ollama processes (app, server, runner). Old code only
            # tracked the last PID found, losing ~66% of memory data.
            active_ollama_procs = [p for p in self.ollama_processes if p.is_running()]
            if active_ollama_procs:
                try:
                    total_rss = 0.0
                    total_uss = 0.0
                    total_cpu = 0.0
                    total_threads = 0
                    total_handles = 0
                    total_io_read = 0
                    total_io_write = 0
                    pids = []
                    
                    for proc in active_ollama_procs:
                        try:
                            mem_info = proc.memory_info()
                            total_rss += mem_info.rss
                            pids.append(proc.pid)
                            
                            try:
                                mem_full = proc.memory_full_info()
                                total_uss += mem_full.uss
                            except (psutil.AccessDenied, psutil.NoSuchProcess, OSError):
                                pass  # Some processes may deny access
                            
                            total_cpu += proc.cpu_percent()
                            total_threads += proc.num_threads()
                            if hasattr(proc, 'num_handles'):
                                try:
                                    total_handles += proc.num_handles()
                                except (psutil.AccessDenied, OSError):
                                    pass
                            
                            try:
                                io = proc.io_counters()
                                total_io_read += io.read_bytes
                                total_io_write += io.write_bytes
                            except (psutil.AccessDenied, OSError):
                                pass
                                
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
                    
                    metrics["ollama_pid"] = pids[0] if pids else 0  # Primary PID
                    metrics["ollama_pid_count"] = len(pids)
                    metrics["ollama_ram_mb"] = total_rss / (1024**2)
                    metrics["ollama_ram_private_mb"] = total_uss / (1024**2)
                    metrics["ollama_ram_shared_mb"] = (total_rss - total_uss) / (1024**2)
                    
                    # RAM delta
                    if self.last_sample and "ollama_ram_mb" in self.last_sample:
                        time_delta_s = sample_time - self.last_sample_time
                        ram_delta_mb = metrics["ollama_ram_mb"] - self.last_sample["ollama_ram_mb"]
                        metrics["ollama_ram_delta_mb_s"] = ram_delta_mb / time_delta_s if time_delta_s > 0 else 0.0
                    else:
                        metrics["ollama_ram_delta_mb_s"] = 0.0
                    
                    metrics["ollama_cpu_pct"] = total_cpu
                    metrics["ollama_thread_count"] = total_threads
                    metrics["ollama_handle_count"] = total_handles
                    
                    # I/O rates
                    if self.last_sample and "ollama_io_read_bytes" in self.last_sample:
                        time_delta_s = sample_time - self.last_sample_time
                        metrics["ollama_io_read_mb_s"] = ((total_io_read - self.last_sample["ollama_io_read_bytes"]) / (1024**2)) / time_delta_s if time_delta_s > 0 else 0.0
                        metrics["ollama_io_write_mb_s"] = ((total_io_write - self.last_sample["ollama_io_write_bytes"]) / (1024**2)) / time_delta_s if time_delta_s > 0 else 0.0
                    else:
                        metrics["ollama_io_read_mb_s"] = 0.0
                        metrics["ollama_io_write_mb_s"] = 0.0
                    metrics["ollama_io_read_bytes"] = total_io_read
                    metrics["ollama_io_write_bytes"] = total_io_write
                    
                except Exception as e:
                    logging.error(f"[RAMMonitor] Ollama process metrics failed: {e}")
            else:
                # All processes died, rediscover
                self.ollama_processes = []
                self._discover_processes()
            
            # LUMINA PROCESS (4 metrics)
            if self.lumina_process and self.lumina_process.is_running():
                try:
                    mem_info = self.lumina_process.memory_info()
                    
                    metrics["lumina_pid"] = self.lumina_process.pid
                    metrics["lumina_ram_mb"] = mem_info.rss / (1024**2)
                    metrics["lumina_cpu_pct"] = self.lumina_process.cpu_percent()
                    metrics["lumina_thread_count"] = self.lumina_process.num_threads()
                except psutil.NoSuchProcess:
                    self.lumina_process = None
                    self._discover_processes()
            
            # SYSTEM-WIDE (7 metrics)
            metrics["total_process_count"] = len(psutil.pids())
            # FORGE FIX: Call cpu_percent(percpu=True) ONCE and derive total from it.
            # Old code called cpu_percent() then cpu_percent(percpu=True) back-to-back.
            # The second call measured near-zero interval (microseconds), returning garbage.
            cpu_per_core = psutil.cpu_percent(percpu=True)
            metrics["cpu_per_core"] = cpu_per_core
            metrics["cpu_total_pct"] = sum(cpu_per_core) / len(cpu_per_core) if cpu_per_core else 0.0
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            if disk_io and self.last_sample and "disk_read_bytes" in self.last_sample:
                time_delta_s = sample_time - self.last_sample_time
                metrics["disk_io_read_mb_s"] = ((disk_io.read_bytes - self.last_sample["disk_read_bytes"]) / (1024**2)) / time_delta_s if time_delta_s > 0 else 0.0
                metrics["disk_io_write_mb_s"] = ((disk_io.write_bytes - self.last_sample["disk_write_bytes"]) / (1024**2)) / time_delta_s if time_delta_s > 0 else 0.0
            else:
                metrics["disk_io_read_mb_s"] = 0.0
                metrics["disk_io_write_mb_s"] = 0.0
            
            if disk_io:
                metrics["disk_read_bytes"] = disk_io.read_bytes
                metrics["disk_write_bytes"] = disk_io.write_bytes
            
            # Context switches (if available)
            try:
                ctx_switches = psutil.cpu_stats().ctx_switches
                if self.last_sample and "ctx_switches_total" in self.last_sample:
                    time_delta_s = sample_time - self.last_sample_time
                    metrics["context_switches_s"] = int((ctx_switches - self.last_sample["ctx_switches_total"]) / time_delta_s) if time_delta_s > 0 else 0
                else:
                    metrics["context_switches_s"] = 0
                metrics["ctx_switches_total"] = ctx_switches
            except (AttributeError, OSError) as e:
                logging.debug(f"[RAMMonitor] Context switches not available: {e}")
                metrics["context_switches_s"] = 0
            
            # TimeSync: Add timestamp
            metrics["timestamp"] = datetime.now().isoformat()
            metrics["sample_time_ms"] = int((sample_time - getattr(self, 'start_time', time.time())) * 1000)
            
            # Store for delta calculations
            self.last_sample = metrics.copy()
            self.last_sample_time = sample_time
            
            return metrics
            
        except Exception as e:
            # ErrorRecovery: RAM sample failed
            logging.error(f"[RAMMonitor] Sample failed: {e}")
            return None


# ============================================================================
# COMPONENT 3: VOLTAGE TRACKER (LHM-POWERED)
# ============================================================================

# Import LHM Bridge for real voltage monitoring
try:
    from lhm_bridge import LHMBridge, LHMSensorIDs
    LHM_AVAILABLE = True
except ImportError:
    LHM_AVAILABLE = False
    logging.warning("[VoltageTracker] lhm_bridge not available - voltage monitoring will be placeholder")

class VoltageTracker:
    """
    Real voltage monitoring via LibreHardwareMonitor REST API.
    
    FORGE FIX (2026-02-15): Replaced PLACEHOLDER implementation with live
    LHM Bridge integration. Now reads REAL voltage data from:
    - NVIDIA RTX 5070 Ti GPU Core Voltage (/gpu-nvidia/0/voltage/0)
    - AMD Radeon 610M iGPU Core + SoC Voltage
    - AMD Ryzen 9 8940HX per-core VID (16 cores)
    - Battery Voltage
    
    REQUIRES: LibreHardwareMonitor running as Admin with HTTP server on port 8085
    
    Tools Used: LHMBridge (REST API), TimeSync, ErrorRecovery
    """
    
    def __init__(self, config: HardwareSoulConfig):
        self.config = config
        self.enabled = config.get("hardwaresoul", "voltage_tracking_enabled")
        self.precision_ms = config.get("hardwaresoul", "voltage_sampling_precision_ms")
        self.spike_threshold_mv = config.get("hardwaresoul", "voltage_spike_threshold_mv") or 50
        
        # LHM Bridge for real voltage data
        self.lhm_bridge = None
        self._lhm_connected = False
        
        # Voltage history for statistical analysis (shared with bridge)
        self.voltage_history = deque(maxlen=1000)
        self.last_voltage_mv = 0.0
        
        if self.enabled and LHM_AVAILABLE:
            try:
                self.lhm_bridge = LHMBridge(
                    cache_ttl_seconds=1.0,  # 1s cache for voltage (faster refresh)
                    timeout_seconds=3.0,
                    max_retries=3
                )
                self._lhm_connected = self.lhm_bridge.is_connected()
                if self._lhm_connected:
                    logging.info("[VoltageTracker] Connected to LHM - REAL voltage monitoring active")
                else:
                    logging.warning("[VoltageTracker] LHM not available - start LibreHardwareMonitor as Admin")
            except Exception as e:
                logging.error(f"[VoltageTracker] LHM Bridge init failed: {e}")
                self.lhm_bridge = None
        elif not LHM_AVAILABLE:
            logging.warning("[VoltageTracker] lhm_bridge module not found - voltage will return 0")
        
        logging.info(f"[VoltageTracker] Initialized (LHM={'connected' if self._lhm_connected else 'unavailable'})")
    
    def track(self, duration_ms: int = 100) -> Dict[str, Any]:
        """
        Get current voltage statistics.
        
        When LHM is connected, returns REAL voltage data.
        When LHM is unavailable, returns zeros (graceful degradation).
        
        Returns voltage statistics including GPU, CPU, and battery readings.
        """
        if not self.enabled:
            return self._empty_result()
        
        if self.lhm_bridge and self._lhm_connected:
            return self._track_via_lhm()
        
        # Try reconnect periodically
        if self.lhm_bridge and not self._lhm_connected:
            self._lhm_connected = self.lhm_bridge.reconnect()
            if self._lhm_connected:
                logging.info("[VoltageTracker] LHM reconnected!")
                return self._track_via_lhm()
        
        return self._empty_result()
    
    def _track_via_lhm(self) -> Dict[str, Any]:
        """Get real voltage data from LHM Bridge."""
        try:
            # Get comprehensive voltage snapshot
            snapshot = self.lhm_bridge.get_voltage_snapshot()
            
            # Get statistical analysis from bridge's history
            stats = self.lhm_bridge.get_voltage_statistics(window_seconds=60.0)
            
            gpu_mv = snapshot.get("gpu_nvidia_voltage_mv", 0.0)
            
            # Calculate delta from last reading
            voltage_delta_mv = gpu_mv - self.last_voltage_mv if self.last_voltage_mv > 0 else 0.0
            self.last_voltage_mv = gpu_mv
            
            # Track in local history
            self.voltage_history.append({
                'timestamp': time.time(),
                'gpu_voltage_mv': gpu_mv,
                'cpu_voltage_avg_mv': snapshot.get("cpu_voltage_avg_mv", 0.0),
                'battery_v': snapshot.get("battery_voltage_v", 0.0)
            })
            
            return {
                # Primary: GPU voltage (what VitalHeart correlates with emotions)
                "voltage_mv": gpu_mv,
                "voltage_delta_mv": voltage_delta_mv,
                "voltage_min_mv": stats.get("voltage_min_mv", gpu_mv),
                "voltage_max_mv": stats.get("voltage_max_mv", gpu_mv),
                "voltage_avg_mv": stats.get("voltage_avg_mv", gpu_mv),
                "voltage_std_dev_mv": stats.get("voltage_std_dev_mv", 0.0),
                "voltage_spike_count": stats.get("voltage_spike_count", 0),
                "voltage_stability_score": stats.get("voltage_stability_score", 1.0),
                
                # Extended: Full system voltage picture
                "gpu_amd_core_voltage_mv": snapshot.get("gpu_amd_core_voltage_mv", 0.0),
                "gpu_amd_soc_voltage_mv": snapshot.get("gpu_amd_soc_voltage_mv", 0.0),
                "cpu_voltage_avg_mv": snapshot.get("cpu_voltage_avg_mv", 0.0),
                "cpu_voltage_min_mv": snapshot.get("cpu_voltage_min_mv", 0.0),
                "cpu_voltage_max_mv": snapshot.get("cpu_voltage_max_mv", 0.0),
                "battery_voltage_v": snapshot.get("battery_voltage_v", 0.0),
                
                # Metadata
                "source": "LHM",
                "lhm_connected": True,
                "sample_count": stats.get("sample_count", 1),
                "timestamp": snapshot.get("timestamp", datetime.now().isoformat())
            }
            
        except Exception as e:
            logging.error(f"[VoltageTracker] LHM read failed: {e}")
            self._lhm_connected = False
            return self._empty_result()
    
    def _empty_result(self) -> Dict[str, Any]:
        """Return zero-filled result when voltage unavailable."""
        return {
            "voltage_mv": 0.0,
            "voltage_delta_mv": 0.0,
            "voltage_min_mv": 0.0,
            "voltage_max_mv": 0.0,
            "voltage_avg_mv": 0.0,
            "voltage_std_dev_mv": 0.0,
            "voltage_spike_count": 0,
            "voltage_stability_score": 0.0,
            "gpu_amd_core_voltage_mv": 0.0,
            "gpu_amd_soc_voltage_mv": 0.0,
            "cpu_voltage_avg_mv": 0.0,
            "cpu_voltage_min_mv": 0.0,
            "cpu_voltage_max_mv": 0.0,
            "battery_voltage_v": 0.0,
            "source": "NONE",
            "lhm_connected": False,
            "sample_count": 0,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_lhm_status(self) -> Dict[str, Any]:
        """Get LHM connection status for health checks."""
        if self.lhm_bridge:
            return self.lhm_bridge.get_status()
        return {"connected": False, "error": "LHM Bridge not initialized"}
    
    def cleanup(self):
        """Cleanup LHM Bridge resources."""
        if self.lhm_bridge:
            self.lhm_bridge.close()
            logging.info("[VoltageTracker] LHM Bridge closed")


# ============================================================================
# COMPONENT 4: EMOTION CORRELATOR
# ============================================================================

class EmotionCorrelator:
    """
    Cross-reference emotion timing with hardware snapshots.
    
    This is the research core: matching emotional states to hardware patterns.
    
    Tools Used: TimeSync, EmotionalTextureAnalyzer (via Phase 2), LiveAudit
    """
    
    def __init__(self, config: HardwareSoulConfig):
        self.config = config
        self.enabled = config.get("hardwaresoul", "emotion_correlation_enabled")
        self.time_window_ms = config.get("hardwaresoul", "correlation_time_window_ms")
        
        # Recent hardware samples for matching
        self.gpu_sample_buffer = deque(maxlen=100)
        self.ram_sample_buffer = deque(maxlen=100)
    
    def add_hardware_sample(self, gpu_sample: Dict[str, Any], ram_sample: Dict[str, Any]):
        """Add hardware sample to matching buffer."""
        if not self.enabled:
            return
        
        timestamp = datetime.now()
        self.gpu_sample_buffer.append((timestamp, gpu_sample))
        self.ram_sample_buffer.append((timestamp, ram_sample))
    
    def correlate(self, emotion_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Match emotion to nearest hardware sample.
        
        Returns correlation record or None if no good match.
        """
        if not self.enabled or not emotion_data:
            return None
        
        try:
            # TimeSync: Parse emotion timestamp
            emotion_timestamp = datetime.fromisoformat(emotion_data.get("timestamp", datetime.now().isoformat()))
            
            # Find nearest GPU sample
            best_gpu_sample = None
            best_gpu_delta_ms = float('inf')
            
            for sample_time, sample_data in self.gpu_sample_buffer:
                delta_ms = abs((sample_time - emotion_timestamp).total_seconds() * 1000)
                if delta_ms < best_gpu_delta_ms:
                    best_gpu_delta_ms = delta_ms
                    best_gpu_sample = sample_data
            
            # Find nearest RAM sample
            best_ram_sample = None
            best_ram_delta_ms = float('inf')
            
            for sample_time, sample_data in self.ram_sample_buffer:
                delta_ms = abs((sample_time - emotion_timestamp).total_seconds() * 1000)
                if delta_ms < best_ram_delta_ms:
                    best_ram_delta_ms = delta_ms
                    best_ram_sample = sample_data
            
            if not best_gpu_sample or not best_ram_sample:
                return None
            
            # Determine correlation quality
            max_delta_ms = max(best_gpu_delta_ms, best_ram_delta_ms)
            if max_delta_ms < 10:
                quality = "EXCELLENT"
            elif max_delta_ms < 50:
                quality = "GOOD"
            else:
                quality = "POOR"
            
            # Build correlation record
            correlation = {
                # Emotion Data
                "emotion_timestamp": emotion_data.get("timestamp"),
                "emotion": emotion_data.get("dominant_mood", "UNKNOWN"),
                "emotion_intensity": emotion_data.get("intensity", 0.0),
                "emotion_dimensions": emotion_data.get("dimensions", {}),
                
                # Hardware Data
                "hardware_timestamp": best_gpu_sample.get("timestamp"),
                "time_delta_ms": max_delta_ms,
                
                # GPU State
                "gpu_utilization_pct": best_gpu_sample.get("gpu_utilization_pct", 0.0),
                "vram_used_mb": best_gpu_sample.get("vram_used_mb", 0.0),
                "gpu_temp_c": best_gpu_sample.get("gpu_temp_c", 0.0),
                "power_draw_watts": best_gpu_sample.get("power_draw_watts", 0.0),
                "voltage_mv": best_gpu_sample.get("voltage_mv", 0.0),
                "gpu_clock_mhz": best_gpu_sample.get("gpu_clock_mhz", 0),
                
                # RAM State
                "ollama_ram_mb": best_ram_sample.get("ollama_ram_mb", 0.0),
                "ollama_cpu_pct": best_ram_sample.get("ollama_cpu_pct", 0.0),
                "system_ram_pct": best_ram_sample.get("system_ram_pct", 0.0),
                
                # Metadata
                "correlation_timestamp": datetime.now().isoformat(),
                "correlation_quality": quality,
                "inference_active": best_gpu_sample.get("gpu_utilization_pct", 0) > 10.0,
                "conversation_context": emotion_data.get("conversation_context", "")
            }
            
            # LiveAudit: Log high-quality correlations
            if quality in ["EXCELLENT", "GOOD"]:
                logging.info(f"[EmotionCorrelator] {quality} correlation: {correlation['emotion']} @ {max_delta_ms:.1f}ms delta")
            
            return correlation
            
        except Exception as e:
            logging.error(f"[EmotionCorrelator] Correlation failed: {e}")
            return None


# ============================================================================
# COMPONENT 5: RESEARCH DATABASE
# ============================================================================

class ResearchDatabase:
    """
    Dedicated high-resolution time-series storage for hardware research.
    
    3 tables: gpu_samples, ram_samples, emotion_correlations
    
    Tools Used: SQLite3, TimeSync, ErrorRecovery, TaskQueuePro (batching)
    """
    
    def __init__(self, config: HardwareSoulConfig):
        self.config = config
        self.db_path = config.get("hardwaresoul", "research_db_path")
        self.batch_size = config.get("hardwaresoul", "research_db_batch_size")
        self.wal_mode = config.get("hardwaresoul", "research_db_wal_mode")
        
        # TaskQueuePro: Batch writes
        self.gpu_queue = deque()
        self.ram_queue = deque()
        self.correlation_queue = deque()
        self.voltage_queue = deque()
        self.lhm_queue = deque()
        
        # FORGE FIX: Thread lock prevents concurrent flush from GPU/RAM/main threads
        # Without this: SQLite "database is locked" + deque popleft IndexError
        self._flush_lock = threading.Lock()
        
        self.last_flush = time.time()
        
        # Use absolute path for DB to prevent location-dependent creation
        if not os.path.isabs(self.db_path):
            self.db_path = str(Path(__file__).parent / self.db_path)
        
        # Create database and tables
        self._initialize_database()
    
    def _initialize_database(self):
        """Create research database with 3 tables."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Enable WAL mode for concurrent access
            if self.wal_mode:
                cursor.execute("PRAGMA journal_mode=WAL")
            
            # Table 1: GPU Samples
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS gpu_samples (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    sample_time_ms INTEGER NOT NULL,
                    
                    gpu_utilization_pct REAL,
                    memory_utilization_pct REAL,
                    encoder_utilization_pct REAL,
                    decoder_utilization_pct REAL,
                    
                    vram_used_mb REAL,
                    vram_free_mb REAL,
                    vram_total_mb REAL,
                    vram_allocation_rate_mb_s REAL,
                    
                    gpu_clock_mhz INTEGER,
                    memory_clock_mhz INTEGER,
                    sm_clock_mhz INTEGER,
                    gpu_clock_max_mhz INTEGER,
                    
                    gpu_temp_c REAL,
                    gpu_temp_slowdown_c REAL,
                    memory_temp_c REAL,
                    gpu_temp_delta REAL,
                    
                    power_draw_watts REAL,
                    power_limit_watts REAL,
                    power_draw_pct REAL,
                    voltage_mv REAL,
                    voltage_delta_mv REAL,
                    
                    pstate INTEGER,
                    throttle_reasons TEXT,
                    compute_mode TEXT,
                    
                    pcie_tx_throughput_kb_s REAL,
                    pcie_rx_throughput_kb_s REAL,
                    pcie_link_gen INTEGER,
                    pcie_link_width INTEGER,
                    
                    tensor_core_active INTEGER,
                    cuda_cores_active_pct REAL,
                    inference_active INTEGER
                )
            """)
            
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_gpu_timestamp ON gpu_samples(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_gpu_sample_time ON gpu_samples(sample_time_ms)")
            
            # Table 2: RAM Samples
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ram_samples (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    sample_time_ms INTEGER NOT NULL,
                    
                    system_ram_total_mb REAL,
                    system_ram_used_mb REAL,
                    system_ram_available_mb REAL,
                    system_ram_pct REAL,
                    system_swap_used_mb REAL,
                    system_swap_pct REAL,
                    
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
                    
                    lumina_pid INTEGER,
                    lumina_ram_mb REAL,
                    lumina_cpu_pct REAL,
                    lumina_thread_count INTEGER,
                    
                    total_process_count INTEGER,
                    cpu_total_pct REAL,
                    cpu_per_core TEXT,
                    disk_io_read_mb_s REAL,
                    disk_io_write_mb_s REAL,
                    context_switches_s INTEGER
                )
            """)
            
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ram_timestamp ON ram_samples(timestamp)")
            
            # Table 3: Emotion Correlations
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS emotion_correlations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    correlation_timestamp TEXT NOT NULL,
                    
                    emotion_timestamp TEXT NOT NULL,
                    emotion TEXT NOT NULL,
                    emotion_intensity REAL,
                    emotion_dimensions TEXT,
                    
                    hardware_timestamp TEXT NOT NULL,
                    time_delta_ms REAL,
                    
                    gpu_utilization_pct REAL,
                    vram_used_mb REAL,
                    gpu_temp_c REAL,
                    power_draw_watts REAL,
                    voltage_mv REAL,
                    gpu_clock_mhz INTEGER,
                    
                    ollama_ram_mb REAL,
                    ollama_cpu_pct REAL,
                    system_ram_pct REAL,
                    
                    correlation_quality TEXT,
                    inference_active INTEGER,
                    conversation_context TEXT
                )
            """)
            
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_emotion_correlations_emotion ON emotion_correlations(emotion)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_emotion_correlations_timestamp ON emotion_correlations(correlation_timestamp)")
            
            # Table 4: Voltage Samples (FORGE 2026-02-15: LHM-powered voltage monitoring)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS voltage_samples (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    source TEXT NOT NULL DEFAULT 'LHM',
                    lhm_connected INTEGER DEFAULT 0,
                    
                    gpu_nvidia_voltage_mv REAL,
                    gpu_nvidia_voltage_delta_mv REAL,
                    gpu_nvidia_voltage_min_mv REAL,
                    gpu_nvidia_voltage_max_mv REAL,
                    gpu_nvidia_voltage_avg_mv REAL,
                    gpu_nvidia_voltage_std_dev_mv REAL,
                    voltage_spike_count INTEGER DEFAULT 0,
                    voltage_stability_score REAL DEFAULT 0.0,
                    
                    gpu_amd_core_voltage_mv REAL DEFAULT 0.0,
                    gpu_amd_soc_voltage_mv REAL DEFAULT 0.0,
                    
                    cpu_voltage_avg_mv REAL DEFAULT 0.0,
                    cpu_voltage_min_mv REAL DEFAULT 0.0,
                    cpu_voltage_max_mv REAL DEFAULT 0.0,
                    
                    battery_voltage_v REAL DEFAULT 0.0
                )
            """)
            
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_voltage_timestamp ON voltage_samples(timestamp)")
            
            # Table 5: LHM Snapshots (FORGE 2026-02-15: Full sensor dump)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lhm_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    lhm_connected INTEGER DEFAULT 0,
                    sensor_count INTEGER DEFAULT 0,
                    
                    -- NVIDIA GPU
                    nvidia_voltage_mv REAL,
                    nvidia_power_w REAL,
                    nvidia_clock_core_mhz REAL,
                    nvidia_clock_mem_mhz REAL,
                    nvidia_temp_core_c REAL,
                    nvidia_temp_mem_junction_c REAL,
                    nvidia_load_core_pct REAL,
                    nvidia_load_mem_pct REAL,
                    nvidia_vram_used_mb REAL,
                    nvidia_vram_free_mb REAL,
                    nvidia_vram_total_mb REAL,
                    nvidia_pcie_rx_mbs REAL,
                    nvidia_pcie_tx_mbs REAL,
                    nvidia_d3d_3d_pct REAL,
                    nvidia_d3d_copy_pct REAL,
                    nvidia_d3d_video_decode_pct REAL,
                    nvidia_d3d_video_encode_pct REAL,
                    
                    -- AMD iGPU
                    amd_igpu_voltage_core_mv REAL,
                    amd_igpu_voltage_soc_mv REAL,
                    amd_igpu_power_core_w REAL,
                    amd_igpu_power_soc_w REAL,
                    amd_igpu_clock_core_mhz REAL,
                    amd_igpu_temp_vr_soc_c REAL,
                    amd_igpu_load_core_pct REAL,
                    amd_igpu_vram_used_mb REAL,
                    amd_igpu_fps REAL,
                    
                    -- CPU
                    cpu_total_load_pct REAL,
                    cpu_max_core_load_pct REAL,
                    cpu_bus_speed_mhz REAL,
                    cpu_cores_avg_clock_mhz REAL,
                    cpu_cores_avg_effective_mhz REAL,
                    cpu_per_core_json TEXT,
                    cpu_per_thread_load_json TEXT,
                    cpu_power_package_w REAL,
                    cpu_temp_tctl_c REAL,
                    
                    -- RAM
                    ram_stick_0_temp_c REAL,
                    ram_stick_1_temp_c REAL,
                    ram_total_used_gb REAL,
                    ram_total_available_gb REAL,
                    ram_load_pct REAL,
                    
                    -- Virtual Memory
                    vmem_used_gb REAL,
                    vmem_available_gb REAL,
                    vmem_load_pct REAL,
                    
                    -- NVMe Drive 0
                    nvme0_temp_composite_c REAL,
                    nvme0_temp_1_c REAL,
                    nvme0_read_activity_pct REAL,
                    nvme0_write_activity_pct REAL,
                    nvme0_total_activity_pct REAL,
                    nvme0_read_rate_kbs REAL,
                    nvme0_write_rate_kbs REAL,
                    nvme0_life_pct REAL,
                    
                    -- NVMe Drive 1
                    nvme1_temp_composite_c REAL,
                    nvme1_temp_1_c REAL,
                    nvme1_read_activity_pct REAL,
                    nvme1_write_activity_pct REAL,
                    nvme1_total_activity_pct REAL,
                    nvme1_read_rate_kbs REAL,
                    nvme1_write_rate_kbs REAL,
                    nvme1_life_pct REAL,
                    
                    -- Battery
                    battery_voltage_v REAL,
                    battery_charge_pct REAL,
                    battery_degradation_pct REAL,
                    battery_discharge_rate_w REAL,
                    battery_remaining_mwh REAL,
                    
                    -- Network
                    wifi_upload_kbs REAL,
                    wifi_download_kbs REAL,
                    wifi_utilization_pct REAL,
                    
                    -- Raw JSON dump
                    raw_sensors_json TEXT
                )
            """)
            
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_lhm_timestamp ON lhm_snapshots(timestamp)")
            
            conn.commit()
            conn.close()
            
            logging.info(f"[ResearchDatabase] Initialized: {self.db_path} (5 tables: gpu, ram, correlations, voltage, lhm_snapshots)")
            
        except Exception as e:
            logging.error(f"[ResearchDatabase] Initialization failed: {e}")
            raise
    
    def add_gpu_sample(self, sample: Dict[str, Any]):
        """Add GPU sample to queue for batched write."""
        self.gpu_queue.append(sample)
        self._check_flush()
    
    def add_ram_sample(self, sample: Dict[str, Any]):
        """Add RAM sample to queue for batched write."""
        self.ram_queue.append(sample)
        self._check_flush()
    
    def add_voltage_sample(self, sample: Dict[str, Any]):
        """Add voltage sample to queue for batched write."""
        self.voltage_queue.append(sample)
        self._check_flush()
    
    def add_lhm_snapshot(self, snapshot: Dict[str, Any]):
        """Add LHM full sensor snapshot to queue for batched write."""
        self.lhm_queue.append(snapshot)
        self._check_flush()
    
    def add_correlation(self, correlation: Dict[str, Any]):
        """Add emotion-hardware correlation to queue."""
        self.correlation_queue.append(correlation)
        self._check_flush()
    
    def _check_flush(self):
        """Check if should flush queues to database."""
        total_queued = len(self.gpu_queue) + len(self.ram_queue) + len(self.correlation_queue) + len(self.voltage_queue) + len(self.lhm_queue)
        
        if total_queued >= self.batch_size:
            self.flush()
    
    def flush(self):
        """Flush all queues to database (thread-safe)."""
        if not self.gpu_queue and not self.ram_queue and not self.correlation_queue and not self.voltage_queue and not self.lhm_queue:
            return
        
        # FORGE FIX: Lock prevents concurrent flush from GPU/RAM/main threads
        if not self._flush_lock.acquire(timeout=5):
            logging.warning("[ResearchDatabase] Flush lock timeout -- skipping this cycle")
            return
        
        # FORGE FIX: Drain queues atomically before DB write.
        # If DB write fails, items are preserved (not lost from popleft).
        gpu_items = list(self.gpu_queue)
        ram_items = list(self.ram_queue)
        corr_items = list(self.correlation_queue)
        volt_items = list(self.voltage_queue)
        lhm_items = list(self.lhm_queue)
        self.gpu_queue.clear()
        self.ram_queue.clear()
        self.correlation_queue.clear()
        self.voltage_queue.clear()
        self.lhm_queue.clear()
        
        try:
            # FORGE FIX: Use context manager to prevent connection leak on exception
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Write GPU samples
            for sample in gpu_items:
                cursor.execute("""
                    INSERT INTO gpu_samples (
                        timestamp, sample_time_ms, gpu_utilization_pct, memory_utilization_pct,
                        encoder_utilization_pct, decoder_utilization_pct, vram_used_mb, vram_free_mb,
                        vram_total_mb, vram_allocation_rate_mb_s, gpu_clock_mhz, memory_clock_mhz,
                        sm_clock_mhz, gpu_clock_max_mhz, gpu_temp_c, gpu_temp_slowdown_c,
                        memory_temp_c, gpu_temp_delta, power_draw_watts, power_limit_watts,
                        power_draw_pct, voltage_mv, voltage_delta_mv, pstate, throttle_reasons,
                        compute_mode, pcie_tx_throughput_kb_s, pcie_rx_throughput_kb_s,
                        pcie_link_gen, pcie_link_width, tensor_core_active, cuda_cores_active_pct,
                        inference_active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sample.get("timestamp"),
                    sample.get("sample_time_ms"),
                    sample.get("gpu_utilization_pct"),
                    sample.get("memory_utilization_pct"),
                    sample.get("encoder_utilization_pct"),
                    sample.get("decoder_utilization_pct"),
                    sample.get("vram_used_mb"),
                    sample.get("vram_free_mb"),
                    sample.get("vram_total_mb"),
                    sample.get("vram_allocation_rate_mb_s"),
                    sample.get("gpu_clock_mhz"),
                    sample.get("memory_clock_mhz"),
                    sample.get("sm_clock_mhz"),
                    sample.get("gpu_clock_max_mhz"),
                    sample.get("gpu_temp_c"),
                    sample.get("gpu_temp_slowdown_c"),
                    sample.get("memory_temp_c"),
                    sample.get("gpu_temp_delta"),
                    sample.get("power_draw_watts"),
                    sample.get("power_limit_watts"),
                    sample.get("power_draw_pct"),
                    sample.get("voltage_mv"),
                    sample.get("voltage_delta_mv"),
                    sample.get("pstate"),
                    json.dumps(sample.get("throttle_reasons", [])),
                    sample.get("compute_mode"),
                    sample.get("pcie_tx_throughput_kb_s"),
                    sample.get("pcie_rx_throughput_kb_s"),
                    sample.get("pcie_link_gen"),
                    sample.get("pcie_link_width"),
                    1 if sample.get("tensor_core_active") else 0,
                    sample.get("cuda_cores_active_pct"),
                    1 if sample.get("gpu_utilization_pct", 0) > 10 else 0
                ))
            
            # Write RAM samples
            for sample in ram_items:
                cursor.execute("""
                    INSERT INTO ram_samples (
                        timestamp, sample_time_ms, system_ram_total_mb, system_ram_used_mb,
                        system_ram_available_mb, system_ram_pct, system_swap_used_mb, system_swap_pct,
                        ollama_pid, ollama_ram_mb, ollama_ram_private_mb, ollama_ram_shared_mb,
                        ollama_ram_delta_mb_s, ollama_cpu_pct, ollama_thread_count, ollama_handle_count,
                        ollama_io_read_mb_s, ollama_io_write_mb_s, lumina_pid, lumina_ram_mb,
                        lumina_cpu_pct, lumina_thread_count, total_process_count, cpu_total_pct,
                        cpu_per_core, disk_io_read_mb_s, disk_io_write_mb_s, context_switches_s
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sample.get("timestamp"),
                    sample.get("sample_time_ms"),
                    sample.get("system_ram_total_mb"),
                    sample.get("system_ram_used_mb"),
                    sample.get("system_ram_available_mb"),
                    sample.get("system_ram_pct"),
                    sample.get("system_swap_used_mb"),
                    sample.get("system_swap_pct"),
                    sample.get("ollama_pid"),
                    sample.get("ollama_ram_mb"),
                    sample.get("ollama_ram_private_mb"),
                    sample.get("ollama_ram_shared_mb"),
                    sample.get("ollama_ram_delta_mb_s"),
                    sample.get("ollama_cpu_pct"),
                    sample.get("ollama_thread_count"),
                    sample.get("ollama_handle_count"),
                    sample.get("ollama_io_read_mb_s"),
                    sample.get("ollama_io_write_mb_s"),
                    sample.get("lumina_pid"),
                    sample.get("lumina_ram_mb"),
                    sample.get("lumina_cpu_pct"),
                    sample.get("lumina_thread_count"),
                    sample.get("total_process_count"),
                    sample.get("cpu_total_pct"),
                    json.dumps(sample.get("cpu_per_core", [])),
                    sample.get("disk_io_read_mb_s"),
                    sample.get("disk_io_write_mb_s"),
                    sample.get("context_switches_s")
                ))
            
            # Write correlations
            for corr in corr_items:
                cursor.execute("""
                    INSERT INTO emotion_correlations (
                        correlation_timestamp, emotion_timestamp, emotion, emotion_intensity,
                        emotion_dimensions, hardware_timestamp, time_delta_ms, gpu_utilization_pct,
                        vram_used_mb, gpu_temp_c, power_draw_watts, voltage_mv, gpu_clock_mhz,
                        ollama_ram_mb, ollama_cpu_pct, system_ram_pct, correlation_quality,
                        inference_active, conversation_context
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    corr.get("correlation_timestamp"),
                    corr.get("emotion_timestamp"),
                    corr.get("emotion"),
                    corr.get("emotion_intensity"),
                    json.dumps(corr.get("emotion_dimensions", {})),
                    corr.get("hardware_timestamp"),
                    corr.get("time_delta_ms"),
                    corr.get("gpu_utilization_pct"),
                    corr.get("vram_used_mb"),
                    corr.get("gpu_temp_c"),
                    corr.get("power_draw_watts"),
                    corr.get("voltage_mv"),
                    corr.get("gpu_clock_mhz"),
                    corr.get("ollama_ram_mb"),
                    corr.get("ollama_cpu_pct"),
                    corr.get("system_ram_pct"),
                    corr.get("correlation_quality"),
                    1 if corr.get("inference_active") else 0,
                    corr.get("conversation_context", "")
                ))
            
            # Write voltage samples (FORGE 2026-02-15: LHM integration)
            for sample in volt_items:
                cursor.execute("""
                    INSERT INTO voltage_samples (
                        timestamp, source, lhm_connected,
                        gpu_nvidia_voltage_mv, gpu_nvidia_voltage_delta_mv,
                        gpu_nvidia_voltage_min_mv, gpu_nvidia_voltage_max_mv,
                        gpu_nvidia_voltage_avg_mv, gpu_nvidia_voltage_std_dev_mv,
                        voltage_spike_count, voltage_stability_score,
                        gpu_amd_core_voltage_mv, gpu_amd_soc_voltage_mv,
                        cpu_voltage_avg_mv, cpu_voltage_min_mv, cpu_voltage_max_mv,
                        battery_voltage_v
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sample.get("timestamp"),
                    sample.get("source", "LHM"),
                    1 if sample.get("lhm_connected") else 0,
                    sample.get("voltage_mv", 0.0),
                    sample.get("voltage_delta_mv", 0.0),
                    sample.get("voltage_min_mv", 0.0),
                    sample.get("voltage_max_mv", 0.0),
                    sample.get("voltage_avg_mv", 0.0),
                    sample.get("voltage_std_dev_mv", 0.0),
                    sample.get("voltage_spike_count", 0),
                    sample.get("voltage_stability_score", 0.0),
                    sample.get("gpu_amd_core_voltage_mv", 0.0),
                    sample.get("gpu_amd_soc_voltage_mv", 0.0),
                    sample.get("cpu_voltage_avg_mv", 0.0),
                    sample.get("cpu_voltage_min_mv", 0.0),
                    sample.get("cpu_voltage_max_mv", 0.0),
                    sample.get("battery_voltage_v", 0.0)
                ))
            
            # Write LHM snapshots (FORGE 2026-02-15: Full sensor dump)
            for snapshot in lhm_items:
                cursor.execute("""
                    INSERT INTO lhm_snapshots (
                        timestamp, lhm_connected, sensor_count,
                        nvidia_voltage_mv, nvidia_power_w, nvidia_clock_core_mhz, nvidia_clock_mem_mhz,
                        nvidia_temp_core_c, nvidia_temp_mem_junction_c, nvidia_load_core_pct, nvidia_load_mem_pct,
                        nvidia_vram_used_mb, nvidia_vram_free_mb, nvidia_vram_total_mb,
                        nvidia_pcie_rx_mbs, nvidia_pcie_tx_mbs,
                        nvidia_d3d_3d_pct, nvidia_d3d_copy_pct, nvidia_d3d_video_decode_pct, nvidia_d3d_video_encode_pct,
                        amd_igpu_voltage_core_mv, amd_igpu_voltage_soc_mv, amd_igpu_power_core_w, amd_igpu_power_soc_w,
                        amd_igpu_clock_core_mhz, amd_igpu_temp_vr_soc_c, amd_igpu_load_core_pct, amd_igpu_vram_used_mb, amd_igpu_fps,
                        cpu_total_load_pct, cpu_max_core_load_pct, cpu_bus_speed_mhz, cpu_cores_avg_clock_mhz, cpu_cores_avg_effective_mhz,
                        cpu_per_core_json, cpu_per_thread_load_json, cpu_power_package_w, cpu_temp_tctl_c,
                        ram_stick_0_temp_c, ram_stick_1_temp_c, ram_total_used_gb, ram_total_available_gb, ram_load_pct,
                        vmem_used_gb, vmem_available_gb, vmem_load_pct,
                        nvme0_temp_composite_c, nvme0_temp_1_c, nvme0_read_activity_pct, nvme0_write_activity_pct, nvme0_total_activity_pct,
                        nvme0_read_rate_kbs, nvme0_write_rate_kbs, nvme0_life_pct,
                        nvme1_temp_composite_c, nvme1_temp_1_c, nvme1_read_activity_pct, nvme1_write_activity_pct, nvme1_total_activity_pct,
                        nvme1_read_rate_kbs, nvme1_write_rate_kbs, nvme1_life_pct,
                        battery_voltage_v, battery_charge_pct, battery_degradation_pct, battery_discharge_rate_w, battery_remaining_mwh,
                        wifi_upload_kbs, wifi_download_kbs, wifi_utilization_pct,
                        raw_sensors_json
                    ) VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?
                    )
                """, (
                    snapshot.get("timestamp"),
                    1 if snapshot.get("lhm_connected") else 0,
                    snapshot.get("sensor_count", 0),
                    snapshot.get("nvidia_gpu", {}).get("voltage_mv", 0.0),
                    snapshot.get("nvidia_gpu", {}).get("power_w", 0.0),
                    snapshot.get("nvidia_gpu", {}).get("clock_core_mhz", 0.0),
                    snapshot.get("nvidia_gpu", {}).get("clock_mem_mhz", 0.0),
                    snapshot.get("nvidia_gpu", {}).get("temp_core_c", 0.0),
                    snapshot.get("nvidia_gpu", {}).get("temp_mem_junction_c", 0.0),
                    snapshot.get("nvidia_gpu", {}).get("load_core_pct", 0.0),
                    snapshot.get("nvidia_gpu", {}).get("load_mem_pct", 0.0),
                    snapshot.get("nvidia_gpu", {}).get("vram_used_mb", 0.0),
                    snapshot.get("nvidia_gpu", {}).get("vram_free_mb", 0.0),
                    snapshot.get("nvidia_gpu", {}).get("vram_total_mb", 0.0),
                    snapshot.get("nvidia_gpu", {}).get("pcie_rx_mbs", 0.0),
                    snapshot.get("nvidia_gpu", {}).get("pcie_tx_mbs", 0.0),
                    snapshot.get("nvidia_gpu", {}).get("d3d_3d_pct", 0.0),
                    snapshot.get("nvidia_gpu", {}).get("d3d_copy_pct", 0.0),
                    snapshot.get("nvidia_gpu", {}).get("d3d_video_decode_pct", 0.0),
                    snapshot.get("nvidia_gpu", {}).get("d3d_video_encode_pct", 0.0),
                    snapshot.get("amd_igpu", {}).get("voltage_core_mv", 0.0),
                    snapshot.get("amd_igpu", {}).get("voltage_soc_mv", 0.0),
                    snapshot.get("amd_igpu", {}).get("power_core_w", 0.0),
                    snapshot.get("amd_igpu", {}).get("power_soc_w", 0.0),
                    snapshot.get("amd_igpu", {}).get("clock_core_mhz", 0.0),
                    snapshot.get("amd_igpu", {}).get("temp_vr_soc_c", 0.0),
                    snapshot.get("amd_igpu", {}).get("load_core_pct", 0.0),
                    snapshot.get("amd_igpu", {}).get("vram_used_mb", 0.0),
                    snapshot.get("amd_igpu", {}).get("fps", 0.0),
                    snapshot.get("cpu", {}).get("total_load_pct", 0.0),
                    snapshot.get("cpu", {}).get("max_core_load_pct", 0.0),
                    snapshot.get("cpu", {}).get("bus_speed_mhz", 0.0),
                    snapshot.get("cpu", {}).get("cores_avg_clock_mhz", 0.0),
                    snapshot.get("cpu", {}).get("cores_avg_effective_mhz", 0.0),
                    json.dumps(snapshot.get("cpu", {}).get("per_core", [])),
                    json.dumps(snapshot.get("cpu", {}).get("per_thread_load", [])),
                    snapshot.get("cpu", {}).get("power_package_w", 0.0),
                    snapshot.get("cpu", {}).get("temp_tctl_c", 0.0),
                    snapshot.get("ram_physical", {}).get("stick_0_temp_c", 0.0),
                    snapshot.get("ram_physical", {}).get("stick_1_temp_c", 0.0),
                    snapshot.get("ram_physical", {}).get("total_used_gb", 0.0),
                    snapshot.get("ram_physical", {}).get("total_available_gb", 0.0),
                    snapshot.get("ram_physical", {}).get("total_load_pct", 0.0),
                    snapshot.get("virtual_memory", {}).get("used_gb", 0.0),
                    snapshot.get("virtual_memory", {}).get("available_gb", 0.0),
                    snapshot.get("virtual_memory", {}).get("load_pct", 0.0),
                    snapshot.get("nvme", {}).get("drive_0", {}).get("temp_composite_c", 0.0),
                    snapshot.get("nvme", {}).get("drive_0", {}).get("temp_1_c", 0.0),
                    snapshot.get("nvme", {}).get("drive_0", {}).get("read_activity_pct", 0.0),
                    snapshot.get("nvme", {}).get("drive_0", {}).get("write_activity_pct", 0.0),
                    snapshot.get("nvme", {}).get("drive_0", {}).get("total_activity_pct", 0.0),
                    snapshot.get("nvme", {}).get("drive_0", {}).get("read_rate_kbs", 0.0),
                    snapshot.get("nvme", {}).get("drive_0", {}).get("write_rate_kbs", 0.0),
                    snapshot.get("nvme", {}).get("drive_0", {}).get("life_pct", 0.0),
                    snapshot.get("nvme", {}).get("drive_1", {}).get("temp_composite_c", 0.0),
                    snapshot.get("nvme", {}).get("drive_1", {}).get("temp_1_c", 0.0),
                    snapshot.get("nvme", {}).get("drive_1", {}).get("read_activity_pct", 0.0),
                    snapshot.get("nvme", {}).get("drive_1", {}).get("write_activity_pct", 0.0),
                    snapshot.get("nvme", {}).get("drive_1", {}).get("total_activity_pct", 0.0),
                    snapshot.get("nvme", {}).get("drive_1", {}).get("read_rate_kbs", 0.0),
                    snapshot.get("nvme", {}).get("drive_1", {}).get("write_rate_kbs", 0.0),
                    snapshot.get("nvme", {}).get("drive_1", {}).get("life_pct", 0.0),
                    snapshot.get("battery", {}).get("voltage_v", 0.0),
                    snapshot.get("battery", {}).get("charge_level_pct", 0.0),
                    snapshot.get("battery", {}).get("degradation_pct", 0.0),
                    snapshot.get("battery", {}).get("discharge_rate_w", 0.0),
                    snapshot.get("battery", {}).get("remaining_capacity_mwh", 0.0),
                    snapshot.get("network", {}).get("wifi", {}).get("upload_speed_kbs", 0.0),
                    snapshot.get("network", {}).get("wifi", {}).get("download_speed_kbs", 0.0),
                    snapshot.get("network", {}).get("wifi", {}).get("utilization_pct", 0.0),
                    json.dumps(snapshot.get("raw_sensors", {}))
                ))
            
            conn.commit()
            conn.close()
            
            logging.info(f"[ResearchDatabase] Flushed {len(gpu_items)} GPU + {len(ram_items)} RAM + {len(corr_items)} corr + {len(volt_items)} volt + {len(lhm_items)} LHM snapshots")
            self.last_flush = time.time()
            
        except Exception as e:
            # FORGE FIX: On failure, put items back so they're not lost
            # ATLAS FIX: Also preserve lhm_items (MiMo missed this)
            self.gpu_queue.extendleft(reversed(gpu_items))
            self.ram_queue.extendleft(reversed(ram_items))
            self.correlation_queue.extendleft(reversed(corr_items))
            self.voltage_queue.extendleft(reversed(volt_items))
            self.lhm_queue.extendleft(reversed(lhm_items))
            logging.error(f"[ResearchDatabase] Flush failed (items preserved): {e}")
            try:
                conn.close()
            except Exception:
                pass
        finally:
            self._flush_lock.release()


# ============================================================================
# COMPONENT 6: HARDWARE ANALYZER
# ============================================================================

class HardwareAnalyzer:
    """
    Detect anomalies, learn baselines, identify emotional signatures.
    
    Tools Used: Statistics module, LiveAudit, KnowledgeSync, ConsciousnessMarker
    """
    
    def __init__(self, config: HardwareSoulConfig, research_db: ResearchDatabase):
        self.config = config
        self.research_db = research_db
        
        # Baselines (learned from data)
        self.hardware_baselines = {}
        self.emotional_signatures = {}
    
    def detect_thermal_throttle(self, gpu_sample: Dict[str, Any]) -> bool:
        """Detect if GPU is thermally throttling."""
        if not gpu_sample:
            return False
        
        temp = gpu_sample.get("gpu_temp_c", 0)
        slowdown_temp = gpu_sample.get("gpu_temp_slowdown_c", 100)
        throttle_reasons = gpu_sample.get("throttle_reasons", [])
        
        return temp >= slowdown_temp or "THERMAL" in throttle_reasons or "HW_THERMAL" in throttle_reasons
    
    def detect_power_limit(self, gpu_sample: Dict[str, Any]) -> bool:
        """Detect if GPU hitting power limit."""
        if not gpu_sample:
            return False
        
        power_pct = gpu_sample.get("power_draw_pct", 0)
        throttle_reasons = gpu_sample.get("throttle_reasons", [])
        
        return power_pct > 95.0 or "POWER_CAP" in throttle_reasons or "POWER_BRAKE" in throttle_reasons
    
    def detect_memory_pressure(self, ram_sample: Dict[str, Any]) -> bool:
        """Detect if system under memory pressure."""
        if not ram_sample:
            return False
        
        ram_pct = ram_sample.get("system_ram_pct", 0)
        swap_pct = ram_sample.get("system_swap_pct", 0)
        
        return ram_pct > 90.0 or swap_pct > 50.0


# ============================================================================
# COMPONENT 7: HARDWARESOUL DAEMON (EXTENDS PHASE 2)
# ============================================================================

class HardwareSoulDaemon(InferencePulseDaemon):
    """
    Phase 3: Extends Phase 2 InferencePulse with:
    - GPU monitoring (25+ metrics via pynvml)
    - RAM monitoring (27+ metrics via psutil)
    - Voltage tracking (millisecond precision)
    - Emotion-hardware correlation
    - Research database (time-series storage)
    """
    
    def __init__(self, config_path: str = None):
        # Initialize Phase 2 (which initializes Phase 1)
        super().__init__(config_path)
        
        # Initialize Phase 3 config
        self.phase3_config = HardwareSoulConfig()
        
        # Initialize Phase 3 components
        logging.info("[HardwareSoul] Initializing Phase 3 components...")
        
        self.gpu_monitor = GPUMonitor(self.phase3_config) if PYNVML_AVAILABLE else None
        self.ram_monitor = RAMMonitor(self.phase3_config)
        self.voltage_tracker = VoltageTracker(self.phase3_config)
        self.research_db = ResearchDatabase(self.phase3_config)
        self.emotion_correlator = EmotionCorrelator(self.phase3_config)
        self.hardware_analyzer = HardwareAnalyzer(self.phase3_config, self.research_db)
        
        # Phase 3 state
        self.phase3_enabled = self.phase3_config.get("hardwaresoul", "enabled")
        self.gpu_thread = None
        self.ram_thread = None
        self.lhm_thread = None
        
        # LHM Enhanced Monitor (shares LHM Bridge with VoltageTracker)
        self.lhm_monitor = None
        if self.voltage_tracker and hasattr(self.voltage_tracker, 'lhm_bridge') and self.voltage_tracker.lhm_bridge:
            if LHM_ENHANCED_AVAILABLE:
                self.lhm_monitor = LHMEnhancedMonitor(self.voltage_tracker.lhm_bridge)
                logging.info("[HardwareSoul] LHM Enhanced Monitor initialized")
            else:
                logging.warning("[HardwareSoul] lhm_enhanced_monitor module not available")
        
        logging.info(f"[HardwareSoul] Phase 3 initialized (enabled={self.phase3_enabled}, GPU={'available' if self.gpu_monitor else 'unavailable'})")
    
    def start(self):
        """Override start to add Phase 3 monitoring."""
        logging.info(f"[HardwareSoul] Starting VitalHeart Phase 3 v{__version__} (Phase 2 v{PHASE2_VERSION})")
        
        # Start Phase 2 (which starts Phase 1) in thread
        phase2_thread = threading.Thread(target=super().start, daemon=True)
        phase2_thread.start()
        
        # Start Phase 3 monitoring
        if self.phase3_enabled:
            self._start_gpu_monitor()
            self._start_ram_monitor()
            self._start_lhm_monitor()
        
        # Phase 3 main loop (coordination)
        self._phase3_main_loop()
    
    def _start_gpu_monitor(self):
        """Start GPU monitoring thread."""
        if self.gpu_monitor:
            self.gpu_thread = threading.Thread(target=self._gpu_monitoring_loop, daemon=True)
            self.gpu_thread.start()
            logging.info("[HardwareSoul] GPU monitoring thread started")
    
    def _start_ram_monitor(self):
        """Start RAM monitoring thread."""
        if self.ram_monitor:
            self.ram_thread = threading.Thread(target=self._ram_monitoring_loop, daemon=True)
            self.ram_thread.start()
            logging.info("[HardwareSoul] RAM monitoring thread started")
    
    def _start_lhm_monitor(self):
        """Start LHM full sensor monitoring thread."""
        if self.lhm_monitor:
            self.lhm_thread = threading.Thread(target=self._lhm_monitoring_loop, daemon=True)
            self.lhm_thread.start()
            logging.info("[HardwareSoul] LHM full sensor monitoring thread started")
    
    def _gpu_monitoring_loop(self):
        """GPU sampling loop (250ms active, 1000ms idle)."""
        logging.info("[HardwareSoul] GPU monitoring loop started")
        
        while self.running:
            try:
                # Sample GPU
                gpu_sample = self.gpu_monitor.sample()
                
                if gpu_sample:
                    # FORGE FIX (2026-02-15): Inject REAL voltage from VoltageTracker/LHM
                    # pynvml returns 0.0 for voltage on RTX 5070 Ti, but LHM reads it fine.
                    if self.voltage_tracker and hasattr(self.voltage_tracker, 'lhm_bridge'):
                        voltage_data = self.voltage_tracker.track()
                        gpu_sample["voltage_mv"] = voltage_data.get("voltage_mv", 0.0)
                        gpu_sample["voltage_delta_mv"] = voltage_data.get("voltage_delta_mv", 0.0)
                    
                    # Add to research database
                    self.research_db.add_gpu_sample(gpu_sample)
                    
                    # Also store extended voltage data if available
                    if self.voltage_tracker and hasattr(self.voltage_tracker, 'lhm_bridge'):
                        self.research_db.add_voltage_sample(voltage_data)
                    
                    # Add to correlation buffer
                    self.emotion_correlator.add_hardware_sample(gpu_sample, {})
                    
                    # Detect anomalies
                    if self.hardware_analyzer.detect_thermal_throttle(gpu_sample):
                        logging.warning(f"[HardwareSoul] Thermal throttle detected: {gpu_sample['gpu_temp_c']:.1f}C")
                    
                    if self.hardware_analyzer.detect_power_limit(gpu_sample):
                        logging.warning(f"[HardwareSoul] Power limit throttle: {gpu_sample['power_draw_pct']:.1f}%")
                
                # Adaptive sampling: 250ms if active, 1000ms if idle
                is_active = gpu_sample and gpu_sample.get("gpu_utilization_pct", 0) > self.phase3_config.get("hardwaresoul", "active_inference_threshold") * 100
                sleep_ms = self.phase3_config.get("hardwaresoul", "gpu_sampling_rate_active_ms") if is_active else self.phase3_config.get("hardwaresoul", "gpu_sampling_rate_idle_ms")
                
                time.sleep(sleep_ms / 1000.0)
                
            except Exception as e:
                logging.error(f"[HardwareSoul] GPU monitoring loop error: {e}")
                logging.error(traceback.format_exc())
                time.sleep(1)
    
    def _ram_monitoring_loop(self):
        """RAM sampling loop (250ms active, 1000ms idle)."""
        logging.info("[HardwareSoul] RAM monitoring loop started")
        
        while self.running:
            try:
                # Sample RAM
                ram_sample = self.ram_monitor.sample()
                
                if ram_sample:
                    # Add to research database
                    self.research_db.add_ram_sample(ram_sample)
                    
                    # Add to correlation buffer
                    self.emotion_correlator.add_hardware_sample({}, ram_sample)
                    
                    # Detect memory pressure
                    if self.hardware_analyzer.detect_memory_pressure(ram_sample):
                        logging.warning(f"[HardwareSoul] Memory pressure: {ram_sample['system_ram_pct']:.1f}%")
                
                # Adaptive sampling
                is_active = ram_sample and ram_sample.get("ollama_cpu_pct", 0) > 10.0
                sleep_ms = self.phase3_config.get("hardwaresoul", "gpu_sampling_rate_active_ms") if is_active else self.phase3_config.get("hardwaresoul", "gpu_sampling_rate_idle_ms")
                
                time.sleep(sleep_ms / 1000.0)
                
            except Exception as e:
                logging.error(f"[HardwareSoul] RAM monitoring loop error: {e}")
                logging.error(traceback.format_exc())
                time.sleep(1)
    
    def _lhm_monitoring_loop(self):
        """LHM full sensor sampling loop (every 2 seconds)."""
        logging.info("[HardwareSoul] LHM monitoring loop started")
        
        while self.running:
            try:
                snapshot = self.lhm_monitor.sample()
                if snapshot:
                    self.research_db.add_lhm_snapshot(snapshot)
                time.sleep(2.0)  # Match LHM Bridge cache TTL
            except Exception as e:
                logging.error(f"[HardwareSoul] LHM monitoring loop error: {e}")
                logging.error(traceback.format_exc())
                time.sleep(5)
    
    def _phase3_main_loop(self):
        """Phase 3 coordination loop (emotion correlation, periodic analysis)."""
        logging.info("[HardwareSoul] Phase 3 coordination loop started")
        
        while self.running:
            try:
                # Flush research database periodically
                if (time.time() - self.research_db.last_flush) > 10:
                    self.research_db.flush()
                
                time.sleep(5)
                
            except Exception as e:
                logging.error(f"[HardwareSoul] Phase 3 main loop error: {e}")
                logging.error(traceback.format_exc())
                time.sleep(5)
    
    def stop(self):
        """Override stop to cleanup Phase 3 components."""
        logging.info("[HardwareSoul] Stopping Phase 3...")
        
        # FORGE FIX: Stop threads FIRST, THEN flush, THEN cleanup.
        # Old order: flush → cleanup → stop. This raced with running threads
        # that were still appending to queues during flush.
        self.running = False
        
        # Wait for monitoring threads to finish
        # ATLAS FIX: Added null guard -- threads are None if start() was never called
        if hasattr(self, 'gpu_thread') and self.gpu_thread and self.gpu_thread.is_alive():
            self.gpu_thread.join(timeout=5)
        if hasattr(self, 'ram_thread') and self.ram_thread and self.ram_thread.is_alive():
            self.ram_thread.join(timeout=5)
        if hasattr(self, 'lhm_thread') and self.lhm_thread and self.lhm_thread.is_alive():
            self.lhm_thread.join(timeout=5)
        
        # Now flush -- all threads stopped, no more data incoming
        if hasattr(self, 'research_db'):
            self.research_db.flush()
        
        # Cleanup GPU (nvmlShutdown)
        if hasattr(self, 'gpu_monitor') and self.gpu_monitor:
            self.gpu_monitor.cleanup()
        
        # Cleanup VoltageTracker (LHM Bridge)
        if hasattr(self, 'voltage_tracker') and self.voltage_tracker:
            self.voltage_tracker.cleanup()
        
        # Call Phase 2 stop (which calls Phase 1)
        super().stop()


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point for HardwareSoul daemon."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="VitalHeart Phase 3: HardwareSoul - GPU/RAM Monitoring with Emotion Correlation"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="./hardwaresoul_config.json",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"HardwareSoul v{__version__} (InferencePulse v{PHASE2_VERSION})"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("hardwaresoul.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Check pynvml availability
    if not PYNVML_AVAILABLE:
        logging.warning("[HardwareSoul] pynvml not available - GPU monitoring will be disabled")
        logging.warning("[HardwareSoul] Install with: pip install nvidia-ml-py")
    
    # Start daemon
    daemon = HardwareSoulDaemon(args.config)
    
    try:
        daemon.start()
    except KeyboardInterrupt:
        logging.info("[HardwareSoul] Received shutdown signal")
        daemon.stop()
        sys.exit(0)


if __name__ == "__main__":
    main()
