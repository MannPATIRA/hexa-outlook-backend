"""LLM integration for email classification and quote extraction."""
import os
import json
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class LLMClassifier:
    """LLM-based classifier for emails and quote extraction."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize LLM classifier.
        
        Args:
            api_key: OpenAI API key (or set OPENAI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self._use_mock = self.api_key is None
        
        if self._use_mock:
            logger.warning("No OpenAI API key found. Using mock LLM responses.")
    
    def classify_email(self, email_subject: str, email_body: str, email_chain: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Classify an email as quote or clarification request.
        
        Args:
            email_subject: Email subject
            email_body: Email body content
            email_chain: Optional email chain context
            
        Returns:
            Dict with classification, confidence, and reasoning
        """
        if self._use_mock:
            return self._mock_classify_email(email_subject, email_body)
        
        # TODO: Implement actual OpenAI API call
        # For now, return mock response
        return self._mock_classify_email(email_subject, email_body)
    
    def classify_clarification(self, question: str, email_body: str) -> Dict[str, Any]:
        """
        Classify a clarification request as engineering or procurement.
        
        Args:
            question: The clarification question
            email_body: Full email body for context
            
        Returns:
            Dict with type (engineering/procurement) and reasoning
        """
        if self._use_mock:
            return self._mock_classify_clarification(question, email_body)
        
        # TODO: Implement actual OpenAI API call
        return self._mock_classify_clarification(question, email_body)
    
    def generate_response(self, question: str, rfq_context: Dict[str, Any]) -> str:
        """
        Generate a suggested response for a procurement clarification.
        
        Args:
            question: The clarification question
            rfq_context: Context about the RFQ (material, specs, etc.)
            
        Returns:
            Suggested response text
        """
        if self._use_mock:
            return self._mock_generate_response(question, rfq_context)
        
        # TODO: Implement actual OpenAI API call
        return self._mock_generate_response(question, rfq_context)
    
    def extract_quote_details(self, email_body: str) -> Dict[str, Any]:
        """
        Extract structured quote details from email body.
        
        Args:
            email_body: Email body containing quote information
            
        Returns:
            Dict with extracted quote details (price, delivery_time, etc.)
        """
        if self._use_mock:
            return self._mock_extract_quote_details(email_body)
        
        # TODO: Implement actual OpenAI API call
        return self._mock_extract_quote_details(email_body)
    
    def _mock_classify_email(self, subject: str, body: str) -> Dict[str, Any]:
        """Mock email classification."""
        body_lower = body.lower()
        subject_lower = subject.lower()
        
        # Simple keyword-based classification
        quote_keywords = ["quote", "quotation", "pricing", "price", "cost", "usd", "eur", "delivery", "valid until"]
        clarification_keywords = ["question", "clarify", "confirm", "need", "require", "specification", "material"]
        engineer_keywords = ["engineer", "engineering", "technical", "review", "approved", "alternative material"]
        
        quote_score = sum(1 for keyword in quote_keywords if keyword in body_lower or keyword in subject_lower)
        clarification_score = sum(1 for keyword in clarification_keywords if keyword in body_lower or keyword in subject_lower)
        engineer_score = sum(1 for keyword in engineer_keywords if keyword in body_lower or keyword in subject_lower)
        
        # Check for engineer response (usually from internal email)
        if engineer_score > 2 and ("@company.com" in body or "engineering" in subject_lower):
            classification = "engineer_response"
            confidence = min(0.95, 0.7 + (engineer_score * 0.05))
        elif quote_score > clarification_score and quote_score > 0:
            classification = "quote"
            confidence = min(0.95, 0.6 + (quote_score * 0.1))
        elif clarification_score > 0:
            classification = "clarification_request"
            confidence = min(0.95, 0.6 + (clarification_score * 0.1))
        else:
            # Default to clarification if unclear
            classification = "clarification_request"
            confidence = 0.5
        
        return {
            "classification": classification,
            "confidence": confidence,
            "reasoning": f"Classified based on keyword analysis"
        }
    
    def _mock_classify_clarification(self, question: str, email_body: str) -> Dict[str, Any]:
        """Mock clarification sub-classification."""
        question_lower = question.lower()
        body_lower = email_body.lower()
        text = question_lower + " " + body_lower
        
        # Engineering keywords
        engineering_keywords = [
            "material", "specification", "spec", "tolerance", "dimension", "grade",
            "technical", "engineering", "design", "drawing", "alternative", "substitute"
        ]
        
        # Procurement keywords
        procurement_keywords = [
            "delivery", "address", "shipping", "payment", "terms", "quantity",
            "timeline", "schedule", "lead time", "purchase order", "po"
        ]
        
        engineering_score = sum(1 for keyword in engineering_keywords if keyword in text)
        procurement_score = sum(1 for keyword in procurement_keywords if keyword in text)
        
        if engineering_score > procurement_score:
            clarification_type = "engineering"
            confidence = min(0.95, 0.7 + (engineering_score * 0.05))
        else:
            clarification_type = "procurement"
            confidence = min(0.95, 0.7 + (procurement_score * 0.05))
        
        return {
            "type": clarification_type,
            "confidence": confidence,
            "reasoning": f"Classified as {clarification_type} based on keyword analysis"
        }
    
    def _mock_generate_response(self, question: str, rfq_context: Dict[str, Any]) -> str:
        """Mock response generation."""
        question_lower = question.lower()
        
        # Simple template-based responses
        if "delivery" in question_lower or "address" in question_lower:
            return f"""Dear Supplier,

Thank you for your inquiry regarding the delivery address for RFQ {rfq_context.get('rfq_id', 'RFQ-001')}.

Our delivery address is:
[Company Address]
[City, State ZIP]
[Country]

Please ensure all deliveries are coordinated with our receiving department. If you have any further questions, please don't hesitate to contact us.

Best regards,
Procurement Team"""
        
        elif "payment" in question_lower or "terms" in question_lower:
            return f"""Dear Supplier,

Thank you for your question about payment terms for RFQ {rfq_context.get('rfq_id', 'RFQ-001')}.

Our standard payment terms are Net 30 days upon receipt of goods and invoice. Payment will be made via [payment method].

If you require different terms, please let us know and we can discuss.

Best regards,
Procurement Team"""
        
        else:
            return f"""Dear Supplier,

Thank you for your clarification request regarding RFQ {rfq_context.get('rfq_id', 'RFQ-001')}.

{question}

[Please provide a detailed response based on the RFQ requirements]

If you need any additional information, please don't hesitate to ask.

Best regards,
Procurement Team"""
    
    def _mock_extract_quote_details(self, email_body: str) -> Dict[str, Any]:
        """Mock quote extraction."""
        body_lower = email_body.lower()
        
        # Simple extraction patterns
        extracted = {}
        
        # Try to extract price
        import re
        price_patterns = [
            r'\$[\d,]+\.?\d*',
            r'usd\s*[\d,]+\.?\d*',
            r'eur\s*[\d,]+\.?\d*',
            r'price[:\s]+[\d,]+\.?\d*',
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, body_lower)
            if match:
                price_str = match.group(0).replace('$', '').replace(',', '').replace('usd', '').replace('eur', '').strip()
                try:
                    extracted['price'] = float(price_str)
                    extracted['currency'] = 'USD' if '$' in match.group(0) or 'usd' in match.group(0).lower() else 'EUR'
                    break
                except ValueError:
                    pass
        
        # Try to extract delivery time
        delivery_patterns = [
            r'(\d+)\s*(?:weeks?|wks?)',
            r'(\d+)\s*(?:days?|d)',
            r'(\d+)\s*(?:months?|mos?)',
            r'delivery[:\s]+(\d+)',
        ]
        
        for pattern in delivery_patterns:
            match = re.search(pattern, body_lower)
            if match:
                extracted['delivery_time'] = match.group(0)
                break
        
        # Try to extract validity
        validity_patterns = [
            r'valid[:\s]+(\d+)',
            r'validity[:\s]+(\d+)',
            r'quote valid[:\s]+(\d+)',
        ]
        
        for pattern in validity_patterns:
            match = re.search(pattern, body_lower)
            if match:
                extracted['validity'] = f"{match.group(1)} days"
                break
        
        # Default values if not found
        if 'price' not in extracted:
            extracted['price'] = None
        if 'currency' not in extracted:
            extracted['currency'] = 'USD'
        if 'delivery_time' not in extracted:
            extracted['delivery_time'] = "To be confirmed"
        if 'validity' not in extracted:
            extracted['validity'] = "30 days"
        
        extracted['terms'] = "Standard terms and conditions apply"
        
        return extracted
