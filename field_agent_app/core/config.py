from pydantic_settings import BaseSettings
from starlette.config import Config

config = Config(".env")

AUTH_MODE               = config("AUTH_MODE", cast=str, default="credential")
PROJECT_TITLE           = config("PROJECT_TITLE", cast=str)
APP_VERSION             = config("APP_VERSION", cast=str)
ENV                     = config("ENV", cast=str)
ALLOWED_ORIGINS         = config("ALLOWED_ORIGINS", cast=list)
GCP_PROJECT_ID          = config("GCP_PROJECT_ID", cast=str)
GCP_REGION              = config("GCP_REGION", cast=str)
DOCAI_PROCESSOR_NAME    = config("DOCAI_PROCESSOR_NAME", cast=str)
DOCAI_PROCESSOR_TYPE    = config("DOCAI_PROCESSOR_TYPE", cast=str)
GCP_SA_JSON_PATH        = config("GCP_SA_JSON_PATH", cast=str)
GEMINI_API_KEY          = config("GEMINI_API_KEY", cast=str, default="")
GCP_STORAGE_BUCKET      = config("GCP_STORAGE_BUCKET", cast=str)
BQ_DATASET_ID           = config("BQ_DATASET_ID", cast=str)
BQ_TABLE_ID             = config("BQ_TABLE_ID", cast=str)
DROP_EXISTING_TABLE     = config("DROP_EXISTING_TABLE", cast=bool, default=False)
EMBEDDING_MODEL         = config("EMBEDDING_MODEL", cast=str, default="text-embedding-005")
RAG_MODEL_NAME          = config("RAG_MODEL_NAME", cast=str, default="gemini-2.0-flash")
GEMINI_MODEL_NAME       = config("GEMINI_MODEL_NAME", cast=str, default="gemini-2.0-flash")
RAG_ENGINE_NAME         = config("RAG_ENGINE_NAME", cast=str, default="policy-guidelines-rag")
EMAIL_USERNAME          = config("EMAIL_USERNAME", cast=str)
EMAIL_PASSWORD          = config("EMAIL_PASSWORD", cast=str)
METADATA_TABLE_ID       = config("METADATA_TABLE_ID", cast=str)

class AppSettings(BaseSettings):
    auth_mode: str = AUTH_MODE
    project_title: str = PROJECT_TITLE
    app_version: str = APP_VERSION
    env: str = ENV
    allowed_origin: list = ALLOWED_ORIGINS
    gcp_project_id: str = GCP_PROJECT_ID
    gcp_region: str = GCP_REGION
    docai_processor_name: str = DOCAI_PROCESSOR_NAME
    docai_processor_type: str = DOCAI_PROCESSOR_TYPE
    gcp_storage_bucket: str = GCP_STORAGE_BUCKET
    gcp_sa_json_path: str = GCP_SA_JSON_PATH
    gemini_api_key: str = GEMINI_API_KEY
    bq_dataset_id: str = BQ_DATASET_ID
    bq_table_id: str = BQ_TABLE_ID
    drop_existing_table: bool = DROP_EXISTING_TABLE
    embedding_model: str = EMBEDDING_MODEL
    rag_model_name: str = RAG_MODEL_NAME
    gemini_model_name: str = GEMINI_MODEL_NAME
    rag_engine_name: str = RAG_ENGINE_NAME
    email_username: str = EMAIL_USERNAME
    email_password: str = EMAIL_PASSWORD
    metadata_table_id: str = METADATA_TABLE_ID

settings = AppSettings()