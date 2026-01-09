"""Service for extracting quote details from emails."""
from typing import Dict, Any, Optional
from datetime import datetime
from ..models.quote import Quote
from ..llm.classifier import LLMClassifier
from ..services.quote_store import QuoteStore
from ..services.mock_erp import MockERP


class QuoteExtractionService:
    """Service for extracting and storing quotes."""
    
    def __init__(
        self,
        quote_store: QuoteStore,
        llm_classifier: Optional[LLMClassifier] = None,
        mock_erp: Optional[MockERP] = None
    ):
        self.quote_store = quote_store
        self.llm_classifier = llm_classifier or LLMClassifier()
        self.mock_erp = mock_erp or MockERP()
        self._quote_counter = 0
    
    def _generate_quote_id(self) -> str:
        """Generate a unique quote ID."""
        self._quote_counter += 1
        return f"QUOTE-{self._quote_counter:03d}"
    
    def extract_and_store_quote(
        self,
        email_id: str,
        rfq_id: str,
        supplier_id: str,
        email_body: str
    ) -> Quote:
        """
        Extract quote details from email and store it.
        
        Args:
            email_id: Source email ID
            rfq_id: Related RFQ ID
            supplier_id: Supplier who provided quote
            email_body: Email body containing quote
            
        Returns:
            Quote object
        """
        # Use LLM to extract quote details
        extracted_details = self.llm_classifier.extract_quote_details(email_body)
        
        # Get supplier name
        supplier = self.mock_erp.get_supplier_by_id(supplier_id)
        supplier_name = supplier.name if supplier else "Unknown Supplier"
        
        quote_id = self._generate_quote_id()
        
        quote = Quote(
            quote_id=quote_id,
            rfq_id=rfq_id,
            supplier_id=supplier_id,
            supplier_name=supplier_name,
            quote_date=datetime.now(),
            price=extracted_details.get("price"),
            currency=extracted_details.get("currency", "USD"),
            delivery_time=extracted_details.get("delivery_time"),
            validity_period=extracted_details.get("validity"),
            terms_and_conditions=extracted_details.get("terms"),
            extracted_details=extracted_details,
            status="received",
            email_id=email_id
        )
        
        # Store quote
        self.quote_store.store_quote(quote)
        
        return quote
    
    def get_quote_by_id(self, quote_id: str) -> Optional[Quote]:
        """Get quote by ID."""
        return self.quote_store.get_quote_by_id(quote_id)
