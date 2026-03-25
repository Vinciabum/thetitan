# tests/test_threads_publisher.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path
from core.threads_publisher import ThreadsPublisher


def test_threads_publisher_requires_token():
    publisher = ThreadsPublisher(access_token="", user_id="")
    assert publisher.is_configured is False


def test_threads_publisher_configured_with_token():
    publisher = ThreadsPublisher(access_token="test_token", user_id="12345")
    assert publisher.is_configured is True


@pytest.mark.asyncio
async def test_publish_returns_false_when_not_configured():
    publisher = ThreadsPublisher(access_token="", user_id="")
    result = await publisher.publish("테스트 캡션", [])
    assert result is False


@pytest.mark.asyncio
async def test_publish_calls_api_when_configured():
    publisher = ThreadsPublisher(access_token="fake_token", user_id="123")

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"id": "post_123"})
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock()
    mock_session.post = MagicMock(return_value=mock_response)

    with patch("aiohttp.ClientSession", return_value=MagicMock(
        __aenter__=AsyncMock(return_value=mock_session),
        __aexit__=AsyncMock(return_value=False)
    )):
        result = await publisher.publish("테스트 캡션", [])

    assert result is True
