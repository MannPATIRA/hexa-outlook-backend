"""
Demo/testing API endpoints for simulating supplier email replies.

These endpoints allow you to trigger automatic email replies that will
appear as threaded replies to RFQ emails - perfect for demos and testing.
"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from ...services.auto_reply_service import AutoReplyService

router = APIRouter()

# Initialize the auto-reply service
auto_reply_service = AutoReplyService()


# ============================================================================
# Request/Response Schemas
# ============================================================================

class AutoReplyRequest(BaseModel):
    """Request to schedule an automatic email reply."""
    
    to_email: str  # The user's email (where to send the reply)
    original_subject: str  # Subject of the original RFQ email
    original_message_id: str  # Message-ID header of original email (for threading)
    material: str  # Material name for generating reply content
    reply_type: str = "quote"  # "quote", "clarification_procurement", "clarification_engineering", or "random"
    delay_seconds: int = 5  # How long to wait before sending
    quantity: int = 100  # Quantity for quote calculations
    supplier_id: Optional[str] = None  # Supplier ID for tracking
    supplier_name: Optional[str] = None  # Supplier name for display
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "to_email": "user@company.com",
                "original_subject": "RFQ for Steel Brackets - 100 pcs",
                "original_message_id": "<abc123@mail.outlook.com>",
                "material": "Steel Brackets",
                "reply_type": "quote",
                "delay_seconds": 5,
                "quantity": 100,
                "supplier_id": "SUP-001",
                "supplier_name": "ABC Manufacturing"
            }
        }
    )


class AutoReplyResponse(BaseModel):
    """Response after scheduling an auto-reply."""
    
    success: bool
    reply_id: Optional[str] = None
    message: str
    to_email: Optional[str] = None
    reply_type: Optional[str] = None
    error: Optional[str] = None


class TestConnectionResponse(BaseModel):
    """Response from connection test."""
    
    success: bool
    message: Optional[str] = None
    sender_email: Optional[str] = None
    error: Optional[str] = None


class ScheduledReplyInfo(BaseModel):
    """Information about a scheduled reply."""
    
    reply_id: str
    to_email: str
    subject: str
    scheduled_time: str
    status: str


class DemoStatusResponse(BaseModel):
    """Current demo system status."""
    
    configured: bool
    sender_email: Optional[str] = None
    scheduled_replies: List[ScheduledReplyInfo]
    message: str


class RFQDetail(BaseModel):
    """Details for a single RFQ to schedule replies for."""
    
    to_email: str  # The user's email (where to send the reply)
    original_subject: str  # Subject of the original RFQ email
    original_message_id: str  # Message-ID header of original email (for threading)
    material: str  # Material name for generating reply content
    quantity: int = 100  # Quantity for quote calculations
    pr_id: Optional[str] = None  # Optional PR ID for special handling (e.g., PR001)
    supplier_id: Optional[str] = None  # Supplier ID for tracking
    supplier_name: Optional[str] = None  # Supplier name for display


class BatchAutoReplyRequest(BaseModel):
    """Request to schedule multiple auto-replies with guaranteed distribution."""
    
    rfqs: List[RFQDetail]  # List of RFQ details
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "rfqs": [
                    {
                        "to_email": "user@company.com",
                        "original_subject": "RFQ for Steel Brackets - 100 pcs",
                        "original_message_id": "<abc123@mail.outlook.com>",
                        "material": "Steel Brackets",
                        "quantity": 100
                    }
                ]
            }
        }
    )


class ScheduledReplyDetail(BaseModel):
    """Details of a scheduled reply."""
    
    reply_id: str
    to_email: str
    reply_type: str
    delay_seconds: int


class BatchAutoReplyResponse(BaseModel):
    """Response after scheduling batch auto-replies."""
    
    success: bool
    total_scheduled: int
    scheduled_replies: List[ScheduledReplyDetail]
    distribution: dict
    message: str
    error: Optional[str] = None


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/status", response_model=DemoStatusResponse)
async def get_demo_status():
    """
    Get the current status of the demo email system.
    
    Shows whether SMTP is configured and lists all scheduled/sent replies.
    """
    configured = auto_reply_service.is_configured()
    
    return DemoStatusResponse(
        configured=configured,
        sender_email=auto_reply_service.sender_email if configured else None,
        scheduled_replies=[
            ScheduledReplyInfo(**r) 
            for r in auto_reply_service.get_scheduled_replies()
        ],
        message="Demo system is ready!" if configured else "Not configured. Set environment variables."
    )


@router.get("/test-connection", response_model=TestConnectionResponse)
async def test_smtp_connection():
    """
    Test the SMTP connection without sending an email.
    
    Use this to verify your Gmail credentials are working correctly.
    """
    result = auto_reply_service.test_connection()
    return TestConnectionResponse(**result)


@router.post("/schedule-reply", response_model=AutoReplyResponse)
async def schedule_auto_reply(request: AutoReplyRequest):
    """
    Schedule an automatic email reply to be sent after a delay.
    
    **IMPORTANT:** If you're sending multiple RFQs, use `/schedule-replies-batch` instead
    to guarantee minimum distribution (1 engineering, 1 procurement, 3 quotes) with proper threading.
    
    **How to use:**
    
    1. From your Outlook add-in, after sending an RFQ, get the Message-ID
    2. Call this endpoint with the Message-ID and user's email
    3. Wait for the specified delay
    4. The reply will appear in the user's inbox as a threaded reply
    
    **Reply Types:**
    - `quote`: Generates a quotation response with pricing
    - `clarification_procurement`: Generates commercial questions
    - `clarification_engineering`: Generates technical questions
    - `random`: Randomly picks one of the above
    """
    import random
    
    # Handle random reply type
    reply_type = request.reply_type
    if reply_type == "random":
        reply_type = random.choice([
            "quote", "quote", "quote",  # 60% chance of quote
            "clarification_procurement",  # 20% chance
            "clarification_engineering"   # 20% chance
        ])
    
    # Validate reply type
    valid_types = ["quote", "clarification_procurement", "clarification_engineering"]
    if reply_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid reply_type. Must be one of: {valid_types} or 'random'"
        )
    
    # Log request for debugging
    logger = logging.getLogger(__name__)
    logger.info(f"Received schedule-reply request - supplier_id: {request.supplier_id}, supplier_name: {request.supplier_name}")
    
    result = auto_reply_service.schedule_reply(
        to_email=request.to_email,
        original_subject=request.original_subject,
        original_message_id=request.original_message_id,
        material=request.material,
        reply_type=reply_type,
        delay_seconds=request.delay_seconds,
        quantity=request.quantity,
        supplier_id=request.supplier_id,
        supplier_name=request.supplier_name
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=503,
            detail=result.get("error", "Failed to schedule reply")
        )
    
    return AutoReplyResponse(
        success=True,
        reply_id=result.get("reply_id"),
        message=result.get("message", "Reply scheduled"),
        to_email=result.get("to_email"),
        reply_type=reply_type
    )


@router.post("/quick-test")
async def quick_test_send(to_email: str):
    """
    Send a quick test email to verify everything works.
    
    This immediately sends a test email (no delay) to the specified address.
    Use this to verify your setup before doing a full demo.
    """
    if not auto_reply_service.is_configured():
        raise HTTPException(
            status_code=503,
            detail="SMTP not configured. Set DEMO_SUPPLIER_EMAIL and DEMO_SUPPLIER_PASSWORD environment variables."
        )
    
    result = auto_reply_service.schedule_reply(
        to_email=to_email,
        original_subject="Test Email - Please Ignore",
        original_message_id="",  # No threading for test
        material="Test Material",
        reply_type="quote",
        delay_seconds=1,  # Send almost immediately
        quantity=100
    )
    
    return {
        "success": True,
        "message": f"Test email will be sent to {to_email} in 1 second",
        "reply_id": result.get("reply_id")
    }


@router.post("/test-supplier-name")
async def test_supplier_name(supplier_name: str, to_email: str = "test@example.com"):
    """
    Test endpoint to verify supplier name is used correctly in email display.
    
    This endpoint allows you to test if a specific supplier name will appear
    in the email "From" field. Useful for debugging supplier name display issues.
    """
    if not auto_reply_service.is_configured():
        raise HTTPException(
            status_code=503,
            detail="SMTP not configured. Set DEMO_SUPPLIER_EMAIL and DEMO_SUPPLIER_PASSWORD environment variables."
        )
    
    result = auto_reply_service.schedule_reply(
        to_email=to_email,
        original_subject="Test Supplier Name",
        original_message_id="<test>",
        material="Test Material",
        reply_type="quote",
        delay_seconds=1,
        quantity=100,
        supplier_id="SUP-001",
        supplier_name=supplier_name
    )
    
    return {
        "success": True,
        "received_supplier_name": supplier_name,
        "display_name_used": result.get("supplier_name"),
        "message": f"Test email will be sent to {to_email} with supplier name: {result.get('supplier_name')}",
        "reply_id": result.get("reply_id")
    }


@router.post("/schedule-replies-batch", response_model=BatchAutoReplyResponse)
async def schedule_batch_auto_replies(request: BatchAutoReplyRequest):
    """
    Schedule multiple auto-replies with guaranteed distribution.
    
    Ensures that replies always include:
    - At least 1 engineering clarification
    - At least 1 procurement clarification
    - At least 3 quotes
    
    Special handling for PR001: Ensures exactly 3 quotes and 2 clarifications (1 engineering + 1 procurement).
    
    If fewer RFQs are sent than needed for minimums, schedules multiple replies per RFQ.
    Replies are sent with staggered delays (5s, 10s, 15s, etc.) so they arrive sequentially.
    """
    if not auto_reply_service.is_configured():
        raise HTTPException(
            status_code=503,
            detail="SMTP not configured. Set DEMO_SUPPLIER_EMAIL and DEMO_SUPPLIER_PASSWORD environment variables."
        )
    
    num_rfqs = len(request.rfqs)
    if num_rfqs == 0:
        raise HTTPException(
            status_code=400,
            detail="At least one RFQ is required"
        )
    
    # Check if this is for PR001
    # PR001 can be identified by multiple signals:
    # 1. pr_id field set to "PR-001" or "PR001"
    # 2. Material "MAT-12345" with exactly 5 RFQs
    # 3. Subject line containing "PR-001" or "PR001"
    is_pr001 = False
    pr_ids = {rfq.pr_id for rfq in request.rfqs if rfq.pr_id}
    subjects = {rfq.original_subject for rfq in request.rfqs}
    materials = {rfq.material for rfq in request.rfqs}
    
    # Check multiple signals for PR001 detection
    if pr_ids:
        # Check if any RFQ has PR001 as pr_id
        if any(pr_id in ["PR-001", "PR001"] for pr_id in pr_ids):
            is_pr001 = True
    elif num_rfqs == 5 and "MAT-12345" in materials:
        # Fallback: Check if all RFQs have the same material and it's MAT-12345
        if len(materials) == 1:
            is_pr001 = True
    elif any("PR-001" in subj or "PR001" in subj for subj in subjects):
        # Check subject lines for PR001 reference
        is_pr001 = True
    
    # Additional check: if we have exactly 5 RFQs with MAT-12345, treat as PR001
    if not is_pr001 and num_rfqs == 5 and "MAT-12345" in materials:
        is_pr001 = True
    
    # Required distribution - special handling for PR001
    if is_pr001:
        # PR001: exactly 3 quotes + 2 clarifications (1 engineering + 1 procurement)
        REQUIRED_DISTRIBUTION = {
            "clarification_engineering": 1,
            "clarification_procurement": 1,
            "quote": 3
        }
        # For PR001, use deterministic order: 3 quotes first, then 2 clarifications
        # This ensures consistent distribution
        reply_types_needed = ["quote"] * 3 + ["clarification_engineering", "clarification_procurement"]
    else:
        # Default distribution
        REQUIRED_DISTRIBUTION = {
            "clarification_engineering": 1,
            "clarification_procurement": 1,
            "quote": 3
        }
        # Build reply types list for non-PR001
        reply_types_needed = []
        for reply_type, count in REQUIRED_DISTRIBUTION.items():
            reply_types_needed.extend([reply_type] * count)
    
    TOTAL_REQUIRED = sum(REQUIRED_DISTRIBUTION.values())  # 5 total
    
    # Build the reply schedule
    reply_schedule = []
    
    # For PR001 with exactly 5 RFQs, assign one reply type per RFQ
    if is_pr001 and num_rfqs == 5:
        # Assign exactly: 3 quotes, 1 engineering clarification, 1 procurement clarification
        # Use deterministic order to ensure correct distribution
        for i, reply_type in enumerate(reply_types_needed):
            reply_schedule.append({
                "rfq": request.rfqs[i],
                "reply_type": reply_type
            })
    elif num_rfqs < TOTAL_REQUIRED:
        # Schedule multiple replies per RFQ to meet minimums
        rfq_index = 0
        for reply_type in reply_types_needed:
            rfq = request.rfqs[rfq_index % num_rfqs]
            reply_schedule.append({
                "rfq": rfq,
                "reply_type": reply_type
            })
            rfq_index += 1
    else:
        # We have enough RFQs, distribute evenly
        # First assign required types
        for i, reply_type in enumerate(reply_types_needed):
            if i < num_rfqs:
                reply_schedule.append({
                    "rfq": request.rfqs[i],
                    "reply_type": reply_type
                })
        
        # Fill remaining RFQs with quotes (most common)
        for i in range(len(reply_types_needed), num_rfqs):
            reply_schedule.append({
                "rfq": request.rfqs[i],
                "reply_type": "quote"
            })
    
    # Validate distribution before scheduling (especially for PR001)
    if is_pr001:
        # Count the scheduled reply types
        scheduled_quotes = sum(1 for item in reply_schedule if item["reply_type"] == "quote")
        scheduled_eng_clar = sum(1 for item in reply_schedule if item["reply_type"] == "clarification_engineering")
        scheduled_proc_clar = sum(1 for item in reply_schedule if item["reply_type"] == "clarification_procurement")
        
        # For PR001, we MUST have exactly 3 quotes and 2 clarifications (1 eng + 1 proc)
        if scheduled_quotes != 3 or scheduled_eng_clar != 1 or scheduled_proc_clar != 1:
            # Fix the distribution if it's wrong
            reply_schedule = []
            # Rebuild with correct distribution: 3 quotes, 1 engineering, 1 procurement
            correct_types = ["quote"] * 3 + ["clarification_engineering", "clarification_procurement"]
            for i, reply_type in enumerate(correct_types):
                if i < num_rfqs:
                    reply_schedule.append({
                        "rfq": request.rfqs[i],
                        "reply_type": reply_type
                    })
    
    # Schedule all replies with staggered delays
    scheduled_replies = []
    base_delay = 5  # Start at 5 seconds
    delay_increment = 5  # 5 seconds between each reply
    
    for i, schedule_item in enumerate(reply_schedule):
        delay = base_delay + (i * delay_increment)
        
        result = auto_reply_service.schedule_reply(
            to_email=schedule_item["rfq"].to_email,
            original_subject=schedule_item["rfq"].original_subject,
            original_message_id=schedule_item["rfq"].original_message_id,
            material=schedule_item["rfq"].material,
            reply_type=schedule_item["reply_type"],
            delay_seconds=delay,
            quantity=schedule_item["rfq"].quantity,
            supplier_id=schedule_item["rfq"].supplier_id,
            supplier_name=schedule_item["rfq"].supplier_name
        )
        
        if result.get("success"):
            scheduled_replies.append(ScheduledReplyDetail(
                reply_id=result.get("reply_id"),
                to_email=schedule_item["rfq"].to_email,
                reply_type=schedule_item["reply_type"],
                delay_seconds=delay
            ))
        else:
            # If any reply fails, return error
            return BatchAutoReplyResponse(
                success=False,
                total_scheduled=len(scheduled_replies),
                scheduled_replies=scheduled_replies,
                distribution=REQUIRED_DISTRIBUTION,
                message=f"Failed to schedule all replies. {len(scheduled_replies)} succeeded.",
                error=result.get("error", "Unknown error")
            )
    
    # Count actual distribution
    actual_distribution = {
        "clarification_engineering": sum(1 for r in scheduled_replies if r.reply_type == "clarification_engineering"),
        "clarification_procurement": sum(1 for r in scheduled_replies if r.reply_type == "clarification_procurement"),
        "quote": sum(1 for r in scheduled_replies if r.reply_type == "quote")
    }
    
    return BatchAutoReplyResponse(
        success=True,
        total_scheduled=len(scheduled_replies),
        scheduled_replies=scheduled_replies,
        distribution=actual_distribution,
        message=f"Successfully scheduled {len(scheduled_replies)} replies with guaranteed distribution. Replies will arrive with {delay_increment}s intervals starting in {base_delay}s."
    )
