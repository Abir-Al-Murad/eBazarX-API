from fastapi import status


class BusinessError(Exception):
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class InsufficientStockError(BusinessError):
    def __init__(self, message: str = "Insufficient stock"):
        super().__init__(message, status.HTTP_400_BAD_REQUEST)


class InvalidCouponError(BusinessError):
    def __init__(self, message: str = "Invalid coupon"):
        super().__init__(message, status.HTTP_400_BAD_REQUEST)


class PaymentError(BusinessError):
    def __init__(self, message: str = "Payment failed"):
        super().__init__(message, status.HTTP_402_PAYMENT_REQUIRED)


class UnauthorizedError(BusinessError):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class ForbiddenError(BusinessError):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, status.HTTP_403_FORBIDDEN)