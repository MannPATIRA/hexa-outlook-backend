"""Integration tests for the complete workflow."""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


class TestCompleteWorkflow:
    """Test the complete workflow from PR to RFQ finalization."""
    
    def test_complete_workflow(self, client):
        """Test the complete workflow: Get PRs -> Search Suppliers -> Generate RFQs -> Finalize."""
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
            
            # Verify body structure
            body = rfq["body"]
            assert "greeting" in body
            assert "material_details" in body
            assert "quotation_deadline" in body
        
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
    
    def test_multiple_prs_workflow(self, client):
        """Test workflow with multiple PRs."""
        # Get all PRs
        prs_response = client.get("/api/prs/open")
        assert prs_response.status_code == 200
        prs = prs_response.json()["prs"]
        
        # Process first two PRs
        for pr in prs[:2]:
            pr_id = pr["pr_id"]
            
            # Get suppliers
            suppliers_response = client.post(
                "/api/suppliers/search",
                json={"pr_id": pr_id}
            )
            assert suppliers_response.status_code == 200
            suppliers = suppliers_response.json()["suppliers"]
            
            if suppliers:
                # Generate RFQ for first supplier
                generate_response = client.post(
                    "/api/rfqs/generate",
                    json={
                        "pr_id": pr_id,
                        "supplier_ids": [suppliers[0]["supplier_id"]]
                    }
                )
                assert generate_response.status_code == 200
                rfqs = generate_response.json()["rfqs"]
                assert len(rfqs) == 1
                
                # Verify RFQ is for correct PR
                assert rfqs[0]["pr_id"] == pr_id
    
    def test_supplier_matching_accuracy(self, client):
        """Test that supplier matching returns relevant suppliers."""
        prs_response = client.get("/api/prs/open")
        assert prs_response.status_code == 200
        prs = prs_response.json()["prs"]
        
        for pr in prs:
            pr_id = pr["pr_id"]
            material = pr["material"]
            
            # Search suppliers
            suppliers_response = client.post(
                "/api/suppliers/search",
                json={"pr_id": pr_id}
            )
            assert suppliers_response.status_code == 200
            suppliers = suppliers_response.json()["suppliers"]
            
            # Verify suppliers have match reasons
            for supplier in suppliers:
                assert "match_reason" in supplier
                assert len(supplier["match_reason"]) > 0
                
                # If it's a standard supplier, verify it's listed as such
                if "Standard supplier" in supplier["match_reason"]:
                    assert material in supplier["match_reason"]
    
    def test_rfq_content_accuracy(self, client):
        """Test that RFQ content accurately reflects PR data."""
        prs_response = client.get("/api/prs/open")
        assert prs_response.status_code == 200
        prs = prs_response.json()["prs"]
        
        if prs:
            pr = prs[0]
            pr_id = pr["pr_id"]
            
            # Get suppliers and generate RFQ
            suppliers_response = client.post(
                "/api/suppliers/search",
                json={"pr_id": pr_id}
            )
            assert suppliers_response.status_code == 200
            suppliers = suppliers_response.json()["suppliers"]
            
            if suppliers:
                generate_response = client.post(
                    "/api/rfqs/generate",
                    json={
                        "pr_id": pr_id,
                        "supplier_ids": [suppliers[0]["supplier_id"]]
                    }
                )
                assert generate_response.status_code == 200
                rfqs = generate_response.json()["rfqs"]
                
                if rfqs:
                    rfq = rfqs[0]
                    body = rfq["body"]
                    material_details = body["material_details"]
                    
                    # Verify PR data is in RFQ
                    assert material_details["material_code"] == pr["material"]
                    assert material_details["quantity"] == pr["quantities"]
                    assert material_details["unit"] == pr["unit"]
                    
                    # Verify drawing files and step files are included
                    assert "drawing_files" in body
                    assert isinstance(body["drawing_files"], list)
                    assert "step_files" in body
                    assert isinstance(body["step_files"], list)
                    
                    # Verify attachments include both drawing and step files
                    assert "attachments" in rfq
                    assert isinstance(rfq["attachments"], list)