# tests/test_context_engine.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from core.context_engine import ContextData, WeatherData, NewsItem, ContextEngine


def test_weather_data_has_required_fields():
    w = WeatherData(temperature=15.0, description="맑음", season="봄", weather_code=1)
    assert w.temperature == 15.0
    assert w.description == "맑음"
    assert w.season == "봄"


def test_news_item_has_required_fields():
    n = NewsItem(title="직장인 번아웃", summary="직장 스트레스 증가")
    assert n.title == "직장인 번아웃"
    assert n.summary == "직장 스트레스 증가"


def test_context_data_aggregates():
    weather = WeatherData(temperature=10.0, description="흐림", season="겨울", weather_code=3)
    news = [NewsItem(title="뉴스1", summary="요약1")]
    ctx = ContextData(weather=weather, news_items=news, trend_keywords=["번아웃", "이직"])
    assert ctx.weather.temperature == 10.0
    assert len(ctx.news_items) == 1
    assert "번아웃" in ctx.trend_keywords


@pytest.mark.asyncio
async def test_fetch_weather_returns_weather_data():
    mock_resp_data = {
        "current": {
            "temperature_2m": 14.5,
            "weather_code": 1
        }
    }

    mock_response = AsyncMock()
    mock_response.json = AsyncMock(return_value=mock_resp_data)
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock()
    mock_session.get = MagicMock(return_value=mock_response)

    engine = ContextEngine()
    with patch("aiohttp.ClientSession", return_value=MagicMock(
        __aenter__=AsyncMock(return_value=mock_session),
        __aexit__=AsyncMock(return_value=False)
    )):
        weather = await engine.fetch_weather()

    assert weather.temperature == 14.5
    assert weather.weather_code == 1
    assert weather.season in ["봄", "여름", "가을", "겨울"]
    assert isinstance(weather.description, str)


@pytest.mark.asyncio
async def test_fetch_weather_fallback_on_error():
    engine = ContextEngine()
    with patch("aiohttp.ClientSession") as mock_cls:
        mock_cls.return_value.__aenter__ = AsyncMock(side_effect=Exception("network error"))
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
        weather = await engine.fetch_weather()

    assert weather is not None
    assert isinstance(weather.temperature, float)


@pytest.mark.asyncio
async def test_fetch_news_returns_news_items():
    mock_raw = [
        {"title": "직장인 번아웃 증가", "description": "스트레스 지수 역대 최고"},
        {"title": "40대 이직 트렌드", "description": "중년 커리어 전환"},
    ]
    engine = ContextEngine()
    with patch.object(engine, "_fetch_gnews_raw", return_value=mock_raw):
        items = await engine.fetch_news()

    assert len(items) == 2
    assert items[0].title == "직장인 번아웃 증가"
    assert items[0].summary == "스트레스 지수 역대 최고"


@pytest.mark.asyncio
async def test_fetch_news_fallback_on_empty():
    engine = ContextEngine()
    with patch.object(engine, "_fetch_gnews_raw", return_value=[]):
        items = await engine.fetch_news()
    assert items == []


@pytest.mark.asyncio
async def test_collect_returns_context_data():
    engine = ContextEngine()
    mock_weather = WeatherData(temperature=15.0, description="맑음", season="봄", weather_code=1)
    mock_news = [NewsItem(title="테스트", summary="요약", url="")]

    with patch.object(engine, "fetch_weather", new=AsyncMock(return_value=mock_weather)), \
         patch.object(engine, "fetch_news", new=AsyncMock(return_value=mock_news)):
        ctx = await engine.collect()

    assert ctx.weather.temperature == 15.0
    assert len(ctx.news_items) == 1
    assert isinstance(ctx.trend_keywords, list)
