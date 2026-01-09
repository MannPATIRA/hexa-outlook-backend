"""Quote retrieval API endpoints."""
from fastapi import APIRouter, HTTPException
from ..schemas.email_schemas import QuoteResponse, QuoteListResponse

router = APIRouter()

# Import shared quote store from emails module
# Using lazy import to avoid circular dependency issues
def get_quote_store():
    """Get the shared quote store instance from emails module."""
    from .emails import quote_store
    return quote_store


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
