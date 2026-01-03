from kennweb.insuranceflow.db.base import BaseRepository
from kennweb.insuranceflow.models.main import FileMetadataRecord


GET_POLICY_BY_CUSTOMER_QUERY = f"""
    SELECT
        policy_id,
        customer_name,
        policy_type,
        state,
        effective_date,
        expiration_date,
        premium,
        status
    FROM policies
    WHERE customer_name = :customer_name;
"""

GET_POLICY_BY_POLICY_ID_QUERY = f"""
    SELECT
        policy_id,
        customer_name,
        policy_type,
        state,
        effective_date,
        expiration_date,
        premium,
        status
    FROM policies
    WHERE policy_id = :policy_id;
"""

CREATE_UPLOAD_METADATA_QUERY = f"""
    INSERT INTO file_metadata (
        file_name,
        file_hash,
        storage_path,
        upload_time,
        created_at
    )
    VALUES (
        :file_name,
        :file_hash,
        :storage_path,
        :upload_time,
        :created_at
    );
"""

GET_FILE_HASH_QUERY = f"""
    SELECT file_hash
    FROM file_metadata
    WHERE file_hash = :file_hash;
"""

GET_FILE_METADATA_QUERY = f"""
    SELECT storage_path
    FROM file_metadata
    WHERE file_name = ANY(:file_names);
"""

GET_FILE_NAMES_QUERY = f"""
    SELECT file_name
    FROM file_metadata;
"""

class PolicyRecordRepository(BaseRepository):
    def __init__(self):
        super().__init__()
        
    async def get_policy_by_customer_name(self, customer_name: str):
        query = GET_POLICY_BY_CUSTOMER_QUERY

        query_params = {
            "customer_name": customer_name
        }

        result = await self.db.fetch_one(query=query, query_params=query_params)

        if result:
            return result
        
        return None
    
    async def get_policy_by_policy_id(self, policy_id: str):
        query = GET_POLICY_BY_POLICY_ID_QUERY

        query_params = {
            "policy_id": policy_id
        }

        result = await self.db.fetch_one(query=query, query_params=query_params)

        if result:
            return result
        
        return None
    
    async def create_metadata_record(self, metadata_record: FileMetadataRecord):
        query_params = metadata_record.model_dump()
        
        query = CREATE_UPLOAD_METADATA_QUERY

        await self.db.fetch_one(query=query, query_params=query_params)

    async def get_storage_paths(self, file_names: list[str]) -> list[str]:

        query = GET_FILE_METADATA_QUERY

        query_params = {
            "file_names": file_names
        }

        results = await self.db.fetch_all(query=query, query_params=query_params)
        
        storage_paths = [row["storage_path"] for row in results]
        
        return storage_paths
    
    async def get_hash_record(self, file_hash: str):
        query = GET_FILE_HASH_QUERY

        query_params = {
            "file_hash": file_hash
        }
        
        record = await self.db.fetch_one(query=query, query_params=query_params)

        return record

    async def get_file_names(self):
        query = GET_FILE_NAMES_QUERY

        records = await self.db.fetch_all(query=query)

        return [row["file_name"] for row in records]