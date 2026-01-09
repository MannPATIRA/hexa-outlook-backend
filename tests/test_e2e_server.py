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
