from fastapi import APIRouter, HTTPException
from ...services.mock_erp import MockERP
from ...services.supplier_service import SupplierService
from ..schemas.supplier_schemas import (
    SupplierSearchRequest,
    SupplierResponse,
    SupplierListResponse
)

router = APIRouter()

# Initialize services (in production, this would be dependency injected)
mock_erp = MockERP()
supplier_service = SupplierService(mock_erp)


@router.post("/search", response_model=SupplierListResponse)
async def search_suppliers(request: SupplierSearchRequest):
    """
    Search for suppliers matching a Purchase Requisition.
    
    Takes a PR ID and optional material/specs, and returns matching suppliers
    with match reasons. Suppliers are ranked by relevance.
    """
    try:
        # Get the PR
        pr = mock_erp.get_pr_by_id(request.pr_id)
        if not pr:
            raise HTTPException(
                status_code=404,
                detail=f"Purchase Requisition {request.pr_id} not found"
            )
        
        # Find matching suppliers
        matching_suppliers = supplier_service.find_matching_suppliers(pr)
        
        # Convert to response format
        supplier_responses = []
        for supplier_info in matching_suppliers:
            supplier_responses.append(SupplierResponse(
                supplier_id=supplier_info["supplier_id"],
                name=supplier_info["name"],
                email=supplier_info["email"],
                contact_person=supplier_info.get("contact_person"),
                phone=supplier_info.get("phone"),
                match_reason=supplier_info["match_reason"],
                match_score=supplier_info.get("match_score"),
            ))
        
        return SupplierListResponse(suppliers=supplier_responses)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error searching suppliers: {str(e)}"
        )
