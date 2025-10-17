from field_agent_app.core.config import settings
from google.cloud import documentai_v1beta3 as documentai
from google.cloud.storage import Client
from google.cloud import bigquery
from field_agent_app.core.logging import logger
from field_agent_app.models.main import AuthMode
from google.auth import default

class AppClients():
    def __init__(self, auth_mode: AuthMode) -> None:
        self.sa_json_path   = settings.gcp_sa_json_path
        self.auth_mode = auth_mode

        logger.info("Initializing Document AI Client...")
        if self.auth_mode != AuthMode.service_account.value:
            credentials, project = default()
            self.processor_client = documentai.DocumentProcessorServiceClient(credentials=credentials)
            self.storage_client = Client(credentials=credentials, project=project)
            self.db_client = bigquery.Client(credentials=credentials, project=project)
        else:
            self.processor_client = documentai.DocumentProcessorServiceClient.from_service_account_json(self.sa_json_path)
            self.storage_client = Client.from_service_account_json(self.sa_json_path)
            self.db_client = bigquery.Client.from_service_account_json(self.sa_json_path)
        logger.info("Document Processor Client Initialized")
        

    def get_processor_client(self):
        return self.processor_client
    
    def get_storage_client(self):
        return self.storage_client
    
    def get_db_client(self):
        return self.db_client
        
app_clients = AppClients(auth_mode=settings.auth_mode)