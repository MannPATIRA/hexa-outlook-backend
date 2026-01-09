from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ClarificationRequest:
    """Clarification request model."""
    
    clarification_id: str
    email_id: str
    rfq_id: str
    supplier_id: str
    type: str  # "engineering" | "procurement"
    question: str
    suggested_response: Optional[str] = None
    status: str = "pending"  # "pending" | "sent_to_engineering" | "responded" | "awaiting_response"
    created_date: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        """Convert ClarificationRequest to dictionary for JSON serialization."""
        return {
            "clarification_id": self.clarification_id,
            "email_id": self.email_id,
            "rfq_id": self.rfq_id,
            "supplier_id": self.supplier_id,
            "type": self.type,
            "question": self.question,
            "suggested_response": self.suggested_response,
            "status": self.status,
            "created_date": self.created_date.isoformat(),
        }
