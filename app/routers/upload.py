import os
from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from typing import List
import uuid

router = APIRouter(tags=["Media Uploads"])

UPLOAD_DIR = "uploads"

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_media(request: Request, files: List[UploadFile] = File(...)):
    """
    Handle multi-part file uploads (images/videos) natively from the device.
    Saves to the local `./uploads` directory statically hosted by FastAPI.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    # Build base URL from the incoming request so it works from any device
    base_url = f"{request.url.scheme}://{request.headers.get('host', 'localhost:8000')}"

    uploaded_urls = []

    for file in files:
        # Generate a unique robust filename
        ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        unique_filename = f"{uuid.uuid4().hex}.{ext}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        # Write blob buffer to storage memory
        try:
            with open(file_path, "wb") as buffer:
                buffer.write(await file.read())
            
            file_url = f"{base_url}/uploads/{unique_filename}"
            uploaded_urls.append(file_url)

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload: {str(e)}")

    return {"media_urls": uploaded_urls}
