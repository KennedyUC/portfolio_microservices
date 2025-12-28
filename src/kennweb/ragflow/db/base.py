from kennweb.ragflow.db.database import database_client

class BaseRepository():
    def __init__(self) -> None:
        self.db = database_client.get_db()