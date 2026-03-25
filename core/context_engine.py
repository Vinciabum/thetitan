"""
Context Engine - 날씨, 뉴스, 트렌드 데이터 수집
"""
from dataclasses import dataclass, field
from typing import List


@dataclass
class WeatherData:
    temperature: float
    description: str   # 한국어 날씨 설명 (맑음, 흐림, 비, 눈 등)
    season: str        # 봄/여름/가을/겨울
    weather_code: int  # WMO Weather Code


@dataclass
class NewsItem:
    title: str
    summary: str
    url: str = ""


@dataclass
class ContextData:
    weather: WeatherData
    news_items: List[NewsItem]
    trend_keywords: List[str] = field(default_factory=list)


import asyncio
from datetime import datetime
import aiohttp


# WMO 날씨 코드 → 한국어 설명 매핑
WMO_DESCRIPTIONS = {
    0: "맑음", 1: "대체로 맑음", 2: "부분적으로 흐림", 3: "흐림",
    45: "안개", 48: "서리 안개",
    51: "가벼운 이슬비", 53: "이슬비", 55: "강한 이슬비",
    61: "가벼운 비", 63: "비", 65: "강한 비",
    71: "가벼운 눈", 73: "눈", 75: "강한 눈",
    80: "소나기", 81: "강한 소나기", 82: "폭우",
    95: "뇌우", 99: "강한 뇌우"
}

SEASONS = {1: "겨울", 2: "겨울", 3: "봄", 4: "봄", 5: "봄",
           6: "여름", 7: "여름", 8: "여름", 9: "가을", 10: "가을",
           11: "가을", 12: "겨울"}


class ContextEngine:
    """날씨, 뉴스, 트렌드 데이터를 수집하는 컨텍스트 엔진"""

    WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
    LATITUDE = 37.5665
    LONGITUDE = 126.9780

    # Monologue 타겟 키워드
    NEWS_QUERY = "직장인 번아웃 커리어 이직 워라밸 중년"
    NEWS_QUERY_EN = "burnout career work life balance workplace stress"

    async def fetch_weather(self) -> WeatherData:
        """Open-Meteo API로 현재 날씨 조회"""
        params = {
            "latitude": self.LATITUDE,
            "longitude": self.LONGITUDE,
            "current": "temperature_2m,weather_code",
            "timezone": "Asia/Seoul"
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.WEATHER_URL, params=params) as resp:
                    data = await resp.json()
                    current = data["current"]
                    code = current["weather_code"]
                    month = datetime.now().month
                    return WeatherData(
                        temperature=current["temperature_2m"],
                        weather_code=code,
                        description=WMO_DESCRIPTIONS.get(code, "알 수 없음"),
                        season=SEASONS[month]
                    )
        except Exception:
            month = datetime.now().month
            return WeatherData(
                temperature=0.0,
                weather_code=0,
                description="알 수 없음",
                season=SEASONS[month]
            )

    async def fetch_news(self) -> List[NewsItem]:
        """GNews에서 Monologue 타겟 키워드 뉴스 수집"""
        raw = await asyncio.to_thread(self._fetch_gnews_raw)
        return [
            NewsItem(
                title=item.get("title", ""),
                summary=item.get("description", ""),
                url=item.get("url", "")
            )
            for item in raw
            if item.get("title")
        ]

    def _fetch_gnews_raw(self) -> List[dict]:
        """GNews API 호출 (동기) - thread에서 실행"""
        try:
            from gnews import GNews
            gnews = GNews(max_results=10, period="1d", country="KR", language="ko")
            results = gnews.get_news(self.NEWS_QUERY)
            if not results:
                gnews_en = GNews(max_results=10, period="1d", country="US", language="en")
                results = gnews_en.get_news(self.NEWS_QUERY_EN)
            return results or []
        except Exception:
            return []

    async def collect(self) -> ContextData:
        """날씨와 뉴스를 병렬로 수집하여 ContextData 반환"""
        weather, news_items = await asyncio.gather(
            self.fetch_weather(),
            self.fetch_news()
        )
        trend_keywords = self._extract_keywords(news_items)
        return ContextData(weather=weather, news_items=news_items, trend_keywords=trend_keywords)

    def _extract_keywords(self, news_items: List[NewsItem]) -> List[str]:
        """뉴스 제목에서 심리/감정 관련 키워드 추출"""
        emotional_keywords = ["번아웃", "스트레스", "이직", "커리어", "워라밸",
                              "피로", "희망", "변화", "성장", "불안"]
        found = []
        all_text = " ".join(item.title + " " + item.summary for item in news_items)
        for kw in emotional_keywords:
            if kw in all_text and kw not in found:
                found.append(kw)
        return found[:5]
