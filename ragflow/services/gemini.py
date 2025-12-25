import time
import re
from google.genai.types import GenerateContentConfig, Part
from ragflow import logger
from core.configs.ragflow import GEMINI_API_KEY, GEMINI_MODEL_NAME, GCP_PROJECT_ID, GCP_REGION
from vertexai.generative_models import Part as VertexPart
from vertexai.generative_models import Content
from ragflow.utils import gcp_clients


class GeminiService:
    def __init__(self, model_name: str = GEMINI_MODEL_NAME):
        self.api_key = GEMINI_API_KEY
        self.model = model_name
        self.temperature = 0.3
        self.max_retries = 3
        self.backoff_time = 3
        self.project = GCP_PROJECT_ID
        self.location = GCP_REGION

    def clean_text(self, text: str):
        if "```json" in text:
            text = re.sub(r"```json|```", "", text.strip())
        if "```html" in text:
            text = re.sub(r"```html|```", "", text.strip())
        if "```markdown" in text:
            text = re.sub(r"```markdown|```", "", text.strip())
        return text

    def call_gemini(self, prompt: str, audio_content: bytes = None, mime_type: str = None) -> str:
        genai_client = gcp_clients.get_genai_client()
        
        attempt = 0

        while attempt < self.max_retries:
            attempt += 1
            logger.info(f"Gemini API call: Attempt {attempt}/{self.max_retries}")
            try:
                if self.api_key:
                    content = [Part.from_text(text=prompt)]

                    if audio_content and mime_type:
                        content.append(Part.from_bytes(data=audio_content, mime_type=mime_type))
                    
                    response = genai_client.models.generate_content(
                        model=self.model,
                        contents=content,
                        config=GenerateContentConfig(temperature=self.temperature)
                    )
                    return self.clean_text(text=response.text)
                else:
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

                    response = genai_client.generate_content(
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