import os
from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError
from ragflow.utils import gcp_clients
from core.configs.ragflow import BQ_DATASET_ID, BQ_TABLE_ID
from ragflow import logger

class FileService:
    def __init__(self):
        pass

    def read_file_content(self, file_path: str, mime_type: str):
        if "audio" not in mime_type:
            raise ValueError("The provided file is not a valid audio file.")
        
        with open(file_path, "rb") as f:
            audio_content = f.read()

        return audio_content
    
    async def upload_all_csv_to_bq(
        self,
        folder_path: str,
        autodetect_schema: bool = True,
        write_disposition: str = "WRITE_APPEND"
    ):
        if not os.path.isdir(folder_path):
            logger.error(f"❌ Provided path is not a directory: {folder_path}")
            return False

        success_count = 0
        total_count = 0

        for file_name in os.listdir(folder_path):
            if file_name.lower().endswith(".csv"):
                total_count += 1
                file_path = os.path.join(folder_path, file_name)
                logger.info(f"📤 Uploading file: {file_path}")
                result = await self.upload_csv_to_bq(
                    file_path=file_path,
                    autodetect_schema=autodetect_schema,
                    write_disposition=write_disposition
                )
                if result:
                    success_count += 1

        logger.info(f"✅ {success_count}/{total_count} CSV files uploaded successfully.")
        return success_count == total_count

    async def upload_csv_to_bq(
        self,
        file_path: str,
        autodetect_schema: bool = True,
        write_disposition: str = "WRITE_APPEND"
    ):
        try:
            client = gcp_clients.get_db_client()
            dataset_id = BQ_DATASET_ID
            table_id = BQ_TABLE_ID

            dataset_ref = client.dataset(dataset_id)
            table_ref = dataset_ref.table(table_id)

            job_config = bigquery.LoadJobConfig(
                source_format=bigquery.SourceFormat.CSV,
                skip_leading_rows=1,
                autodetect=autodetect_schema,
                write_disposition=write_disposition
            )

            with open(file_path, "rb") as f:
                load_job = client.load_table_from_file(
                    f,
                    table_ref,
                    job_config=job_config
                )

            result = load_job.result()
            logger.info(f"✅ Loaded {result.output_rows} rows into {dataset_id}.{table_id}.")
            return True

        except GoogleCloudError as e:
            logger.error(f"❌ Google Cloud error: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")

        return False
    
file_service = FileService()