"""
Demo/testing API endpoints for simulating supplier email replies.

These endpoints allow you to trigger automatic email replies that will
appear as threaded replies to RFQ emails - perfect for demos and testing.
"""
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
    delay_seconds: int = 30  # How long to wait before sending
    quantity: int = 100  # Quantity for quote calculations
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "to_email": "user@company.com",
                "original_subject": "RFQ for Steel Brackets - 100 pcs",
                "original_message_id": "<abc123@mail.outlook.com>",
                "material": "Steel Brackets",
                "reply_type": "quote",
                "delay_seconds": 30,
                "quantity": 100
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
    
    This is the main endpoint for triggering demo replies. The email will:
    - Be sent from the configured demo supplier email
    - Include proper threading headers (In-Reply-To, References)
    - Appear as a reply in the same email thread as the original RFQ
    
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
    
    result = auto_reply_service.schedule_reply(
        to_email=request.to_email,
        original_subject=request.original_subject,
        original_message_id=request.original_message_id,
        material=request.material,
        reply_type=reply_type,
        delay_seconds=request.delay_seconds,
        quantity=request.quantity
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
