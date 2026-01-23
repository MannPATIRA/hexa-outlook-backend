"""Quote retrieval API endpoints."""
from fastapi import APIRouter, HTTPException
from ..schemas.email_schemas import (
    QuoteResponse, 
    QuoteListResponse, 
    QuoteComparisonResponse,
    SupplierRFQInfo
)

router = APIRouter()

# Import shared quote store from emails module
# Using lazy import to avoid circular dependency issues
def get_quote_store():
    """Get the shared quote store instance from emails module."""
    from .emails import quote_store
    return quote_store


def get_mock_erp():
    """Get the MockERP instance."""
    from .rfqs import mock_erp
    return mock_erp


@router.get("/pr/{pr_id}", response_model=QuoteComparisonResponse)
async def get_quotes_by_pr(pr_id: str):
    """
    Get quote comparison for a PR, showing all suppliers that received RFQs
    and which ones have responded.
    
    This endpoint provides a complete view of:
    - All suppliers that were sent RFQs for this PR
    - Which suppliers have provided quotes
    - Which suppliers haven't responded yet
    """
    try:
        mock_erp = get_mock_erp()
        quote_store = get_quote_store()
        
        # Verify PR exists
        pr = mock_erp.get_pr_by_id(pr_id)
        if not pr:
            raise HTTPException(
                status_code=404,
                detail=f"Purchase Requisition {pr_id} not found"
            )
        
        # Get all RFQs for this PR
        rfqs = mock_erp.get_rfqs_by_pr_id(pr_id)
        
        if not rfqs:
            # No RFQs sent yet for this PR
            return QuoteComparisonResponse(
                pr_id=pr_id,
                suppliers_sent_rfq=[],
                quotes_received=[],
                suppliers_without_quotes=[]
            )
        
        # Build supplier RFQ info list
        suppliers_sent_rfq = []
        rfq_ids = []
        supplier_ids_with_rfq = set()
        
        for rfq in rfqs:
            supplier = mock_erp.get_supplier_by_id(rfq.supplier_id)
            suppliers_sent_rfq.append(SupplierRFQInfo(
                supplier_id=rfq.supplier_id,
                supplier_name=supplier.name if supplier else "Unknown Supplier",
                supplier_email=supplier.email if supplier else "",
                rfq_id=rfq.rfq_id,
                rfq_status=rfq.status
            ))
            rfq_ids.append(rfq.rfq_id)
            supplier_ids_with_rfq.add(rfq.supplier_id)
        
        # Get all quotes for all RFQs of this PR
        all_quotes = []
        supplier_ids_with_quotes = set()
        
        for rfq_id in rfq_ids:
            quotes = quote_store.get_quotes_by_rfq(rfq_id)
            for quote in quotes:
                all_quotes.append(QuoteResponse(
                    quote_id=quote.quote_id,
                    supplier_name=quote.supplier_name,
                    price=quote.price,
                    currency=quote.currency,
                    delivery_time=quote.delivery_time,
                    quote_date=quote.quote_date.isoformat(),
                    status=quote.status
                ))
                supplier_ids_with_quotes.add(quote.supplier_id)
        
        # Find suppliers that haven't responded
        suppliers_without_quotes = []
        for supplier_info in suppliers_sent_rfq:
            if supplier_info.supplier_id not in supplier_ids_with_quotes:
                suppliers_without_quotes.append(supplier_info.supplier_name)
        
        return QuoteComparisonResponse(
            pr_id=pr_id,
            suppliers_sent_rfq=suppliers_sent_rfq,
            quotes_received=all_quotes,
            suppliers_without_quotes=suppliers_without_quotes
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving quote comparison: {str(e)}"
        )


@router.get("/{rfq_id}", response_model=QuoteListResponse)
async def get_quotes_by_rfq(rfq_id: str):
    """
    Get all quotes for a specific RFQ.
    """
    try:
        quote_store = get_quote_store()
        quotes = quote_store.get_quotes_by_rfq(rfq_id)
        
        quote_responses = []
        for quote in quotes:
            quote_responses.append(QuoteResponse(
                quote_id=quote.quote_id,
                supplier_name=quote.supplier_name,
                price=quote.price,
                currency=quote.currency,
                delivery_time=quote.delivery_time,
                quote_date=quote.quote_date.isoformat(),
                status=quote.status
            ))
        
        return QuoteListResponse(quotes=quote_responses)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving quotes: {str(e)}"
        )
