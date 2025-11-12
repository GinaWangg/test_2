"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture
def sample_email_content():
    """Sample email content for testing."""
    return """[Product Information]
Product Type: Gaming NB

[Problem Description]
Subject: Laptop not turning on
My laptop stopped working yesterday. When I press the power button, 
nothing happens. The charging light doesn't come on either."""


@pytest.fixture
def sample_case_data():
    """Sample case data for testing."""
    return {
        "case_id": "TEST_CASE_123",
        "email": "test@example.com",
        "phone": "1234567890",
        "case_date": 1747825750000,
        "site": "uk",
        "product_type": "Graphic Card",
        "email_content": "Test email content",
        "product_model": "K3605VC",
        "product_sn": "S1N0CX065068038",
        "problem_description_content": "Test problem description",
    }
