from config.config import DB_PATH

from .database import Database

db = Database(DB_PATH)

__all__ = ["Database", "db"]
