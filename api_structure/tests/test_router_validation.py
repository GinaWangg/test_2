"""Unit tests for email detection router validation."""

import pytest
from pydantic import ValidationError

from api_structure.src.routers.email_detect import (
    EmailDetectInput,
    _validate_input_fields,
)
from api_structure.core.exception_handlers import AbortException


def test_email_detect_input_valid():
    """Test valid EmailDetectInput creation."""
    input_data = EmailDetectInput(
        case_id="TEST123",
        email="test@example.com",
        phone="1234567890",
        case_date=1747825750000,
        site="uk",
        product_type="Graphic Card",
        email_content="Test email content",
        product_model="K3605VC",
        product_sn="S1N0CX065068038",
        problem_description_content="Test problem",
    )
    assert input_data.case_id == "TEST123"
    assert input_data.site == "uk"


def test_validate_input_fields_valid():
    """Test validation passes for valid input."""
    input_data = EmailDetectInput(
        case_id="TEST123",
        email="test@example.com",
        phone="1234567890",
        case_date=1747825750000,
        site="uk",
        product_type="Graphic Card",
        email_content="Test email content",
    )
    # Should not raise exception
    _validate_input_fields(input_data)


def test_validate_input_fields_missing_case_id():
    """Test validation fails for missing case_id."""
    input_data = EmailDetectInput(
        case_id="",
        email="test@example.com",
        phone="1234567890",
        case_date=1747825750000,
        site="uk",
        product_type="Graphic Card",
        email_content="Test email content",
    )
    with pytest.raises(AbortException) as exc_info:
        _validate_input_fields(input_data)
    assert exc_info.value.status == 400
    assert "case_id" in exc_info.value.message


def test_validate_input_fields_wrong_type_case_date():
    """Test validation fails for wrong type in case_date."""
    input_data = EmailDetectInput(
        case_id="TEST123",
        email="test@example.com",
        phone="1234567890",
        case_date="not_an_int",  # type: ignore
        site="uk",
        product_type="Graphic Card",
        email_content="Test email content",
    )
    with pytest.raises(AbortException) as exc_info:
        _validate_input_fields(input_data)
    assert exc_info.value.status == 400
    assert "case_date" in exc_info.value.message


def test_validate_input_fields_empty_email():
    """Test validation fails for empty email."""
    input_data = EmailDetectInput(
        case_id="TEST123",
        email="",
        phone="1234567890",
        case_date=1747825750000,
        site="uk",
        product_type="Graphic Card",
        email_content="Test email content",
    )
    with pytest.raises(AbortException) as exc_info:
        _validate_input_fields(input_data)
    assert exc_info.value.status == 400
    assert "email" in exc_info.value.message


def test_email_detect_input_optional_fields():
    """Test EmailDetectInput with optional fields omitted."""
    input_data = EmailDetectInput(
        case_id="TEST123",
        email="test@example.com",
        phone="1234567890",
        case_date=1747825750000,
        site="uk",
        product_type="Graphic Card",
        email_content="Test email content",
    )
    assert input_data.product_model == ""
    assert input_data.product_sn is None
    assert input_data.problem_description_content is None
