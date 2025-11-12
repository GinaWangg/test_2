# Testing Notes

## Test Coverage

### Completed Tests ✅
- `test_product_line_mapping.py` - All 7 tests passing
  - Tests valid lookups for various sites and product types
  - Tests case insensitivity
  - Tests error handling for invalid inputs

### Blocked Tests ⚠️
- `test_router_validation.py` - Cannot run due to missing `opentelemetry` dependency
  - Tests are written but require OpenTelemetry to be installed
  - OpenTelemetry is used by `core/timer.py` for the `@timed` decorator

## Dependencies Required for Full Testing

The following dependencies are needed but not in `requirements.txt`:
```
opentelemetry-api
opentelemetry-sdk
opentelemetry-instrumentation-fastapi
azure-monitor-opentelemetry
```

## Running Tests

```bash
# Install dependencies
pip install -r requirements.txt
pip install opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation-fastapi

# Run all tests
pytest api_structure/tests/ -v

# Run specific test file
pytest api_structure/tests/test_product_line_mapping.py -v
```

## Manual Testing

To manually test the endpoint:

1. Start the server:
```bash
cd /home/runner/work/test_2/test_2
python -m api_structure.main
```

2. Send a test request:
```bash
curl -X POST http://127.0.0.1:8000/v3/emailDetect \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "AOCC_test",
    "email": "dawid@kaczmarski.pl",
    "phone": "555444333",
    "case_date": 1747825750000,
    "site": "uk",
    "product_type": "Graphic Card",
    "email_content": "你好",
    "product_model": "K3605VC",
    "product_sn": "S1N0CX065068038",
    "problem_description_content": "你好"
  }'
```

Expected response status: 200 OK

## Test Coverage Summary

| Component | Test File | Status |
|-----------|-----------|--------|
| Product Line Mapping | test_product_line_mapping.py | ✅ 7/7 passing |
| Router Validation | test_router_validation.py | ⚠️ Blocked (missing deps) |
| Email Summary Handler | N/A | ❌ Not implemented |
| Email Split Handler | N/A | ❌ Not implemented |
| Email Translate Handler | N/A | ❌ Not implemented |
| Vector Search Handler | N/A | ❌ Not implemented |
| Email Detect Pipeline | N/A | ❌ Not implemented |

## Recommendations

1. Add OpenTelemetry dependencies to `requirements.txt` or `api_structure/requirements.txt`
2. Add integration tests that mock the GPT and Google Translate clients
3. Add end-to-end tests that test the full pipeline
4. Consider adding tests for error scenarios (timeout, API failures, etc.)
