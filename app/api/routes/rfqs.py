from fastapi import APIRouter, HTTPException
import json
from ...services.mock_erp import MockERP
from ...services.supplier_service import SupplierService
from ...services.rfq_service import RFQService
from ...services.auto_reply_service import AutoReplyService
from ..schemas.rfq_schemas import (
    RFQGenerateRequest,
    RFQResponse,
    RFQListResponse,
    RFQFinalizeRequest,
    RFQFinalizeResponse,
    RFQMarkSentRequest,
    RFQMarkSentResponse
)

router = APIRouter()

# Initialize services (in production, this would be dependency injected)
mock_erp = MockERP()
supplier_service = SupplierService(mock_erp)
rfq_service = RFQService(mock_erp)
auto_reply_service = AutoReplyService()


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


@router.post("/mark-sent", response_model=RFQMarkSentResponse)
async def mark_rfqs_sent(request: RFQMarkSentRequest):
    """
    Mark RFQs as sent after they've been successfully sent via Outlook.
    
    This endpoint:
    - Updates RFQ status to "sent" in the backend
    - Optionally schedules auto-replies for each sent RFQ
    - Returns confirmation of which RFQs were marked as sent
    
    The frontend should call this after successfully sending RFQ emails via Outlook API.
    """
    try:
        marked_sent = []
        failed = []
        auto_replies_scheduled = 0
        
        for sent_rfq in request.rfqs:
            try:
                # Verify RFQ exists
                rfq = mock_erp.get_rfq_by_id(sent_rfq.rfq_id)
                if not rfq:
                    failed.append(sent_rfq.rfq_id)
                    continue
                
                # Update RFQ status to "sent"
                mock_erp.update_rfq_status(sent_rfq.rfq_id, "sent")
                marked_sent.append(sent_rfq.rfq_id)
                
                # Schedule auto-reply if requested
                if request.schedule_auto_replies:
                    # Get supplier info from RFQ
                    supplier = mock_erp.get_supplier_by_id(rfq.supplier_id)
                    supplier_id = rfq.supplier_id if rfq.supplier_id else None
                    supplier_name = supplier.name if supplier else None
                    
                    # Get PR to extract material
                    pr = mock_erp.get_pr_by_id(rfq.pr_id)
                    material = pr.material if pr else "Unknown Material"
                    quantity = pr.quantities if pr else 100
                    
                    # Schedule auto-reply
                    if auto_reply_service.is_configured():
                        result = auto_reply_service.schedule_reply(
                            to_email=sent_rfq.to_email,
                            original_subject=sent_rfq.subject,
                            original_message_id=sent_rfq.message_id,
                            material=material,
                            reply_type="random",  # Random reply type for variety
                            delay_seconds=30,  # 30 second delay
                            quantity=quantity,
                            supplier_id=supplier_id,
                            supplier_name=supplier_name
                        )
                        
                        if result.get("success"):
                            auto_replies_scheduled += 1
                    else:
                        # Auto-reply not configured, but RFQ still marked as sent
                        pass
                
            except Exception as e:
                # Log error but continue with other RFQs
                print(f"Error processing RFQ {sent_rfq.rfq_id}: {e}")
                failed.append(sent_rfq.rfq_id)
        
        # Build response message
        if failed:
            message = f"{len(marked_sent)} RFQ(s) marked as sent, {len(failed)} failed"
        else:
            message = f"{len(marked_sent)} RFQ(s) marked as sent"
        
        if request.schedule_auto_replies:
            message += f", {auto_replies_scheduled} auto-reply(ies) scheduled"
        
        return RFQMarkSentResponse(
            marked_sent=marked_sent,
            failed=failed,
            auto_replies_scheduled=auto_replies_scheduled,
            message=message
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error marking RFQs as sent: {str(e)}"
        )
