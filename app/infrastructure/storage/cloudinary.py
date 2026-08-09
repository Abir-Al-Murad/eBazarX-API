import cloudinary
import cloudinary.uploader
from cloudinary.exceptions import Error as CloudinaryError
from fastapi import UploadFile
from app.core.config import settings
from app.core.exceptions import BusinessError
from typing import Optional

class CloudinaryService:
    def __init__(self):
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET.get_secret_value(),
            secure=True,
        )

    async def upload_image(
        self,
        file: UploadFile,
        folder: str = "ebazar",
        public_id: Optional[str] = None,
        transformation: Optional[dict] = None,
    ) -> dict:
        """Upload an image to Cloudinary and return the secure URL."""
        # Validate file type
        allowed_mime_types = ["image/jpeg", "image/png", "image/webp", "image/gif"]
        if file.content_type not in allowed_mime_types:
            raise BusinessError(
                f"File type {file.content_type} not allowed. Allowed: {', '.join(allowed_mime_types)}"
            )

        # Validate file size (5MB)
        file_size = 0
        contents = await file.read()
        file_size = len(contents)
        if file_size > settings.MAX_UPLOAD_SIZE:
            raise BusinessError(f"File size exceeds {settings.MAX_UPLOAD_SIZE // (1024*1024)} MB limit")

        # Reset file pointer
        await file.seek(0)

        try:
            # Upload to Cloudinary
            upload_options = {
                "folder": folder,
                "use_filename": True,
                "unique_filename": True,
                "overwrite": False,
                "resource_type": "image",
            }
            if public_id:
                upload_options["public_id"] = public_id
            if transformation:
                upload_options["transformation"] = transformation

            result = cloudinary.uploader.upload(file.file, **upload_options)

            return {
                "public_id": result["public_id"],
                "url": result["secure_url"],
                "format": result["format"],
                "width": result["width"],
                "height": result["height"],
                "bytes": result["bytes"],
            }
        except CloudinaryError as e:
            raise BusinessError(f"Cloudinary upload failed: {str(e)}")
        except Exception as e:
            raise BusinessError(f"Upload failed: {str(e)}")
        finally:
            await file.close()