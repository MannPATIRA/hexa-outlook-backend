"""Tests for API endpoints."""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


class TestPRsAPI:
    """Tests for Purchase Requisitions API endpoints."""
    
    def test_get_open_prs(self, client):
        """Test getting all open PRs."""
        response = client.get("/api/prs/open")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "prs" in data
        assert isinstance(data["prs"], list)
        assert len(data["prs"]) > 0
        
        # Check structure of first PR
        pr = data["prs"][0]
        assert "pr_id" in pr
        assert "material" in pr
        assert "specs" in pr
        assert "drawing_files" in pr
        assert "step_files" in pr
        assert "quantities" in pr
        assert "unit" in pr
        assert "status" in pr
        assert pr["status"] == "open"
    
    def test_get_open_prs_response_structure(self, client):
        """Test that open PRs response has correct structure."""
        response = client.get("/api/prs/open")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate all required fields are present
        for pr in data["prs"]:
            required_fields = [
                "pr_id", "material", "specs", "drawing_files", "step_files",
                "quantities", "unit", "status", "created_date"
            ]
            for field in required_fields:
                assert field in pr, f"Missing field: {field}"


class TestSuppliersAPI:
    """Tests for Suppliers API endpoints."""
    
    def test_search_suppliers_with_pr_id(self, client):
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
    
    def test_search_suppliers_with_material(self, client):
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
    
    def test_search_suppliers_with_specs(self, client):
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
    
    def test_search_suppliers_invalid_pr_id(self, client):
        """Test searching suppliers with invalid PR ID."""
        response = client.post(
            "/api/suppliers/search",
            json={"pr_id": "PR-NONEXISTENT"}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_search_suppliers_validation_error(self, client):
        """Test supplier search with missing required field."""
        response = client.post(
            "/api/suppliers/search",
            json={}  # Missing pr_id
        )
        
        assert response.status_code == 422  # Validation error


class TestRFQsAPI:
    """Tests for RFQs API endpoints."""
    
    def test_generate_rfqs(self, client):
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
                assert "step_files" in body
                assert "quotation_deadline" in body
                assert "closing" in body
    
    def test_generate_rfqs_invalid_pr_id(self, client):
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
    
    def test_generate_rfqs_invalid_supplier_ids(self, client):
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
            # When all supplier IDs are invalid, the message is "No valid suppliers found"
            detail = response.json()["detail"]
            assert "supplier" in detail.lower() or "invalid" in detail.lower()
    
    def test_finalize_rfq(self, client):
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
    
    def test_finalize_rfq_with_json_body(self, client):
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
    
    def test_finalize_rfq_not_found(self, client):
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
    
    def test_finalize_rfq_validation_error(self, client):
        """Test finalize RFQ with missing required fields."""
        response = client.post(
            "/api/rfqs/finalize",
            json={
                "rfq_id": "RFQ-001"
                # Missing final_subject and final_body
            }
        )
        
        assert response.status_code == 422  # Validation error


class TestHealthAndRoot:
    """Tests for health check and root endpoints."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "outlook-add-in-backend"
    
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data


class TestErrorHandling:
    """Tests for error handling."""
    
    def test_cors_headers(self, client):
        """Test that CORS headers are present."""
        # Test CORS headers with a regular GET request
        response = client.get(
            "/api/prs/open",
            headers={"Origin": "https://outlook.office.com"}
        )
        
        # Should succeed and CORS headers should be present
        assert response.status_code == 200
        # Check for CORS headers (FastAPI CORS middleware adds these)
        assert "access-control-allow-origin" in response.headers or "*" in str(response.headers)
    
    def test_404_for_invalid_endpoint(self, client):
        """Test 404 for invalid endpoint."""
        response = client.get("/api/invalid/endpoint")
        
        assert response.status_code == 404
