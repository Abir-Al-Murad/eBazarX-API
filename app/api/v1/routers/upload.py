from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from typing import Optional
from app.api.v1.dependencies.auth import get_current_user
from app.infrastructure.database.models import User
from app.infrastructure.storage.cloudinary import CloudinaryService
from app.core.exceptions import BusinessError

router = APIRouter(prefix="/upload", tags=["Upload"])

@router.post("/image")
async def upload_image(
    file: UploadFile = File(...),
    folder: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """Upload an image to Cloudinary. Requires authentication."""
    try:
        service = CloudinaryService()
        # Use provided folder or default to "ebazar"
        upload_folder = folder or "ebazar"
        result = await service.upload_image(file, folder=upload_folder)
        return {
            "success": True,
            "data": {
                "url": result["url"],
                "public_id": result["public_id"],
                "format": result["format"],
                "width": result["width"],
                "height": result["height"],
            },
            "message": "Image uploaded successfully",
        }
    except BusinessError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")