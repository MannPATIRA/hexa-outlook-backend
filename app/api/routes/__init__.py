from fastapi import APIRouter
from . import prs, suppliers, rfqs, emails, quotes, demo

api_router = APIRouter()

api_router.include_router(prs.router, prefix="/prs", tags=["Purchase Requisitions"])
api_router.include_router(suppliers.router, prefix="/suppliers", tags=["Suppliers"])
api_router.include_router(rfqs.router, prefix="/rfqs", tags=["RFQs"])
api_router.include_router(emails.router, prefix="/emails", tags=["Emails"])
api_router.include_router(quotes.router, prefix="/quotes", tags=["Quotes"])
api_router.include_router(demo.router, prefix="/demo", tags=["Demo & Testing"])