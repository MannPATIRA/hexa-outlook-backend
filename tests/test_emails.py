"""Tests for email processing and classification."""
import pytest
from app.services.email_classification_service import EmailClassificationService
from app.services.clarification_service import ClarificationService
from app.services.quote_extraction_service import QuoteExtractionService
from app.services.quote_store import QuoteStore
from app.services.mock_erp import MockERP
from app.llm.classifier import LLMClassifier


@pytest.fixture
def mock_erp():
    """Create a MockERP instance."""
    return MockERP()


@pytest.fixture
def llm_classifier():
    """Create an LLMClassifier instance."""
    return LLMClassifier()


@pytest.fixture
def quote_store():
    """Create a QuoteStore instance."""
    return QuoteStore()


@pytest.fixture
def email_classification_service(llm_classifier):
    """Create an EmailClassificationService instance."""
    return EmailClassificationService(llm_classifier)


@pytest.fixture
def clarification_service(llm_classifier, mock_erp):
    """Create a ClarificationService instance."""
    return ClarificationService(llm_classifier, mock_erp)


@pytest.fixture
def quote_extraction_service(quote_store, llm_classifier, mock_erp):
    """Create a QuoteExtractionService instance."""
    return QuoteExtractionService(quote_store, llm_classifier, mock_erp)


class TestEmailClassificationService:
    """Tests for EmailClassificationService."""
    
    def test_classify_email_as_quote(self, email_classification_service):
        """Test classifying an email as a quote."""
        classification = email_classification_service.classify_email(
            rfq_id="RFQ-001",
            supplier_id="SUP-001",
            subject="Re: RFQ for MAT-12345",
            body="Dear Procurement Team, We are pleased to provide our quote. Price: $1000 USD. Delivery: 4-6 weeks.",
            from_email="supplier@example.com"
        )
        
        assert classification.classification in ["quote", "clarification_request"]
        assert classification.email_id is not None
        assert classification.rfq_id == "RFQ-001"
        assert classification.supplier_id == "SUP-001"
        assert classification.confidence is not None
    
    def test_classify_email_as_clarification(self, email_classification_service):
        """Test classifying an email as a clarification request."""
        classification = email_classification_service.classify_email(
            rfq_id="RFQ-001",
            supplier_id="SUP-001",
            subject="Re: RFQ for MAT-12345",
            body="Dear Procurement Team, We have a question about the delivery address. Can you please clarify?",
            from_email="supplier@example.com"
        )
        
        assert classification.classification in ["quote", "clarification_request"]
        assert classification.email_id is not None
    
    def test_get_classification_by_id(self, email_classification_service):
        """Test retrieving classification by ID."""
        classification = email_classification_service.classify_email(
            rfq_id="RFQ-001",
            supplier_id="SUP-001",
            subject="Test",
            body="Test body",
            from_email="test@example.com"
        )
        
        retrieved = email_classification_service.get_classification_by_id(classification.email_id)
        assert retrieved is not None
        assert retrieved.email_id == classification.email_id


class TestClarificationService:
    """Tests for ClarificationService."""
    
    def test_classify_clarification(self, clarification_service, email_classification_service):
        """Test classifying a clarification as engineering or procurement."""
        # First classify an email
        email_class = email_classification_service.classify_email(
            rfq_id="RFQ-001",
            supplier_id="SUP-001",
            subject="Question about material",
            body="Can we use an alternative material specification?",
            from_email="supplier@example.com"
        )
        
        # Then classify the clarification
        clarification = clarification_service.classify_clarification(
            email_id=email_class.email_id,
            rfq_id="RFQ-001",
            supplier_id="SUP-001",
            question="Can we use an alternative material?",
            email_body=email_class.body
        )
        
        assert clarification.type in ["engineering", "procurement"]
        assert clarification.clarification_id is not None
        assert clarification.email_id == email_class.email_id
    
    def test_generate_suggested_response(self, clarification_service, email_classification_service):
        """Test generating a suggested response for procurement clarification."""
        # Create email classification
        email_class = email_classification_service.classify_email(
            rfq_id="RFQ-001",
            supplier_id="SUP-001",
            subject="Question about delivery",
            body="What is the delivery address?",
            from_email="supplier@example.com"
        )
        
        # Classify clarification
        clarification = clarification_service.classify_clarification(
            email_id=email_class.email_id,
            rfq_id="RFQ-001",
            supplier_id="SUP-001",
            question="What is the delivery address?",
            email_body=email_class.body
        )
        
        # Generate response
        response = clarification_service.generate_suggested_response(
            clarification.clarification_id,
            clarification.question
        )
        
        assert response is not None
        assert len(response) > 0
        assert "RFQ" in response or "delivery" in response.lower()
    
    def test_update_clarification_status(self, clarification_service, email_classification_service):
        """Test updating clarification status."""
        email_class = email_classification_service.classify_email(
            rfq_id="RFQ-001",
            supplier_id="SUP-001",
            subject="Question",
            body="What is the delivery address?",
            from_email="supplier@example.com"
        )
        
        clarification = clarification_service.classify_clarification(
            email_id=email_class.email_id,
            rfq_id="RFQ-001",
            supplier_id="SUP-001",
            question="What is the delivery address?",
            email_body=email_class.body
        )
        
        clarification_service.update_clarification_status(
            clarification.clarification_id,
            "sent_to_engineering"
        )
        
        updated = clarification_service.get_clarification_by_id(clarification.clarification_id)
        assert updated.status == "sent_to_engineering"


class TestQuoteExtractionService:
    """Tests for QuoteExtractionService."""
    
    def test_extract_and_store_quote(self, quote_extraction_service, mock_erp):
        """Test extracting and storing a quote."""
        quote_email = """
        Dear Procurement Team,
        
        We are pleased to provide our quotation for RFQ-001.
        
        Price: $1,500.00 USD
        Delivery Time: 4-6 weeks
        Quote Valid: 30 days
        
        Terms and conditions apply.
        
        Best regards,
        Supplier Team
        """
        
        quote = quote_extraction_service.extract_and_store_quote(
            email_id="EMAIL-001",
            rfq_id="RFQ-001",
            supplier_id="SUP-001",
            email_body=quote_email
        )
        
        assert quote.quote_id is not None
        assert quote.rfq_id == "RFQ-001"
        assert quote.supplier_id == "SUP-001"
        assert quote.status == "received"
        assert quote.extracted_details is not None
        
        # Verify quote is stored
        stored = quote_extraction_service.quote_store.get_quote_by_id(quote.quote_id)
        assert stored is not None
        assert stored.quote_id == quote.quote_id
    
    def test_get_quotes_by_rfq(self, quote_extraction_service):
        """Test retrieving quotes by RFQ ID."""
        # Extract multiple quotes
        quote1 = quote_extraction_service.extract_and_store_quote(
            email_id="EMAIL-001",
            rfq_id="RFQ-001",
            supplier_id="SUP-001",
            email_body="Price: $1000"
        )
        
        quote2 = quote_extraction_service.extract_and_store_quote(
            email_id="EMAIL-002",
            rfq_id="RFQ-001",
            supplier_id="SUP-002",
            email_body="Price: $1200"
        )
        
        quotes = quote_extraction_service.quote_store.get_quotes_by_rfq("RFQ-001")
        assert len(quotes) == 2
        assert quote1.quote_id in [q.quote_id for q in quotes]
        assert quote2.quote_id in [q.quote_id for q in quotes]


class TestQuoteStore:
    """Tests for QuoteStore."""
    
    def test_store_and_retrieve_quote(self, quote_store):
        """Test storing and retrieving quotes."""
        from app.models.quote import Quote
        
        quote = Quote(
            quote_id="QUOTE-001",
            rfq_id="RFQ-001",
            supplier_id="SUP-001",
            supplier_name="Test Supplier",
            price=1000.0,
            currency="USD"
        )
        
        quote_store.store_quote(quote)
        retrieved = quote_store.get_quote_by_id("QUOTE-001")
        
        assert retrieved is not None
        assert retrieved.quote_id == "QUOTE-001"
        assert retrieved.price == 1000.0
    
    def test_get_quotes_by_rfq(self, quote_store):
        """Test getting quotes by RFQ ID."""
        from app.models.quote import Quote
        
        quote1 = Quote(
            quote_id="QUOTE-001",
            rfq_id="RFQ-001",
            supplier_id="SUP-001",
            supplier_name="Supplier 1"
        )
        
        quote2 = Quote(
            quote_id="QUOTE-002",
            rfq_id="RFQ-001",
            supplier_id="SUP-002",
            supplier_name="Supplier 2"
        )
        
        quote3 = Quote(
            quote_id="QUOTE-003",
            rfq_id="RFQ-002",
            supplier_id="SUP-001",
            supplier_name="Supplier 1"
        )
        
        quote_store.store_quote(quote1)
        quote_store.store_quote(quote2)
        quote_store.store_quote(quote3)
        
        quotes = quote_store.get_quotes_by_rfq("RFQ-001")
        assert len(quotes) == 2
        assert all(q.rfq_id == "RFQ-001" for q in quotes)
    
    def test_update_quote_status(self, quote_store):
        """Test updating quote status."""
        from app.models.quote import Quote
        
        quote = Quote(
            quote_id="QUOTE-001",
            rfq_id="RFQ-001",
            supplier_id="SUP-001",
            supplier_name="Test Supplier"
        )
        
        quote_store.store_quote(quote)
        quote_store.update_quote_status("QUOTE-001", "under_review")
        
        updated = quote_store.get_quote_by_id("QUOTE-001")
        assert updated.status == "under_review"
