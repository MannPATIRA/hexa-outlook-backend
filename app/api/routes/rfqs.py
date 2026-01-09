from fastapi import APIRouter, HTTPException
import json
from ...services.mock_erp import MockERP
from ...services.supplier_service import SupplierService
from ...services.rfq_service import RFQService
from ..schemas.rfq_schemas import (
    RFQGenerateRequest,
    RFQResponse,
    RFQListResponse,
    RFQFinalizeRequest,
    RFQFinalizeResponse
)

router = APIRouter()

# Initialize services (in production, this would be dependency injected)
mock_erp = MockERP()
supplier_service = SupplierService(mock_erp)
rfq_service = RFQService(mock_erp)


@router.post("/generate", response_model=RFQListResponse)
async def generate_rfqs(request: RFQGenerateRequest):
    """
    Generate RFQ content for selected suppliers based on a PR.
    
    Takes a PR ID and list of supplier IDs, and returns structured RFQ content
    for each supplier. The RFQ content is in JSON format that can be rendered
    as an email by the Outlook add-in.
    """
    try:
        # Get the PR
        pr = mock_erp.get_pr_by_id(request.pr_id)
        if not pr:
            raise HTTPException(
                status_code=404,
                detail=f"Purchase Requisition {request.pr_id} not found"
            )
        
        # Get the suppliers
        suppliers = supplier_service.get_suppliers_by_ids(request.supplier_ids)
        if not suppliers:
            raise HTTPException(
                status_code=404,
                detail="No valid suppliers found for the provided supplier IDs"
            )
        
        if len(suppliers) != len(request.supplier_ids):
            # Some supplier IDs were invalid
            found_ids = {s.supplier_id for s in suppliers}
            invalid_ids = [sid for sid in request.supplier_ids if sid not in found_ids]
            raise HTTPException(
                status_code=404,
                detail=f"Invalid supplier IDs: {', '.join(invalid_ids)}"
            )
        
        # Generate RFQs
        rfqs = rfq_service.generate_rfqs(pr, suppliers)
        
        # Convert to response format
        rfq_responses = []
        for rfq in rfqs:
            supplier = mock_erp.get_supplier_by_id(rfq.supplier_id)
            rfq_responses.append(RFQResponse(
                rfq_id=rfq.rfq_id,
                supplier_id=rfq.supplier_id,
                supplier_name=supplier.name if supplier else "Unknown",
                supplier_email=supplier.email if supplier else "",
                pr_id=rfq.pr_id,
                subject=rfq.subject,
                body=rfq.body,
                attachments=rfq.attachments,
                status=rfq.status,
            ))
        
        return RFQListResponse(rfqs=rfq_responses)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating RFQs: {str(e)}"
        )


@router.post("/finalize", response_model=RFQFinalizeResponse)
async def finalize_rfq(request: RFQFinalizeRequest):
    """
    Finalize an RFQ with user-edited content.
    
    Receives the finalized RFQ content from the Outlook add-in after the user
    has reviewed and edited it. Updates the RFQ status to 'finalized'.
    """
    try:
        # Parse final_body if it's a JSON string
        final_body = request.final_body
        if isinstance(request.final_body, str):
            try:
                final_body = json.loads(request.final_body)
            except json.JSONDecodeError:
                # If it's not valid JSON, treat as plain text
                final_body = {"content": request.final_body}
        
        # Finalize the RFQ
        rfq = rfq_service.finalize_rfq(
            request.rfq_id,
            request.final_subject,
            final_body
        )
        
        return RFQFinalizeResponse(
            rfq_id=rfq.rfq_id,
            status=rfq.status,
            message="RFQ finalized successfully"
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error finalizing RFQ: {str(e)}"
        )
