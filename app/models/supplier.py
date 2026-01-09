from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class Supplier:
    """Supplier model representing a supplier in the ERP system."""
    
    supplier_id: str
    name: str
    email: str
    capabilities: List[str] = field(default_factory=list)
    standard_for_materials: List[str] = field(default_factory=list)
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert Supplier to dictionary for JSON serialization."""
        return {
            "supplier_id": self.supplier_id,
            "name": self.name,
            "email": self.email,
            "capabilities": self.capabilities,
            "standard_for_materials": self.standard_for_materials,
            "contact_person": self.contact_person,
            "phone": self.phone,
        }
