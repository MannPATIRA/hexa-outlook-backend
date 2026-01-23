from fastapi import APIRouter, HTTPException
from typing import List
from ...services.mock_erp import MockERP
from ...models.pr import PurchaseRequisition
from ..schemas.pr_schemas import PRResponse, PRListResponse

router = APIRouter()

# Initialize MockERP instance (in production, this would be dependency injected)
mock_erp = MockERP()


@router.get("/open", response_model=PRListResponse)
async def get_open_prs():
    """
    Get all open purchase requisitions.
    
    Returns a list of all PRs with status 'open' from the ERP system.
    """
    try:
        open_prs = mock_erp.get_open_prs()
        
        # Convert to response format
        pr_responses = []
        for pr in open_prs:
            pr_responses.append(PRResponse(
                pr_id=pr.pr_id,
                material=pr.material,
                specs=pr.specs,
                drawing_files=pr.drawing_files,
                step_files=pr.step_files,
                quantities=pr.quantities,
                unit=pr.unit,
                description=pr.description,
                status=pr.status,
                created_date=pr.created_date.isoformat(),
            ))
        
        return PRListResponse(prs=pr_responses)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving open PRs: {str(e)}"
        )
