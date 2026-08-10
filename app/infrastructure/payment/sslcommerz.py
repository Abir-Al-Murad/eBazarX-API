import hashlib
import hmac
import json
import time
import httpx
from typing import Dict, Any
from app.core.config import settings

class SSLCommerzService:
    def __init__(self):
        self.store_id = settings.SSLCOMMERZ_STORE_ID
        self.store_pass = settings.SSLCOMMERZ_STORE_PASS.get_secret_value()
        self.base_url = settings.SSLCOMMERZ_BASE_URL

    async def initiate_payment(self, order_id: str, amount: float, customer_name: str, customer_email: str, customer_phone: str) -> Dict[str, Any]:
        """
        Initiate SSLCommerz payment session.
        Returns the redirect URL and session key.
        """
        transaction_id = f"EBZ-{order_id[:8]}-{int(time.time())}"
        data = {
            "store_id": self.store_id,
            "store_passwd": self.store_pass,
            "total_amount": amount,
            "currency": "BDT",
            "tran_id": transaction_id,
            "success_url": f"https://your-domain.com/api/v1/payments/sslcommerz/success?order_id={order_id}",
            "fail_url": f"https://your-domain.com/api/v1/payments/sslcommerz/fail?order_id={order_id}",
            "cancel_url": f"https://your-domain.com/api/v1/payments/sslcommerz/cancel?order_id={order_id}",
            "cus_name": customer_name,
            "cus_email": customer_email,
            "cus_phone": customer_phone,
            "shipping_method": "NO",
            "product_name": "Order",
            "product_category": "Ecommerce",
            "product_profile": "general",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/gwprocess/v4/api.php",
                data=data,
                timeout=30.0
            )
            result = response.json()
            if result.get("status") == "SUCCESS":
                return {
                    "success": True,
                    "redirect_url": result["GatewayPageURL"],
                    "session_key": result["sessionkey"],
                    "transaction_id": transaction_id,
                }
            else:
                return {
                    "success": False,
                    "message": result.get("failedreason", "Payment initiation failed"),
                }

    async def verify_payment(self, transaction_id: str) -> Dict[str, Any]:
        """
        Verify payment status with SSLCommerz.
        """
        data = {
            "store_id": self.store_id,
            "store_passwd": self.store_pass,
            "tran_id": transaction_id,
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/validator/api/validationserverAPI.php",
                data=data,
                timeout=30.0
            )
            return response.json()