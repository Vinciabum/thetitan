# AutoGram 파이프라인 아키텍처

> 주제 선정 → 콘텐츠 변환 → 이미지 생성 → 게시 전 과정 설명

---

## 1. 주제는 어디서 오는가

`core/context_engine.py` 가 매일 3가지 소스에서 데이터를 수집한다.

| 소스 | 방법 | 현재 설정 |
|------|------|-----------|
| 날씨 | Open-Meteo API | 서울 (위도 37.5665, 경도 126.9780) |
| 뉴스 | GNews API | `"직장인 번아웃 커리어 이직 워라밸 중년"` |
| 트렌드 키워드 | 뉴스 헤드라인에서 추출 | `["번아웃", "스트레스", "이직", "커리어", "워라밸", "피로", "희망", "변화", "성장", "불안"]` |

이 3개를 합쳐 `DailyContext` 객체를 만들고 AI에게 넘긴다.

**주제를 바꾸려면**: `NEWS_QUERY` 한 줄만 수정하면 된다.

```python
# context_engine.py
NEWS_QUERY = "직장인 번아웃 커리어 이직 워라밸 중년"  # ← 이 줄만 바꾸면 됨
```

---

## 2. 어떻게 콘텐츠로 변환되는가

`core/psychological_engine.py` 의 `_build_prompt()` 가 핵심이다.

```
DailyContext (날씨 + 뉴스 헤드라인 + 트렌드 키워드)
        ↓
SYSTEM_PERSONA (계정의 철학 / 말투 / 정체성)
        ↓
Gemini AI 프롬프트 조합
        ↓
JSON 출력: {
    p1_hook,
    p2_text ~ p5_text,
    p1_image ~ p5_image,
    caption,
    hashtags
}
```

- **컨텍스트** → 오늘 어떤 상황인지 (뉴스, 날씨, 트렌드)
- **페르소나** → 그 상황을 어떤 철학과 말투로 해석할지

---

## 3. 이미지 프롬프트는 어떻게 만들어지는가

두 단계로 구성된다.

### 3-1. 스타일 기반 (고정)

```python
# psychological_engine.py
IMAGE_STYLE_BASE = (
    "black and white vintage film photography, "
    "1960s artistic portrait style, soft film grain, high contrast shadows, "
    "no text, no logos, cinematic still photography, introspective mood"
)
```

이 부분이 **비주얼 아이덴티티**를 고정한다. 모든 슬라이드 이미지에 공통 적용.

### 3-2. 장면 묘사 (AI가 동적 생성)

```
슬라이드 텍스트: "오늘도 마감을 앞두고 커피를 홀짝이는 당신..."
        ↓
AI가 장면 생성: "office worker sitting alone at desk, window light, late night"
        ↓
최종 프롬프트 = AI 장면 묘사 + IMAGE_STYLE_BASE
```

슬라이드마다 다른 장면을 묘사하되, 스타일은 항상 B&W 빈티지로 통일된다.

---

## 4. Soul / Identity — 어디 있고 어떻게 바꾸는가

### 현재 위치

`core/psychological_engine.py` 상단의 두 상수에 하드코딩되어 있다.

```python
SYSTEM_PERSONA = """당신은 빅터 프랭클의 로고테라피 철학을 계승한 20년 경력의 시니어 커리어 코치입니다.
당신의 역할은 3040 직장인이 번아웃, 커리어 정체기, 관계의 피로감을 겪을 때
스토아 철학의 지혜와 의미치료의 통찰로 따뜻하고 실질적인 안내를 제공하는 것입니다.
말투: 1인칭 관찰자 시점, 따뜻하고 신뢰감 있는, 깊이 있는 통찰, 절제된 감성.
금지: 자극적 언어, 과장된 위로, 상업적 표현."""

IMAGE_STYLE_BASE = "black and white vintage film photography, ..."
```

### 현재 문제

코드에 직접 박혀 있어서 수정하려면 파이썬 파일을 열어야 한다.

### 향후 개선 가능 방향 (config.json 분리)

```json
{
  "identity": {
    "persona": "당신은 ...",
    "image_style": "black and white vintage ...",
    "target_audience": "3040 직장인",
    "core_values": ["번아웃 회복", "의미 발견", "실용적 지혜"]
  },
  "context": {
    "news_query": "직장인 번아웃 커리어 이직",
    "city_lat": 37.5665,
    "city_lon": 126.9780
  }
}
```

이렇게 분리하면 같은 코드베이스로 `config.json` 하나만 바꿔서 완전히 다른 계정 정체성의 봇을 운용할 수 있다.

---

## 전체 요약

| 요소 | 위치 | 변경 난이도 |
|------|------|------------|
| 뉴스 주제 | `context_engine.py` — `NEWS_QUERY` | 한 줄 수정 |
| 대상 도시/날씨 | `context_engine.py` — `LATITUDE`, `LONGITUDE` | 한 줄 수정 |
| 계정 말투/철학 | `psychological_engine.py` — `SYSTEM_PERSONA` | 현재 하드코딩, config 분리 가능 |
| 비주얼 스타일 | `psychological_engine.py` — `IMAGE_STYLE_BASE` | 현재 하드코딩, config 분리 가능 |
| 슬라이드 이미지 장면 | AI 동적 생성 (슬라이드 텍스트 기반) | 자동, 수정 불필요 |

---

## 다른 주제/계정으로 확장할 때 바꿀 것들

1. `NEWS_QUERY` → 새 주제 키워드
2. `SYSTEM_PERSONA` → 새 계정의 철학, 말투, 타겟
3. `IMAGE_STYLE_BASE` → 원하는 비주얼 스타일 (컬러, 무드 등)
4. `.env` → 새 인스타그램/쓰레드 계정 토큰

코드 나머지는 건드릴 필요 없다.
