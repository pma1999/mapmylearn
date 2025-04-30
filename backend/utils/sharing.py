import nanoid
from sqlalchemy.orm import Session
# Avoid circular import at runtime, only import for type checking if needed
# from typing import TYPE_CHECKING
# if TYPE_CHECKING:
#     from backend.models.auth_models import LearningPath 

SHARE_ID_ALPHABET = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
SHARE_ID_SIZE = 12 # Can be adjusted based on desired collision probability vs length

def generate_unique_share_id(db: Session) -> str:
    """
    Generates a unique, URL-friendly share ID using nanoid.
    Ensures uniqueness within the LearningPath table.
    """
    # Import model locally within the function to avoid top-level circular imports
    from backend.models.auth_models import LearningPath 
    
    while True:
        share_id = nanoid.generate(SHARE_ID_ALPHABET, SHARE_ID_SIZE)
        # Check if the generated ID already exists in the database
        exists = db.query(LearningPath.id).filter(LearningPath.share_id == share_id).first()
        if not exists:
            return share_id 