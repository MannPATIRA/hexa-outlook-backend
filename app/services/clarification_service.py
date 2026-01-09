"""Service for handling clarification requests."""
from typing import Dict, Any, Optional
from datetime import datetime
from ..models.clarification import ClarificationRequest
from ..llm.classifier import LLMClassifier
from ..services.mock_erp import MockERP


class ClarificationService:
    """Service for processing clarification requests."""
    
    def __init__(self, llm_classifier: Optional[LLMClassifier] = None, mock_erp: Optional[MockERP] = None):
        self.llm_classifier = llm_classifier or LLMClassifier()
        self.mock_erp = mock_erp or MockERP()
        self._clarifications: Dict[str, ClarificationRequest] = {}
        self._clarification_counter = 0
    
    def _generate_clarification_id(self) -> str:
        """Generate a unique clarification ID."""
        self._clarification_counter += 1
        return f"CLAR-{self._clarification_counter:03d}"
    
    def classify_clarification(
        self,
        email_id: str,
        rfq_id: str,
        supplier_id: str,
        question: str,
        email_body: str
    ) -> ClarificationRequest:
        """
        Classify a clarification request as engineering or procurement.
        
        Args:
            email_id: Source email ID
            rfq_id: Related RFQ ID
            supplier_id: Supplier asking
            question: The clarification question
            email_body: Full email body for context
            
        Returns:
            ClarificationRequest object
        """
        # Use LLM to classify
        llm_result = self.llm_classifier.classify_clarification(question, email_body)
        
        clarification_id = self._generate_clarification_id()
        
        clarification = ClarificationRequest(
            clarification_id=clarification_id,
            email_id=email_id,
            rfq_id=rfq_id,
            supplier_id=supplier_id,
            type=llm_result["type"],
            question=question,
            status="pending",
            created_date=datetime.now()
        )
        
        # Store clarification
        self._clarifications[clarification_id] = clarification
        
        return clarification
    
    def generate_suggested_response(
        self,
        clarification_id: str,
        question: str
    ) -> str:
        """
        Generate a suggested response for a procurement clarification.
        
        Args:
            clarification_id: Clarification ID
            question: The clarification question
            
        Returns:
            Suggested response text
        """
        clarification = self._clarifications.get(clarification_id)
        if not clarification:
            raise ValueError(f"Clarification {clarification_id} not found")
        
        # Get RFQ context - clarification.rfq_id is the RFQ ID
        rfq = self.mock_erp.get_rfq_by_id(clarification.rfq_id)
        if rfq:
            pr = self.mock_erp.get_pr_by_id(rfq.pr_id)
            rfq_context = {
                "rfq_id": clarification.rfq_id,
                "pr_id": rfq.pr_id,
                "material": pr.material if pr else "N/A"
            }
        else:
            # Try to get PR directly if RFQ not found
            pr = self.mock_erp.get_pr_by_id(clarification.rfq_id.replace("RFQ", "PR"))
            rfq_context = {
                "rfq_id": clarification.rfq_id,
                "pr_id": clarification.rfq_id.replace("RFQ", "PR") if "RFQ" in clarification.rfq_id else clarification.rfq_id,
                "material": pr.material if pr else "N/A"
            }
        
        # Generate response using LLM
        suggested_response = self.llm_classifier.generate_response(question, rfq_context)
        
        # Update clarification with suggested response
        clarification.suggested_response = suggested_response
        
        return suggested_response
    
    def get_clarification_by_id(self, clarification_id: str) -> Optional[ClarificationRequest]:
        """Get clarification by ID."""
        return self._clarifications.get(clarification_id)
    
    def update_clarification_status(self, clarification_id: str, status: str) -> None:
        """Update clarification status."""
        if clarification_id in self._clarifications:
            self._clarifications[clarification_id].status = status
    
    def get_clarification_by_email_id(self, email_id: str) -> Optional[ClarificationRequest]:
        """Get clarification by email ID."""
        for clarification in self._clarifications.values():
            if clarification.email_id == email_id:
                return clarification
        return None
