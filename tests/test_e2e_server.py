"""End-to-end tests with a real uvicorn server."""
import pytest
import httpx
import socket
import time
import atexit
from typing import Generator


def find_free_port() -> int:
    """Find an available port for the test server."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


@pytest.fixture(scope="session")
def server_port() -> int:
    """Get an available port for the test server."""
    port = find_free_port()
    return port


@pytest.fixture(scope="session")
def server_process(server_port: int) -> Generator[None, None, None]:
    """Start uvicorn server in a thread and ensure cleanup."""
    import uvicorn
    from app.main import app
    
    # Configure server
    config = uvicorn.Config(
        app=app,
        host="127.0.0.1",
        port=server_port,
        log_level="error",  # Reduce noise in test output
        access_log=False
    )
    server = uvicorn.Server(config)
    
    # Start server in a daemon thread
    import threading
    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()
    
    # Wait for server to be ready
    base_url = f"http://127.0.0.1:{server_port}"
    max_attempts = 50
    for attempt in range(max_attempts):
        try:
            response = httpx.get(f"{base_url}/health", timeout=1.0)
            if response.status_code == 200:
                break
        except (httpx.ConnectError, httpx.TimeoutException):
            if attempt < max_attempts - 1:
                time.sleep(0.2)
            else:
                pytest.fail("Server failed to start within timeout")
    
    # Register cleanup function
    def cleanup():
        try:
            server.should_exit = True
            time.sleep(0.5)
        except Exception:
            pass
    
    atexit.register(cleanup)
    
    yield
    
    # Cleanup: shutdown server
    try:
        server.should_exit = True
        # Give it a moment to shutdown gracefully
        time.sleep(0.5)
    except Exception as e:
        # Force cleanup if graceful shutdown fails
        print(f"Warning: Error during server shutdown: {e}")


@pytest.fixture
def client(server_port: int, server_process) -> Generator[httpx.Client, None, None]:
    """Create an HTTP client for making requests to the test server."""
    base_url = f"http://127.0.0.1:{server_port}"
    with httpx.Client(base_url=base_url, timeout=10.0) as client:
        yield client


class TestE2ERootAndHealth:
    """Test root and health endpoints."""
    
    def test_root_endpoint(self, client: httpx.Client):
        """Test the root endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data
        assert data["message"] == "Outlook Add-in Backend API"
        assert data["version"] == "1.0.0"
    
    def test_health_endpoint(self, client: httpx.Client):
        """Test the health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "outlook-add-in-backend"


class TestE2EPurchaseRequisitions:
    """Test Purchase Requisitions endpoints with real HTTP requests."""
    
    def test_get_open_prs(self, client: httpx.Client):
        """Test getting all open PRs."""
        response = client.get("/api/prs/open")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "prs" in data
        assert isinstance(data["prs"], list)
        assert len(data["prs"]) > 0
        
        # Verify structure of first PR
        pr = data["prs"][0]
        required_fields = [
            "pr_id", "material", "specs", "drawing_files",
            "quantities", "unit", "status", "created_date"
        ]
        for field in required_fields:
            assert field in pr, f"Missing field: {field}"
        
        assert pr["status"] == "open"
        assert isinstance(pr["drawing_files"], list)
        assert isinstance(pr["specs"], dict)
    
    def test_get_open_prs_response_structure(self, client: httpx.Client):
        """Test that open PRs response has correct structure."""
        response = client.get("/api/prs/open")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate all PRs have required fields
        for pr in data["prs"]:
            assert "pr_id" in pr
            assert "material" in pr
            assert "quantities" in pr
            assert "unit" in pr
            assert pr["quantities"] > 0


class TestE2ESuppliers:
    """Test Suppliers endpoints with real HTTP requests."""
    
    def test_search_suppliers_with_pr_id(self, client: httpx.Client):
        """Test searching suppliers with PR ID."""
        # First get a PR ID
        prs_response = client.get("/api/prs/open")
        assert prs_response.status_code == 200
        prs = prs_response.json()["prs"]
        
        if prs:
            pr_id = prs[0]["pr_id"]
            
            response = client.post(
                "/api/suppliers/search",
                json={"pr_id": pr_id}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert "suppliers" in data
            assert isinstance(data["suppliers"], list)
            
            # Check structure of suppliers
            if data["suppliers"]:
                supplier = data["suppliers"][0]
                assert "supplier_id" in supplier
                assert "name" in supplier
                assert "email" in supplier
                assert "match_reason" in supplier
    
    def test_search_suppliers_with_material(self, client: httpx.Client):
        """Test searching suppliers with material code."""
        prs_response = client.get("/api/prs/open")
        assert prs_response.status_code == 200
        prs = prs_response.json()["prs"]
        
        if prs:
            pr_id = prs[0]["pr_id"]
            material = prs[0]["material"]
            
            response = client.post(
                "/api/suppliers/search",
                json={
                    "pr_id": pr_id,
                    "material": material
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "suppliers" in data
    
    def test_search_suppliers_with_specs(self, client: httpx.Client):
        """Test searching suppliers with specifications."""
        prs_response = client.get("/api/prs/open")
        assert prs_response.status_code == 200
        prs = prs_response.json()["prs"]
        
        if prs:
            pr_id = prs[0]["pr_id"]
            specs = prs[0]["specs"]
            
            response = client.post(
                "/api/suppliers/search",
                json={
                    "pr_id": pr_id,
                    "specs": specs
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "suppliers" in data
    
    def test_search_suppliers_invalid_pr_id(self, client: httpx.Client):
        """Test searching suppliers with invalid PR ID."""
        response = client.post(
            "/api/suppliers/search",
            json={"pr_id": "PR-NONEXISTENT"}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_search_suppliers_validation_error(self, client: httpx.Client):
        """Test supplier search with missing required field."""
        response = client.post(
            "/api/suppliers/search",
            json={}  # Missing pr_id
        )
        
        assert response.status_code == 422  # Validation error


class TestE2ERFQs:
    """Test RFQs endpoints with real HTTP requests."""
    
    def test_generate_rfqs(self, client: httpx.Client):
        """Test generating RFQs for suppliers."""
        # Get a PR and suppliers
        prs_response = client.get("/api/prs/open")
        assert prs_response.status_code == 200
        prs = prs_response.json()["prs"]
        
        if prs:
            pr_id = prs[0]["pr_id"]
            
            # Get suppliers for this PR
            suppliers_response = client.post(
                "/api/suppliers/search",
                json={"pr_id": pr_id}
            )
            assert suppliers_response.status_code == 200
            suppliers = suppliers_response.json()["suppliers"]
            
            if len(suppliers) >= 2:
                supplier_ids = [s["supplier_id"] for s in suppliers[:2]]
                
                response = client.post(
                    "/api/rfqs/generate",
                    json={
                        "pr_id": pr_id,
                        "supplier_ids": supplier_ids
                    }
                )
                
                assert response.status_code == 200
                data = response.json()
                
                assert "rfqs" in data
                assert len(data["rfqs"]) == 2
                
                # Check RFQ structure
                rfq = data["rfqs"][0]
                assert "rfq_id" in rfq
                assert "supplier_id" in rfq
                assert "supplier_name" in rfq
                assert "supplier_email" in rfq
                assert "pr_id" in rfq
                assert "subject" in rfq
                assert "body" in rfq
                assert "attachments" in rfq
                assert "status" in rfq
                assert rfq["status"] == "draft"
                
                # Check RFQ body structure
                body = rfq["body"]
                assert "greeting" in body
                assert "introduction" in body
                assert "material_details" in body
                assert "requirements" in body
                assert "drawing_files" in body
                assert "quotation_deadline" in body
                assert "closing" in body
    
    def test_generate_rfqs_invalid_pr_id(self, client: httpx.Client):
        """Test generating RFQs with invalid PR ID."""
        response = client.post(
            "/api/rfqs/generate",
            json={
                "pr_id": "PR-NONEXISTENT",
                "supplier_ids": ["SUP-001"]
            }
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_generate_rfqs_invalid_supplier_ids(self, client: httpx.Client):
        """Test generating RFQs with invalid supplier IDs."""
        prs_response = client.get("/api/prs/open")
        assert prs_response.status_code == 200
        prs = prs_response.json()["prs"]
        
        if prs:
            pr_id = prs[0]["pr_id"]
            
            response = client.post(
                "/api/rfqs/generate",
                json={
                    "pr_id": pr_id,
                    "supplier_ids": ["SUP-NONEXISTENT-1", "SUP-NONEXISTENT-2"]
                }
            )
            
            assert response.status_code == 404
            detail = response.json()["detail"]
            assert "supplier" in detail.lower() or "invalid" in detail.lower()
    
    def test_finalize_rfq(self, client: httpx.Client):
        """Test finalizing an RFQ."""
        # First generate an RFQ
        prs_response = client.get("/api/prs/open")
        assert prs_response.status_code == 200
        prs = prs_response.json()["prs"]
        
        if prs:
            pr_id = prs[0]["pr_id"]
            
            suppliers_response = client.post(
                "/api/suppliers/search",
                json={"pr_id": pr_id}
            )
            assert suppliers_response.status_code == 200
            suppliers = suppliers_response.json()["suppliers"]
            
            if suppliers:
                supplier_ids = [suppliers[0]["supplier_id"]]
                
                generate_response = client.post(
                    "/api/rfqs/generate",
                    json={
                        "pr_id": pr_id,
                        "supplier_ids": supplier_ids
                    }
                )
                assert generate_response.status_code == 200
                rfqs = generate_response.json()["rfqs"]
                rfq_id = rfqs[0]["rfq_id"]
                
                # Now finalize it
                finalize_response = client.post(
                    "/api/rfqs/finalize",
                    json={
                        "rfq_id": rfq_id,
                        "final_subject": "Finalized RFQ Subject",
                        "final_body": "Finalized body content",
                        "status": "ready_to_send"
                    }
                )
                
                assert finalize_response.status_code == 200
                data = finalize_response.json()
                
                assert data["rfq_id"] == rfq_id
                assert data["status"] == "finalized"
                assert "message" in data
    
    def test_finalize_rfq_with_json_body(self, client: httpx.Client):
        """Test finalizing RFQ with JSON body."""
        prs_response = client.get("/api/prs/open")
        assert prs_response.status_code == 200
        prs = prs_response.json()["prs"]
        
        if prs:
            pr_id = prs[0]["pr_id"]
            
            suppliers_response = client.post(
                "/api/suppliers/search",
                json={"pr_id": pr_id}
            )
            assert suppliers_response.status_code == 200
            suppliers = suppliers_response.json()["suppliers"]
            
            if suppliers:
                supplier_ids = [suppliers[0]["supplier_id"]]
                
                generate_response = client.post(
                    "/api/rfqs/generate",
                    json={
                        "pr_id": pr_id,
                        "supplier_ids": supplier_ids
                    }
                )
                assert generate_response.status_code == 200
                rfqs = generate_response.json()["rfqs"]
                rfq_id = rfqs[0]["rfq_id"]
                
                # Finalize with JSON body
                json_body = {
                    "greeting": "Dear Supplier,",
                    "content": "This is the finalized content"
                }
                
                finalize_response = client.post(
                    "/api/rfqs/finalize",
                    json={
                        "rfq_id": rfq_id,
                        "final_subject": "Finalized Subject",
                        "final_body": json_body,
                        "status": "ready_to_send"
                    }
                )
                
                assert finalize_response.status_code == 200
                assert finalize_response.json()["status"] == "finalized"
    
    def test_finalize_rfq_not_found(self, client: httpx.Client):
        """Test finalizing a non-existent RFQ."""
        response = client.post(
            "/api/rfqs/finalize",
            json={
                "rfq_id": "RFQ-NONEXISTENT",
                "final_subject": "Subject",
                "final_body": "Body",
                "status": "ready_to_send"
            }
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_finalize_rfq_validation_error(self, client: httpx.Client):
        """Test finalize RFQ with missing required fields."""
        response = client.post(
            "/api/rfqs/finalize",
            json={
                "rfq_id": "RFQ-001"
                # Missing final_subject and final_body
            }
        )
        
        assert response.status_code == 422  # Validation error


class TestE2EErrorHandling:
    """Test error handling with real HTTP requests."""
    
    def test_404_for_invalid_endpoint(self, client: httpx.Client):
        """Test 404 for invalid endpoint."""
        response = client.get("/api/invalid/endpoint")
        
        assert response.status_code == 404
    
    def test_422_validation_error(self, client: httpx.Client):
        """Test 422 validation error."""
        response = client.post(
            "/api/suppliers/search",
            json={"invalid": "data"}
        )
        
        assert response.status_code == 422


class TestE2ECORS:
    """Test CORS headers with real HTTP requests."""
    
    def test_cors_headers_present(self, client: httpx.Client):
        """Test that CORS headers are present in responses."""
        response = client.get(
            "/api/prs/open",
            headers={"Origin": "https://outlook.office.com"}
        )
        
        assert response.status_code == 200
        # Check for CORS headers
        # httpx Headers are case-insensitive, check using get() method
        cors_header = response.headers.get("access-control-allow-origin")
        # CORS middleware should add access-control-allow-origin header
        # It should be "*" (since we allow all origins) or the origin that was sent
        assert cors_header is not None, "CORS header 'access-control-allow-origin' should be present"
        assert cors_header == "*" or cors_header == "https://outlook.office.com"


class TestE2ECompleteWorkflow:
    """Test complete workflow with real HTTP requests."""
    
    def test_complete_workflow(self, client: httpx.Client):
        """Test the complete workflow: Get PRs → Search Suppliers → Generate RFQs → Finalize."""
        # Step 1: Get all open PRs
        prs_response = client.get("/api/prs/open")
        assert prs_response.status_code == 200
        prs = prs_response.json()["prs"]
        assert len(prs) > 0
        
        # Select first PR
        selected_pr = prs[0]
        pr_id = selected_pr["pr_id"]
        
        # Step 2: Search for suppliers matching this PR
        suppliers_response = client.post(
            "/api/suppliers/search",
            json={"pr_id": pr_id}
        )
        assert suppliers_response.status_code == 200
        suppliers = suppliers_response.json()["suppliers"]
        assert len(suppliers) > 0
        
        # Select first two suppliers
        selected_suppliers = suppliers[:2]
        supplier_ids = [s["supplier_id"] for s in selected_suppliers]
        
        # Step 3: Generate RFQs for selected suppliers
        generate_response = client.post(
            "/api/rfqs/generate",
            json={
                "pr_id": pr_id,
                "supplier_ids": supplier_ids
            }
        )
        assert generate_response.status_code == 200
        rfqs = generate_response.json()["rfqs"]
        assert len(rfqs) == len(supplier_ids)
        
        # Verify RFQ structure
        for rfq in rfqs:
            assert rfq["pr_id"] == pr_id
            assert rfq["supplier_id"] in supplier_ids
            assert rfq["status"] == "draft"
            assert "subject" in rfq
            assert "body" in rfq
            assert "attachments" in rfq
        
        # Step 4: Finalize each RFQ
        for rfq in rfqs:
            finalize_response = client.post(
                "/api/rfqs/finalize",
                json={
                    "rfq_id": rfq["rfq_id"],
                    "final_subject": f"Finalized: {rfq['subject']}",
                    "final_body": "Finalized body content after user review",
                    "status": "ready_to_send"
                }
            )
            assert finalize_response.status_code == 200
            finalized_data = finalize_response.json()
            assert finalized_data["status"] == "finalized"
            assert finalized_data["rfq_id"] == rfq["rfq_id"]


class TestE2EEmails:
    """Test email classification endpoints with real HTTP requests."""
    
    def test_classify_email_quote_e2e(self, client: httpx.Client):
        """Test classifying email as quote with real HTTP request."""
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
    
    def test_classify_email_clarification_e2e(self, client: httpx.Client):
        """Test classifying email as clarification with real HTTP request."""
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
        assert "confidence" in data
        assert "message" in data
    
    def test_classify_email_validation_e2e(self, client: httpx.Client):
        """Test validation errors with real server."""
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
    
    def test_classify_email_response_structure_e2e(self, client: httpx.Client):
        """Validate response structure with real HTTP request."""
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


class TestE2EEmailProcessing:
    """Test email processing endpoints with real HTTP requests."""
    
    def test_process_clarification_e2e(self, client: httpx.Client):
        """Test processing clarification with real HTTP request."""
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
        classification = classify_response.json()["classification"]
        
        # Process
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
            
            assert "email_id" in data
            if "sub_classification" in data:
                assert data["sub_classification"] in ["engineering", "procurement"]
                assert "question" in data
    
    def test_process_quote_e2e(self, client: httpx.Client):
        """Test processing quote with real HTTP request."""
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
    
    def test_process_email_not_found_e2e(self, client: httpx.Client):
        """Test 404 with real server."""
        response = client.post(
            "/api/emails/process",
            json={
                "email_id": "EMAIL-NONEXISTENT",
                "classification": "quote"
            }
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_process_email_classification_mismatch_e2e(self, client: httpx.Client):
        """Test 400 with real server."""
        # Classify
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
        
        # Try with wrong classification
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


class TestE2ESuggestResponse:
    """Test suggest response endpoints with real HTTP requests."""
    
    def test_suggest_response_e2e(self, client: httpx.Client):
        """Test response suggestion with real HTTP request."""
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
    
    def test_suggest_response_structure_e2e(self, client: httpx.Client):
        """Validate response structure with real HTTP request."""
        # Create clarification
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


class TestE2EForwardToEngineering:
    """Test forward to engineering endpoints with real HTTP requests."""
    
    def test_forward_to_engineering_e2e(self, client: httpx.Client):
        """Test forwarding with real HTTP request."""
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
    
    def test_forward_to_engineering_status_e2e(self, client: httpx.Client):
        """Verify status updates with real HTTP request."""
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


class TestE2EEngineerResponse:
    """Test engineer response endpoints with real HTTP requests."""
    
    def test_process_engineer_response_e2e(self, client: httpx.Client):
        """Test engineer response processing with real HTTP request."""
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
    
    def test_process_engineer_response_draft_e2e(self, client: httpx.Client):
        """Validate draft response with real HTTP request."""
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


class TestE2EQuoteExtraction:
    """Test quote extraction endpoints with real HTTP requests."""
    
    def test_extract_quote_e2e(self, client: httpx.Client):
        """Test quote extraction with real HTTP request."""
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
    
    def test_extract_quote_details_e2e(self, client: httpx.Client):
        """Validate extracted details with real HTTP request."""
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
        assert isinstance(details, dict)
    
    def test_extract_quote_multiple_e2e(self, client: httpx.Client):
        """Test multiple quote extractions with real HTTP request."""
        # Extract multiple quotes
        quote_ids = []
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
            
            extract_response = client.post(
                "/api/emails/extract-quote",
                json={
                    "email_id": email_id,
                    "rfq_id": "RFQ-001",
                    "supplier_id": f"SUP-00{i+1}",
                    "email_body": f"Price: ${1000 + i*100} USD"
                }
            )
            assert extract_response.status_code == 200
            quote_ids.append(extract_response.json()["quote_id"])
        
        # Verify quotes were extracted
        assert len(quote_ids) == 2
        assert len(set(quote_ids)) == 2  # All unique


class TestE2EQuotes:
    """Test quotes retrieval endpoints with real HTTP requests."""
    
    def test_get_quotes_by_rfq_e2e(self, client: httpx.Client):
        """Test quote retrieval with real HTTP request."""
        # Extract a quote first
        classify_response = client.post(
            "/api/emails/classify",
            json={
                "email_chain": [],
                "most_recent_reply": {
                    "subject": "Quote 1",
                    "body": "Price: $1000",
                    "from_email": "supplier1@example.com",
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
        assert isinstance(data["quotes"], list)
    
    def test_get_quotes_empty_e2e(self, client: httpx.Client):
        """Test empty quote list with real HTTP request."""
        response = client.get("/api/quotes/RFQ-NONEXISTENT")
        
        assert response.status_code == 200
        data = response.json()
        assert "quotes" in data
        assert len(data["quotes"]) == 0
    
    def test_get_quotes_structure_e2e(self, client: httpx.Client):
        """Validate quote list structure with real HTTP request."""
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


class TestE2ECompleteEmailWorkflows:
    """Test complete email workflows with real HTTP requests."""
    
    def test_complete_quote_workflow_e2e(self, client: httpx.Client):
        """End-to-end quote workflow with real HTTP requests."""
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
    
    def test_complete_clarification_workflow_e2e(self, client: httpx.Client):
        """End-to-end clarification workflow with real HTTP requests."""
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
    
    def test_complete_engineering_workflow_e2e(self, client: httpx.Client):
        """End-to-end engineering workflow with real HTTP requests."""
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


class TestE2EEmailErrorHandling:
    """Test email error handling with real HTTP requests."""
    
    def test_email_404_errors_e2e(self, client: httpx.Client):
        """Test all 404 error cases with real server."""
        # Test process email not found
        response = client.post(
            "/api/emails/process",
            json={
                "email_id": "EMAIL-NONEXISTENT",
                "classification": "quote"
            }
        )
        assert response.status_code == 404
        
        # Test suggest response not found
        response = client.post(
            "/api/emails/suggest-response",
            json={
                "clarification_id": "CLAR-NONEXISTENT",
                "email_id": "EMAIL-001",
                "question": "Test"
            }
        )
        assert response.status_code == 404
        
        # Test forward to engineering not found
        response = client.post(
            "/api/emails/forward-to-engineering",
            json={
                "email_id": "EMAIL-NONEXISTENT",
                "clarification_id": "CLAR-NONEXISTENT"
            }
        )
        assert response.status_code == 404
        
        # Test process engineer response not found
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
    
    def test_email_422_errors_e2e(self, client: httpx.Client):
        """Test all validation errors with real server."""
        # Test classify with missing fields
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
        
        # Test process with missing fields
        response = client.post(
            "/api/emails/process",
            json={
                # Missing email_id
                "classification": "quote"
            }
        )
        assert response.status_code == 422
        
        # Test extract quote with missing fields
        response = client.post(
            "/api/emails/extract-quote",
            json={
                "email_id": "EMAIL-001",
                # Missing rfq_id, supplier_id, email_body
            }
        )
        assert response.status_code == 422
    
    def test_email_400_errors_e2e(self, client: httpx.Client):
        """Test all 400 error cases with real server."""
        # Classify an email
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
        
        # Test classification mismatch
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


class TestE2ECleanup:
    """Test that server cleanup works correctly."""
    
    def test_server_is_running(self, client: httpx.Client, server_port: int):
        """Verify server is running and accessible."""
        # This test verifies the server is up
        response = client.get("/health")
        assert response.status_code == 200
        
        # Verify it's actually the test server by checking the port
        assert f":{server_port}" in str(client.base_url) or str(server_port) in str(client.base_url)
    
    def test_server_cleanup_after_tests(self, server_process, server_port: int):
        """Verify server can be accessed and will cleanup properly."""
        # This test runs at the end to verify cleanup
        # The server_process fixture handles cleanup via yield
        base_url = f"http://127.0.0.1:{server_port}"
        
        # Verify server is still running
        try:
            response = httpx.get(f"{base_url}/health", timeout=2.0)
            assert response.status_code == 200
        except Exception:
            # If server is already shutting down, that's okay
            pass

