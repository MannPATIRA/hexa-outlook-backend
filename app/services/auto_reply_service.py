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
import logging
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
        self.smtp_port_ssl = 465  # Alternative SSL port
        
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
    
    def _is_render_free_tier(self) -> bool:
        """Check if running on Render free tier (which blocks SMTP)."""
        import os
        # Render sets RENDER environment variable
        return os.getenv("RENDER") == "true" and os.getenv("RENDER_SERVICE_TYPE") is not None
    
    def _generate_reply_id(self) -> str:
        self._reply_counter += 1
        return f"AUTO-REPLY-{self._reply_counter:03d}"
    
    def generate_quote_reply(self, material: str, quantity: int = 100, display_name: Optional[str] = None) -> str:
        """Generate a realistic quote email body."""
        price = random.randint(35, 75)
        delivery = random.choice(["2-3 weeks", "3-4 weeks", "4-6 weeks"])
        
        # Use provided display_name or fall back to self.sender_name
        sender_name = display_name if display_name else self.sender_name
        
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

{sender_name}
Sales Department
Email: {self.sender_email}
"""

    def generate_clarification_reply(self, material: str, clarification_type: str = "procurement", display_name: Optional[str] = None) -> str:
        """Generate a clarification request email body."""
        
        # Use provided display_name or fall back to self.sender_name
        sender_name = display_name if display_name else self.sender_name
        
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

{sender_name}
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

{sender_name}
Sales Department
"""

    def schedule_reply(
        self,
        to_email: str,
        original_subject: str,
        original_message_id: str,
        material: str,
        reply_type: str = "quote",  # "quote", "clarification_procurement", "clarification_engineering"
        delay_seconds: int = 5,
        quantity: int = 100,
        supplier_id: Optional[str] = None,
        supplier_name: Optional[str] = None
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
            supplier_id: Optional supplier ID for tracking
            supplier_name: Optional supplier name for email display
            
        Returns:
            Dict with reply_id and status
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "SMTP not configured. Set DEMO_SUPPLIER_EMAIL and DEMO_SUPPLIER_PASSWORD environment variables.",
                "reply_id": None
            }
        
        # Warn if on Render free tier
        if self._is_render_free_tier():
            print("⚠️  Warning: Render free tier blocks SMTP. Email sending may fail.")
            print("   Consider upgrading to a paid plan or using an email API service.")
        
        reply_id = self._generate_reply_id()
        
        # #region agent log
        import json
        try:
            with open('/Users/ishaanmakkar/Documents/hexa-outlook-backend/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"id":f"log_{int(__import__('time').time()*1000)}","timestamp":int(__import__('time').time()*1000),"location":"auto_reply_service.py:233","message":"schedule_reply method entry","data":{"supplier_id":supplier_id,"supplier_name":supplier_name,"supplier_id_type":str(type(supplier_id)),"supplier_name_type":str(type(supplier_name)),"supplier_name_is_none":supplier_name is None,"supplier_name_is_empty":supplier_name == "" if supplier_name else None,"supplier_name_stripped":supplier_name.strip() if supplier_name else None,"fallback_name":self.sender_name},"sessionId":"debug-session","runId":"run1","hypothesisId":"B"}) + '\n')
        except: pass
        # #endregion
        
        # Use supplier_name if provided and not empty, otherwise fall back to environment variable
        display_name = supplier_name if supplier_name and supplier_name.strip() else self.sender_name
        
        # #region agent log
        try:
            with open('/Users/ishaanmakkar/Documents/hexa-outlook-backend/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"id":f"log_{int(__import__('time').time()*1000)}","timestamp":int(__import__('time').time()*1000),"location":"auto_reply_service.py:236","message":"display_name calculated","data":{"supplier_name_input":supplier_name,"display_name_result":display_name,"used_fallback":display_name == self.sender_name,"condition_supplier_name_truthy":bool(supplier_name),"condition_supplier_name_strip":bool(supplier_name and supplier_name.strip()) if supplier_name else False},"sessionId":"debug-session","runId":"run1","hypothesisId":"C"}) + '\n')
        except: pass
        # #endregion
        
        # Log for debugging (both logging and print for visibility)
        logger = logging.getLogger(__name__)
        logger.info(f"Schedule reply - supplier_id: {supplier_id}, supplier_name: {supplier_name}")
        logger.info(f"Using display_name: {display_name} (fallback: {self.sender_name})")
        
        # Print for immediate visibility in console/logs
        print(f"🔍 DEBUG: Schedule reply received - supplier_id: {supplier_id}, supplier_name: '{supplier_name}'")
        print(f"🔍 DEBUG: Using display_name: '{display_name}' (fallback was: '{self.sender_name}')")
        
        # Generate reply content based on type
        if reply_type == "quote":
            body = self.generate_quote_reply(material, quantity, display_name)
        elif reply_type == "clarification_engineering":
            body = self.generate_clarification_reply(material, "engineering", display_name)
        else:
            body = self.generate_clarification_reply(material, "procurement", display_name)
        
        # Track the scheduled reply
        self._scheduled_replies[reply_id] = ScheduledReply(
            reply_id=reply_id,
            to_email=to_email,
            subject=f"RE: {original_subject}",
            scheduled_time=datetime.now()
        )
        
        # Start a background thread to send after delay
        def send_delayed():
            # #region agent log
            import json
            try:
                with open('/Users/ishaanmakkar/Documents/hexa-outlook-backend/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"id":f"log_{int(__import__('time').time()*1000)}","timestamp":int(__import__('time').time()*1000),"location":"auto_reply_service.py:254","message":"send_delayed thread entry - before _send_email call","data":{"display_name_passed":display_name,"display_name_type":str(type(display_name))},"sessionId":"debug-session","runId":"run1","hypothesisId":"D"}) + '\n')
            except: pass
            # #endregion
            time.sleep(delay_seconds)
            success = self._send_email(
                to_email=to_email,
                subject=f"RE: {original_subject}",
                body=body,
                original_message_id=original_message_id,
                display_name=display_name
            )
            self._scheduled_replies[reply_id].status = "sent" if success else "failed"
        
        thread = threading.Thread(target=send_delayed, daemon=True)
        thread.start()
        
        return {
            "success": True,
            "reply_id": reply_id,
            "message": f"Reply scheduled to be sent in {delay_seconds} seconds",
            "to_email": to_email,
            "reply_type": reply_type,
            "supplier_id": supplier_id,
            "supplier_name": display_name
        }
    
    def _send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        original_message_id: str,
        display_name: Optional[str] = None
    ) -> bool:
        """
        Send the actual email via SMTP.
        
        Returns True if successful, False otherwise.
        """
        try:
            # #region agent log
            import json
            try:
                with open('/Users/ishaanmakkar/Documents/hexa-outlook-backend/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"id":f"log_{int(__import__('time').time()*1000)}","timestamp":int(__import__('time').time()*1000),"location":"auto_reply_service.py:302","message":"_send_email method entry","data":{"display_name_received":display_name,"display_name_type":str(type(display_name)),"display_name_is_none":display_name is None,"display_name_is_empty":display_name == "" if display_name else None,"fallback_sender_name":self.sender_name},"sessionId":"debug-session","runId":"run1","hypothesisId":"E"}) + '\n')
            except: pass
            # #endregion
            
            # Use provided display_name or fall back to self.sender_name
            sender_display_name = display_name if display_name else self.sender_name
            
            # #region agent log
            try:
                with open('/Users/ishaanmakkar/Documents/hexa-outlook-backend/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"id":f"log_{int(__import__('time').time()*1000)}","timestamp":int(__import__('time').time()*1000),"location":"auto_reply_service.py:305","message":"sender_display_name calculated in _send_email","data":{"display_name_input":display_name,"sender_display_name_result":sender_display_name,"used_fallback":sender_display_name == self.sender_name,"from_field_value":f"{sender_display_name} <{self.sender_email}>"},"sessionId":"debug-session","runId":"run1","hypothesisId":"E"}) + '\n')
            except: pass
            # #endregion
            
            # Debug: Print what will be used in From field
            print(f"🔍 DEBUG: Sending email with From: '{sender_display_name} <{self.sender_email}>'")
            
            # Create message
            msg = MIMEMultipart("alternative")
            msg["From"] = f"{sender_display_name} <{self.sender_email}>"
            
            # #region agent log
            try:
                with open('/Users/ishaanmakkar/Documents/hexa-outlook-backend/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"id":f"log_{int(__import__('time').time()*1000)}","timestamp":int(__import__('time').time()*1000),"location":"auto_reply_service.py:310","message":"Email From header set","data":{"from_header_value":msg["From"],"sender_display_name":sender_display_name,"sender_email":self.sender_email},"sessionId":"debug-session","runId":"run1","hypothesisId":"E"}) + '\n')
            except: pass
            # #endregion
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
            # Try port 587 (TLS) first, then fallback to 465 (SSL)
            context = ssl.create_default_context()
            
            # Try port 587 (TLS/STARTTLS)
            try:
                with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                    server.starttls(context=context)
                    server.login(self.sender_email, self.sender_password)
                    server.send_message(msg)
                print(f"✅ Email sent successfully to {to_email}")
                return True
            except (OSError, ConnectionError) as e:
                # Port 587 might be blocked (common on free hosting)
                # Try port 465 (SSL) as fallback
                error_msg = str(e)
                if "Network is unreachable" in error_msg or "101" in error_msg:
                    print(f"⚠️  Port 587 blocked, trying SSL port 465...")
                    try:
                        with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port_ssl, timeout=10) as server:
                            server.login(self.sender_email, self.sender_password)
                            server.send_message(msg)
                        print(f"✅ Email sent successfully to {to_email} (via SSL)")
                        return True
                    except Exception as ssl_error:
                        print(f"❌ Both SMTP ports blocked. This is common on free hosting tiers.")
                        print(f"   Error: {ssl_error}")
                        print(f"   💡 Solution: Use a paid Render plan or switch to an email API service (SendGrid, Mailgun, etc.)")
                        return False
                else:
                    raise  # Re-raise if it's a different error
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ SMTP Authentication failed: {e}")
            print("   Make sure you're using an App Password, not your regular password!")
            return False
        except Exception as e:
            error_str = str(e)
            if "Network is unreachable" in error_str or "101" in error_str:
                print(f"❌ SMTP connection blocked by hosting provider")
                print(f"   This is common on free tiers (Render, Heroku, etc.)")
                print(f"   💡 Solutions:")
                print(f"      1. Upgrade to a paid Render plan")
                print(f"      2. Use an email API service (SendGrid, Mailgun, AWS SES)")
                print(f"      3. Run locally for testing")
            else:
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
        
        # Try port 587 (TLS) first
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)
            
            return {
                "success": True,
                "message": "SMTP connection successful! (Port 587/TLS)",
                "sender_email": self.sender_email,
                "port": self.smtp_port
            }
        except (OSError, ConnectionError) as e:
            error_str = str(e)
            if "Network is unreachable" in error_str or "101" in error_str:
                # Try port 465 (SSL) as fallback
                try:
                    with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port_ssl, timeout=10) as server:
                        server.login(self.sender_email, self.sender_password)
                    return {
                        "success": True,
                        "message": "SMTP connection successful! (Port 465/SSL)",
                        "sender_email": self.sender_email,
                        "port": self.smtp_port_ssl,
                        "warning": "Port 587 was blocked, using SSL port 465"
                    }
                except Exception as ssl_error:
                    return {
                        "success": False,
                        "error": f"Both SMTP ports blocked. This is common on free hosting tiers.",
                        "details": str(ssl_error),
                        "suggestion": "Upgrade to a paid plan or use an email API service (SendGrid, Mailgun, AWS SES)"
                    }
            else:
                return {
                    "success": False,
                    "error": str(e)
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
