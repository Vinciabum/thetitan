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


import asyncio
import json
from typing import Any


# 5슬라이드 역할 정의
SLIDE_ROLES = ["Hook", "Context", "Insight", "Action", "Outro"]

# 시네마틱 배경 이미지 프롬프트 (페이지별, 텍스트 없음)
IMAGE_PROMPT_TEMPLATES = {
    "Hook": (
        "cinematic moody photography, Korean office worker silhouette seen from behind, late evening, "
        "looking out floor-to-ceiling office window at city lights below, "
        "dark atmospheric, warm amber city glow, shallow depth of field, "
        "no text, no faces visible, fine art photography"
    ),
    "Context": (
        "cinematic street photography, empty subway platform late at night, Seoul Metro, "
        "warm tungsten light reflecting on wet floor tiles, "
        "solitary figure waiting in distance, atmospheric, moody, "
        "no text, dark tones with warm light pockets"
    ),
    "Insight": (
        "cinematic still photography, warm reading lamp light on wooden desk, "
        "open journal and pen, steaming cup of tea, soft bokeh background, "
        "cozy but contemplative mood, warm amber tones, "
        "no text visible, intimate and philosophical atmosphere"
    ),
    "Action": (
        "cinematic nature photography, lone person walking narrow path through misty bamboo forest at dawn, "
        "seen from behind, soft morning fog, hopeful forward motion, "
        "cool-to-warm tones, leading lines toward light, "
        "no text, serene and purposeful mood"
    ),
    "Outro": (
        "cinematic window photography, apartment window view of Seoul dawn skyline, "
        "warm golden hour light beginning to emerge, curtain softly blurred in foreground, "
        "sense of new beginning and quiet resolve, "
        "no text, soft glowing tones, peaceful atmosphere"
    ),
}

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
        clean = text.strip()
        if clean.startswith("```"):
            lines = clean.splitlines()
            start = 1
            end = len(lines) - 1 if lines[-1].startswith("```") else len(lines)
            clean = "\n".join(lines[start:end]).strip()

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
