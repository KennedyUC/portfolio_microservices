from kennweb.insuranceflow.db import database_conn

class BaseRepository():
    def __init__(self) -> None:
        self.db = database_conn