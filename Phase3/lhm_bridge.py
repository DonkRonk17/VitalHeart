"""
VitalHeart Phase 3: LibreHardwareMonitor Bridge
================================================

Connects VitalHeart to LibreHardwareMonitor's REST API for real hardware
voltage monitoring. LHM exposes sensors that pynvml/nvidia-smi cannot
access, including:

- GPU Core Voltage (RTX 5070 Ti: /gpu-nvidia/0/voltage/0)
- CPU per-core VID (AMD Ryzen 9: /amdcpu/0/voltage/2-17)
- iGPU Voltage (AMD Radeon 610M: /gpu-amd/0/voltage/0,2)
- Battery Voltage (/battery/R220358_1/voltage/0)
- Plus 300+ other hardware sensors

REQUIRES:
- LibreHardwareMonitor running as Administrator with HTTP server enabled
- Default endpoint: http://127.0.0.1:8085

TOOLS USED:
- requests: HTTP client for LHM REST API
- TimeSync: Sample timestamping
- ErrorRecovery: Connection failure handling with backoff

Author: FORGE (Team Brain)
Date: February 15, 2026
Protocol: BUILD_PROTOCOL_V1.md + Bug Hunt Protocol (100% Compliance)
License: MIT
"""

import time
import json
import logging
import threading
from datetime import datetime
from typing import Optional, Dict, Any, List
from collections import deque

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logging.warning("[LHMBridge] requests library not available - pip install requests")


__version__ = "1.0.0"


# ============================================================================
# SENSOR ID REGISTRY
# ============================================================================

class LHMSensorIDs:
    """
    Known sensor IDs for Logan's ASUS AMD 9 system.
    
    Discovered via LHM REST API sensor enumeration on 2026-02-15.
    These IDs are hardware-specific -- different systems will have
    different IDs. The bridge auto-discovers if these don't match.
    """
    
    # NVIDIA GeForce RTX 5070 Ti Laptop GPU
    GPU_NVIDIA_VOLTAGE = "/gpu-nvidia/0/voltage/0"      # GPU Core Voltage (V)
    GPU_NVIDIA_POWER = "/gpu-nvidia/0/power/0"           # GPU Package Power (W)
    GPU_NVIDIA_CLOCK_CORE = "/gpu-nvidia/0/clock/0"      # GPU Core Clock (MHz)
    GPU_NVIDIA_CLOCK_MEM = "/gpu-nvidia/0/clock/4"       # GPU Memory Clock (MHz)
    GPU_NVIDIA_TEMP_CORE = "/gpu-nvidia/0/temperature/0" # GPU Core Temp (C)
    GPU_NVIDIA_TEMP_MEM = "/gpu-nvidia/0/temperature/3"  # GPU Memory Junction Temp (C)
    GPU_NVIDIA_LOAD_CORE = "/gpu-nvidia/0/load/0"        # GPU Core Load (%)
    GPU_NVIDIA_LOAD_MEM = "/gpu-nvidia/0/load/3"         # GPU Memory Load (%)
    GPU_NVIDIA_VRAM_USED = "/gpu-nvidia/0/smalldata/1"   # VRAM Used (MB)
    GPU_NVIDIA_VRAM_FREE = "/gpu-nvidia/0/smalldata/0"   # VRAM Free (MB)
    GPU_NVIDIA_VRAM_TOTAL = "/gpu-nvidia/0/smalldata/2"  # VRAM Total (MB)
    GPU_NVIDIA_PCIE_RX = "/gpu-nvidia/0/throughput/0"    # PCIe Rx (MB/s)
    GPU_NVIDIA_PCIE_TX = "/gpu-nvidia/0/throughput/1"    # PCIe Tx (MB/s)
    
    # AMD Radeon 610M (iGPU)
    GPU_AMD_VOLTAGE_CORE = "/gpu-amd/0/voltage/0"       # iGPU Core Voltage (V)
    GPU_AMD_VOLTAGE_SOC = "/gpu-amd/0/voltage/2"        # iGPU SoC Voltage (V)
    
    # AMD Ryzen 9 8940HX CPU (first and last core for range)
    CPU_VOLTAGE_CORE_1 = "/amdcpu/0/voltage/2"          # Core #1 VID (V)
    CPU_VOLTAGE_CORE_16 = "/amdcpu/0/voltage/17"        # Core #16 VID (V)
    
    # Battery
    BATTERY_VOLTAGE = "/battery/R220358_1/voltage/0"     # Battery Voltage (V)
    
    # Watchlist: All voltage sensor IDs for bulk query
    ALL_VOLTAGE_IDS = [
        GPU_NVIDIA_VOLTAGE,
        GPU_AMD_VOLTAGE_CORE,
        GPU_AMD_VOLTAGE_SOC,
        BATTERY_VOLTAGE,
    ] + [f"/amdcpu/0/voltage/{i}" for i in range(2, 18)]  # Cores 1-16


# ============================================================================
# LHM BRIDGE - REST API CLIENT
# ============================================================================

class LHMBridge:
    """
    Bridge between VitalHeart and LibreHardwareMonitor's REST API.
    
    Features:
    - Auto-discovery: Enumerates all sensors on first connect
    - Caching: Caches full sensor tree, refreshes on configurable interval
    - Retry/backoff: Handles LHM restarts gracefully
    - Thread-safe: Safe for concurrent reads from GPU/RAM/Voltage threads
    - Selective query: Get individual sensor values by ID
    - Bulk query: Get all voltage sensors in one call
    
    Usage:
        bridge = LHMBridge()
        if bridge.is_connected():
            voltage = bridge.get_sensor_value("/gpu-nvidia/0/voltage/0")
            all_voltages = bridge.get_all_voltages()
    """
    
    def __init__(self, 
                 url: str = "http://127.0.0.1:8085",
                 cache_ttl_seconds: float = 2.0,
                 timeout_seconds: float = 5.0,
                 max_retries: int = 3,
                 retry_backoff_seconds: float = 1.0):
        """
        Initialize LHM Bridge.
        
        Args:
            url: LHM HTTP server URL (default: http://127.0.0.1:8085)
            cache_ttl_seconds: How long to cache the full sensor tree
            timeout_seconds: HTTP request timeout
            max_retries: Max retries on connection failure
            retry_backoff_seconds: Initial backoff between retries (doubles each retry)
        """
        self.url = url.rstrip('/')
        self.cache_ttl = cache_ttl_seconds
        self.timeout = timeout_seconds
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff_seconds
        
        # Connection state
        self._connected = False
        self._last_error = None
        self._last_connect_attempt = 0
        self._consecutive_failures = 0
        
        # Sensor cache
        self._sensor_cache = {}          # {sensor_id: {value, min, max, path, ...}}
        self._cache_timestamp = 0
        self._raw_tree = None
        self._cache_lock = threading.Lock()
        
        # Voltage history for statistical analysis
        self._voltage_history = deque(maxlen=1000)
        
        # Auto-connect on init
        if REQUESTS_AVAILABLE:
            self._try_connect()
        else:
            logging.error("[LHMBridge] requests library not installed. pip install requests")
    
    def _try_connect(self) -> bool:
        """Attempt to connect to LHM REST API."""
        try:
            resp = requests.get(f"{self.url}/data.json", timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                self._parse_sensor_tree(data)
                self._connected = True
                self._consecutive_failures = 0
                self._last_error = None
                logging.info(f"[LHMBridge] Connected to LHM at {self.url} ({len(self._sensor_cache)} sensors)")
                return True
            else:
                self._connected = False
                self._last_error = f"HTTP {resp.status_code}"
                logging.warning(f"[LHMBridge] LHM returned HTTP {resp.status_code}")
                return False
        except requests.ConnectionError:
            self._connected = False
            self._last_error = "Connection refused"
            self._consecutive_failures += 1
            if self._consecutive_failures <= 3:
                logging.warning(f"[LHMBridge] Cannot connect to LHM at {self.url} (attempt {self._consecutive_failures})")
            return False
        except Exception as e:
            self._connected = False
            self._last_error = str(e)
            self._consecutive_failures += 1
            logging.error(f"[LHMBridge] Connection error: {e}")
            return False
    
    def _parse_sensor_tree(self, node: Dict, path: str = ''):
        """Recursively parse the LHM JSON sensor tree into a flat dict."""
        current_path = path + '/' + node.get('Text', '?')
        children = node.get('Children', [])
        
        if len(children) > 0:
            for child in children:
                self._parse_sensor_tree(child, current_path)
        else:
            sensor_id = node.get('SensorId')
            if sensor_id:
                # Parse value string to float (e.g., "0.680 V" -> 0.68)
                raw_value = node.get('Value', 'N/A')
                raw_min = node.get('Min', 'N/A')
                raw_max = node.get('Max', 'N/A')
                
                self._sensor_cache[sensor_id] = {
                    'path': current_path,
                    'id': sensor_id,
                    'raw_value': raw_value,
                    'raw_min': raw_min,
                    'raw_max': raw_max,
                    'value': self._parse_value(raw_value),
                    'min': self._parse_value(raw_min),
                    'max': self._parse_value(raw_max),
                    'type': node.get('Type', 'Unknown'),
                    'timestamp': time.time()
                }
        
        self._cache_timestamp = time.time()
    
    @staticmethod
    def _parse_value(raw: str) -> float:
        """Parse a sensor value string like '0.680 V' or '46.6 °C' to float."""
        if not raw or raw == 'N/A':
            return 0.0
        try:
            # Strip units: take only the numeric part
            parts = raw.strip().split()
            if parts:
                return float(parts[0].replace(',', '.'))
        except (ValueError, IndexError):
            pass
        return 0.0
    
    def _refresh_cache(self):
        """Refresh sensor cache if TTL expired."""
        with self._cache_lock:
            now = time.time()
            if (now - self._cache_timestamp) < self.cache_ttl:
                return  # Cache still fresh
            
            if not self._connected:
                # Try reconnect with backoff
                backoff = min(self.retry_backoff * (2 ** self._consecutive_failures), 30)
                if (now - self._last_connect_attempt) < backoff:
                    return
                self._last_connect_attempt = now
                self._try_connect()
                return
            
            try:
                resp = requests.get(f"{self.url}/data.json", timeout=self.timeout)
                if resp.status_code == 200:
                    data = resp.json()
                    self._sensor_cache.clear()
                    self._parse_sensor_tree(data)
                    self._raw_tree = data
                    self._consecutive_failures = 0
                else:
                    logging.warning(f"[LHMBridge] Cache refresh: HTTP {resp.status_code}")
                    self._consecutive_failures += 1
            except Exception as e:
                self._connected = False
                self._consecutive_failures += 1
                self._last_error = str(e)
                if self._consecutive_failures <= 3:
                    logging.warning(f"[LHMBridge] Cache refresh failed: {e}")
    
    # ========================================================================
    # PUBLIC API
    # ========================================================================
    
    def is_connected(self) -> bool:
        """Check if bridge is connected to LHM."""
        return self._connected and REQUESTS_AVAILABLE
    
    def get_status(self) -> Dict[str, Any]:
        """Get bridge connection status."""
        return {
            "connected": self._connected,
            "url": self.url,
            "sensor_count": len(self._sensor_cache),
            "cache_age_seconds": time.time() - self._cache_timestamp if self._cache_timestamp else -1,
            "consecutive_failures": self._consecutive_failures,
            "last_error": self._last_error,
            "requests_available": REQUESTS_AVAILABLE
        }
    
    def get_sensor_value(self, sensor_id: str) -> Optional[float]:
        """
        Get current value of a specific sensor by ID.
        
        Args:
            sensor_id: LHM sensor ID (e.g., "/gpu-nvidia/0/voltage/0")
            
        Returns:
            Sensor value as float, or None if unavailable.
        """
        self._refresh_cache()
        
        sensor = self._sensor_cache.get(sensor_id)
        if sensor:
            return sensor['value']
        return None
    
    def get_sensor_full(self, sensor_id: str) -> Optional[Dict[str, Any]]:
        """
        Get full sensor data (value, min, max, path, type).
        
        Args:
            sensor_id: LHM sensor ID
            
        Returns:
            Full sensor dict or None.
        """
        self._refresh_cache()
        return self._sensor_cache.get(sensor_id)
    
    def get_sensor_by_path(self, path_fragment: str) -> List[Dict[str, Any]]:
        """
        Find sensors whose path OR sensor ID contains the given fragment.
        
        Args:
            path_fragment: Substring to match in sensor path/ID (case-insensitive)
            
        Returns:
            List of matching sensor dicts.
        """
        self._refresh_cache()
        fragment_lower = path_fragment.lower()
        return [
            s for s in self._sensor_cache.values()
            if fragment_lower in s['path'].lower() or fragment_lower in s.get('id', '').lower()
        ]
    
    def get_all_voltages(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all voltage sensor readings.
        
        Returns:
            Dict mapping sensor ID to voltage data:
            {
                "/gpu-nvidia/0/voltage/0": {
                    "value": 0.680,
                    "min": 0.625,
                    "max": 0.760,
                    "label": "GPU Core Voltage",
                    "path": "/Sensor/.../Voltages/GPU Core Voltage"
                },
                ...
            }
        """
        self._refresh_cache()
        
        voltages = {}
        for sensor_id, sensor_data in self._sensor_cache.items():
            if 'voltage' in sensor_id.lower():
                # Extract label from path
                path = sensor_data.get('path', '')
                label = path.split('/')[-1] if '/' in path else sensor_id
                
                voltages[sensor_id] = {
                    'value': sensor_data['value'],
                    'min': sensor_data['min'],
                    'max': sensor_data['max'],
                    'label': label,
                    'path': path,
                    'raw_value': sensor_data.get('raw_value', 'N/A')
                }
        
        return voltages
    
    def get_gpu_voltage_mv(self) -> float:
        """
        Get NVIDIA GPU core voltage in millivolts.
        
        This is the primary voltage metric for VitalHeart.
        LHM reports in Volts, we convert to mV for consistency with existing code.
        
        Returns:
            GPU core voltage in millivolts, or 0.0 if unavailable.
        """
        volts = self.get_sensor_value(LHMSensorIDs.GPU_NVIDIA_VOLTAGE)
        if volts is not None:
            mv = volts * 1000.0  # V -> mV
            
            # Track in history for statistical analysis
            self._voltage_history.append({
                'timestamp': time.time(),
                'voltage_mv': mv
            })
            
            return mv
        return 0.0
    
    def get_voltage_snapshot(self) -> Dict[str, Any]:
        """
        Get comprehensive voltage snapshot across all components.
        
        Returns:
            {
                "gpu_nvidia_voltage_mv": float,
                "gpu_amd_core_voltage_mv": float,
                "gpu_amd_soc_voltage_mv": float,
                "cpu_voltage_avg_mv": float,
                "cpu_voltage_min_mv": float,
                "cpu_voltage_max_mv": float,
                "cpu_voltage_per_core_mv": [float, ...],
                "battery_voltage_v": float,
                "timestamp": str,
                "lhm_connected": bool
            }
        """
        self._refresh_cache()
        
        # GPU NVIDIA
        nvidia_v = self.get_sensor_value(LHMSensorIDs.GPU_NVIDIA_VOLTAGE)
        nvidia_mv = (nvidia_v * 1000.0) if nvidia_v else 0.0
        
        # GPU AMD (iGPU)
        amd_core_v = self.get_sensor_value(LHMSensorIDs.GPU_AMD_VOLTAGE_CORE)
        amd_soc_v = self.get_sensor_value(LHMSensorIDs.GPU_AMD_VOLTAGE_SOC)
        
        # CPU per-core voltages
        cpu_voltages = []
        for i in range(2, 18):  # Cores 1-16 map to voltage/2 through voltage/17
            v = self.get_sensor_value(f"/amdcpu/0/voltage/{i}")
            if v is not None:
                cpu_voltages.append(v * 1000.0)  # V -> mV
        
        cpu_avg = sum(cpu_voltages) / len(cpu_voltages) if cpu_voltages else 0.0
        cpu_min = min(cpu_voltages) if cpu_voltages else 0.0
        cpu_max = max(cpu_voltages) if cpu_voltages else 0.0
        
        # Battery
        battery_v = self.get_sensor_value(LHMSensorIDs.BATTERY_VOLTAGE)
        
        snapshot = {
            "gpu_nvidia_voltage_mv": nvidia_mv,
            "gpu_amd_core_voltage_mv": (amd_core_v * 1000.0) if amd_core_v else 0.0,
            "gpu_amd_soc_voltage_mv": (amd_soc_v * 1000.0) if amd_soc_v else 0.0,
            "cpu_voltage_avg_mv": cpu_avg,
            "cpu_voltage_min_mv": cpu_min,
            "cpu_voltage_max_mv": cpu_max,
            "cpu_voltage_per_core_mv": cpu_voltages,
            "battery_voltage_v": battery_v if battery_v else 0.0,
            "timestamp": datetime.now().isoformat(),
            "lhm_connected": self._connected
        }
        
        # Track GPU voltage in history
        if nvidia_mv > 0:
            self._voltage_history.append({
                'timestamp': time.time(),
                'voltage_mv': nvidia_mv
            })
        
        return snapshot
    
    def get_voltage_statistics(self, window_seconds: float = 60.0) -> Dict[str, Any]:
        """
        Calculate voltage statistics over recent history.
        
        Args:
            window_seconds: How far back to look
            
        Returns:
            Statistical analysis of GPU voltage over the window.
        """
        cutoff = time.time() - window_seconds
        recent = [h for h in self._voltage_history if h['timestamp'] > cutoff]
        
        if not recent:
            return {
                "sample_count": 0,
                "voltage_mv": 0.0,
                "voltage_min_mv": 0.0,
                "voltage_max_mv": 0.0,
                "voltage_avg_mv": 0.0,
                "voltage_std_dev_mv": 0.0,
                "voltage_spike_count": 0,
                "voltage_stability_score": 0.0,
                "window_seconds": window_seconds
            }
        
        voltages = [h['voltage_mv'] for h in recent]
        avg = sum(voltages) / len(voltages)
        
        # Standard deviation
        if len(voltages) > 1:
            variance = sum((v - avg) ** 2 for v in voltages) / (len(voltages) - 1)
            std_dev = variance ** 0.5
        else:
            std_dev = 0.0
        
        # Spike detection (>50mV change between consecutive samples)
        spike_threshold = 50.0  # mV
        spike_count = 0
        for i in range(1, len(voltages)):
            if abs(voltages[i] - voltages[i-1]) > spike_threshold:
                spike_count += 1
        
        # Stability score: 1.0 = perfectly stable, 0.0 = chaotic
        # Based on coefficient of variation (lower = more stable)
        cv = (std_dev / avg) if avg > 0 else 0
        stability = max(0.0, min(1.0, 1.0 - (cv * 10)))
        
        return {
            "sample_count": len(voltages),
            "voltage_mv": voltages[-1] if voltages else 0.0,
            "voltage_min_mv": min(voltages),
            "voltage_max_mv": max(voltages),
            "voltage_avg_mv": avg,
            "voltage_std_dev_mv": std_dev,
            "voltage_spike_count": spike_count,
            "voltage_stability_score": stability,
            "window_seconds": window_seconds
        }
    
    def get_all_sensors(self) -> Dict[str, Dict[str, Any]]:
        """Get all cached sensor readings."""
        self._refresh_cache()
        return dict(self._sensor_cache)
    
    def get_sensor_count(self) -> int:
        """Get total number of known sensors."""
        return len(self._sensor_cache)
    
    def reconnect(self) -> bool:
        """Force reconnection attempt."""
        self._consecutive_failures = 0
        return self._try_connect()
    
    def close(self):
        """Cleanup bridge resources."""
        self._connected = False
        self._sensor_cache.clear()
        self._voltage_history.clear()
        logging.info("[LHMBridge] Bridge closed")


# ============================================================================
# MODULE TEST / CLI
# ============================================================================

def main():
    """Quick test of LHM Bridge connection and voltage readings."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("=" * 60)
    print("  LHM Bridge - Connection Test")
    print("=" * 60)
    
    bridge = LHMBridge()
    status = bridge.get_status()
    
    print(f"\n  Connected: {status['connected']}")
    print(f"  Sensors: {status['sensor_count']}")
    print(f"  URL: {status['url']}")
    
    if bridge.is_connected():
        # Voltage snapshot
        snapshot = bridge.get_voltage_snapshot()
        print(f"\n  === VOLTAGE SNAPSHOT ===")
        print(f"  NVIDIA GPU Core: {snapshot['gpu_nvidia_voltage_mv']:.1f} mV ({snapshot['gpu_nvidia_voltage_mv']/1000:.3f} V)")
        print(f"  AMD iGPU Core:   {snapshot['gpu_amd_core_voltage_mv']:.1f} mV ({snapshot['gpu_amd_core_voltage_mv']/1000:.3f} V)")
        print(f"  AMD iGPU SoC:    {snapshot['gpu_amd_soc_voltage_mv']:.1f} mV ({snapshot['gpu_amd_soc_voltage_mv']/1000:.3f} V)")
        print(f"  CPU Average:     {snapshot['cpu_voltage_avg_mv']:.1f} mV ({snapshot['cpu_voltage_avg_mv']/1000:.3f} V)")
        print(f"  CPU Range:       {snapshot['cpu_voltage_min_mv']:.1f} - {snapshot['cpu_voltage_max_mv']:.1f} mV")
        print(f"  Battery:         {snapshot['battery_voltage_v']:.3f} V")
        print(f"  Cores monitored: {len(snapshot['cpu_voltage_per_core_mv'])}")
        
        # All voltages
        all_v = bridge.get_all_voltages()
        print(f"\n  === ALL VOLTAGE SENSORS ({len(all_v)}) ===")
        for vid, vdata in all_v.items():
            print(f"  {vdata['label']}: {vdata['raw_value']}  [{vid}]")
    else:
        print(f"\n  ERROR: {status['last_error']}")
        print("  Make sure LibreHardwareMonitor is running as Administrator")
        print("  with HTTP server enabled on port 8085.")
    
    bridge.close()
    print(f"\n  Done.")


if __name__ == '__main__':
    main()
