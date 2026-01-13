# Demo Email Auto-Reply Setup Guide

This guide explains how to set up automatic email replies for demos and testing. When you send an RFQ, a realistic supplier reply will automatically appear in your inbox 30 seconds later - no manual work required!

---

## 🚀 Quick Setup (5 minutes)

### Step 1: Create a Demo Supplier Gmail Account

1. Go to https://accounts.google.com/signup
2. Create a new Gmail account (e.g., `hexademosupplier@gmail.com`)
3. **Save** the email and password somewhere safe

---

### Step 2: Enable 2-Factor Authentication

This is required before you can create an App Password.

1. Log into your new Gmail account
2. Go to https://myaccount.google.com/security
3. Click **"2-Step Verification"**
4. Follow the steps to enable it (use your phone number)

---

### Step 3: Create an App Password

Regular Gmail passwords don't work with SMTP. You need an "App Password":

1. After enabling 2FA, go to: https://myaccount.google.com/apppasswords
2. Click **"Select app"** → Choose **"Mail"**
3. Click **"Select device"** → Choose **"Other"** and type `Hexa Backend`
4. Click **"Generate"**
5. **Copy the 16-character password** (looks like: `abcd efgh ijkl mnop`)
   - ⚠️ **Save this immediately!** You won't be able to see it again.

---

### Step 4: Set Environment Variables

Before starting the backend, set these environment variables:

#### On Mac/Linux (Terminal):

```bash
export DEMO_SUPPLIER_EMAIL="hexademosupplier@gmail.com"
export DEMO_SUPPLIER_PASSWORD="abcd efgh ijkl mnop"
export DEMO_SUPPLIER_NAME="ABC Manufacturing (Demo)"
```

#### On Windows (Command Prompt):

```cmd
set DEMO_SUPPLIER_EMAIL=hexademosupplier@gmail.com
set DEMO_SUPPLIER_PASSWORD=abcd efgh ijkl mnop
set DEMO_SUPPLIER_NAME=ABC Manufacturing (Demo)
```

#### Or create a `.env` file in the project root:

```
DEMO_SUPPLIER_EMAIL=hexademosupplier@gmail.com
DEMO_SUPPLIER_PASSWORD=abcd efgh ijkl mnop
DEMO_SUPPLIER_NAME=ABC Manufacturing (Demo)
```

---

### Step 5: Start the Backend

```bash
cd /Users/mannpatira/hexa-outlook-backend
uvicorn app.main:app --reload --port 8000
```

---

### Step 6: Test the Connection

Open your browser or use curl:

```bash
# Test if SMTP is configured correctly
curl http://localhost:8000/api/demo/test-connection
```

Expected response:
```json
{
  "success": true,
  "message": "SMTP connection successful!",
  "sender_email": "hexademosupplier@gmail.com"
}
```

---

### Step 7: Send a Quick Test Email

```bash
# Replace with YOUR email address
curl -X POST "http://localhost:8000/api/demo/quick-test?to_email=YOUR_EMAIL@outlook.com"
```

Check your inbox - you should receive an email from the demo supplier within a few seconds!

---

## 📧 How to Use Auto-Replies

### From the Outlook Add-in:

When an RFQ is sent, the add-in should call this endpoint:

```javascript
// After sending RFQ, get the message ID and trigger auto-reply
fetch('http://localhost:8000/api/demo/schedule-reply', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        to_email: userEmail,                    // User's Outlook email
        original_subject: "RFQ for Steel Brackets - 100 pcs",
        original_message_id: sentItem.internetMessageId,  // From Outlook
        material: "Steel Brackets",
        reply_type: "random",  // or "quote", "clarification_procurement", "clarification_engineering"
        delay_seconds: 30,
        quantity: 100
    })
});
```

### Using curl:

```bash
curl -X POST http://localhost:8000/api/demo/schedule-reply \
  -H "Content-Type: application/json" \
  -d '{
    "to_email": "your.email@outlook.com",
    "original_subject": "RFQ for Steel Brackets - 100 pcs",
    "original_message_id": "<message123@outlook.com>",
    "material": "Steel Brackets",
    "reply_type": "quote",
    "delay_seconds": 30,
    "quantity": 100
  }'
```

---

## 📋 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/demo/status` | GET | Check if SMTP is configured, view scheduled replies |
| `/api/demo/test-connection` | GET | Test SMTP connection without sending email |
| `/api/demo/schedule-reply` | POST | Schedule an auto-reply (main endpoint) |
| `/api/demo/quick-test?to_email=X` | POST | Send a test email immediately |

---

## 🔧 Reply Types

| Type | Description |
|------|-------------|
| `quote` | A quotation with pricing, delivery time, and terms |
| `clarification_procurement` | Commercial questions (payment terms, shipping, etc.) |
| `clarification_engineering` | Technical questions (tolerances, materials, specs) |
| `random` | Randomly picks one (60% quote, 20% procurement, 20% engineering) |

---

## ❓ Troubleshooting

### "Authentication failed" error

- Make sure you're using the **App Password**, not your regular Gmail password
- The App Password should be 16 characters with spaces (like `abcd efgh ijkl mnop`)
- Make sure 2FA is enabled on the Gmail account

### "Not configured" error

- Check that the environment variables are set:
  ```bash
  echo $DEMO_SUPPLIER_EMAIL
  echo $DEMO_SUPPLIER_PASSWORD
  ```
- If using a `.env` file, make sure `python-dotenv` is loading it

### Email doesn't appear as a reply/thread

- Make sure you're passing the correct `original_message_id` from the sent RFQ
- The Message-ID should look like `<abc123@mail.outlook.com>`
- Check that `In-Reply-To` and `References` headers are being set

### Email goes to spam

- First few emails from a new account may go to spam
- Mark them as "Not spam" and they should appear in inbox going forward
- Add the demo supplier email to your contacts

---

## 🎯 Demo Flow Example

1. User opens Outlook add-in
2. User selects a PR and generates an RFQ
3. User reviews the RFQ and clicks "Send"
4. Add-in sends RFQ email via Outlook
5. Add-in captures the `internetMessageId` of the sent email
6. Add-in calls `/api/demo/schedule-reply` with the message ID
7. **30 seconds later**: A reply appears in the inbox, threaded with the original RFQ
8. User clicks the reply → Add-in sends to `/api/emails/classify`
9. Backend classifies it as quote or clarification
10. Add-in moves email to appropriate folder

---

## 📝 Notes

- The demo supplier account is just for testing - it simulates supplier behavior
- All replies are generated automatically with realistic content
- The threading works because we include `In-Reply-To` and `References` headers
- You can adjust the delay by changing `delay_seconds` (default: 30)
