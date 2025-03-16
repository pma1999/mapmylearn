import json
import streamlit as st
import base64
import zlib
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import logging
from history.history_models import LearningPathHistory, LearningPathHistoryEntry

# Configuración de las claves de almacenamiento
HISTORY_KEY = "learning_path_history"
HISTORY_META_KEY = "learning_path_history_meta"
HISTORY_SEGMENT_KEY_PREFIX = "learning_path_history_segment_"

# Tamaño máximo recomendado para un segmento (en bytes)
MAX_SEGMENT_SIZE = 1024 * 1024  # 1MB

# Configuración de logging
logger = logging.getLogger("history_service")

# Clase personalizada para manejar la serialización de objetos datetime
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def _compress_data(data: str) -> str:
    """Comprime una cadena de texto usando zlib y la codifica en base64."""
    compressed = zlib.compress(data.encode('utf-8'))
    return base64.b64encode(compressed).decode('utf-8')

def _decompress_data(compressed_data: str) -> str:
    """Descomprime una cadena codificada en base64 y comprimida con zlib."""
    try:
        decoded = base64.b64decode(compressed_data)
        decompressed = zlib.decompress(decoded)
        return decompressed.decode('utf-8')
    except Exception as e:
        logger.error(f"Error al descomprimir datos: {str(e)}")
        return ""

def _serialize_history(history: LearningPathHistory) -> str:
    """Serializa el historial a formato JSON."""
    try:
        # Intentar con model_dump() para Pydantic v2
        history_dict = history.model_dump()
    except AttributeError:
        try:
            # Fallback a dict() para Pydantic v1
            history_dict = history.dict()
        except AttributeError:
            # Último fallback a to_dict() personalizado
            history_dict = history.to_dict()
    
    return json.dumps(history_dict, ensure_ascii=False, cls=DateTimeEncoder)

def _deserialize_history(data: str) -> LearningPathHistory:
    """Deserializa un JSON a objeto LearningPathHistory."""
    try:
        json_data = json.loads(data)
        
        # Convertimos el formato ISO de las fechas a objetos datetime
        entries = []
        for entry_data in json_data.get("entries", []):
            # Convertir fechas ISO a datetime
            if "creation_date" in entry_data:
                entry_data["creation_date"] = datetime.fromisoformat(entry_data["creation_date"])
            if "last_modified_date" in entry_data and entry_data["last_modified_date"]:
                entry_data["last_modified_date"] = datetime.fromisoformat(entry_data["last_modified_date"])
            
            # Crear objeto de entrada
            entry = LearningPathHistoryEntry(**entry_data)
            entries.append(entry)
        
        # Crear objeto de historial
        last_updated = datetime.fromisoformat(json_data.get("last_updated", datetime.now().isoformat()))
        return LearningPathHistory(entries=entries, last_updated=last_updated)
    except Exception as e:
        logger.error(f"Error al deserializar historial: {str(e)}")
        return LearningPathHistory()

def _store_in_session_state(history: LearningPathHistory) -> None:
    """Almacena el historial en el estado de la sesión."""
    st.session_state["learning_path_history"] = history

def _get_from_session_state() -> Optional[LearningPathHistory]:
    """Recupera el historial del estado de la sesión."""
    return st.session_state.get("learning_path_history")

def _segment_data(data: str) -> List[str]:
    """Divide los datos en segmentos si exceden el tamaño máximo."""
    if len(data) <= MAX_SEGMENT_SIZE:
        return [data]
    
    segments = []
    for i in range(0, len(data), MAX_SEGMENT_SIZE):
        segments.append(data[i:i + MAX_SEGMENT_SIZE])
    
    return segments

def _save_segmented(data: str) -> None:
    """Guarda datos segmentados en localStorage."""
    segments = _segment_data(data)
    
    # Almacenar metadatos de segmentación
    meta = {
        "segments_count": len(segments),
        "timestamp": datetime.now().isoformat()
    }
    st.session_state[HISTORY_META_KEY] = meta
    
    # Almacenar cada segmento
    for i, segment in enumerate(segments):
        segment_key = f"{HISTORY_SEGMENT_KEY_PREFIX}{i}"
        st.session_state[segment_key] = segment

def _load_segmented() -> Optional[str]:
    """Carga datos segmentados desde localStorage."""
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
            logger.error(f"Segmento {i} no encontrado, datos posiblemente corruptos")
            return None
    
    return "".join(segments)

def save_history(history: LearningPathHistory) -> bool:
    """Guarda el historial en localStorage de forma persistente."""
    try:
        # Serializar y comprimir
        serialized = _serialize_history(history)
        compressed = _compress_data(serialized)
        
        # Guardar datos (segmentados si es necesario)
        if len(compressed) > MAX_SEGMENT_SIZE:
            _save_segmented(compressed)
        else:
            st.session_state[HISTORY_KEY] = compressed
        
        # Actualizar estado de sesión
        _store_in_session_state(history)
        return True
    except Exception as e:
        logger.error(f"Error al guardar historial: {str(e)}")
        return False

def load_history() -> LearningPathHistory:
    """Carga el historial desde localStorage."""
    # Primero intentamos obtener del estado de la sesión
    cached_history = _get_from_session_state()
    if cached_history:
        return cached_history
    
    try:
        # Intentar cargar datos directos o segmentados
        compressed = st.session_state.get(HISTORY_KEY)
        if not compressed:
            compressed = _load_segmented()
        
        if not compressed:
            logger.info("No se encontró historial guardado, creando uno nuevo")
            new_history = LearningPathHistory()
            _store_in_session_state(new_history)
            return new_history
        
        # Descomprimir y deserializar
        decompressed = _decompress_data(compressed)
        history = _deserialize_history(decompressed)
        
        # Guardar en estado de sesión
        _store_in_session_state(history)
        return history
    except Exception as e:
        logger.error(f"Error al cargar historial: {str(e)}")
        return LearningPathHistory()

def add_learning_path(learning_path: Dict[str, Any], source: str = "generated") -> bool:
    """Añade un nuevo learning path al historial."""
    try:
        # Obtener historial actual
        history = load_history()
        
        # Crear nueva entrada
        entry = LearningPathHistoryEntry(
            topic=learning_path.get("topic", "Sin título"),
            path_data=learning_path,
            source=source
        )
        
        # Añadir al historial
        history.add_entry(entry)
        
        # Guardar historial actualizado
        return save_history(history)
    except Exception as e:
        logger.error(f"Error al añadir learning path: {str(e)}")
        return False

def import_learning_path(json_data: str) -> Tuple[bool, str]:
    """Importa un learning path desde JSON."""
    try:
        # Deserializar JSON
        learning_path = json.loads(json_data)
        
        # Validar que tenga la estructura básica esperada
        if not isinstance(learning_path, dict) or "topic" not in learning_path or "modules" not in learning_path:
            return False, "El archivo JSON no tiene el formato correcto de learning path"
        
        # Verificar si ya existe un path similar
        history = load_history()
        topic = learning_path.get("topic", "")
        
        for entry in history.entries:
            if entry.topic == topic:
                # Podríamos implementar una comparación más sofisticada aquí
                logger.warning(f"Ya existe un learning path con el tema '{topic}'")
                # No obstante, permitimos importarlo igualmente
        
        # Añadir al historial
        success = add_learning_path(learning_path, source="imported")
        if success:
            return True, f"Learning path '{topic}' importado correctamente"
        else:
            return False, "Error al guardar el learning path importado"
    except json.JSONDecodeError:
        return False, "El archivo no es un JSON válido"
    except Exception as e:
        logger.error(f"Error al importar learning path: {str(e)}")
        return False, f"Error: {str(e)}"

def get_history_preview() -> List[Dict[str, Any]]:
    """Obtiene una vista previa del historial para mostrar en la UI."""
    history = load_history()
    entries = history.get_sorted_entries()
    return [entry.to_preview_dict() for entry in entries]

def get_learning_path(entry_id: str) -> Optional[Dict[str, Any]]:
    """Obtiene un learning path específico por su ID."""
    history = load_history()
    entry = history.get_entry(entry_id)
    if entry:
        return entry.path_data
    return None

def delete_learning_path(entry_id: str) -> bool:
    """Elimina un learning path del historial."""
    history = load_history()
    success = history.remove_entry(entry_id)
    if success:
        return save_history(history)
    return False

def update_learning_path_metadata(entry_id: str, favorite: bool = None, tags: List[str] = None) -> bool:
    """Actualiza los metadatos de un learning path en el historial."""
    history = load_history()
    updates = {}
    
    if favorite is not None:
        updates["favorite"] = favorite
    if tags is not None:
        updates["tags"] = tags
    
    if not updates:
        return True  # No hay nada que actualizar
    
    success = history.update_entry(entry_id, **updates)
    if success:
        return save_history(history)
    return False

def export_history() -> str:
    """Exporta todo el historial como JSON para respaldo."""
    history = load_history()
    return json.dumps(history.to_dict(), ensure_ascii=False, indent=2)

def clear_history() -> bool:
    """Borra todo el historial."""
    try:
        # Eliminar del estado de sesión
        if "learning_path_history" in st.session_state:
            del st.session_state["learning_path_history"]
        
        # Eliminar de localStorage
        if HISTORY_KEY in st.session_state:
            del st.session_state[HISTORY_KEY]
        
        # Eliminar metadatos de segmentación si existen
        if HISTORY_META_KEY in st.session_state:
            meta = st.session_state[HISTORY_META_KEY]
            segments_count = meta.get("segments_count", 0)
            
            # Eliminar segmentos
            for i in range(segments_count):
                segment_key = f"{HISTORY_SEGMENT_KEY_PREFIX}{i}"
                if segment_key in st.session_state:
                    del st.session_state[segment_key]
            
            # Eliminar metadatos
            del st.session_state[HISTORY_META_KEY]
        
        return True
    except Exception as e:
        logger.error(f"Error al limpiar historial: {str(e)}")
        return False 