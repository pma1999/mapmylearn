from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

class LearningPathHistoryEntry(BaseModel):
    """Modelo para una entrada individual en el historial de rutas de aprendizaje."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="UUID único para cada entrada del historial")
    topic: str = Field(..., description="Tema del learning path")
    creation_date: datetime = Field(default_factory=datetime.now, description="Fecha y hora de creación")
    last_modified_date: Optional[datetime] = Field(None, description="Fecha de última modificación")
    path_data: Dict[str, Any] = Field(..., description="Datos completos del learning path")
    favorite: bool = Field(False, description="Marcador para rutas favoritas")
    tags: List[str] = Field(default_factory=list, description="Etiquetas definidas por el usuario")
    source: str = Field("generated", description="Origen del learning path: 'generated' o 'imported'")
    
    def update_modified_date(self):
        """Actualiza la fecha de última modificación al momento actual."""
        self.last_modified_date = datetime.now()
    
    def to_preview_dict(self) -> Dict[str, Any]:
        """Retorna una versión reducida con solo los metadatos para la vista previa."""
        modules_count = len(self.path_data.get("modules", []))
        return {
            "id": self.id,
            "topic": self.topic,
            "creation_date": self.creation_date.isoformat(),
            "last_modified_date": self.last_modified_date.isoformat() if self.last_modified_date else None,
            "modules_count": modules_count,
            "favorite": self.favorite,
            "tags": self.tags,
            "source": self.source
        }

class LearningPathHistory(BaseModel):
    """Modelo para el historial completo de rutas de aprendizaje."""
    entries: List[LearningPathHistoryEntry] = Field(default_factory=list, description="Lista de rutas de aprendizaje guardadas")
    last_updated: datetime = Field(default_factory=datetime.now, description="Fecha de última actualización del historial")
    
    def add_entry(self, entry: LearningPathHistoryEntry) -> None:
        """Añade una nueva entrada al historial y actualiza la fecha de última actualización."""
        self.entries.append(entry)
        self.last_updated = datetime.now()
    
    def remove_entry(self, entry_id: str) -> bool:
        """Elimina una entrada del historial por su ID. Retorna True si se eliminó correctamente."""
        initial_length = len(self.entries)
        self.entries = [entry for entry in self.entries if entry.id != entry_id]
        success = len(self.entries) < initial_length
        if success:
            self.last_updated = datetime.now()
        return success
    
    def get_entry(self, entry_id: str) -> Optional[LearningPathHistoryEntry]:
        """Obtiene una entrada del historial por su ID."""
        for entry in self.entries:
            if entry.id == entry_id:
                return entry
        return None
    
    def update_entry(self, entry_id: str, **kwargs) -> bool:
        """Actualiza una entrada existente con los nuevos valores proporcionados."""
        entry = self.get_entry(entry_id)
        if not entry:
            return False
        
        # Actualizar los campos permitidos
        for key, value in kwargs.items():
            if hasattr(entry, key) and key not in ["id", "creation_date", "path_data"]:
                setattr(entry, key, value)
        
        entry.update_modified_date()
        self.last_updated = datetime.now()
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el historial completo a un diccionario."""
        # Convertir cada entrada manualmente para controlar la serialización de datetime
        entries_dict = []
        for entry in self.entries:
            # Convertir manualmente los objetos datetime a cadenas ISO
            entry_dict = {
                "id": entry.id,
                "topic": entry.topic,
                "creation_date": entry.creation_date.isoformat(),
                "last_modified_date": entry.last_modified_date.isoformat() if entry.last_modified_date else None,
                "path_data": entry.path_data,
                "favorite": entry.favorite,
                "tags": entry.tags,
                "source": entry.source
            }
            entries_dict.append(entry_dict)
        
        return {
            "entries": entries_dict,
            "last_updated": self.last_updated.isoformat()
        }
    
    def get_sorted_entries(self, sort_by="creation_date", reverse=True) -> List[LearningPathHistoryEntry]:
        """Retorna las entradas ordenadas según el criterio especificado."""
        if sort_by == "creation_date":
            return sorted(self.entries, key=lambda x: x.creation_date, reverse=reverse)
        elif sort_by == "last_modified_date":
            return sorted(self.entries, key=lambda x: x.last_modified_date or x.creation_date, reverse=reverse)
        elif sort_by == "topic":
            return sorted(self.entries, key=lambda x: x.topic.lower(), reverse=reverse)
        elif sort_by == "favorite":
            return sorted(self.entries, key=lambda x: (not x.favorite, x.creation_date), reverse=reverse)
        return self.entries 