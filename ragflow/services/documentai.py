from google.cloud import documentai_v1beta3 as documentai
from ragflow import logger
from core.configs.ragflow import GCP_PROJECT_ID, DOCAI_PROCESSOR_NAME, DOCAI_PROCESSOR_TYPE
from ragflow.utils import gcp_clients
import uuid

class DocumentAIService:
    def __init__(self):
        self.project_id         = GCP_PROJECT_ID
        self.location           = "us"
        self.processor_name     = DOCAI_PROCESSOR_NAME
        self.processor_type     = DOCAI_PROCESSOR_TYPE
        self.processor_client   = gcp_clients.get_docai_client()
    
    def create_doc_processor(self):
        logger.info("Creating Document AI Processor...")
        processor_name_uid = str(uuid.uuid4())[:8]
        parent = self.processor_client.common_location_path(self.project_id, self.location)

        processor = self.processor_client.create_processor(
            parent=parent,
            processor=documentai.Processor(
                type_=self.processor_type,
                display_name=f"{self.processor_name}_{processor_name_uid}"
            )
        )
        logger.info(f"Document AI Processor '{processor.name}' successfully created")
        return processor
    
    def delete_doc_processor(self, processor_name):
        try:
            logger.info("Deleting Document AI Processor")
            operation = self.processor_client.delete_processor(name=processor_name)
            operation.result()
            logger.info(f"Document AI Processor '{processor_name}' successfully deleted")
        except Exception as e:
            logger.error(f"Error occurred during processor deletion: {e}")

    async def extract_text(self, file_path: str, mime_type: str):
        try:
            processor_name = self.create_doc_processor().name

            with open(file_path, "rb") as f:
                document_content = f.read()

            logger.info(f"Extracting text from document...")

            raw_document = documentai.RawDocument(content=document_content, mime_type=mime_type)
            request = documentai.ProcessRequest(name=processor_name, raw_document=raw_document)
            result = self.processor_client.process_document(request=request)

            logger.info("Document Processing Successfully Completed")
            self.delete_doc_processor(processor_name=processor_name)
            return result.document.text.strip()
        except Exception as e:
            logger.error(f"Error occurred during document processing: {e}")
            self.delete_doc_processor(processor_name=processor_name)
            return None