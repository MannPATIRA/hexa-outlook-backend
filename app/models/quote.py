from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any


@dataclass
class Quote:
    """Quote model representing a supplier quote."""
    
    quote_id: str
    rfq_id: str
    supplier_id: str
    supplier_name: str
    quote_date: datetime = field(default_factory=datetime.now)
    price: Optional[float] = None
    currency: Optional[str] = None
    delivery_time: Optional[str] = None
    validity_period: Optional[str] = None
    terms_and_conditions: Optional[str] = None
    attachments: List[str] = field(default_factory=list)
    extracted_details: Dict[str, Any] = field(default_factory=dict)
    status: str = "received"  # "received" | "under_review" | "accepted" | "rejected"
    email_id: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert Quote to dictionary for JSON serialization."""
        return {
            "quote_id": self.quote_id,
            "rfq_id": self.rfq_id,
            "supplier_id": self.supplier_id,
            "supplier_name": self.supplier_name,
            "quote_date": self.quote_date.isoformat(),
            "price": self.price,
            "currency": self.currency,
            "delivery_time": self.delivery_time,
            "validity_period": self.validity_period,
            "terms_and_conditions": self.terms_and_conditions,
            "attachments": self.attachments,
            "extracted_details": self.extracted_details,
            "status": self.status,
            "email_id": self.email_id,
        }
