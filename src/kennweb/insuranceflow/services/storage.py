import os
import mimetypes
import asyncio
from kennweb.core.configs.insuranceflow import GCP_STORAGE_BUCKET
from kennweb.insuranceflow import logger
from kennweb.insuranceflow.utils import gcp_clients
from io import BytesIO
from typing import List

class StorageService:
    def __init__(self):
        self.storage_bucket = GCP_STORAGE_BUCKET
        self.storage_client = gcp_clients.get_storage_client()

    async def upload_document(self, storage_folder, file_name, file_content, mime_type):
        bucket = self.storage_client.bucket(self.storage_bucket)
        storage_path = f"{storage_folder}/{file_name}"
        blob = bucket.blob(storage_path)

        logger.info(f"Uploading file '{file_name}' to '{storage_path}'...")
        try:
            blob.upload_from_file(file_content, content_type=mime_type, rewind=True)
            logger.info(f"File '{file_name}' uploaded to path '{self.storage_bucket}/{storage_path}'")
            return storage_path
        except Exception as e:
            logger.info(f"Error uploading {file_name} to {self.storage_bucket}: {e}")

    async def upload_documents(self, local_dir: str, gcs_folder: str):
        tasks = []
        for file_name in os.listdir(local_dir):
            file_path = os.path.join(local_dir, file_name)

            if os.path.isfile(file_path):
                mime_type, _ = mimetypes.guess_type(file_path)
                mime_type = mime_type or "application/octet-stream"

                file_obj = open(file_path, "rb")
                tasks.append(self.upload_document(gcs_folder, file_name, file_obj, mime_type))

        await asyncio.gather(*tasks)
    
    async def download_document(self, storage_folder: str, file_name: str) -> BytesIO:
        bucket = self.storage_client.bucket(self.storage_bucket)
        blob = bucket.blob(f"{storage_folder}/{file_name}")

        logger.info(f"Downloading file '{file_name}' from Google Cloud Storage")

        try:
            file_data = blob.download_as_bytes()
            file_obj = BytesIO(file_data)
            file_obj.seek(0)
            logger.info(f"File '{file_name}' successfully downloaded from '{self.storage_bucket}/{storage_folder}'")
            return file_obj
        except Exception as e:
            logger.error(f"Error downloading '{file_name}' from '{self.storage_bucket}': {e}")
            raise

    async def list_blobs_in_folder(self, folder: str) -> List[str]:
        try:
            bucket = self.storage_client.bucket(self.storage_bucket)
            blobs = bucket.list_blobs(prefix=folder)
            blob_uris = [
                f"gs://{self.storage_bucket}/{blob.name}"
                for blob in blobs
                if not blob.name.endswith("/")
            ]
            return blob_uris
        except Exception as e:
            logger.error(f"Error listing blobs in folder '{folder}': {e}")
            return []
        
    async def create_folder_if_not_exists(self, folder_path: str) -> None:
        if not folder_path.endswith("/"):
            folder_path += "/"

        bucket = self.storage_client.bucket(self.storage_bucket)
        blob = bucket.blob(folder_path)

        if not blob.exists():
            logger.info(f"Creating folder '{folder_path}' in bucket '{self.storage_bucket}'")
            blob.upload_from_string('', content_type='application/x-www-form-urlencoded;charset=UTF-8')
        else:
            logger.info(f"Folder '{folder_path}' already exists.")