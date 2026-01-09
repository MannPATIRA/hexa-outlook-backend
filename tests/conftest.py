"""Pytest configuration and fixtures."""
import pytest
from app.services.mock_erp import MockERP
from app.services.pr_service import PRService
from app.services.supplier_service import SupplierService
from app.services.rfq_service import RFQService


@pytest.fixture
def mock_erp():
    """Create a MockERP instance for testing."""
    return MockERP()


@pytest.fixture
def pr_service():
    """Create a PRService instance for testing."""
    return PRService()


@pytest.fixture
def supplier_service(mock_erp):
    """Create a SupplierService instance for testing."""
    return SupplierService(mock_erp)


@pytest.fixture
def rfq_service(mock_erp):
    """Create an RFQService instance for testing."""
    return RFQService(mock_erp)
