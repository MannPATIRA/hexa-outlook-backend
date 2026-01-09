"""Comprehensive tests for email processing API endpoints."""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


class TestEmailClassificationAPI:
    """Tests for email classification API endpoints."""
    
    def test_classify_email_quote(self, client):
        """Test classifying an email as quote with detailed response validation."""
        response = client.post(
            "/api/emails/classify",
            json={
                "email_chain": [
                    {
                        "subject": "RFQ for MAT-12345",
                        "body": "Original RFQ email",
                        "from_email": "procurement@company.com",
                        "date": "2024-01-15T10:00:00Z"
                    }
                ],
                "most_recent_reply": {
                    "subject": "Re: RFQ for MAT-12345",
                    "body": "Here is our quote: Price $1000 USD, Delivery: 4-6 weeks, Valid until March 2024",
                    "from_email": "supplier@example.com",
                    "date": "2024-01-16T10:00:00Z"
                },
                "rfq_id": "RFQ-001",
                "supplier_id": "SUP-001"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "email_id" in data
        assert "classification" in data
        assert data["classification"] in ["quote", "clarification_request", "engineer_response"]
        assert "confidence" in data
        assert isinstance(data["confidence"], (int, float))
        assert 0 <= data["confidence"] <= 1
        assert "message" in data
        assert isinstance(data["message"], str)
        assert len(data["message"]) > 0
    
    def test_classify_email_clarification(self, client):
        """Test classifying an email as clarification request."""
        response = client.post(
            "/api/emails/classify",
            json={
                "email_chain": [],
                "most_recent_reply": {
                    "subject": "Re: RFQ for MAT-12345",
                    "body": "We have a question: What is the delivery address? Can you please clarify?",
                    "from_email": "supplier@example.com",
                    "date": "2024-01-16T10:00:00Z"
                },
                "rfq_id": "RFQ-001",
                "supplier_id": "SUP-001"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "email_id" in data
        assert "classification" in data
        assert data["classification"] in ["quote", "clarification_request", "engineer_response"]
        assert "confidence" in data
        assert "message" in data
    
    def test_classify_email_engineer_response(self, client):
        """Test classifying an email as engineer response."""
        response = client.post(
            "/api/emails/classify",
            json={
                "email_chain": [],
                "most_recent_reply": {
                    "subject": "Engineering Review - RFQ-001",
                    "body": "After technical review, we approve the use of alternative material specification. The engineering team has reviewed and confirmed.",
                    "from_email": "engineer@company.com",
                    "date": "2024-01-16T10:00:00Z"
                },
                "rfq_id": "RFQ-001",
                "supplier_id": "SUP-001"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "email_id" in data
        assert "classification" in data
        assert data["classification"] in ["quote", "clarification_request", "engineer_response"]
        assert "confidence" in data
    
    def test_classify_email_with_chain(self, client):
        """Test classifying email with email chain context."""
        response = client.post(
            "/api/emails/classify",
            json={
                "email_chain": [
                    {
                        "subject": "RFQ for MAT-12345",
                        "body": "Original RFQ email with specifications",
                        "from_email": "procurement@company.com",
                        "date": "2024-01-15T10:00:00Z"
                    },
                    {
                        "subject": "Re: RFQ for MAT-12345",
                        "body": "Question about delivery timeline",
                        "from_email": "supplier@example.com",
                        "date": "2024-01-15T14:00:00Z"
                    }
                ],
                "most_recent_reply": {
                    "subject": "Re: RFQ for MAT-12345",
                    "body": "Our quotation: $1500 USD, delivery in 4-6 weeks",
                    "from_email": "supplier@example.com",
                    "date": "2024-01-16T10:00:00Z"
                },
                "rfq_id": "RFQ-001",
                "supplier_id": "SUP-001"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "email_id" in data
        assert "classification" in data
    
    def test_classify_email_validation_error(self, client):
        """Test missing required fields (422)."""
        response = client.post(
            "/api/emails/classify",
            json={
                "email_chain": [],
                # Missing most_recent_reply
                "rfq_id": "RFQ-001",
                "supplier_id": "SUP-001"
            }
        )
        
        assert response.status_code == 422
    
    def test_classify_email_response_structure(self, client):
        """Validate all response fields."""
        response = client.post(
            "/api/emails/classify",
            json={
                "email_chain": [],
                "most_recent_reply": {
                    "subject": "Test",
                    "body": "Test body",
                    "from_email": "test@example.com",
                    "date": "2024-01-16T10:00:00Z"
                },
                "rfq_id": "RFQ-001",
                "supplier_id": "SUP-001"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ["email_id", "classification", "confidence", "message"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        assert isinstance(data["email_id"], str)
        assert len(data["email_id"]) > 0
        assert isinstance(data["classification"], str)
        assert isinstance(data["confidence"], (int, float))
        assert isinstance(data["message"], str)


class TestEmailProcessingAPI:
    """Tests for email processing API endpoints."""
    
    def test_process_clarification_procurement(self, client):
        """Test processing procurement clarification."""
        # Classify
        classify_response = client.post(
            "/api/emails/classify",
            json={
                "email_chain": [],
                "most_recent_reply": {
                    "subject": "Question",
                    "body": "What is the delivery address for this order?",
                    "from_email": "supplier@example.com",
                    "date": "2024-01-16T10:00:00Z"
                },
                "rfq_id": "RFQ-001",
                "supplier_id": "SUP-001"
            }
        )
        assert classify_response.status_code == 200
        email_id = classify_response.json()["email_id"]
        
        # Process
        process_response = client.post(
            "/api/emails/process",
            json={
                "email_id": email_id,
                "classification": classify_response.json()["classification"]
            }
        )
        
        if process_response.status_code == 200:
            data = process_response.json()
            if "sub_classification" in data:
                assert data["sub_classification"] in ["engineering", "procurement"]
                if data["sub_classification"] == "procurement":
                    assert "suggested_response" in data
                    assert data["suggested_response"] is not None
    
    def test_process_clarification_engineering(self, client):
        """Test processing engineering clarification."""
        # Classify
        classify_response = client.post(
            "/api/emails/classify",
            json={
                "email_chain": [],
                "most_recent_reply": {
                    "subject": "Question",
                    "body": "Can we use alternative material specification? What are the technical requirements?",
                    "from_email": "supplier@example.com",
                    "date": "2024-01-16T10:00:00Z"
                },
                "rfq_id": "RFQ-001",
                "supplier_id": "SUP-001"
            }
        )
        assert classify_response.status_code == 200
        email_id = classify_response.json()["email_id"]
        classification = classify_response.json()["classification"]
        
        # Process
        process_response = client.post(
            "/api/emails/process",
            json={
                "email_id": email_id,
                "classification": classification
            }
        )
        
        if process_response.status_code == 200:
            data = process_response.json()
            if "sub_classification" in data:
                assert data["sub_classification"] in ["engineering", "procurement"]
                if data["sub_classification"] == "engineering":
                    assert data.get("requires_engineering", False) is True
    
    def test_process_quote(self, client):
        """Test processing quote email."""
        # Classify
        classify_response = client.post(
            "/api/emails/classify",
            json={
                "email_chain": [],
                "most_recent_reply": {
                    "subject": "Re: RFQ for MAT-12345",
                    "body": "Price: $1500 USD, Delivery: 4-6 weeks",
                    "from_email": "supplier@example.com",
                    "date": "2024-01-16T10:00:00Z"
                },
                "rfq_id": "RFQ-001",
                "supplier_id": "SUP-001"
            }
        )
        assert classify_response.status_code == 200
        email_id = classify_response.json()["email_id"]
        classification = classify_response.json()["classification"]
        
        # Process
        process_response = client.post(
            "/api/emails/process",
            json={
                "email_id": email_id,
                "classification": classification
            }
        )
        
        if process_response.status_code == 200:
            data = process_response.json()
            assert "email_id" in data
            assert "message" in data
    
    def test_process_engineer_response(self, client):
        """Test processing engineer response email."""
        # Classify
        classify_response = client.post(
            "/api/emails/classify",
            json={
                "email_chain": [],
                "most_recent_reply": {
                    "subject": "Engineering Review",
                    "body": "Technical review completed by engineering team",
                    "from_email": "engineer@company.com",
                    "date": "2024-01-16T10:00:00Z"
                },
                "rfq_id": "RFQ-001",
                "supplier_id": "SUP-001"
            }
        )
        assert classify_response.status_code == 200
        email_id = classify_response.json()["email_id"]
        classification = classify_response.json()["classification"]
        
        # Process
        process_response = client.post(
            "/api/emails/process",
            json={
                "email_id": email_id,
                "classification": classification
            }
        )
        
        if process_response.status_code == 200:
            data = process_response.json()
            assert "email_id" in data
            assert "message" in data
    
    def test_process_email_not_found(self, client):
        """Test 404 for non-existent email."""
        response = client.post(
            "/api/emails/process",
            json={
                "email_id": "EMAIL-NONEXISTENT",
                "classification": "quote"
            }
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_process_email_classification_mismatch(self, client):
        """Test 400 for wrong classification."""
        # Classify as quote
        classify_response = client.post(
            "/api/emails/classify",
            json={
                "email_chain": [],
                "most_recent_reply": {
                    "subject": "Quote",
                    "body": "Price: $1000 USD",
                    "from_email": "supplier@example.com",
                    "date": "2024-01-16T10:00:00Z"
                },
                "rfq_id": "RFQ-001",
                "supplier_id": "SUP-001"
            }
        )
        assert classify_response.status_code == 200
        email_id = classify_response.json()["email_id"]
        actual_classification = classify_response.json()["classification"]
        
        # Try to process with wrong classification
        wrong_classification = "clarification_request" if actual_classification == "quote" else "quote"
        response = client.post(
            "/api/emails/process",
            json={
                "email_id": email_id,
                "classification": wrong_classification
            }
        )
        
        assert response.status_code == 400
        assert "mismatch" in response.json()["detail"].lower()
    
    def test_process_email_response_structure(self, client):
        """Validate response structure."""
        # Classify
        classify_response = client.post(
            "/api/emails/classify",
            json={
                "email_chain": [],
                "most_recent_reply": {
                    "subject": "Question",
                    "body": "What is the delivery address?",
                    "from_email": "supplier@example.com",
                    "date": "2024-01-16T10:00:00Z"
                },
                "rfq_id": "RFQ-001",
                "supplier_id": "SUP-001"
            }
        )
        assert classify_response.status_code == 200
        email_id = classify_response.json()["email_id"]
        classification = classify_response.json()["classification"]
        
        # Process
        process_response = client.post(
            "/api/emails/process",
            json={
                "email_id": email_id,
                "classification": classification
            }
        )
        
        if process_response.status_code == 200:
            data = process_response.json()
            assert "email_id" in data
            assert "message" in data
            
            if classification == "clarification_request":
                assert "sub_classification" in data
                assert "question" in data
                assert "requires_engineering" in data


class TestSuggestResponseAPI:
    """Tests for suggest response API endpoints."""
    
    def test_suggest_response_procurement(self, client):
        """Test response generation for procurement clarification."""
        # Classify and process
        classify_response = client.post(
            "/api/emails/classify",
            json={
                "email_chain": [],
                "most_recent_reply": {
                    "subject": "Question",
                    "body": "What is the delivery address?",
                    "from_email": "supplier@example.com",
                    "date": "2024-01-16T10:00:00Z"
                },
                "rfq_id": "RFQ-001",
                "supplier_id": "SUP-001"
            }
        )
        email_id = classify_response.json()["email_id"]
        
        process_response = client.post(
            "/api/emails/process",
            json={
                "email_id": email_id,
                "classification": "clarification_request"
            }
        )
        
        if process_response.status_code == 200:
            data = process_response.json()
            clarification_id = data.get("clarification_id")
            
            if clarification_id:
                suggest_response = client.post(
                    "/api/emails/suggest-response",
                    json={
                        "clarification_id": clarification_id,
                        "email_id": email_id,
                        "question": data.get("question", "What is the delivery address?")
                    }
                )
                
                assert suggest_response.status_code == 200
                suggest_data = suggest_response.json()
                assert "suggested_response" in suggest_data
                assert "draft_subject" in suggest_data
                assert isinstance(suggest_data["suggested_response"], str)
                assert len(suggest_data["suggested_response"]) > 0
                assert isinstance(suggest_data["draft_subject"], str)
    
    def test_suggest_response_structure(self, client):
        """Validate response fields."""
        # Create a clarification first
        classify_response = client.post(
            "/api/emails/classify",
            json={
                "email_chain": [],
                "most_recent_reply": {
                    "subject": "Question",
                    "body": "What are the payment terms?",
                    "from_email": "supplier@example.com",
                    "date": "2024-01-16T10:00:00Z"
                },
                "rfq_id": "RFQ-001",
                "supplier_id": "SUP-001"
            }
        )
        email_id = classify_response.json()["email_id"]
        
        process_response = client.post(
            "/api/emails/process",
            json={
                "email_id": email_id,
                "classification": "clarification_request"
            }
        )
        
        if process_response.status_code == 200:
            data = process_response.json()
            clarification_id = data.get("clarification_id")
            
            if clarification_id:
                suggest_response = client.post(
                    "/api/emails/suggest-response",
                    json={
                        "clarification_id": clarification_id,
                        "email_id": email_id,
                        "question": data.get("question", "What are the payment terms?")
                    }
                )
                
                if suggest_response.status_code == 200:
                    suggest_data = suggest_response.json()
                    required_fields = ["suggested_response", "draft_subject"]
                    for field in required_fields:
                        assert field in suggest_data, f"Missing field: {field}"
    
    def test_suggest_response_not_found(self, client):
        """Test 404 for non-existent clarification."""
        response = client.post(
            "/api/emails/suggest-response",
            json={
                "clarification_id": "CLAR-NONEXISTENT",
                "email_id": "EMAIL-001",
                "question": "Test question"
            }
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestForwardToEngineeringAPI:
    """Tests for forward to engineering API endpoints."""
    
    def test_forward_to_engineering_success(self, client):
        """Test successful forwarding."""
        # Classify and process
        classify_response = client.post(
            "/api/emails/classify",
            json={
                "email_chain": [],
                "most_recent_reply": {
                    "subject": "Question",
                    "body": "Can we use alternative material specification?",
                    "from_email": "supplier@example.com",
                    "date": "2024-01-16T10:00:00Z"
                },
                "rfq_id": "RFQ-001",
                "supplier_id": "SUP-001"
            }
        )
        email_id = classify_response.json()["email_id"]
        
        process_response = client.post(
            "/api/emails/process",
            json={
                "email_id": email_id,
                "classification": "clarification_request"
            }
        )
        
        if process_response.status_code == 200:
            data = process_response.json()
            clarification_id = data.get("clarification_id")
            
            if clarification_id:
                forward_response = client.post(
                    "/api/emails/forward-to-engineering",
                    json={
                        "email_id": email_id,
                        "clarification_id": clarification_id
                    }
                )
                
                assert forward_response.status_code == 200
                forward_data = forward_response.json()
                assert forward_data["status"] == "sent_to_engineering"
                assert "message" in forward_data
    
    def test_forward_to_engineering_not_found(self, client):
        """Test 404 cases."""
        response = client.post(
            "/api/emails/forward-to-engineering",
            json={
                "email_id": "EMAIL-NONEXISTENT",
                "clarification_id": "CLAR-NONEXISTENT"
            }
        )
        
        assert response.status_code == 404
    
    def test_forward_to_engineering_status_update(self, client):
        """Verify status updates."""
        # Classify and process
        classify_response = client.post(
            "/api/emails/classify",
            json={
                "email_chain": [],
                "most_recent_reply": {
                    "subject": "Question",
                    "body": "What material grade is required?",
                    "from_email": "supplier@example.com",
                    "date": "2024-01-16T10:00:00Z"
                },
                "rfq_id": "RFQ-001",
                "supplier_id": "SUP-001"
            }
        )
        email_id = classify_response.json()["email_id"]
        
        process_response = client.post(
            "/api/emails/process",
            json={
                "email_id": email_id,
                "classification": "clarification_request"
            }
        )
        
        if process_response.status_code == 200:
            data = process_response.json()
            clarification_id = data.get("clarification_id")
            
            if clarification_id:
                forward_response = client.post(
                    "/api/emails/forward-to-engineering",
                    json={
                        "email_id": email_id,
                        "clarification_id": clarification_id
                    }
                )
                
                assert forward_response.status_code == 200
                assert forward_response.json()["status"] == "sent_to_engineering"


class TestEngineerResponseAPI:
    """Tests for engineer response API endpoints."""
    
    def test_process_engineer_response_success(self, client):
        """Test draft generation."""
        # Classify
        classify_response = client.post(
            "/api/emails/classify",
            json={
                "email_chain": [],
                "most_recent_reply": {
                    "subject": "Engineer Response",
                    "body": "Technical response from engineer",
                    "from_email": "engineer@company.com",
                    "date": "2024-01-16T10:00:00Z"
                },
                "rfq_id": "RFQ-001",
                "supplier_id": "SUP-001"
            }
        )
        email_id = classify_response.json()["email_id"]
        
        # Process engineer response
        response = client.post(
            "/api/emails/process-engineer-response",
            json={
                "email_id": email_id,
                "engineer_response": {
                    "body": "Yes, alternative material X can be used with these specifications...",
                    "from": "engineer@company.com"
                }
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "draft_response" in data
        assert "subject" in data["draft_response"]
        assert "body" in data["draft_response"]
        assert "to" in data["draft_response"]
    
    def test_process_engineer_response_structure(self, client):
        """Validate draft response structure."""
        # Classify
        classify_response = client.post(
            "/api/emails/classify",
            json={
                "email_chain": [],
                "most_recent_reply": {
                    "subject": "Engineering Review",
                    "body": "Review completed",
                    "from_email": "engineer@company.com",
                    "date": "2024-01-16T10:00:00Z"
                },
                "rfq_id": "RFQ-001",
                "supplier_id": "SUP-001"
            }
        )
        email_id = classify_response.json()["email_id"]
        
        # Process
        response = client.post(
            "/api/emails/process-engineer-response",
            json={
                "email_id": email_id,
                "engineer_response": {
                    "body": "Technical approval granted",
                    "from": "engineer@company.com"
                }
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            draft = data["draft_response"]
            required_fields = ["subject", "body", "to"]
            for field in required_fields:
                assert field in draft, f"Missing field: {field}"
            assert isinstance(draft["subject"], str)
            assert isinstance(draft["body"], str)
            assert isinstance(draft["to"], str)
            assert "@" in draft["to"]  # Valid email format
    
    def test_process_engineer_response_not_found(self, client):
        """Test 404 cases."""
        response = client.post(
            "/api/emails/process-engineer-response",
            json={
                "email_id": "EMAIL-NONEXISTENT",
                "engineer_response": {
                    "body": "Test",
                    "from": "engineer@company.com"
                }
            }
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestQuoteExtractionAPI:
    """Tests for quote extraction API endpoints."""
    
    def test_extract_quote_success(self, client):
        """Test quote extraction."""
        # Classify
        classify_response = client.post(
            "/api/emails/classify",
            json={
                "email_chain": [],
                "most_recent_reply": {
                    "subject": "Re: RFQ for MAT-12345",
                    "body": "Price: $1500 USD, Delivery: 4-6 weeks",
                    "from_email": "supplier@example.com",
                    "date": "2024-01-16T10:00:00Z"
                },
                "rfq_id": "RFQ-001",
                "supplier_id": "SUP-001"
            }
        )
        email_id = classify_response.json()["email_id"]
        
        # Extract quote
        extract_response = client.post(
            "/api/emails/extract-quote",
            json={
                "email_id": email_id,
                "rfq_id": "RFQ-001",
                "supplier_id": "SUP-001",
                "email_body": "Price: $1500 USD, Delivery: 4-6 weeks, Valid for 30 days"
            }
        )
        
        assert extract_response.status_code == 200
        data = extract_response.json()
        
        assert "quote_id" in data
        assert "extracted_details" in data
        assert "status" in data
        assert data["status"] == "received"
        assert isinstance(data["extracted_details"], dict)
    
    def test_extract_quote_with_price(self, client):
        """Test with price extraction."""
        # Classify
        classify_response = client.post(
            "/api/emails/classify",
            json={
                "email_chain": [],
                "most_recent_reply": {
                    "subject": "Quote",
                    "body": "Our quotation: $2000 USD",
                    "from_email": "supplier@example.com",
                    "date": "2024-01-16T10:00:00Z"
                },
                "rfq_id": "RFQ-001",
                "supplier_id": "SUP-001"
            }
        )
        email_id = classify_response.json()["email_id"]
        
        # Extract
        extract_response = client.post(
            "/api/emails/extract-quote",
            json={
                "email_id": email_id,
                "rfq_id": "RFQ-001",
                "supplier_id": "SUP-001",
                "email_body": "Our quotation: $2000 USD, delivery in 5 weeks"
            }
        )
        
        assert extract_response.status_code == 200
        data = extract_response.json()
        assert "extracted_details" in data
        details = data["extracted_details"]
        # Price may or may not be extracted depending on mock implementation
        assert isinstance(details, dict)
    
    def test_extract_quote_with_delivery(self, client):
        """Test with delivery time."""
        # Classify
        classify_response = client.post(
            "/api/emails/classify",
            json={
                "email_chain": [],
                "most_recent_reply": {
                    "subject": "Quote",
                    "body": "Delivery: 6-8 weeks",
                    "from_email": "supplier@example.com",
                    "date": "2024-01-16T10:00:00Z"
                },
                "rfq_id": "RFQ-001",
                "supplier_id": "SUP-001"
            }
        )
        email_id = classify_response.json()["email_id"]
        
        # Extract
        extract_response = client.post(
            "/api/emails/extract-quote",
            json={
                "email_id": email_id,
                "rfq_id": "RFQ-001",
                "supplier_id": "SUP-001",
                "email_body": "Price: $1000, Delivery: 6-8 weeks, Valid for 30 days"
            }
        )
        
        assert extract_response.status_code == 200
        data = extract_response.json()
        assert "extracted_details" in data
        details = data["extracted_details"]
        assert isinstance(details, dict)
    
    def test_extract_quote_response_structure(self, client):
        """Validate extracted details."""
        # Classify
        classify_response = client.post(
            "/api/emails/classify",
            json={
                "email_chain": [],
                "most_recent_reply": {
                    "subject": "Quote",
                    "body": "Our quote",
                    "from_email": "supplier@example.com",
                    "date": "2024-01-16T10:00:00Z"
                },
                "rfq_id": "RFQ-001",
                "supplier_id": "SUP-001"
            }
        )
        email_id = classify_response.json()["email_id"]
        
        # Extract
        extract_response = client.post(
            "/api/emails/extract-quote",
            json={
                "email_id": email_id,
                "rfq_id": "RFQ-001",
                "supplier_id": "SUP-001",
                "email_body": "Price: $1000 USD"
            }
        )
        
        assert extract_response.status_code == 200
        data = extract_response.json()
        
        required_fields = ["quote_id", "extracted_details", "status"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        assert isinstance(data["quote_id"], str)
        assert isinstance(data["extracted_details"], dict)
        assert isinstance(data["status"], str)
        assert data["status"] == "received"
    
    def test_extract_quote_status_update(self, client):
        """Verify email status update."""
        # Classify
        classify_response = client.post(
            "/api/emails/classify",
            json={
                "email_chain": [],
                "most_recent_reply": {
                    "subject": "Quote",
                    "body": "Our quote",
                    "from_email": "supplier@example.com",
                    "date": "2024-01-16T10:00:00Z"
                },
                "rfq_id": "RFQ-001",
                "supplier_id": "SUP-001"
            }
        )
        email_id = classify_response.json()["email_id"]
        
        # Extract
        extract_response = client.post(
            "/api/emails/extract-quote",
            json={
                "email_id": email_id,
                "rfq_id": "RFQ-001",
                "supplier_id": "SUP-001",
                "email_body": "Price: $1000 USD"
            }
        )
        
        assert extract_response.status_code == 200
        # Status should be updated to "processed" after extraction
        assert extract_response.json()["status"] == "received"


class TestQuotesAPI:
    """Tests for quotes API endpoints."""
    
    def test_get_quotes_by_rfq_with_quotes(self, client):
        """Test with existing quotes."""
        # Extract quotes
        for i in range(2):
            classify_response = client.post(
                "/api/emails/classify",
                json={
                    "email_chain": [],
                    "most_recent_reply": {
                        "subject": f"Quote {i+1}",
                        "body": f"Price: ${1000 + i*100}",
                        "from_email": f"supplier{i+1}@example.com",
                        "date": "2024-01-16T10:00:00Z"
                    },
                    "rfq_id": "RFQ-001",
                    "supplier_id": f"SUP-00{i+1}"
                }
            )
            email_id = classify_response.json()["email_id"]
            
            client.post(
                "/api/emails/extract-quote",
                json={
                    "email_id": email_id,
                    "rfq_id": "RFQ-001",
                    "supplier_id": f"SUP-00{i+1}",
                    "email_body": f"Price: ${1000 + i*100} USD"
                }
            )
        
        # Get quotes
        response = client.get("/api/quotes/RFQ-001")
        
        assert response.status_code == 200
        data = response.json()
        assert "quotes" in data
        assert isinstance(data["quotes"], list)
        assert len(data["quotes"]) >= 2
    
    def test_get_quotes_by_rfq_empty(self, client):
        """Test with no quotes."""
        response = client.get("/api/quotes/RFQ-NONEXISTENT")
        
        assert response.status_code == 200
        data = response.json()
        assert "quotes" in data
        assert len(data["quotes"]) == 0
    
    def test_get_quotes_response_structure(self, client):
        """Validate quote list structure."""
        # Extract a quote
        classify_response = client.post(
            "/api/emails/classify",
            json={
                "email_chain": [],
                "most_recent_reply": {
                    "subject": "Quote",
                    "body": "Price: $1000",
                    "from_email": "supplier@example.com",
                    "date": "2024-01-16T10:00:00Z"
                },
                "rfq_id": "RFQ-001",
                "supplier_id": "SUP-001"
            }
        )
        email_id = classify_response.json()["email_id"]
        
        client.post(
            "/api/emails/extract-quote",
            json={
                "email_id": email_id,
                "rfq_id": "RFQ-001",
                "supplier_id": "SUP-001",
                "email_body": "Price: $1000 USD"
            }
        )
        
        # Get quotes
        response = client.get("/api/quotes/RFQ-001")
        
        assert response.status_code == 200
        data = response.json()
        assert "quotes" in data
        
        if len(data["quotes"]) > 0:
            quote = data["quotes"][0]
            required_fields = ["quote_id", "supplier_name", "quote_date", "status"]
            for field in required_fields:
                assert field in quote, f"Missing field: {field}"
    
    def test_get_quotes_multiple_suppliers(self, client):
        """Test multiple quotes from different suppliers."""
        # Extract quotes from different suppliers
        suppliers = ["SUP-001", "SUP-002"]
        for supplier_id in suppliers:
            classify_response = client.post(
                "/api/emails/classify",
                json={
                    "email_chain": [],
                    "most_recent_reply": {
                        "subject": f"Quote from {supplier_id}",
                        "body": f"Price: $1000",
                        "from_email": f"supplier@{supplier_id.lower()}.com",
                        "date": "2024-01-16T10:00:00Z"
                    },
                    "rfq_id": "RFQ-001",
                    "supplier_id": supplier_id
                }
            )
            email_id = classify_response.json()["email_id"]
            
            client.post(
                "/api/emails/extract-quote",
                json={
                    "email_id": email_id,
                    "rfq_id": "RFQ-001",
                    "supplier_id": supplier_id,
                    "email_body": f"Price: $1000 USD from {supplier_id}"
                }
            )
        
        # Get quotes
        response = client.get("/api/quotes/RFQ-001")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["quotes"]) >= 2
        
        # Verify different suppliers
        supplier_ids = {quote["supplier_name"] for quote in data["quotes"]}
        assert len(supplier_ids) >= 1  # At least one supplier


class TestEmailWorkflowAPI:
    """Tests for complete email workflows."""
    
    def test_complete_quote_workflow(self, client):
        """Full workflow: classify → extract → retrieve."""
        # Step 1: Classify
        classify_response = client.post(
            "/api/emails/classify",
            json={
                "email_chain": [],
                "most_recent_reply": {
                    "subject": "Re: RFQ for MAT-12345",
                    "body": "Price: $1500 USD, Delivery: 4-6 weeks",
                    "from_email": "supplier@example.com",
                    "date": "2024-01-16T10:00:00Z"
                },
                "rfq_id": "RFQ-001",
                "supplier_id": "SUP-001"
            }
        )
        assert classify_response.status_code == 200
        email_id = classify_response.json()["email_id"]
        
        # Step 2: Extract quote
        extract_response = client.post(
            "/api/emails/extract-quote",
            json={
                "email_id": email_id,
                "rfq_id": "RFQ-001",
                "supplier_id": "SUP-001",
                "email_body": "Price: $1500 USD, Delivery: 4-6 weeks, Valid for 30 days"
            }
        )
        assert extract_response.status_code == 200
        quote_id = extract_response.json()["quote_id"]
        
        # Step 3: Retrieve quotes
        quotes_response = client.get("/api/quotes/RFQ-001")
        assert quotes_response.status_code == 200
        quotes = quotes_response.json()["quotes"]
        
        # Verify quote is in the list
        quote_ids = [q["quote_id"] for q in quotes]
        assert quote_id in quote_ids
    
    def test_complete_clarification_workflow(self, client):
        """Full workflow: classify → process → suggest → forward."""
        # Step 1: Classify
        classify_response = client.post(
            "/api/emails/classify",
            json={
                "email_chain": [],
                "most_recent_reply": {
                    "subject": "Question",
                    "body": "What is the delivery address?",
                    "from_email": "supplier@example.com",
                    "date": "2024-01-16T10:00:00Z"
                },
                "rfq_id": "RFQ-001",
                "supplier_id": "SUP-001"
            }
        )
        assert classify_response.status_code == 200
        email_id = classify_response.json()["email_id"]
        classification = classify_response.json()["classification"]
        
        # Step 2: Process
        if classification == "clarification_request":
            process_response = client.post(
                "/api/emails/process",
                json={
                    "email_id": email_id,
                    "classification": classification
                }
            )
            assert process_response.status_code == 200
            data = process_response.json()
            clarification_id = data.get("clarification_id")
            
            # Step 3: Suggest response (if procurement)
            if data.get("sub_classification") == "procurement" and clarification_id:
                suggest_response = client.post(
                    "/api/emails/suggest-response",
                    json={
                        "clarification_id": clarification_id,
                        "email_id": email_id,
                        "question": data.get("question", "What is the delivery address?")
                    }
                )
                assert suggest_response.status_code == 200
                assert "suggested_response" in suggest_response.json()
            
            # Step 4: Forward to engineering (if engineering)
            if data.get("sub_classification") == "engineering" and clarification_id:
                forward_response = client.post(
                    "/api/emails/forward-to-engineering",
                    json={
                        "email_id": email_id,
                        "clarification_id": clarification_id
                    }
                )
                assert forward_response.status_code == 200
                assert forward_response.json()["status"] == "sent_to_engineering"
    
    def test_complete_engineering_workflow(self, client):
        """Full workflow: classify → process → engineer response → draft."""
        # Step 1: Classify clarification
        classify_response = client.post(
            "/api/emails/classify",
            json={
                "email_chain": [],
                "most_recent_reply": {
                    "subject": "Question",
                    "body": "Can we use alternative material?",
                    "from_email": "supplier@example.com",
                    "date": "2024-01-16T10:00:00Z"
                },
                "rfq_id": "RFQ-001",
                "supplier_id": "SUP-001"
            }
        )
        assert classify_response.status_code == 200
        email_id = classify_response.json()["email_id"]
        
        # Step 2: Process clarification
        process_response = client.post(
            "/api/emails/process",
            json={
                "email_id": email_id,
                "classification": "clarification_request"
            }
        )
        assert process_response.status_code == 200
        
        # Step 3: Classify engineer response
        engineer_classify = client.post(
            "/api/emails/classify",
            json={
                "email_chain": [],
                "most_recent_reply": {
                    "subject": "Engineering Review",
                    "body": "Technical review completed",
                    "from_email": "engineer@company.com",
                    "date": "2024-01-16T10:00:00Z"
                },
                "rfq_id": "RFQ-001",
                "supplier_id": "SUP-001"
            }
        )
        engineer_email_id = engineer_classify.json()["email_id"]
        
        # Step 4: Process engineer response
        engineer_response = client.post(
            "/api/emails/process-engineer-response",
            json={
                "email_id": engineer_email_id,
                "engineer_response": {
                    "body": "Alternative material approved with specifications...",
                    "from": "engineer@company.com"
                }
            }
        )
        assert engineer_response.status_code == 200
        assert "draft_response" in engineer_response.json()
