import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from field_agent_app.core.logging import logger
from field_agent_app.core.config import ALLOWED_ORIGINS, APP_VERSION, PROJECT_TITLE
from field_agent_app.api.routes.router import router as processor_router
from field_agent_app.db.database import database_client
from field_agent_app.core.config import settings

tags_metadata = [
    {"name": "Document Processor", "description": "Manages the endpoints for the document processor"}
]

app = FastAPI(
    title=PROJECT_TITLE,
    version=APP_VERSION,
    openapi_tags=tags_metadata
)

app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.add_event_handler('startup', database_client.startup_event)
app.add_event_handler('shutdown', database_client.shutdown_event)

app.include_router(router=processor_router, tags=["Document Processor"])

def main():
    logger.info("Starting Field Agent Assistant API Endpoint")
    uvicorn.run("field_agent_app.api.server:app", host="0.0.0.0", port=9008, reload=True if settings.env == "dev" else False)

if __name__ == "__main__":
    main()