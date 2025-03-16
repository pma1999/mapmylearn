from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

class LearningPathHistoryEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique ID")
    topic: str = Field(..., description="Learning path topic")
    creation_date: datetime = Field(default_factory=datetime.now, description="Creation datetime")
    last_modified_date: Optional[datetime] = Field(None, description="Last modification datetime")
    path_data: Dict[str, Any] = Field(..., description="Complete learning path data")
    favorite: bool = Field(False, description="Favorite flag")
    tags: List[str] = Field(default_factory=list, description="User-defined tags")
    source: str = Field("generated", description="Source: 'generated' or 'imported'")
    
    def update_modified_date(self):
        self.last_modified_date = datetime.now()
    
    def to_preview_dict(self) -> Dict[str, Any]:
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
    entries: List[LearningPathHistoryEntry] = Field(default_factory=list, description="Saved learning paths")
    last_updated: datetime = Field(default_factory=datetime.now, description="Last update datetime")
    
    def add_entry(self, entry: LearningPathHistoryEntry) -> None:
        self.entries.append(entry)
        self.last_updated = datetime.now()
    
    def remove_entry(self, entry_id: str) -> bool:
        initial = len(self.entries)
        self.entries = [entry for entry in self.entries if entry.id != entry_id]
        success = len(self.entries) < initial
        if success:
            self.last_updated = datetime.now()
        return success
    
    def get_entry(self, entry_id: str) -> Optional[LearningPathHistoryEntry]:
        for entry in self.entries:
            if entry.id == entry_id:
                return entry
        return None
    
    def update_entry(self, entry_id: str, **kwargs) -> bool:
        entry = self.get_entry(entry_id)
        if not entry:
            return False
        for key, value in kwargs.items():
            if hasattr(entry, key) and key not in ["id", "creation_date", "path_data"]:
                setattr(entry, key, value)
        entry.update_modified_date()
        self.last_updated = datetime.now()
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        entries_dict = []
        for entry in self.entries:
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
        return {"entries": entries_dict, "last_updated": self.last_updated.isoformat()}
    
    def get_sorted_entries(self, sort_by="creation_date", reverse=True) -> List[LearningPathHistoryEntry]:
        if sort_by == "creation_date":
            return sorted(self.entries, key=lambda x: x.creation_date, reverse=reverse)
        elif sort_by == "last_modified_date":
            return sorted(self.entries, key=lambda x: x.last_modified_date or x.creation_date, reverse=reverse)
        elif sort_by == "topic":
            return sorted(self.entries, key=lambda x: x.topic.lower(), reverse=reverse)
        elif sort_by == "favorite":
            return sorted(self.entries, key=lambda x: (not x.favorite, x.creation_date), reverse=reverse)
        return self.entries
