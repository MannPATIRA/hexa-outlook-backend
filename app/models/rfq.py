from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any


@dataclass
class RFQ:
    """RFQ model representing a Request for Quotation."""
    
    rfq_id: str
    supplier_id: str
    pr_id: str
    subject: str
    body: Dict[str, Any]
    attachments: List[str] = field(default_factory=list)
    status: str = "draft"  # draft, finalized, sent
    created_date: datetime = field(default_factory=datetime.now)
    finalized_date: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """Convert RFQ to dictionary for JSON serialization."""
        return {
            "rfq_id": self.rfq_id,
            "supplier_id": self.supplier_id,
            "pr_id": self.pr_id,
            "subject": self.subject,
            "body": self.body,
            "attachments": self.attachments,
            "status": self.status,
            "created_date": self.created_date.isoformat(),
            "finalized_date": self.finalized_date.isoformat() if self.finalized_date else None,
        }
