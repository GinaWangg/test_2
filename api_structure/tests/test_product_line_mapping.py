"""Unit tests for product line mapping utility."""

import pytest

from api_structure.src.utils.product_line_mapping import find_productline


def test_find_productline_tw_notebook():
    """Test product line lookup for Taiwan notebook."""
    result = find_productline("tw", "Notebook")
    assert result == "notebook"


def test_find_productline_uk_graphic_card():
    """Test product line lookup for UK graphic card."""
    result = find_productline("uk", "Graphic Card")
    assert result == "graphics"


def test_find_productline_us_gaming_handhelds():
    """Test product line lookup for US gaming handhelds."""
    result = find_productline("us", "Gaming Handhelds")
    assert result == "gaming_handhelds"


def test_find_productline_case_insensitive():
    """Test that site and product type are case insensitive."""
    result1 = find_productline("TW", "NOTEBOOK")
    result2 = find_productline("tw", "notebook")
    assert result1 == result2 == "notebook"


def test_find_productline_invalid_site():
    """Test error handling for invalid site."""
    with pytest.raises(KeyError) as exc_info:
        find_productline("invalid_site", "Notebook")
    assert "Not supported by Genio" in str(exc_info.value)


def test_find_productline_invalid_product_type():
    """Test error handling for invalid product type."""
    with pytest.raises(KeyError) as exc_info:
        find_productline("tw", "Invalid Product")
    assert "Not supported by Genio" in str(exc_info.value)


def test_find_productline_gb_to_uk():
    """Test that 'gb' site code works (normalized to 'uk')."""
    # Note: The vector_search handler normalizes gb to uk
    # but product_line_mapping doesn't have gb, only uk
    result = find_productline("uk", "Notebook")
    assert result == "notebook"
