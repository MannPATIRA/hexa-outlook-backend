"""Service for email classification."""
from typing import Dict, Any, List, Optional
from datetime import datetime
from ..models.email import EmailClassification
from ..llm.classifier import LLMClassifier


class EmailClassificationService:
    """Service for classifying emails."""
    
    def __init__(self, llm_classifier: Optional[LLMClassifier] = None):
        self.llm_classifier = llm_classifier or LLMClassifier()
        self._classifications: Dict[str, EmailClassification] = {}
        self._email_counter = 0
    
    def _generate_email_id(self) -> str:
        """Generate a unique email ID."""
        self._email_counter += 1
        return f"EMAIL-{self._email_counter:03d}"
    
    def classify_email(
        self,
        rfq_id: str,
        supplier_id: str,
        subject: str,
        body: str,
        from_email: str,
        email_chain: Optional[List[Dict[str, Any]]] = None
    ) -> EmailClassification:
        """
        Classify an email as quote or clarification request.
        
        Args:
            rfq_id: Related RFQ ID
            supplier_id: Supplier who sent the email
            subject: Email subject
            body: Email body
            from_email: Sender email address
            email_chain: Optional email chain for context
            
        Returns:
            EmailClassification object
        """
        # Use LLM to classify
        llm_result = self.llm_classifier.classify_email(subject, body, email_chain)
        
        email_id = self._generate_email_id()
        
        classification = EmailClassification(
            email_id=email_id,
            rfq_id=rfq_id,
            supplier_id=supplier_id,
            subject=subject,
            body=body,
            from_email=from_email,
            received_date=datetime.now(),
            classification=llm_result["classification"],
            confidence=llm_result.get("confidence", 0.5),
            status="pending"
        )
        
        # Store classification
        self._classifications[email_id] = classification
        
        return classification
    
    def get_classification_by_id(self, email_id: str) -> Optional[EmailClassification]:
        """Get email classification by ID."""
        return self._classifications.get(email_id)
    
    def update_classification_status(self, email_id: str, status: str) -> None:
        """Update the status of an email classification."""
        if email_id in self._classifications:
            self._classifications[email_id].status = status
