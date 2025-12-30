from kennweb.ragflow.services.documentai import DocumentAIService
from kennweb.ragflow.services.email import EmailService
from kennweb.ragflow.services.gemini import GeminiService
from kennweb.ragflow.services.storage import StorageService
from kennweb.ragflow.services.rag import RAGService
from kennweb.core.configs.ragflow import EMAIL_USERNAME, EMAIL_PASSWORD

documentai_service = DocumentAIService()
email_service = EmailService(user=EMAIL_USERNAME, password=EMAIL_PASSWORD)
gemini_service = GeminiService()
storage_service = StorageService()
rag_service = RAGService()