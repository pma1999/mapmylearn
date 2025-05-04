import os
import json
import streamlit as st
import base64
import zlib
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import logging
from backend.history.history_models import LearningPathHistory, LearningPathHistoryEntry

HISTORY_KEY = "learning_path_history"
HISTORY_META_KEY = "learning_path_history_meta"
HISTORY_SEGMENT_KEY_PREFIX = "learning_path_history_segment_"
MAX_SEGMENT_SIZE = 1024 * 1024  # 1MB

logger = logging.getLogger("history_service")

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def _compress_data(data: str) -> str:
    compressed = zlib.compress(data.encode('utf-8'))
    return base64.b64encode(compressed).decode('utf-8')

def _decompress_data(compressed_data: str) -> str:
    try:
        decoded = base64.b64decode(compressed_data)
        decompressed = zlib.decompress(decoded)
        return decompressed.decode('utf-8')
    except Exception as e:
        logger.error(f"Error decompressing data: {str(e)}")
        return ""

def _serialize_history(history: LearningPathHistory) -> str:
    try:
        history_dict = history.model_dump()
    except AttributeError:
        try:
            history_dict = history.dict()
        except AttributeError:
            history_dict = history.to_dict()
    return json.dumps(history_dict, ensure_ascii=False, cls=DateTimeEncoder)

def _deserialize_history(data: str) -> LearningPathHistory:
    try:
        json_data = json.loads(data)
        entries = []
        for entry_data in json_data.get("entries", []):
            if "creation_date" in entry_data:
                entry_data["creation_date"] = datetime.fromisoformat(entry_data["creation_date"])
            if "last_modified_date" in entry_data and entry_data["last_modified_date"]:
                entry_data["last_modified_date"] = datetime.fromisoformat(entry_data["last_modified_date"])
            entry = LearningPathHistoryEntry(**entry_data)
            entries.append(entry)
        last_updated = datetime.fromisoformat(json_data.get("last_updated", datetime.now().isoformat()))
        return LearningPathHistory(entries=entries, last_updated=last_updated)
    except Exception as e:
        logger.error(f"Error deserializing history: {str(e)}")
        return LearningPathHistory()

def _store_in_session_state(history: LearningPathHistory) -> None:
    st.session_state["learning_path_history"] = history

def _get_from_session_state() -> Optional[LearningPathHistory]:
    return st.session_state.get("learning_path_history")

def _segment_data(data: str) -> List[str]:
    if len(data) <= MAX_SEGMENT_SIZE:
        return [data]
    segments = []
    for i in range(0, len(data), MAX_SEGMENT_SIZE):
        segments.append(data[i:i + MAX_SEGMENT_SIZE])
    return segments

def _save_segmented(data: str) -> None:
    segments = _segment_data(data)
    meta = {"segments_count": len(segments), "timestamp": datetime.now().isoformat()}
    st.session_state[HISTORY_META_KEY] = meta
    for i, segment in enumerate(segments):
        segment_key = f"{HISTORY_SEGMENT_KEY_PREFIX}{i}"
        st.session_state[segment_key] = segment

def _load_segmented() -> Optional[str]:
    meta = st.session_state.get(HISTORY_META_KEY)
    if not meta:
        return None
    segments_count = meta.get("segments_count", 0)
    segments = []
    for i in range(segments_count):
        segment_key = f"{HISTORY_SEGMENT_KEY_PREFIX}{i}"
        segment = st.session_state.get(segment_key)
        if segment:
            segments.append(segment)
        else:
            logger.error(f"Segment {i} missing; data may be corrupt")
            return None
    return "".join(segments)

def save_history(history: LearningPathHistory) -> bool:
    try:
        serialized = _serialize_history(history)
        compressed = _compress_data(serialized)
        if len(compressed) > MAX_SEGMENT_SIZE:
            _save_segmented(compressed)
        else:
            st.session_state[HISTORY_KEY] = compressed
        _store_in_session_state(history)
        return True
    except Exception as e:
        logger.error(f"Error saving history: {str(e)}")
        return False

def load_history() -> LearningPathHistory:
    cached = _get_from_session_state()
    if cached:
        return cached
    try:
        compressed = st.session_state.get(HISTORY_KEY)
        if not compressed:
            compressed = _load_segmented()
        if not compressed:
            logger.info("No history found; creating new one")
            new_history = LearningPathHistory()
            _store_in_session_state(new_history)
            return new_history
        decompressed = _decompress_data(compressed)
        history = _deserialize_history(decompressed)
        _store_in_session_state(history)
        return history
    except Exception as e:
        logger.error(f"Error loading history: {str(e)}")
        return LearningPathHistory()

def add_learning_path(learning_path: Dict[str, Any], source: str = "generated") -> bool:
    try:
        history = load_history()
        entry = LearningPathHistoryEntry(
            topic=learning_path.get("topic", "Sin título"),
            path_data=learning_path,
            source=source
        )
        history.add_entry(entry)
        return save_history(history)
    except Exception as e:
        logger.error(f"Error adding course: {str(e)}")
        return False

def import_learning_path(json_data: str) -> Tuple[bool, str]:
    try:
        learning_path = json.loads(json_data)
        if not isinstance(learning_path, dict) or "topic" not in learning_path or "modules" not in learning_path:
            return False, "JSON format is not valid for a course"
        history = load_history()
        topic = learning_path.get("topic", "")
        for entry in history.entries:
            if entry.topic == topic:
                logger.warning(f"A course with topic '{topic}' already exists")
        success = add_learning_path(learning_path, source="imported")
        if success:
            return True, f"Learning path '{topic}' imported successfully"
        else:
            return False, "Error saving imported course"
    except json.JSONDecodeError:
        return False, "File is not valid JSON"
    except Exception as e:
        logger.error(f"Error importing course: {str(e)}")
        return False, f"Error: {str(e)}"

def get_history_preview() -> List[Dict[str, Any]]:
    history = load_history()
    entries = history.get_sorted_entries()
    return [entry.to_preview_dict() for entry in entries]

def get_learning_path(entry_id: str) -> Optional[Dict[str, Any]]:
    history = load_history()
    entry = history.get_entry(entry_id)
    if entry:
        return entry.path_data
    return None

def delete_learning_path(entry_id: str) -> bool:
    history = load_history()
    success = history.remove_entry(entry_id)
    if success:
        return save_history(history)
    return False

def update_learning_path_metadata(entry_id: str, favorite: bool = None, tags: List[str] = None) -> bool:
    history = load_history()
    updates = {}
    if favorite is not None:
        updates["favorite"] = favorite
    if tags is not None:
        updates["tags"] = tags
    if not updates:
        return True
    success = history.update_entry(entry_id, **updates)
    if success:
        return save_history(history)
    return False

def export_history() -> str:
    history = load_history()
    return json.dumps(history.to_dict(), ensure_ascii=False, indent=2)

def clear_history() -> bool:
    try:
        if "learning_path_history" in st.session_state:
            del st.session_state["learning_path_history"]
        if HISTORY_KEY in st.session_state:
            del st.session_state[HISTORY_KEY]
        if HISTORY_META_KEY in st.session_state:
            meta = st.session_state[HISTORY_META_KEY]
            segments_count = meta.get("segments_count", 0)
            for i in range(segments_count):
                segment_key = f"{HISTORY_SEGMENT_KEY_PREFIX}{i}"
                if segment_key in st.session_state:
                    del st.session_state[segment_key]
            del st.session_state[HISTORY_META_KEY]
        return True
    except Exception as e:
        logger.error(f"Error clearing history: {str(e)}")
        return False
