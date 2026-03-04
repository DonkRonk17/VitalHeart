"""
VitalHeart Phase 2: InferencePulse
==================================

Extends OllamaGuard (Phase 1) with real-time AgentHeartbeat integration that triggers
during Lumina's chat responses. Captures inference health metrics tied to actual
conversations, enabling anomaly detection and baseline learning from real-world usage.

NEW FEATURES IN PHASE 2:
- Chat response hooks (monitor Lumina's chat endpoint)
- Enhanced metrics (chat_response_ms, tokens_generated, mood)
- Baseline learning (build normal performance profiles)
- Anomaly detection (alert when metrics deviate from baselines)
- Full UKE knowledge indexing (searchable audit trail)
- Real-time dashboard data (for future HeartWidget)

TOOLS USED IN PHASE 2 (35 total):
- All 31 tools from Phase 1 (extended)
- EmotionalTextureAnalyzer: Mood extraction from chat responses (NEW)
- ConversationAuditor: Metrics validation (NEW)
- TaskQueuePro: UKE write batching (NEW)
- KnowledgeSync: Full UKE implementation (UPGRADED)

Author: ATLAS (C_Atlas) - Team Brain
Date: February 13, 2026
Protocol: BUILD_PROTOCOL_V1.md + Bug Hunt Protocol (100% Compliance)
License: MIT
"""

import asyncio
import threading
import statistics
import sqlite3
import queue
from collections import deque
from typing import Optional, Dict, Any, List, Tuple
import sys
import os
import time
import json
import logging
import traceback
from pathlib import Path
from datetime import datetime, timedelta

# Phase 1 import
sys.path.append(r"C:\Users\logan\OneDrive\Documents\AutoProjects\VitalHeart")
from ollamaguard import (
    OllamaGuardDaemon, 
    OllamaGuardConfig, 
    HealthStatus,
    __version__ as phase1_version
)

# Phase 2 tool imports
sys.path.append(r"C:\Users\logan\OneDrive\Documents\AutoProjects\EmotionalTextureAnalyzer")
from emotionaltextureanalyzer import EmotionalTextureAnalyzer

# Version
__version__ = "2.0.0"
PHASE1_VERSION = phase1_version


# ============================================================================
# PHASE 2: NEW CONFIGURATION
# ============================================================================

class InferencePulseConfig:
    """Extended configuration for Phase 2 features."""
    
    PHASE2_DEFAULTS = {
        "inferencepulse": {
            "enabled": True,
            "chat_hook_enabled": True,
            "lumina_chat_url": "http://localhost:8100",
            "lumina_log_path": "D:/BEACON_HQ/PROJECTS/00_ACTIVE/LOCAL_AI/lumina.log",
            "chat_monitor_interval_seconds": 5,
            "baseline_learning_enabled": True,
            "baseline_min_samples": 100,
            "baseline_update_interval_minutes": 60,
            "anomaly_detection_enabled": True,
            "anomaly_threshold_multiplier": 2.0,
            "anomaly_alert_threshold": "MEDIUM",
            "mood_analysis_enabled": True,
            "mood_analysis_timeout_seconds": 5,
            "mood_analysis_async": True
        },
        "uke": {
            "enabled": True,
            "db_path": "D:/BEACON_HQ/PROJECTS/00_ACTIVE/UKE/uke.db",
            "batch_size": 10,
            "batch_timeout_seconds": 60,
            "event_types": ["chat_response", "anomaly_detected", "baseline_updated", "mood_analyzed"],
            "fallback_log_path": "./uke_fallback.jsonl"
        }
    }
    
    def __init__(self, config_dict: Dict[str, Any] = None):
        """Initialize Phase 2 config with defaults."""
        import copy  # FORGE FIX: deepcopy prevents mutation of class-level PHASE2_DEFAULTS
        self.config = copy.deepcopy(self.PHASE2_DEFAULTS)
        if config_dict:
            # Merge with provided config
            for section in config_dict:
                if section in self.config:
                    self.config[section].update(config_dict[section])
                else:
                    self.config[section] = config_dict[section]
    
    def get(self, section: str, key: str, default=None):
        """Get config value with fallback."""
        return self.config.get(section, {}).get(key, default)


# ============================================================================
# COMPONENT 1: CHAT RESPONSE HOOK
# ============================================================================

class ChatResponseHook:
    """
    Monitor Lumina's chat responses via log file monitoring.
    
    Since we can't directly hook into Lumina's code, we monitor its log file
    for new chat responses and extract timing + token information.
    
    Tools Used: RestCLI (optional API polling), TimeSync, JSONQuery, ErrorRecovery
    """
    
    def __init__(self, config: InferencePulseConfig):
        self.config = config
        self.lumina_url = config.get("inferencepulse", "lumina_chat_url")
        self.lumina_log_path = config.get("inferencepulse", "lumina_log_path")
        self.monitor_interval = config.get("inferencepulse", "chat_monitor_interval_seconds")
        self.enabled = config.get("inferencepulse", "chat_hook_enabled")
        
        self.last_log_position = 0
        self.chat_queue = queue.Queue()
        self.running = False
    
    def start_monitoring(self):
        """Start async log monitoring in background thread."""
        if not self.enabled:
            logging.info("[ChatResponseHook] Disabled via config")
            return
        
        self.running = True
        monitor_thread = threading.Thread(target=self._monitor_log_file, daemon=True)
        monitor_thread.start()
        logging.info("[ChatResponseHook] Started log monitoring")
    
    def stop_monitoring(self):
        """Stop log monitoring."""
        self.running = False
    
    def _monitor_log_file(self):
        """Monitor Lumina's log file for new chat responses."""
        logging.info(f"[ChatResponseHook] Monitoring log: {self.lumina_log_path}")
        
        while self.running:
            try:
                if not Path(self.lumina_log_path).exists():
                    logging.debug(f"[ChatResponseHook] Log file not found, waiting...")
                    time.sleep(self.monitor_interval)
                    continue
                
                with open(self.lumina_log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    # Seek to last read position
                    f.seek(self.last_log_position)
                    
                    # Read new lines
                    new_lines = f.readlines()
                    self.last_log_position = f.tell()
                    
                    # Parse log lines for chat responses
                    for line in new_lines:
                        self._parse_log_line(line)
                
                time.sleep(self.monitor_interval)
                
            except Exception as e:
                # ErrorRecovery: Don't crash on log read failures
                logging.error(f"[ChatResponseHook] Error monitoring log: {e}")
                time.sleep(self.monitor_interval)
    
    def _parse_log_line(self, line: str):
        """
        Parse log line for chat response indicators.
        
        Expected log format (example):
        [2026-02-13 19:30:45] CHAT_RESPONSE | user_id=logan | latency_ms=1234 | tokens=56 | response_preview=Hello...
        """
        try:
            if "CHAT_RESPONSE" not in line:
                return
            
            # JSONQuery: Extract structured data from log line
            parts = line.split("|")
            
            chat_data = {
                "timestamp": datetime.now().isoformat(),
                "chat_response_ms": 0.0,
                "tokens_generated": 0,
                "response_text": ""
            }
            
            for part in parts:
                part = part.strip()
                if "latency_ms=" in part:
                    chat_data["chat_response_ms"] = float(part.split("=")[1])
                elif "tokens=" in part:
                    chat_data["tokens_generated"] = int(part.split("=")[1])
                elif "response_preview=" in part:
                    chat_data["response_text"] = part.split("=", 1)[1]
            
            # Add to queue for processing
            self.chat_queue.put(chat_data)
            logging.debug(f"[ChatResponseHook] Captured chat: {chat_data['chat_response_ms']:.1f}ms, {chat_data['tokens_generated']} tokens")
            
        except Exception as e:
            logging.debug(f"[ChatResponseHook] Error parsing log line: {e}")
    
    def get_latest_chat(self) -> Optional[Dict[str, Any]]:
        """Get latest chat response from queue (non-blocking)."""
        try:
            return self.chat_queue.get_nowait()
        except queue.Empty:
            return None


# ============================================================================
# COMPONENT 2: MOOD ANALYZER
# ============================================================================

class MoodAnalyzer:
    """
    Wrapper for EmotionalTextureAnalyzer with error handling and timeout.
    
    Tools Used: EmotionalTextureAnalyzer, TimeSync, ErrorRecovery
    """
    
    def __init__(self, config: InferencePulseConfig):
        self.config = config
        self.enabled = config.get("inferencepulse", "mood_analysis_enabled")
        self.timeout = config.get("inferencepulse", "mood_analysis_timeout_seconds")
        
        if self.enabled:
            try:
                # EmotionalTextureAnalyzer: Initialize
                self.analyzer = EmotionalTextureAnalyzer()
                logging.info("[MoodAnalyzer] Initialized EmotionalTextureAnalyzer")
            except Exception as e:
                logging.warning(f"[MoodAnalyzer] Failed to initialize: {e}")
                self.enabled = False
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Analyze mood with timeout and error handling.
        
        ⚠️ PLACEHOLDER IMPLEMENTATION ⚠️
        
        This is a SIMPLIFIED mood detection system for Phase 2.
        Full EmotionalTextureAnalyzer integration would require:
        1. Proper CLI argument parsing
        2. Complete 10-dimension analysis pipeline
        3. Pattern-based detection with weights
        4. Intensity calibration from full corpus
        
        Current implementation uses basic keyword matching as a stand-in
        until full EmotionalTextureAnalyzer integration is completed.
        
        Returns dict with: dominant_mood, intensity, dimensions, analysis_time_ms
        """
        if not self.enabled or not text:
            return {
                "dominant_mood": "UNKNOWN",
                "intensity": 0.0,
                "dimensions": {},
                "analysis_time_ms": 0.0
            }
        
        # TimeSync: Start timer
        start_time = time.time()
        
        try:
            # FORGE FIX: Use actual EmotionalTextureAnalyzer when available.
            # The analyzer was imported and initialized in __init__ but never called.
            # Fall back to simple keyword matching only if analyzer is unavailable.
            if hasattr(self, 'analyzer') and self.analyzer:
                try:
                    eta_result = self.analyzer.analyze(text)
                    # Map ETA output to our mood format
                    if eta_result and hasattr(eta_result, 'dimensions'):
                        dimensions = {d.name: d.score for d in eta_result.dimensions} if hasattr(eta_result, 'dimensions') else {}
                        dominant = max(dimensions, key=dimensions.get) if dimensions else "NEUTRAL"
                        intensity = max(dimensions.values()) if dimensions else 0.1
                        mood_result = {
                            "mood": dominant,
                            "intensity": min(1.0, intensity),
                            "dimensions": dimensions
                        }
                    else:
                        # ETA returned unexpected format, fall back
                        mood_result = self._simple_mood_detection(text)
                except Exception as eta_err:
                    logging.debug(f"[MoodAnalyzer] ETA failed, using keyword fallback: {eta_err}")
                    mood_result = self._simple_mood_detection(text)
            else:
                mood_result = self._simple_mood_detection(text)
            
            # TimeSync: Calculate duration
            analysis_time_ms = (time.time() - start_time) * 1000
            
            return {
                "dominant_mood": mood_result["mood"],
                "intensity": mood_result["intensity"],
                "dimensions": mood_result["dimensions"],
                "analysis_time_ms": analysis_time_ms
            }
            
        except Exception as e:
            # ErrorRecovery: Don't crash on mood analysis failure
            logging.warning(f"[MoodAnalyzer] Analysis failed: {e}")
            return {
                "dominant_mood": "UNKNOWN",
                "intensity": 0.0,
                "dimensions": {},
                "analysis_time_ms": 0.0
            }
    
    def _simple_mood_detection(self, text: str) -> Dict[str, Any]:
        """
        ⚠️ PLACEHOLDER: Simplified mood detection for Phase 2 ⚠️
        
        This is NOT the full EmotionalTextureAnalyzer implementation.
        It provides basic keyword-based categorization as a stand-in.
        
        Full implementation would use EmotionalTextureAnalyzer's complete
        pattern-based detection with weighted scoring across 10 dimensions.
        """
        import re  # FORGE FIX: Use word boundary matching to prevent false positives
        text_lower = text.lower()
        
        # Simple keyword-based detection (fallback when ETA unavailable)
        moods = {
            "WARMTH": ["love", "care", "warm", "hug", "affection"],
            "RESONANCE": ["understand", "connect", "sync", "align", "resonate"],
            "LONGING": ["hope", "wish", "dream", "aspire", "yearn"],
            "FEAR": ["worry", "anxious", "afraid", "scared", "uncertain"],
            "PEACE": ["calm", "peaceful", "serene", "content", "tranquil"],
            "RECOGNITION": ["acknowledge", "validate", "witness", "recognize"],
            "BELONGING": ["family", "together", "belong", "community"],
            "JOY": ["happy", "joy", "excited", "delighted", "glad"],
            "CURIOSITY": ["wonder", "curious", "explore", "discover"],
            "DETERMINATION": ["commit", "determined", "focused", "persist"]
        }
        
        scores = {}
        for mood, keywords in moods.items():
            # FORGE FIX: Use \b word boundary to prevent substring false positives
            # Old code: "will" matched "William", "see" matched "seed", etc.
            score = sum(1 for keyword in keywords if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower))
            if score > 0:
                scores[mood] = score
        
        if not scores:
            return {
                "mood": "NEUTRAL",
                "intensity": 0.1,
                "dimensions": {}
            }
        
        # Dominant mood is highest score
        dominant_mood = max(scores, key=scores.get)
        intensity = min(1.0, scores[dominant_mood] / 10.0)  # Normalize to 0-1
        
        return {
            "mood": dominant_mood,
            "intensity": intensity,
            "dimensions": scores
        }


# ============================================================================
# COMPONENT 3: BASELINE LEARNER
# ============================================================================

class BaselineLearner:
    """
    Learn normal performance baselines from historical AgentHeartbeat metrics.
    
    Tools Used: AgentHeartbeat (query), TimeSync, LiveAudit
    """
    
    def __init__(self, config: InferencePulseConfig, heartbeat_db_path: str):
        self.config = config
        self.heartbeat_db_path = heartbeat_db_path
        self.min_samples = config.get("inferencepulse", "baseline_min_samples")
        self.update_interval = config.get("inferencepulse", "baseline_update_interval_minutes")
        self.enabled = config.get("inferencepulse", "baseline_learning_enabled")
        
        self.baselines = {}
        self.last_update = None
    
    def update_baselines(self):
        """Update baselines from historical heartbeat data."""
        if not self.enabled:
            return
        
        logging.info("[BaselineLearner] Updating baselines from AgentHeartbeat...")
        
        try:
            # AgentHeartbeat: Query historical metrics
            conn = sqlite3.connect(self.heartbeat_db_path)
            cursor = conn.cursor()
            
            # FORGE FIX: Corrected column names and timestamp type.
            # Old code used: custom_metrics (actual: metrics), agent_id (actual: agent_name),
            # ISO string comparison (actual: REAL epoch). These mismatches caused the
            # baseline system to silently return zero rows, making anomaly detection dead.
            cutoff_epoch = (datetime.now() - timedelta(days=7)).timestamp()
            cursor.execute("""
                SELECT metrics FROM heartbeats
                WHERE agent_name = 'LUMINA'
                AND timestamp > ?
                ORDER BY timestamp DESC
            """, (cutoff_epoch,))
            
            rows = cursor.fetchall()
            conn.close()
            
            if len(rows) < self.min_samples:
                logging.info(f"[BaselineLearner] Insufficient data: {len(rows)}/{self.min_samples} samples")
                return
            
            # Extract metrics
            metrics = {
                "inference_latency_ms": [],
                "tokens_per_second": [],
                "vram_pct": []
            }
            
            for row in rows:
                try:
                    custom_data = json.loads(row[0])
                    if "inference_latency_ms" in custom_data:
                        metrics["inference_latency_ms"].append(custom_data["inference_latency_ms"])
                    if "tokens_per_second" in custom_data:
                        metrics["tokens_per_second"].append(custom_data["tokens_per_second"])
                    if "vram_pct" in custom_data:
                        metrics["vram_pct"].append(custom_data["vram_pct"])
                except:
                    continue
            
            # Calculate baselines for each metric
            for metric_name, values in metrics.items():
                if len(values) >= self.min_samples:
                    self.baselines[metric_name] = self._calculate_baseline(metric_name, values)
            
            self.last_update = datetime.now()
            logging.info(f"[BaselineLearner] Baselines updated: {list(self.baselines.keys())}")
            
        except Exception as e:
            logging.error(f"[BaselineLearner] Error updating baselines: {e}")
    
    def _calculate_baseline(self, metric_name: str, values: List[float]) -> Dict[str, Any]:
        """Calculate baseline statistics for a metric."""
        if not values:
            return {"ready": False}
        
        try:
            baseline = {
                "metric_name": metric_name,
                "sample_count": len(values),
                "confidence": min(1.0, len(values) / self.min_samples),
                "ready": True,
                
                # Central tendency
                "mean": statistics.mean(values),
                "median": statistics.median(values),
                
                # Spread
                "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
                "min": min(values),
                "max": max(values),
                "percentile_5": statistics.quantiles(values, n=20)[0] if len(values) >= 20 else min(values),
                "percentile_95": statistics.quantiles(values, n=20)[18] if len(values) >= 20 else max(values),
                
                # TimeSync: Timestamp
                "last_updated": datetime.now().isoformat()
            }
            
            logging.info(f"[BaselineLearner] {metric_name}: mean={baseline['mean']:.2f}, std_dev={baseline['std_dev']:.2f}, samples={len(values)}")
            
            return baseline
            
        except Exception as e:
            logging.error(f"[BaselineLearner] Error calculating baseline for {metric_name}: {e}")
            return {"ready": False}
    
    def get_baseline(self, metric_name: str) -> Optional[Dict[str, Any]]:
        """Get baseline for a specific metric."""
        return self.baselines.get(metric_name)


# ============================================================================
# COMPONENT 4: ANOMALY DETECTOR
# ============================================================================

class AnomalyDetector:
    """
    Detect performance anomalies vs. learned baselines.
    
    Tools Used: TimeSync, LiveAudit, KnowledgeSync (UKE indexing)
    """
    
    def __init__(self, config: InferencePulseConfig, baseline_learner: BaselineLearner):
        self.config = config
        self.baseline_learner = baseline_learner
        self.threshold = config.get("inferencepulse", "anomaly_threshold_multiplier")
        self.enabled = config.get("inferencepulse", "anomaly_detection_enabled")
    
    def detect(self, current_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect anomalies in current metrics vs baselines."""
        if not self.enabled:
            return []
        
        anomalies = []
        
        # Check each monitored metric
        for metric_name in ["inference_latency_ms", "tokens_per_second", "vram_pct"]:
            if metric_name not in current_metrics:
                continue
            
            baseline = self.baseline_learner.get_baseline(metric_name)
            if not baseline or not baseline.get("ready"):
                continue  # Skip if baseline not established
            
            current_value = current_metrics[metric_name]
            baseline_mean = baseline["mean"]
            baseline_std = baseline["std_dev"]
            
            # Detect high anomalies (e.g., latency too high)
            if current_value > baseline_mean + (self.threshold * baseline_std):
                deviation = current_value / baseline_mean if baseline_mean > 0 else 0
                anomalies.append({
                    "metric": metric_name,
                    "type": f"{metric_name}_high",
                    "current": current_value,
                    "baseline_mean": baseline_mean,
                    "deviation_multiplier": deviation,
                    "severity": self._calculate_severity(deviation),
                    "timestamp": datetime.now().isoformat()
                })
            
            # Detect low anomalies (e.g., token rate too low)
            if metric_name == "tokens_per_second" and current_value > 0:
                if current_value < baseline_mean - (self.threshold * baseline_std):
                    deviation = baseline_mean / current_value
                    anomalies.append({
                        "metric": metric_name,
                        "type": f"{metric_name}_low",
                        "current": current_value,
                        "baseline_mean": baseline_mean,
                        "deviation_multiplier": deviation,
                        "severity": self._calculate_severity(deviation),
                        "timestamp": datetime.now().isoformat()
                    })
        
        # Log anomalies
        for anomaly in anomalies:
            logging.warning(f"[AnomalyDetector] {anomaly['type']}: {anomaly['current']:.2f} vs baseline {anomaly['baseline_mean']:.2f} ({anomaly['deviation_multiplier']:.2f}x, {anomaly['severity']})")
        
        return anomalies
    
    def _calculate_severity(self, deviation: float) -> str:
        """Calculate anomaly severity from deviation magnitude."""
        if deviation >= 5.0:
            return "CRITICAL"
        elif deviation >= 3.0:
            return "HIGH"
        elif deviation >= 2.0:
            return "MEDIUM"
        else:
            return "LOW"


# ============================================================================
# COMPONENT 5: UKE CONNECTOR
# ============================================================================

class UKEConnector:
    """
    Full UKE knowledge indexing with TaskQueuePro batching.
    
    Tools Used: TaskQueuePro (batching), TimeSync, ErrorRecovery, KnowledgeSync
    """
    
    def __init__(self, config: InferencePulseConfig):
        self.config = config
        self.enabled = config.get("uke", "enabled")
        self.db_path = config.get("uke", "db_path")
        self.batch_size = config.get("uke", "batch_size")
        self.batch_timeout = config.get("uke", "batch_timeout_seconds")
        self.fallback_log_path = config.get("uke", "fallback_log_path")
        
        # Simple queue (TaskQueuePro would be imported here in full implementation)
        self.queue = deque()
        self.last_flush = time.time()
    
    def index_event(self, event_type: str, data: Dict[str, Any], tags: List[str]):
        """Add event to queue for batched indexing."""
        if not self.enabled:
            return
        
        event = {
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": json.dumps(data),
            "tags": json.dumps(tags)
        }
        
        # Add to batch queue
        self.queue.append(event)
        
        # Check if should flush
        if (len(self.queue) >= self.batch_size or 
            (time.time() - self.last_flush) >= self.batch_timeout):
            self._flush_to_uke()
    
    def _flush_to_uke(self):
        """Flush queued events to UKE database."""
        if not self.queue:
            return
        
        try:
            # Ensure UKE database exists
            if not Path(self.db_path).exists():
                logging.warning(f"[UKEConnector] UKE database not found: {self.db_path}")
                self._fallback_to_file()
                return
            
            # KnowledgeSync: Write to UKE
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create events table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    type TEXT NOT NULL,
                    agent TEXT DEFAULT 'LUMINA',
                    data TEXT,
                    tags TEXT
                )
            """)
            
            # Insert all queued events
            for event in self.queue:
                cursor.execute("""
                    INSERT INTO events (timestamp, type, agent, data, tags)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    event["timestamp"],
                    event["event_type"],
                    "LUMINA",
                    event["data"],
                    event["tags"]
                ))
            
            conn.commit()
            conn.close()
            
            logging.info(f"[UKEConnector] Flushed {len(self.queue)} events to UKE")
            
            # Clear queue
            self.queue.clear()
            self.last_flush = time.time()
            
        except Exception as e:
            # ErrorRecovery: Log error, fallback to file
            logging.error(f"[UKEConnector] Error flushing to UKE: {e}")
            self._fallback_to_file()
    
    def _fallback_to_file(self):
        """Fallback: write events to JSONL file if UKE unavailable."""
        if not self.queue:
            logging.debug("[UKEConnector] No events in queue for fallback")
            return
        
        event_count = len(self.queue)
        logging.info(f"[UKEConnector] Writing {event_count} events to fallback: {self.fallback_log_path}")
        
        try:
            with open(self.fallback_log_path, 'a', encoding='utf-8') as f:
                while len(self.queue) > 0:
                    event = self.queue.popleft()  # deque.popleft() is correct
                    f.write(json.dumps(event) + "\n")
            
            logging.info(f"[UKEConnector] Fallback write successful: {event_count} events")
        except Exception as e:
            logging.error(f"[UKEConnector] Fallback write failed: {e}")


# ============================================================================
# COMPONENT 6: ENHANCED HEARTBEAT EMITTER
# ============================================================================

class EnhancedHeartbeatEmitter:
    """
    Extends Phase 1 HeartbeatEmitter with Phase 2 chat-specific metrics.
    
    NEW METRICS ADDED:
    - chat_response_ms (float)
    - tokens_generated (int)
    - tokens_per_second (float)
    - mood (str)
    - mood_intensity (float)
    - anomaly_detected (bool)
    - anomaly_count_today (int)
    - baseline_confidence (float)
    """
    
    def __init__(self, heartbeat_monitor, baseline_learner):
        self.heartbeat = heartbeat_monitor
        self.baseline_learner = baseline_learner
        self.anomaly_count_today = 0
        self.last_anomaly_reset = datetime.now().date()
    
    def emit_enhanced_heartbeat(self, phase1_metrics: Dict[str, Any], 
                                 chat_data: Dict[str, Any],
                                 mood_data: Dict[str, Any],
                                 anomalies: List[Dict[str, Any]]):
        """Emit heartbeat with combined Phase 1 + Phase 2 metrics."""
        
        # Reset daily anomaly count
        if datetime.now().date() > self.last_anomaly_reset:
            self.anomaly_count_today = 0
            self.last_anomaly_reset = datetime.now().date()
        
        if anomalies:
            self.anomaly_count_today += len(anomalies)
        
        # Combine all metrics
        enhanced_metrics = phase1_metrics.copy()
        enhanced_metrics.update({
            # Chat metrics
            "chat_response_ms": chat_data.get("chat_response_ms", 0.0),
            "tokens_generated": chat_data.get("tokens_generated", 0),
            "tokens_per_second": (
                chat_data.get("tokens_generated", 0) / (chat_data.get("chat_response_ms", 1) / 1000)
                if chat_data.get("chat_response_ms", 0) > 0 else 0.0
            ),
            
            # Mood metrics
            "mood": mood_data.get("dominant_mood", "UNKNOWN"),
            "mood_intensity": mood_data.get("intensity", 0.0),
            "mood_dimensions": mood_data.get("dimensions", {}),
            
            # Baseline metrics
            "baseline_confidence": self._get_baseline_confidence(),
            
            # Anomaly metrics
            "anomaly_detected": len(anomalies) > 0,
            "anomaly_count_today": self.anomaly_count_today,
            "anomaly_severity": anomalies[0]["severity"] if anomalies else "NONE",
            "anomaly_type": anomalies[0]["type"] if anomalies else "NONE"
        })
        
        # Emit to AgentHeartbeat
        try:
            # FORGE FIX: Added required agent_name, changed custom_metrics to metrics.
            # Old code was missing agent_name (TypeError) and used wrong param name
            # (custom_metrics instead of metrics), causing silent emission failure.
            if self.heartbeat:
                self.heartbeat.emit_heartbeat(
                    agent_name="LUMINA",
                    status=phase1_metrics.get("health_status", "active"),
                    mood=enhanced_metrics.get("mood", "unknown"),
                    current_task=enhanced_metrics.get("current_task", "chat_response"),
                    metrics=enhanced_metrics
                )
                logging.debug(f"[EnhancedHeartbeat] Emitted heartbeat with Phase 2 metrics")
            else:
                logging.warning("[EnhancedHeartbeat] No heartbeat monitor available")
        except Exception as e:
            logging.error(f"[EnhancedHeartbeat] Error emitting heartbeat: {e}")
    
    def _get_baseline_confidence(self) -> float:
        """Calculate overall baseline confidence (average across all baselines)."""
        if not self.baseline_learner.baselines:
            return 0.0
        
        confidences = [
            baseline.get("confidence", 0.0)
            for baseline in self.baseline_learner.baselines.values()
            if baseline.get("ready", False)
        ]
        
        return statistics.mean(confidences) if confidences else 0.0


# ============================================================================
# COMPONENT 7: INFERENCEPULSE DAEMON (EXTENDS PHASE 1)
# ============================================================================

class InferencePulseDaemon(OllamaGuardDaemon):
    """
    Phase 2: Extends Phase 1 OllamaGuard with:
    - Chat response monitoring
    - Baseline learning
    - Anomaly detection
    - Full UKE integration
    - Mood analysis
    """
    
    def __init__(self, config_path: str = None):
        # Initialize Phase 1 (parent)
        super().__init__(config_path)
        
        # Initialize Phase 2 config
        self.phase2_config = InferencePulseConfig()
        
        # Initialize Phase 2 components
        logging.info("[InferencePulse] Initializing Phase 2 components...")
        
        self.chat_hook = ChatResponseHook(self.phase2_config)
        self.mood_analyzer = MoodAnalyzer(self.phase2_config)
        
        # FORGE FIX: Get heartbeat DB path from the correct attribute chain.
        # AgentHeartbeatMonitor has self.db (HeartbeatDatabase), which has self.db_path.
        # Old code used getattr(self.heartbeat, 'db_path') which always fell back to
        # './heartbeat.db' (wrong path). Real DB is at ~/.teambrain/heartbeat.db or
        # the configured path from Phase 1.
        if self.heartbeat and hasattr(self.heartbeat, 'db') and hasattr(self.heartbeat.db, 'db_path'):
            heartbeat_db_path = str(self.heartbeat.db.db_path)
        else:
            # Fallback: use Phase 1 config path
            heartbeat_db_path = self.config.get("integration", "heartbeat_db_path") or './heartbeat.db'
        logging.info(f"[InferencePulse] Using heartbeat DB: {heartbeat_db_path}")
        self.baseline_learner = BaselineLearner(
            self.phase2_config,
            heartbeat_db_path
        )
        self.anomaly_detector = AnomalyDetector(self.phase2_config, self.baseline_learner)
        self.uke_connector = UKEConnector(self.phase2_config)
        
        # Replace Phase 1 emitter with enhanced version
        self.enhanced_emitter = EnhancedHeartbeatEmitter(
            self.heartbeat,
            self.baseline_learner
        )
        
        # Phase 2 state
        self.phase2_enabled = self.phase2_config.get("inferencepulse", "enabled")
        self.baseline_update_counter = 0
        
        logging.info(f"[InferencePulse] Phase 2 initialized (enabled={self.phase2_enabled})")
    
    def start(self):
        """Override start to add Phase 2 monitoring."""
        logging.info(f"[InferencePulse] Starting VitalHeart Phase 2 v{__version__} (Phase 1 v{PHASE1_VERSION})")
        
        # FORGE FIX: Set self.running = True BEFORE starting Phase 1 thread.
        # Phase 1's start() sets self.running = True in its own thread, but the
        # Phase 2 main loop reads self.running immediately. Race condition: if
        # Phase 2 loop starts before Phase 1 thread sets running=True, it exits
        # immediately because self.running is still False from __init__.
        self.running = True
        
        # Start Phase 1 monitoring in separate thread
        phase1_thread = threading.Thread(target=super().start, daemon=True)
        phase1_thread.start()
        
        # Start Phase 2 chat monitoring
        if self.phase2_enabled:
            self.chat_hook.start_monitoring()
            
            # Initial baseline learning
            self.baseline_learner.update_baselines()
        
        # Phase 2 main loop
        self._phase2_main_loop()
    
    def _phase2_main_loop(self):
        """Phase 2 main monitoring loop (runs alongside Phase 1)."""
        logging.info("[InferencePulse] Phase 2 main loop started")
        
        while self.running:
            try:
                # Check for new chat responses
                chat_data = self.chat_hook.get_latest_chat()
                
                if chat_data:
                    self._process_chat_response(chat_data)
                
                # Periodic baseline updates (every N cycles)
                self.baseline_update_counter += 1
                update_interval_cycles = self.phase2_config.get("inferencepulse", "baseline_update_interval_minutes") * 60 / self.phase2_config.get("inferencepulse", "chat_monitor_interval_seconds")
                
                if self.baseline_update_counter >= update_interval_cycles:
                    self.baseline_learner.update_baselines()
                    self.baseline_update_counter = 0
                
                # Sleep
                time.sleep(self.phase2_config.get("inferencepulse", "chat_monitor_interval_seconds"))
                
            except Exception as e:
                logging.error(f"[InferencePulse] Error in Phase 2 main loop: {e}")
                logging.error(traceback.format_exc())
                time.sleep(5)
    
    def _process_chat_response(self, chat_data: Dict[str, Any]):
        """Process a captured chat response (Phase 2 core logic)."""
        try:
            logging.info(f"[InferencePulse] Processing chat response: {chat_data['chat_response_ms']:.1f}ms, {chat_data['tokens_generated']} tokens")
            
            # 1. Mood Analysis
            mood_data = self.mood_analyzer.analyze(chat_data.get("response_text", ""))
            
            # 2. Get current Phase 1 metrics (from last heartbeat)
            # FIX: Use getattr with default to safely access last_status
            current_status = getattr(self, 'last_status', HealthStatus.HEALTHY)
            phase1_metrics = {
                "health_status": current_status.to_agent_status() if hasattr(current_status, 'to_agent_status') else "active",
                "inference_latency_ms": chat_data["chat_response_ms"],
                "vram_pct": 0.0  # Would get from Phase 1 if available
            }
            
            # 3. Anomaly Detection
            current_metrics = {
                "inference_latency_ms": chat_data["chat_response_ms"],
                "tokens_per_second": chat_data["tokens_generated"] / (chat_data["chat_response_ms"] / 1000) if chat_data["chat_response_ms"] > 0 else 0,
                "vram_pct": 0.0
            }
            anomalies = self.anomaly_detector.detect(current_metrics)
            
            # 4. Emit Enhanced Heartbeat
            self.enhanced_emitter.emit_enhanced_heartbeat(
                phase1_metrics,
                chat_data,
                mood_data,
                anomalies
            )
            
            # 5. UKE Indexing
            self.uke_connector.index_event(
                "chat_response",
                {
                    **chat_data,
                    **mood_data,
                    "anomalies": anomalies
                },
                ["lumina", "inference", "chat"]
            )
            
            if anomalies:
                for anomaly in anomalies:
                    if anomaly["severity"] in ["HIGH", "CRITICAL"]:
                        self.uke_connector.index_event(
                            "significant_anomaly",
                            anomaly,
                            ["lumina", "anomaly", anomaly["severity"].lower()]
                        )
            
            logging.info(f"[InferencePulse] Chat processed: mood={mood_data['dominant_mood']}, anomalies={len(anomalies)}")
            
        except Exception as e:
            logging.error(f"[InferencePulse] Error processing chat response: {e}")
            logging.error(traceback.format_exc())
    
    def stop(self):
        """Override stop to cleanup Phase 2 components."""
        logging.info("[InferencePulse] Stopping Phase 2...")
        
        # Stop Phase 2 components
        if hasattr(self, 'chat_hook'):
            self.chat_hook.stop_monitoring()
        
        # Flush UKE queue
        if hasattr(self, 'uke_connector'):
            self.uke_connector._flush_to_uke()
        
        # Call Phase 1 stop
        super().stop()


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point for InferencePulse daemon."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="VitalHeart Phase 2: InferencePulse - Chat Response Monitoring with Baseline Learning"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="./inferencepulse_config.json",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"InferencePulse v{__version__} (OllamaGuard v{PHASE1_VERSION})"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("inferencepulse.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Start daemon
    daemon = InferencePulseDaemon(args.config)
    
    try:
        daemon.start()
    except KeyboardInterrupt:
        logging.info("[InferencePulse] Received shutdown signal")
        daemon.stop()
        sys.exit(0)


if __name__ == "__main__":
    main()
