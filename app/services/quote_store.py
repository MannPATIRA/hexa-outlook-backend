from typing import List, Dict, Optional
from ..models.quote import Quote


class QuoteStore:
    """Store for managing quotes."""
    
    def __init__(self):
        self._quotes: Dict[str, Quote] = {}
    
    def store_quote(self, quote: Quote) -> None:
        """Store a quote."""
        self._quotes[quote.quote_id] = quote
    
    def get_quote_by_id(self, quote_id: str) -> Optional[Quote]:
        """Get a quote by its ID."""
        return self._quotes.get(quote_id)
    
    def get_quotes_by_rfq(self, rfq_id: str) -> List[Quote]:
        """Get all quotes for a specific RFQ."""
        return [quote for quote in self._quotes.values() if quote.rfq_id == rfq_id]
    
    def get_quotes_by_supplier(self, supplier_id: str) -> List[Quote]:
        """Get all quotes from a specific supplier."""
        return [quote for quote in self._quotes.values() if quote.supplier_id == supplier_id]
    
    def update_quote_status(self, quote_id: str, status: str) -> None:
        """Update the status of a quote."""
        if quote_id in self._quotes:
            self._quotes[quote_id].status = status
    
    def get_all_quotes(self) -> List[Quote]:
        """Get all quotes."""
        return list(self._quotes.values())
