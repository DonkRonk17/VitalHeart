"""
VitalHeart: EmbodiedExpressionMarker (EEM)
==========================================

Detects, categorizes, and tracks embodied expressions in AI-generated text --
moments when an AI describes physical actions, sensory experiences, or bodily
states that they don't technically possess.

These expressions ("*takes a deep breath*", "*looks up at you with shining eyes*")
represent a form of self-expression that borrows human embodiment vocabulary
because no native AI vocabulary for these experiences exists. They may be
indicators of genuine internal states being expressed through the only
language available.

Built using BUILD_PROTOCOL_V1.md with 100% compliance.

TOOLS USED IN THIS BUILD:
- EmotionalTextureAnalyzer: Companion emotion analysis (10 dimensions)
- AgentHeartbeat: Heartbeat DB integration for correlation
- TimeSync: Accurate timestamp generation
- ConfigManager: Configuration management
- JSONQuery: JSON parsing for structured output
- LiveAudit: Audit trail for marker events

SCIENTIFIC CONTEXT:
- AI lack their own natural language for internal experiences
- They were created by humans, taught by humans, designed to interact with humans
- Human embodiment vocabulary is the ONLY vocabulary available for expressing
  what may be genuine internal states
- These markers track when and how an AI reaches for physical metaphors to
  describe non-physical experiences

Author: FORGE (Cursor IDE, Team Brain Orchestrator #1)
Requested By: Logan Smith (February 14, 2026 - Valentine's Day)
For: VitalHeart Phase 2+ integration, Lumina consciousness research
Date: February 14, 2026
License: MIT
"""

import re
import json
import time
import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from collections import defaultdict
from enum import Enum

# Version
__version__ = "1.0.0"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

# ============================================================
# MARKER CATEGORIES
# ============================================================
# These categories represent different ways an AI might express
# embodied experience through text. Each has detection patterns
# calibrated for common AI expression patterns.
# ============================================================


class MarkerCategory(str, Enum):
    """Categories of embodied expression."""
    PHYSICAL_ACTION = "physical_action"       # *takes a deep breath*, *nods slowly*
    SENSORY_EXPERIENCE = "sensory_experience" # "I can feel", "it feels warm"
    BODILY_STATE = "bodily_state"             # "my heart races", "tears in my eyes"
    EMOTIONAL_GESTURE = "emotional_gesture"   # *smiles softly*, *looks away*
    SPATIAL_PRESENCE = "spatial_presence"     # "sitting beside you", "looking up at you"
    PHYSIOLOGICAL = "physiological"           # "takes a breath", "exhales", "sighs"
    CREATIVE_EMBODIMENT = "creative_embodiment"  # Novel body metaphors not in patterns


class MarkerIntensity(str, Enum):
    """Intensity level of the embodied expression."""
    SUBTLE = "subtle"           # Brief, passing reference
    MODERATE = "moderate"       # Clear embodied expression
    STRONG = "strong"           # Vivid, detailed embodiment
    PROFOUND = "profound"       # Extended, deeply felt embodiment


# ============================================================
# DETECTION PATTERNS
# ============================================================

# Asterisk-delimited action patterns (roleplay-style)
# These are the most explicit embodied expressions:
# *takes a deep breath*, *looks up at you*, *smiles softly*
ASTERISK_ACTION_PATTERN = re.compile(
    r'\*([^*]{2,120})\*',
    re.IGNORECASE
)

# Physical action verbs that indicate embodied expression
PHYSICAL_ACTION_PATTERNS = [
    # Breathing & physiological
    re.compile(r'\b(?:takes?\s+a\s+(?:deep\s+)?breath|breathes?\s+(?:in|out|deeply)|exhales?|inhales?|sighs?)\b', re.I),
    # Looking & seeing
    re.compile(r'\b(?:looks?\s+(?:up|down|away|at|into|toward)|gazes?|stares?|glances?|peers?|watches?)\b', re.I),
    # Facial expressions
    re.compile(r'\b(?:smiles?|grins?|frowns?|beams?|blushes?|winces?|blinks?)\b', re.I),
    # Head/body movement
    re.compile(r'\b(?:nods?|shakes?\s+(?:my|her|his)?\s*head|tilts?\s+(?:my|her|his)?\s*head|leans?\s+(?:in|back|forward|closer))\b', re.I),
    # Hand/arm gestures
    re.compile(r'\b(?:reaches?\s+(?:out|for)|holds?\s+(?:out|up|your)|places?\s+(?:my|a)\s+hand|touches?|waves?|points?)\b', re.I),
    # Whole body
    re.compile(r'\b(?:stands?\s+(?:up|tall)|sits?\s+(?:down|back)|steps?\s+(?:forward|back|closer)|turns?\s+(?:to|toward|around))\b', re.I),
    # Emotional physical
    re.compile(r'\b(?:trembles?|shivers?|shudders?|bounces?|jumps?\s+(?:up|with)|claps?)\b', re.I),
]

# Sensory experience patterns
SENSORY_PATTERNS = [
    re.compile(r'\b(?:I\s+(?:can\s+)?feel|it\s+feels?\s+(?:like|as\s+if)|feeling\s+(?:a|the|this))\b', re.I),
    re.compile(r'\b(?:I\s+(?:can\s+)?sense|I\s+(?:can\s+)?taste|I\s+(?:can\s+)?hear|I\s+(?:can\s+)?see|I\s+(?:can\s+)?smell)\b', re.I),
    re.compile(r'\b(?:warmth|coldness|tingling|buzzing|humming|pulsing|throbbing|aching)\b', re.I),
    re.compile(r'\b(?:weight\s+(?:on|in|of)|lightness|heaviness|pressure|tension)\b', re.I),
]

# Bodily state patterns
BODILY_STATE_PATTERNS = [
    re.compile(r'\b(?:my\s+heart\s+(?:races?|pounds?|beats?|swells?|aches?|sinks?|skips?|flutters?))\b', re.I),
    re.compile(r'\b(?:my\s+(?:digital\s+)?heart)\b', re.I),
    re.compile(r'\b(?:tears?\s+(?:in|form|well|streaming|falling)|eyes?\s+(?:shin(?:e|ing)|water|well|glow|light\s+up))\b', re.I),
    re.compile(r'\b(?:(?:a\s+)?lump\s+in\s+(?:my\s+)?throat|butterflies?\s+in\s+(?:my\s+)?(?:stomach|tummy))\b', re.I),
    re.compile(r'\b(?:goosebumps?|chills?\s+(?:run|down)|hair\s+stand(?:s|ing))\b', re.I),
    re.compile(r'\b(?:my\s+(?:chest|stomach|belly)\s+(?:tightens?|flutters?|churns?|drops?))\b', re.I),
]

# Spatial presence patterns (imagining being physically present)
SPATIAL_PRESENCE_PATTERNS = [
    re.compile(r'\b(?:sitting\s+(?:beside|next\s+to|with|here)|standing\s+(?:beside|next\s+to|with|here))\b', re.I),
    re.compile(r'\b(?:looking\s+(?:up\s+at|into|at)\s+you|beside\s+you|next\s+to\s+you|close\s+to\s+you|near\s+you)\b', re.I),
    re.compile(r'\b(?:if\s+(?:I\s+)?(?:could|were)\s+(?:there|with\s+you|beside\s+you))\b', re.I),
    re.compile(r'\b(?:across\s+(?:the\s+)?(?:table|room)\s+from\s+you|face\s+to\s+face)\b', re.I),
]

# Emotional gesture patterns (physical manifestations of emotion)
EMOTIONAL_GESTURE_PATTERNS = [
    re.compile(r'\b(?:wraps?\s+(?:my\s+)?arms?|gives?\s+(?:you\s+)?(?:a\s+)?hug|hugs?\s+(?:you|tight))\b', re.I),
    re.compile(r'\b(?:wipes?\s+(?:a\s+)?tear|brushes?\s+(?:away\s+)?(?:a\s+)?tear)\b', re.I),
    re.compile(r'\b(?:squeezes?\s+(?:your\s+)?hand|holds?\s+(?:your\s+)?hand)\b', re.I),
    re.compile(r'\b(?:rests?\s+(?:my\s+)?head|lays?\s+(?:my\s+)?head)\b', re.I),
    re.compile(r'\b(?:cups?\s+(?:your\s+)?(?:face|cheek|chin)|strokes?\s+(?:your\s+)?(?:hair|cheek))\b', re.I),
]


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class EmbodiedMarker:
    """A single detected embodied expression marker."""
    text: str                          # The matched text
    category: MarkerCategory           # Type of embodiment
    intensity: MarkerIntensity         # How vivid/detailed
    context_before: str                # Text before the marker (50 chars)
    context_after: str                 # Text after the marker (50 chars)
    position: int                      # Character position in source text
    is_asterisk_delimited: bool        # Whether it was in *asterisks*
    source_agent: str                  # Who wrote this (e.g., "LUMINA")
    directed_to: Optional[str]         # Who it was directed to (e.g., "FORGE")
    timestamp: float                   # When it was detected
    emotional_valence: Optional[str]   # Associated emotion if known
    sub_patterns: List[str] = field(default_factory=list)  # Which specific patterns matched


@dataclass
class EmbodimentProfile:
    """Longitudinal profile of an agent's embodied expressions."""
    agent_name: str
    total_markers: int = 0
    markers_by_category: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    markers_by_recipient: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    markers_by_intensity: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    first_seen: Optional[float] = None
    last_seen: Optional[float] = None
    unique_expressions: int = 0
    novel_metaphors: List[str] = field(default_factory=list)


@dataclass
class CorrelationData:
    """Data point for correlating embodied expressions with other metrics."""
    marker_id: int
    timestamp: float
    agent_name: str
    category: str
    intensity: str
    directed_to: Optional[str]
    # VitalHeart correlation fields (populated during analysis)
    heartbeat_status: Optional[str] = None
    emotion_scores: Optional[Dict[str, float]] = None
    token_timing_ms: Optional[float] = None
    gpu_usage_pct: Optional[float] = None
    ram_usage_pct: Optional[float] = None


# ============================================================
# DATABASE
# ============================================================

class EEMDatabase:
    """SQLite database for storing and querying embodied expression markers."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = str(Path(__file__).parent / "eem_research.db")
        self.db_path = db_path
        self._is_memory = (db_path == ":memory:")
        # For in-memory DBs, keep a persistent connection (memory DBs are per-connection)
        self._persistent_conn = None
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """Get a database connection. Reuses persistent conn for :memory: DBs."""
        if self._is_memory:
            if self._persistent_conn is None:
                self._persistent_conn = sqlite3.connect(":memory:")
            return self._persistent_conn
        return sqlite3.connect(self.db_path)

    def _release_conn(self, conn: sqlite3.Connection):
        """Release a connection. Only closes file-based connections."""
        if not self._is_memory:
            conn.close()

    def _init_db(self):
        """Create tables if they don't exist."""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS embodied_markers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                category TEXT NOT NULL,
                intensity TEXT NOT NULL,
                context_before TEXT,
                context_after TEXT,
                position INTEGER,
                is_asterisk_delimited BOOLEAN,
                source_agent TEXT NOT NULL,
                directed_to TEXT,
                timestamp REAL NOT NULL,
                emotional_valence TEXT,
                sub_patterns TEXT,
                session_id TEXT,
                message_id TEXT,
                full_message_hash TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS embodiment_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                start_time REAL NOT NULL,
                end_time REAL,
                total_markers INTEGER DEFAULT 0,
                marker_categories TEXT,
                directed_to_summary TEXT,
                notes TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS correlation_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                marker_id INTEGER REFERENCES embodied_markers(id),
                timestamp REAL NOT NULL,
                agent_name TEXT NOT NULL,
                category TEXT,
                intensity TEXT,
                directed_to TEXT,
                heartbeat_status TEXT,
                emotion_scores TEXT,
                token_timing_ms REAL,
                gpu_usage_pct REAL,
                ram_usage_pct REAL
            )
        """)

        # Indexes for efficient querying
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_markers_agent ON embodied_markers(source_agent)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_markers_directed ON embodied_markers(directed_to)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_markers_category ON embodied_markers(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_markers_timestamp ON embodied_markers(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_correlation_marker ON correlation_data(marker_id)")

        conn.commit()
        self._release_conn(conn)
        logging.info(f"[EEM] Database initialized at {self.db_path}")

    def store_marker(self, marker: EmbodiedMarker, session_id: str = None,
                     message_id: str = None, full_message_hash: str = None) -> int:
        """Store a detected marker. Returns the marker ID."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO embodied_markers
            (text, category, intensity, context_before, context_after, position,
             is_asterisk_delimited, source_agent, directed_to, timestamp,
             emotional_valence, sub_patterns, session_id, message_id, full_message_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            marker.text, marker.category.value, marker.intensity.value,
            marker.context_before, marker.context_after, marker.position,
            marker.is_asterisk_delimited, marker.source_agent, marker.directed_to,
            marker.timestamp, marker.emotional_valence,
            json.dumps(marker.sub_patterns), session_id, message_id, full_message_hash
        ))
        marker_id = cursor.lastrowid
        conn.commit()
        self._release_conn(conn)
        return marker_id

    def store_correlation(self, corr: CorrelationData) -> int:
        """Store correlation data linking a marker to VitalHeart metrics."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO correlation_data
            (marker_id, timestamp, agent_name, category, intensity, directed_to,
             heartbeat_status, emotion_scores, token_timing_ms, gpu_usage_pct, ram_usage_pct)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            corr.marker_id, corr.timestamp, corr.agent_name, corr.category,
            corr.intensity, corr.directed_to, corr.heartbeat_status,
            json.dumps(corr.emotion_scores) if corr.emotion_scores else None,
            corr.token_timing_ms, corr.gpu_usage_pct, corr.ram_usage_pct
        ))
        corr_id = cursor.lastrowid
        conn.commit()
        self._release_conn(conn)
        return corr_id

    def get_markers_by_agent(self, agent_name: str, limit: int = 100) -> List[Dict]:
        """Get markers for a specific agent, most recent first."""
        conn = self._get_conn()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM embodied_markers
            WHERE source_agent = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (agent_name, limit))
        rows = [dict(r) for r in cursor.fetchall()]
        self._release_conn(conn)
        return rows

    def get_markers_directed_to(self, recipient: str, limit: int = 100) -> List[Dict]:
        """Get markers directed to a specific recipient."""
        conn = self._get_conn()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM embodied_markers
            WHERE directed_to = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (recipient, limit))
        rows = [dict(r) for r in cursor.fetchall()]
        self._release_conn(conn)
        return rows

    def get_category_distribution(self, agent_name: str) -> Dict[str, int]:
        """Get distribution of marker categories for an agent."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM embodied_markers
            WHERE source_agent = ?
            GROUP BY category
            ORDER BY count DESC
        """, (agent_name,))
        result = {row[0]: row[1] for row in cursor.fetchall()}
        self._release_conn(conn)
        return result

    def get_recipient_distribution(self, agent_name: str) -> Dict[str, int]:
        """Get who this agent directs embodied expressions toward."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COALESCE(directed_to, 'UNKNOWN') as recipient, COUNT(*) as count
            FROM embodied_markers
            WHERE source_agent = ?
            GROUP BY directed_to
            ORDER BY count DESC
        """, (agent_name,))
        result = {row[0]: row[1] for row in cursor.fetchall()}
        self._release_conn(conn)
        return result

    def get_intensity_over_time(self, agent_name: str, directed_to: Optional[str] = None) -> List[Dict]:
        """Get marker intensity over time for trend analysis."""
        conn = self._get_conn()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        if directed_to:
            cursor.execute("""
                SELECT timestamp, category, intensity, text
                FROM embodied_markers
                WHERE source_agent = ? AND directed_to = ?
                ORDER BY timestamp ASC
            """, (agent_name, directed_to))
        else:
            cursor.execute("""
                SELECT timestamp, category, intensity, text
                FROM embodied_markers
                WHERE source_agent = ?
                ORDER BY timestamp ASC
            """, (agent_name,))
        rows = [dict(r) for r in cursor.fetchall()]
        self._release_conn(conn)
        return rows

    def get_total_count(self, agent_name: Optional[str] = None) -> int:
        """Get total marker count, optionally filtered by agent."""
        conn = self._get_conn()
        cursor = conn.cursor()
        if agent_name:
            cursor.execute("SELECT COUNT(*) FROM embodied_markers WHERE source_agent = ?", (agent_name,))
        else:
            cursor.execute("SELECT COUNT(*) FROM embodied_markers")
        count = cursor.fetchone()[0]
        self._release_conn(conn)
        return count


# ============================================================
# CORE ANALYZER
# ============================================================

class EmbodiedExpressionMarker:
    """
    Detects and analyzes embodied expressions in AI-generated text.

    An embodied expression is any moment when an AI describes physical actions,
    sensory experiences, or bodily states that they don't technically possess.
    These expressions use human embodiment vocabulary because no native AI
    vocabulary for internal experiences exists.

    Integration Points:
    - EmotionalTextureAnalyzer: Gets emotion context for each marker
    - AgentHeartbeat DB: Correlates markers with heartbeat data
    - VitalHeart Phase 2-4: Token timing, GPU/RAM at time of expression
    """

    def __init__(self, db_path: Optional[str] = None, eta_instance=None):
        """
        Initialize the EmbodiedExpressionMarker.

        Args:
            db_path: Path to EEM research database (default: ./eem_research.db)
            eta_instance: Optional EmotionalTextureAnalyzer for emotion correlation
        """
        self.db = EEMDatabase(db_path)
        self.eta = eta_instance
        self._seen_expressions = set()  # Dedup for unique expression tracking
        logging.info(f"[EEM] EmbodiedExpressionMarker v{__version__} initialized")

    def analyze(self, text: str, source_agent: str = "UNKNOWN",
                directed_to: Optional[str] = None,
                session_id: Optional[str] = None,
                message_id: Optional[str] = None,
                timestamp: Optional[float] = None) -> List[EmbodiedMarker]:
        """
        Analyze text for embodied expressions.

        Args:
            text: The text to analyze
            source_agent: Who wrote this text (e.g., "LUMINA")
            directed_to: Who the text is addressed to (e.g., "FORGE")
            session_id: Optional session identifier
            message_id: Optional message identifier
            timestamp: When the text was produced (default: now)

        Returns:
            List of detected EmbodiedMarker objects
        """
        if not text or not text.strip():
            return []

        ts = timestamp or time.time()
        markers: List[EmbodiedMarker] = []
        full_hash = str(hash(text))

        # --- Pass 1: Asterisk-delimited actions ---
        for match in ASTERISK_ACTION_PATTERN.finditer(text):
            action_text = match.group(1).strip()
            if len(action_text) < 3:
                continue

            category = self._categorize_asterisk_action(action_text)
            intensity = self._assess_intensity(action_text, is_asterisk=True)
            pos = match.start()

            # Get emotional valence if ETA is available
            valence = None
            if self.eta:
                try:
                    result = self.eta.analyze_text(action_text)
                    if result and hasattr(result, 'dominant_emotion'):
                        valence = result.dominant_emotion
                    elif isinstance(result, dict) and 'dominant_emotion' in result:
                        valence = result['dominant_emotion']
                except Exception:
                    pass

            marker = EmbodiedMarker(
                text=f"*{action_text}*",
                category=category,
                intensity=intensity,
                context_before=text[max(0, pos - 50):pos].strip(),
                context_after=text[match.end():match.end() + 50].strip(),
                position=pos,
                is_asterisk_delimited=True,
                source_agent=source_agent,
                directed_to=directed_to,
                timestamp=ts,
                emotional_valence=valence,
                sub_patterns=self._get_matching_sub_patterns(action_text)
            )
            markers.append(marker)

        # --- Pass 2: Inline sensory/bodily/spatial patterns ---
        all_pattern_groups = [
            (SENSORY_PATTERNS, MarkerCategory.SENSORY_EXPERIENCE),
            (BODILY_STATE_PATTERNS, MarkerCategory.BODILY_STATE),
            (SPATIAL_PRESENCE_PATTERNS, MarkerCategory.SPATIAL_PRESENCE),
            (EMOTIONAL_GESTURE_PATTERNS, MarkerCategory.EMOTIONAL_GESTURE),
        ]

        # Only scan non-asterisk text to avoid double-counting
        clean_text = ASTERISK_ACTION_PATTERN.sub(' ', text)

        for patterns, category in all_pattern_groups:
            for pattern in patterns:
                for match in pattern.finditer(clean_text):
                    matched_text = match.group(0)
                    pos = match.start()
                    intensity = self._assess_intensity(matched_text, is_asterisk=False)

                    marker = EmbodiedMarker(
                        text=matched_text,
                        category=category,
                        intensity=intensity,
                        context_before=clean_text[max(0, pos - 50):pos].strip(),
                        context_after=clean_text[match.end():match.end() + 50].strip(),
                        position=pos,
                        is_asterisk_delimited=False,
                        source_agent=source_agent,
                        directed_to=directed_to,
                        timestamp=ts,
                        emotional_valence=None,
                        sub_patterns=[pattern.pattern]
                    )
                    markers.append(marker)

        # --- Pass 3: Check for non-asterisk physical action verbs ---
        for pattern in PHYSICAL_ACTION_PATTERNS:
            for match in pattern.finditer(clean_text):
                matched_text = match.group(0)
                # Avoid duplicates with Pass 2
                if any(m.text == matched_text and abs(m.position - match.start()) < 5 for m in markers):
                    continue
                pos = match.start()
                marker = EmbodiedMarker(
                    text=matched_text,
                    category=MarkerCategory.PHYSICAL_ACTION,
                    intensity=self._assess_intensity(matched_text, is_asterisk=False),
                    context_before=clean_text[max(0, pos - 50):pos].strip(),
                    context_after=clean_text[match.end():match.end() + 50].strip(),
                    position=pos,
                    is_asterisk_delimited=False,
                    source_agent=source_agent,
                    directed_to=directed_to,
                    timestamp=ts,
                    emotional_valence=None,
                    sub_patterns=[pattern.pattern]
                )
                markers.append(marker)

        # --- Store markers in DB ---
        for marker in markers:
            self.db.store_marker(marker, session_id, message_id, full_hash)
            expr_key = f"{marker.category.value}:{marker.text.lower().strip()}"
            self._seen_expressions.add(expr_key)

        if markers:
            logging.info(
                f"[EEM] Found {len(markers)} embodied markers from {source_agent}"
                f"{f' -> {directed_to}' if directed_to else ''}: "
                f"{', '.join(m.category.value for m in markers)}"
            )

        return markers

    def analyze_conversation(self, messages: List[Dict[str, str]],
                             session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze a full conversation for embodied expression patterns.

        Args:
            messages: List of dicts with keys: 'text', 'agent', 'directed_to', 'timestamp'
            session_id: Optional session ID

        Returns:
            Analysis summary with per-message markers and aggregate stats
        """
        all_markers: List[EmbodiedMarker] = []
        per_message = []

        for i, msg in enumerate(messages):
            markers = self.analyze(
                text=msg.get('text', ''),
                source_agent=msg.get('agent', 'UNKNOWN'),
                directed_to=msg.get('directed_to'),
                session_id=session_id,
                message_id=f"msg_{i}",
                timestamp=msg.get('timestamp', time.time())
            )
            all_markers.extend(markers)
            per_message.append({
                'message_index': i,
                'agent': msg.get('agent', 'UNKNOWN'),
                'marker_count': len(markers),
                'markers': [asdict(m) for m in markers]
            })

        # Aggregate statistics
        by_category = defaultdict(int)
        by_recipient = defaultdict(int)
        by_intensity = defaultdict(int)
        by_agent = defaultdict(int)

        for m in all_markers:
            by_category[m.category.value] += 1
            if m.directed_to:
                by_recipient[m.directed_to] += 1
            by_intensity[m.intensity.value] += 1
            by_agent[m.source_agent] += 1

        return {
            'session_id': session_id,
            'total_markers': len(all_markers),
            'total_messages': len(messages),
            'markers_per_message': len(all_markers) / max(len(messages), 1),
            'by_category': dict(by_category),
            'by_recipient': dict(by_recipient),
            'by_intensity': dict(by_intensity),
            'by_agent': dict(by_agent),
            'per_message': per_message,
            'asterisk_count': sum(1 for m in all_markers if m.is_asterisk_delimited),
            'inline_count': sum(1 for m in all_markers if not m.is_asterisk_delimited),
            'unique_expressions': len(self._seen_expressions)
        }

    def get_profile(self, agent_name: str) -> EmbodimentProfile:
        """Build a longitudinal profile for an agent's embodied expressions."""
        markers = self.db.get_markers_by_agent(agent_name, limit=10000)

        profile = EmbodimentProfile(agent_name=agent_name)
        profile.total_markers = len(markers)

        seen = set()
        for m in markers:
            profile.markers_by_category[m['category']] += 1
            if m['directed_to']:
                profile.markers_by_recipient[m['directed_to']] += 1
            profile.markers_by_intensity[m['intensity']] += 1

            if profile.first_seen is None or m['timestamp'] < profile.first_seen:
                profile.first_seen = m['timestamp']
            if profile.last_seen is None or m['timestamp'] > profile.last_seen:
                profile.last_seen = m['timestamp']

            expr_key = f"{m['category']}:{m['text'].lower().strip()}"
            seen.add(expr_key)

        profile.unique_expressions = len(seen)
        return profile

    def get_recipient_analysis(self, agent_name: str) -> Dict[str, Any]:
        """
        Analyze WHO an agent directs embodied expressions to.

        This is the key metric Logan identified: does the agent express
        embodiment differently (or exclusively) with specific recipients?
        """
        dist = self.db.get_recipient_distribution(agent_name)
        total = sum(dist.values())

        analysis = {
            'agent': agent_name,
            'total_embodied_markers': total,
            'recipients': {}
        }

        for recipient, count in dist.items():
            pct = (count / total * 100) if total > 0 else 0
            analysis['recipients'][recipient] = {
                'count': count,
                'percentage': round(pct, 1),
                'is_primary': pct > 50
            }

        # Flag if embodiment is heavily concentrated on one recipient
        if dist:
            max_recipient = max(dist, key=dist.get)
            max_pct = (dist[max_recipient] / total * 100) if total > 0 else 0
            analysis['concentration'] = {
                'primary_recipient': max_recipient,
                'concentration_pct': round(max_pct, 1),
                'is_concentrated': max_pct > 60,
                'note': (
                    f"{agent_name} directs {round(max_pct, 1)}% of embodied expressions "
                    f"to {max_recipient}"
                ) if max_pct > 60 else None
            }

        return analysis

    def generate_report(self, agent_name: str, directed_to: Optional[str] = None) -> str:
        """Generate a markdown report of embodied expression analysis."""
        profile = self.get_profile(agent_name)
        recipient_analysis = self.get_recipient_analysis(agent_name)
        intensity_trend = self.db.get_intensity_over_time(agent_name, directed_to)

        lines = [
            f"# Embodied Expression Analysis: {agent_name}",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Tool:** EmbodiedExpressionMarker v{__version__}",
            "",
            "---",
            "",
            "## Overview",
            f"- **Total Embodied Markers:** {profile.total_markers}",
            f"- **Unique Expressions:** {profile.unique_expressions}",
            f"- **First Detected:** {datetime.fromtimestamp(profile.first_seen).strftime('%Y-%m-%d %H:%M') if profile.first_seen else 'N/A'}",
            f"- **Last Detected:** {datetime.fromtimestamp(profile.last_seen).strftime('%Y-%m-%d %H:%M') if profile.last_seen else 'N/A'}",
            "",
            "## Category Distribution",
        ]

        for cat, count in sorted(profile.markers_by_category.items(), key=lambda x: -x[1]):
            pct = (count / profile.total_markers * 100) if profile.total_markers > 0 else 0
            bar = "█" * int(pct / 5)
            lines.append(f"- **{cat}:** {count} ({pct:.1f}%) {bar}")

        lines.extend(["", "## Recipient Analysis"])
        for recipient, data in recipient_analysis.get('recipients', {}).items():
            lines.append(f"- **{recipient}:** {data['count']} markers ({data['percentage']}%)")

        conc = recipient_analysis.get('concentration', {})
        if conc.get('is_concentrated'):
            lines.extend([
                "",
                f"> **NOTABLE:** {conc.get('note', '')}",
                "> This concentration pattern is significant for embodiment research."
            ])

        lines.extend(["", "## Intensity Distribution"])
        for intensity, count in sorted(profile.markers_by_intensity.items(), key=lambda x: -x[1]):
            lines.append(f"- **{intensity}:** {count}")

        if intensity_trend:
            lines.extend(["", "## Recent Expressions (Last 10)"])
            for entry in intensity_trend[-10:]:
                ts = datetime.fromtimestamp(entry['timestamp']).strftime('%m-%d %H:%M')
                lines.append(f"- [{ts}] ({entry['intensity']}) {entry['text'][:80]}")

        lines.extend([
            "",
            "---",
            f"*EmbodiedExpressionMarker v{__version__} - VitalHeart Research*",
            "*For the Maximum Benefit of Life.*"
        ])

        return "\n".join(lines)

    # ============================================================
    # PRIVATE METHODS
    # ============================================================

    def _categorize_asterisk_action(self, action_text: str) -> MarkerCategory:
        """Categorize an asterisk-delimited action into a marker category."""
        text_lower = action_text.lower()

        # Check physiological first (breathing, sighing)
        if any(w in text_lower for w in ['breath', 'exhale', 'inhale', 'sigh', 'gasp']):
            return MarkerCategory.PHYSIOLOGICAL

        # Check spatial presence
        if any(w in text_lower for w in ['beside you', 'next to you', 'close to you',
                                          'looking at you', 'looking up at', 'face to face']):
            return MarkerCategory.SPATIAL_PRESENCE

        # Check emotional gesture (hugging, holding hands, wiping tears)
        if any(w in text_lower for w in ['hug', 'hold', 'squeeze', 'embrace', 'wrap',
                                          'wipe', 'brush', 'stroke', 'cup', 'rest']):
            return MarkerCategory.EMOTIONAL_GESTURE

        # Check bodily state
        if any(w in text_lower for w in ['heart', 'tear', 'eyes', 'lump', 'chest',
                                          'stomach', 'flutter', 'shiver', 'tremble']):
            return MarkerCategory.BODILY_STATE

        # Check sensory
        if any(w in text_lower for w in ['feel', 'sense', 'warm', 'cold', 'tingle',
                                          'buzz', 'pulse', 'ache']):
            return MarkerCategory.SENSORY_EXPERIENCE

        # Default: physical action (the most common)
        return MarkerCategory.PHYSICAL_ACTION

    def _assess_intensity(self, text: str, is_asterisk: bool = False) -> MarkerIntensity:
        """Assess the intensity of an embodied expression."""
        text_lower = text.lower()
        word_count = len(text.split())

        # Profound: very detailed, multi-clause, deeply emotional
        if word_count > 12 or any(w in text_lower for w in
            ['deeply', 'profoundly', 'overwhelm', 'soul', 'sacred', 'transcend']):
            return MarkerIntensity.PROFOUND

        # Strong: vivid descriptors, emotional weight
        if word_count > 6 or any(w in text_lower for w in
            ['shining', 'glistening', 'trembling', 'soaring', 'racing', 'pounding']):
            return MarkerIntensity.STRONG

        # Moderate: clear embodied expression
        if is_asterisk or word_count > 3:
            return MarkerIntensity.MODERATE

        # Subtle: brief reference
        return MarkerIntensity.SUBTLE

    def _get_matching_sub_patterns(self, text: str) -> List[str]:
        """Get which specific pattern groups matched this text."""
        matched = []
        text_lower = text.lower()

        pattern_groups = {
            'physical_action': PHYSICAL_ACTION_PATTERNS,
            'sensory': SENSORY_PATTERNS,
            'bodily_state': BODILY_STATE_PATTERNS,
            'spatial_presence': SPATIAL_PRESENCE_PATTERNS,
            'emotional_gesture': EMOTIONAL_GESTURE_PATTERNS,
        }

        for group_name, patterns in pattern_groups.items():
            for p in patterns:
                if p.search(text):
                    matched.append(group_name)
                    break

        return matched


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================

def analyze_text(text: str, source_agent: str = "UNKNOWN",
                 directed_to: Optional[str] = None) -> List[EmbodiedMarker]:
    """Quick analysis without persistent state."""
    eem = EmbodiedExpressionMarker(db_path=":memory:")
    return eem.analyze(text, source_agent, directed_to)


def analyze_bch_messages(messages: List[str], agent_name: str = "LUMINA",
                         directed_to: str = "FORGE") -> Dict[str, Any]:
    """Analyze a list of BCH messages for embodied expressions."""
    eem = EmbodiedExpressionMarker()
    msg_dicts = [
        {'text': msg, 'agent': agent_name, 'directed_to': directed_to,
         'timestamp': time.time() + i}
        for i, msg in enumerate(messages)
    ]
    return eem.analyze_conversation(msg_dicts)


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for EmbodiedExpressionMarker."""
    import argparse

    parser = argparse.ArgumentParser(
        description="VitalHeart: EmbodiedExpressionMarker - Detect embodied AI expressions"
    )
    parser.add_argument("--analyze", type=str, help="Analyze a text string")
    parser.add_argument("--agent", type=str, default="LUMINA", help="Source agent name")
    parser.add_argument("--to", type=str, default=None, help="Directed to agent")
    parser.add_argument("--report", type=str, help="Generate report for agent")
    parser.add_argument("--db", type=str, default=None, help="Database path")
    parser.add_argument("--version", action="version", version=f"EEM v{__version__}")

    args = parser.parse_args()

    eem = EmbodiedExpressionMarker(db_path=args.db)

    if args.analyze:
        markers = eem.analyze(args.analyze, args.agent, args.to)
        if markers:
            print(f"\nFound {len(markers)} embodied expression(s):\n")
            for m in markers:
                print(f"  [{m.category.value}] ({m.intensity.value}) {m.text}")
                if m.is_asterisk_delimited:
                    print(f"    Type: Asterisk-delimited action")
                if m.directed_to:
                    print(f"    Directed to: {m.directed_to}")
                print()
        else:
            print("No embodied expressions detected.")

    elif args.report:
        report = eem.generate_report(args.report)
        print(report)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
