from typing import List, Optional, Dict, Any
from datetime import datetime
from ..models.pr import PurchaseRequisition
from ..models.supplier import Supplier
from ..models.rfq import RFQ


class MockERP:
    """Mock ERP system simulating SAP ERP with PRs and suppliers."""
    
    def __init__(self):
        self._prs: Dict[str, PurchaseRequisition] = {}
        self._suppliers: Dict[str, Supplier] = {}
        self._rfqs: Dict[str, RFQ] = {}
        self._initialize_sample_data()
    
    def _initialize_sample_data(self):
        """Initialize with sample PRs and suppliers."""
        
        # Sample Purchase Requisitions
        prs = [
            PurchaseRequisition(
                pr_id="PR-001",
                material="MAT-12345",
                specs={
                    "material_type": "Steel Component",
                    "grade": "SS304",
                    "dimensions": "100mm x 50mm x 25mm",
                    "tolerance": "±0.1mm",
                    "surface_finish": "Ra 1.6",
                    "weight": "2.5 kg"
                },
                drawing_files=["drawing_PR001_main.pdf", "drawing_PR001_detail.dwg"],
                step_files=["model_PR001.step", "assembly_PR001.step"],
                quantities=100,
                unit="pcs",
                description="Steel bracket for assembly line",
                status="open",
                created_date=datetime(2024, 1, 15, 10, 30)
            ),
            PurchaseRequisition(
                pr_id="PR-002",
                material="MAT-67890",
                specs={
                    "material_type": "Aluminum Housing",
                    "grade": "6061-T6",
                    "dimensions": "200mm x 150mm x 100mm",
                    "tolerance": "±0.2mm",
                    "surface_finish": "Anodized",
                    "weight": "1.8 kg"
                },
                drawing_files=["drawing_PR002_housing.pdf"],
                step_files=["model_PR002.step"],
                quantities=50,
                unit="pcs",
                description="Aluminum housing for electronic enclosure",
                status="open",
                created_date=datetime(2024, 1, 20, 14, 15)
            ),
            PurchaseRequisition(
                pr_id="PR-003",
                material="MAT-11111",
                specs={
                    "material_type": "Plastic Injection Molded Part",
                    "material": "ABS",
                    "dimensions": "75mm x 50mm x 30mm",
                    "tolerance": "±0.15mm",
                    "color": "Black",
                    "weight": "0.3 kg"
                },
                drawing_files=["drawing_PR003_plastic.pdf", "drawing_PR003_mold.dwg"],
                step_files=["model_PR003.step", "mold_PR003.step"],
                quantities=200,
                unit="pcs",
                description="Plastic cover for control panel",
                status="open",
                created_date=datetime(2024, 1, 22, 9, 0)
            ),
        ]
        
        for pr in prs:
            self._prs[pr.pr_id] = pr
        
        # Sample Suppliers
        suppliers = [
            Supplier(
                supplier_id="SUP-001",
                name="ABC Manufacturing",
                email="supplier-hexa@outlook.com",
                capabilities=["Steel Components", "Machining", "Welding", "SS304"],
                standard_for_materials=["MAT-12345", "MAT-99999"],
                contact_person="John Smith",
                phone="+1-555-0101"
            ),
            Supplier(
                supplier_id="SUP-002",
                name="XYZ Metalworks",
                email="supplier-hexa@outlook.com",
                capabilities=["Steel Components", "Aluminum Components", "SS304", "6061-T6"],
                standard_for_materials=["MAT-12345", "MAT-67890"],
                contact_person="Sarah Johnson",
                phone="+1-555-0102"
            ),
            Supplier(
                supplier_id="SUP-003",
                name="Precision Plastics Inc",
                email="supplier-hexa@outlook.com",
                capabilities=["Plastic Injection Molding", "ABS", "Polycarbonate"],
                standard_for_materials=["MAT-11111"],
                contact_person="Mike Davis",
                phone="+1-555-0103"
            ),
            Supplier(
                supplier_id="SUP-004",
                name="Global Components Ltd",
                email="supplier-hexa@outlook.com",
                capabilities=["Steel Components", "Aluminum Components", "Plastic Molding"],
                standard_for_materials=[],
                contact_person="Lisa Chen",
                phone="+1-555-0104"
            ),
        ]
        
        for supplier in suppliers:
            self._suppliers[supplier.supplier_id] = supplier
    
    def get_open_prs(self) -> List[PurchaseRequisition]:
        """Get all open purchase requisitions."""
        return [pr for pr in self._prs.values() if pr.status == "open"]
    
    def get_pr_by_id(self, pr_id: str) -> Optional[PurchaseRequisition]:
        """Get a PR by its ID."""
        return self._prs.get(pr_id)
    
    def get_suppliers_by_material(self, material: str) -> List[Supplier]:
        """Get suppliers that are standard suppliers for a given material."""
        return [
            supplier for supplier in self._suppliers.values()
            if material in supplier.standard_for_materials
        ]
    
    def get_suppliers_by_specs(self, specs: Dict[str, Any]) -> List[Supplier]:
        """Get suppliers that match given specifications."""
        matching_suppliers = []
        
        # Extract key spec attributes for matching
        material_type = specs.get("material_type", "").lower()
        grade = specs.get("grade", "").lower()
        material = specs.get("material", "").lower()
        
        for supplier in self._suppliers.values():
            match_score = 0
            
            # Check capabilities
            for capability in supplier.capabilities:
                cap_lower = capability.lower()
                if material_type and material_type in cap_lower:
                    match_score += 2
                if grade and grade in cap_lower:
                    match_score += 2
                if material and material in cap_lower:
                    match_score += 2
            
            if match_score > 0:
                matching_suppliers.append((supplier, match_score))
        
        # Sort by match score (descending) and return suppliers
        matching_suppliers.sort(key=lambda x: x[1], reverse=True)
        return [supplier for supplier, _ in matching_suppliers]
    
    def get_all_suppliers(self) -> List[Supplier]:
        """Get all suppliers."""
        return list(self._suppliers.values())
    
    def get_supplier_by_id(self, supplier_id: str) -> Optional[Supplier]:
        """Get a supplier by its ID."""
        return self._suppliers.get(supplier_id)
    
    def store_rfq(self, rfq: RFQ):
        """Store an RFQ for tracking."""
        self._rfqs[rfq.rfq_id] = rfq
    
    def get_rfq_by_id(self, rfq_id: str) -> Optional[RFQ]:
        """Get an RFQ by its ID."""
        return self._rfqs.get(rfq_id)
    
    def update_rfq_status(self, rfq_id: str, status: str):
        """Update the status of an RFQ."""
        if rfq_id in self._rfqs:
            self._rfqs[rfq_id].status = status
