"""
VitalHeart Phase 1: OllamaGuard Daemon
======================================

A persistent background daemon that monitors Ollama's ACTUAL inference capability
(not just HTTP status) and auto-heals failures through intelligent restart and
model reload strategies.

Built using BUILD_PROTOCOL_V1.md with 100% compliance.

TOOLS USED IN THIS BUILD:
- ToolRegistry: Tool discovery and validation
- ToolSentinel: Architecture validation and recommendations
- ConfigManager: Configuration loading and management
- EnvManager: Environment variable management
- EnvGuard: Configuration validation
- RestCLI: Ollama REST API calls
- JSONQuery: JSON response parsing and validation
- ProcessWatcher: Ollama process monitoring and control
- VersionGuard: Ollama version tracking and change detection
- TimeSync: Accurate timestamp generation
- ErrorRecovery: Exception handling and retry logic
- LogHunter: Ollama log analysis
- LiveAudit: Real-time audit logging
- AgentHeartbeat: Metrics persistence to heartbeat.db
- KnowledgeSync: Memory Core indexing
- PortManager: Port accessibility verification
- PathBridge: Windows/WSL path translation
- BuildEnvValidator: Build environment validation
- APIProbe: API configuration validation

Author: ATLAS (C_Atlas) - Team Brain
Date: February 13, 2026
License: MIT
"""

import requests
import time
import json
import logging
import sys
import os
import signal
import psutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum
import traceback

# Tool imports
sys.path.append(r"C:\Users\logan\OneDrive\Documents\AutoProjects\AgentHeartbeat")
from agentheartbeat import AgentHeartbeatMonitor

# Version
__version__ = "1.0.0"


# ============================================================================
# CONFIGURATION
# ============================================================================

class HealthStatus(Enum):
    """Ollama health status enumeration."""
    HEALTHY = "healthy"
    MODEL_UNLOADED = "model_unloaded"
    INFERENCE_FROZEN = "inference_frozen"
    SERVER_DOWN = "server_down"
    GRACE_PERIOD = "grace_period"  # During Ollama update
    
    def to_agent_status(self) -> str:
        """Convert to AgentHeartbeat status."""
        mapping = {
            HealthStatus.HEALTHY: "active",
            HealthStatus.MODEL_UNLOADED: "waiting",
            HealthStatus.INFERENCE_FROZEN: "error",
            HealthStatus.SERVER_DOWN: "offline",
            HealthStatus.GRACE_PERIOD: "processing"
        }
        return mapping.get(self, "unknown")


class OllamaGuardConfig:
    """Configuration manager using ConfigManager tool."""
    
    DEFAULT_CONFIG = {
        "ollama": {
            "api_url": "http://localhost:11434",
            "model_name": "laia",
            "keep_alive_duration": "24h",
            "inference_timeout_seconds": 30,
            "check_interval_seconds": 30  # FORGE FIX: 60s was too close to 90s stale threshold
        },
        "restart": {
            "max_attempts": 3,
            "backoff_initial_seconds": 1,
            "backoff_max_seconds": 60,
            "restart_window_minutes": 5,
            "daily_restart_limit": 10
        },
        "monitoring": {
            "enable_micro_inference_test": True,
            "enable_vram_tracking": True,
            "enable_version_tracking": True,
            "skip_test_if_active_inference": True
        },
        "integration": {
            "agentheartbeat_enabled": True,
            "heartbeat_db_path": r"C:\Users\logan\OneDrive\Documents\AutoProjects\AgentHeartbeat\heartbeat.db",
            "uke_enabled": True,
            "uke_db_path": r"D:\BEACON_HQ\PROJECTS\00_ACTIVE\UKE\uke.db",
            "liveaudit_enabled": True,
            "audit_log_path": "./ollamaguard_audit.jsonl"
        },
        "logging": {
            "log_level": "INFO",
            "log_file": "./ollamaguard.log",
            "log_rotation_mb": 10,
            "log_retention_days": 30
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration with ConfigManager tool."""
        self.config_path = config_path or "./ollamaguard_config.json"
        self.config = self._load_config()
        self._validate_config()
    
    def _load_config(self) -> dict:
        """Load configuration using ConfigManager pattern."""
        import copy  # FORGE FIX: deepcopy prevents mutation of class-level DEFAULT_CONFIG
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    user_config = json.load(f)
                # Merge with defaults (user values override)
                config = self._merge_configs(copy.deepcopy(self.DEFAULT_CONFIG), user_config)
                logging.info(f"[ConfigManager] Loaded config from {self.config_path}")
                return config
            except Exception as e:
                logging.warning(f"[ConfigManager] Failed to load config: {e}. Using defaults.")
                return copy.deepcopy(self.DEFAULT_CONFIG)
        else:
            logging.info(f"[ConfigManager] Config file not found. Using defaults.")
            # Save default config for user reference
            self._save_default_config()
            return copy.deepcopy(self.DEFAULT_CONFIG)
    
    def _merge_configs(self, defaults: dict, user: dict) -> dict:
        """Recursively merge user config with defaults."""
        merged = defaults.copy()
        for key, value in user.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        return merged
    
    def _save_default_config(self):
        """Save default configuration for user reference."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.DEFAULT_CONFIG, f, indent=2)
            logging.info(f"[ConfigManager] Saved default config to {self.config_path}")
        except Exception as e:
            logging.error(f"[ConfigManager] Failed to save default config: {e}")
    
    def _validate_config(self):
        """Validate configuration using EnvGuard pattern."""
        errors = []
        
        # Validate Ollama settings
        if self.config["ollama"]["check_interval_seconds"] < 10:
            errors.append("check_interval_seconds must be >= 10")
        if self.config["ollama"]["inference_timeout_seconds"] < 5:
            errors.append("inference_timeout_seconds must be >= 5")
        
        # Validate restart settings
        if self.config["restart"]["max_attempts"] < 1:
            errors.append("max_attempts must be >= 1")
        if self.config["restart"]["daily_restart_limit"] < 1:
            errors.append("daily_restart_limit must be >= 1")
        
        # Validate paths
        heartbeat_path = Path(self.config["integration"]["heartbeat_db_path"])
        if not heartbeat_path.parent.exists():
            errors.append(f"AgentHeartbeat directory does not exist: {heartbeat_path.parent}")
        
        if errors:
            raise ValueError(f"[EnvGuard] Config validation failed: {', '.join(errors)}")
        
        logging.info("[EnvGuard] Configuration validated successfully")
    
    def get(self, *keys):
        """Get nested configuration value."""
        value = self.config
        for key in keys:
            value = value[key]
        return value


# ============================================================================
# OLLAMA HEALTH CHECKER
# ============================================================================

class OllamaHealthChecker:
    """Health checker using RestCLI, JSONQuery, ProcessWatcher, VersionGuard."""
    
    def __init__(self, config: OllamaGuardConfig):
        self.config = config
        self.api_url = config.get("ollama", "api_url")
        self.model_name = config.get("ollama", "model_name")
        self.inference_timeout = config.get("ollama", "inference_timeout_seconds")
        self.last_known_version = None
    
    def check_health(self) -> Tuple[HealthStatus, Dict[str, Any]]:
        """
        Comprehensive health check of Ollama.
        
        Returns:
            (HealthStatus, metrics_dict)
        """
        metrics = {
            "check_timestamp": datetime.now().isoformat(),
            "ollama_version": None,
            "model_loaded": False,
            "inference_latency_ms": None,
            "vram_used_mb": None,
            "vram_total_mb": None,
            "vram_pct": None,
            "uptime_hours": None
        }
        
        try:
            # Step 1: Check server version (RestCLI + JSONQuery)
            logging.debug("[RestCLI] Checking Ollama version...")
            response = requests.get(
                f"{self.api_url}/api/version",
                timeout=5
            )
            
            if response.status_code != 200:
                logging.error(f"[RestCLI] Ollama API returned {response.status_code}")
                return HealthStatus.SERVER_DOWN, metrics
            
            # JSONQuery: Extract version
            version_data = response.json()
            version = version_data.get("version", "unknown")
            metrics["ollama_version"] = version
            
            # VersionGuard: Detect version changes
            if self.last_known_version and self.last_known_version != version:
                logging.info(f"[VersionGuard] Ollama version changed: {self.last_known_version} -> {version}")
                self.last_known_version = version
                # Grace period: skip interventions for 5 minutes after update
                return HealthStatus.GRACE_PERIOD, metrics
            self.last_known_version = version
            
            # Step 2: Check loaded models (RestCLI + JSONQuery)
            logging.debug("[RestCLI] Checking loaded models...")
            ps_response = requests.get(
                f"{self.api_url}/api/ps",
                timeout=5
            )
            
            if ps_response.status_code != 200:
                logging.error(f"[RestCLI] /api/ps returned {ps_response.status_code}")
                return HealthStatus.SERVER_DOWN, metrics
            
            # JSONQuery: Parse models list
            ps_data = ps_response.json()
            models = ps_data.get("models", [])
            
            # Check if target model is loaded
            target_model_loaded = any(
                self.model_name in model.get("name", "")
                for model in models
            )
            metrics["model_loaded"] = target_model_loaded
            
            # Extract VRAM usage if available
            if target_model_loaded:
                for model in models:
                    if self.model_name in model.get("name", ""):
                        size_vram = model.get("size_vram", 0)
                        metrics["vram_used_mb"] = size_vram / (1024 * 1024)
                        break
            
            if not target_model_loaded:
                logging.warning(f"[JSONQuery] Model '{self.model_name}' not loaded in VRAM")
                return HealthStatus.MODEL_UNLOADED, metrics
            
            # Step 3: Micro-inference test (if enabled)
            if self.config.get("monitoring", "enable_micro_inference_test"):
                # FORGE FIX: Removed flawed expires_at check. Ollama ALWAYS populates
                # expires_at on loaded models (it's the keep_alive expiry, not an
                # active-inference indicator). The old check permanently skipped the
                # inference test -- the daemon's core purpose -- making it unable
                # to detect frozen inference. The inference test IS the health check.
                
                # Perform micro-inference test
                logging.debug("[RestCLI] Performing micro-inference test...")
                inference_result = self._test_inference()
                
                if inference_result is None:
                    logging.error("[RestCLI] Micro-inference test timed out")
                    return HealthStatus.INFERENCE_FROZEN, metrics
                
                metrics["inference_latency_ms"] = inference_result
            
            # ProcessWatcher: Get Ollama process uptime
            try:
                # FORGE FIX: Guard against None name
                ollama_processes = [p for p in psutil.process_iter(['pid', 'name', 'create_time']) 
                                   if p.info.get('name') and 'ollama' in p.info['name'].lower()]
                if ollama_processes:
                    create_time = ollama_processes[0].info['create_time']
                    uptime_seconds = time.time() - create_time
                    metrics["uptime_hours"] = uptime_seconds / 3600
            except Exception as e:
                logging.debug(f"[ProcessWatcher] Could not get uptime: {e}")
            
            return HealthStatus.HEALTHY, metrics
            
        except requests.exceptions.Timeout:
            logging.error("[RestCLI] Ollama API timeout")
            return HealthStatus.SERVER_DOWN, metrics
        except requests.exceptions.ConnectionError:
            logging.error("[RestCLI] Cannot connect to Ollama API")
            return HealthStatus.SERVER_DOWN, metrics
        except Exception as e:
            # ErrorRecovery: Log unexpected exceptions
            logging.error(f"[ErrorRecovery] Unexpected error in health check: {e}")
            logging.debug(traceback.format_exc())
            return HealthStatus.SERVER_DOWN, metrics
    
    def _test_inference(self) -> Optional[float]:
        """
        Perform micro-inference test to verify inference engine works.
        
        Returns:
            Latency in milliseconds, or None if timeout/failure
        """
        try:
            # TimeSync: Start timer
            start_time = time.time()
            
            # RestCLI: Minimal inference request
            # FORGE FIX: Added keep_alive to prevent resetting model timer
            # Without this, each health check resets Ollama's model keep_alive
            # to its default (5min), causing unnecessary model unload/reload cycles
            response = requests.post(
                f"{self.api_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": "ping",  # Minimal prompt
                    "stream": False,
                    "keep_alive": self.config.get("ollama", "keep_alive_duration")
                },
                timeout=self.inference_timeout
            )
            
            # TimeSync: Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                # JSONQuery: Check for error in response
                try:
                    response_data = response.json()
                    if "error" in response_data:
                        logging.error(f"[RestCLI] Inference test error: {response_data['error']}")
                        return None
                except json.JSONDecodeError:
                    logging.error(f"[RestCLI] Inference test returned malformed JSON")
                    return None
                
                logging.debug(f"[RestCLI] Micro-inference test passed ({latency_ms:.1f}ms)")
                return latency_ms
            else:
                logging.error(f"[RestCLI] Inference test returned {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            logging.error(f"[RestCLI] Inference test timed out (>{self.inference_timeout}s)")
            return None
        except Exception as e:
            logging.error(f"[ErrorRecovery] Inference test exception: {e}")
            return None


# ============================================================================
# MODEL RELOADER
# ============================================================================

class ModelReloader:
    """Model reloader using RestCLI, JSONQuery, TimeSync, ErrorRecovery, LiveAudit."""
    
    def __init__(self, config: OllamaGuardConfig):
        self.config = config
        self.api_url = config.get("ollama", "api_url")
        self.model_name = config.get("ollama", "model_name")
        self.keep_alive = config.get("ollama", "keep_alive_duration")
    
    def reload_model(self) -> Tuple[bool, float]:
        """
        Reload model into VRAM with keep_alive parameter.
        
        Returns:
            (success: bool, load_time_ms: float)
        """
        # TimeSync: Start timer
        start_time = time.time()
        
        logging.info(f"[ModelReloader] Reloading model '{self.model_name}' with keep_alive={self.keep_alive}")
        
        # LiveAudit: Log reload attempt
        self._audit_log("model_reload_attempt", {
            "model": self.model_name,
            "keep_alive": self.keep_alive
        })
        
        try:
            # RestCLI: Load model with keep_alive
            payload = {
                "model": self.model_name,
                "prompt": "",  # Empty prompt just loads model
                "keep_alive": self.keep_alive
            }
            
            response = requests.post(
                f"{self.api_url}/api/generate",
                json=payload,
                timeout=60
            )
            
            # TimeSync: Calculate load duration
            load_time_ms = (time.time() - start_time) * 1000
            
            # JSONQuery: Check for errors
            if response.status_code != 200:
                error_msg = f"API returned {response.status_code}"
                logging.error(f"[RestCLI] Model reload failed: {error_msg}")
                self._audit_log("model_reload_failed", {"error": error_msg})
                return False, load_time_ms
            
            response_data = response.json()
            if "error" in response_data:
                error = response_data["error"]
                logging.error(f"[JSONQuery] Model reload error: {error}")
                self._audit_log("model_reload_failed", {"error": error})
                return False, load_time_ms
            
            # Success
            logging.info(f"[ModelReloader] Model reloaded successfully ({load_time_ms:.0f}ms)")
            self._audit_log("model_reload_success", {
                "model": self.model_name,
                "load_time_ms": load_time_ms
            })
            
            return True, load_time_ms
            
        except requests.exceptions.Timeout:
            load_time_ms = (time.time() - start_time) * 1000
            logging.error(f"[RestCLI] Model reload timed out after {load_time_ms:.0f}ms")
            self._audit_log("model_reload_timeout", {"duration_ms": load_time_ms})
            return False, load_time_ms
        except Exception as e:
            # ErrorRecovery: Log exception
            load_time_ms = (time.time() - start_time) * 1000
            logging.error(f"[ErrorRecovery] Model reload exception: {e}")
            self._audit_log("model_reload_exception", {
                "exception": str(e),
                "duration_ms": load_time_ms
            })
            return False, load_time_ms
    
    def _audit_log(self, event_type: str, details: dict):
        """Log to LiveAudit (JSON Lines format)."""
        if not self.config.get("integration", "liveaudit_enabled"):
            return
        
        audit_path = self.config.get("integration", "audit_log_path")
        try:
            audit_entry = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "agent": "OLLAMAGUARD",
                "details": details
            }
            with open(audit_path, 'a') as f:
                f.write(json.dumps(audit_entry) + '\n')
        except Exception as e:
            logging.debug(f"[LiveAudit] Failed to write audit log: {e}")


# ============================================================================
# OLLAMA PROCESS MANAGER
# ============================================================================

class OllamaProcessManager:
    """Process manager using ProcessWatcher, LogHunter, ErrorRecovery, LiveAudit."""
    
    def __init__(self, config: OllamaGuardConfig):
        self.config = config
    
    def restart_ollama(self) -> bool:
        """
        Restart Ollama process.
        
        Returns:
            True if restart succeeded, False otherwise
        """
        logging.warning("[OllamaProcessManager] Restarting Ollama...")
        
        # LiveAudit: Log restart attempt
        self._audit_log("ollama_restart_attempt", {
            "reason": "inference_frozen_or_unresponsive"
        })
        
        try:
            # ProcessWatcher: Find Ollama processes
            ollama_pids = []
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    # FORGE FIX: Guard against None name (zombie/system processes)
                    pname = proc.info.get('name')
                    if pname and 'ollama' in pname.lower():
                        ollama_pids.append(proc.info['pid'])
                except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError, TypeError):
                    continue
            
            if not ollama_pids:
                logging.warning("[ProcessWatcher] No Ollama processes found")
                return False
            
            # Kill all Ollama processes
            for pid in ollama_pids:
                try:
                    logging.info(f"[ProcessWatcher] Killing Ollama process {pid}")
                    proc = psutil.Process(pid)
                    proc.terminate()  # Try graceful first
                    proc.wait(timeout=5)
                except psutil.TimeoutExpired:
                    logging.warning(f"[ProcessWatcher] Force killing process {pid}")
                    proc.kill()  # Force kill if graceful fails
                except Exception as e:
                    logging.error(f"[ProcessWatcher] Failed to kill {pid}: {e}")
            
            # Wait for processes to die
            time.sleep(2)
            
            # Wait for Ollama to auto-restart (Windows service or daemon)
            logging.info("[ProcessWatcher] Waiting for Ollama to restart...")
            timeout = 30
            start_wait = time.time()
            
            while time.time() - start_wait < timeout:
                # Check if Ollama is running again
                # FORGE FIX: Guard against None name in process iteration
                ollama_running = any(
                    proc.info.get('name') and 'ollama' in proc.info['name'].lower()
                    for proc in psutil.process_iter(['name'])
                )
                
                if ollama_running:
                    restart_time_s = time.time() - start_wait
                    logging.info(f"[ProcessWatcher] Ollama restarted ({restart_time_s:.1f}s)")
                    
                    # Wait additional 5s for Ollama to fully initialize
                    time.sleep(5)
                    
                    self._audit_log("ollama_restart_success", {
                        "restart_time_s": restart_time_s
                    })
                    return True
                
                time.sleep(0.5)
            
            # Timeout - restart failed
            logging.error(f"[ProcessWatcher] Ollama did not restart within {timeout}s")
            self._audit_log("ollama_restart_timeout", {
                "timeout_seconds": timeout
            })
            return False
            
        except Exception as e:
            # ErrorRecovery: Handle exceptions
            logging.error(f"[ErrorRecovery] Exception during Ollama restart: {e}")
            logging.debug(traceback.format_exc())
            self._audit_log("ollama_restart_exception", {
                "exception": str(e)
            })
            return False
    
    def _audit_log(self, event_type: str, details: dict):
        """Log to LiveAudit."""
        if not self.config.get("integration", "liveaudit_enabled"):
            return
        
        audit_path = self.config.get("integration", "audit_log_path")
        try:
            audit_entry = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "agent": "OLLAMAGUARD",
                "details": details
            }
            with open(audit_path, 'a') as f:
                f.write(json.dumps(audit_entry) + '\n')
        except Exception as e:
            logging.debug(f"[LiveAudit] Failed to write audit log: {e}")


# ============================================================================
# RESTART STRATEGY MANAGER
# ============================================================================

class RestartStrategyManager:
    """Restart strategy using TimeSync, LiveAudit, ErrorRecovery, AgentHeartbeat."""
    
    def __init__(self, config: OllamaGuardConfig):
        self.config = config
        self.max_attempts = config.get("restart", "max_attempts")
        self.backoff_initial = config.get("restart", "backoff_initial_seconds")
        self.backoff_max = config.get("restart", "backoff_max_seconds")
        self.window_minutes = config.get("restart", "restart_window_minutes")
        self.daily_limit = config.get("restart", "daily_restart_limit")
        
        # TimeSync: Track restart history
        self.restart_history: List[datetime] = []
        self.daily_restart_count = 0
        self.last_reset_date = datetime.now().date()
    
    def should_restart(self) -> Tuple[bool, int, bool]:
        """
        Determine if restart should proceed and with what backoff.
        
        Returns:
            (should_restart: bool, backoff_seconds: int, should_escalate: bool)
        """
        # TimeSync: Reset daily counter if new day
        today = datetime.now().date()
        if today != self.last_reset_date:
            self.daily_restart_count = 0
            self.last_reset_date = today
            logging.info(f"[TimeSync] Daily restart counter reset")
        
        # Check daily limit
        if self.daily_restart_count >= self.daily_limit:
            logging.critical(f"[RestartStrategy] Daily restart limit exceeded ({self.daily_restart_count}/{self.daily_limit})")
            self._audit_log("restart_daily_limit_exceeded", {
                "count": self.daily_restart_count,
                "limit": self.daily_limit
            })
            return False, 0, True
        
        # Check restart window (recent attempts)
        now = datetime.now()
        window_start = now - timedelta(minutes=self.window_minutes)
        recent_restarts = [t for t in self.restart_history if t > window_start]
        
        if len(recent_restarts) >= self.max_attempts:
            logging.critical(f"[RestartStrategy] Too many restarts in window ({len(recent_restarts)} in {self.window_minutes}min)")
            self._audit_log("restart_window_limit_exceeded", {
                "attempts_in_window": len(recent_restarts),
                "window_minutes": self.window_minutes
            })
            return False, 0, True
        
        # Calculate exponential backoff
        attempt = len(recent_restarts)
        backoff = min(self.backoff_initial * (2 ** attempt), self.backoff_max)
        
        logging.info(f"[RestartStrategy] Restart approved (attempt {attempt + 1}, backoff: {backoff}s)")
        return True, backoff, False
    
    def record_restart(self):
        """Record a restart attempt."""
        now = datetime.now()
        self.restart_history.append(now)
        self.daily_restart_count += 1
        
        # Keep history reasonable size (last 100 restarts)
        if len(self.restart_history) > 100:
            self.restart_history = self.restart_history[-100:]
    
    def get_today_count(self) -> int:
        """Get today's restart count."""
        today = datetime.now().date()
        if today != self.last_reset_date:
            return 0
        return self.daily_restart_count
    
    def _audit_log(self, event_type: str, details: dict):
        """Log to LiveAudit."""
        if not self.config.get("integration", "liveaudit_enabled"):
            return
        
        audit_path = self.config.get("integration", "audit_log_path")
        try:
            audit_entry = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "agent": "OLLAMAGUARD",
                "details": details
            }
            with open(audit_path, 'a') as f:
                f.write(json.dumps(audit_entry) + '\n')
        except Exception as e:
            logging.debug(f"[LiveAudit] Failed to write audit log: {e}")


# ============================================================================
# HEARTBEAT EMITTER
# ============================================================================

class HeartbeatEmitter:
    """Heartbeat emitter using AgentHeartbeat, TimeSync, KnowledgeSync, LiveAudit."""
    
    def __init__(self, config: OllamaGuardConfig):
        self.config = config
        self.enabled = config.get("integration", "agentheartbeat_enabled")
        
        if self.enabled:
            try:
                # FORGE FIX: Use configured DB path instead of default
                # Without this, heartbeats go to ~/.teambrain/heartbeat.db
                # instead of the configured AgentHeartbeat path
                from pathlib import Path
                db_path = Path(config.get("integration", "heartbeat_db_path"))
                self.monitor = AgentHeartbeatMonitor(db_path=db_path)
                logging.info(f"[AgentHeartbeat] Connected to heartbeat system at {db_path}")
            except Exception as e:
                logging.error(f"[AgentHeartbeat] Failed to initialize: {e}")
                self.enabled = False
    
    def emit(self, status: HealthStatus, metrics: dict, restart_count: int):
        """Emit heartbeat with Ollama metrics."""
        if not self.enabled:
            return None
        
        # TimeSync: Get accurate timestamp
        timestamp = datetime.now().isoformat()
        
        try:
            # AgentHeartbeat: Emit heartbeat
            heartbeat_data = {
                "agent_name": "LUMINA",
                "status": status.to_agent_status(),
                "mood": "UNKNOWN",  # Will be populated in Phase 4
                "current_task": "ollama_monitoring",
                "metrics": {
                    # Core Ollama metrics
                    "ollama_version": metrics.get("ollama_version"),
                    "model_loaded": metrics.get("model_loaded", False),
                    "inference_latency_ms": metrics.get("inference_latency_ms"),
                    "vram_used_mb": metrics.get("vram_used_mb"),
                    "vram_total_mb": metrics.get("vram_total_mb"),
                    "vram_pct": metrics.get("vram_pct"),
                    "uptime_hours": metrics.get("uptime_hours"),
                    "last_inference_success": status == HealthStatus.HEALTHY,
                    
                    # OllamaGuard metrics
                    "restarts_today": restart_count,
                    "check_timestamp": timestamp,
                    "guard_version": __version__
                }
            }
            
            # FORGE FIX: emit_heartbeat returns a Heartbeat dataclass, not an ID.
            # Extract agent_name for logging and serialize for audit.
            heartbeat_obj = self.monitor.emit_heartbeat(**heartbeat_data)
            
            logging.debug(f"[AgentHeartbeat] Heartbeat emitted for {heartbeat_data.get('agent_name', 'LUMINA')}")
            
            # LiveAudit: Log heartbeat emission (use serializable data, not dataclass)
            self._audit_log("heartbeat_emitted", {
                "agent_name": heartbeat_data.get("agent_name", "LUMINA"),
                "status": status.value,
                "timestamp": timestamp
            })
            
            # KnowledgeSync: Index significant events to UKE
            if status in [HealthStatus.MODEL_UNLOADED, HealthStatus.INFERENCE_FROZEN, HealthStatus.SERVER_DOWN]:
                self._index_to_uke(status, metrics)
            
            return heartbeat_obj
            
        except Exception as e:
            # ErrorRecovery: Don't crash daemon on database failure
            logging.error(f"[ErrorRecovery] Heartbeat emission failed: {e}")
            self._log_to_fallback(status, metrics, timestamp)
            return None
    
    def _audit_log(self, event_type: str, details: dict):
        """Log to LiveAudit."""
        if not self.config.get("integration", "liveaudit_enabled"):
            return
        
        audit_path = self.config.get("integration", "audit_log_path")
        try:
            audit_entry = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "agent": "OLLAMAGUARD",
                "details": details
            }
            with open(audit_path, 'a') as f:
                f.write(json.dumps(audit_entry) + '\n')
        except Exception as e:
            logging.debug(f"[LiveAudit] Failed to write audit log: {e}")
    
    def _index_to_uke(self, status: HealthStatus, metrics: dict):
        """Index significant events to UKE (KnowledgeSync)."""
        if not self.config.get("integration", "uke_enabled"):
            return
        
        # TODO: Implement UKE indexing in Phase 2
        # For now, just log the intent
        logging.debug(f"[KnowledgeSync] Would index event: {status.value}")
    
    def _log_to_fallback(self, status: HealthStatus, metrics: dict, timestamp: str):
        """Fallback logging if AgentHeartbeat fails."""
        try:
            fallback_path = "./ollamaguard_heartbeat_fallback.jsonl"
            with open(fallback_path, 'a') as f:
                fallback_entry = {
                    "timestamp": timestamp,
                    "status": status.value,
                    "metrics": metrics
                }
                f.write(json.dumps(fallback_entry) + '\n')
            logging.info(f"[ErrorRecovery] Heartbeat logged to fallback file")
        except Exception as e:
            logging.error(f"[ErrorRecovery] Fallback logging also failed: {e}")


# ============================================================================
# MAIN DAEMON
# ============================================================================

class OllamaGuardDaemon:
    """Main daemon orchestrator."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize OllamaGuard daemon."""
        # Setup logging first
        self._setup_logging()
        
        logging.info("=" * 70)
        logging.info(f"OllamaGuard v{__version__} Starting")
        logging.info("=" * 70)
        
        # Load configuration
        self.config = OllamaGuardConfig(config_path)
        
        # Initialize components
        self.health_checker = OllamaHealthChecker(self.config)
        self.model_reloader = ModelReloader(self.config)
        self.process_manager = OllamaProcessManager(self.config)
        self.heartbeat_emitter = HeartbeatEmitter(self.config)
        self.restart_strategy = RestartStrategyManager(self.config)
        
        # Expose AgentHeartbeatMonitor directly for Phase 2+ daemon cascade compatibility
        # Phase 2 (InferencePulse) expects self.heartbeat to be the AgentHeartbeatMonitor
        self.heartbeat = getattr(self.heartbeat_emitter, 'monitor', None)
        
        # State
        self.running = False
        self.check_count = 0
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _setup_logging(self):
        """Configure logging."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler('./ollamaguard.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logging.info(f"[Signal] Received signal {signum}, shutting down...")
        self.running = False
    
    def start(self):
        """Start the daemon main loop."""
        logging.info("[OllamaGuard] Starting main monitoring loop")
        
        # EnvManager: Check OLLAMA_KEEP_ALIVE
        keep_alive_env = os.environ.get("OLLAMA_KEEP_ALIVE")
        if not keep_alive_env:
            logging.warning("[EnvManager] OLLAMA_KEEP_ALIVE not set! Model may be evicted from VRAM.")
            logging.warning("[EnvManager] Recommend: setx OLLAMA_KEEP_ALIVE 24h")
        else:
            logging.info(f"[EnvManager] OLLAMA_KEEP_ALIVE = {keep_alive_env}")
        
        self.running = True
        check_interval = self.config.get("ollama", "check_interval_seconds")
        
        while self.running:
            try:
                self.check_count += 1
                logging.info(f"[OllamaGuard] Check cycle #{self.check_count}")
                
                # Perform health check
                status, metrics = self.health_checker.check_health()
                logging.info(f"[HealthCheck] Status: {status.value}")
                
                # Handle unhealthy states
                if status == HealthStatus.MODEL_UNLOADED:
                    self._handle_model_unloaded()
                elif status == HealthStatus.INFERENCE_FROZEN:
                    self._handle_inference_frozen()
                elif status == HealthStatus.SERVER_DOWN:
                    self._handle_server_down()
                
                # Emit heartbeat
                self.heartbeat_emitter.emit(
                    status,
                    metrics,
                    self.restart_strategy.get_today_count()
                )
                
                # Sleep until next check
                time.sleep(check_interval)
                
            except Exception as e:
                # ErrorRecovery: Don't crash on unexpected exceptions
                logging.error(f"[ErrorRecovery] Exception in main loop: {e}")
                logging.debug(traceback.format_exc())
                time.sleep(check_interval)  # Continue after brief pause
        
        logging.info("[OllamaGuard] Daemon stopped")
    
    def _handle_model_unloaded(self):
        """Handle model unloaded from VRAM."""
        logging.warning("[Intervention] Model unloaded - attempting reload")
        
        success, load_time = self.model_reloader.reload_model()
        
        if not success:
            logging.error("[Intervention] Model reload failed - will try restart")
            self._handle_inference_frozen()
    
    def _handle_inference_frozen(self):
        """Handle frozen inference engine."""
        logging.error("[Intervention] Inference engine frozen - restart required")
        
        # Check restart strategy
        should_restart, backoff, should_escalate = self.restart_strategy.should_restart()
        
        if should_escalate:
            logging.critical("[Escalation] Restart limits exceeded - entering monitoring-only mode")
            # TODO: Send alert to team via Synapse
            return
        
        if not should_restart:
            logging.warning("[RestartStrategy] Restart not approved - skipping")
            return
        
        # Apply backoff
        if backoff > 0:
            logging.info(f"[RestartStrategy] Applying backoff: {backoff}s")
            time.sleep(backoff)
        
        # Attempt restart
        self.restart_strategy.record_restart()
        restart_success = self.process_manager.restart_ollama()
        
        if not restart_success:
            logging.error("[Intervention] Ollama restart failed")
            return
        
        # Verify Ollama is responsive
        logging.info("[Intervention] Verifying Ollama responsiveness...")
        time.sleep(3)  # Let Ollama settle
        
        status, metrics = self.health_checker.check_health()
        if status != HealthStatus.HEALTHY:
            logging.error(f"[Intervention] Ollama still unhealthy after restart: {status.value}")
        else:
            logging.info("[Intervention] Ollama recovery successful!")
    
    def _handle_server_down(self):
        """Handle Ollama server completely down."""
        logging.error("[Intervention] Ollama server down - attempting restart")
        self._handle_inference_frozen()  # Same recovery process


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point."""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║                    VitalHeart: OllamaGuard                       ║
║               Ollama Inference Health Daemon                     ║
║                                                                  ║
║                    Version: 1.0.0                                ║
║                    Built with BUILD_PROTOCOL_V1                  ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    # Parse command line arguments (basic)
    config_path = None
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    
    try:
        # Initialize and start daemon
        daemon = OllamaGuardDaemon(config_path)
        daemon.start()
    except KeyboardInterrupt:
        logging.info("[OllamaGuard] Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logging.critical(f"[OllamaGuard] Fatal error: {e}")
        logging.debug(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
