"""LLM integration for email classification and quote extraction."""
import os
import json
from typing import Dict, Any, Optional, List
import logging
from pathlib import Path
from openai import OpenAI

# Load environment variables
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

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
        self._client = None
        
        if self._use_mock:
            logger.warning("No OpenAI API key found. Using mock LLM responses.")
        else:
            self._client = OpenAI(api_key=self.api_key)
            logger.info("OpenAI client initialized successfully.")
    
    def _call_openai(self, system_prompt: str, user_prompt: str, response_format: Optional[Dict] = None) -> str:
        """
        Make an OpenAI API call.
        
        Args:
            system_prompt: System prompt for the model
            user_prompt: User prompt/content
            response_format: Optional response format (for JSON mode)
            
        Returns:
            The model's response text
        """
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            kwargs = {
                "model": "gpt-4o-mini",
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 2000
            }
            
            if response_format:
                kwargs["response_format"] = response_format
            
            response = self._client.chat.completions.create(**kwargs)
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
    
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
        
        system_prompt = """You are an email classification assistant for a procurement system.
Your task is to classify incoming emails related to Request for Quotation (RFQ) processes.

Classify the email into ONE of these categories:
1. "quote" - The email contains a price quote or quotation from a supplier. Look for prices, delivery terms, validity periods, etc.
2. "clarification_request" - The supplier is asking questions or seeking clarification about the RFQ. Look for questions, requests for more information, or clarifications needed.
3. "engineer_response" - An internal engineering team response to a technical question. Usually from internal email domains or engineering departments.

Respond in JSON format with these fields:
- classification: One of "quote", "clarification_request", or "engineer_response"
- confidence: A number between 0 and 1 indicating your confidence
- reasoning: A brief explanation of why you chose this classification"""

        chain_context = ""
        if email_chain:
            chain_context = "\n\nPrevious email chain context:\n"
            for msg in email_chain[-3:]:  # Last 3 messages for context
                chain_context += f"From: {msg.get('from', 'Unknown')}\nSubject: {msg.get('subject', '')}\n{msg.get('body', '')[:500]}\n---\n"

        user_prompt = f"""Classify this email:

Subject: {email_subject}

Body:
{email_body}
{chain_context}

Respond with JSON only."""

        try:
            response = self._call_openai(
                system_prompt, 
                user_prompt, 
                response_format={"type": "json_object"}
            )
            result = json.loads(response)
            
            # Ensure required fields exist
            if "classification" not in result:
                result["classification"] = "clarification_request"
            if "confidence" not in result:
                result["confidence"] = 0.7
            if "reasoning" not in result:
                result["reasoning"] = "Classified by LLM"
                
            return result
        except Exception as e:
            logger.error(f"Error in classify_email: {str(e)}")
            # Fallback to mock if API fails
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
        
        system_prompt = """You are a procurement assistant helping to route clarification requests.

Classify the clarification question into ONE of these categories:
1. "engineering" - Technical questions requiring engineering expertise:
   - Material specifications, grades, or alternatives
   - Technical drawings or dimensions
   - Tolerances or quality requirements
   - Design specifications
   - Performance requirements
   
2. "procurement" - Commercial/logistics questions that procurement can answer:
   - Delivery addresses or schedules
   - Payment terms
   - Quantities or packaging
   - Shipping requirements
   - Lead times
   - Purchase order details

Respond in JSON format with these fields:
- type: Either "engineering" or "procurement"
- confidence: A number between 0 and 1 indicating your confidence
- reasoning: A brief explanation of why you chose this classification"""

        user_prompt = f"""Classify this clarification request:

Question: {question}

Full email context:
{email_body}

Respond with JSON only."""

        try:
            response = self._call_openai(
                system_prompt, 
                user_prompt,
                response_format={"type": "json_object"}
            )
            result = json.loads(response)
            
            # Ensure required fields exist
            if "type" not in result:
                result["type"] = "procurement"
            if "confidence" not in result:
                result["confidence"] = 0.7
            if "reasoning" not in result:
                result["reasoning"] = "Classified by LLM"
                
            return result
        except Exception as e:
            logger.error(f"Error in classify_clarification: {str(e)}")
            return self._mock_classify_clarification(question, email_body)
    
    def extract_questions(self, email_body: str) -> List[str]:
        """
        Extract all questions/clarification requests from an email body.
        
        Args:
            email_body: Email body text
            
        Returns:
            List of extracted questions
        """
        if self._use_mock:
            return self._mock_extract_questions(email_body)
        
        system_prompt = """You are an email analysis assistant. Your task is to extract all questions or clarification requests from an email.

Extract each distinct question or request for information as a separate item.
Be thorough - capture all questions including:
- Direct questions (ending with ?)
- Implicit questions ("Could you please confirm...", "We need to know...")
- Requests for clarification or information

Respond in JSON format with a single field:
- questions: An array of strings, each containing one question or clarification request"""

        user_prompt = f"""Extract all questions and clarification requests from this email:

{email_body}

Respond with JSON only."""

        try:
            response = self._call_openai(
                system_prompt, 
                user_prompt,
                response_format={"type": "json_object"}
            )
            result = json.loads(response)
            
            questions = result.get("questions", [])
            if not questions:
                # If no questions found, return the whole body as context
                return [email_body.strip()[:500]]
            return questions
        except Exception as e:
            logger.error(f"Error in extract_questions: {str(e)}")
            return self._mock_extract_questions(email_body)
    
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
        
        system_prompt = """You are a procurement professional drafting professional email responses to supplier inquiries.

Generate a clear, professional, and helpful response to the supplier's question.
Keep the response:
- Professional and courteous
- Clear and specific
- Helpful with actionable information where possible
- Well-structured with proper greeting and closing

If specific information is not available, indicate where the user should fill in details."""

        context_str = json.dumps(rfq_context, indent=2)
        
        user_prompt = f"""Generate a professional response to this supplier question:

Question: {question}

RFQ Context:
{context_str}

Write a complete email response."""

        try:
            response = self._call_openai(system_prompt, user_prompt)
            return response.strip()
        except Exception as e:
            logger.error(f"Error in generate_response: {str(e)}")
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
        
        system_prompt = """You are a quote extraction assistant for a procurement system.

Extract all relevant quote information from the email. Look for:
- Price/cost information (unit price, total price)
- Currency (USD, EUR, etc.)
- Delivery time/lead time
- Quote validity period
- Payment terms
- Quantity offered
- Material specifications
- Any terms and conditions

Respond in JSON format with these fields (use null if not found):
- price: The numeric price value (just the number, no currency symbol)
- currency: The currency code (e.g., "USD", "EUR")
- unit_price: Price per unit if specified
- quantity: Quantity being quoted
- delivery_time: Delivery or lead time as stated
- validity: Quote validity period
- payment_terms: Payment terms if specified
- terms: Any additional terms and conditions
- notes: Any other relevant information extracted"""

        user_prompt = f"""Extract quote details from this email:

{email_body}

Respond with JSON only."""

        try:
            response = self._call_openai(
                system_prompt, 
                user_prompt,
                response_format={"type": "json_object"}
            )
            result = json.loads(response)
            
            # Ensure we have the expected structure
            extracted = {
                "price": result.get("price"),
                "currency": result.get("currency", "USD"),
                "unit_price": result.get("unit_price"),
                "quantity": result.get("quantity"),
                "delivery_time": result.get("delivery_time", "To be confirmed"),
                "validity": result.get("validity", "30 days"),
                "payment_terms": result.get("payment_terms"),
                "terms": result.get("terms", "Standard terms and conditions apply"),
                "notes": result.get("notes")
            }
            
            return extracted
        except Exception as e:
            logger.error(f"Error in extract_quote_details: {str(e)}")
            return self._mock_extract_quote_details(email_body)
    
    def _mock_extract_questions(self, email_body: str) -> List[str]:
        """Mock question extraction."""
        questions = []
        
        # Split by common question patterns
        sentences = email_body.replace('\n', ' ').split('.')
        for sentence in sentences:
            sentence = sentence.strip()
            if '?' in sentence:
                # Find the question part
                parts = sentence.split('?')
                for part in parts[:-1]:  # All except the last empty part
                    q = part.strip()
                    if q and len(q) > 10:
                        questions.append(q + "?")
            elif any(keyword in sentence.lower() for keyword in 
                    ["could you", "can you", "please confirm", "need to know", 
                     "clarify", "requesting", "require"]):
                if len(sentence) > 10:
                    questions.append(sentence + ".")
        
        if not questions:
            # Return first meaningful chunk if no questions found
            return [email_body.strip()[:300]]
        
        return questions
    
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
