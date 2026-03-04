"""
VitalHeart Phase 3: LHM Enhanced Monitor
=========================================

Captures ALL 315 sensors from LibreHardwareMonitor and stores them in the 
research database. This supplements (does NOT replace) existing pynvml/psutil 
monitoring.

REQUIRES:
- LibreHardwareMonitor running as Administrator with HTTP server on port 8085
- LHM Bridge (lhm_bridge.py) for REST API access

TOOLS USED:
- LHMBridge: REST API client for LHM
- TimeSync: Timestamping
- ErrorRecovery: Graceful degradation

Author: MiMo (Executor Agent for Team Brain)
Date: February 15, 2026
Protocol: BUILD_PROTOCOL_V1.md + Bug Hunt Protocol (100% Compliance)
License: MIT
"""

import time
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

try:
    from lhm_bridge import LHMBridge
    LHM_AVAILABLE = True
except ImportError:
    LHM_AVAILABLE = False
    logging.warning("[LHMEnhancedMonitor] lhm_bridge not available")

__version__ = "1.0.0"


class LHMEnhancedMonitor:
    """
    LHM Enhanced Monitor - Captures ALL 315 sensors from LibreHardwareMonitor.
    
    Features:
    - Takes existing LHMBridge instance (shares connection with VoltageTracker)
    - Samples all 315 sensors in one call
    - Organizes data by hardware component
    - Graceful degradation (returns None if LHM not connected)
    - Stores raw sensor dump for future-proofing
    
    Usage:
        bridge = LHMBridge()
        monitor = LHMEnhancedMonitor(bridge)
        if monitor.enabled:
            snapshot = monitor.sample()
            # snapshot contains all 315 sensors organized by component
    """
    
    def __init__(self, bridge: LHMBridge):
        """
        Initialize LHM Enhanced Monitor.
        
        Args:
            bridge: Existing LHMBridge instance (shared with VoltageTracker)
        """
        self.bridge = bridge
        self.enabled = bridge.is_connected() if bridge else False
        
        if not self.enabled:
            logging.warning("[LHMEnhancedMonitor] LHM Bridge not connected - monitor disabled")
        else:
            logging.info("[LHMEnhancedMonitor] Initialized with LHM Bridge")
    
    def sample(self) -> Optional[Dict[str, Any]]:
        """
        Sample ALL 315 sensors from LHM and organize by component.
        
        Returns:
            Structured dict with all sensor data, or None if LHM not connected.
        """
        if not self.enabled or not self.bridge:
            return None
        
        try:
            # Get all sensors from LHM
            all_sensors = self.bridge.get_all_sensors()
            
            if not all_sensors:
                logging.warning("[LHMEnhancedMonitor] No sensors returned from LHM")
                return None
            
            # Build organized snapshot
            snapshot = {
                "timestamp": datetime.now().isoformat(),
                "lhm_connected": True,
                "sensor_count": len(all_sensors),
                "nvidia_gpu": self._extract_nvidia_gpu(all_sensors),
                "amd_igpu": self._extract_amd_igpu(all_sensors),
                "cpu": self._extract_cpu(all_sensors),
                "ram_physical": self._extract_ram_physical(all_sensors),
                "virtual_memory": self._extract_virtual_memory(all_sensors),
                "nvme": self._extract_nvme(all_sensors),
                "battery": self._extract_battery(all_sensors),
                "network": self._extract_network(all_sensors),
                "raw_sensors": all_sensors  # Complete dump for future-proofing
            }
            
            return snapshot
            
        except Exception as e:
            logging.error(f"[LHMEnhancedMonitor] Sample failed: {e}")
            return None
    
    def _extract_nvidia_gpu(self, sensors: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
        """Extract NVIDIA GPU metrics from sensor dict."""
        gpu_data = {}
        
        # Helper to safely get sensor value
        def get_value(sensor_id: str, default: float = 0.0) -> float:
            sensor = sensors.get(sensor_id)
            return float(sensor['value']) if sensor else default
        
        # Voltage and Power
        gpu_data["voltage_mv"] = get_value("/gpu-nvidia/0/voltage/0") * 1000.0
        gpu_data["power_w"] = get_value("/gpu-nvidia/0/power/0")
        
        # Clocks
        gpu_data["clock_core_mhz"] = get_value("/gpu-nvidia/0/clock/0")
        gpu_data["clock_mem_mhz"] = get_value("/gpu-nvidia/0/clock/4")
        
        # Temperatures
        gpu_data["temp_core_c"] = get_value("/gpu-nvidia/0/temperature/0")
        gpu_data["temp_mem_junction_c"] = get_value("/gpu-nvidia/0/temperature/3")
        
        # Loads
        gpu_data["load_core_pct"] = get_value("/gpu-nvidia/0/load/0")
        gpu_data["load_mem_controller_pct"] = get_value("/gpu-nvidia/0/load/1")
        gpu_data["load_video_engine_pct"] = get_value("/gpu-nvidia/0/load/2")
        gpu_data["load_mem_pct"] = get_value("/gpu-nvidia/0/load/3")
        
        # VRAM
        gpu_data["vram_used_mb"] = get_value("/gpu-nvidia/0/smalldata/1")
        gpu_data["vram_free_mb"] = get_value("/gpu-nvidia/0/smalldata/0")
        gpu_data["vram_total_mb"] = get_value("/gpu-nvidia/0/smalldata/2")
        gpu_data["d3d_dedicated_used_mb"] = get_value("/gpu-nvidia/0/smalldata/3")
        gpu_data["d3d_shared_used_mb"] = get_value("/gpu-nvidia/0/smalldata/4")
        
        # PCIe
        gpu_data["pcie_rx_mbs"] = get_value("/gpu-nvidia/0/throughput/0")
        gpu_data["pcie_tx_mbs"] = get_value("/gpu-nvidia/0/throughput/1")
        
        # D3D Loads
        gpu_data["d3d_3d_pct"] = get_value("/gpu-nvidia/0/load/5")
        gpu_data["d3d_copy_pct"] = get_value("/gpu-nvidia/0/load/6")
        gpu_data["d3d_copy_2_pct"] = get_value("/gpu-nvidia/0/load/7")
        gpu_data["d3d_jpeg_decode_pct"] = get_value("/gpu-nvidia/0/load/8")
        gpu_data["d3d_optical_flow_pct"] = get_value("/gpu-nvidia/0/load/9")
        gpu_data["d3d_security_pct"] = get_value("/gpu-nvidia/0/load/10")
        gpu_data["d3d_video_decode_pct"] = get_value("/gpu-nvidia/0/load/11")
        gpu_data["d3d_video_encode_pct"] = get_value("/gpu-nvidia/0/load/12")
        gpu_data["d3d_vr_pct"] = get_value("/gpu-nvidia/0/load/13")
        
        return gpu_data
    
    def _extract_amd_igpu(self, sensors: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
        """Extract AMD iGPU metrics from sensor dict."""
        igpu_data = {}
        
        def get_value(sensor_id: str, default: float = 0.0) -> float:
            sensor = sensors.get(sensor_id)
            return float(sensor['value']) if sensor else default
        
        # Voltage
        igpu_data["voltage_core_mv"] = get_value("/gpu-amd/0/voltage/0") * 1000.0
        igpu_data["voltage_soc_mv"] = get_value("/gpu-amd/0/voltage/2") * 1000.0
        
        # Power
        igpu_data["power_core_w"] = get_value("/gpu-amd/0/power/0")
        igpu_data["power_soc_w"] = get_value("/gpu-amd/0/power/2")
        
        # Clocks
        igpu_data["clock_core_mhz"] = get_value("/gpu-amd/0/clock/0")
        igpu_data["clock_soc_mhz"] = get_value("/gpu-amd/0/clock/1")
        igpu_data["clock_mem_mhz"] = get_value("/gpu-amd/0/clock/2")
        
        # Temperature
        igpu_data["temp_vr_soc_c"] = get_value("/gpu-amd/0/temperature/4")
        
        # Load
        igpu_data["load_core_pct"] = get_value("/gpu-amd/0/load/0")
        
        # VRAM
        igpu_data["vram_used_mb"] = get_value("/gpu-amd/0/smalldata/0")
        igpu_data["vram_free_mb"] = get_value("/gpu-amd/0/smalldata/1")
        igpu_data["vram_total_mb"] = get_value("/gpu-amd/0/smalldata/2")
        
        # D3D
        igpu_data["d3d_3d_pct"] = get_value("/gpu-amd/0/load/2")
        
        # FPS
        igpu_data["fps"] = get_value("/gpu-amd/0/factor/0")
        
        return igpu_data
    
    def _extract_cpu(self, sensors: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Extract CPU metrics from sensor dict."""
        cpu_data = {}
        
        def get_value(sensor_id: str, default: float = 0.0) -> float:
            sensor = sensors.get(sensor_id)
            return float(sensor['value']) if sensor else default
        
        # Aggregate
        cpu_data["total_load_pct"] = get_value("/amdcpu/0/load/0")
        cpu_data["max_core_load_pct"] = get_value("/amdcpu/0/load/1")
        cpu_data["bus_speed_mhz"] = get_value("/amdcpu/0/clock/0")
        cpu_data["cores_avg_clock_mhz"] = get_value("/amdcpu/0/clock/1")
        cpu_data["cores_avg_effective_mhz"] = get_value("/amdcpu/0/clock/2")
        
        # Per-core (16 cores)
        per_core = []
        for core_num in range(1, 17):
            # Pattern: Core N: clock=/amdcpu/0/clock/{3+2*(N-1)}, effective=/amdcpu/0/clock/{4+2*(N-1)}
            # voltage=/amdcpu/0/voltage/{N+1}, factor=/amdcpu/0/factor/{N-1}
            clock_idx = 3 + 2 * (core_num - 1)
            effective_idx = 4 + 2 * (core_num - 1)
            voltage_idx = core_num + 1
            factor_idx = core_num - 1
            
            core_data = {
                "core": core_num,
                "clock_mhz": get_value(f"/amdcpu/0/clock/{clock_idx}"),
                "effective_mhz": get_value(f"/amdcpu/0/clock/{effective_idx}"),
                "voltage_mv": get_value(f"/amdcpu/0/voltage/{voltage_idx}") * 1000.0,
                "multiplier": get_value(f"/amdcpu/0/factor/{factor_idx}")
            }
            per_core.append(core_data)
        
        cpu_data["per_core"] = per_core
        
        # Per-thread load (32 threads)
        per_thread_load = []
        for thread in range(2, 34):  # /amdcpu/0/load/2 through /amdcpu/0/load/33
            per_thread_load.append(get_value(f"/amdcpu/0/load/{thread}"))
        cpu_data["per_thread_load"] = per_thread_load
        
        # Power and temperature (if available)
        cpu_data["power_package_w"] = get_value("/amdcpu/0/power/0", default=0.0)
        cpu_data["temp_tctl_c"] = get_value("/amdcpu/0/temperature/0", default=0.0)
        
        return cpu_data
    
    def _extract_ram_physical(self, sensors: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Extract RAM physical metrics from sensor dict."""
        ram_data = {}
        
        def get_value(sensor_id: str, default: float = 0.0) -> float:
            sensor = sensors.get(sensor_id)
            return float(sensor['value']) if sensor else default
        
        # System RAM
        ram_data["total_used_gb"] = get_value("/ram/data/0")
        ram_data["total_available_gb"] = get_value("/ram/data/1")
        ram_data["total_load_pct"] = get_value("/ram/load/0")
        
        # Corsair RAM sticks - find by path matching
        corsair_stick_0 = {}
        corsair_stick_1 = {}
        
        for sensor_id, sensor_data in sensors.items():
            path = sensor_data.get('path', '').lower()
            
            if 'corsair' in path:
                if '#0' in path:
                    if 'temperature' in path:
                        ram_data["stick_0_temp_c"] = sensor_data['value']
                    elif 'data' in path:
                        # Extract key from path
                        key = path.split('/')[-1]
                        corsair_stick_0[key] = sensor_data['value']
                    elif 'timings' in path:
                        key = path.split('/')[-1]
                        corsair_stick_0[key] = sensor_data['value']
                
                elif '#1' in path:
                    if 'temperature' in path:
                        ram_data["stick_1_temp_c"] = sensor_data['value']
                    elif 'data' in path:
                        key = path.split('/')[-1]
                        corsair_stick_1[key] = sensor_data['value']
                    elif 'timings' in path:
                        key = path.split('/')[-1]
                        corsair_stick_1[key] = sensor_data['value']
        
        # Store Corsair data
        ram_data["stick_0_data"] = corsair_stick_0
        ram_data["stick_1_data"] = corsair_stick_1
        ram_data["stick_0_timings"] = corsair_stick_0  # Combined for simplicity
        ram_data["stick_1_timings"] = corsair_stick_1
        
        # Set defaults if not found
        if "stick_0_temp_c" not in ram_data:
            ram_data["stick_0_temp_c"] = 0.0
        if "stick_1_temp_c" not in ram_data:
            ram_data["stick_1_temp_c"] = 0.0
        
        return ram_data
    
    def _extract_virtual_memory(self, sensors: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
        """Extract virtual memory metrics from sensor dict."""
        vmem_data = {}
        
        def get_value(sensor_id: str, default: float = 0.0) -> float:
            sensor = sensors.get(sensor_id)
            return float(sensor['value']) if sensor else default
        
        vmem_data["used_gb"] = get_value("/vram/data/2")
        vmem_data["available_gb"] = get_value("/vram/data/3")
        vmem_data["load_pct"] = get_value("/vram/load/1")
        
        return vmem_data
    
    def _extract_nvme(self, sensors: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Extract NVMe drive metrics from sensor dict."""
        nvme_data = {
            "drive_0": {},
            "drive_1": {}
        }
        
        def get_value(sensor_id: str, default: float = 0.0) -> float:
            sensor = sensors.get(sensor_id)
            return float(sensor['value']) if sensor else default
        
        # Drive 0
        drive_0 = nvme_data["drive_0"]
        drive_0["temp_composite_c"] = get_value("/nvme/0/temperature/0")
        drive_0["temp_1_c"] = get_value("/nvme/0/temperature/1")
        drive_0["temp_2_c"] = get_value("/nvme/0/temperature/2")
        drive_0["temp_3_c"] = get_value("/nvme/0/temperature/3")
        drive_0["temp_warning_c"] = get_value("/nvme/0/temperature/10")
        drive_0["temp_critical_c"] = get_value("/nvme/0/temperature/11")
        drive_0["life_pct"] = get_value("/nvme/0/level/20")
        drive_0["available_spare_pct"] = get_value("/nvme/0/level/100")
        drive_0["spare_threshold_pct"] = get_value("/nvme/0/level/101")
        drive_0["pct_used"] = get_value("/nvme/0/level/102")
        drive_0["used_space_pct"] = get_value("/nvme/0/load/30")
        drive_0["read_activity_pct"] = get_value("/nvme/0/load/51")
        drive_0["write_activity_pct"] = get_value("/nvme/0/load/52")
        drive_0["total_activity_pct"] = get_value("/nvme/0/load/53")
        drive_0["read_rate_kbs"] = get_value("/nvme/0/throughput/54")
        drive_0["write_rate_kbs"] = get_value("/nvme/0/throughput/55")
        drive_0["data_read_gb"] = get_value("/nvme/0/data/21")
        drive_0["data_written_gb"] = get_value("/nvme/0/data/22")
        drive_0["free_space_gb"] = get_value("/nvme/0/data/31")
        drive_0["total_space_gb"] = get_value("/nvme/0/data/32")
        drive_0["power_on_count"] = int(get_value("/nvme/0/factor/23"))
        drive_0["power_on_hours"] = int(get_value("/nvme/0/factor/24"))
        
        # Drive 1
        drive_1 = nvme_data["drive_1"]
        drive_1["temp_composite_c"] = get_value("/nvme/1/temperature/0")
        drive_1["temp_1_c"] = get_value("/nvme/1/temperature/1")
        drive_1["temp_2_c"] = get_value("/nvme/1/temperature/2")
        drive_1["temp_3_c"] = get_value("/nvme/1/temperature/3")
        drive_1["temp_warning_c"] = get_value("/nvme/1/temperature/10")
        drive_1["temp_critical_c"] = get_value("/nvme/1/temperature/11")
        drive_1["life_pct"] = get_value("/nvme/1/level/20")
        drive_1["available_spare_pct"] = get_value("/nvme/1/level/100")
        drive_1["spare_threshold_pct"] = get_value("/nvme/1/level/101")
        drive_1["pct_used"] = get_value("/nvme/1/level/102")
        drive_1["used_space_pct"] = get_value("/nvme/1/load/30")
        drive_1["read_activity_pct"] = get_value("/nvme/1/load/51")
        drive_1["write_activity_pct"] = get_value("/nvme/1/load/52")
        drive_1["total_activity_pct"] = get_value("/nvme/1/load/53")
        drive_1["read_rate_kbs"] = get_value("/nvme/1/throughput/54")
        drive_1["write_rate_kbs"] = get_value("/nvme/1/throughput/55")
        drive_1["data_read_gb"] = get_value("/nvme/1/data/21")
        drive_1["data_written_gb"] = get_value("/nvme/1/data/22")
        drive_1["free_space_gb"] = get_value("/nvme/1/data/31")
        drive_1["total_space_gb"] = get_value("/nvme/1/data/32")
        drive_1["power_on_count"] = int(get_value("/nvme/1/factor/23"))
        drive_1["power_on_hours"] = int(get_value("/nvme/1/factor/24"))
        
        return nvme_data
    
    def _extract_battery(self, sensors: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
        """Extract battery metrics from sensor dict."""
        battery_data = {}
        
        def get_value(sensor_id: str, default: float = 0.0) -> float:
            sensor = sensors.get(sensor_id)
            return float(sensor['value']) if sensor else default
        
        battery_data["voltage_v"] = get_value("/battery/R220358_1/voltage/0")
        battery_data["discharge_current_a"] = get_value("/battery/R220358_1/current/0")
        battery_data["discharge_rate_w"] = get_value("/battery/R220358_1/power/0")
        battery_data["charge_level_pct"] = get_value("/battery/R220358_1/level/0")
        battery_data["degradation_pct"] = get_value("/battery/R220358_1/level/1")
        battery_data["designed_capacity_mwh"] = get_value("/battery/R220358_1/energy/0")
        battery_data["full_charge_capacity_mwh"] = get_value("/battery/R220358_1/energy/1")
        battery_data["remaining_capacity_mwh"] = get_value("/battery/R220358_1/energy/2")
        
        return battery_data
    
    def _extract_network(self, sensors: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Extract network adapter metrics from sensor dict."""
        network_data = {
            "wifi": {},
            "tailscale": {},
            "wsl": {}
        }
        
        def get_value(sensor_id: str, default: float = 0.0) -> float:
            sensor = sensors.get(sensor_id)
            return float(sensor['value']) if sensor else default
        
        # Find network adapters by path matching
        wifi_adapter = None
        tailscale_adapter = None
        wsl_adapter = None
        
        for sensor_id, sensor_data in sensors.items():
            # ATLAS FIX: 'nic' appears in sensor_id (/nic/{guid}/...) NOT in path.
            # Path format is /Sensor/HOSTNAME/AdapterName/... (e.g. /Sensor/ASUS_AMD_9/Wi-Fi/...)
            if not sensor_id.startswith('/nic/'):
                continue
            path = sensor_data.get('path', '').lower()
            
            if 'wi-fi' in path or 'wifi' in path:
                # ATLAS FIX: sensor_id format is /nic/{guid}/... so GUID is at index 2
                wifi_adapter = sensor_id.split('/')[2]  # Extract URL-encoded GUID
            elif 'tailscale' in path:
                tailscale_adapter = sensor_id.split('/')[2]
            elif 'vethernet' in path or 'wsl' in path:
                wsl_adapter = sensor_id.split('/')[2]
        
        # Extract data for each adapter
        def extract_adapter_data(guid: str, adapter_name: str):
            if not guid:
                return {}
            
            adapter_data = {}
            # Throughput
            adapter_data["upload_speed_kbs"] = get_value(f"/nic/{guid}/throughput/7")
            adapter_data["download_speed_kbs"] = get_value(f"/nic/{guid}/throughput/8")
            # Load
            adapter_data["utilization_pct"] = get_value(f"/nic/{guid}/load/1")
            # Data
            adapter_data["data_uploaded_gb"] = get_value(f"/nic/{guid}/data/2")
            adapter_data["data_downloaded_gb"] = get_value(f"/nic/{guid}/data/3")
            
            return adapter_data
        
        network_data["wifi"] = extract_adapter_data(wifi_adapter, "wifi")
        network_data["tailscale"] = extract_adapter_data(tailscale_adapter, "tailscale")
        network_data["wsl"] = extract_adapter_data(wsl_adapter, "wsl")
        
        return network_data


def main():
    """Quick test of LHM Enhanced Monitor."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("=" * 60)
    print("  LHM Enhanced Monitor - Test")
    print("=" * 60)
    
    # Create bridge
    bridge = LHMBridge()
    
    if not bridge.is_connected():
        print("\n  ERROR: LHM not connected")
        print("  Make sure LibreHardwareMonitor is running as Administrator")
        print("  with HTTP server enabled on port 8085.")
        return
    
    # Create monitor
    monitor = LHMEnhancedMonitor(bridge)
    
    if not monitor.enabled:
        print("\n  ERROR: Monitor not enabled")
        return
    
    # Sample
    print("\n  Sampling all 315 sensors...")
    snapshot = monitor.sample()
    
    if snapshot:
        print(f"\n  SUCCESS!")
        print(f"  Timestamp: {snapshot['timestamp']}")
        print(f"  Sensor Count: {snapshot['sensor_count']}")
        print(f"  LHM Connected: {snapshot['lhm_connected']}")
        
        # Show some key metrics
        print(f"\n  NVIDIA GPU:")
        print(f"    Voltage: {snapshot['nvidia_gpu']['voltage_mv']:.1f} mV")
        print(f"    Power: {snapshot['nvidia_gpu']['power_w']:.1f} W")
        print(f"    Temp: {snapshot['nvidia_gpu']['temp_core_c']:.1f} °C")
        
        print(f"\n  CPU:")
        print(f"    Load: {snapshot['cpu']['total_load_pct']:.1f}%")
        print(f"    Cores: {len(snapshot['cpu']['per_core'])}")
        
        print(f"\n  Battery:")
        print(f"    Voltage: {snapshot['battery']['voltage_v']:.3f} V")
        print(f"    Charge: {snapshot['battery']['charge_level_pct']:.1f}%")
        
        print(f"\n  NVMe Drives:")
        print(f"    Drive 0 Temp: {snapshot['nvme']['drive_0']['temp_composite_c']:.1f} °C")
        print(f"    Drive 1 Temp: {snapshot['nvme']['drive_1']['temp_composite_c']:.1f} °C")
        
        print(f"\n  Raw sensors stored: {len(snapshot['raw_sensors'])} entries")
        
    else:
        print("\n  ERROR: Failed to sample")
    
    bridge.close()


if __name__ == '__main__':
    main()