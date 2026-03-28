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

# 기본 이미지 스타일 지시 (모든 슬라이드 공통 — AI가 내용에 맞게 장면을 결정)
IMAGE_STYLE_BASE = (
    "black and white vintage film photography, "
    "1960s artistic portrait style, soft film grain, high contrast shadows, "
    "no text, no logos, cinematic still photography, introspective mood"
)

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

- P1 (Hook): 스크롤을 멈추게 하는 짧고 강렬한 문장. 반드시 2~3개의 짧은 어절로 끊어서 작성.
  예시: "오늘도\n버텨낸 것만으로\n충분합니다." 또는 "퇴근 후\n아무 생각도\n하기 싫다면."
  규칙: 한 줄에 7~10자, 총 2~3줄, 줄바꿈은 \n으로 표시. 질문형보다 선언형 우선.

- P2~P5: 반드시 "소제목\n\n본문" 형식으로 작성 (JSON 문자열 안에서 \n\n 그대로 사용).
  소제목: 슬라이드 핵심을 담은 짧은 문장 (10~18자, Bold 대형으로 표시됨)
  본문: 소제목에 대한 깊이 있는 설명 2~3문장 (80~120자, 작은 Regular로 표시됨)
  예시: "공허함에 이름 붙이기\n\n오늘의 무거움에 이름을 붙이면, 그것은 더 이상 막연한 두려움이 아닙니다. 의미를 찾는 첫 걸음은 지금 이 감정을 인정하는 데서 시작됩니다."

- P2 (Context): 소제목 + 오늘의 뉴스·날씨·트렌드를 반영한 현재의 공기 묘사
- P3 (Insight): 소제목 + 프랭클/스토아 철학 기반 따뜻한 통찰
- P4 (Action): 소제목 + 오늘 당장 할 수 있는 아주 작고 구체적인 행동 1가지
- P5 (Outro): 팔로워 모두가 공감할 수 있는 짧고 울림 있는 질문 하나만. 소제목 없이 질문 문장만 작성. 2줄 이내, 줄바꿈은 \n 사용. 예시: "오늘 하루,\n당신의 감정은 안녕했나요?"

instagram_caption 작성 규칙 (아래 4파트를 이어서 하나의 문자열로):
  파트1: 오늘 Hook과 연결된 공감 문장 1줄 (직장인/번아웃/퇴근 키워드 자연 포함)
  파트2: 오늘 날씨·상황 반영 감성 문장 2줄
  파트3: "📌 저장해두고 오늘 밤 꺼내 읽어보세요 🤍" (고정)
  파트4: 오늘 주제와 연결된 개방형 질문 + "댓글로 나눠봐요."

hashtags 규칙: 정확히 5개. #모노로그와 #직장인은 반드시 포함. 나머지 3개는 오늘 주제/날씨/철학에 맞게 선택.

이미지 프롬프트 규칙 (p1_image ~ p5_image):
- 각 슬라이드 텍스트 내용과 감정에 맞는 구체적인 장면을 영어로 묘사
- 스타일 고정: "black and white vintage film photography, 1960s style, soft film grain, no text"
- 매 슬라이드마다 다른 장면 (인물/장소/상황/구도 모두 다양하게)
- 텍스트 주제와 감정적으로 연결되는 장면 선택

반드시 아래 JSON 형식으로만 응답하세요 (다른 텍스트 없이):
{{
    "p1_hook": "...",
    "p1_image": "black and white vintage film photography, [내용에 맞는 구체적 장면], 1960s style, soft film grain, no text",
    "p2_context": "소제목\\n\\n본문",
    "p2_image": "black and white vintage film photography, [내용에 맞는 구체적 장면], 1960s style, soft film grain, no text",
    "p3_insight": "소제목\\n\\n본문",
    "p3_image": "black and white vintage film photography, [내용에 맞는 구체적 장면], 1960s style, soft film grain, no text",
    "p4_action": "소제목\\n\\n본문",
    "p4_image": "black and white vintage film photography, [내용에 맞는 구체적 장면], 1960s style, soft film grain, no text",
    "p5_outro": "질문 문장 (2줄 이내, \\n으로 줄바꿈)",
    "p5_image": "black and white vintage film photography, [내용에 맞는 구체적 장면], 1960s style, soft film grain, no text",
    "instagram_caption": "...",
    "hashtags": ["#모노로그", "#직장인", "#태그3", "#태그4", "#태그5"]
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
        image_keys = ["p1_image", "p2_image", "p3_image", "p4_image", "p5_image"]
        slides = [
            SlideContent(
                page=i + 1,
                role=SLIDE_ROLES[i],
                text=texts[i],
                image_prompt=data.get(image_keys[i], IMAGE_STYLE_BASE)
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
            "오늘 당신의 이름은\n직급 뒤에\n숨어있지 않았나요?",
            f"오늘의 공기\n\n{context.weather.season}의 {context.weather.description} 속, 우리는 각자의 하루를 버텨냅니다. 모두가 달려가는 사이, 당신의 속도는 어떤가요?",
            "의미를 찾는 힘\n\n프랭클은 말했습니다. 의미를 찾는 자는 어떤 상황도 견딜 수 있다고. 오늘의 피로도 당신의 이야기입니다.",
            "딱 5분만\n\n오늘 퇴근 후, 핸드폰을 내려두세요. 조용히 앉아 오늘 가장 '나다운' 순간을 하나 떠올려보세요.",
            "당신의 이야기\n\n오늘 하루, 어떤 순간이 가장 힘들었나요? 댓글로 나눠봐요."
        ]
        fallback_images = [
            f"{IMAGE_STYLE_BASE}, tired office worker silhouette at large window overlooking city at night, seen from behind",
            f"{IMAGE_STYLE_BASE}, empty subway platform late at night, solitary figure in distance, reflections on wet floor",
            f"{IMAGE_STYLE_BASE}, woman reading a book at wooden desk under warm lamp, contemplative and serene",
            f"{IMAGE_STYLE_BASE}, lone person walking narrow path through misty forest at dawn, seen from behind, hopeful",
            f"{IMAGE_STYLE_BASE}, woman silhouette at apartment window, soft morning light, quiet resolve",
        ]
        slides = [
            SlideContent(
                page=i + 1,
                role=SLIDE_ROLES[i],
                text=fallback_texts[i],
                image_prompt=fallback_images[i]
            )
            for i in range(5)
        ]
        return MonologueContent(
            slides=slides,
            instagram_caption="오늘도 수고했습니다. 잠깐 멈춰서 스스로를 돌아보세요.",
            hashtags=["#모노로그", "#직장인", "#번아웃", "#의미치료", "#스토아"]
        )
