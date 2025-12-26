from enum import Enum
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone

class AuthMode(str, Enum):
    service_account = "service_account"
    credential = "credential"

class ProcessorFolders(str, Enum):
    audio       = "audio-conversations"
    document    = "additional-documents"
    guideline   = "policy-guidelines"

class DocumentProcessRequest(BaseModel):
    audio_gcs_path: Optional[str]
    audio_mimetype: str
    policy_id_or_customer_name: Optional[str] = None
    local_image_paths: Optional[List[dict]] = None
    gcs_paths: Optional[List[dict]] = None
    include_history_data: bool = False
    history_gcs_paths: Optional[str] = None

class ChatRequest(BaseModel):
    query: str

class FileMetadataRecord(BaseModel):
    File_Name: str
    File_Hash: str
    Storage_Path: str
    Upload_Time: datetime
    Created_At: datetime = datetime.now(timezone.utc)

class FileNamesRequest(BaseModel):
    file_names: str