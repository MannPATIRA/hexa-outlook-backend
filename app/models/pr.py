from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field


@dataclass
class PurchaseRequisition:
    """Purchase Requisition model representing a PR from SAP ERP."""
    
    pr_id: str
    material: str
    specs: Dict[str, Any]
    quantities: int
    unit: str
    drawing_files: List[str] = field(default_factory=list)
    description: Optional[str] = None
    status: str = "open"
    created_date: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        """Convert PR to dictionary for JSON serialization."""
        return {
            "pr_id": self.pr_id,
            "material": self.material,
            "specs": self.specs,
            "drawing_files": self.drawing_files,
            "quantities": self.quantities,
            "unit": self.unit,
            "description": self.description,
            "status": self.status,
            "created_date": self.created_date.isoformat(),
        }
