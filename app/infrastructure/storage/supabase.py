from supabase import create_client, Client
from app.core.config import settings
import io

class SupabaseStorage:
    def __init__(self):
        self.client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY.get_secret_value())
        self.bucket = settings.SUPABASE_BUCKET

    async def upload_file(self, file_bytes: bytes, filename: str, content_type: str = "image/jpeg") -> str:
        # Upload to Supabase Storage
        file_path = f"{filename}"
        self.client.storage.from_(self.bucket).upload(file_path, file_bytes, {"content-type": content_type})
        # Get public URL
        return self.client.storage.from_(self.bucket).get_public_url(file_path)