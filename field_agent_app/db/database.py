import asyncio
from google.cloud import bigquery
from field_agent_app.core.config import settings
from typing import Callable
from field_agent_app.core.logging import logger
from field_agent_app.core.tasks import app_clients

class DatabaseClient:
    def __init__(self):
        pass

    def connect_to_db(self):
        try:
            logger.info('Connecting to the Database Client')
            self.db = app_clients.get_db_client()
            logger.info('Connected to the Database Client')
        except Exception as e:
            logger.error('<---> Error Connecting to the Database Client <--->')
            logger.error(e)
            logger.error('<---> Error Connecting to the Database Client <--->')

    def close_db_connection(self):
        try:
            logger.info('Closing the Database Client connection')
            if self.db:
                self.db.close()
            logger.info('Closed the Database Client connection')

        except Exception as e:
            logger.error('<---> Error closing the Database Client connection <--->')
            logger.error(e)
            logger.error('<---> Error closing the Database Client connection <--->')

    def get_db(self):
        if not self.db:
            raise RuntimeError("Database client is not connected.")
        return self.db
    
    def drop_table(self, table_fqn):
        try:
            self.db.delete_table(table=table_fqn, not_found_ok=True)
            logger.info(f"Table {table_fqn} deleted successfully.")
        except Exception as e:
            logger.info(f"Failed to delete table {table_fqn} or table does not exist: {e}")

    async def create_tables(self, tables_fqn: list, drop_existing: bool = False):
        for table_fqn in tables_fqn:
            try:
                if drop_existing:
                    self.drop_table(table_fqn)

                self.db.get_table(table_fqn)
                logger.info(f"Table {table_fqn} already exists.")
            except Exception:
                logger.info(f"Creating table: {table_fqn}...")

                table = bigquery.Table(table_fqn)
                if 'metadata' in table_fqn:
                    table.schema = [
                        bigquery.SchemaField("File_Name", "STRING"),
                        bigquery.SchemaField("File_Hash", "STRING"),
                        bigquery.SchemaField("Storage_Path", "STRING"),
                        bigquery.SchemaField("Upload_Time", "TIMESTAMP"),
                        bigquery.SchemaField("Created_At", "TIMESTAMP")
                    ]
                self.db.create_table(table)
                logger.info(f"Table {table_fqn} created successfully.")
    
    def startup_event(self) -> Callable:
        self.connect_to_db()

    def shutdown_event(self) -> Callable:
        self.close_db_connection()
    

database_client = DatabaseClient()