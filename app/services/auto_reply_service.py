"""
Service for sending automatic email replies for demo/testing purposes.

This service sends REAL emails via SMTP that will appear as threaded replies
to the original RFQ emails.
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import threading
import time
import random
from typing import Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# Ensure .env is loaded (in case this module is imported before main.py runs)
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


@dataclass
class ScheduledReply:
    """Tracks a scheduled reply."""
    reply_id: str
    to_email: str
    subject: str
    scheduled_time: datetime
    status: str = "pending"


class AutoReplyService:
    """
    Sends actual email replies after a configurable delay.
    
    The emails include proper headers (In-Reply-To, References) so they
    appear as threaded replies in email clients.
    """
    
    def __init__(self):
        # Gmail SMTP settings
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        
        # Track scheduled replies
        self._scheduled_replies: dict = {}
        self._reply_counter = 0
    
    @property
    def sender_email(self) -> str:
        """Get sender email from environment (read each time for hot-reload support)."""
        return os.getenv("DEMO_SUPPLIER_EMAIL", "")
    
    @property
    def sender_password(self) -> str:
        """Get sender password from environment (read each time for hot-reload support)."""
        return os.getenv("DEMO_SUPPLIER_PASSWORD", "")
    
    @property
    def sender_name(self) -> str:
        """Get sender name from environment (read each time for hot-reload support)."""
        return os.getenv("DEMO_SUPPLIER_NAME", "ABC Manufacturing (Demo)")
    
    def is_configured(self) -> bool:
        """Check if SMTP credentials are configured."""
        return bool(self.sender_email and self.sender_password)
    
    def _generate_reply_id(self) -> str:
        self._reply_counter += 1
        return f"AUTO-REPLY-{self._reply_counter:03d}"
    
    def generate_quote_reply(self, material: str, quantity: int = 100) -> str:
        """Generate a realistic quote email body."""
        price = random.randint(35, 75)
        delivery = random.choice(["2-3 weeks", "3-4 weeks", "4-6 weeks"])
        
        return f"""Dear Procurement Team,

Thank you for your Request for Quotation regarding {material}.

We are pleased to provide the following quotation:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QUOTATION DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Item: {material}
Quantity: {quantity} units
Unit Price: ${price}.00 USD
Total Price: ${price * quantity:,}.00 USD

Delivery Time: {delivery} after order confirmation
Payment Terms: Net 30
Validity: This quote is valid for 30 days

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

All items will be manufactured according to your specifications.
Shipping terms: FOB Origin

Please let us know if you would like to proceed or if you have any questions.

Best regards,

{self.sender_name}
Sales Department
Email: {self.sender_email}
"""

    def generate_clarification_reply(self, material: str, clarification_type: str = "procurement") -> str:
        """Generate a clarification request email body."""
        
        if clarification_type == "engineering":
            return f"""Dear Procurement Team,

Thank you for your RFQ regarding {material}.

Before we can provide a formal quotation, our engineering team requires clarification on the following technical specifications:

TECHNICAL QUESTIONS:

1. Tolerance Requirements
   - What are the critical dimension tolerances?
   - Are there any specific GD&T callouts we should be aware of?

2. Material Specifications
   - Please confirm the exact material grade (e.g., ASTM standard)
   - Are there specific hardness requirements?

3. Surface Finish
   - What is the required surface roughness (Ra value)?
   - Are there any coating or plating requirements?

4. Quality & Certification
   - Is material certification required?
   - Are there any specific inspection requirements?

We cannot proceed with an accurate quotation until these details are confirmed.

Please respond at your earliest convenience.

Best regards,

{self.sender_name}
Engineering Department
"""
        else:
            return f"""Dear Procurement Team,

Thank you for your RFQ regarding {material}.

We are interested in providing a quotation, but we need clarification on a few commercial points:

QUESTIONS:

1. What are your preferred payment terms?

2. Is there flexibility on the delivery schedule?

3. What is the shipping destination and preferred Incoterms?

4. Is this a one-time order or part of an ongoing requirement?

5. Are there any approved vendor requirements we should be aware of?

Once we have this information, we will provide a detailed quotation.

Best regards,

{self.sender_name}
Sales Department
"""

    def schedule_reply(
        self,
        to_email: str,
        original_subject: str,
        original_message_id: str,
        material: str,
        reply_type: str = "quote",  # "quote", "clarification_procurement", "clarification_engineering"
        delay_seconds: int = 30,
        quantity: int = 100
    ) -> dict:
        """
        Schedule a real email reply to be sent after the specified delay.
        
        Args:
            to_email: Recipient email (the user's email)
            original_subject: Subject of the original RFQ email
            original_message_id: Message-ID header of the original email (for threading)
            material: Material name for the reply content
            reply_type: Type of reply to generate
            delay_seconds: How long to wait before sending
            quantity: Quantity for quote calculations
            
        Returns:
            Dict with reply_id and status
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "SMTP not configured. Set DEMO_SUPPLIER_EMAIL and DEMO_SUPPLIER_PASSWORD environment variables.",
                "reply_id": None
            }
        
        reply_id = self._generate_reply_id()
        
        # Generate reply content based on type
        if reply_type == "quote":
            body = self.generate_quote_reply(material, quantity)
        elif reply_type == "clarification_engineering":
            body = self.generate_clarification_reply(material, "engineering")
        else:
            body = self.generate_clarification_reply(material, "procurement")
        
        # Track the scheduled reply
        self._scheduled_replies[reply_id] = ScheduledReply(
            reply_id=reply_id,
            to_email=to_email,
            subject=f"RE: {original_subject}",
            scheduled_time=datetime.now()
        )
        
        # Start a background thread to send after delay
        def send_delayed():
            time.sleep(delay_seconds)
            success = self._send_email(
                to_email=to_email,
                subject=f"RE: {original_subject}",
                body=body,
                original_message_id=original_message_id
            )
            self._scheduled_replies[reply_id].status = "sent" if success else "failed"
        
        thread = threading.Thread(target=send_delayed, daemon=True)
        thread.start()
        
        return {
            "success": True,
            "reply_id": reply_id,
            "message": f"Reply scheduled to be sent in {delay_seconds} seconds",
            "to_email": to_email,
            "reply_type": reply_type
        }
    
    def _send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        original_message_id: str
    ) -> bool:
        """
        Send the actual email via SMTP.
        
        Returns True if successful, False otherwise.
        """
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["From"] = f"{self.sender_name} <{self.sender_email}>"
            msg["To"] = to_email
            msg["Subject"] = subject
            
            # These headers make the email thread as a reply!
            if original_message_id:
                msg["In-Reply-To"] = original_message_id
                msg["References"] = original_message_id
            
            # Add plain text body
            msg.attach(MIMEText(body, "plain"))
            
            # Also add HTML version for better formatting
            html_body = f"<pre style='font-family: Arial, sans-serif; white-space: pre-wrap;'>{body}</pre>"
            msg.attach(MIMEText(html_body, "html"))
            
            # Connect and send
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            print(f"✅ Email sent successfully to {to_email}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ SMTP Authentication failed: {e}")
            print("   Make sure you're using an App Password, not your regular password!")
            return False
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False
    
    def get_scheduled_replies(self) -> list:
        """Get all scheduled/sent replies."""
        return [
            {
                "reply_id": r.reply_id,
                "to_email": r.to_email,
                "subject": r.subject,
                "scheduled_time": r.scheduled_time.isoformat(),
                "status": r.status
            }
            for r in self._scheduled_replies.values()
        ]
    
    def test_connection(self) -> dict:
        """Test SMTP connection without sending an email."""
        if not self.is_configured():
            return {
                "success": False,
                "error": "Not configured. Set DEMO_SUPPLIER_EMAIL and DEMO_SUPPLIER_PASSWORD."
            }
        
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)
            
            return {
                "success": True,
                "message": "SMTP connection successful!",
                "sender_email": self.sender_email
            }
        except smtplib.SMTPAuthenticationError:
            return {
                "success": False,
                "error": "Authentication failed. Check your App Password."
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
