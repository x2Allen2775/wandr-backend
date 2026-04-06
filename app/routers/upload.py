import os
from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from typing import List
import uuid
import logging

try:
    import cloudinary
    import cloudinary.uploader
except ImportError:
    cloudinary = None

router = APIRouter(tags=["Media Uploads"])

UPLOAD_DIR = "uploads"

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_media(request: Request, files: List[UploadFile] = File(...)):
    """
    Handle multi-part file uploads (images/videos).
    Uploads to Cloudinary if configured; otherwise, saves to local `./uploads`.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    base_url = f"{request.url.scheme}://{request.headers.get('host', 'localhost:8000')}"
    uploaded_urls = []

    for file in files:
        file_content = await file.read()
        
        # Determine if we can use Cloudinary
        from app.config import settings
        use_cloudinary = bool(settings.CLOUDINARY_CLOUD_NAME and settings.CLOUDINARY_API_KEY and settings.CLOUDINARY_API_SECRET)

        if use_cloudinary and cloudinary:
            try:
                # Upload to Cloudinary
                response = cloudinary.uploader.upload(file_content)
                uploaded_urls.append(response.get("secure_url"))
            except Exception as e:
                logging.error(f"Cloudinary upload failed: {e}")
                raise HTTPException(status_code=500, detail=f"Cloudinary upload failed: {str(e)}")
        else:
            # Fallback to Local Storage
            ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
            unique_filename = f"{uuid.uuid4().hex}.{ext}"
            file_path = os.path.join(UPLOAD_DIR, unique_filename)

            try:
                with open(file_path, "wb") as buffer:
                    buffer.write(file_content)
                
                file_url = f"{base_url}/uploads/{unique_filename}"
                uploaded_urls.append(file_url)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to upload locally: {str(e)}")

    return {"media_urls": uploaded_urls}
