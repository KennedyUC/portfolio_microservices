from kennweb.insuranceflow.services.documentai import DocumentAIService
from kennweb.insuranceflow.services.email import EmailService
from kennweb.insuranceflow.services.gemini import GeminiService
from kennweb.insuranceflow.services.storage import StorageService
from kennweb.insuranceflow.services.rag import RAGService
from kennweb.core.configs.insuranceflow import EMAIL_USERNAME, EMAIL_PASSWORD

documentai_service = DocumentAIService()
email_service = EmailService(user=EMAIL_USERNAME, password=EMAIL_PASSWORD)
gemini_service = GeminiService()
storage_service = StorageService()
rag_service = RAGService()