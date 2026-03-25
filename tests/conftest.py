# tests/conftest.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_gemini_response():
    """Gemini API 응답 Mock"""
    mock = MagicMock()
    mock.text = ""
    return mock


@pytest.fixture
def mock_weather_data():
    return {
        "temperature": 12.3,
        "weather_code": 3,
        "description": "흐림",
        "season": "봄"
    }


@pytest.fixture
def mock_news_items():
    return [
        {"title": "직장인 번아웃 역대 최고", "description": "2026년 직장인 스트레스 지수 상승"},
        {"title": "재택근무 종료 기업 증가", "description": "사무실 복귀 압박 증가"},
        {"title": "중년 커리어 전환 트렌드", "description": "40대 이직 급증"},
    ]
