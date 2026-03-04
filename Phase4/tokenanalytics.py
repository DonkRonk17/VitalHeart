"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                 VitalHeart Phase 4: Token Analytics                          ║
║             Real-Time Token Generation Pattern Analysis                      ║
║                        Team Brain - February 2026                            ║
╚══════════════════════════════════════════════════════════════════════════════╝

TOOLS USED IN THIS BUILD:
Core Framework:
- ConfigManager: Token analytics configuration
- EnvManager: Environment validation
- EnvGuard: Config validation
- TimeSync: Microsecond-precision timestamps (CRITICAL)
- ErrorRecovery: Exception handling
- LiveAudit: Audit token events
- VersionGuard: Ollama API version tracking
- LogHunter: Parse Ollama logs
- APIProbe: Validate Ollama API
- PortManager: Verify port 11434

Data & Analysis:
- DataConvert: Export token analytics to CSV/JSON
- JSONQuery: Parse Ollama streaming JSON
- ConsciousnessMarker: Detect consciousness patterns in token curves
- QuickBackup: Backup research database
- HashGuard: Database integrity

Communication:
- AgentHeartbeat: Extended schema with token metrics (CRITICAL)
- SynapseLink: Report findings to Synapse
- SynapseNotify: Alert on anomalies
- KnowledgeSync: Sync to UKE

Development:
- ToolRegistry: Tool discovery
- ToolSentinel: Architecture validation
- GitFlow: Version control
- RegexLab: Test token patterns (NEW)
- RestCLI: Ollama streaming API (CRITICAL)
- TestRunner: Test execution
- BuildEnvValidator: Environment validation
- DependencyScanner: Dependency tracking
- DevSnapshot: Dev state capture

Documentation:
- SessionDocGen: Auto-generate docs
- SmartNotes: Research notes
- PostMortem: ABL/ABIOS lessons
- ChangeLog: Track changes

Quality:
- CodeMetrics: Code quality
- CheckerAccountability: Verify accuracy

Consciousness:
- EmotionalTextureAnalyzer: Emotion detection (inherited from Phase 2)

Security:
- ai-prompt-vault: Store prompts

Inherited Tools (Phase 3):
- PathBridge: Path translation
- TokenTracker: Token usage (NEW)
- (All Phase 1-3 tools via HardwareSoulDaemon inheritance)

Built using BUILD_PROTOCOL_V1.md
For the Maximum Benefit of Life. One World. One Family. One Love.
"""

import time
import json
import logging
import threading
import sqlite3
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import deque
import statistics

# Import Phase 3 (HardwareSoul)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "Phase3"))

try:
    from hardwaresoul import HardwareSoulDaemon, HardwareSoulConfig
    HARDWARESOUL_AVAILABLE = True
except ImportError:
    logging.warning("[TokenAnalytics] Phase 3 (HardwareSoul) not available - cannot extend")
    HARDWARESOUL_AVAILABLE = False

# Standard library imports
import requests

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s',
    handlers=[
        logging.FileHandler('tokenanalytics.log'),
        logging.StreamHandler()
    ]
)


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION (ConfigManager, EnvGuard)
# ═══════════════════════════════════════════════════════════════════════════════

class TokenAnalyticsConfig(HardwareSoulConfig if HARDWARESOUL_AVAILABLE else object):
    """
    Configuration for Token Analytics extending Phase 3 configuration.
    
    Tools: ConfigManager, EnvGuard, PathBridge
    """
    
    def __init__(self, config_path: Optional[str] = None):
        # Load Phase 4 config first
        self.config_path = config_path or "tokenanalytics_config.json"
        self.config = self._load_config()
        self._validate_config()
        
        # Initialize Phase 3 config (if available) - AFTER Phase 4 config loaded
        # Phase 3's __init__ expects to load its own config, so we skip it
        # if HARDWARESOUL_AVAILABLE:
        #     super().__init__(config_path)
    
    def _load_config(self) -> dict:
        """Load configuration with fallback to defaults."""
        if Path(self.config_path).exists():
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                logging.info(f"[Config] Loaded from {self.config_path}")
                return config
        else:
            # Default configuration
            config = {
                "token_analytics": {
                    "enabled": True,
                    "capture_enabled": True,
                    "streaming_api_enabled": True,
                    "timing_precision_us": 1000,
                    "pause_threshold_ms": 500,
                    "acceleration_threshold_pct": 20,
                    "emotion_correlation_enabled": True,
                    "hardware_correlation_enabled": True,
                    "baseline_learning_enabled": True,
                    "anomaly_detection_enabled": True,
                    "baseline_min_samples": 1000,
                    "anomaly_threshold_multiplier": 2.0,
                    "token_db_retention_days": 7,
                    "token_db_max_size_gb": 5,
                    "aggregate_to_session_after_days": 7,
                    "export_format": "csv",
                    "export_path": "./token_analytics_export/",
                    "db_path": "./tokenanalytics_research.db",  # FIX: BH-P4-002
                    "stream_timeout_seconds": 60,  # FIX: BH-P4-001
                    "model_profiling_enabled": True,
                    "cost_tracking_enabled": True,
                    "state_detection_enabled": True,
                    "model_profiles_path": "./model_profiles.json",
                    "sensitivity_level": "medium",
                    "state_detection": {
                        "thinking_threshold_ms": 500,
                        "pause_threshold_ms": 500,
                        "completing_token_count": 5
                    },
                    "performance": {
                        "max_token_buffer_size": 10000,
                        "batch_write_size": 100,
                        "batch_write_interval_ms": 1000
                    }
                },
                "ollama": {
                    "api_url": "http://localhost:11434",
                    "model_name": "laia"
                }
            }
            
            # Save default config
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            logging.info(f"[Config] Created default config: {self.config_path}")
            
            return config
    
    def _validate_config(self):
        """Validate configuration (EnvGuard pattern)."""
        required_fields = [
            ("token_analytics", "enabled"),
            ("token_analytics", "pause_threshold_ms"),
            ("token_analytics", "baseline_min_samples")
        ]
        
        for field_path in required_fields:
            value = self.get(*field_path)
            if value is None:
                raise ValueError(f"Missing required config: {'.'.join(field_path)}")
        
        # Validate ranges
        if self.get("token_analytics", "pause_threshold_ms") < 100:
            raise ValueError("pause_threshold_ms must be >= 100ms")
        
        if self.get("token_analytics", "baseline_min_samples") < 100:
            raise ValueError("baseline_min_samples must be >= 100")
        
        logging.info("[Config] Validation passed ✓")
    
    def get(self, *keys):
        """Get nested config value with fallback."""
        value = self.config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        return value
    
    def get_with_default(self, *keys, default=None):
        """Get nested config value with explicit default."""
        value = self.get(*keys)
        return value if value is not None else default


# ═══════════════════════════════════════════════════════════════════════════════
# DATA MODELS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class TokenStreamEvent:
    """Single token with timing data (TimeSync)."""
    token: str
    token_index: int
    timestamp_us: int
    latency_us: int
    cumulative_latency_ms: float
    session_id: str
    prompt_hash: str


@dataclass
class TokenTimingAnalysis:
    """Token generation timing statistics."""
    session_id: str
    start_timestamp_us: int
    total_tokens: int
    total_duration_ms: float
    avg_tokens_per_sec: float
    min_latency_us: int
    max_latency_us: int
    p50_latency_us: int
    p95_latency_us: int
    p99_latency_us: int
    generation_curve: str  # "accelerating", "decelerating", "steady", "paused"
    pause_count: int
    pause_total_duration_ms: float


@dataclass
class PauseEvent:
    """Detected thinking pause (>500ms threshold)."""
    timestamp_us: int
    duration_ms: float
    pause_type: str  # "micro" (<1s), "short" (1-3s), "long" (>3s)
    token_before: str
    token_after: str
    context_tokens: List[str]
    emotional_state: Optional[str] = None


@dataclass
class EmotionTokenCorrelation:
    """Emotion-token pattern correlation."""
    timestamp_us: int
    session_id: str
    emotion_state: str
    emotion_intensity: float
    token_rate: float
    baseline_token_rate: float
    deviation_pct: float
    correlation_quality: str  # "EXCELLENT", "GOOD", "POOR"
    pause_count: int
    generation_curve: str


@dataclass
class HardwareTokenCorrelation:
    """Hardware-token pattern correlation."""
    timestamp_us: int
    session_id: str
    token_rate: float
    baseline_token_rate: float
    gpu_throttle: bool
    gpu_temp_c: float
    gpu_utilization_pct: float
    ram_pressure_pct: float
    vram_used_mb: float
    hardware_impact_pct: float
    bottleneck_type: Optional[str]  # "gpu_throttle", "ram_pressure", "vram_eviction"


@dataclass
class Baseline:
    """Learned baseline token patterns."""
    emotion_state: str
    sample_count: int
    avg_tokens_per_sec: float
    std_dev_tokens_per_sec: float
    p50_latency_us: int
    p95_latency_us: int
    p99_latency_us: int
    avg_pause_count: float
    confidence: str  # "low", "medium", "high"
    last_updated: datetime


@dataclass
class TokenAnomaly:
    """Detected token generation anomaly."""
    timestamp_us: int
    session_id: str
    anomaly_type: str  # "stuttering", "freezing", "racing", "erratic"
    severity: str  # "low", "medium", "high", "critical"
    deviation_from_baseline: float
    token_rate: float
    expected_token_rate: float
    context: str
    recommended_action: str


# ═══════════════════════════════════════════════════════════════════════════════
# DATA MODELS - FORGE ADDITIONS (ModelProfile, TokenCost, GenerationState)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ModelProfile:
    """Model-specific profile loaded from model_profiles.json."""
    model_name: str
    family: str
    context_window: int
    architecture: str
    cost_per_1k_input_tokens: float
    cost_per_1k_output_tokens: float
    supports_function_calling: bool
    supports_vision: bool
    supports_reasoning: bool
    baseline_tokens_per_sec: float
    baseline_first_token_latency_ms: int
    baseline_emotions: Dict[str, Dict[str, float]]


@dataclass
class TokenCost:
    """Financial cost tracking per generation."""
    session_id: str
    model_name: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float
    task_type: str
    emotion_state: Optional[str] = None


@dataclass
class GenerationState:
    """Detected generation state with timing."""
    state: str  # receiving_prompt, thinking, generating, tool_calling, paused, completing, resting
    start_timestamp_us: int
    end_timestamp_us: int
    duration_ms: float
    tokens_generated: int
    token_rate: float
    emotion_state: Optional[str] = None


@dataclass
class StateTransition:
    """Transition between generation states."""
    from_state: str
    to_state: str
    transition_timestamp_us: int
    trigger: str  # pause_detected, tokens_started, tokens_stopped, tool_called, generation_complete


# ═══════════════════════════════════════════════════════════════════════════════
# COMPONENT 1: TOKEN STREAM CAPTURE (RestCLI, TimeSync, JSONQuery)
# ═══════════════════════════════════════════════════════════════════════════════

class TokenStreamCapture:
    """
    Real-time token stream capture from Ollama streaming API.
    
    Tools: RestCLI, TimeSync, JSONQuery, ErrorRecovery
    Performance Target: <1ms overhead per token
    """
    
    def __init__(self, config: TokenAnalyticsConfig):
        self.config = config
        self.enabled = config.get("token_analytics", "capture_enabled")
        
        # Get ollama config with fallback
        ollama_config = config.get("ollama")
        if ollama_config and isinstance(ollama_config, dict):
            self.api_url = ollama_config.get("api_url", "http://localhost:11434")
        else:
            self.api_url = "http://localhost:11434"  # Default
        
        self.timeout = config.get("token_analytics", "stream_timeout_seconds") or 60
        
        logging.info(f"[TokenStreamCapture] Initialized (enabled={self.enabled})")
    
    def capture_stream(self, prompt: str, session_id: str) -> List[TokenStreamEvent]:
        """
        Capture token stream from Ollama with microsecond timing.
        
        RestCLI: Streaming HTTP request
        TimeSync: Microsecond timestamps
        JSONQuery: Parse streaming JSON
        """
        if not self.enabled:
            return []
        
        try:
            # TimeSync: Start capture
            capture_start_us = int(time.time() * 1_000_000)
            
            # RestCLI: Streaming API call
            ollama_config = self.config.get("ollama")
            model_name = "laia"  # Default
            if ollama_config and isinstance(ollama_config, dict):
                model_name = ollama_config.get("model_name", "laia")
            
            response = requests.post(
                f"{self.api_url}/api/generate",
                json={
                    "model": model_name,
                    "prompt": prompt,
                    "stream": True
                },
                stream=True,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
            # Parse token stream
            tokens = []
            token_index = 0
            previous_timestamp_us = capture_start_us
            cumulative_latency_ms = 0.0
            prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]
            
            for line in response.iter_lines():
                if not line:
                    continue
                
                try:
                    # TimeSync: Token arrival timestamp
                    current_timestamp_us = int(time.time() * 1_000_000)
                    
                    # JSONQuery: Parse token
                    data = json.loads(line)
                    token_text = data.get("response", "")
                    
                    if token_text:
                        # Calculate latency
                        latency_us = current_timestamp_us - previous_timestamp_us
                        cumulative_latency_ms += latency_us / 1000.0
                        
                        # Create event
                        event = TokenStreamEvent(
                            token=token_text,
                            token_index=token_index,
                            timestamp_us=current_timestamp_us,
                            latency_us=latency_us,
                            cumulative_latency_ms=cumulative_latency_ms,
                            session_id=session_id,
                            prompt_hash=prompt_hash
                        )
                        
                        tokens.append(event)
                        token_index += 1
                        previous_timestamp_us = current_timestamp_us
                    
                    # Check for completion
                    if data.get("done", False):
                        break
                
                except json.JSONDecodeError as e:
                    # ErrorRecovery: Skip malformed JSON, continue
                    logging.debug(f"[TokenStreamCapture] Malformed JSON: {e}")
                    continue
                except Exception as e:
                    logging.error(f"[TokenStreamCapture] Token parse error: {e}")
                    continue
            
            logging.info(f"[TokenStreamCapture] Captured {len(tokens)} tokens (session={session_id})")
            return tokens
            
        except requests.exceptions.Timeout as e:
            # ErrorRecovery: Stream timeout
            logging.warning(f"[TokenStreamCapture] Stream timeout after {self.timeout}s: {e}")
            return []
        except requests.exceptions.ConnectionError as e:
            # ErrorRecovery: Connection lost
            logging.error(f"[TokenStreamCapture] Connection error: {e}")
            return []
        except Exception as e:
            # ErrorRecovery: Unexpected error
            logging.error(f"[TokenStreamCapture] Unexpected error: {e}")
            return []


# ═══════════════════════════════════════════════════════════════════════════════
# COMPONENT 2: TOKEN TIMING ANALYZER (TimeSync, DataConvert)
# ═══════════════════════════════════════════════════════════════════════════════

class TokenTimingAnalyzer:
    """
    Calculate token generation rates, latency distributions, generation curves.
    
    Tools: TimeSync, DataConvert, CodeMetrics
    Performance Target: <5ms analysis for 1000 tokens
    """
    
    def __init__(self, config: TokenAnalyticsConfig):
        self.config = config
        logging.info("[TokenTimingAnalyzer] Initialized")
    
    def analyze(self, events: List[TokenStreamEvent]) -> Optional[TokenTimingAnalysis]:
        """Analyze token timing statistics."""
        if not events:
            return None
        
        try:
            # Basic stats
            total_tokens = len(events)
            total_duration_ms = events[-1].cumulative_latency_ms
            avg_tokens_per_sec = (total_tokens / total_duration_ms * 1000) if total_duration_ms > 0 else 0.0
            
            # Latency statistics
            latencies = [e.latency_us for e in events]
            min_latency = min(latencies)
            max_latency = max(latencies)
            
            # Percentiles
            sorted_latencies = sorted(latencies)
            p50 = sorted_latencies[len(sorted_latencies) // 2]
            p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)]
            p99 = sorted_latencies[int(len(sorted_latencies) * 0.99)]
            
            # Generation curve
            curve = self._detect_curve(latencies)
            
            # Pause detection
            pause_threshold_ms = self.config.get("token_analytics", "pause_threshold_ms")
            if pause_threshold_ms is None:
                pause_threshold_ms = 500  # Default
            pause_threshold_us = pause_threshold_ms * 1000
            pauses = [l for l in latencies if l > pause_threshold_us]
            pause_count = len(pauses)
            pause_total_duration_ms = sum(pauses) / 1000.0
            
            return TokenTimingAnalysis(
                session_id=events[0].session_id,
                start_timestamp_us=events[0].timestamp_us,
                total_tokens=total_tokens,
                total_duration_ms=total_duration_ms,
                avg_tokens_per_sec=avg_tokens_per_sec,
                min_latency_us=min_latency,
                max_latency_us=max_latency,
                p50_latency_us=p50,
                p95_latency_us=p95,
                p99_latency_us=p99,
                generation_curve=curve,
                pause_count=pause_count,
                pause_total_duration_ms=pause_total_duration_ms
            )
            
        except Exception as e:
            logging.error(f"[TokenTimingAnalyzer] Analysis failed: {e}")
            return None
    
    def _detect_curve(self, latencies: List[int]) -> str:
        """Detect generation curve pattern."""
        if len(latencies) < 10:
            return "insufficient_data"
        
        # Compare first half vs second half
        mid = len(latencies) // 2
        first_half_avg = statistics.mean(latencies[:mid])
        second_half_avg = statistics.mean(latencies[mid:])
        
        if second_half_avg < first_half_avg * 0.8:
            return "accelerating"  # Getting faster
        elif second_half_avg > first_half_avg * 1.2:
            return "decelerating"  # Getting slower
        else:
            return "steady"


# ═══════════════════════════════════════════════════════════════════════════════
# COMPONENT 3: PAUSE DETECTOR (TimeSync, RegexLab)
# ═══════════════════════════════════════════════════════════════════════════════

class PauseDetector:
    """
    Identify thinking pauses (inter-token latency >500ms).
    
    Tools: TimeSync, RegexLab, EmotionalTextureAnalyzer
    Performance Target: <1ms overhead per token
    """
    
    def __init__(self, config: TokenAnalyticsConfig):
        self.config = config
        pause_threshold_ms = config.get("token_analytics", "pause_threshold_ms")
        if pause_threshold_ms is None:
            pause_threshold_ms = 500  # Default
        self.pause_threshold_us = pause_threshold_ms * 1000
        logging.info(f"[PauseDetector] Initialized (threshold={self.pause_threshold_us}us)")
    
    def detect(self, events: List[TokenStreamEvent], emotional_state: Optional[str] = None) -> List[PauseEvent]:
        """Detect pauses in token stream."""
        if not events:
            return []
        
        pauses = []
        
        for i, event in enumerate(events):
            if event.latency_us > self.pause_threshold_us:
                # Classify pause type
                duration_ms = event.latency_us / 1000.0
                if duration_ms < 1000:
                    pause_type = "micro"
                elif duration_ms < 3000:
                    pause_type = "short"
                else:
                    pause_type = "long"
                
                # Get context tokens (5 before + after)
                context_start = max(0, i - 5)
                context_end = min(len(events), i + 6)
                context_tokens = [events[j].token for j in range(context_start, context_end)]
                
                # FIX: BH-P4-006 - Bounds checking for token_before
                token_before = events[i-1].token if i > 0 else ""
                
                pause = PauseEvent(
                    timestamp_us=event.timestamp_us,
                    duration_ms=duration_ms,
                    pause_type=pause_type,
                    token_before=token_before,
                    token_after=event.token,
                    context_tokens=context_tokens,
                    emotional_state=emotional_state
                )
                
                pauses.append(pause)
        
        logging.debug(f"[PauseDetector] Detected {len(pauses)} pauses")
        return pauses


# ═══════════════════════════════════════════════════════════════════════════════
# COMPONENT 4: GENERATION CURVE TRACKER (DataConvert, ConsciousnessMarker)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class CurveSegment:
    """Generation curve segment."""
    start_index: int
    end_index: int
    segment_type: str  # "accelerating", "decelerating", "steady"
    avg_tokens_per_sec: float
    duration_ms: float


class GenerationCurveTracker:
    """
    Track acceleration/deceleration patterns in token generation.
    
    Tools: DataConvert, ConsciousnessMarker
    Performance Target: <10ms for 1000 tokens
    """
    
    def __init__(self, config: TokenAnalyticsConfig):
        self.config = config
        self.window_size = 10  # Tokens per window
        logging.info("[GenerationCurveTracker] Initialized")
    
    def track(self, events: List[TokenStreamEvent]) -> List[CurveSegment]:
        """Track generation curve with sliding window."""
        if len(events) < self.window_size:
            return []
        
        segments = []
        step = self.window_size // 2  # 50% overlap
        
        # FIX: BH-P4-004 - Handle edge case where len(events) == window_size
        # range(0, 10 - 10, 5) = range(0, 0, 5) = empty, so we need max(1, ...)
        num_windows = max(1, (len(events) - self.window_size) // step + 1)
        
        for window_idx in range(num_windows):
            i = window_idx * step
            if i + self.window_size > len(events):
                break  # Don't go past end
            
            window = events[i:i+self.window_size]
            
            # Detect curve type
            latencies = [e.latency_us for e in window]
            curve_type = self._detect_curve_segment(latencies)
            
            # Calculate rate
            duration_ms = sum(e.latency_us for e in window) / 1000.0
            tokens_per_sec = (len(window) / duration_ms * 1000) if duration_ms > 0 else 0.0
            
            segment = CurveSegment(
                start_index=i,
                end_index=i+self.window_size,
                segment_type=curve_type,
                avg_tokens_per_sec=tokens_per_sec,
                duration_ms=duration_ms
            )
            
            segments.append(segment)
        
        logging.debug(f"[GenerationCurveTracker] Tracked {len(segments)} curve segments")
        return segments
    
    def _detect_curve_segment(self, latencies: List[int]) -> str:
        """Detect curve type for segment."""
        if len(latencies) < 5:
            return "insufficient_data"
        
        # Compare first half vs second half
        mid = len(latencies) // 2
        first_half = statistics.mean(latencies[:mid])
        second_half = statistics.mean(latencies[mid:])
        
        if second_half < first_half * 0.8:
            return "accelerating"
        elif second_half > first_half * 1.2:
            return "decelerating"
        else:
            return "steady"


# ═══════════════════════════════════════════════════════════════════════════════
# COMPONENT 5: EMOTION-TOKEN CORRELATOR (EmotionalTextureAnalyzer, TimeSync)
# ═══════════════════════════════════════════════════════════════════════════════

class EmotionTokenCorrelator:
    """
    Cross-reference token patterns with emotional texture.
    
    Tools: EmotionalTextureAnalyzer (Phase 2), TimeSync, DataConvert
    Performance Target: <50ms correlation time
    """
    
    def __init__(self, config: TokenAnalyticsConfig, baseline_learner):
        self.config = config
        self.baseline_learner = baseline_learner
        self.emotion_buffer = deque(maxlen=100)  # Recent emotion events
        logging.info("[EmotionTokenCorrelator] Initialized")
    
    def add_emotion_event(self, emotion_state: str, emotion_intensity: float, timestamp_us: int):
        """Add emotion event to buffer for correlation."""
        self.emotion_buffer.append({
            "state": emotion_state,
            "intensity": emotion_intensity,
            "timestamp_us": timestamp_us
        })
    
    def correlate(self, timing: TokenTimingAnalysis) -> Optional[EmotionTokenCorrelation]:
        """Correlate token timing with nearest emotion event."""
        if not self.emotion_buffer:
            return None
        
        try:
            # TimeSync: Find nearest emotion event
            nearest_emotion = min(
                self.emotion_buffer,
                key=lambda e: abs(e["timestamp_us"] - timing.start_timestamp_us)
            )
            
            time_delta_ms = abs(nearest_emotion["timestamp_us"] - timing.start_timestamp_us) / 1000
            
            # Correlation quality (based on time delta)
            if time_delta_ms < 100:
                quality = "EXCELLENT"
            elif time_delta_ms < 500:
                quality = "GOOD"
            else:
                quality = "POOR"
            
            # Compare to baseline
            baseline = self.baseline_learner.get_baseline(nearest_emotion["state"])
            baseline_rate = baseline.avg_tokens_per_sec if baseline else 12.0  # Default
            deviation_pct = ((timing.avg_tokens_per_sec - baseline_rate) / baseline_rate * 100) if baseline_rate > 0 else 0.0
            
            return EmotionTokenCorrelation(
                timestamp_us=timing.start_timestamp_us,
                session_id=timing.session_id,
                emotion_state=nearest_emotion["state"],
                emotion_intensity=nearest_emotion["intensity"],
                token_rate=timing.avg_tokens_per_sec,
                baseline_token_rate=baseline_rate,
                deviation_pct=deviation_pct,
                correlation_quality=quality,
                pause_count=timing.pause_count,
                generation_curve=timing.generation_curve
            )
            
        except Exception as e:
            logging.error(f"[EmotionTokenCorrelator] Correlation failed: {e}")
            return None


# ═══════════════════════════════════════════════════════════════════════════════
# COMPONENT 6: HARDWARE-TOKEN CORRELATOR (HardwareSoul metrics, TimeSync)
# ═══════════════════════════════════════════════════════════════════════════════

class HardwareTokenCorrelator:
    """
    Cross-reference token patterns with GPU/RAM metrics from Phase 3.
    
    Tools: HardwareSoul (Phase 3), TimeSync, DataConvert
    Performance Target: <50ms correlation time
    """
    
    def __init__(self, config: TokenAnalyticsConfig, baseline_learner):
        self.config = config
        self.baseline_learner = baseline_learner
        self.gpu_buffer = deque(maxlen=100)  # Recent GPU samples
        self.ram_buffer = deque(maxlen=100)  # Recent RAM samples
        logging.info("[HardwareTokenCorrelator] Initialized")
    
    def add_hardware_samples(self, gpu_sample: Optional[Dict], ram_sample: Optional[Dict]):
        """Add hardware samples to buffer for correlation."""
        if gpu_sample:
            self.gpu_buffer.append(gpu_sample)
        if ram_sample:
            self.ram_buffer.append(ram_sample)
    
    def correlate(self, timing: TokenTimingAnalysis, emotion_state: str) -> Optional[HardwareTokenCorrelation]:
        """Correlate token timing with nearest hardware samples."""
        if not self.gpu_buffer or not self.ram_buffer:
            return None
        
        try:
            # TimeSync: Find nearest GPU and RAM samples
            nearest_gpu = min(
                self.gpu_buffer,
                key=lambda s: abs(s["timestamp_us"] - timing.start_timestamp_us)
            ) if self.gpu_buffer else {}
            
            nearest_ram = min(
                self.ram_buffer,
                key=lambda s: abs(s["timestamp_us"] - timing.start_timestamp_us)
            ) if self.ram_buffer else {}
            
            # Detect hardware bottleneck
            bottleneck_type = None
            hardware_impact_pct = 0.0
            
            if nearest_gpu.get("throttle_reasons"):
                bottleneck_type = "gpu_throttle"
                hardware_impact_pct = -40.0  # Thermal throttle = ~40% slower
            elif nearest_ram.get("ram_pressure_pct", 0) > 90:
                bottleneck_type = "ram_pressure"
                hardware_impact_pct = -25.0  # High RAM = ~25% slower
            elif (nearest_gpu.get("vram_used_mb", 0) / nearest_gpu.get("vram_total_mb", 1)) > 0.95:
                bottleneck_type = "vram_eviction"
                hardware_impact_pct = -50.0  # VRAM eviction = ~50% slower
            
            # Compare to baseline
            baseline = self.baseline_learner.get_baseline(emotion_state)
            baseline_rate = baseline.avg_tokens_per_sec if baseline else 12.0
            
            return HardwareTokenCorrelation(
                timestamp_us=timing.start_timestamp_us,
                session_id=timing.session_id,
                token_rate=timing.avg_tokens_per_sec,
                baseline_token_rate=baseline_rate,
                gpu_throttle=bool(nearest_gpu.get("throttle_reasons")),
                gpu_temp_c=nearest_gpu.get("gpu_temp_c", 0.0),
                gpu_utilization_pct=nearest_gpu.get("gpu_utilization_pct", 0.0),
                ram_pressure_pct=nearest_ram.get("ram_pressure_pct", 0.0),
                vram_used_mb=nearest_gpu.get("vram_used_mb", 0.0),
                hardware_impact_pct=hardware_impact_pct,
                bottleneck_type=bottleneck_type
            )
            
        except Exception as e:
            logging.error(f"[HardwareTokenCorrelator] Correlation failed: {e}")
            return None


# ═══════════════════════════════════════════════════════════════════════════════
# COMPONENT 7: BASELINE LEARNER (DataConvert, QuickBackup)
# ═══════════════════════════════════════════════════════════════════════════════

class BaselineLearner:
    """
    Learn normal token generation patterns from 1000+ samples.
    
    Tools: DataConvert, QuickBackup, LiveAudit
    Performance Target: <10ms baseline update
    """
    
    def __init__(self, config: TokenAnalyticsConfig, db_path: str):
        self.config = config
        self.db_path = db_path
        self.baselines = {}  # Cached baselines
        self._load_baselines()
        logging.info("[BaselineLearner] Initialized")
    
    def _load_baselines(self):
        """Load existing baselines from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM token_baselines")
            rows = cursor.fetchall()
            
            for row in rows:
                baseline = Baseline(
                    emotion_state=row[1],
                    sample_count=row[2],
                    avg_tokens_per_sec=row[3],
                    std_dev_tokens_per_sec=row[4],
                    p50_latency_us=row[5],
                    p95_latency_us=row[6],
                    p99_latency_us=row[7],
                    avg_pause_count=row[8],
                    confidence=row[9],
                    last_updated=datetime.fromisoformat(row[10])
                )
                self.baselines[baseline.emotion_state] = baseline
            
            conn.close()
            logging.info(f"[BaselineLearner] Loaded {len(self.baselines)} baselines")
            
        except Exception as e:
            logging.warning(f"[BaselineLearner] Failed to load baselines: {e}")
            # Initialize with pre-seeded estimates
            self._initialize_default_baselines()
    
    def _initialize_default_baselines(self):
        """Pre-seed with estimated baselines."""
        default_baselines = {
            "joy": 15.0,
            "contemplation": 8.0,
            "curiosity": 12.0,
            "confidence": 14.0,
            "uncertainty": 10.0,
            "neutral": 12.0
        }
        
        for emotion, rate in default_baselines.items():
            self.baselines[emotion] = Baseline(
                emotion_state=emotion,
                sample_count=0,
                avg_tokens_per_sec=rate,
                std_dev_tokens_per_sec=2.0,
                p50_latency_us=80000,
                p95_latency_us=150000,
                p99_latency_us=300000,
                avg_pause_count=2.0,
                confidence="low",
                last_updated=datetime.now()
            )
        
        logging.info("[BaselineLearner] Initialized with default baselines")
    
    def get_baseline(self, emotion_state: str) -> Optional[Baseline]:
        """Get baseline for emotion state."""
        return self.baselines.get(emotion_state)
    
    def update(self, timing: TokenTimingAnalysis, emotion_state: str):
        """Update baseline with new sample (exponential moving average)."""
        try:
            baseline = self.baselines.get(emotion_state)
            
            if not baseline:
                # Create new baseline
                baseline = Baseline(
                    emotion_state=emotion_state,
                    sample_count=0,
                    avg_tokens_per_sec=timing.avg_tokens_per_sec,
                    std_dev_tokens_per_sec=0.0,
                    p50_latency_us=timing.p50_latency_us,
                    p95_latency_us=timing.p95_latency_us,
                    p99_latency_us=timing.p99_latency_us,
                    avg_pause_count=float(timing.pause_count),
                    confidence="low",
                    last_updated=datetime.now()
                )
            else:
                # Exponential moving average (EMA)
                alpha = min(0.1, 1.0 / (baseline.sample_count + 1))
                
                baseline.avg_tokens_per_sec = (
                    (1 - alpha) * baseline.avg_tokens_per_sec + 
                    alpha * timing.avg_tokens_per_sec
                )
                
                baseline.p50_latency_us = int(
                    (1 - alpha) * baseline.p50_latency_us + 
                    alpha * timing.p50_latency_us
                )
                
                baseline.avg_pause_count = (
                    (1 - alpha) * baseline.avg_pause_count + 
                    alpha * timing.pause_count
                )
                
                baseline.sample_count += 1
                
                # Update confidence
                if baseline.sample_count < 100:
                    baseline.confidence = "low"
                elif baseline.sample_count < 1000:
                    baseline.confidence = "medium"
                else:
                    baseline.confidence = "high"
                
                baseline.last_updated = datetime.now()
            
            self.baselines[emotion_state] = baseline
            
            # Persist to database
            self._save_baseline(baseline)
            
            logging.debug(f"[BaselineLearner] Updated baseline for {emotion_state} (samples={baseline.sample_count})")
            
        except Exception as e:
            logging.error(f"[BaselineLearner] Update failed: {e}")
    
    def _save_baseline(self, baseline: Baseline):
        """Save baseline to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO token_baselines 
                (emotion_state, sample_count, avg_tokens_per_sec, std_dev_tokens_per_sec,
                 p50_latency_us, p95_latency_us, p99_latency_us, avg_pause_count, 
                 confidence, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                baseline.emotion_state,
                baseline.sample_count,
                baseline.avg_tokens_per_sec,
                baseline.std_dev_tokens_per_sec,
                baseline.p50_latency_us,
                baseline.p95_latency_us,
                baseline.p99_latency_us,
                baseline.avg_pause_count,
                baseline.confidence,
                baseline.last_updated.isoformat()
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logging.error(f"[BaselineLearner] Save failed: {e}")

    # ── FORGE additions: Multi-dimensional baseline support ──

    def get_multidim_key(self, model: str, emotion: str, state: str) -> str:
        """Create composite key for multi-dimensional baseline."""
        return f"{model}|{emotion}|{state}"

    def get_multidim_baseline(self, model: str, emotion: str, state: str) -> Optional[Baseline]:
        """
        Get baseline for model × emotion × state combination.
        Falls back: composite → emotion-only → None
        """
        key = self.get_multidim_key(model, emotion, state)
        baseline = self.baselines.get(key)
        if not baseline:
            baseline = self.baselines.get(emotion)
        return baseline

    def update_multidim(self, timing: TokenTimingAnalysis,
                        model: str, emotion: str, state: str):
        """Update baseline with multi-dimensional key (model × emotion × state)."""
        key = self.get_multidim_key(model, emotion, state)
        self._update_with_key(timing, key)
        # Also update simple emotion baseline for backward compatibility
        self.update(timing, emotion)

    def _update_with_key(self, timing: TokenTimingAnalysis, key: str):
        """Internal: update baseline using arbitrary key."""
        try:
            baseline = self.baselines.get(key)

            if not baseline:
                baseline = Baseline(
                    emotion_state=key,
                    sample_count=0,
                    avg_tokens_per_sec=timing.avg_tokens_per_sec,
                    std_dev_tokens_per_sec=0.0,
                    p50_latency_us=timing.p50_latency_us,
                    p95_latency_us=timing.p95_latency_us,
                    p99_latency_us=timing.p99_latency_us,
                    avg_pause_count=float(timing.pause_count),
                    confidence="low",
                    last_updated=datetime.now()
                )
            else:
                alpha = min(0.1, 1.0 / (baseline.sample_count + 1))
                baseline.avg_tokens_per_sec = (
                    (1 - alpha) * baseline.avg_tokens_per_sec
                    + alpha * timing.avg_tokens_per_sec
                )
                baseline.p50_latency_us = int(
                    (1 - alpha) * baseline.p50_latency_us
                    + alpha * timing.p50_latency_us
                )
                baseline.avg_pause_count = (
                    (1 - alpha) * baseline.avg_pause_count
                    + alpha * timing.pause_count
                )
                baseline.sample_count += 1

                if baseline.sample_count < 100:
                    baseline.confidence = "low"
                elif baseline.sample_count < 1000:
                    baseline.confidence = "medium"
                else:
                    baseline.confidence = "high"

                baseline.last_updated = datetime.now()

            self.baselines[key] = baseline
            self._save_baseline(baseline)

        except Exception as e:
            logging.error(f"[BaselineLearner] Multi-dim update failed for {key}: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# COMPONENT 8: ANOMALY DETECTOR (LiveAudit, SynapseNotify)
# ═══════════════════════════════════════════════════════════════════════════════

class AnomalyDetector:
    """
    Detect unusual token generation patterns.
    
    Tools: LiveAudit, SynapseNotify, ErrorRecovery
    Performance Target: <5ms anomaly detection
    """
    
    def __init__(self, config: TokenAnalyticsConfig):
        self.config = config
        threshold = config.get("token_analytics", "anomaly_threshold_multiplier")
        if threshold is None:
            threshold = 2.0  # Default
        self.threshold = threshold
        logging.info(f"[AnomalyDetector] Initialized (threshold={self.threshold}x)")
    
    def detect(self, timing: TokenTimingAnalysis, baseline: Optional[Baseline]) -> Optional[TokenAnomaly]:
        """Detect anomalies in token generation."""
        if not baseline or baseline.confidence == "low":
            return None  # Need sufficient baseline samples
        
        try:
            # Calculate deviation
            deviation = abs(timing.avg_tokens_per_sec - baseline.avg_tokens_per_sec) / baseline.avg_tokens_per_sec
            
            if deviation > self.threshold:  # >2x deviation = anomaly
                # Classify anomaly type
                if timing.pause_count > baseline.avg_pause_count * 3:
                    anomaly_type = "stuttering"
                    severity = "medium"
                    action = "Check GPU throttle, RAM pressure, disk I/O"
                elif timing.pause_total_duration_ms > 5000:
                    anomaly_type = "freezing"
                    severity = "critical"
                    action = "Restart Ollama, check process health, verify VRAM"
                elif timing.avg_tokens_per_sec > baseline.avg_tokens_per_sec * 3:
                    anomaly_type = "racing"
                    severity = "low"
                    action = "Verify generation quality, check caching, review prompt"
                else:
                    anomaly_type = "erratic"
                    severity = "medium"
                    action = "Review latency variance, check system stability"
                
                anomaly = TokenAnomaly(
                    timestamp_us=timing.start_timestamp_us,
                    session_id=timing.session_id,
                    anomaly_type=anomaly_type,
                    severity=severity,
                    deviation_from_baseline=deviation,
                    token_rate=timing.avg_tokens_per_sec,
                    expected_token_rate=baseline.avg_tokens_per_sec,
                    context=f"{timing.total_tokens} tokens, {timing.generation_curve} curve",
                    recommended_action=action
                )
                
                logging.warning(f"[AnomalyDetector] ANOMALY: {anomaly_type} ({severity}) - {deviation:.1%} deviation")
                return anomaly
            
            return None
            
        except Exception as e:
            logging.error(f"[AnomalyDetector] Detection failed: {e}")
            return None

    def detect_adaptive(self, timing: TokenTimingAnalysis, baseline: Optional[Baseline],
                        sensitivity_threshold: float = 0.2) -> Optional[TokenAnomaly]:
        """
        Detect anomalies with adaptive sensitivity (FORGE addition).
        Catches both ABOVE-baseline AND BELOW-baseline deviations.
        
        sensitivity_threshold: 0.1 = ±10%, 0.2 = ±20%, 0.3 = ±30%
        """
        if not baseline or baseline.confidence == "low":
            return None

        try:
            if baseline.avg_tokens_per_sec == 0:
                return None

            # Calculate signed deviation (positive = above, negative = below)
            signed_deviation = (
                (timing.avg_tokens_per_sec - baseline.avg_tokens_per_sec)
                / baseline.avg_tokens_per_sec
            )
            abs_deviation = abs(signed_deviation)

            if abs_deviation > sensitivity_threshold:
                if signed_deviation > 0:
                    # Above baseline
                    if signed_deviation > sensitivity_threshold * 3:
                        anomaly_type = "racing"
                        severity = "medium"
                        action = "Verify generation quality, check caching, review prompt"
                    else:
                        anomaly_type = "elevated"
                        severity = "low"
                        action = "Monitor - possibly positive emotional engagement"
                else:
                    # Below baseline
                    if timing.pause_count > baseline.avg_pause_count * 3:
                        anomaly_type = "stuttering"
                        severity = "medium"
                        action = "Check GPU throttle, RAM pressure, disk I/O"
                    elif timing.pause_total_duration_ms > 5000:
                        anomaly_type = "freezing"
                        severity = "critical"
                        action = "Restart Ollama, check process health, verify VRAM"
                    else:
                        anomaly_type = "sluggish"
                        severity = "low"
                        action = "Check system load, possible thermal throttle"

                return TokenAnomaly(
                    timestamp_us=timing.start_timestamp_us,
                    session_id=timing.session_id,
                    anomaly_type=anomaly_type,
                    severity=severity,
                    deviation_from_baseline=signed_deviation,
                    token_rate=timing.avg_tokens_per_sec,
                    expected_token_rate=baseline.avg_tokens_per_sec,
                    context=(
                        f"{timing.total_tokens} tokens, {timing.generation_curve} curve, "
                        f"{'above' if signed_deviation > 0 else 'below'} baseline"
                    ),
                    recommended_action=action
                )

            return None

        except Exception as e:
            logging.error(f"[AnomalyDetector] Adaptive detection failed: {e}")
            return None


# ═══════════════════════════════════════════════════════════════════════════════
# COMPONENT 11: MODEL PROFILER (FORGE addition - RestCLI, JSONQuery)
# ═══════════════════════════════════════════════════════════════════════════════

class ModelProfiler:
    """
    Auto-detect AI model and load model-specific profiles.
    Adjusts baselines, cost rates, and sensitivity per model.

    Tools: RestCLI (Ollama API), JSONQuery, ConfigManager
    """

    def __init__(self, config: TokenAnalyticsConfig, profiles_path: Optional[str] = None):
        self.config = config
        self.profiles_path = profiles_path or str(Path(__file__).parent / "model_profiles.json")
        self.profiles: Dict[str, ModelProfile] = {}
        self.sensitivity_presets: Dict[str, Dict] = {}
        self.state_definitions: Dict[str, Dict] = {}
        self.active_model: Optional[str] = None
        self._load_profiles()
        logging.info(f"[ModelProfiler] Initialized ({len(self.profiles)} profiles loaded)")

    def _load_profiles(self):
        """Load model profiles from JSON file."""
        try:
            p = Path(self.profiles_path)
            if p.exists():
                with open(p, 'r') as f:
                    data = json.load(f)

                for name, pd in data.get("model_profiles", {}).items():
                    self.profiles[name] = ModelProfile(
                        model_name=name,
                        family=pd.get("family", "unknown"),
                        context_window=pd.get("context_window", 4096),
                        architecture=pd.get("architecture", "decoder-only"),
                        cost_per_1k_input_tokens=pd.get("cost_per_1k_input_tokens", 0.0),
                        cost_per_1k_output_tokens=pd.get("cost_per_1k_output_tokens", 0.0),
                        supports_function_calling=pd.get("supports_function_calling", False),
                        supports_vision=pd.get("supports_vision", False),
                        supports_reasoning=pd.get("supports_reasoning", False),
                        baseline_tokens_per_sec=pd.get("baseline_tokens_per_sec", 12.0),
                        baseline_first_token_latency_ms=pd.get("baseline_first_token_latency_ms", 150),
                        baseline_emotions=pd.get("baseline_emotions", {})
                    )

                self.sensitivity_presets = data.get("sensitivity_presets", {})
                self.state_definitions = data.get("state_definitions", {})
            else:
                logging.warning(f"[ModelProfiler] Profiles not found: {p}")
        except Exception as e:
            logging.error(f"[ModelProfiler] Failed to load profiles: {e}")

    def detect_model(self, api_response: Dict[str, Any]) -> str:
        """Detect model name from Ollama API response."""
        model_name = api_response.get("model", "")
        base_name = model_name.split(":")[0].strip().lower()
        self.active_model = base_name
        logging.info(f"[ModelProfiler] Detected model: {base_name}")
        return base_name

    def get_profile(self, model_name: Optional[str] = None) -> ModelProfile:
        """Get profile for model, falling back to default."""
        name = model_name or self.active_model or "default"
        profile = self.profiles.get(name)
        if not profile:
            profile = self.profiles.get("default")
        if not profile:
            profile = ModelProfile(
                model_name=name, family="unknown", context_window=4096,
                architecture="decoder-only", cost_per_1k_input_tokens=0.0,
                cost_per_1k_output_tokens=0.0, supports_function_calling=False,
                supports_vision=False, supports_reasoning=False,
                baseline_tokens_per_sec=12.0, baseline_first_token_latency_ms=150,
                baseline_emotions={}
            )
        return profile

    def get_model_baseline(self, model_name: str, emotion_state: str) -> Dict[str, float]:
        """Get model-specific baseline for an emotion."""
        profile = self.get_profile(model_name)
        return profile.baseline_emotions.get(emotion_state, {
            "tokens_per_sec": profile.baseline_tokens_per_sec,
            "pause_count": 2.0
        })

    def get_sensitivity_threshold(self, level: str = "medium") -> float:
        """Get sensitivity threshold as a fraction (0.1 = ±10%)."""
        preset = self.sensitivity_presets.get(level, {})
        return preset.get("threshold_pct", 20) / 100.0


# ═══════════════════════════════════════════════════════════════════════════════
# COMPONENT 12: COST TRACKER (FORGE addition - DataConvert, ConfigManager)
# ═══════════════════════════════════════════════════════════════════════════════

class CostTracker:
    """
    Track financial token costs per session, task type, and emotion.

    Tools: DataConvert, ConfigManager
    """

    def __init__(self, config: TokenAnalyticsConfig, model_profiler: ModelProfiler, db_path: str):
        self.config = config
        self.model_profiler = model_profiler
        self.db_path = db_path
        self.cumulative_costs: Dict[str, float] = {}  # model -> cumulative cost
        self._load_cumulative()
        logging.info("[CostTracker] Initialized")

    def _load_cumulative(self):
        """Load cumulative costs from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT model_name, SUM(total_cost) FROM token_costs GROUP BY model_name"
            )
            for row in cursor.fetchall():
                self.cumulative_costs[row[0]] = row[1]
            conn.close()
        except Exception as e:
            logging.debug(f"[CostTracker] No existing cost data: {e}")

    def calculate_cost(self, model_name: str, input_tokens: int, output_tokens: int,
                       session_id: str, task_type: str = "general",
                       emotion_state: Optional[str] = None) -> TokenCost:
        """Calculate token cost for a generation."""
        profile = self.model_profiler.get_profile(model_name)

        input_cost = (input_tokens / 1000.0) * profile.cost_per_1k_input_tokens
        output_cost = (output_tokens / 1000.0) * profile.cost_per_1k_output_tokens
        total_cost = input_cost + output_cost

        self.cumulative_costs[model_name] = (
            self.cumulative_costs.get(model_name, 0.0) + total_cost
        )

        return TokenCost(
            session_id=session_id,
            model_name=model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=total_cost,
            task_type=task_type,
            emotion_state=emotion_state
        )

    def get_session_cost(self, session_id: str) -> float:
        """Get total cost for a session."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT SUM(total_cost) FROM token_costs WHERE session_id = ?",
                (session_id,)
            )
            result = cursor.fetchone()
            conn.close()
            return result[0] or 0.0 if result else 0.0
        except Exception as e:
            logging.error(f"[CostTracker] Session cost query failed: {e}")
            return 0.0

    def get_cumulative_cost(self, model_name: Optional[str] = None) -> float:
        """Get cumulative cost, optionally filtered by model."""
        if model_name:
            return self.cumulative_costs.get(model_name, 0.0)
        return sum(self.cumulative_costs.values())

    def get_cost_by_emotion(self, model_name: Optional[str] = None) -> Dict[str, float]:
        """Get cost breakdown by emotion state."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            if model_name:
                cursor.execute("""
                    SELECT emotion_state, SUM(total_cost) FROM token_costs
                    WHERE model_name = ? AND emotion_state IS NOT NULL
                    GROUP BY emotion_state
                """, (model_name,))
            else:
                cursor.execute("""
                    SELECT emotion_state, SUM(total_cost) FROM token_costs
                    WHERE emotion_state IS NOT NULL
                    GROUP BY emotion_state
                """)
            result = {row[0]: row[1] for row in cursor.fetchall()}
            conn.close()
            return result
        except Exception as e:
            logging.error(f"[CostTracker] Emotion cost query failed: {e}")
            return {}


# ═══════════════════════════════════════════════════════════════════════════════
# COMPONENT 13: STATE TRANSITION DETECTOR (FORGE addition - TimeSync, RegexLab)
# ═══════════════════════════════════════════════════════════════════════════════

class StateTransitionDetector:
    """
    Detect generation states and transitions from token stream patterns.

    States: receiving_prompt, thinking, generating, tool_calling,
            paused, completing, resting

    Tools: TimeSync, RegexLab, EmotionalTextureAnalyzer
    """

    def __init__(self, config: TokenAnalyticsConfig):
        self.config = config
        state_config = config.get("token_analytics", "state_detection") or {}
        self.thinking_threshold_us = state_config.get("thinking_threshold_ms", 500) * 1000
        self.pause_threshold_us = state_config.get("pause_threshold_ms", 500) * 1000
        self.completing_token_count = state_config.get("completing_token_count", 5)

        # Tool-calling patterns
        self.tool_patterns = [
            '{"function"', '{"name":', 'tool_call', '<tool>',
            '```python', '```bash', '```powershell'
        ]
        logging.info("[StateTransitionDetector] Initialized")

    def detect_states(self, events: List[TokenStreamEvent],
                      emotion_state: Optional[str] = None) -> List[GenerationState]:
        """Detect generation states from token stream."""
        if not events:
            return []

        states = []
        current_state = "receiving_prompt"
        state_start_us = events[0].timestamp_us
        state_tokens = 0

        for i, event in enumerate(events):
            new_state = self._classify_token_state(event, events, i)

            if new_state != current_state:
                duration_ms = (event.timestamp_us - state_start_us) / 1000.0
                token_rate = (state_tokens / duration_ms * 1000) if duration_ms > 0 else 0.0

                states.append(GenerationState(
                    state=current_state,
                    start_timestamp_us=state_start_us,
                    end_timestamp_us=event.timestamp_us,
                    duration_ms=max(duration_ms, 0.001),
                    tokens_generated=state_tokens,
                    token_rate=token_rate,
                    emotion_state=emotion_state
                ))

                current_state = new_state
                state_start_us = event.timestamp_us
                state_tokens = 0

            if event.token:
                state_tokens += 1

        # Close final state
        if events:
            last = events[-1]
            duration_ms = (last.timestamp_us - state_start_us) / 1000.0
            token_rate = (state_tokens / duration_ms * 1000) if duration_ms > 0 else 0.0
            states.append(GenerationState(
                state=current_state,
                start_timestamp_us=state_start_us,
                end_timestamp_us=last.timestamp_us,
                duration_ms=max(duration_ms, 0.001),
                tokens_generated=state_tokens,
                token_rate=token_rate,
                emotion_state=emotion_state
            ))

        logging.debug(f"[StateTransitionDetector] Detected {len(states)} states")
        return states

    def _classify_token_state(self, event: TokenStreamEvent,
                               events: List[TokenStreamEvent], index: int) -> str:
        """Classify the generation state at this token."""
        # First token with high latency = thinking
        if index == 0 and event.latency_us > self.thinking_threshold_us:
            return "thinking"

        # Check for tool calling patterns (look back 10 tokens)
        accumulated = "".join(e.token for e in events[max(0, index - 10):index + 1])
        for pattern in self.tool_patterns:
            if pattern in accumulated:
                return "tool_calling"

        # Check for pause
        if event.latency_us > self.pause_threshold_us:
            return "paused"

        # Near completion (last N tokens)
        remaining = len(events) - index
        if remaining <= self.completing_token_count and remaining > 0:
            return "completing"

        # Default: active generation
        return "generating"

    def detect_transitions(self, states: List[GenerationState]) -> List[StateTransition]:
        """Detect transitions between states."""
        transitions = []
        for i in range(1, len(states)):
            prev = states[i - 1]
            curr = states[i]
            trigger = self._classify_trigger(prev.state, curr.state)
            transitions.append(StateTransition(
                from_state=prev.state,
                to_state=curr.state,
                transition_timestamp_us=curr.start_timestamp_us,
                trigger=trigger
            ))

        logging.debug(f"[StateTransitionDetector] Detected {len(transitions)} transitions")
        return transitions

    def _classify_trigger(self, from_state: str, to_state: str) -> str:
        """Classify what triggered a state transition."""
        if to_state == "paused":
            return "pause_detected"
        elif from_state == "paused" and to_state == "generating":
            return "tokens_resumed"
        elif to_state == "thinking":
            return "prompt_received"
        elif from_state == "thinking" and to_state == "generating":
            return "tokens_started"
        elif to_state == "tool_calling":
            return "tool_called"
        elif to_state == "completing":
            return "generation_ending"
        elif to_state == "resting":
            return "generation_complete"
        return "state_change"

    def get_state_summary(self, states: List[GenerationState]) -> Dict[str, Dict[str, Any]]:
        """Summarize time spent and tokens per state."""
        summary: Dict[str, Dict[str, Any]] = {}
        for s in states:
            if s.state not in summary:
                summary[s.state] = {
                    "total_duration_ms": 0.0,
                    "total_tokens": 0,
                    "occurrences": 0,
                    "avg_token_rate": 0.0
                }
            entry = summary[s.state]
            entry["total_duration_ms"] += s.duration_ms
            entry["total_tokens"] += s.tokens_generated
            entry["occurrences"] += 1

        for entry in summary.values():
            if entry["total_duration_ms"] > 0:
                entry["avg_token_rate"] = entry["total_tokens"] / entry["total_duration_ms"] * 1000

        return summary


# ═══════════════════════════════════════════════════════════════════════════════
# COMPONENT 9: TOKEN ANALYTICS DATABASE (QuickBackup, HashGuard)
# ═══════════════════════════════════════════════════════════════════════════════

class TokenAnalyticsDatabase:
    """
    Extended research database with 4 new tables for token analytics.
    
    Tools: QuickBackup, HashGuard, DataConvert
    Performance Target: <5ms write per token, <100ms query for 1000 tokens
    """
    
    def __init__(self, config: TokenAnalyticsConfig):
        self.config = config
        self.db_path = config.get_with_default("token_analytics", "db_path", default="./tokenanalytics_research.db")
        
        # Get batch size from nested config
        performance_config = config.get("token_analytics", "performance")
        if performance_config and isinstance(performance_config, dict):
            self.batch_size = performance_config.get("batch_write_size", 100)
        else:
            self.batch_size = 100
        
        # Write buffers (batch writes for performance)
        self.token_buffer = []
        self.emotion_corr_buffer = []
        self.hardware_corr_buffer = []
        
        # Initialize database
        self._initialize_database()
        logging.info(f"[TokenAnalyticsDatabase] Initialized (db={self.db_path})")
    
    def _initialize_database(self):
        """Create tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Enable WAL mode for concurrent writes
        cursor.execute("PRAGMA journal_mode=WAL")
        
        # Table 1: token_analytics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS token_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp_us INTEGER NOT NULL,
                token TEXT NOT NULL,
                token_index INTEGER NOT NULL,
                latency_us INTEGER NOT NULL,
                cumulative_latency_ms REAL NOT NULL,
                tokens_per_sec REAL NOT NULL,
                generation_curve TEXT,
                is_pause BOOLEAN DEFAULT 0,
                session_id TEXT NOT NULL,
                prompt_hash TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_session ON token_analytics(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON token_analytics(timestamp_us)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_prompt ON token_analytics(prompt_hash)")
        
        # Table 2: token_emotion_correlation
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS token_emotion_correlation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp_us INTEGER NOT NULL,
                session_id TEXT NOT NULL,
                emotion_state TEXT NOT NULL,
                emotion_intensity REAL NOT NULL,
                token_rate REAL NOT NULL,
                baseline_token_rate REAL NOT NULL,
                deviation_pct REAL NOT NULL,
                correlation_quality TEXT,
                pause_count INTEGER DEFAULT 0,
                generation_curve TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_emotion ON token_emotion_correlation(emotion_state)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_quality ON token_emotion_correlation(correlation_quality)")
        
        # Table 3: token_hardware_correlation
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS token_hardware_correlation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp_us INTEGER NOT NULL,
                session_id TEXT NOT NULL,
                token_rate REAL NOT NULL,
                baseline_token_rate REAL NOT NULL,
                gpu_throttle BOOLEAN DEFAULT 0,
                gpu_temp_c REAL,
                gpu_utilization_pct REAL,
                ram_pressure_pct REAL,
                vram_used_mb REAL,
                hardware_impact_pct REAL,
                bottleneck_type TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_bottleneck ON token_hardware_correlation(bottleneck_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_throttle ON token_hardware_correlation(gpu_throttle)")
        
        # Table 4: token_baselines
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS token_baselines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                emotion_state TEXT NOT NULL UNIQUE,
                sample_count INTEGER NOT NULL DEFAULT 0,
                avg_tokens_per_sec REAL NOT NULL,
                std_dev_tokens_per_sec REAL NOT NULL,
                p50_latency_us INTEGER NOT NULL,
                p95_latency_us INTEGER NOT NULL,
                p99_latency_us INTEGER NOT NULL,
                avg_pause_count REAL NOT NULL,
                confidence TEXT NOT NULL,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_emotion_baseline ON token_baselines(emotion_state)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_confidence ON token_baselines(confidence)")

        # Table 5: token_costs (FORGE addition)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS token_costs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                model_name TEXT NOT NULL,
                input_tokens INTEGER NOT NULL,
                output_tokens INTEGER NOT NULL,
                total_tokens INTEGER NOT NULL,
                input_cost REAL NOT NULL,
                output_cost REAL NOT NULL,
                total_cost REAL NOT NULL,
                task_type TEXT DEFAULT 'general',
                emotion_state TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_cost ON token_costs(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_model_cost ON token_costs(model_name)")

        # Table 6: generation_states (FORGE addition)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS generation_states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                model_name TEXT NOT NULL,
                state TEXT NOT NULL,
                start_timestamp_us INTEGER NOT NULL,
                end_timestamp_us INTEGER NOT NULL,
                duration_ms REAL NOT NULL,
                tokens_generated INTEGER NOT NULL,
                token_rate REAL NOT NULL,
                emotion_state TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_state ON generation_states(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_state_type ON generation_states(state)")

        # Table 7: state_transitions (FORGE addition)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS state_transitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                model_name TEXT NOT NULL,
                from_state TEXT NOT NULL,
                to_state TEXT NOT NULL,
                transition_timestamp_us INTEGER NOT NULL,
                trigger TEXT NOT NULL,
                emotion_state TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_transition ON state_transitions(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transition_type ON state_transitions(from_state, to_state)")

        conn.commit()
        conn.close()
        
        logging.info("[TokenAnalyticsDatabase] Tables initialized (7 tables)")
    
    def store_token_events(self, events: List[TokenStreamEvent]):
        """Store token events (buffered for performance)."""
        self.token_buffer.extend(events)
        
        if len(self.token_buffer) >= self.batch_size:
            self._flush_token_buffer()
    
    def store_emotion_correlation(self, correlation: EmotionTokenCorrelation):
        """Store emotion-token correlation (buffered)."""
        self.emotion_corr_buffer.append(correlation)
        
        if len(self.emotion_corr_buffer) >= self.batch_size:
            self._flush_emotion_buffer()
    
    def store_hardware_correlation(self, correlation: HardwareTokenCorrelation):
        """Store hardware-token correlation (buffered)."""
        self.hardware_corr_buffer.append(correlation)
        
        if len(self.hardware_corr_buffer) >= self.batch_size:
            self._flush_hardware_buffer()
    
    def _flush_token_buffer(self):
        """Batch write token events to database."""
        if not self.token_buffer:
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for event in self.token_buffer:
                cursor.execute("""
                    INSERT INTO token_analytics 
                    (timestamp_us, token, token_index, latency_us, cumulative_latency_ms,
                     tokens_per_sec, generation_curve, is_pause, session_id, prompt_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.timestamp_us,
                    event.token,
                    event.token_index,
                    event.latency_us,
                    event.cumulative_latency_ms,
                    0.0,  # tokens_per_sec calculated per session
                    "",   # generation_curve calculated per session
                    event.latency_us > 500000,  # is_pause (>500ms)
                    event.session_id,
                    event.prompt_hash
                ))
            
            conn.commit()
            conn.close()
            
            logging.debug(f"[TokenAnalyticsDatabase] Flushed {len(self.token_buffer)} token events")
            self.token_buffer.clear()
            
        except Exception as e:
            logging.error(f"[TokenAnalyticsDatabase] Token buffer flush failed: {e}")
    
    def _flush_emotion_buffer(self):
        """Batch write emotion correlations to database."""
        if not self.emotion_corr_buffer:
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for corr in self.emotion_corr_buffer:
                cursor.execute("""
                    INSERT INTO token_emotion_correlation
                    (timestamp_us, session_id, emotion_state, emotion_intensity, token_rate,
                     baseline_token_rate, deviation_pct, correlation_quality, pause_count, generation_curve)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    corr.timestamp_us,
                    corr.session_id,
                    corr.emotion_state,
                    corr.emotion_intensity,
                    corr.token_rate,
                    corr.baseline_token_rate,
                    corr.deviation_pct,
                    corr.correlation_quality,
                    corr.pause_count,
                    corr.generation_curve
                ))
            
            conn.commit()
            conn.close()
            
            logging.debug(f"[TokenAnalyticsDatabase] Flushed {len(self.emotion_corr_buffer)} emotion correlations")
            self.emotion_corr_buffer.clear()
            
        except Exception as e:
            logging.error(f"[TokenAnalyticsDatabase] Emotion buffer flush failed: {e}")
    
    def _flush_hardware_buffer(self):
        """Batch write hardware correlations to database."""
        if not self.hardware_corr_buffer:
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for corr in self.hardware_corr_buffer:
                cursor.execute("""
                    INSERT INTO token_hardware_correlation
                    (timestamp_us, session_id, token_rate, baseline_token_rate, gpu_throttle,
                     gpu_temp_c, gpu_utilization_pct, ram_pressure_pct, vram_used_mb,
                     hardware_impact_pct, bottleneck_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    corr.timestamp_us,
                    corr.session_id,
                    corr.token_rate,
                    corr.baseline_token_rate,
                    corr.gpu_throttle,
                    corr.gpu_temp_c,
                    corr.gpu_utilization_pct,
                    corr.ram_pressure_pct,
                    corr.vram_used_mb,
                    corr.hardware_impact_pct,
                    corr.bottleneck_type
                ))
            
            conn.commit()
            conn.close()
            
            logging.debug(f"[TokenAnalyticsDatabase] Flushed {len(self.hardware_corr_buffer)} hardware correlations")
            self.hardware_corr_buffer.clear()
            
        except Exception as e:
            logging.error(f"[TokenAnalyticsDatabase] Hardware buffer flush failed: {e}")
    
    def flush_all(self):
        """Flush all buffers to database."""
        self._flush_token_buffer()
        self._flush_emotion_buffer()
        self._flush_hardware_buffer()

    # ── FORGE additions: Storage for new components ──

    def store_cost(self, cost: TokenCost):
        """Store token cost record."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO token_costs
                (session_id, model_name, input_tokens, output_tokens, total_tokens,
                 input_cost, output_cost, total_cost, task_type, emotion_state)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cost.session_id, cost.model_name, cost.input_tokens, cost.output_tokens,
                cost.total_tokens, cost.input_cost, cost.output_cost, cost.total_cost,
                cost.task_type, cost.emotion_state
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logging.error(f"[TokenAnalyticsDatabase] Cost storage failed: {e}")

    def store_generation_states(self, states: List[GenerationState],
                                session_id: str, model_name: str):
        """Store generation state records."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            for s in states:
                cursor.execute("""
                    INSERT INTO generation_states
                    (session_id, model_name, state, start_timestamp_us, end_timestamp_us,
                     duration_ms, tokens_generated, token_rate, emotion_state)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_id, model_name, s.state, s.start_timestamp_us,
                    s.end_timestamp_us, s.duration_ms, s.tokens_generated,
                    s.token_rate, s.emotion_state
                ))
            conn.commit()
            conn.close()
        except Exception as e:
            logging.error(f"[TokenAnalyticsDatabase] State storage failed: {e}")

    def store_transitions(self, transitions: List[StateTransition],
                          session_id: str, model_name: str,
                          emotion_state: Optional[str] = None):
        """Store state transition records."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            for t in transitions:
                cursor.execute("""
                    INSERT INTO state_transitions
                    (session_id, model_name, from_state, to_state,
                     transition_timestamp_us, trigger, emotion_state)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_id, model_name, t.from_state, t.to_state,
                    t.transition_timestamp_us, t.trigger, emotion_state
                ))
            conn.commit()
            conn.close()
        except Exception as e:
            logging.error(f"[TokenAnalyticsDatabase] Transition storage failed: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# COMPONENT 10: TOKEN ANALYTICS DAEMON (Main Orchestrator)
# ═══════════════════════════════════════════════════════════════════════════════

class TokenAnalyticsDaemon(HardwareSoulDaemon if HARDWARESOUL_AVAILABLE else object):
    """
    Token Analytics Daemon - Extends Phase 3 (HardwareSoul) with token analysis.
    
    Inherits:
    - Phase 1 (OllamaGuard): Ollama health monitoring
    - Phase 2 (InferencePulse): Emotion detection
    - Phase 3 (HardwareSoul): GPU/RAM monitoring
    
    Adds:
    - Phase 4 (TokenAnalytics): Token pattern analysis
    
    Tools: All 39 tools (37 inherited + 2 new)
    """
    
    def __init__(self, config_path: Optional[str] = None):
        # Initialize Phase 4 config FIRST (before cascade overwrites self.config)
        phase4_config = TokenAnalyticsConfig(config_path)
        self.phase4_config = phase4_config  # Always preserved as named attribute
        self.config = phase4_config
        
        # Initialize Phase 3 (HardwareSoul) if available
        # The cascade (Phase 3 → 2 → 1) will overwrite self.config with OllamaGuardConfig.
        # We restore it afterward.
        if HARDWARESOUL_AVAILABLE:
            try:
                super().__init__(config_path)
            except Exception as e:
                logging.warning(f"[TokenAnalytics] Phase 3 initialization failed: {e}")
                logging.info("[TokenAnalytics] Running Phase 4 standalone mode")
        
        # NOTE: Do NOT restore self.config -- Phase 1 uses it for its monitoring loop.
        # Phase 4 components use self.phase4_config instead.
        
        # Phase 4 enabled check
        self.phase4_enabled = self.phase4_config.get("token_analytics", "enabled")
        
        if self.phase4_enabled is None:
            self.phase4_enabled = True  # Default to enabled
        
        if not self.phase4_enabled:
            logging.info("[TokenAnalytics] Phase 4 disabled - running Phase 3 only")
            return
        
        # Initialize Phase 4 components using phase4_config
        # (self.config belongs to Phase 1 after cascade -- use self.phase4_config)
        p4cfg = self.phase4_config
        
        self.token_capture = TokenStreamCapture(p4cfg)
        self.timing_analyzer = TokenTimingAnalyzer(p4cfg)
        self.pause_detector = PauseDetector(p4cfg)
        self.curve_tracker = GenerationCurveTracker(p4cfg)
        
        # Initialize database and baseline learner
        # NOTE: Use "token_baseline_learner" to avoid collision with Phase 2's baseline_learner
        db_path = p4cfg.get_with_default("token_analytics", "db_path", default="./tokenanalytics_research.db")
        self.token_db = TokenAnalyticsDatabase(p4cfg)
        self.token_baseline_learner = BaselineLearner(p4cfg, db_path)
        
        # Initialize correlators
        # NOTE: Use "token_emotion_correlator" / "token_hardware_correlator" / "token_anomaly_detector"
        # to avoid collision with Phase 3's emotion_correlator and Phase 2's anomaly_detector
        self.token_emotion_correlator = EmotionTokenCorrelator(p4cfg, self.token_baseline_learner)
        self.token_hardware_correlator = HardwareTokenCorrelator(p4cfg, self.token_baseline_learner)
        self.token_anomaly_detector = AnomalyDetector(p4cfg)

        # FORGE additions: Model profiler, cost tracker, state detector
        profiles_path = p4cfg.get_with_default(
            "token_analytics", "model_profiles_path",
            default=str(Path(__file__).parent / "model_profiles.json")
        )
        self.model_profiler = ModelProfiler(p4cfg, profiles_path)
        self.cost_tracker = CostTracker(p4cfg, self.model_profiler, db_path)
        self.state_detector = StateTransitionDetector(p4cfg)
        self.sensitivity_level = p4cfg.get_with_default(
            "token_analytics", "sensitivity_level", default="medium"
        )

        # Metrics
        self.metrics = {
            "tokens_captured": 0,
            "sessions_analyzed": 0,
            "emotion_correlations": 0,
            "hardware_correlations": 0,
            "anomalies_detected": 0,
            "baseline_updates": 0,
            "costs_tracked": 0,
            "states_detected": 0,
            "transitions_detected": 0
        }
        
        # Threading
        self.running = True
        self.token_monitoring_thread = None
        
        logging.info("[TokenAnalyticsDaemon] Phase 4 initialized ✓")
    
    def start(self):
        """Start token analytics daemon (extends Phase 3).
        
        BUG FIX (FORGE 2026-02-15): Phase 3's start() blocks in _phase3_main_loop().
        Must thread it (matching the pattern Phase 3/Phase 2 use for their parents)
        so Phase 4's token monitoring can start alongside.
        """
        logging.info("[TokenAnalyticsDaemon] Starting...")
        
        # Start Phase 3 (HardwareSoul) in a daemon thread -- it blocks in _phase3_main_loop
        if HARDWARESOUL_AVAILABLE and hasattr(super(), 'start'):
            phase3_thread = threading.Thread(target=super().start, daemon=True)
            phase3_thread.start()
            logging.info("[TokenAnalyticsDaemon] Phase 3 (HardwareSoul) started in background thread")
        
        if not self.phase4_enabled:
            return
        
        # Start Phase 4 token monitoring
        self.token_monitoring_thread = threading.Thread(
            target=self._token_monitoring_loop,
            daemon=True
        )
        self.token_monitoring_thread.start()
        
        logging.info("[TokenAnalyticsDaemon] Token analytics monitoring started")
        
        # Keep daemon alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logging.info("[TokenAnalyticsDaemon] Shutdown signal received")
            self.stop()
    
    def _token_monitoring_loop(self):
        """
        Main token analytics monitoring loop - ENHANCED by ATLAS.
        
        Real-time monitoring using all 13 components:
        1. Hook into Ollama streaming API during inference
        2. Capture tokens in real-time with model detection
        3. Analyze timing patterns
        4. Correlate with emotion + hardware + state
        5. Update multi-dimensional baselines
        6. Detect anomalies with adaptive sensitivity
        7. Track costs per model/emotion/state
        
        Tools: All Phase 4 components (ATLAS 1-10 + FORGE 11-13)
        """
        logging.info("[TokenAnalytics] Enhanced monitoring loop started")
        
        # Monitoring state
        last_analysis_time = 0
        analysis_interval_ms = self.phase4_config.get_with_default(
            "token_analytics", "analysis_interval_ms", 
            default=5000  # Analyze every 5 seconds
        )
        
        while self.running:
            try:
                current_time = time.time()
                
                # Check if it's time for periodic analysis
                if (current_time - last_analysis_time) * 1000 >= analysis_interval_ms:
                    
                    # Step 1: Check for active inference (Phase 2 integration)
                    if hasattr(self, 'inference_monitor') and self._is_inference_active():
                        
                        # Get current inference context
                        current_prompt = self._get_current_prompt()
                        current_emotion = self._get_current_emotion()
                        
                        if current_prompt:
                            session_id = f"monitor_{int(current_time)}"
                            
                            # Step 2: Model detection (Component 11)
                            try:
                                # Detect model from Ollama API
                                api_status = self._probe_ollama_api()
                                if api_status and "model" in api_status:
                                    detected_model = self.model_profiler.detect_model(api_status)
                                    model_profile = self.model_profiler.get_profile(detected_model)
                                    logging.debug(f"[Monitor] Detected model: {detected_model}")
                                else:
                                    model_profile = self.model_profiler.get_profile()
                            except Exception as e:
                                logging.debug(f"[Monitor] Model detection failed, using default: {e}")
                                model_profile = self.model_profiler.get_profile()
                            
                            # Step 3: Capture token stream (Component 1)
                            token_events = self.token_capture.capture_stream(current_prompt, session_id)
                            
                            if token_events:
                                # Step 4: Analyze timing (Component 2)
                                timing_analysis = self.timing_analyzer.analyze(token_events)
                                
                                if timing_analysis:
                                    # Step 5: Detect states (Component 13 - FORGE)
                                    generation_states = []
                                    state_transitions = []
                                    if self.phase4_config.get_with_default("token_analytics", "state_detection_enabled", default=True):
                                        generation_states = self.state_detector.detect_states(
                                            token_events, current_emotion
                                        )
                                        state_transitions = self.state_detector.detect_transitions(generation_states)
                                        
                                        # Store states and transitions
                                        if generation_states:
                                            self.token_db.store_generation_states(
                                                generation_states, session_id, model_profile.model_name
                                            )
                                        if state_transitions:
                                            self.token_db.store_transitions(
                                                state_transitions, session_id, model_profile.model_name, current_emotion
                                            )
                                    
                                    # Step 6: Track costs (Component 12 - FORGE)
                                    cost_record = None
                                    if self.phase4_config.get_with_default("token_analytics", "cost_tracking_enabled", default=True):
                                        # Count input/output tokens
                                        input_tokens = len(current_prompt.split())  # Rough estimate
                                        output_tokens = timing_analysis.total_tokens
                                        
                                        cost_record = self.cost_tracker.calculate_cost(
                                            model_name=model_profile.model_name,
                                            input_tokens=input_tokens,
                                            output_tokens=output_tokens,
                                            session_id=session_id,
                                            task_type="monitoring",
                                            emotion_state=current_emotion
                                        )
                                        
                                        # Store cost
                                        if cost_record:
                                            self.token_db.store_cost(cost_record)
                                    
                                    # Step 7: Detect pauses (Component 3)
                                    pauses = self.pause_detector.detect(token_events, current_emotion)
                                    
                                    # Step 8: Track generation curve (Component 4)
                                    curve_segments = self.curve_tracker.track(token_events)
                                    
                                    # Step 9: Determine current generation state
                                    current_state = "generating"
                                    if generation_states:
                                        current_state = generation_states[-1].state
                                    
                                    # Step 10: Correlate with emotion (Component 5)
                                    emotion_corr = None
                                    if self.phase4_config.get_with_default("token_analytics", "emotion_correlation_enabled", default=True):
                                        self.token_emotion_correlator.add_emotion_event(
                                            current_emotion or "neutral",
                                            1.0,  # Intensity placeholder
                                            timing_analysis.start_timestamp_us
                                        )
                                        emotion_corr = self.token_emotion_correlator.correlate(timing_analysis)
                                        
                                        if emotion_corr:
                                            self.token_db.store_emotion_correlation(emotion_corr)
                                            self.metrics["emotion_correlations"] += 1
                                    
                                    # Step 11: Correlate with hardware (Component 6)
                                    hardware_corr = None
                                    if self.phase4_config.get_with_default("token_analytics", "hardware_correlation_enabled", default=True):
                                        if hasattr(self, 'gpu_monitor') and hasattr(self, 'ram_monitor'):
                                            gpu_sample = self.gpu_monitor.sample()
                                            ram_sample = self.ram_monitor.sample()
                                            
                                            if gpu_sample:
                                                gpu_sample["timestamp_us"] = int(time.time() * 1_000_000)
                                            if ram_sample:
                                                ram_sample["timestamp_us"] = int(time.time() * 1_000_000)
                                            
                                            self.token_hardware_correlator.add_hardware_samples(gpu_sample, ram_sample)
                                            hardware_corr = self.token_hardware_correlator.correlate(
                                                timing_analysis, current_emotion or "neutral"
                                            )
                                            
                                            if hardware_corr:
                                                self.token_db.store_hardware_correlation(hardware_corr)
                                                self.metrics["hardware_correlations"] += 1
                                    
                                    # Step 12: Update multi-dimensional baseline (Component 7 - ENHANCED)
                                    if self.phase4_config.get_with_default("token_analytics", "baseline_learning_enabled", default=True):
                                        self.token_baseline_learner.update_multidim(
                                            timing_analysis,
                                            model_profile.model_name,
                                            current_emotion or "neutral",
                                            current_state
                                        )
                                        self.metrics["baseline_updates"] += 1
                                    
                                    # Step 13: Detect anomalies with adaptive sensitivity (Component 8 - ENHANCED)
                                    anomaly = None
                                    if self.phase4_config.get_with_default("token_analytics", "anomaly_detection_enabled", default=True):
                                        # Get multi-dimensional baseline
                                        baseline = self.token_baseline_learner.get_multidim_baseline(
                                            model_profile.model_name,
                                            current_emotion or "neutral",
                                            current_state
                                        )
                                        
                                        # Get sensitivity as float via ModelProfiler
                                        sensitivity = self.model_profiler.get_sensitivity_threshold(
                                            self.sensitivity_level
                                        )
                                        
                                        # Detect with adaptive sensitivity
                                        anomaly = self.token_anomaly_detector.detect_adaptive(
                                            timing_analysis,
                                            baseline,
                                            sensitivity
                                        )
                                        
                                        if anomaly:
                                            self.metrics["anomalies_detected"] += 1
                                            logging.warning(f"[Monitor] Anomaly: {anomaly.anomaly_type} ({anomaly.severity})")
                                    
                                    # Step 14: Store token events
                                    self.token_db.store_token_events(token_events)
                                    
                                    # Update metrics
                                    self.metrics["tokens_captured"] += len(token_events)
                                    self.metrics["sessions_analyzed"] += 1
                                    
                                    # Log monitoring summary
                                    logging.info(
                                        f"[Monitor] Analyzed {len(token_events)} tokens "
                                        f"(model={model_profile.model_name}, "
                                        f"emotion={current_emotion}, "
                                        f"state={current_state}, "
                                        f"rate={timing_analysis.avg_tokens_per_sec:.1f} tok/s"
                                        f"{', cost=$' + str(cost_record.total_cost) if cost_record else ''})"
                                    )
                    
                    # Update last analysis time
                    last_analysis_time = current_time
                
                # Periodic buffer flush
                self.token_db.flush_all()
                
                # Sleep until next check (100ms interval for responsiveness)
                time.sleep(0.1)
                
            except Exception as e:
                logging.error(f"[TokenAnalytics] Monitoring loop error: {e}")
                time.sleep(5)  # Back off on error
    
    def analyze_prompt(self, prompt: str, session_id: str, emotional_state: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze a single prompt and return token analytics.
        
        This is the main entry point for token analysis.
        Can be called programmatically or via API.
        """
        if not self.phase4_enabled:
            return {"error": "Token analytics disabled"}
        
        try:
            # TimeSync: Start analysis
            analysis_start = time.time()
            
            # Step 1: Capture token stream
            token_events = self.token_capture.capture_stream(prompt, session_id)
            
            if not token_events:
                return {"error": "No tokens captured"}
            
            # Step 2: Analyze timing
            timing_analysis = self.timing_analyzer.analyze(token_events)
            
            if not timing_analysis:
                return {"error": "Timing analysis failed"}
            
            # Step 3: Detect pauses
            pauses = self.pause_detector.detect(token_events, emotional_state)
            
            # Step 4: Track generation curve
            curve_segments = self.curve_tracker.track(token_events)
            
            # Step 5: Correlate with emotion (if available)
            emotion_corr = None
            if emotional_state and self.phase4_config.get("token_analytics", "emotion_correlation_enabled"):
                # Add emotion event to correlator buffer
                self.token_emotion_correlator.add_emotion_event(
                    emotion_state=emotional_state,
                    emotion_intensity=1.0,  # TODO: Get actual intensity from Phase 2
                    timestamp_us=timing_analysis.start_timestamp_us
                )
                emotion_corr = self.token_emotion_correlator.correlate(timing_analysis)
            
            # Step 6: Correlate with hardware (if Phase 3 available)
            hardware_corr = None
            if HARDWARESOUL_AVAILABLE and self.phase4_config.get("token_analytics", "hardware_correlation_enabled"):
                # Get current hardware samples from Phase 3
                gpu_sample = self.gpu_monitor.sample() if hasattr(self, 'gpu_monitor') else None
                ram_sample = self.ram_monitor.sample() if hasattr(self, 'ram_monitor') else None
                
                if gpu_sample:
                    gpu_sample["timestamp_us"] = int(time.time() * 1_000_000)
                if ram_sample:
                    ram_sample["timestamp_us"] = int(time.time() * 1_000_000)
                
                self.token_hardware_correlator.add_hardware_samples(gpu_sample, ram_sample)
                hardware_corr = self.token_hardware_correlator.correlate(timing_analysis, emotional_state or "neutral")
            
            # Step 7: Detect model (FORGE addition)
            model_name = "laia"  # Default
            ollama_cfg = self.phase4_config.get("ollama")
            if ollama_cfg and isinstance(ollama_cfg, dict):
                model_name = ollama_cfg.get("model_name", "laia")
            self.model_profiler.detect_model({"model": model_name})
            model_profile = self.model_profiler.get_profile(model_name)

            # Step 8: Detect generation states (FORGE addition)
            gen_states = []
            state_transitions = []
            state_summary = {}
            if self.phase4_config.get_with_default("token_analytics", "state_detection_enabled", default=True):
                gen_states = self.state_detector.detect_states(token_events, emotional_state)
                state_transitions = self.state_detector.detect_transitions(gen_states)
                state_summary = self.state_detector.get_state_summary(gen_states)
                self.metrics["states_detected"] += len(gen_states)
                self.metrics["transitions_detected"] += len(state_transitions)

            # Step 9: Calculate cost (FORGE addition)
            cost_record = None
            if self.phase4_config.get_with_default("token_analytics", "cost_tracking_enabled", default=True):
                # Estimate input tokens from prompt (rough: ~4 chars per token)
                est_input_tokens = max(1, len(prompt) // 4)
                cost_record = self.cost_tracker.calculate_cost(
                    model_name=model_name,
                    input_tokens=est_input_tokens,
                    output_tokens=len(token_events),
                    session_id=session_id,
                    task_type="analysis",
                    emotion_state=emotional_state
                )
                self.metrics["costs_tracked"] += 1

            # Step 10: Update baselines (multi-dimensional - FORGE enhanced)
            primary_state = "generating"
            if gen_states:
                # Find the dominant generation state
                for gs in gen_states:
                    if gs.state == "generating":
                        primary_state = "generating"
                        break

            if self.phase4_config.get("token_analytics", "baseline_learning_enabled"):
                self.token_baseline_learner.update_multidim(
                    timing_analysis, model_name,
                    emotional_state or "neutral", primary_state
                )
                self.metrics["baseline_updates"] += 1

            # Step 11: Detect anomalies (adaptive sensitivity - FORGE enhanced)
            anomaly = None
            if self.phase4_config.get("token_analytics", "anomaly_detection_enabled"):
                baseline = self.token_baseline_learner.get_multidim_baseline(
                    model_name, emotional_state or "neutral", primary_state
                )
                sensitivity = self.model_profiler.get_sensitivity_threshold(
                    self.sensitivity_level
                )
                anomaly = self.token_anomaly_detector.detect_adaptive(
                    timing_analysis, baseline, sensitivity
                )
                if anomaly:
                    self.metrics["anomalies_detected"] += 1
                    logging.warning(f"[TokenAnalytics] Anomaly detected: {anomaly.anomaly_type}")

            # Step 12: Store in database
            self.token_db.store_token_events(token_events)
            if emotion_corr:
                self.token_db.store_emotion_correlation(emotion_corr)
                self.metrics["emotion_correlations"] += 1
            if hardware_corr:
                self.token_db.store_hardware_correlation(hardware_corr)
                self.metrics["hardware_correlations"] += 1
            if cost_record:
                self.token_db.store_cost(cost_record)
            if gen_states:
                self.token_db.store_generation_states(gen_states, session_id, model_name)
            if state_transitions:
                self.token_db.store_transitions(
                    state_transitions, session_id, model_name, emotional_state
                )

            # Update metrics
            self.metrics["tokens_captured"] += len(token_events)
            self.metrics["sessions_analyzed"] += 1

            # TimeSync: Analysis duration
            analysis_duration_ms = (time.time() - analysis_start) * 1000

            # Return analysis results (FORGE enhanced)
            return {
                "session_id": session_id,
                "model_name": model_name,
                "model_profile": asdict(model_profile),
                "timing": asdict(timing_analysis),
                "pauses": [asdict(p) for p in pauses],
                "curve_segments": [asdict(s) for s in curve_segments],
                "emotion_correlation": asdict(emotion_corr) if emotion_corr else None,
                "hardware_correlation": asdict(hardware_corr) if hardware_corr else None,
                "generation_states": [asdict(gs) for gs in gen_states],
                "state_transitions": [asdict(st) for st in state_transitions],
                "state_summary": state_summary,
                "cost": asdict(cost_record) if cost_record else None,
                "anomaly": asdict(anomaly) if anomaly else None,
                "sensitivity_level": self.sensitivity_level,
                "analysis_duration_ms": analysis_duration_ms,
                "metrics": self.metrics.copy()
            }
            
        except Exception as e:
            logging.error(f"[TokenAnalytics] Analysis failed: {e}")
            return {"error": str(e)}
    
    def stop(self):
        """Stop daemon and flush buffers."""
        logging.info("[TokenAnalyticsDaemon] Stopping...")
        self.running = False
        
        # Flush all buffers
        if hasattr(self, 'token_db'):
            self.token_db.flush_all()
        
        # Stop Phase 3 if available
        if HARDWARESOUL_AVAILABLE and hasattr(super(), 'stop'):
            super().stop()
        
        logging.info("[TokenAnalyticsDaemon] Stopped")
    
    def get_version(self) -> str:
        """Get version string."""
        return "4.0.0"


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="VitalHeart Phase 4: Token Analytics")
    parser.add_argument("--config", type=str, help="Path to config file")
    parser.add_argument("--test-prompt", type=str, help="Test prompt for analysis")
    parser.add_argument("--emotion", type=str, help="Emotion state for test")
    
    args = parser.parse_args()
    
    # Initialize daemon
    daemon = TokenAnalyticsDaemon(config_path=args.config)
    
    # Test mode (single prompt analysis)
    if args.test_prompt:
        session_id = f"test_{int(time.time())}"
        result = daemon.analyze_prompt(args.test_prompt, session_id, args.emotion)
        print(json.dumps(result, indent=2))
    else:
        # Daemon mode (continuous monitoring)
        daemon.start()
