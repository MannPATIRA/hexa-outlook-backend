from typing import Dict, List, Any
from ..models.pr import PurchaseRequisition


class PRService:
    """Service for decomposing and processing Purchase Requisitions."""
    
    @staticmethod
    def decompose_pr(pr: PurchaseRequisition) -> Dict[str, Any]:
        """
        Decompose a PR into its constituent parts for supplier matching.
        
        Returns a structured dictionary with all PR information.
        """
        return {
            "pr_id": pr.pr_id,
            "material": pr.material,
            "material_info": {
                "code": pr.material,
                "description": pr.description,
                "type": pr.specs.get("material_type", ""),
                "grade": pr.specs.get("grade") or pr.specs.get("material", ""),
            },
            "specifications": pr.specs,
            "drawing_files": pr.drawing_files,
            "quantities": {
                "amount": pr.quantities,
                "unit": pr.unit,
            },
            "requirements": {
                "dimensions": pr.specs.get("dimensions", ""),
                "tolerance": pr.specs.get("tolerance", ""),
                "surface_finish": pr.specs.get("surface_finish", ""),
                "weight": pr.specs.get("weight", ""),
            },
            "status": pr.status,
            "created_date": pr.created_date.isoformat(),
        }
    
    @staticmethod
    def extract_material_code(pr: PurchaseRequisition) -> str:
        """Extract material code from PR."""
        return pr.material
    
    @staticmethod
    def extract_specs(pr: PurchaseRequisition) -> Dict[str, Any]:
        """Extract specifications from PR."""
        return pr.specs.copy()
    
    @staticmethod
    def extract_drawing_files(pr: PurchaseRequisition) -> List[str]:
        """Extract drawing file references from PR."""
        return pr.drawing_files.copy()
    
    @staticmethod
    def extract_quantities(pr: PurchaseRequisition) -> Dict[str, Any]:
        """Extract quantity information from PR."""
        return {
            "amount": pr.quantities,
            "unit": pr.unit,
        }
