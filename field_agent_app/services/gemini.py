import time
import re
from google import genai
from google.genai.types import GenerateContentConfig, Part
from field_agent_app.core.logging import logger
from field_agent_app.core.config import settings

if settings.gemini_api_key == "":
    from vertexai import init as vertexai_init
    from vertexai.preview.generative_models import GenerativeModel as VertexGenerativeModel
    from vertexai.generative_models import Part as VertexPart
    from vertexai.generative_models import Content


class GeminiService:
    def __init__(self, model_name: str = settings.gemini_model_name):
        self.api_key = settings.gemini_api_key
        self.model = model_name
        self.temperature = 0.3
        self.max_retries = 3
        self.backoff_time = 3
        self.project = settings.gcp_project_id
        self.location = settings.gcp_region
        self.client = None

        if not self.api_key:
            vertexai_init(project=self.project, location=self.location)
            self.gen_model = VertexGenerativeModel(self.model)
            logger.info("Initialized Gemini Service with VertexAI.")
        else:
            self.client = genai.Client(api_key=self.api_key)
            logger.info("Initialized Gemini Service with API Key.")

    def clean_text(self, text: str):
        if "```json" in text:
            text = re.sub(r"```json|```", "", text.strip())
        if "```html" in text:
            text = re.sub(r"```html|```", "", text.strip())
        if "```markdown" in text:
            text = re.sub(r"```markdown|```", "", text.strip())
        return text

    def call_gemini(self, prompt: str, audio_content: bytes = None, mime_type: str = None) -> str:
        attempt = 0

        while attempt < self.max_retries:
            attempt += 1
            logger.info(f"Gemini API call: Attempt {attempt}/{self.max_retries}")
            try:
                # --- API KEY path ---
                if self.client:
                    content = [Part.from_text(text=prompt)]

                    if audio_content and mime_type:
                        content.append(Part.from_bytes(data=audio_content, mime_type=mime_type))
                    
                    response = self.client.models.generate_content(
                        model=self.model,
                        contents=content,
                        config=GenerateContentConfig(temperature=self.temperature)
                    )
                    return self.clean_text(text=response.text)

                # --- Vertex AI path ---
                if audio_content and mime_type:
                    content = Content(
                        role="user",
                        parts=[
                            VertexPart.from_text(text=prompt),
                            VertexPart.from_data(data=audio_content, mime_type=mime_type)
                        ]
                    )
                else:
                    content = Content(
                        role="user",
                        parts=[VertexPart.from_text(text=prompt)]
                    )

                response = self.gen_model.generate_content(
                    contents=content,
                    generation_config={"temperature": self.temperature}
                )
                return self.clean_text(text=response.text)

            except Exception as e:
                logger.error(f"[Error] Gemini call failed (attempt {attempt}/{self.max_retries}): {e}")
                if attempt < self.max_retries:
                    logger.info(f"Retrying in {self.backoff_time} seconds...")
                    time.sleep(self.backoff_time)
                else:
                    logger.warning("Max retries reached. Returning empty string.")
                    return ""
                
gemini_service = GeminiService()