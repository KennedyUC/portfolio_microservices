import asyncio
from field_agent_app.core.config import settings
from field_agent_app.services.storage import storage_processor
from field_agent_app.models.main import ProcessorFolders
from field_agent_app.services.documents import file_service
from field_agent_app.db.database import database_client
from field_agent_app.services.rag import rag_service

policy_table_fqn = f"{settings.gcp_project_id}.{settings.bq_dataset_id}.{settings.bq_table_id}"
metadata_table_fqn = f"{settings.gcp_project_id}.{settings.bq_dataset_id}.{settings.metadata_table_id}"

class Process:
    def __init__(self):
        pass

    async def run(self):
        # Connect to BigQuery
        database_client.connect_to_db()

        # Create table in BigQuery
        await database_client.create_tables(
            tables_fqn=[policy_table_fqn, metadata_table_fqn],
            drop_existing=settings.drop_existing_table
        )

        # Upload CSV data to BigQuery
        if settings.drop_existing_table:
            await file_service.upload_all_csv_to_bq(
                folder_path="field_agent_app/scripts/demo_documents/policies")

        # Create storage folders in GCS
        await storage_processor.create_folder_if_not_exists(ProcessorFolders.audio.value)
        await storage_processor.create_folder_if_not_exists(ProcessorFolders.document.value)
        await storage_processor.create_folder_if_not_exists(ProcessorFolders.guideline.value)

        # Upload Guideline Documents to GCS
        await storage_processor.upload_documents(
            local_dir="field_agent_app/scripts/demo_documents/guidelines",
            gcs_folder=ProcessorFolders.guideline.value
        )

        # List the Guideline GCS paths
        document_list = await storage_processor.list_blobs_in_folder(folder=ProcessorFolders.guideline.value)

        # Create RAG Engine if it does not exist
        await rag_service.create_rag_corpus()

        # Upload the Guideline documents in GCS to the RAG Engine
        await rag_service.import_files(data_paths_gcs=document_list)

if __name__ == '__main__':
    pre_run_process = Process()

    asyncio.run(pre_run_process.run())