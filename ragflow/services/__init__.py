from ragflow.services.documentai import DocumentAIService
from ragflow.services.email import EmailService
from ragflow.services.gemini import GeminiService
from ragflow.services.storage import StorageService
from ragflow.services.rag import RAGService
from core.configs.ragflow import EMAIL_USERNAME, EMAIL_PASSWORD

documentai_service = DocumentAIService()
email_service = EmailService(user=EMAIL_USERNAME, password=EMAIL_PASSWORD)
gemini_service = GeminiService()
storage_service = StorageService()
rag_service = RAGService()