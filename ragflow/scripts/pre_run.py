import asyncio
from ragflow.services import storage_service
from ragflow.models.main import ProcessorFolders
from ragflow.services.documents import file_service
from ragflow.db.database import database_client
from ragflow.services.rag import rag_service
from core.configs.ragflow import (
    GCP_PROJECT_ID, 
    BQ_DATASET_ID, 
    BQ_TABLE_ID, 
    METADATA_TABLE_ID,
    DROP_EXISTING_TABLE
)

policy_table_fqn = f"{GCP_PROJECT_ID}.{BQ_DATASET_ID}.{BQ_TABLE_ID}"
metadata_table_fqn = f"{GCP_PROJECT_ID}.{BQ_DATASET_ID}.{METADATA_TABLE_ID}"

class Process:
    def __init__(self):
        pass

    async def run(self):
        # Connect to BigQuery
        database_client.connect_to_db()

        # Create table in BigQuery
        await database_client.create_tables(
            tables_fqn=[policy_table_fqn, metadata_table_fqn],
            drop_existing=DROP_EXISTING_TABLE
        )

        # Upload CSV data to BigQuery
        if DROP_EXISTING_TABLE:
            await file_service.upload_all_csv_to_bq(
                folder_path="ragflow/scripts/demo_documents/policies")

        # Create storage folders in GCS
        await storage_service.create_folder_if_not_exists(ProcessorFolders.audio.value)
        await storage_service.create_folder_if_not_exists(ProcessorFolders.document.value)
        await storage_service.create_folder_if_not_exists(ProcessorFolders.guideline.value)

        # Upload Guideline Documents to GCS
        await storage_service.upload_documents(
            local_dir="ragflow/scripts/demo_documents/guidelines",
            gcs_folder=ProcessorFolders.guideline.value
        )

        # List the Guideline GCS paths
        document_list = await storage_service.list_blobs_in_folder(folder=ProcessorFolders.guideline.value)

        # Create RAG Engine if it does not exist
        await rag_service.create_rag_corpus()

        # Upload the Guideline documents in GCS to the RAG Engine
        await rag_service.import_files(data_paths_gcs=document_list)

if __name__ == '__main__':
    pre_run_process = Process()

    asyncio.run(pre_run_process.run())