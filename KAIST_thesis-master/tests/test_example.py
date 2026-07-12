"""
Example Test File

This is a template showing how to write tests for the TNIC module.
Delete this file once real tests are added.

Author: KAIST Thesis Project
Date: 2025-01-05
"""

import pytest


def test_tnic_module_imports():
    """Test that tnic module can be imported."""
    import tnic
    assert tnic.__version__ == "0.1.0"


def test_sample_fixture(sample_korean_text):
    """Test that sample fixture is available."""
    assert isinstance(sample_korean_text, str)
    assert len(sample_korean_text) > 0
    assert '반도체' in sample_korean_text


def test_temp_directory(temp_data_dir):
    """Test that temp directory fixture works."""
    assert temp_data_dir.exists()
    assert temp_data_dir.is_dir()

    # Create test file
    test_file = temp_data_dir / "test.txt"
    test_file.write_text("test content")

    assert test_file.exists()
    assert test_file.read_text() == "test content"


@pytest.mark.slow
def test_marked_as_slow():
    """Example of a test marked as slow."""
    # This test would be skipped when running: pytest -m "not slow"
    import time
    time.sleep(0.1)  # Simulate slow operation
    assert True


@pytest.mark.parametrize("input_text,expected_length", [
    ("test", 4),
    ("hello", 5),
    ("", 0),
])
def test_parametrized_example(input_text, expected_length):
    """Example of parametrized test."""
    assert len(input_text) == expected_length


class TestExampleClass:
    """Example test class for grouping related tests."""

    def test_method_one(self):
        """First test method."""
        assert 1 + 1 == 2

    def test_method_two(self, sample_korean_text):
        """Second test method using fixture."""
        assert '반도체' in sample_korean_text
