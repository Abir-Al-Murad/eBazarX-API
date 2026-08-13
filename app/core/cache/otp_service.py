import random
from datetime import datetime, timedelta
from app.core.cache.redis_service import redis_service
from app.core.config import settings

class OTPService:
    @staticmethod
    def generate_otp() -> str:
        return ''.join(random.choices('0123456789', k=settings.OTP_LENGTH))

    @staticmethod
    async def store_otp(email: str, otp: str) -> None:
        key = f"otp:{email}"
        await redis_service.set(key, otp, ttl=settings.OTP_EXPIRE_SECONDS)

    @staticmethod
    async def get_otp(email: str) -> str | None:
        key = f"otp:{email}"
        return await redis_service.get(key)

    @staticmethod
    async def verify_otp(email: str, otp: str) -> bool:
        stored_otp = await OTPService.get_otp(email)
        if stored_otp and stored_otp == otp:
            await redis_service.delete(f"otp:{email}")
            return True
        return False

    @staticmethod
    async def is_otp_valid(email: str) -> bool:
        return await redis_service.exists(f"otp:{email}")