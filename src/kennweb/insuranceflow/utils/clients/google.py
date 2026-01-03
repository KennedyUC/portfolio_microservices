from google.cloud import documentai_v1beta3 as documentai
from google.cloud.storage import Client as StorageClient
from google.cloud.bigquery import Client as BQClient
from google.genai import Client as GenAIClient
from vertexai import init as vertexai_init
from vertexai.preview.generative_models import GenerativeModel as VertexGenerativeModel
from kennweb.insuranceflow import logger
from kennweb.insuranceflow.models.main import AuthMode
from google.auth import default
from kennweb.core.configs.insuranceflow import GCP_SA_JSON_PATH, GEMINI_API_KEY, GCP_PROJECT_ID, GCP_REGION

class GCPClients():
    def __init__(self, auth_mode: AuthMode) -> None:
        self.sa_json_path   = GCP_SA_JSON_PATH
        self.auth_mode = auth_mode
        self.api_key = GEMINI_API_KEY
        self.project_id = GCP_PROJECT_ID
        self.location = GCP_REGION

        self.docai_client: documentai.DocumentProcessorServiceClient = None
        self.storage_client: StorageClient = None
        self.bq_client: BQClient = None
        self.genai_client = None

    def _docai_client_init(self):
        logger.info("Initializing Document AI Client...")
        if self.auth_mode == AuthMode.credential.value:
            credentials, _ = default()
            self.docai_client = documentai.DocumentProcessorServiceClient(credentials=credentials)
            logger.info("Initialized Document AI Client with users credentials.")
        elif self.auth_mode == AuthMode.service_account.value:
            self.docai_client = documentai.DocumentProcessorServiceClient.from_service_account_json(self.sa_json_path)
            logger.info("Initialized Document AI Client with service account.")

    def _storage_client_init(self):
        logger.info("Initializing GCS Client...")
        if self.auth_mode == AuthMode.credential.value:
            credentials, project = default()
            self.storage_client = StorageClient(credentials=credentials, project=project)
            logger.info("Initialized GCS Client with user credentials")
        elif self.auth_mode == AuthMode.service_account.value:
            self.storage_client = StorageClient.from_service_account_json(self.sa_json_path)
            logger.info("Initialized GCS Client with service account.")

    def _bq_client_init(self):
        logger.info("Initializing BigQuery Client...")
        if self.auth_mode == AuthMode.credential.value:
            credentials, project = default()
            self.bq_client = BQClient(credentials=credentials, project=project)
            logger.info("Initialized BigQuery Client with user credentials.")
        elif self.auth_mode == AuthMode.service_account.value:
            self.bq_client = BQClient.from_service_account_json(self.sa_json_path)
            logger.info("Initialized BigQuery Client with service account.")
        
    def _genai_client_init(self):
        logger.info("Initializing Gemini GenAI Client...")
        if not self.api_key:
            vertexai_init(project=self.project_id, location=self.location)
            self.genai_client = VertexGenerativeModel(self.model)
            logger.info("Initialized Gemini Client with VertexAI.")
        else:
            self.genai_client = GenAIClient(api_key=self.api_key)
            logger.info("Initialized Gemini Client with API Key.")

    def get_docai_client(self):
        if not self.docai_client:
            self._docai_client_init()
        return self.docai_client
    
    def get_storage_client(self):
        if not self.storage_client:
            self._storage_client_init()
        return self.storage_client
    
    def get_bq_client(self):
        if not self.bq_client():
            self._bq_client_init
        return self.bq_client
    
    def get_genai_client(self):
        if not self.genai_client():
            self._genai_client_init
        return self.genai_client