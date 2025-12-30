from typing import Callable, Union, Dict, List, Any
from kennweb.ragflow import logger
from databases import Database
from databases import DatabaseURL

class DatabaseConnTasks:
    def __init__(self, service_name: str, db_url: Union[str, DatabaseURL]):
        self.service_name = service_name
        self.db_url = db_url
        self.db = None

    async def connect_to_db(self):
        try:
            if not self.db:
                self.db = Database(self.db_url)
            
            logger.info(f'Connecting to the Database {str(self.db_url)} for {self.service_name} service.')
            if self.db and not self.db.is_connected:
                await self.db.connect()
            logger.info(f'Connected to the Database {str(self.db_url)} for {self.service_name} service.')
        except Exception as e:
            logger.exception(
                f'Error Connecting to the Database {str(self.db_url)} for {self.service_name} service.'
            )

    async def disconnect_from_db(self):
        try:
            logger.info(f'Closing the Database connection for {self.service_name} service.')
            if self.db.is_connected:
                await self.db.disconnect()
                logger.info(f'Successfully closed the Database connection for {self.service_name} service.')
            else:
                logger.info(f'No active Database connection found for {self.service_name} service.')
        except Exception as e:
            logger.exception(f'Error closing the Database connection for {self.service_name} service.')

    async def get_db(self):
        if not self.db:
            raise RuntimeError(f"No database connection exists for {self.service_name} service.")
        return self.db
    
    async def fetch_one(self, query: str, values: Dict[str, Any] = None) -> Dict[str, Any]:
        try:
            result = await self.db.fetch_one(query=query, values=values)
            return result
        except Exception as e:
            logger.exception(f'Error fetching record from Database: {str(self.db_url)}')
            raise

    async def fetch_all(self, query: str, values: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        try:
            results = await self.db.fetch_all(query=query, values=values)
            return results
        except Exception as e:
            logger.exception(f'Error fetching records from Database: {str(self.db_url)}')
            raise
    
    async def startup_event(self) -> Callable:
        await self.connect_to_db()

    async def shutdown_event(self) -> Callable:
        await self.disconnect_from_db()