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


def test_monologue_content_default_hashtags():
    slides = [
        SlideContent(page=1, role="Hook", text="텍스트", image_prompt="프롬프트")
    ]
    content = MonologueContent(slides=slides, instagram_caption="캡션")
    assert isinstance(content.hashtags, list)


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
    mock_response_json = {
        "p1_hook": "오늘 당신의 이름은 직급 뒤에 숨어있지 않았나요?",
        "p2_context": "봄비가 내리는 월요일 아침, 번아웃이라는 단어가 뉴스를 가득 채웁니다.",
        "p3_insight": "프랭클은 말했습니다. 의미를 찾는 자는 어떤 상황도 견딜 수 있다고.",
        "p4_action": "오늘 퇴근 후 5분, 스스로에게 질문하세요: 내가 진짜 원하는 것은 무엇인가?",
        "p5_outro": "당신에게 의미 있는 하루란 어떤 모습인가요?",
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
    assert content.slides[1].role == "Context"
    assert content.slides[2].role == "Insight"
    assert content.slides[3].role == "Action"
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
    assert content.slides[0].role == "Hook"


@pytest.mark.asyncio
async def test_generate_handles_markdown_wrapped_json(sample_context):
    """AI가 JSON을 ```json ... ``` 으로 감싸서 반환하는 경우 처리"""
    mock_gemini = MagicMock()
    response_data = {
        "p1_hook": "질문",
        "p2_context": "맥락",
        "p3_insight": "통찰",
        "p4_action": "행동",
        "p5_outro": "마무리",
        "instagram_caption": "캡션",
        "hashtags": ["#태그"]
    }
    mock_response = MagicMock()
    mock_response.text = "```json\n" + json.dumps(response_data, ensure_ascii=False) + "\n```"
    mock_gemini.generate_content = MagicMock(return_value=mock_response)

    engine = PsychologicalEngine(content_analyzer=mock_gemini)
    content = await engine.generate(sample_context)

    assert len(content.slides) == 5
