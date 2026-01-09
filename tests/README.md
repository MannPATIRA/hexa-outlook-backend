# Test Suite Documentation

This directory contains comprehensive tests for the Outlook Add-in Backend API.

## Test Structure

### `test_models.py`
Tests for data models:
- `PurchaseRequisition` model creation and serialization
- `Supplier` model creation and serialization
- `RFQ` model creation and serialization

### `test_services.py`
Tests for business logic services:
- **MockERP**: Data storage and retrieval
  - Initialization with sample data
  - Getting open PRs
  - Getting PRs by ID
  - Supplier matching by material and specs
  - RFQ storage and retrieval
- **PRService**: PR decomposition
  - Decomposing PRs into structured data
  - Extracting material codes, specs, drawing files, quantities
- **SupplierService**: Supplier matching
  - Finding matching suppliers for PRs
  - Getting suppliers by IDs
- **RFQService**: RFQ generation
  - Generating RFQs for multiple suppliers
  - Finalizing RFQs with user edits

### `test_api.py`
Tests for API endpoints:
- **PRs API**:
  - GET `/api/prs/open` - Get all open PRs
  - Response structure validation
- **Suppliers API**:
  - POST `/api/suppliers/search` - Search suppliers
  - Validation error handling
  - Invalid PR ID handling
- **RFQs API**:
  - POST `/api/rfqs/generate` - Generate RFQs
  - POST `/api/rfqs/finalize` - Finalize RFQs
  - Invalid input handling
  - JSON and string body handling
- **Health & Root**:
  - GET `/health` - Health check
  - GET `/` - Root endpoint
- **Error Handling**:
  - CORS headers
  - 404 errors
  - Validation errors

### `test_integration.py`
End-to-end integration tests (using TestClient):
- Complete workflow: Get PRs → Search Suppliers → Generate RFQs → Finalize
- Multiple PRs workflow
- Supplier matching accuracy
- RFQ content accuracy

### `test_e2e_server.py`
**End-to-end tests with a real uvicorn server:**
- Starts an actual HTTP server on a random available port
- Makes real HTTP requests using `httpx`
- Tests all endpoints with actual network requests
- Verifies server startup, shutdown, and cleanup
- Tests complete workflows with real HTTP stack
- Verifies CORS headers in real HTTP responses
- Ensures proper server cleanup after tests (pass or fail)

**Key differences from `test_api.py`:**
- `test_api.py` uses FastAPI's `TestClient` (in-process, no real server)
- `test_e2e_server.py` starts a real uvicorn server and makes actual HTTP requests
- E2E tests verify the full HTTP stack, middleware, and server behavior

## Running Tests

### Run All Tests
```bash
pytest
```

### Run Specific Test File
```bash
pytest tests/test_models.py
pytest tests/test_services.py
pytest tests/test_api.py
pytest tests/test_integration.py
pytest tests/test_e2e_server.py
```

### Run E2E Tests (Real Server)
```bash
# Run only the E2E tests with real server
pytest tests/test_e2e_server.py

# Run with verbose output to see server startup
pytest tests/test_e2e_server.py -v
```

### Run Specific Test Class
```bash
pytest tests/test_services.py::TestMockERP
```

### Run Specific Test Method
```bash
pytest tests/test_api.py::TestPRsAPI::test_get_open_prs
```

### Run with Verbose Output
```bash
pytest -v
```

### Run with Coverage
```bash
pytest --cov=app --cov-report=html
```

## Test Fixtures

The `conftest.py` file provides shared fixtures:
- `mock_erp`: MockERP instance
- `pr_service`: PRService instance
- `supplier_service`: SupplierService instance with MockERP
- `rfq_service`: RFQService instance with MockERP

The `test_api.py` file provides:
- `client`: FastAPI TestClient for API testing (in-process)

The `test_e2e_server.py` file provides:
- `server_port`: Available port for test server
- `server_process`: Running uvicorn server instance (session-scoped)
- `client`: httpx.Client for real HTTP requests to the test server

## Test Coverage Goals

The test suite aims to cover:
- ✅ All model methods
- ✅ All service methods
- ✅ All API endpoints (with TestClient)
- ✅ All API endpoints (with real HTTP server)
- ✅ Error handling scenarios
- ✅ Validation errors
- ✅ Integration workflows
- ✅ Edge cases (non-existent IDs, invalid inputs)
- ✅ Real HTTP stack and middleware
- ✅ Server lifecycle (startup/shutdown)
- ✅ CORS headers in real HTTP responses

## Adding New Tests

When adding new functionality:
1. Add model tests in `test_models.py`
2. Add service tests in `test_services.py`
3. Add API tests in `test_api.py` (using TestClient)
4. Add E2E tests in `test_e2e_server.py` (using real server) if the endpoint needs real HTTP testing
5. Add integration tests in `test_integration.py` if applicable
6. Update this README if adding new test categories

## E2E Test Details

The `test_e2e_server.py` file provides comprehensive end-to-end testing with a real server:

**Server Management:**
- Automatically finds an available port
- Starts uvicorn server in a background thread
- Waits for server to be ready before running tests
- Ensures server shutdown after all tests complete (using `atexit` and fixture cleanup)

**Test Coverage:**
- All API endpoints tested with real HTTP requests
- Error scenarios (404, 422) tested with real HTTP
- CORS headers verified in actual HTTP responses
- Complete workflow tested end-to-end with real requests
- Server cleanup verified

**Running E2E Tests:**
```bash
# Run all E2E tests
pytest tests/test_e2e_server.py -v

# Run specific E2E test class
pytest tests/test_e2e_server.py::TestE2EPurchaseRequisitions

# Run with output to see server lifecycle
pytest tests/test_e2e_server.py -v -s
```

**Note:** E2E tests may take slightly longer than TestClient tests as they involve actual network requests and server startup/shutdown.
