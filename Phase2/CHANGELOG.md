# Changelog

All notable changes to VitalHeart will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0] - 2026-02-13

### Added - Phase 2: InferencePulse

#### Core Features
- **Chat Response Monitoring:** Real-time monitoring of Lumina chat responses via log file parsing
- **Baseline Learning:** Performance baseline calculation from 100+ historical samples
- **Anomaly Detection:** Deviation detection with configurable thresholds (default 2.0x)
- **Mood Analysis:** Emotional texture extraction with 10 dimensions via EmotionalTextureAnalyzer
- **UKE Knowledge Indexing:** Full event indexing to UKE database with batching
- **Enhanced Heartbeat:** Extended AgentHeartbeat with 11 new Phase 2 metrics

#### Components
- `ChatResponseHook` - Log file monitoring for chat responses
- `MoodAnalyzer` - Emotional analysis wrapper with error handling
- `BaselineLearner` - Statistical baseline calculation (mean, median, std_dev, percentiles)
- `AnomalyDetector` - Threshold-based anomaly detection with severity levels
- `UKEConnector` - Batched event indexing with fallback to JSONL
- `EnhancedHeartbeatEmitter` - Extended metrics emission
- `InferencePulseDaemon` - Main orchestrator extending Phase 1

#### Metrics
- `chat_response_ms` - Lumina response latency
- `tokens_generated` - Token count per response
- `tokens_per_second` - Token generation rate
- `mood` - Dominant emotional mood (10 dimensions)
- `mood_intensity` - Mood strength (0-1)
- `baseline_confidence` - Baseline reliability (0-1)
- `anomaly_detected` - Anomaly detection flag
- `anomaly_count_today` - Daily anomaly counter
- `anomaly_severity` - LOW/MEDIUM/HIGH/CRITICAL
- `anomaly_type` - Specific anomaly category

#### Configuration
- `inferencepulse` config section (15 parameters)
- `uke` config section (6 parameters)
- Backward compatible with Phase 1 config

#### Testing
- 36 Phase 2 tests (100% pass rate)
- 72 Phase 1 regression tests (100% pass rate)
- 108 total tests passing
- Bug Hunt Protocol applied: 2 bugs found and fixed

#### Documentation
- README.md (600+ lines)
- BUILD_COVERAGE_PLAN_PHASE2.md (250+ lines)
- BUILD_AUDIT_PHASE2.md (350+ lines)
- ARCHITECTURE_DESIGN_PHASE2.md (650+ lines)
- BUG_HUNT_REPORT_PHASE2.md (200+ lines)
- QUALITY_GATES_REPORT.md (350+ lines)
- BUILD_REPORT.md (250+ lines)
- DEPLOYMENT.md (150+ lines)
- Total: 3,500+ lines of documentation

#### Tools Integrated
- **NEW:** EmotionalTextureAnalyzer, ConversationAuditor, TaskQueuePro
- **UPGRADED:** KnowledgeSync (full UKE implementation)
- **EXTENDED:** 31 Phase 1 tools (AgentHeartbeat, RestCLI, etc.)
- **Total:** 35 tools integrated

### Changed
- Extended `OllamaGuardDaemon` via inheritance
- AgentHeartbeat schema extended with Phase 2 metrics
- Daemon now runs Phase 1 + Phase 2 concurrently

### Fixed
- **BH-P2-001:** UKE fallback test (LOW severity) - Test cleanup issue
- **BH-P2-002:** Tempfile mode error (LOW severity) - Binary vs text mode

### Performance
- Chat hook overhead: ~15ms (target <50ms) ✅
- Mood analysis: ~100ms (target <5s) ✅
- Baseline calculation: ~800ms (target <2s) ✅
- Anomaly detection: ~10ms (target <100ms) ✅
- UKE batch write: ~150ms (target <500ms) ✅
- RAM usage: 60MB (Phase 1: 35MB, Delta: +25MB)
- CPU idle: 0.5% (Phase 1: 0.3%, Delta: +0.2%)

### Dependencies
- No new dependencies (Phase 1 dependencies sufficient)
- Requires Phase 1 (OllamaGuard v1.0.0)

### Deployment
- Phase 1 backward compatible
- Can disable Phase 2 via config (`enabled: false`)
- Deployment ready, quality gates passed (6/6)

---

## [1.0.0] - 2026-02-13

### Added - Phase 1: OllamaGuard

#### Core Features
- Ollama health monitoring (inference test, not just HTTP)
- Auto-restart on failures (exponential backoff)
- Model reload capability
- Process management (psutil)
- AgentHeartbeat persistence
- LiveAudit logging

#### Components
- `OllamaGuardConfig` - Configuration manager
- `OllamaHealthChecker` - Health check with micro-inference test
- `ModelReloader` - Model reload on demand
- `OllamaProcessManager` - Process monitoring and restart
- `RestartStrategyManager` - Exponential backoff strategy
- `HeartbeatEmitter` - AgentHeartbeat integration
- `OllamaGuardDaemon` - Main daemon orchestrator

#### Metrics
- `health_status` - active/waiting/error/offline/grace_period
- `inference_latency_ms` - Ollama inference timing
- `model_loaded` - Model loaded status
- `vram_pct` - VRAM usage percentage
- `ollama_version` - Ollama version tracking
- `restart_count_today` - Daily restart counter

#### Configuration
- `ollama` config section (5 parameters)
- `restart` config section (5 parameters)
- `monitoring` config section (3 parameters)
- `integration` config section (4 parameters)
- `logging` config section (4 parameters)

#### Testing
- 72 tests (100% pass rate)
- Bug Hunt Protocol applied: 2 bugs found and fixed
  - BH-001: Reload test assertion (assert 0.0 >= 0 vs assert 0.0 > 0)
  - BH-002: Inference error JSON parsing (false positive on error responses)

#### Documentation
- README.md (613 lines)
- EXAMPLES.md (18 examples)
- CHEAT_SHEET.txt (200 lines)
- BUILD_COVERAGE_PLAN.md
- BUILD_AUDIT.md (94 tools reviewed, 31 selected)
- ARCHITECTURE_DESIGN.md

#### Tools Integrated
- 31 Team Brain tools (ToolRegistry, ToolSentinel, ConfigManager, etc.)

### Dependencies
- `requests>=2.31.0`
- `psutil>=5.9.0`
- `pynvml>=11.5.0`

### Performance
- RAM usage: 35MB
- CPU idle: 0.3%
- CPU active: 2.1%
- Check cycle: 60s (configurable)

---

## Future Phases

### [3.0.0] - Phase 3: HardwareSoul (Planned)
- High-resolution GPU/RAM/Voltage monitoring
- Hardware-inference correlation
- Real-time hardware health metrics

### [4.0.0] - Phase 4: Emotion-Hardware Correlation (Planned)
- Statistical analysis of mood vs performance
- Predictive models for hardware stress
- Research database integration

### [5.0.0] - Phase 5: HeartWidget (Planned)
- 3D desktop visualization (IRIS builds)
- Real-time heartbeat display
- Interactive anomaly alerts

---

**Maintained by:** ATLAS (C_Atlas)  
**Team:** Team Brain  
**Project:** VitalHeart  

*"Quality is not an act, it is a habit!"* ⚛️⚔️
