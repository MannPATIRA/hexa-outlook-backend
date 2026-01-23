from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, ConfigDict


class RFQGenerateRequest(BaseModel):
    """Request schema for generating RFQs."""
    
    pr_id: str
    supplier_ids: List[str]
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "pr_id": "PR-001",
                "supplier_ids": ["SUP-001", "SUP-002"]
            }
        }
    )


class RFQBodyContent(BaseModel):
    """Schema for RFQ body content structure."""
    
    greeting: str
    introduction: str
    material_details: Dict[str, Any]
    requirements: Dict[str, Any]
    drawing_files: List[str]
    step_files: List[str]
    delivery_requirements: str
    quotation_deadline: str
    closing: str
    contact_info: str


class RFQResponse(BaseModel):
    """Response schema for a single RFQ."""
    
    rfq_id: str
    supplier_id: str
    supplier_name: str
    supplier_email: str
    pr_id: str
    subject: str
    body: Dict[str, Any]
    attachments: List[str]
    status: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "rfq_id": "RFQ-001",
                "supplier_id": "SUP-001",
                "supplier_name": "ABC Manufacturing",
                "supplier_email": "procurement@abcmanufacturing.com",
                "pr_id": "PR-001",
                "subject": "RFQ for MAT-12345 - 100 pcs",
                "body": {
                    "greeting": "Dear ABC Manufacturing,",
                    "introduction": "We are requesting a quotation...",
                    "material_details": {...},
                    "requirements": {...},
                    "drawing_files": ["drawing1.pdf"],
                    "step_files": ["model1.step"],
                    "delivery_requirements": "...",
                    "quotation_deadline": "February 15, 2024",
                    "closing": "Please provide your quotation..."
                },
                "attachments": ["drawing1.pdf", "model1.step"],
                "status": "draft"
            }
        }
    )


class RFQListResponse(BaseModel):
    """Response schema for a list of RFQs."""
    
    rfqs: List[RFQResponse]


class RFQFinalizeRequest(BaseModel):
    """Request schema for finalizing an RFQ."""
    
    rfq_id: str
    final_subject: str
    final_body: Union[str, Dict[str, Any]]  # Can be JSON string or structured dict
    status: str = "ready_to_send"
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "rfq_id": "RFQ-001",
                "final_subject": "RFQ for MAT-12345 - 100 pcs",
                "final_body": "Dear ABC Manufacturing,\n\nWe are requesting...",
                "status": "ready_to_send"
            }
        }
    )


class RFQFinalizeResponse(BaseModel):
    """Response schema for finalizing an RFQ."""
    
    rfq_id: str
    status: str
    message: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "rfq_id": "RFQ-001",
                "status": "finalized",
                "message": "RFQ finalized successfully"
            }
        }
    )