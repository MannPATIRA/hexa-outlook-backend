"""Email processing API endpoints."""
from fastapi import APIRouter, HTTPException
from typing import Optional
from ...services.email_classification_service import EmailClassificationService
from ...services.clarification_service import ClarificationService
from ...services.quote_extraction_service import QuoteExtractionService
from ...services.quote_store import QuoteStore
from ...services.mock_erp import MockERP
from ...llm.classifier import LLMClassifier
from ..schemas.email_schemas import (
    EmailClassifyRequest,
    EmailClassifyResponse,
    EmailProcessRequest,
    EmailProcessResponse,
    SuggestResponseRequest,
    SuggestResponseResponse,
    ForwardToEngineeringRequest,
    ForwardToEngineeringResponse,
    EngineerResponseRequest,
    EngineerResponseResponse,
    ExtractQuoteRequest,
    ExtractQuoteResponse,
)

router = APIRouter()

# Initialize services (in production, this would be dependency injected)
mock_erp = MockERP()
llm_classifier = LLMClassifier()
quote_store = QuoteStore()
email_classification_service = EmailClassificationService(llm_classifier)
clarification_service = ClarificationService(llm_classifier, mock_erp)
quote_extraction_service = QuoteExtractionService(quote_store, llm_classifier, mock_erp)


@router.post("/classify", response_model=EmailClassifyResponse)
async def classify_email(request: EmailClassifyRequest):
    """
    Classify an email as quote or clarification request.
    
    Takes email chain and most recent reply, uses LLM to classify,
    and returns classification with confidence score.
    """
    try:
        most_recent = request.most_recent_reply
        
        # Convert email chain to list of dicts
        email_chain = [
            {
                "subject": msg.subject,
                "body": msg.body,
                "from": msg.from_email,
                "date": msg.date
            }
            for msg in request.email_chain
        ]
        
        # Classify the email
        classification = email_classification_service.classify_email(
            rfq_id=request.rfq_id,
            supplier_id=request.supplier_id,
            subject=most_recent.subject,
            body=most_recent.body,
            from_email=most_recent.from_email,
            email_chain=email_chain
        )
        
        return EmailClassifyResponse(
            email_id=classification.email_id,
            classification=classification.classification,
            confidence=classification.confidence or 0.5,
            message=f"Email classified as {classification.classification}"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error classifying email: {str(e)}"
        )


@router.post("/process", response_model=EmailProcessResponse)
async def process_email(request: EmailProcessRequest):
    """
    Process an email when user clicks to address it.
    
    For clarification requests, sub-classifies as engineering or procurement
    and generates suggested response if procurement.
    """
    try:
        # Get the email classification
        email_classification = email_classification_service.get_classification_by_id(request.email_id)
        if not email_classification:
            raise HTTPException(
                status_code=404,
                detail=f"Email {request.email_id} not found"
            )
        
        if request.classification != email_classification.classification:
            raise HTTPException(
                status_code=400,
                detail=f"Classification mismatch. Expected {email_classification.classification}"
            )
        
        if request.classification == "clarification_request":
            # Extract question from email body (simplified - in production, use LLM)
            # For now, use first few sentences or a reasonable chunk
            body_text = email_classification.body.strip()
            # Try to find question markers or use first paragraph
            if "?" in body_text:
                question = body_text.split("?")[0] + "?"
            else:
                # Use first 200 characters or first sentence
                question = body_text[:200] if len(body_text) > 200 else body_text
                if "." in question:
                    question = question.split(".")[0] + "."
            
            # Classify clarification type
            clarification = clarification_service.classify_clarification(
                email_id=request.email_id,
                rfq_id=email_classification.rfq_id,
                supplier_id=email_classification.supplier_id,
                question=question,
                email_body=email_classification.body
            )
            
            # Generate suggested response if procurement
            suggested_response = None
            if clarification.type == "procurement":
                suggested_response = clarification_service.generate_suggested_response(
                    clarification.clarification_id,
                    clarification.question
                )
            
            return EmailProcessResponse(
                email_id=request.email_id,
                sub_classification=clarification.type,
                question=clarification.question,
                suggested_response=suggested_response,
                requires_engineering=(clarification.type == "engineering"),
                message="Clarification processed successfully",
                clarification_id=clarification.clarification_id
            )
        
        elif request.classification == "quote":
            # For quotes, just return basic info
            return EmailProcessResponse(
                email_id=request.email_id,
                message="Quote email ready for extraction"
            )
        
        elif request.classification == "engineer_response":
            # For engineer responses, return info for draft generation
            return EmailProcessResponse(
                email_id=request.email_id,
                message="Engineer response ready for processing"
            )
        
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported classification: {request.classification}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing email: {str(e)}"
        )


@router.post("/suggest-response", response_model=SuggestResponseResponse)
async def suggest_response(request: SuggestResponseRequest):
    """
    Get suggested response for a procurement clarification.
    """
    try:
        clarification = clarification_service.get_clarification_by_id(request.clarification_id)
        if not clarification:
            raise HTTPException(
                status_code=404,
                detail=f"Clarification {request.clarification_id} not found"
            )
        
        # Get email classification for subject
        email_classification = email_classification_service.get_classification_by_id(request.email_id)
        if not email_classification:
            raise HTTPException(
                status_code=404,
                detail=f"Email {request.email_id} not found"
            )
        
        # Generate suggested response
        suggested_response = clarification_service.generate_suggested_response(
            request.clarification_id,
            request.question
        )
        
        # Generate draft subject
        draft_subject = f"Re: {email_classification.subject}"
        
        return SuggestResponseResponse(
            suggested_response=suggested_response,
            draft_subject=draft_subject
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating suggested response: {str(e)}"
        )


@router.post("/forward-to-engineering", response_model=ForwardToEngineeringResponse)
async def forward_to_engineering(request: ForwardToEngineeringRequest):
    """
    Mark a clarification as forwarded to engineering team.
    """
    try:
        clarification = clarification_service.get_clarification_by_id(request.clarification_id)
        if not clarification:
            raise HTTPException(
                status_code=404,
                detail=f"Clarification {request.clarification_id} not found"
            )
        
        # Update status
        clarification_service.update_clarification_status(
            request.clarification_id,
            "sent_to_engineering"
        )
        
        # Update email status
        email_classification_service.update_classification_status(
            request.email_id,
            "processed"
        )
        
        return ForwardToEngineeringResponse(
            status="sent_to_engineering",
            message="Clarification forwarded to engineering team"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error forwarding to engineering: {str(e)}"
        )


@router.post("/process-engineer-response", response_model=EngineerResponseResponse)
async def process_engineer_response(request: EngineerResponseRequest):
    """
    Process an engineer response email and generate draft response to supplier.
    """
    try:
        # Get email classification
        email_classification = email_classification_service.get_classification_by_id(request.email_id)
        if not email_classification:
            raise HTTPException(
                status_code=404,
                detail=f"Email {request.email_id} not found"
            )
        
        # Get clarification if exists
        clarification = clarification_service.get_clarification_by_email_id(request.email_id)
        
        engineer_response_body = request.engineer_response.get("body", "")
        
        # Generate draft response incorporating engineer's response
        draft_body = f"""Dear Supplier,

Thank you for your clarification request regarding RFQ {email_classification.rfq_id}.

Based on our engineering team's review:

{engineer_response_body}

Please let us know if you need any additional information.

Best regards,
Procurement Team"""
        
        return EngineerResponseResponse(
            draft_response={
                "subject": f"Re: {email_classification.subject}",
                "body": draft_body,
                "to": email_classification.from_email
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing engineer response: {str(e)}"
        )


@router.post("/extract-quote", response_model=ExtractQuoteResponse)
async def extract_quote(request: ExtractQuoteRequest):
    """
    Extract and store quote details from an email.
    """
    try:
        # Extract quote details
        quote = quote_extraction_service.extract_and_store_quote(
            email_id=request.email_id,
            rfq_id=request.rfq_id,
            supplier_id=request.supplier_id,
            email_body=request.email_body
        )
        
        # Update email classification status
        email_classification_service.update_classification_status(
            request.email_id,
            "processed"
        )
        
        return ExtractQuoteResponse(
            quote_id=quote.quote_id,
            extracted_details=quote.extracted_details,
            status=quote.status
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error extracting quote: {str(e)}"
        )
