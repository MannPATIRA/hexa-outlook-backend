from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EmailClassification:
    """Email classification model for RFQ reply emails."""
    
    email_id: str
    rfq_id: str
    supplier_id: str
    subject: str
    body: str
    from_email: str
    received_date: datetime = field(default_factory=datetime.now)
    classification: str = "pending"  # "quote" | "clarification_request" | "engineer_response"
    sub_classification: Optional[str] = None  # For clarifications: "engineering" | "procurement"
    status: str = "pending"  # "pending" | "processed" | "responded"
    confidence: Optional[float] = None
    
    def to_dict(self) -> dict:
        """Convert EmailClassification to dictionary for JSON serialization."""
        return {
            "email_id": self.email_id,
            "rfq_id": self.rfq_id,
            "supplier_id": self.supplier_id,
            "subject": self.subject,
            "body": self.body,
            "from_email": self.from_email,
            "received_date": self.received_date.isoformat(),
            "classification": self.classification,
            "sub_classification": self.sub_classification,
            "status": self.status,
            "confidence": self.confidence,
        }
