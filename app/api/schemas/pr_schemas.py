from typing import List, Dict, Optional, Any
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class PRResponse(BaseModel):
    """Response schema for a single Purchase Requisition."""
    
    pr_id: str
    material: str
    specs: Dict[str, Any]
    drawing_files: List[str]
    step_files: List[str]
    quantities: int
    unit: str
    description: Optional[str] = None
    status: str
    created_date: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "pr_id": "PR-001",
                "material": "MAT-12345",
                "specs": {
                    "material_type": "Steel Component",
                    "grade": "SS304",
                    "dimensions": "100mm x 50mm x 25mm"
                },
                "drawing_files": ["drawing1.pdf"],
                "step_files": ["model1.step", "assembly.step"],
                "quantities": 100,
                "unit": "pcs",
                "description": "Steel bracket",
                "status": "open",
                "created_date": "2024-01-15T10:30:00"
            }
        }
    )


class PRListResponse(BaseModel):
    """Response schema for a list of Purchase Requisitions."""
    
    prs: List[PRResponse]
