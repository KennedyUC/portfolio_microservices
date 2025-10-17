from vertexai import rag
from vertexai.generative_models import GenerativeModel, Tool, Part
import vertexai
from typing import Optional
from google.oauth2 import service_account
from field_agent_app.core.config import settings
from field_agent_app.core.logging import logger
from field_agent_app.models.main import AuthMode
from field_agent_app.services.gemini import gemini_service
from field_agent_app.services.prompts import PromptsTemplates

class RAGService:
    def __init__(
        self, 
        embedding_model: str = settings.embedding_model, 
        rag_model: str = settings.rag_model_name
    ):
        logger.info("Initializing RAG Service...")
        self.auth_mode = settings.auth_mode
        self.gcp_location = settings.gcp_region
        self.project_id = settings.gcp_project_id
        self.display_name = settings.rag_engine_name
        self.embedding_model = embedding_model
        self.rag_model = rag_model
        self.rag = rag
        
        if self.auth_mode == AuthMode.service_account.value:
            credentials = service_account.Credentials.from_service_account_file(settings.gcp_sa_json_path)
            vertexai.init(project=self.project_id, location=self.gcp_location, credentials=credentials)
        else:   
            vertexai.init(project=self.project_id, location=self.gcp_location)

        logger.info("RAG Service Initialized")

    async def create_rag_corpus(self):
        logger.info(f"Checking if RAG Corpus '{self.display_name}' already exists...")

        existing_corpora = list(self.rag.list_corpora())
        for corpus in existing_corpora:
            if corpus.display_name == self.display_name:
                self.rag_corpus = corpus
                logger.info(f"Found existing RAG Corpus: {corpus.name}")
                return corpus

        logger.info(f"RAG Corpus '{self.display_name}' not found. Creating new corpus...")
        embedding_model_config = self.rag.RagEmbeddingModelConfig(
            vertex_prediction_endpoint=self.rag.VertexPredictionEndpoint(
                publisher_model=f"publishers/google/models/{self.embedding_model}"
            )
        )

        rag_corpus = self.rag.create_corpus(
            display_name=self.display_name,
            backend_config=self.rag.RagVectorDbConfig(
                rag_embedding_model_config=embedding_model_config
            )
        )

        self.rag_corpus = rag_corpus
        logger.info(f"RAG Corpus '{self.display_name}' successfully created.")
        return rag_corpus

    async def import_files(self, data_paths_gcs: list):
        if not hasattr(self, "rag_corpus"):
            raise RuntimeError("RAG corpus must be created or retrieved before importing files.")
        
        if not data_paths_gcs:
            logger.warning("No data paths provided for import.")
            return

        logger.info(f"Importing files from paths: {data_paths_gcs}...")

        await self.rag.import_files_async(
            self.rag_corpus.name,
            data_paths_gcs,
            transformation_config=self.rag.TransformationConfig(
                chunking_config=self.rag.ChunkingConfig(
                    chunk_size=512,
                    chunk_overlap=100
                ),
            ),
            max_embedding_requests_per_min=1000
        )

        logger.info(f"All Guidelines Documents Successfully Imported to the RAG Engine")

    async def generate_search_query(self, combined_text: str) -> str:
        instruction = PromptsTemplates.rag_prompt(combined_text=combined_text)
        
        generative_model = GenerativeModel(
            model_name=self.rag_model,
            system_instruction=Part.from_text(text=instruction)
        )
        response = generative_model.generate_content(combined_text)
        search_query = response.text.strip()
        logger.info(f"Generated search query: {search_query}")
        return search_query

    async def create_response(self, query: str, instruction: str):
        logger.info(f"Generating RAG Response...")

        rag_retrieval_config = self.rag.RagRetrievalConfig(
            top_k=20,
            filter=self.rag.Filter(vector_distance_threshold=None)
        )
        
        rag_retrieval_tool = Tool.from_retrieval(
            retrieval=self.rag.Retrieval(
                source=self.rag.VertexRagStore(
                    rag_resources=[
                        self.rag.RagResource(
                            rag_corpus=self.rag_corpus.name
                        )
                    ],
                    rag_retrieval_config=rag_retrieval_config
                )
            )
        )

        rag_model = GenerativeModel(
            model_name=self.rag_model, 
            tools=[rag_retrieval_tool],
            system_instruction=Part.from_text(text=instruction)
        )

        response = rag_model.generate_content(query)

        return response
    
    async def run(self, instruction: str, combined_text: Optional[str] = None, user_query: Optional[str] = None):
        await self.create_rag_corpus()

        if not user_query and combined_text:
            query = await self.generate_search_query(combined_text)
        else:
            query = user_query
        
        response = await self.create_response(query=query, instruction=instruction)
        
        return response.text.strip()
    
rag_service = RAGService()