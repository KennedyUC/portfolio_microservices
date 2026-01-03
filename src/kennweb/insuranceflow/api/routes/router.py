import os
import tempfile
import mimetypes
from uuid import uuid4
from typing import List

from fastapi import status
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File

from kennweb.insuranceflow import logger
from kennweb.insuranceflow.db.repositories import PolicyRecordRepository
from kennweb.insuranceflow.models.main import (
    ProcessorFolders,
    DocumentProcessRequest,
    ChatRequest,
    FileMetadataRecord,
    FileNamesRequest,
)
from kennweb.insuranceflow.services import rag_service
from kennweb.insuranceflow.services import email_service
from kennweb.insuranceflow.services import gemini_service
from kennweb.insuranceflow.services.chat import ConversationStore
from kennweb.insuranceflow.services.prompts import PromptsTemplates
from kennweb.insuranceflow.services import storage_service
from kennweb.insuranceflow.services import documentai_service

router = APIRouter()

store = ConversationStore("data/chat_history.json")

@router.get("/", include_in_schema=False)
async def spec():
    return RedirectResponse(url='/docs')

@router.post("/upload/audio")
async def upload_audio(audio_file: UploadFile = File(...)):
    if not audio_file.content_type.startswith("audio/"):
        raise HTTPException(400, detail="Invalid audio file type.")

    file_ext = audio_file.filename.split('.')[-1]
    file_name = f"{uuid4()}.{file_ext}"

    folder = ProcessorFolders.audio

    try:
        await storage_service.upload_document(
            storage_folder=folder,
            file_name=file_name,
            file_content=audio_file.file,
            mime_type=audio_file.content_type
        )

        return {
            "audio_gcs_path": f"{folder}/{file_name}",
            "audio_mimetype": audio_file.content_type
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Upload failed: {str(e)}"
        )
    
@router.post("/upload/documents")
async def upload_documents(files: List[UploadFile] = File(...)):
    folder = ProcessorFolders.document
    local_paths = []
    gcs_paths = []

    for file in files:
        mime_type = file.content_type.lower()
        suffix = os.path.splitext(file.filename)[1]

        if mime_type.startswith("image/"):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    contents = await file.read()
                    tmp.write(contents)
                    tmp_path = tmp.name
                    local_paths.append({"file_path": tmp_path, "mime_type": mime_type})
            except Exception as e:
                raise HTTPException(500, detail=f"Error saving image file locally: {file.filename}: {str(e)}")
        elif mime_type.startswith("audio/"):
            folder = ProcessorFolders.audio
            file_name = f"{uuid4()}{suffix}"

            try:
                await storage_service.upload_document(
                    storage_folder=folder,
                    file_name=file_name,
                    file_content=file.file,
                    mime_type=file.content_type
                )

                gcs_paths.append({"file_path": f"{folder}/{file_name}", "mime_type": mime_type})
            except Exception as e:
                logger.error(f"Error while processing {file_name}: {e}")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"File Format {file.content_type} not supported. Only Image and Audio files are supported at the moment."
            )

    return {
        "local_image_paths": local_paths,
        "gcs_paths": gcs_paths
    }

@router.post("/chat")
async def chat(
    chat: ChatRequest
):
    user_query = chat.query
    prompt = store.chat_prompt(user_query)
    
    response = await rag_service.run(
        instruction=prompt,
        user_query=user_query
    )

    store.append_to_history(user_query, response)

    return {"chat_response": response}

@router.post("/process-document")
async def process_document(
    payload: DocumentProcessRequest,
    record_repo: PolicyRecordRepository = Depends(PolicyRecordRepository)
):
    audio_gcs_path = payload.audio_gcs_path
    audio_mimetype = payload.audio_mimetype
    policy_id_or_customer_name = payload.policy_id_or_customer_name
    local_image_paths = payload.local_image_paths
    gcs_paths = payload.gcs_paths
    include_history_data = payload.include_history_data
    history_gcs_paths = [payload.history_gcs_paths]

    combined_text_parts = []
    audio_gcs_paths = []
    customer_record = None

    logger.info(f"History GCS Paths: {history_gcs_paths}")

    if audio_gcs_path:
        audio_gcs_paths.append(audio_gcs_path)
    if include_history_data and history_gcs_paths:
        audio_gcs_paths.extend(history_gcs_paths)

    try:
        if audio_gcs_paths:
            logger.info(f"Audio Files List: {audio_gcs_paths}")
            for audio_gcs_path in audio_gcs_paths:
                audio_folder, audio_file = os.path.split(audio_gcs_path)
                audio_file_obj = await storage_service.download_document(audio_folder, audio_file)
                audio_bytes = audio_file_obj.read()

                if not audio_mimetype:
                    audio_mimetype, _ = mimetypes.guess_type(audio_file)

                transcript_text = gemini_service.call_gemini(
                    prompt=PromptsTemplates.diarize_conversation(),
                    audio_content=audio_bytes,
                    mime_type=audio_mimetype
                )

                combined_text_parts.append(f"\nAUDIO CONVERSATION TEXT: \n{transcript_text}")

        if local_image_paths:
            for image in local_image_paths:
                path = image.get("file_path")
                mime_type = image.get("mime_type")

                try:
                    scanned_text = await documentai_service.extract_text(
                        file_path=path,
                        mime_type=mime_type
                    )
                    combined_text_parts.append(f"\nSCANNED DOCUMENT TEXT: \n{scanned_text}")
                finally:
                    try:
                        os.remove(path)
                    except Exception as e:
                        logger.warning(f"Could not delete temp image file {path}: {e}")

        if gcs_paths:
            for file in gcs_paths:
                path = file.get("file_path")
                mime_type: str = file.get("mime_type")

                folder, filename = os.path.split(path)
                logger.info(f"Downloading File: {filename} from Folder: {folder}")
                file_obj = await storage_service.download_document(folder, filename)
                
                if mime_type.startswith("audio/"):
                    audio_bytes = file_obj.read()
                    text = gemini_service.call_gemini(
                        prompt=PromptsTemplates.diarize_conversation(),
                        audio_content=audio_bytes,
                        mime_type=mime_type
                    )
                    logger.info(f"TRANSCRIPT TEXT: {text}")
                    combined_text_parts.append(f"\nAUDIO CONVERSATION TEXT: \n{text}")

        if policy_id_or_customer_name:
            logger.info("Retrieving customer's policy record from BigQuery...")
            customer_record = await record_repo.get_policy_by_customer_name(policy_id_or_customer_name) \
                or await record_repo.get_policy_by_policy_id(policy_id_or_customer_name)

        if not customer_record:
            logger.warning(f"No matching policy record found for {policy_id_or_customer_name}")
            customer_record = "N/A"
        
        combined_text_parts.append(f"\nCUSTOMER POLICY RECORD: \n{customer_record}")
        
        combined_text = "\n".join(combined_text_parts)

        logger.info(f"COMBINED TEXTS: \n\n{combined_text}")

        transcript_summary = gemini_service.call_gemini(
                prompt=PromptsTemplates.summarize_transcript(transcript=combined_text)
            )
        
        logger.info(f"TRANSCRIPT SUMMARY TEXTS: \n\n{transcript_summary}")

        logger.info("Starting RAG Pipeline...")

        response = await rag_service.run(
            combined_text=combined_text,
            instruction=PromptsTemplates.recommendation_prompt(combined_text=combined_text)
        )

        return {"response": response, "summary": transcript_summary}

    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
    
@router.post("/sync-history")
async def update_history(
    record_repo: PolicyRecordRepository = Depends(PolicyRecordRepository)
):
    try:
        metadata_list = await email_service.process_files(record_repo=record_repo)

        if not metadata_list:
            return JSONResponse(
                content="No update found for today. History Data Successfully Synced!",
                status_code=status.HTTP_200_OK
            )

        for metadata in metadata_list:
            await record_repo.create_metadata_record(metadata_record=FileMetadataRecord(**metadata))

        response = JSONResponse(
            content="History Data Successfully Synced!",
            status_code=status.HTTP_200_OK
        )

        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/get-history-data")
async def get_history_data(
    request: FileNamesRequest,
    record_repo: PolicyRecordRepository = Depends(PolicyRecordRepository)
):
    logger.info(f"Received file names: {request.file_names}") 
    
    if not request.file_names:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one file name is required"
        )
    
    try:
        file_gcs_paths = await record_repo.get_storage_paths(
            file_names=[request.file_names]
        )
        
        if not file_gcs_paths:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No files found for the given names"
            )
            
        return file_gcs_paths
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    
@router.get("/get-file-names")
async def get_file_names(
    record_repo: PolicyRecordRepository = Depends(PolicyRecordRepository)
):
    try:
        records = await record_repo.get_file_names()
        return records
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )