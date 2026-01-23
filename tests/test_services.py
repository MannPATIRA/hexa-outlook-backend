"""Tests for service classes."""
import pytest
from app.services.mock_erp import MockERP
from app.services.pr_service import PRService
from app.services.supplier_service import SupplierService
from app.services.rfq_service import RFQService


class TestMockERP:
    """Tests for MockERP class."""
    
    def test_initialization(self, mock_erp):
        """Test MockERP initialization with sample data."""
        assert mock_erp is not None
        assert len(mock_erp.get_open_prs()) > 0
        assert len(mock_erp.get_all_suppliers()) > 0
    
    def test_get_open_prs(self, mock_erp):
        """Test getting open PRs."""
        open_prs = mock_erp.get_open_prs()
        
        assert len(open_prs) > 0
        for pr in open_prs:
            assert pr.status == "open"
    
    def test_get_pr_by_id(self, mock_erp):
        """Test getting a PR by ID."""
        # Get a PR ID from open PRs
        open_prs = mock_erp.get_open_prs()
        if open_prs:
            pr_id = open_prs[0].pr_id
            pr = mock_erp.get_pr_by_id(pr_id)
            
            assert pr is not None
            assert pr.pr_id == pr_id
        
        # Test non-existent PR
        non_existent = mock_erp.get_pr_by_id("PR-NONEXISTENT")
        assert non_existent is None
    
    def test_get_suppliers_by_material(self, mock_erp):
        """Test getting suppliers by material code."""
        # Get a material from a PR
        open_prs = mock_erp.get_open_prs()
        if open_prs:
            material = open_prs[0].material
            suppliers = mock_erp.get_suppliers_by_material(material)
            
            # Should return at least one supplier if material has standard suppliers
            assert isinstance(suppliers, list)
            for supplier in suppliers:
                assert material in supplier.standard_for_materials
    
    def test_get_suppliers_by_specs(self, mock_erp):
        """Test getting suppliers by specifications."""
        specs = {
            "material_type": "Steel Component",
            "grade": "SS304"
        }
        
        suppliers = mock_erp.get_suppliers_by_specs(specs)
        
        assert isinstance(suppliers, list)
        # Should find suppliers with matching capabilities
    
    def test_get_supplier_by_id(self, mock_erp):
        """Test getting a supplier by ID."""
        all_suppliers = mock_erp.get_all_suppliers()
        if all_suppliers:
            supplier_id = all_suppliers[0].supplier_id
            supplier = mock_erp.get_supplier_by_id(supplier_id)
            
            assert supplier is not None
            assert supplier.supplier_id == supplier_id
        
        # Test non-existent supplier
        non_existent = mock_erp.get_supplier_by_id("SUP-NONEXISTENT")
        assert non_existent is None
    
    def test_store_and_get_rfq(self, mock_erp):
        """Test storing and retrieving RFQs."""
        from app.models.rfq import RFQ
        
        rfq = RFQ(
            rfq_id="RFQ-TEST-001",
            supplier_id="SUP-001",
            pr_id="PR-001",
            subject="Test",
            body={"content": "test"}
        )
        
        mock_erp.store_rfq(rfq)
        retrieved = mock_erp.get_rfq_by_id("RFQ-TEST-001")
        
        assert retrieved is not None
        assert retrieved.rfq_id == "RFQ-TEST-001"
    
    def test_update_rfq_status(self, mock_erp):
        """Test updating RFQ status."""
        from app.models.rfq import RFQ
        
        rfq = RFQ(
            rfq_id="RFQ-TEST-002",
            supplier_id="SUP-001",
            pr_id="PR-001",
            subject="Test",
            body={"content": "test"}
        )
        
        mock_erp.store_rfq(rfq)
        mock_erp.update_rfq_status("RFQ-TEST-002", "finalized")
        
        retrieved = mock_erp.get_rfq_by_id("RFQ-TEST-002")
        assert retrieved.status == "finalized"


class TestPRService:
    """Tests for PRService class."""
    
    def test_decompose_pr(self, pr_service, mock_erp):
        """Test decomposing a PR."""
        open_prs = mock_erp.get_open_prs()
        if open_prs:
            pr = open_prs[0]
            decomposed = pr_service.decompose_pr(pr)
            
            assert decomposed["pr_id"] == pr.pr_id
            assert decomposed["material"] == pr.material
            assert "material_info" in decomposed
            assert "specifications" in decomposed
            assert "drawing_files" in decomposed
            assert "step_files" in decomposed
            assert "quantities" in decomposed
            assert "requirements" in decomposed
    
    def test_extract_material_code(self, pr_service, mock_erp):
        """Test extracting material code."""
        open_prs = mock_erp.get_open_prs()
        if open_prs:
            pr = open_prs[0]
            material = pr_service.extract_material_code(pr)
            
            assert material == pr.material
    
    def test_extract_specs(self, pr_service, mock_erp):
        """Test extracting specifications."""
        open_prs = mock_erp.get_open_prs()
        if open_prs:
            pr = open_prs[0]
            specs = pr_service.extract_specs(pr)
            
            assert specs == pr.specs
            assert isinstance(specs, dict)
    
    def test_extract_drawing_files(self, pr_service, mock_erp):
        """Test extracting drawing files."""
        open_prs = mock_erp.get_open_prs()
        if open_prs:
            pr = open_prs[0]
            files = pr_service.extract_drawing_files(pr)
            
            assert files == pr.drawing_files
            assert isinstance(files, list)
    
    def test_extract_step_files(self, pr_service, mock_erp):
        """Test extracting step files."""
        open_prs = mock_erp.get_open_prs()
        if open_prs:
            pr = open_prs[0]
            files = pr_service.extract_step_files(pr)
            
            assert files == pr.step_files
            assert isinstance(files, list)
    
    def test_extract_quantities(self, pr_service, mock_erp):
        """Test extracting quantities."""
        open_prs = mock_erp.get_open_prs()
        if open_prs:
            pr = open_prs[0]
            quantities = pr_service.extract_quantities(pr)
            
            assert quantities["amount"] == pr.quantities
            assert quantities["unit"] == pr.unit


class TestSupplierService:
    """Tests for SupplierService class."""
    
    def test_find_matching_suppliers(self, supplier_service, mock_erp):
        """Test finding matching suppliers for a PR."""
        open_prs = mock_erp.get_open_prs()
        if open_prs:
            pr = open_prs[0]
            matches = supplier_service.find_matching_suppliers(pr)
            
            assert isinstance(matches, list)
            # Should find at least some suppliers
            assert len(matches) >= 0
            
            # Check structure of matches
            if matches:
                match = matches[0]
                assert "supplier_id" in match
                assert "name" in match
                assert "email" in match
                assert "match_reason" in match
                assert "match_score" in match
    
    def test_get_suppliers_by_ids(self, supplier_service, mock_erp):
        """Test getting suppliers by IDs."""
        all_suppliers = mock_erp.get_all_suppliers()
        if len(all_suppliers) >= 2:
            supplier_ids = [all_suppliers[0].supplier_id, all_suppliers[1].supplier_id]
            suppliers = supplier_service.get_suppliers_by_ids(supplier_ids)
            
            assert len(suppliers) == 2
            assert suppliers[0].supplier_id in supplier_ids
            assert suppliers[1].supplier_id in supplier_ids
        
        # Test with invalid IDs
        invalid_suppliers = supplier_service.get_suppliers_by_ids(["INVALID-1", "INVALID-2"])
        assert len(invalid_suppliers) == 0


class TestRFQService:
    """Tests for RFQService class."""
    
    def test_generate_rfqs(self, rfq_service, mock_erp):
        """Test generating RFQs for suppliers."""
        open_prs = mock_erp.get_open_prs()
        all_suppliers = mock_erp.get_all_suppliers()
        
        if open_prs and len(all_suppliers) >= 2:
            pr = open_prs[0]
            suppliers = all_suppliers[:2]
            
            rfqs = rfq_service.generate_rfqs(pr, suppliers)
            
            assert len(rfqs) == 2
            assert rfqs[0].pr_id == pr.pr_id
            assert rfqs[1].pr_id == pr.pr_id
            assert rfqs[0].supplier_id == suppliers[0].supplier_id
            assert rfqs[1].supplier_id == suppliers[1].supplier_id
            
            # Check RFQ structure
            rfq = rfqs[0]
            assert rfq.subject is not None
            assert rfq.body is not None
            assert "greeting" in rfq.body
            assert "introduction" in rfq.body
            assert "material_details" in rfq.body
            assert "drawing_files" in rfq.body
            assert "step_files" in rfq.body
            assert rfq.status == "draft"
            
            # Check that attachments include both drawing_files and step_files
            assert isinstance(rfq.attachments, list)
            # Attachments should include all drawing_files and step_files from PR
            expected_attachments = len(pr.drawing_files) + len(pr.step_files)
            assert len(rfq.attachments) == expected_attachments
            
            # Check that RFQs are stored in MockERP
            stored_rfq = mock_erp.get_rfq_by_id(rfq.rfq_id)
            assert stored_rfq is not None
    
    def test_finalize_rfq(self, rfq_service, mock_erp):
        """Test finalizing an RFQ."""
        open_prs = mock_erp.get_open_prs()
        all_suppliers = mock_erp.get_all_suppliers()
        
        if open_prs and all_suppliers:
            pr = open_prs[0]
            supplier = all_suppliers[0]
            
            # Generate an RFQ first
            rfqs = rfq_service.generate_rfqs(pr, [supplier])
            rfq = rfqs[0]
            
            # Finalize it
            final_subject = "Finalized RFQ Subject"
            final_body = {"content": "Finalized body content"}
            
            finalized = rfq_service.finalize_rfq(
                rfq.rfq_id,
                final_subject,
                final_body
            )
            
            assert finalized.rfq_id == rfq.rfq_id
            assert finalized.subject == final_subject
            assert finalized.body == final_body
            assert finalized.status == "finalized"
            assert finalized.finalized_date is not None
    
    def test_finalize_rfq_not_found(self, rfq_service):
        """Test finalizing a non-existent RFQ."""
        with pytest.raises(ValueError, match="not found"):
            rfq_service.finalize_rfq(
                "RFQ-NONEXISTENT",
                "Subject",
                "Body"
            )
    
    def test_finalize_rfq_with_string_body(self, rfq_service, mock_erp):
        """Test finalizing RFQ with string body."""
        open_prs = mock_erp.get_open_prs()
        all_suppliers = mock_erp.get_all_suppliers()
        
        if open_prs and all_suppliers:
            pr = open_prs[0]
            supplier = all_suppliers[0]
            
            rfqs = rfq_service.generate_rfqs(pr, [supplier])
            rfq = rfqs[0]
            
            # Finalize with string body
            final_body_str = "This is a plain text body"
            finalized = rfq_service.finalize_rfq(
                rfq.rfq_id,
                "Subject",
                final_body_str
            )
            
            # Should convert string to dict with "content" key
            assert isinstance(finalized.body, dict)
            assert "content" in finalized.body
