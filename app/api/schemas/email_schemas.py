"""Pydantic schemas for email processing."""
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, ConfigDict


class EmailMessage(BaseModel):
    """Schema for an email message in a chain."""
    
    subject: str
    body: str
    from_email: str
    date: Optional[str] = None
    in_reply_to: Optional[str] = None


class EmailClassifyRequest(BaseModel):
    """Request schema for email classification."""
    
    email_chain: List[EmailMessage]
    most_recent_reply: EmailMessage
    rfq_id: str
    supplier_id: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email_chain": [
                    {
                        "subject": "RFQ for MAT-12345",
                        "body": "Original RFQ email...",
                        "from_email": "procurement@company.com",
                        "date": "2024-01-15T10:00:00Z"
                    }
                ],
                "most_recent_reply": {
                    "subject": "Re: RFQ for MAT-12345",
                    "body": "Here is our quote: $1000...",
                    "from_email": "supplier@example.com",
                    "date": "2024-01-16T10:00:00Z"
                },
                "rfq_id": "RFQ-001",
                "supplier_id": "SUP-001"
            }
        }
    )


class EmailClassifyResponse(BaseModel):
    """Response schema for email classification."""
    
    email_id: str
    classification: str
    confidence: float
    message: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email_id": "EMAIL-001",
                "classification": "quote",
                "confidence": 0.95,
                "message": "Email classified as quote"
            }
        }
    )


class EmailProcessRequest(BaseModel):
    """Request schema for processing an email."""
    
    email_id: str
    classification: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email_id": "EMAIL-001",
                "classification": "clarification_request"
            }
        }
    )


class EmailProcessResponse(BaseModel):
    """Response schema for email processing."""
    
    email_id: str
    sub_classification: Optional[str] = None
    question: Optional[str] = None
    suggested_response: Optional[str] = None
    requires_engineering: bool = False
    message: Optional[str] = None
    clarification_id: Optional[str] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email_id": "EMAIL-001",
                "sub_classification": "procurement",
                "question": "What is the delivery address?",
                "suggested_response": "Dear Supplier,\n\nOur delivery address is...",
                "requires_engineering": False
            }
        }
    )


class SuggestResponseRequest(BaseModel):
    """Request schema for getting suggested response."""
    
    clarification_id: str
    email_id: str
    question: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "clarification_id": "CLAR-001",
                "email_id": "EMAIL-001",
                "question": "What is the delivery address?"
            }
        }
    )


class SuggestResponseResponse(BaseModel):
    """Response schema for suggested response."""
    
    suggested_response: str
    draft_subject: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "suggested_response": "Dear Supplier,\n\nOur delivery address is:\n123 Main St...",
                "draft_subject": "Re: Clarification on RFQ-001"
            }
        }
    )


class ForwardToEngineeringRequest(BaseModel):
    """Request schema for forwarding to engineering."""
    
    email_id: str
    clarification_id: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email_id": "EMAIL-001",
                "clarification_id": "CLAR-001"
            }
        }
    )


class ForwardToEngineeringResponse(BaseModel):
    """Response schema for forwarding to engineering."""
    
    status: str
    message: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "sent_to_engineering",
                "message": "Clarification forwarded to engineering team"
            }
        }
    )


class EngineerResponseRequest(BaseModel):
    """Request schema for processing engineer response."""
    
    email_id: str
    engineer_response: Dict[str, str]
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email_id": "EMAIL-001",
                "engineer_response": {
                    "body": "Engineer's technical response...",
                    "from": "engineer@company.com"
                }
            }
        }
    )


class EngineerResponseResponse(BaseModel):
    """Response schema for engineer response processing."""
    
    draft_response: Dict[str, str]
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "draft_response": {
                    "subject": "Re: Clarification on RFQ-001",
                    "body": "Dear Supplier,\n\nBased on engineering review: [engineer response]",
                    "to": "supplier@example.com"
                }
            }
        }
    )


class ExtractQuoteRequest(BaseModel):
    """Request schema for quote extraction."""
    
    email_id: str
    rfq_id: str
    supplier_id: str
    email_body: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email_id": "EMAIL-001",
                "rfq_id": "RFQ-001",
                "supplier_id": "SUP-001",
                "email_body": "Dear Procurement Team,\n\nWe are pleased to provide our quote..."
            }
        }
    )


class ExtractQuoteResponse(BaseModel):
    """Response schema for quote extraction."""
    
    quote_id: str
    extracted_details: Dict[str, Any]
    status: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "quote_id": "QUOTE-001",
                "extracted_details": {
                    "price": 1000.00,
                    "currency": "USD",
                    "delivery_time": "4-6 weeks",
                    "validity": "30 days",
                    "terms": "..."
                },
                "status": "received"
            }
        }
    )


class QuoteResponse(BaseModel):
    """Response schema for a single quote."""
    
    quote_id: str
    supplier_name: str
    price: Optional[float] = None
    currency: Optional[str] = None
    delivery_time: Optional[str] = None
    quote_date: str
    status: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "quote_id": "QUOTE-001",
                "supplier_name": "ABC Manufacturing",
                "price": 1000.00,
                "currency": "USD",
                "delivery_time": "4-6 weeks",
                "quote_date": "2024-01-15T10:00:00Z",
                "status": "received"
            }
        }
    )


class QuoteListResponse(BaseModel):
    """Response schema for a list of quotes."""
    
    quotes: List[QuoteResponse]
