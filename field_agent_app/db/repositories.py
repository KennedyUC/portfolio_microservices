from field_agent_app.db.base import BaseRepository
from field_agent_app.core.config import settings
from google.cloud import bigquery
from field_agent_app.models.main import FileMetadataRecord

bq_table_fqn = f"{settings.gcp_project_id}.{settings.bq_dataset_id}.{settings.bq_table_id}"
metadata_table = f"{settings.gcp_project_id}.{settings.bq_dataset_id}.{settings.metadata_table_id}"

GET_POLICY_BY_CUSTOMER_QUERY = f"""
    SELECT PolicyID, CustomerName, PolicyType, State, EffectiveDate, ExpirationDate, Premium, Status
    FROM `{bq_table_fqn}`
    WHERE CustomerName = @CustomerName
"""

GET_POLICY_BY_POLICY_ID_QUERY = f"""
    SELECT PolicyID, CustomerName, PolicyType, State, EffectiveDate, ExpirationDate, Premium, Status
    FROM `{bq_table_fqn}`
    WHERE PolicyID = @PolicyID
"""

CREATE_UPLOAD_METADATA_QUERY = f"""
    INSERT INTO `{metadata_table}` 
    (File_Name, File_Hash, Storage_Path, Upload_Time, Created_At)
    VALUES ( 
        @File_Name,
        @File_Hash, 
        @Storage_Path, 
        @Upload_Time, 
        @Created_At
    )
"""

GET_FILE_HASH_QUERY = f"""
    SELECT File_Hash
    FROM `{metadata_table}`
    WHERE File_Hash = @File_Hash
"""

GET_FILE_METADATA_QUERY = f"""
    SELECT Storage_Path
    FROM `{metadata_table}`
    WHERE File_Name IN UNNEST(@file_names)
"""

GET_FILE_NAMES_QUERY = f"""
    SELECT File_Name
    FROM `{metadata_table}`
"""

class PolicyRecordRepository(BaseRepository):
    def __init__(self):
        super().__init__()

    async def fetch_one(self, query, query_params):
        job = self.db.query(query, job_config=bigquery.QueryJobConfig(query_parameters=query_params))

        try:
            result = job.result()
        except Exception as e:
            raise Exception(f"Failed to execute query: {e}")
        
        rows = [dict(row) for row in result]
        
        if len(rows) > 0:
            return rows[0]
    
    async def fetch_all(self, query, query_params):
        job = self.db.query(query, job_config=bigquery.QueryJobConfig(query_parameters=query_params or []))

        try:
            result = job.result()
        except Exception as e:
            raise Exception(f"Failed to execute query: {e}")
        
        rows = [dict(row) for row in result]
        return rows

        
    async def get_policy_by_customer_name(self, customer_name: str):
        query = GET_POLICY_BY_CUSTOMER_QUERY

        query_params = [
            bigquery.ScalarQueryParameter("CustomerName", "STRING", customer_name)
        ]

        result = await self.fetch_one(query=query, query_params=query_params)

        if result:
            return result
        
        return None
    
    async def get_policy_by_policy_id(self, policy_id: str):
        query = GET_POLICY_BY_POLICY_ID_QUERY

        query_params = [
            bigquery.ScalarQueryParameter("PolicyID", "STRING", policy_id)
        ]

        result = await self.fetch_one(query=query, query_params=query_params)

        if result:
            return result
        
        return None
    
    async def create_metadata_record(self, metadata_record: FileMetadataRecord):
        row_to_insert = metadata_record.model_dump()

        query_params = [
            bigquery.ScalarQueryParameter("File_Name", "STRING", row_to_insert["File_Name"]),
            bigquery.ScalarQueryParameter("File_Hash", "STRING", row_to_insert["File_Hash"]),
            bigquery.ScalarQueryParameter("Storage_Path", "STRING", row_to_insert["Storage_Path"]),
            bigquery.ScalarQueryParameter("Upload_Time", "TIMESTAMP", row_to_insert["Upload_Time"]),
            bigquery.ScalarQueryParameter("Created_At", "TIMESTAMP", row_to_insert["Created_At"])
        ]
        
        query = CREATE_UPLOAD_METADATA_QUERY

        await self.fetch_one(query=query, query_params=query_params)

    async def get_storage_paths(self, file_names: list[str]) -> list[str]:

        query = GET_FILE_METADATA_QUERY

        query_params = [bigquery.ArrayQueryParameter("file_names", "STRING", file_names)]

        results = await self.fetch_all(query=query, query_params=query_params)
        
        storage_paths = [row["Storage_Path"] for row in results]
        
        return storage_paths
    
    async def get_hash_record(self, file_hash: str):
        query = GET_FILE_HASH_QUERY

        query_params = [
            bigquery.ScalarQueryParameter("File_Hash", "STRING", file_hash),
        ]

        record = await self.fetch_one(query=query, query_params=query_params)

        return record

    async def get_file_names(self):
        query = GET_FILE_NAMES_QUERY

        records = await self.fetch_all(query=query, query_params=None)

        return [row["File_Name"] for row in records]