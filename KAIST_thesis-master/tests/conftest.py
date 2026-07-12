"""
Pytest Configuration and Shared Fixtures

This file contains pytest configuration and shared fixtures used across all tests.

Fixtures:
    - sample_korean_text: Sample Korean business description for testing
    - sample_english_text: Sample English text for comparison
    - temp_data_dir: Temporary directory for test data

Author: KAIST Thesis Project
Date: 2025-01-05
"""

import pytest
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def sample_korean_text():
    """Sample Korean business description for testing."""
    return """
    당사는 반도체 설계 및 제조를 주요 사업으로 영위하고 있습니다.
    주요 제품은 메모리 반도체, 시스템 반도체 등이 있으며,
    국내외 고객사에 제품을 공급하고 있습니다.
    2024년 기준으로 매출액은 전년 대비 15% 증가하였으며,
    연구개발에 지속적으로 투자하고 있습니다.
    """


@pytest.fixture
def sample_english_text():
    """Sample English business description for comparison."""
    return """
    The company engages in the design and manufacture of semiconductors
    as its primary business. Main products include memory semiconductors
    and system semiconductors, which are supplied to domestic and
    international customers. Revenue increased by 15% year-over-year
    as of 2024, with continued investment in research and development.
    """


@pytest.fixture
def sample_korean_texts_dict():
    """Dictionary of sample Korean texts for corpus testing."""
    return {
        'firm1': '당사는 반도체 제조 및 판매 업체입니다. 메모리 반도체 전문 기업입니다.',
        'firm2': '우리 회사는 소프트웨어 개발 전문 기업입니다. 클라우드 서비스를 제공합니다.',
        'firm3': '제약 산업에서 의약품 연구 개발을 하고 있습니다. 바이오 의약품을 생산합니다.',
        'firm4': '자동차 부품 제조 및 공급 업체입니다. 전기차 배터리 시스템을 개발합니다.',
        'firm5': '건설 및 토목 공사를 수행하는 기업입니다. 스마트 건설 기술을 보유하고 있습니다.',
    }


@pytest.fixture
def temp_data_dir(tmp_path):
    """
    Create temporary directory for test data.

    Automatically cleaned up after test completes.

    Usage:
        def test_something(temp_data_dir):
            test_file = temp_data_dir / "test.csv"
            # ... use test_file ...
    """
    data_dir = tmp_path / "test_data"
    data_dir.mkdir()
    yield data_dir
    # Cleanup happens automatically via tmp_path


@pytest.fixture
def sample_firm_words():
    """Sample firm word sets for matrix testing."""
    return {
        'firm1': {'반도체', '제조', '판매', '메모리', '전문'},
        'firm2': {'소프트웨어', '개발', '전문', '클라우드', '서비스'},
        'firm3': {'제약', '의약품', '연구', '개발', '바이오', '생산'},
    }


@pytest.fixture
def sample_vocabulary():
    """Sample vocabulary list for testing."""
    return [
        '반도체', '제조', '판매', '메모리', '전문',
        '소프트웨어', '개발', '클라우드', '서비스',
        '제약', '의약품', '연구', '바이오', '생산'
    ]


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "requires_mongodb: marks tests that require MongoDB connection"
    )
    config.addinivalue_line(
        "markers", "requires_kiwi: marks tests that require kiwipiepy"
    )
