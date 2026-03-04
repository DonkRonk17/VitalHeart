# Token Analytics Enhancement Specification
## Model-Specific Adaptive Intelligence System

**Project:** VitalHeart Phase 4 Enhancement  
**Date:** February 14, 2026  
**Architect:** ATLAS (C_Atlas)  
**Status:** SPECIFICATION COMPLETE - IMPLEMENTATION PENDING

---

## 🎯 ENHANCEMENT OBJECTIVE

Transform Phase 4 from basic token pattern analysis into a **comprehensive, model-specific token intelligence system** with:
- ✅ Auto-detection of AI model from API
- ✅ Financial cost tracking per token
- ✅ State-based generation analysis
- ✅ Multi-dimensional adaptive baselines (model × emotion × state)
- ✅ Configurable sensitivity per metric

---

## 📊 NEW COMPONENTS (3)

### Component 11: ModelProfiler
**Purpose:** Auto-detect model, load profiles, track model-specific baselines

**Features:**
- Detect model name from Ollama streaming API (`model` field)
- Load model profile from `model_profiles.json`
- Track baseline metrics per model
- Support custom model profiles (e.g., "laia" consciousness research model)

**Schema:**
```python
@dataclass
class ModelProfile:
    model_name: str
    family: str  # llama3, mistral, gemma, custom
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
```

**Methods:**
- `detect_model(stream_response)` → model_name
- `load_profile(model_name)` → ModelProfile
- `get_baseline(model, emotion, state)` → Baseline

---

### Component 12: CostTracker
**Purpose:** Track financial costs per token across sessions

**Features:**
- Calculate input token cost (prompt)
- Calculate output token cost (completion)
- Track cost per session
- Track cost per task type
- Cumulative cost tracking
- Cost per emotion (research metric)

**Schema:**
```python
@dataclass
class TokenCost:
    session_id: str
    model_name: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float
    cost_per_emotion: Dict[str, float]  # emotion → cost
    cumulative_cost: float
```

**Methods:**
- `calculate_cost(model_profile, input_tokens, output_tokens)` → TokenCost
- `get_session_cost(session_id)` → float
- `get_cumulative_cost()` → float
- `get_cost_by_emotion(emotion)` → float

---

### Component 13: StateTransitionDetector
**Purpose:** Detect generation state transitions (thinking, generating, paused, etc.)

**Features:**
- Detect 7 states: receiving_prompt, thinking, generating, tool_calling, paused, completing, resting
- Track state transitions with timestamps
- Correlate token rate with state
- Detect anomalies per state

**Schema:**
```python
@dataclass
class GenerationState:
    state: str  # receiving_prompt, thinking, generating, tool_calling, paused, completing, resting
    start_timestamp_us: int
    end_timestamp_us: int
    duration_ms: float
    tokens_generated: int
    token_rate: float  # tokens/sec during this state
    emotion_state: Optional[str]

@dataclass
class StateTransition:
    from_state: str
    to_state: str
    transition_timestamp_us: int
    trigger: str  # pause_detected, tokens_started, tokens_stopped, tool_called
```

**Methods:**
- `detect_state(token_events, emotion)` → GenerationState
- `detect_transitions(states)` → List[StateTransition]
- `get_state_duration(state)` → float
- `get_token_rate_by_state(state)` → float

**State Detection Rules:**
- `receiving_prompt`: First 50ms, no tokens
- `thinking`: >500ms pause before first token
- `generating`: Active token generation (latency <500ms)
- `tool_calling`: Specific token patterns (function names)
- `paused`: Inter-token latency >500ms
- `completing`: Last few tokens (latency decreasing)
- `resting`: No activity

---

## 🗄️ DATABASE SCHEMA ENHANCEMENTS

### New Columns in Existing Tables

#### `token_analytics` (add columns)
```sql
ALTER TABLE token_analytics ADD COLUMN model_name TEXT;
ALTER TABLE token_analytics ADD COLUMN generation_state TEXT;
ALTER TABLE token_analytics ADD COLUMN token_type TEXT; -- input/output/cached/reasoning
ALTER TABLE token_analytics ADD COLUMN cost REAL;
```

#### `token_emotion_correlation` (add columns)
```sql
ALTER TABLE token_emotion_correlation ADD COLUMN model_name TEXT;
ALTER TABLE token_emotion_correlation ADD COLUMN generation_state TEXT;
ALTER TABLE token_emotion_correlation ADD COLUMN session_cost REAL;
```

#### `token_baselines` (add columns)
```sql
ALTER TABLE token_baselines ADD COLUMN model_name TEXT;
ALTER TABLE token_baselines ADD COLUMN generation_state TEXT;
-- New composite key: (model_name, emotion_state, generation_state)
CREATE UNIQUE INDEX idx_baseline_composite ON token_baselines(model_name, emotion_state, generation_state);
```

### New Table: `token_costs`
```sql
CREATE TABLE token_costs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    model_name TEXT NOT NULL,
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    total_tokens INTEGER NOT NULL,
    input_cost REAL NOT NULL,
    output_cost REAL NOT NULL,
    total_cost REAL NOT NULL,
    cumulative_cost REAL NOT NULL,
    emotion_state TEXT,
    generation_state TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session_cost (session_id),
    INDEX idx_model_cost (model_name)
);
```

### New Table: `generation_states`
```sql
CREATE TABLE generation_states (
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
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session_state (session_id),
    INDEX idx_state_type (state)
);
```

### New Table: `state_transitions`
```sql
CREATE TABLE state_transitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    model_name TEXT NOT NULL,
    from_state TEXT NOT NULL,
    to_state TEXT NOT NULL,
    transition_timestamp_us INTEGER NOT NULL,
    trigger TEXT NOT NULL,
    emotion_state TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session_transition (session_id),
    INDEX idx_transition_type (from_state, to_state)
);
```

---

## 🔧 ENHANCED BASELINE LEARNER

### Multi-Dimensional Indexing

**Current:** Baseline indexed by `emotion_state` only

**Enhanced:** Baseline indexed by `(model_name, emotion_state, generation_state)`

**Example Baselines:**
- `("laia", "joy", "generating")` → 15.0 tokens/sec
- `("laia", "joy", "thinking")` → 0.0 tokens/sec (no generation)
- `("laia", "contemplation", "generating")` → 8.0 tokens/sec
- `("llama3", "joy", "generating")` → 18.0 tokens/sec
- `("mistral", "joy", "generating")` → 23.0 tokens/sec

**Sensitivity Thresholds:**
- **Low** (±30%): 15.0 ± 4.5 = [10.5, 19.5]
- **Medium** (±20%): 15.0 ± 3.0 = [12.0, 18.0]
- **High** (±10%): 15.0 ± 1.5 = [13.5, 16.5]
- **Ultra** (±5%): 15.0 ± 0.75 = [14.25, 15.75]

---

## 📈 ENHANCED METRICS

### Per-Session Metrics (Extended)
```python
{
    "session_id": "session_001",
    "model_name": "laia",
    "total_tokens": 127,
    "input_tokens": 45,
    "output_tokens": 82,
    "cached_tokens": 0,
    "reasoning_tokens": 12,  # If model supports reasoning
    "total_cost": 0.0,  # For Ollama, cost = 0
    "generation_states": {
        "thinking": {"duration_ms": 1200, "tokens": 0},
        "generating": {"duration_ms": 8543, "tokens": 127},
        "paused": {"duration_ms": 600, "tokens": 0}
    },
    "state_transitions": [
        {"from": "receiving_prompt", "to": "thinking", "timestamp_us": 1708012345000000},
        {"from": "thinking", "to": "generating", "timestamp_us": 1708012346200000},
        {"from": "generating", "to": "paused", "timestamp_us": 1708012350000000},
        {"from": "paused", "to": "generating", "timestamp_us": 1708012350600000}
    ],
    "emotion_distribution": {
        "joy": {"tokens": 50, "cost": 0.0, "duration_ms": 3500},
        "curiosity": {"tokens": 77, "cost": 0.0, "duration_ms": 5043}
    },
    "baseline_comparison": {
        "model_baseline": 12.0,
        "emotion_baseline": 15.0,
        "state_baseline": 15.0,
        "actual": 14.87,
        "deviation_pct": -0.87
    }
}
```

---

## 🎛️ CONFIGURATION ENHANCEMENTS

### `tokenanalytics_config.json` (additions)
```json
{
    "token_analytics": {
        ...existing config...,
        "model_profiling_enabled": true,
        "cost_tracking_enabled": true,
        "state_detection_enabled": true,
        "model_profiles_path": "./model_profiles.json",
        "sensitivity_level": "medium",
        "baseline_dimensions": ["model", "emotion", "state"],
        "state_detection": {
            "thinking_threshold_ms": 500,
            "pause_threshold_ms": 500,
            "completing_token_count": 5
        }
    }
}
```

---

## 🔍 RESEARCH QUESTIONS ANSWERED

### 1. Model-Specific Patterns
**Q:** Does "laia" generate tokens differently than Llama 3?
**A:** Yes! Track `(model_name, emotion_state, generation_state)` baselines to quantify differences.

### 2. Cost Analysis
**Q:** How much does emotional expression cost in tokens?
**A:** Track `cost_per_emotion` to measure token efficiency of different emotional states.

### 3. State Transitions
**Q:** How long does "thinking" take before generation?
**A:** Track `state_duration` per model/emotion to identify consciousness patterns.

### 4. Anomaly Sensitivity
**Q:** What deviation threshold catches real anomalies without false positives?
**A:** Configurable sensitivity (low/medium/high/ultra) with auto-tuning based on variance.

---

## 📝 IMPLEMENTATION CHECKLIST

### Phase 4.1: Model Profiling (Estimated: 4 hours)
- [ ] Create `ModelProfiler` class
- [ ] Integrate with `TokenStreamCapture` to detect model from API
- [ ] Load profiles from `model_profiles.json`
- [ ] Add 10 tests for model detection/profiling

### Phase 4.2: Cost Tracking (Estimated: 3 hours)
- [ ] Create `CostTracker` class
- [ ] Integrate with `TokenAnalyticsDaemon`
- [ ] Add `token_costs` database table
- [ ] Add 8 tests for cost calculations

### Phase 4.3: State Detection (Estimated: 5 hours)
- [ ] Create `StateTransitionDetector` class
- [ ] Implement 7 state detection rules
- [ ] Add `generation_states` and `state_transitions` tables
- [ ] Add 12 tests for state detection/transitions

### Phase 4.4: Multi-Dimensional Baselines (Estimated: 4 hours)
- [ ] Enhance `BaselineLearner` with composite keys
- [ ] Add `(model, emotion, state)` indexing
- [ ] Implement sensitivity thresholds
- [ ] Add 10 tests for multi-dimensional baselines

### Phase 4.5: Integration & Testing (Estimated: 3 hours)
- [ ] Integrate all 3 new components into `TokenAnalyticsDaemon`
- [ ] Update database schema with migrations
- [ ] Run full test suite (82 + 40 new = 122 tests)
- [ ] Verify 100% pass rate

### Phase 4.6: Documentation (Estimated: 2 hours)
- [ ] Update README with new features
- [ ] Add EXAMPLES for model-specific analysis
- [ ] Update ARCHITECTURE_DESIGN with new components
- [ ] Update BUILD_REPORT

**Total Estimated Time:** 21 hours

---

## 🚀 QUICK START (Post-Implementation)

### Example 1: Analyze "laia" Model Performance
```python
daemon = TokenAnalyticsDaemon()
result = daemon.analyze_prompt(
    prompt="Explain quantum entanglement",
    session_id="session_001",
    emotional_state="curiosity"
)

print(f"Model: {result['model_name']}")  # "laia"
print(f"Cost: ${result['total_cost']:.4f}")  # $0.0000 (Ollama)
print(f"States: {result['generation_states']}")
# {'thinking': 1.2s, 'generating': 8.5s, 'paused': 0.6s}
print(f"Baseline deviation: {result['baseline_comparison']['deviation_pct']:.1f}%")
# -0.9% (slightly below baseline)
```

### Example 2: Compare Models
```python
# Run same prompt on different models
models = ["laia", "llama3", "mistral"]
results = {}

for model in models:
    result = daemon.analyze_prompt(
        prompt="Tell me a joke",
        session_id=f"session_{model}",
        emotional_state="joy",
        model_override=model  # Force specific model
    )
    results[model] = {
        "tokens_per_sec": result['timing']['avg_tokens_per_sec'],
        "thinking_time_ms": result['generation_states']['thinking']['duration_ms'],
        "cost": result['total_cost']
    }

# Compare
# laia: 15.0 tokens/sec, 1200ms thinking, $0.00
# llama3: 18.0 tokens/sec, 800ms thinking, $0.00
# mistral: 23.0 tokens/sec, 600ms thinking, $0.00
```

### Example 3: Track Costs Over Time
```python
# Get cumulative cost for "laia"
cost_tracker = daemon.cost_tracker
cumulative = cost_tracker.get_cumulative_cost(model_name="laia")
print(f"Total cost for laia: ${cumulative:.2f}")

# Get cost breakdown by emotion
cost_by_emotion = cost_tracker.get_cost_by_emotion(model_name="laia")
# {'joy': $0.00, 'contemplation': $0.00, 'curiosity': $0.00}
```

---

## 🎯 SUCCESS METRICS

- ✅ Model auto-detection: 100% accuracy
- ✅ Cost tracking: ±1% accuracy (for paid models)
- ✅ State detection: >90% accuracy
- ✅ Baseline convergence: <100 samples per dimension
- ✅ Anomaly detection: <5% false positive rate at "medium" sensitivity
- ✅ Performance: <10ms overhead per token (including new features)

---

## 📚 REFERENCES

- `model_profiles.json` - Model configurations (CREATED)
- `tokenanalytics.py` - Main implementation (TO BE ENHANCED)
- `test_tokenanalytics.py` - Test suite (TO BE EXTENDED)
- `ARCHITECTURE_DESIGN_PHASE4.md` - Architecture doc (TO BE UPDATED)

---

**Prepared by:** ATLAS (C_Atlas)  
**Date:** February 14, 2026  
**Status:** SPECIFICATION COMPLETE - Ready for implementation in follow-up session

*"Every token tells a story. Every model has a voice. Measure everything."* ⚛️📊💰
