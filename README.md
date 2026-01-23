# Outlook Add-in Backend API

Backend server for Outlook add-in integration to manage Purchase Requisitions (PRs) and generate Request for Quotations (RFQs) from SAP ERP data.

## Overview

This FastAPI backend provides REST endpoints for an Outlook add-in to:
- Retrieve open Purchase Requisitions from a mock SAP ERP system
- Search for suppliers matching PR requirements
- Generate RFQ content for selected suppliers
- Finalize RFQs after user review and editing

## Architecture

### Backend Responsibilities
- Data management via MockERP class
- Business logic (PR decomposition, supplier matching, RFQ generation)
- REST API endpoints for Outlook add-in communication

### Outlook Add-in Responsibilities
- Email operations (creating drafts, sending emails)
- Folder management (creating folders, organizing emails)
- User interface (displaying PRs, supplier selection, RFQ review/editing)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd hexa-outlook-backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy environment file:
```bash
cp .env.example .env
```

5. Update `.env` with your configuration (especially CORS origins for production)

## Running the Server

### Development Mode
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at:
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### 1. Get Open Purchase Requisitions
**GET** `/api/prs/open`

Returns all open PRs from the ERP system.

**Response:**
```json
{
  "prs": [
    {
      "pr_id": "PR-001",
      "material": "MAT-12345",
      "specs": {...},
      "drawing_files": ["drawing1.pdf"],
      "step_files": ["model1.step", "assembly.step"],
      "quantities": 100,
      "unit": "pcs",
      "description": "...",
      "status": "open",
      "created_date": "2024-01-15T10:30:00"
    }
  ]
}
```

### 2. Search Suppliers
**POST** `/api/suppliers/search`

Searches for suppliers matching a PR's requirements.

**Request:**
```json
{
  "pr_id": "PR-001",
  "material": "MAT-12345",
  "specs": {
    "material_type": "Steel Component",
    "grade": "SS304"
  }
}
```

**Response:**
```json
{
  "suppliers": [
    {
      "supplier_id": "SUP-001",
      "name": "ABC Manufacturing",
      "email": "procurement@abcmanufacturing.com",
      "contact_person": "John Smith",
      "phone": "+1-555-0101",
      "match_reason": "Standard supplier for MAT-12345",
      "match_score": 10
    }
  ]
}
```

### 3. Generate RFQs
**POST** `/api/rfqs/generate`

Generates RFQ content for selected suppliers.

**Request:**
```json
{
  "pr_id": "PR-001",
  "supplier_ids": ["SUP-001", "SUP-002"]
}
```

**Response:**
```json
{
  "rfqs": [
    {
      "rfq_id": "RFQ-001",
      "supplier_id": "SUP-001",
      "supplier_name": "ABC Manufacturing",
      "supplier_email": "procurement@abcmanufacturing.com",
      "pr_id": "PR-001",
      "subject": "RFQ for MAT-12345 - 100 pcs",
      "body": {
        "greeting": "Dear ABC Manufacturing,",
        "introduction": "We are requesting a quotation for the following:",
        "material_details": {...},
        "requirements": {...},
        "drawing_files": ["drawing1.pdf"],
        "step_files": ["model1.step"],
        "delivery_requirements": "...",
        "quotation_deadline": "February 15, 2024",
        "closing": "Please provide your quotation by..."
      },
      "attachments": ["drawing1.pdf", "model1.step"],
      "status": "draft"
    }
  ]
}
```

### 4. Finalize RFQ
**POST** `/api/rfqs/finalize`

Finalizes an RFQ with user-edited content.

**Request:**
```json
{
  "rfq_id": "RFQ-001",
  "final_subject": "RFQ for MAT-12345 - 100 pcs",
  "final_body": "Dear ABC Manufacturing,\n\nWe are requesting...",
  "status": "ready_to_send"
}
```

**Response:**
```json
{
  "rfq_id": "RFQ-001",
  "status": "finalized",
  "message": "RFQ finalized successfully"
}
```

## Data Models

### Purchase Requisition (PR)
- `pr_id`: Unique identifier
- `material`: Material code
- `specs`: Technical specifications (dict)
- `drawing_files`: List of drawing file references
- `step_files`: List of STEP file references (3D CAD models)
- `quantities`: Quantity required
- `unit`: Unit of measurement
- `description`: Additional description
- `status`: Status (e.g., "open", "closed")
- `created_date`: Creation timestamp

### Supplier
- `supplier_id`: Unique identifier
- `name`: Supplier name
- `email`: Contact email
- `capabilities`: List of materials/specs they can handle
- `standard_for_materials`: List of material codes they're standard supplier for

### RFQ
- `rfq_id`: Unique identifier
- `supplier_id`: Target supplier
- `pr_id`: Related purchase requisition
- `subject`: Email subject line
- `body`: Email body content (structured JSON)
  - Contains `drawing_files` and `step_files` fields
- `attachments`: List of all files to attach (drawing files + step files)
- `status`: Status (draft, finalized, sent)

## MockERP

The backend includes a `MockERP` class that simulates SAP ERP functionality with:
- Pre-populated sample PRs
- Pre-populated sample suppliers
- Supplier matching logic based on material codes and specifications

## Outlook Add-in Integration Notes

### Email Drafts
The Outlook add-in should use `Office.context.mailbox.item` API to create email drafts from the RFQ content returned by the backend.

### Email Sending
The add-in should send emails using `Office.context.mailbox.item.send()` or Microsoft Graph API. This ensures emails are sent from the user's account and appear in their sent items.

### Folder Creation
The add-in should use Microsoft Graph API or EWS to create folders and organize emails. For example:
- Create a folder named after the part/material
- Create a subfolder "Sent RFQs"
- Move sent RFQ emails to the appropriate folder

### Workflow
1. Add-in calls `GET /api/prs/open` to get open PRs
2. User selects a PR
3. Add-in calls `POST /api/suppliers/search` with PR ID
4. User selects suppliers
5. Add-in calls `POST /api/rfqs/generate` with PR ID and supplier IDs
6. Add-in creates email drafts from RFQ content
7. User reviews and edits RFQ emails
8. Add-in calls `POST /api/rfqs/finalize` with finalized content
9. Add-in sends emails to suppliers
10. Add-in creates folders and organizes sent emails

## Error Handling

The API returns appropriate HTTP status codes:
- `200`: Success
- `404`: Resource not found
- `422`: Validation error
- `500`: Internal server error

Error responses include a `detail` field with error information.

## CORS Configuration

In production, update the CORS configuration in `app/main.py` to allow only specific Outlook add-in domains:
```python
allow_origins=["https://outlook.office.com", "https://outlook.live.com"]
```

## Development

### Project Structure
```
hexa-outlook-backend/
├── app/
│   ├── main.py              # FastAPI app initialization
│   ├── models/              # Data models
│   ├── services/            # Business logic services
│   ├── api/
│   │   ├── routes/          # API endpoints
│   │   └── schemas/         # Pydantic schemas
│   └── utils/               # Utility functions
├── requirements.txt
├── .env.example
└── README.md
```

## Testing

### Running Tests

The project includes comprehensive test suites covering all functionality:

1. **Install test dependencies** (already in requirements.txt):
```bash
pip install -r requirements.txt
```

2. **Run all tests**:
```bash
pytest
```

3. **Run with verbose output**:
```bash
pytest -v
```

4. **Run specific test files**:
```bash
pytest tests/test_models.py
pytest tests/test_services.py
pytest tests/test_api.py
pytest tests/test_integration.py
```

5. **Run with coverage** (requires pytest-cov):
```bash
pytest --cov=app --cov-report=html
```

### Test Coverage

The test suite includes:

- **Model Tests** (`test_models.py`): Tests for PurchaseRequisition, Supplier, and RFQ models
- **Service Tests** (`test_services.py`): Tests for MockERP, PRService, SupplierService, and RFQService
- **API Tests** (`test_api.py`): Tests for all API endpoints including:
  - GET `/api/prs/open`
  - POST `/api/suppliers/search`
  - POST `/api/rfqs/generate`
  - POST `/api/rfqs/finalize`
  - Error handling and validation
- **Integration Tests** (`test_integration.py`): End-to-end workflow tests

### Manual Testing

You can also test the API manually using:
- Swagger UI at `/docs`
- ReDoc at `/redoc`
- curl or Postman
- Integration tests from the Outlook add-in

## License

[Add your license here]
