from fastapi import APIRouter, Depends
from app.application.services.product_service import ProductService
from app.api.v1.dependencies.services import get_product_service

router = APIRouter(prefix="/public", tags=["Public"])

@router.get("/products")
async def list_products(skip: int = 0, limit: int = 20, product_service: ProductService = Depends(get_product_service)):
    products = await product_service.get_approved_products(skip, limit)
    return products