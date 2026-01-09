from typing import List, Dict
from datetime import datetime, timedelta
from ..models.pr import PurchaseRequisition
from ..models.supplier import Supplier
from ..models.rfq import RFQ
from .mock_erp import MockERP
from .pr_service import PRService


class RFQService:
    """Service for generating RFQ content."""
    
    def __init__(self, mock_erp: MockERP):
        self.mock_erp = mock_erp
        self.pr_service = PRService()
        self._rfq_counter = 0
    
    def _generate_rfq_id(self) -> str:
        """Generate a unique RFQ ID."""
        self._rfq_counter += 1
        return f"RFQ-{self._rfq_counter:03d}"
    
    def generate_rfqs(
        self, 
        pr: PurchaseRequisition, 
        suppliers: List[Supplier]
    ) -> List[RFQ]:
        """
        Generate RFQ content for multiple suppliers based on a PR.
        
        Returns a list of RFQ objects with structured content.
        """
        rfqs = []
        pr_decomposed = self.pr_service.decompose_pr(pr)
        
        for supplier in suppliers:
            rfq_id = self._generate_rfq_id()
            
            # Generate RFQ subject
            subject = f"RFQ for {pr.material} - {pr.quantities} {pr.unit}"
            
            # Calculate quotation deadline (e.g., 2 weeks from now)
            deadline_date = datetime.now() + timedelta(days=14)
            deadline_str = deadline_date.strftime("%B %d, %Y")
            
            # Generate structured RFQ body
            body = {
                "greeting": f"Dear {supplier.name},",
                "introduction": "We are requesting a quotation for the following item:",
                "material_details": {
                    "material_code": pr.material,
                    "description": pr.description or "As per specifications",
                    "quantity": pr.quantities,
                    "unit": pr.unit,
                    "specifications": pr_decomposed["specifications"],
                },
                "requirements": {
                    "dimensions": pr_decomposed["requirements"].get("dimensions", "As per drawing"),
                    "tolerance": pr_decomposed["requirements"].get("tolerance", ""),
                    "surface_finish": pr_decomposed["requirements"].get("surface_finish", ""),
                    "weight": pr_decomposed["requirements"].get("weight", ""),
                },
                "drawing_files": pr.drawing_files,
                "delivery_requirements": "Please provide delivery timeline and terms",
                "quotation_deadline": deadline_str,
                "closing": f"Please provide your quotation by {deadline_str}. We look forward to your response.",
                "contact_info": "For any questions, please contact our procurement team.",
            }
            
            rfq = RFQ(
                rfq_id=rfq_id,
                supplier_id=supplier.supplier_id,
                pr_id=pr.pr_id,
                subject=subject,
                body=body,
                attachments=pr.drawing_files.copy(),
                status="draft",
                created_date=datetime.now()
            )
            
            rfqs.append(rfq)
            # Store in MockERP for tracking
            self.mock_erp.store_rfq(rfq)
        
        return rfqs
    
    def finalize_rfq(
        self, 
        rfq_id: str, 
        final_subject: str, 
        final_body: str
    ) -> RFQ:
        """
        Finalize an RFQ with user-edited content.
        
        Returns the updated RFQ.
        """
        rfq = self.mock_erp.get_rfq_by_id(rfq_id)
        if not rfq:
            raise ValueError(f"RFQ {rfq_id} not found")
        
        # Update RFQ with finalized content
        rfq.subject = final_subject
        # If final_body is a string, parse it or keep as is
        # If it's already a dict, use it directly
        if isinstance(final_body, str):
            # Try to parse as JSON if needed, otherwise use as plain text
            rfq.body = {"content": final_body}
        else:
            rfq.body = final_body
        
        rfq.status = "finalized"
        rfq.finalized_date = datetime.now()
        
        return rfq
