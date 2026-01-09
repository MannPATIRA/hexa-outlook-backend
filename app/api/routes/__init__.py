from fastapi import APIRouter
from . import prs, suppliers, rfqs

api_router = APIRouter()

api_router.include_router(prs.router, prefix="/prs", tags=["Purchase Requisitions"])
api_router.include_router(suppliers.router, prefix="/suppliers", tags=["Suppliers"])
api_router.include_router(rfqs.router, prefix="/rfqs", tags=["RFQs"])
