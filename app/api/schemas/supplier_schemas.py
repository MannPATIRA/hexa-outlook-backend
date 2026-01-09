from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class SupplierSearchRequest(BaseModel):
    """Request schema for searching suppliers."""
    
    pr_id: str
    material: Optional[str] = None
    specs: Optional[dict] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "pr_id": "PR-001",
                "material": "MAT-12345",
                "specs": {
                    "material_type": "Steel Component",
                    "grade": "SS304"
                }
            }
        }
    )


class SupplierResponse(BaseModel):
    """Response schema for a single Supplier."""
    
    supplier_id: str
    name: str
    email: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    match_reason: str
    match_score: Optional[int] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "supplier_id": "SUP-001",
                "name": "ABC Manufacturing",
                "email": "procurement@abcmanufacturing.com",
                "contact_person": "John Smith",
                "phone": "+1-555-0101",
                "match_reason": "Standard supplier for MAT-12345",
                "match_score": 10
            }
        }
    )


class SupplierListResponse(BaseModel):
    """Response schema for a list of Suppliers."""
    
    suppliers: List[SupplierResponse]
