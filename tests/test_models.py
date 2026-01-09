"""Tests for data models."""
import pytest
from datetime import datetime
from app.models.pr import PurchaseRequisition
from app.models.supplier import Supplier
from app.models.rfq import RFQ


class TestPurchaseRequisition:
    """Tests for PurchaseRequisition model."""
    
    def test_pr_creation(self):
        """Test creating a Purchase Requisition."""
        pr = PurchaseRequisition(
            pr_id="PR-TEST-001",
            material="MAT-TEST",
            specs={"type": "test", "grade": "A"},
            drawing_files=["test.pdf"],
            quantities=50,
            unit="pcs",
            description="Test PR",
            status="open"
        )
        
        assert pr.pr_id == "PR-TEST-001"
        assert pr.material == "MAT-TEST"
        assert pr.quantities == 50
        assert pr.unit == "pcs"
        assert pr.status == "open"
        assert len(pr.drawing_files) == 1
        assert isinstance(pr.created_date, datetime)
    
    def test_pr_to_dict(self):
        """Test converting PR to dictionary."""
        pr = PurchaseRequisition(
            pr_id="PR-TEST-002",
            material="MAT-TEST-2",
            specs={"type": "test"},
            quantities=100,
            unit="pcs"
        )
        
        pr_dict = pr.to_dict()
        
        assert pr_dict["pr_id"] == "PR-TEST-002"
        assert pr_dict["material"] == "MAT-TEST-2"
        assert pr_dict["quantities"] == 100
        assert "created_date" in pr_dict
        assert isinstance(pr_dict["created_date"], str)  # ISO format string


class TestSupplier:
    """Tests for Supplier model."""
    
    def test_supplier_creation(self):
        """Test creating a Supplier."""
        supplier = Supplier(
            supplier_id="SUP-TEST-001",
            name="Test Supplier",
            email="test@supplier.com",
            capabilities=["Steel", "Aluminum"],
            standard_for_materials=["MAT-001"]
        )
        
        assert supplier.supplier_id == "SUP-TEST-001"
        assert supplier.name == "Test Supplier"
        assert supplier.email == "test@supplier.com"
        assert len(supplier.capabilities) == 2
        assert "MAT-001" in supplier.standard_for_materials
    
    def test_supplier_to_dict(self):
        """Test converting Supplier to dictionary."""
        supplier = Supplier(
            supplier_id="SUP-TEST-002",
            name="Test Supplier 2",
            email="test2@supplier.com"
        )
        
        supplier_dict = supplier.to_dict()
        
        assert supplier_dict["supplier_id"] == "SUP-TEST-002"
        assert supplier_dict["name"] == "Test Supplier 2"
        assert supplier_dict["email"] == "test2@supplier.com"


class TestRFQ:
    """Tests for RFQ model."""
    
    def test_rfq_creation(self):
        """Test creating an RFQ."""
        rfq = RFQ(
            rfq_id="RFQ-TEST-001",
            supplier_id="SUP-001",
            pr_id="PR-001",
            subject="Test RFQ",
            body={"greeting": "Hello", "content": "Test"}
        )
        
        assert rfq.rfq_id == "RFQ-TEST-001"
        assert rfq.supplier_id == "SUP-001"
        assert rfq.pr_id == "PR-001"
        assert rfq.subject == "Test RFQ"
        assert rfq.status == "draft"
        assert isinstance(rfq.created_date, datetime)
        assert rfq.finalized_date is None
    
    def test_rfq_to_dict(self):
        """Test converting RFQ to dictionary."""
        rfq = RFQ(
            rfq_id="RFQ-TEST-002",
            supplier_id="SUP-002",
            pr_id="PR-002",
            subject="Test RFQ 2",
            body={"content": "Test"}
        )
        
        rfq_dict = rfq.to_dict()
        
        assert rfq_dict["rfq_id"] == "RFQ-TEST-002"
        assert rfq_dict["status"] == "draft"
        assert "created_date" in rfq_dict
        assert rfq_dict["finalized_date"] is None
