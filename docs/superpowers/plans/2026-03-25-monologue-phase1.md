# Monologue Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** AutoGram AI 뉴스봇을 3040 직장인을 위한 미니멀 심리 처방 서비스 "Monologue"로 전환한다.

**Architecture:** 기존 agent.py의 뉴스수집/이미지생성/인스타그램 포스팅 파이프라인을 유지하면서, 새로운 세 모듈(ContextEngine, PsychologicalEngine, SlideGenerator)을 추가하여 5페이지 슬라이드 카루셀 콘텐츠를 생성한다. agent.py는 오케스트레이터 역할만 하고 비즈니스 로직은 각 엔진으로 위임한다.

**Tech Stack:** Python 3.9+, aiohttp, Google Gemini 1.5 Flash (텍스트), Gemini Image (이미지), Open-Meteo API (날씨, 무료/무키), GNews (뉴스), instagrapi (Instagram 카루셀), pytest + pytest-asyncio (테스트)

---

## 파일 구조 (변경/생성 대상)

| 파일 | 상태 | 역할 |
|---|---|---|
| `core/context_engine.py` | **신규** | 날씨(Open-Meteo) + 뉴스(GNews) 수집, ContextData 반환 |
| `core/psychological_engine.py` | **신규** | Frankl+Stoic 페르소나 기반 5슬라이드 텍스트 생성 |
| `core/slide_generator.py` | **신규** | 각 슬라이드용 이미지 프롬프트 + 캡션 조립 |
| `core/agent.py` | **수정** | 새 엔진 사용하도록 `_execute_cycle` 리팩터, 뉴스 쿼리 변경 |
| `main.py` | **수정** | Monologue 브랜드 테마 + 설정으로 교체 |
| `tests/test_context_engine.py` | **신규** | ContextEngine 단위 테스트 |
| `tests/test_psychological_engine.py` | **신규** | PsychologicalEngine 단위 테스트 |
| `tests/test_slide_generator.py` | **신규** | SlideGenerator 단위 테스트 |
| `tests/conftest.py` | **신규** | 공통 픽스처 (Mock Gemini, Mock weather) |

---

## Chunk 1: 테스트 인프라 + Context Engine

### Task 1: 테스트 환경 셋업

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: tests 디렉터리 생성 및 conftest 작성**

```python
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
```

- [ ] **Step 2: pytest 설정 파일 생성**

```ini
# pytest.ini
[pytest]
asyncio_mode = auto
testpaths = tests
```

- [ ] **Step 3: 커밋**

```bash
git add tests/__init__.py tests/conftest.py pytest.ini
git commit -m "test: 테스트 인프라 셋업 (conftest, pytest.ini)"
```

---

### Task 2: ContextEngine - 데이터 모델 정의

**Files:**
- Create: `core/context_engine.py`
- Create: `tests/test_context_engine.py`

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# tests/test_context_engine.py
import pytest
from core.context_engine import ContextData, WeatherData, NewsItem


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
```

- [ ] **Step 2: 테스트 실행 → 실패 확인**

```bash
pytest tests/test_context_engine.py -v
# Expected: FAIL - ImportError: cannot import name 'ContextData'
```

- [ ] **Step 3: 데이터 모델 구현**

```python
# core/context_engine.py
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
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
pytest tests/test_context_engine.py::test_weather_data_has_required_fields
pytest tests/test_context_engine.py::test_news_item_has_required_fields
pytest tests/test_context_engine.py::test_context_data_aggregates -v
# Expected: 3 passed
```

- [ ] **Step 5: 커밋**

```bash
git add core/context_engine.py tests/test_context_engine.py
git commit -m "feat: ContextData 데이터 모델 정의 (WeatherData, NewsItem, ContextData)"
```

---

### Task 3: ContextEngine - 날씨 수집 (Open-Meteo)

> Open-Meteo: `https://api.open-meteo.com/v1/forecast` — 무료, API 키 불필요
> 서울 기준 위도 37.5665, 경도 126.9780

- [ ] **Step 1: 날씨 수집 테스트 작성**

```python
# tests/test_context_engine.py 에 추가
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from core.context_engine import ContextEngine


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

    # 오류 시 기본값 반환
    assert weather is not None
    assert isinstance(weather.temperature, float)
```

- [ ] **Step 2: 테스트 실행 → 실패 확인**

```bash
pytest tests/test_context_engine.py::test_fetch_weather_returns_weather_data -v
# Expected: FAIL - ImportError: cannot import name 'ContextEngine'
```

- [ ] **Step 3: 날씨 수집 구현**

```python
# core/context_engine.py 에 추가 (import 포함)
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
    # 서울 기준
    LATITUDE = 37.5665
    LONGITUDE = 126.9780

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
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
pytest tests/test_context_engine.py -v
# Expected: 5 passed
```

- [ ] **Step 5: 커밋**

```bash
git add core/context_engine.py tests/test_context_engine.py
git commit -m "feat: Open-Meteo 날씨 수집 구현 (fetch_weather)"
```

---

### Task 4: ContextEngine - 뉴스 수집 (Monologue 키워드)

- [ ] **Step 1: 뉴스 수집 테스트 작성**

```python
# tests/test_context_engine.py 에 추가
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
```

- [ ] **Step 2: 테스트 실행 → 실패 확인**

```bash
pytest tests/test_context_engine.py::test_fetch_news_returns_news_items -v
# Expected: FAIL
```

- [ ] **Step 3: 뉴스 수집 구현**

```python
# core/context_engine.py 에 추가
from gnews import GNews
from typing import List


# ContextEngine 클래스에 추가:
    # Monologue 타겟 키워드: 3040 직장인의 현실을 반영하는 경제/사회 뉴스
    NEWS_QUERY = "직장인 번아웃 커리어 이직 워라밸 중년"
    NEWS_QUERY_EN = "burnout career work life balance workplace stress"

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
            gnews = GNews(max_results=10, period="1d", country="KR", language="ko")
            results = gnews.get_news(self.NEWS_QUERY)
            if not results:
                # 한국어 결과 없으면 영어로 폴백
                gnews_en = GNews(max_results=10, period="1d", country="US", language="en")
                results = gnews_en.get_news(self.NEWS_QUERY_EN)
            return results or []
        except Exception:
            return []
```

- [ ] **Step 4: 전체 컨텍스트 수집 메서드 추가**

```python
# ContextEngine 클래스에 추가:
    async def collect(self) -> ContextData:
        """날씨와 뉴스를 병렬로 수집하여 ContextData 반환"""
        weather, news_items = await asyncio.gather(
            self.fetch_weather(),
            self.fetch_news()
        )
        # 뉴스 제목에서 트렌드 키워드 추출 (간단 버전)
        trend_keywords = self._extract_keywords(news_items)
        return ContextData(weather=weather, news_items=news_items, trend_keywords=trend_keywords)

    def _extract_keywords(self, news_items: List[NewsItem]) -> List[str]:
        """뉴스 제목에서 심리/감정 관련 키워드 추출"""
        emotional_keywords = ["번아웃", "스트레스", "이직", "커리어", "워라밸",
                              "번아웃", "피로", "희망", "변화", "성장", "불안"]
        found = []
        all_text = " ".join(item.title + " " + item.summary for item in news_items)
        for kw in emotional_keywords:
            if kw in all_text and kw not in found:
                found.append(kw)
        return found[:5]
```

- [ ] **Step 5: 테스트 통과 확인**

```bash
pytest tests/test_context_engine.py -v
# Expected: all passed
```

- [ ] **Step 6: 커밋**

```bash
git add core/context_engine.py tests/test_context_engine.py
git commit -m "feat: ContextEngine 완성 (날씨+뉴스+트렌드 키워드 수집)"
```

---

## Chunk 2: Psychological Engine

### Task 5: PsychologicalEngine - 5슬라이드 텍스트 생성

**Files:**
- Create: `core/psychological_engine.py`
- Create: `tests/test_psychological_engine.py`

- [ ] **Step 1: 데이터 모델 테스트 작성**

```python
# tests/test_psychological_engine.py
import pytest
from core.psychological_engine import SlideContent, MonologueContent


def test_slide_content_has_required_fields():
    slide = SlideContent(
        page=1,
        role="Hook",
        text="오늘 당신의 이름은 직급 뒤에 숨어있지 않았나요?",
        image_prompt="minimalist empty office chair by window, soft morning light"
    )
    assert slide.page == 1
    assert slide.role == "Hook"
    assert len(slide.text) > 0
    assert len(slide.image_prompt) > 0


def test_monologue_content_has_five_slides():
    slides = [
        SlideContent(page=i, role=f"P{i}", text=f"텍스트{i}", image_prompt=f"프롬프트{i}")
        for i in range(1, 6)
    ]
    content = MonologueContent(slides=slides, instagram_caption="캡션", hashtags=["#모노로그"])
    assert len(content.slides) == 5
    assert content.instagram_caption == "캡션"
```

- [ ] **Step 2: 테스트 실행 → 실패 확인**

```bash
pytest tests/test_psychological_engine.py -v
# Expected: FAIL - ImportError
```

- [ ] **Step 3: 데이터 모델 구현**

```python
# core/psychological_engine.py
"""
Psychological Engine - Frankl 로고테라피 + 스토아 철학 기반 콘텐츠 생성
"""
from dataclasses import dataclass, field
from typing import List


@dataclass
class SlideContent:
    page: int           # 1-5
    role: str           # Hook / Context / Insight / Action / Outro
    text: str           # 슬라이드에 들어갈 텍스트
    image_prompt: str   # 이미지 생성용 프롬프트 (영어)


@dataclass
class MonologueContent:
    slides: List[SlideContent]
    instagram_caption: str
    hashtags: List[str] = field(default_factory=list)
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
pytest tests/test_psychological_engine.py -v
# Expected: 2 passed
```

- [ ] **Step 5: 커밋**

```bash
git add core/psychological_engine.py tests/test_psychological_engine.py
git commit -m "feat: SlideContent, MonologueContent 데이터 모델 정의"
```

---

### Task 6: PsychologicalEngine - AI 페르소나 + 슬라이드 생성

- [ ] **Step 1: 슬라이드 생성 테스트 작성**

```python
# tests/test_psychological_engine.py 에 추가
from unittest.mock import MagicMock, patch, AsyncMock
from core.psychological_engine import PsychologicalEngine
from core.context_engine import ContextData, WeatherData, NewsItem
import json


@pytest.fixture
def sample_context():
    return ContextData(
        weather=WeatherData(temperature=12.0, description="흐림", season="봄", weather_code=3),
        news_items=[
            NewsItem(title="직장인 번아웃 역대 최고", summary="스트레스 지수 상승"),
            NewsItem(title="40대 이직 급증", summary="커리어 전환 트렌드"),
        ],
        trend_keywords=["번아웃", "이직"]
    )


@pytest.mark.asyncio
async def test_generate_returns_five_slides(sample_context):
    mock_gemini = MagicMock()
    # Gemini가 반환할 JSON 구조
    mock_response_json = {
        "p1_hook": "오늘 당신의 이름은 직급 뒤에 숨어있지 않았나요?",
        "p2_context": "봄비가 내리는 월요일 아침, 번아웃이라는 단어가 뉴스를 가득 채웁니다.",
        "p3_insight": "프랭클은 말했습니다. 의미를 찾는 자는 어떤 상황도 견딜 수 있다고.",
        "p4_action": "오늘 퇴근 후 5분, 스스로에게 질문하세요: 내가 진짜 원하는 것은 무엇인가?",
        "p5_outro": "당신에게 '의미 있는 하루'란 어떤 모습인가요?",
        "instagram_caption": "오늘도 수고했습니다. 잠깐, 멈춰서 스스로에게 물어보세요.",
        "hashtags": ["#모노로그", "#직장인", "#번아웃"]
    }
    mock_response = MagicMock()
    mock_response.text = json.dumps(mock_response_json, ensure_ascii=False)
    mock_gemini.generate_content = MagicMock(return_value=mock_response)

    engine = PsychologicalEngine(content_analyzer=mock_gemini)
    content = await engine.generate(sample_context)

    assert len(content.slides) == 5
    assert content.slides[0].role == "Hook"
    assert content.slides[2].role == "Insight"
    assert content.slides[4].role == "Outro"
    assert len(content.instagram_caption) > 0


@pytest.mark.asyncio
async def test_generate_fallback_on_ai_error(sample_context):
    mock_gemini = MagicMock()
    mock_gemini.generate_content = MagicMock(side_effect=Exception("API error"))

    engine = PsychologicalEngine(content_analyzer=mock_gemini)
    content = await engine.generate(sample_context)

    # 폴백 콘텐츠도 5슬라이드 반환
    assert len(content.slides) == 5
```

- [ ] **Step 2: 테스트 실행 → 실패 확인**

```bash
pytest tests/test_psychological_engine.py -v
# Expected: FAIL - cannot import PsychologicalEngine
```

- [ ] **Step 3: PsychologicalEngine 구현**

```python
# core/psychological_engine.py 에 추가
import asyncio
import json
import google.generativeai as genai
from typing import Any


# 5슬라이드 역할 정의
SLIDE_ROLES = ["Hook", "Context", "Insight", "Action", "Outro"]

# 미니멀리즘 이미지 프롬프트 템플릿 (페이지별)
IMAGE_PROMPT_TEMPLATES = {
    "Hook": (
        "minimalist black and white photography, empty wooden chair near window, "
        "soft diffused morning light, shallow depth of field, negative space, "
        "contemplative mood, no people, fine art photography style"
    ),
    "Context": (
        "minimalist street photography, early morning empty city street, "
        "gentle rain reflections on pavement, muted tones, solitary atmosphere, "
        "documentary style, natural light, no text"
    ),
    "Insight": (
        "minimalist still life, single open book on wooden desk, "
        "warm sunlight through sheer curtain, dust particles in light, "
        "peaceful and philosophical mood, soft shadows, high contrast"
    ),
    "Action": (
        "minimalist nature photography, single path through misty forest, "
        "leading lines, soft morning fog, hopeful and forward-moving mood, "
        "green tones, serene atmosphere"
    ),
    "Outro": (
        "minimalist window photography, looking out to dawn sky, "
        "warm golden hour light, curtain gently moving, "
        "sense of possibility and new beginning, soft bokeh"
    ),
}

# 시스템 프롬프트: Monologue AI 페르소나
SYSTEM_PERSONA = """당신은 빅터 프랭클의 로고테라피 철학을 계승한 20년 경력의 시니어 커리어 코치입니다.
당신의 역할은 3040 직장인이 번아웃, 커리어 정체기, 관계의 피로감을 겪을 때
스토아 철학의 지혜와 의미치료의 통찰로 따뜻하고 실질적인 안내를 제공하는 것입니다.

말투: 1인칭 관찰자 시점, 따뜻하고 신뢰감 있는, 깊이 있는 통찰, 절제된 감성.
금지: 자극적 언어, 과장된 위로, 상업적 표현."""


class PsychologicalEngine:
    """Frankl 로고테라피 + 스토아 철학 기반 5슬라이드 콘텐츠 생성"""

    def __init__(self, content_analyzer: Any):
        self.analyzer = content_analyzer

    async def generate(self, context: "ContextData") -> MonologueContent:
        """컨텍스트 기반 5페이지 Monologue 콘텐츠 생성"""
        try:
            prompt = self._build_prompt(context)
            response = await asyncio.to_thread(
                self.analyzer.generate_content, prompt
            )
            return self._parse_response(response.text)
        except Exception:
            return self._fallback_content(context)

    def _build_prompt(self, context: "ContextData") -> str:
        news_summary = "\n".join(
            f"- {item.title}" for item in context.news_items[:3]
        )
        return f"""{SYSTEM_PERSONA}

오늘의 컨텍스트:
- 날씨: {context.weather.season} / {context.weather.description} / {context.weather.temperature}°C
- 오늘의 사회적 뉴스:
{news_summary}
- 대중 심리 키워드: {', '.join(context.trend_keywords)}

위 컨텍스트를 바탕으로 Instagram 5페이지 슬라이드 콘텐츠를 생성하세요.

각 페이지의 역할:
- P1 (Hook): 본질을 꿰뚫는 짧은 질문 (30자 이내)
- P2 (Context): 오늘의 뉴스+날씨+트렌드로 현재의 공기 묘사 (80자 이내)
- P3 (Insight): 프랭클/스토아 철학 기반 따뜻한 통찰 (100자 이내)
- P4 (Action): 오늘 당장 할 수 있는 아주 작고 구체적인 행동 1가지 (60자 이내)
- P5 (Outro): 팔로워와 소통할 개방형 질문 + "저장하고 오늘 밤 읽어보세요" CTA

반드시 아래 JSON 형식으로만 응답하세요 (다른 텍스트 없이):
{{
    "p1_hook": "...",
    "p2_context": "...",
    "p3_insight": "...",
    "p4_action": "...",
    "p5_outro": "...",
    "instagram_caption": "인스타그램 본문 캡션 (200자 이내)",
    "hashtags": ["#모노로그", "#직장인", ...]
}}"""

    def _parse_response(self, text: str) -> MonologueContent:
        """AI 응답 파싱 → MonologueContent 변환"""
        # 마크다운 코드 블록 제거
        clean = text.strip()
        if clean.startswith("```"):
            lines = clean.splitlines()
            clean = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])

        data = json.loads(clean)
        texts = [
            data["p1_hook"],
            data["p2_context"],
            data["p3_insight"],
            data["p4_action"],
            data["p5_outro"],
        ]
        slides = [
            SlideContent(
                page=i + 1,
                role=SLIDE_ROLES[i],
                text=texts[i],
                image_prompt=IMAGE_PROMPT_TEMPLATES[SLIDE_ROLES[i]]
            )
            for i in range(5)
        ]
        return MonologueContent(
            slides=slides,
            instagram_caption=data.get("instagram_caption", ""),
            hashtags=data.get("hashtags", ["#모노로그", "#직장인"])
        )

    def _fallback_content(self, context: "ContextData") -> MonologueContent:
        """AI 오류 시 기본 콘텐츠 반환"""
        fallback_texts = [
            "오늘 당신의 이름은 직급 뒤에 숨어있지 않았나요?",
            f"{context.weather.season}의 {context.weather.description} 속, 우리는 각자의 하루를 살아냅니다.",
            "프랭클은 말했습니다. 의미를 찾는 자는 어떤 상황도 견딜 수 있다고.",
            "오늘 퇴근 후 딱 5분, 핸드폰 없이 조용히 앉아보세요.",
            "오늘 하루, 어떤 순간이 가장 '나다운' 순간이었나요?"
        ]
        slides = [
            SlideContent(
                page=i + 1,
                role=SLIDE_ROLES[i],
                text=fallback_texts[i],
                image_prompt=IMAGE_PROMPT_TEMPLATES[SLIDE_ROLES[i]]
            )
            for i in range(5)
        ]
        return MonologueContent(
            slides=slides,
            instagram_caption="오늘도 수고했습니다. 잠깐 멈춰서 스스로를 돌아보세요.",
            hashtags=["#모노로그", "#직장인", "#번아웃", "#의미치료", "#스토아"]
        )
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
pytest tests/test_psychological_engine.py -v
# Expected: 4 passed
```

- [ ] **Step 5: 커밋**

```bash
git add core/psychological_engine.py tests/test_psychological_engine.py
git commit -m "feat: PsychologicalEngine 구현 (Frankl+Stoic 5슬라이드 생성)"
```

---

## Chunk 3: Slide Generator + Agent 통합

### Task 7: SlideGenerator - 슬라이드별 이미지 생성

**Files:**
- Create: `core/slide_generator.py`
- Create: `tests/test_slide_generator.py`

- [ ] **Step 1: 슬라이드 생성기 테스트 작성**

```python
# tests/test_slide_generator.py
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from core.psychological_engine import SlideContent, MonologueContent
from core.slide_generator import SlideGenerator


@pytest.fixture
def sample_monologue_content():
    slides = [
        SlideContent(page=1, role="Hook", text="오늘 당신은 누구였나요?",
                     image_prompt="empty chair window morning light"),
        SlideContent(page=2, role="Context", text="뉴스가 말하는 오늘",
                     image_prompt="rainy city street morning"),
        SlideContent(page=3, role="Insight", text="프랭클의 통찰",
                     image_prompt="open book desk sunlight"),
        SlideContent(page=4, role="Action", text="오늘의 작은 행동",
                     image_prompt="path through misty forest"),
        SlideContent(page=5, role="Outro", text="당신의 의미는?",
                     image_prompt="window dawn golden hour"),
    ]
    return MonologueContent(
        slides=slides,
        instagram_caption="오늘도 수고했습니다.",
        hashtags=["#모노로그"]
    )


@pytest.mark.asyncio
async def test_generate_images_returns_five_paths(sample_monologue_content, tmp_path):
    mock_generator = MagicMock()
    # generate는 async 메서드
    mock_generator.generate = AsyncMock(return_value=tmp_path / "test.jpg")

    generator = SlideGenerator(image_generator=mock_generator, output_dir=tmp_path)
    paths = await generator.generate_slide_images(sample_monologue_content)

    assert len(paths) == 5
    assert mock_generator.generate.call_count == 5


@pytest.mark.asyncio
async def test_generate_images_skips_failed_slides(sample_monologue_content, tmp_path):
    mock_generator = MagicMock()
    # 3번째 슬라이드는 None 반환 (실패)
    mock_generator.generate = AsyncMock(side_effect=[
        tmp_path / "s1.jpg",
        tmp_path / "s2.jpg",
        None,
        tmp_path / "s4.jpg",
        tmp_path / "s5.jpg",
    ])

    generator = SlideGenerator(image_generator=mock_generator, output_dir=tmp_path)
    paths = await generator.generate_slide_images(sample_monologue_content)

    # None 제외 4개 반환
    assert len(paths) == 4
```

- [ ] **Step 2: 테스트 실행 → 실패 확인**

```bash
pytest tests/test_slide_generator.py -v
# Expected: FAIL
```

- [ ] **Step 3: SlideGenerator 구현**

```python
# core/slide_generator.py
"""
Slide Generator - 5페이지 슬라이드 이미지 생성 및 조립
"""
import asyncio
from pathlib import Path
from typing import List, Optional

from core.image_generator import ImageGenerator
from core.psychological_engine import MonologueContent, SlideContent


class SlideGenerator:
    """MonologueContent의 각 슬라이드에 대한 이미지를 생성"""

    def __init__(self, image_generator: ImageGenerator, output_dir: Path):
        self.image_generator = image_generator
        self.output_dir = output_dir

    async def generate_slide_images(self, content: MonologueContent) -> List[Path]:
        """5개 슬라이드 이미지를 병렬 생성, 성공한 것만 반환"""
        tasks = [
            self._generate_one(slide)
            for slide in content.slides
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if isinstance(r, Path) and r is not None]

    async def _generate_one(self, slide: SlideContent) -> Optional[Path]:
        """슬라이드 1개 이미지 생성"""
        filename = f"slide_{slide.page:02d}_{slide.role.lower()}.jpg"
        output_path = self.output_dir / filename
        # 슬라이드 텍스트를 프롬프트에 결합
        full_prompt = (
            f"{slide.image_prompt}\n\n"
            f"Overlay text (Korean, minimal, centered): \"{slide.text}\"\n"
            f"Typography: clean sans-serif, white text, subtle dark gradient overlay"
        )
        return await self.image_generator.generate(full_prompt, output_path)
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
pytest tests/test_slide_generator.py -v
# Expected: 2 passed
```

- [ ] **Step 5: 커밋**

```bash
git add core/slide_generator.py tests/test_slide_generator.py
git commit -m "feat: SlideGenerator 구현 (5슬라이드 병렬 이미지 생성)"
```

---

### Task 8: Agent 통합 - `_execute_cycle` 리팩터

**Files:**
- Modify: `core/agent.py` (ContextEngine + PsychologicalEngine + SlideGenerator 사용)
- Modify: `main.py` (Monologue 브랜드 테마 + 설정)

- [ ] **Step 1: agent.py에 새 엔진 임포트 추가**

`core/agent.py` 상단 import 블록에 추가:

```python
from core.context_engine import ContextEngine
from core.psychological_engine import PsychologicalEngine
from core.slide_generator import SlideGenerator
```

- [ ] **Step 2: `AINewsAgent.__init__`에 새 엔진 초기화 추가**

`_init_ai_components` 메서드 내, Instagram 초기화 이후에 추가:

```python
# Monologue 엔진 초기화
self.context_engine = ContextEngine()
self.psychological_engine = PsychologicalEngine(
    content_analyzer=self.content_analyzer
)
self.slide_generator = SlideGenerator(
    image_generator=self.image_generator,
    output_dir=self.config.output_dir
)
```

- [ ] **Step 3: `_execute_cycle` 메서드 교체**

기존 `_execute_cycle`을 아래로 교체:

```python
async def _execute_cycle(self) -> None:
    """Monologue 5슬라이드 카루셀 한 사이클 실행"""
    # 1. 컨텍스트 수집 (날씨 + 뉴스)
    self.state = AgentState.COLLECTING
    context = await self.context_engine.collect()
    self.logger.info(
        f"Context: {context.weather.season}/{context.weather.description} "
        f"| 뉴스 {len(context.news_items)}건 | 키워드: {context.trend_keywords}"
    )

    # 2. 심리학적 5슬라이드 텍스트 생성
    self.state = AgentState.ANALYZING
    monologue = await self.psychological_engine.generate(context)
    self.logger.info(f"Hook: {monologue.slides[0].text[:30]}...")

    # 3. 슬라이드 이미지 생성
    self.state = AgentState.GENERATING
    image_paths = await self.slide_generator.generate_slide_images(monologue)
    if not image_paths:
        self.logger.warning("이미지 생성 실패 - 사이클 중단")
        return

    # 4. Instagram 카루셀 포스팅
    self.state = AgentState.POSTING
    caption = monologue.instagram_caption + "\n\n" + " ".join(monologue.hashtags)
    content = {"images": image_paths, "caption": caption}
    success = await self._post_content(content)

    if success:
        self.metrics.successful_posts += 1
        self.logger.info("Monologue 포스팅 성공")
    else:
        self.metrics.failed_posts += 1

    self.state = AgentState.IDLE
```

- [ ] **Step 4: `main.py` Monologue 브랜드 테마로 교체**

`main.py`의 `main()` 함수에서 theme 부분을 교체:

```python
# 기존 cyberpunk 테마를 Monologue 미니멀 테마로 교체
theme = BrandTheme(
    primary_color="#1A1A1A",       # 딥 차콜
    secondary_color="#F5F0E8",     # 아이보리 화이트
    accent_color="#8B7355",        # 웜 브라운
    background_color="#FAFAF8",    # 오프 화이트
    text_color="#2C2C2C",          # 소프트 블랙
    font_style="Noto Sans KR",
    visual_style="minimalist",
    content_tone="warm and philosophical"
)
```

그리고 config의 `name`을 변경:

```python
# load_agent_config의 default_config에서:
"name": "Monologue",
```

- [ ] **Step 5: 통합 테스트 (드라이런)**

```bash
# .env에 GEMINI_API_KEY 설정 후
python -c "
import asyncio
from core.context_engine import ContextEngine
asyncio.run(ContextEngine().collect())
print('ContextEngine OK')
"
```

Expected output:
```
ContextEngine OK
```

- [ ] **Step 6: 전체 테스트 실행**

```bash
pytest tests/ -v
# Expected: all passed
```

- [ ] **Step 7: 커밋**

```bash
git add core/agent.py main.py
git commit -m "feat: Agent를 Monologue 5슬라이드 카루셀 파이프라인으로 전환"
```

---

### Task 9: 최종 통합 검증

- [ ] **Step 1: 전체 테스트 스위트 실행**

```bash
pytest tests/ -v --tb=short
# Expected: 모든 테스트 통과
```

- [ ] **Step 2: 실제 API 연결 스모크 테스트**

```bash
# GEMINI_API_KEY가 있을 때만 실행
python -c "
import asyncio, os
from core.context_engine import ContextEngine
from core.psychological_engine import PsychologicalEngine
import google.generativeai as genai

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
analyzer = genai.GenerativeModel('gemini-1.5-flash')

async def smoke():
    ctx = await ContextEngine().collect()
    print('날씨:', ctx.weather.description, ctx.weather.temperature)
    print('뉴스:', len(ctx.news_items), '건')
    engine = PsychologicalEngine(analyzer)
    content = await engine.generate(ctx)
    print('P1 Hook:', content.slides[0].text)
    print('Caption:', content.instagram_caption[:50])

asyncio.run(smoke())
"
```

- [ ] **Step 3: 최종 커밋**

```bash
git add .
git commit -m "feat: Monologue Phase 1 완성 - AutoGram → 3040 직장인 심리 처방 서비스 전환"
```

---

## 실행 순서 요약

| # | Task | 핵심 산출물 |
|---|---|---|
| 1 | 테스트 환경 셋업 | `tests/conftest.py`, `pytest.ini` |
| 2 | ContextData 모델 | `WeatherData`, `NewsItem`, `ContextData` |
| 3 | 날씨 수집 | `fetch_weather()` with Open-Meteo |
| 4 | 뉴스 수집 | `fetch_news()` with GNews (한국 키워드) |
| 5 | SlideContent 모델 | `SlideContent`, `MonologueContent` |
| 6 | PsychologicalEngine | Frankl+Stoic AI 페르소나, 5슬라이드 생성 |
| 7 | SlideGenerator | 5슬라이드 병렬 이미지 생성 |
| 8 | Agent 통합 | `_execute_cycle` 교체, Monologue 테마 |
| 9 | 최종 검증 | 전체 테스트 + 스모크 테스트 |

## Phase 2 이후 메모 (이번 플랜 범위 외)

- **Threads API**: 텍스트 중심 배포 (`core/threads_publisher.py`)
- **Blog 변환**: 슬라이드 → 장문 포스팅 (`core/blog_converter.py`)
- **개인화 처방**: DM/댓글 기반 1:1 카드 (`core/personalization_engine.py`)
