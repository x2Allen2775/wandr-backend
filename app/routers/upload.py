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
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail=f"Invalid file type for {file.filename}. Only images are allowed.")

        if hasattr(file, "size") and file.size is not None:
            if file.size > 10 * 1024 * 1024:
                raise HTTPException(status_code=413, detail=f"File {file.filename} is too large. Limit is 10MB.")

        # Read into memory safely assuming size is valid or checking length
        file_content = await file.read()
        if len(file_content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail=f"File {file.filename} is too large. Limit is 10MB.")
        
        # Determine if we can use Cloudinary
        from app.config import settings
        use_cloudinary = bool(settings.CLOUDINARY_CLOUD_NAME and settings.CLOUDINARY_API_KEY and settings.CLOUDINARY_API_SECRET)

        if not use_cloudinary:
            raise HTTPException(status_code=500, detail="Cloudinary credentials missing in Render environment variables.")
            
        if cloudinary is None:
            raise HTTPException(status_code=500, detail="Cloudinary Python package failed to import on Render.")

        try:
            # We must use file.file (SpooledTemporaryFile) for Cloudinary, not raw bytes (file_content)
            # Some versions of Python Cloudinary SDK fail silently or raise errors with raw bytes
            file.file.seek(0)
            response = cloudinary.uploader.upload(file.file)
            uploaded_urls.append(response.get("secure_url"))
        except Exception as e:
            logging.error(f"Cloudinary upload failed: {e}")
            raise HTTPException(status_code=500, detail=f"Cloudinary upload failed: {str(e)}")

    return {"media_urls": uploaded_urls}
