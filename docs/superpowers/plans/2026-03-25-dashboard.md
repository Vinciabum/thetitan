# Monologue Dashboard Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Monologue 서비스를 관리하는 Streamlit 다크 미니멀 대시보드를 구현한다 — 콘텐츠 미리보기/자동 포스팅 타이머, 에이전트 모니터링, Instagram+Threads 설정 포함.

**Architecture:** `dashboard_state.json` 파일을 에이전트(main.py)와 대시보드(Streamlit) 간 공유 상태로 사용한다. 에이전트가 콘텐츠 생성 후 JSON에 저장하면 대시보드가 5초 폴링으로 읽어 미리보기를 표시하고 타이머 카운트다운 후 자동 포스팅한다. Streamlit 멀티페이지 구조 (pages/ 디렉터리) 사용.

**Tech Stack:** Python 3.9+, streamlit, streamlit-autorefresh, instagrapi (Instagram), requests (Threads API), pytest

---

## 파일 구조

| 파일 | 상태 | 역할 |
|---|---|---|
| `dashboard/__init__.py` | 신규 | 패키지 마커 |
| `dashboard/app.py` | 신규 | 메인 진입점, 다크 테마 CSS, 사이드바 |
| `dashboard/state.py` | 신규 | dashboard_state.json 읽기/쓰기, DashboardState 모델 |
| `dashboard/pages/01_preview.py` | 신규 | 콘텐츠 미리보기 + 자동 포스팅 타이머 |
| `dashboard/pages/02_monitor.py` | 신규 | 에이전트 상태 + 로그 |
| `dashboard/pages/03_settings.py` | 신규 | 플랫폼 설정 |
| `dashboard/components/__init__.py` | 신규 | 패키지 마커 |
| `dashboard/components/slide_card.py` | 신규 | 슬라이드 카드 HTML 렌더링 |
| `dashboard/components/status_badge.py` | 신규 | 에이전트 상태 뱃지 HTML |
| `core/threads_publisher.py` | 신규 | Threads API 포스팅 |
| `core/agent.py` | 수정 | 콘텐츠 생성 후 dashboard_state.json 저장 |
| `dashboard_state.json` | 신규 | 공유 상태 파일 (초기값) |
| `tests/test_dashboard_state.py` | 신규 | state.py 단위 테스트 |
| `tests/test_threads_publisher.py` | 신규 | ThreadsPublisher 단위 테스트 |

---

## Chunk 1: 상태 관리 기반 (State Foundation)

### Task 1: DashboardState 모델 + JSON 읽기/쓰기

**Files:**
- Create: `dashboard/__init__.py`
- Create: `dashboard/state.py`
- Create: `tests/test_dashboard_state.py`
- Create: `dashboard_state.json`

- [ ] **Step 1: 초기 dashboard_state.json 생성**

```json
{
  "agent_state": "idle",
  "last_run": null,
  "agent_log": [],
  "pending_content": null,
  "post_history": [],
  "settings": {
    "auto_post_delay_minutes": 30,
    "post_frequency": 3,
    "platforms": {
      "instagram": {"enabled": true},
      "threads": {"enabled": false},
      "blog": {"enabled": false}
    }
  }
}
```

파일 위치: `c:/Users/user/Desktop/autogram-main/dashboard_state.json`

- [ ] **Step 2: 실패하는 테스트 작성**

```python
# tests/test_dashboard_state.py
import pytest
import json
from pathlib import Path
from dashboard.state import DashboardState, load_state, save_state


def test_load_state_returns_default_when_missing(tmp_path):
    path = tmp_path / "state.json"
    state = load_state(path)
    assert state["agent_state"] == "idle"
    assert state["pending_content"] is None
    assert isinstance(state["post_history"], list)


def test_save_and_load_roundtrip(tmp_path):
    path = tmp_path / "state.json"
    data = {
        "agent_state": "collecting_news",
        "last_run": "2026-03-25T09:00:00",
        "agent_log": ["수집 시작"],
        "pending_content": None,
        "post_history": [],
        "settings": {
            "auto_post_delay_minutes": 15,
            "post_frequency": 3,
            "platforms": {
                "instagram": {"enabled": True},
                "threads": {"enabled": False},
                "blog": {"enabled": False}
            }
        }
    }
    save_state(data, path)
    loaded = load_state(path)
    assert loaded["agent_state"] == "collecting_news"
    assert loaded["settings"]["auto_post_delay_minutes"] == 15


def test_update_agent_state(tmp_path):
    path = tmp_path / "state.json"
    state = load_state(path)
    state["agent_state"] = "generating_content"
    save_state(state, path)
    reloaded = load_state(path)
    assert reloaded["agent_state"] == "generating_content"


def test_append_log(tmp_path):
    path = tmp_path / "state.json"
    state = load_state(path)
    state["agent_log"].append("테스트 로그")
    save_state(state, path)
    reloaded = load_state(path)
    assert "테스트 로그" in reloaded["agent_log"]
```

- [ ] **Step 3: 테스트 실행 → 실패 확인**

```bash
cd c:/Users/user/Desktop/autogram-main && python -m pytest tests/test_dashboard_state.py -v 2>&1 | tail -10
```
Expected: FAIL - ImportError: No module named 'dashboard'

- [ ] **Step 4: `dashboard/__init__.py` 및 `dashboard/state.py` 구현**

```python
# dashboard/__init__.py
# (empty)
```

```python
# dashboard/state.py
"""
대시보드 상태 관리 - dashboard_state.json 읽기/쓰기
"""
import json
from pathlib import Path
from typing import Any, Dict

STATE_PATH = Path(__file__).parent.parent / "dashboard_state.json"

DEFAULT_STATE: Dict[str, Any] = {
    "agent_state": "idle",
    "last_run": None,
    "agent_log": [],
    "pending_content": None,
    "post_history": [],
    "settings": {
        "auto_post_delay_minutes": 30,
        "post_frequency": 3,
        "platforms": {
            "instagram": {"enabled": True},
            "threads": {"enabled": False},
            "blog": {"enabled": False}
        }
    }
}


def load_state(path: Path = STATE_PATH) -> Dict[str, Any]:
    """JSON에서 상태 로드. 파일 없으면 기본값 반환."""
    if not path.exists():
        return dict(DEFAULT_STATE)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        # 기본값에 없는 키 보완
        for key, val in DEFAULT_STATE.items():
            if key not in data:
                data[key] = val
        return data
    except Exception:
        return dict(DEFAULT_STATE)


def save_state(state: Dict[str, Any], path: Path = STATE_PATH) -> None:
    """상태를 JSON 파일로 저장."""
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


# DashboardState는 dict 기반으로 충분 (Pydantic 불필요)
DashboardState = Dict[str, Any]
```

- [ ] **Step 5: 테스트 통과 확인**

```bash
cd c:/Users/user/Desktop/autogram-main && python -m pytest tests/test_dashboard_state.py -v 2>&1 | tail -10
```
Expected: 4 passed

- [ ] **Step 6: 커밋**

```bash
git add dashboard/__init__.py dashboard/state.py dashboard_state.json tests/test_dashboard_state.py
git commit -m "feat: DashboardState 모델 + JSON 읽기/쓰기 구현"
```

---

### Task 2: Agent → dashboard_state.json 연동

**Files:**
- Modify: `core/agent.py`

에이전트가 콘텐츠 생성 완료 후 `dashboard_state.json`에 pending_content를 저장하고, 포스팅 완료 후 post_history에 추가한다.

- [ ] **Step 1: `core/agent.py` 상단 import에 추가**

`core/agent.py`의 기존 import 블록 끝에 추가:

```python
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from dashboard.state import load_state, save_state, STATE_PATH
```

- [ ] **Step 2: `_execute_cycle` 메서드에 상태 저장 추가**

`_execute_cycle`에서 `monologue` 생성 직후, 이미지 생성 전에 아래 코드 추가:

```python
        # dashboard_state.json에 pending_content 저장
        self._save_pending_to_dashboard(monologue, context)
```

그리고 클래스에 새 메서드 추가:

```python
    def _save_pending_to_dashboard(self, monologue, context) -> None:
        """생성된 콘텐츠를 대시보드 상태에 저장"""
        try:
            state = load_state()
            state["agent_state"] = self._state.value
            state["last_run"] = datetime.now().isoformat()
            state["pending_content"] = {
                "slides": [
                    {
                        "page": s.page,
                        "role": s.role,
                        "text": s.text,
                        "image_prompt": s.image_prompt,
                        "image_path": None
                    }
                    for s in monologue.slides
                ],
                "instagram_caption": monologue.instagram_caption,
                "hashtags": monologue.hashtags,
                "image_paths": [],
                "created_at": datetime.now().isoformat()
            }
            save_state(state)
        except Exception as e:
            self.logger.warning(f"대시보드 상태 저장 실패: {e}")

    def _update_dashboard_after_post(self, success: bool, caption: str) -> None:
        """포스팅 완료 후 히스토리 업데이트"""
        try:
            state = load_state()
            state["agent_state"] = "idle"
            if state.get("pending_content"):
                history_item = {
                    "posted_at": datetime.now().isoformat(),
                    "caption": caption[:100],
                    "success": success,
                    "platforms": []
                }
                state["post_history"].insert(0, history_item)
                state["post_history"] = state["post_history"][:50]  # 최대 50개
                state["pending_content"] = None
            save_state(state)
        except Exception as e:
            self.logger.warning(f"대시보드 히스토리 저장 실패: {e}")
```

- [ ] **Step 3: `_execute_cycle`에서 포스팅 후 히스토리 저장 호출**

`_execute_cycle`의 `success = await self._post_content(content)` 이후:

```python
        self._update_dashboard_after_post(success, caption)
```

- [ ] **Step 4: 전체 테스트 실행 (기존 테스트 깨지지 않는지 확인)**

```bash
cd c:/Users/user/Desktop/autogram-main && python -m pytest tests/ -v 2>&1 | tail -15
```
Expected: 21 passed (기존 17 + 새 4)

- [ ] **Step 5: 커밋**

```bash
git add core/agent.py
git commit -m "feat: 에이전트가 콘텐츠 생성/포스팅 후 dashboard_state.json 업데이트"
```

---

### Task 3: ThreadsPublisher 구현

**Files:**
- Create: `core/threads_publisher.py`
- Create: `tests/test_threads_publisher.py`

> Threads API: Meta Graph API 사용. 토큰 없으면 skip.

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# tests/test_threads_publisher.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path
from core.threads_publisher import ThreadsPublisher


def test_threads_publisher_requires_token():
    """토큰 없으면 초기화는 되지만 publish는 False 반환"""
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
```

- [ ] **Step 2: 테스트 실행 → 실패 확인**

```bash
cd c:/Users/user/Desktop/autogram-main && python -m pytest tests/test_threads_publisher.py -v 2>&1 | tail -10
```
Expected: FAIL

- [ ] **Step 3: `core/threads_publisher.py` 구현**

```python
# core/threads_publisher.py
"""
Threads Publisher - Meta Threads API 포스팅
"""
import asyncio
import logging
from pathlib import Path
from typing import List, Optional

import aiohttp

logger = logging.getLogger(__name__)

THREADS_API_BASE = "https://graph.threads.net/v1.0"


class ThreadsPublisher:
    """Meta Threads API를 통한 포스팅"""

    def __init__(self, access_token: str, user_id: str):
        self.access_token = access_token
        self.user_id = user_id

    @property
    def is_configured(self) -> bool:
        return bool(self.access_token and self.user_id)

    async def publish(self, caption: str, image_paths: List[Path]) -> bool:
        """Threads에 텍스트 + 이미지 포스팅. 실패 시 False 반환."""
        if not self.is_configured:
            logger.warning("Threads 미설정 - 포스팅 건너뜀")
            return False

        try:
            # Step 1: 미디어 컨테이너 생성
            container_id = await self._create_container(caption, image_paths)
            if not container_id:
                return False

            # Step 2: 게시
            return await self._publish_container(container_id)

        except Exception as e:
            logger.error(f"Threads 포스팅 실패: {e}")
            return False

    async def _create_container(self, caption: str, image_paths: List[Path]) -> Optional[str]:
        """Threads 미디어 컨테이너 생성"""
        url = f"{THREADS_API_BASE}/{self.user_id}/threads"
        params = {
            "media_type": "TEXT",
            "text": caption,
            "access_token": self.access_token
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=params) as resp:
                if resp.status != 200:
                    logger.error(f"컨테이너 생성 실패: {resp.status}")
                    return None
                data = await resp.json()
                return data.get("id")

    async def _publish_container(self, container_id: str) -> bool:
        """생성된 컨테이너 게시"""
        url = f"{THREADS_API_BASE}/{self.user_id}/threads_publish"
        params = {
            "creation_id": container_id,
            "access_token": self.access_token
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=params) as resp:
                if resp.status != 200:
                    logger.error(f"게시 실패: {resp.status}")
                    return False
                data = await resp.json()
                return bool(data.get("id"))
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
cd c:/Users/user/Desktop/autogram-main && python -m pytest tests/test_threads_publisher.py -v 2>&1 | tail -10
```
Expected: 4 passed

- [ ] **Step 5: 커밋**

```bash
git add core/threads_publisher.py tests/test_threads_publisher.py
git commit -m "feat: ThreadsPublisher 구현 (Meta Threads API)"
```

---

## Chunk 2: 대시보드 UI 기반

### Task 4: 다크 테마 CSS + 메인 앱

**Files:**
- Create: `dashboard/app.py`

- [ ] **Step 1: streamlit 및 streamlit-autorefresh 설치 확인**

```bash
cd c:/Users/user/Desktop/autogram-main && pip install streamlit streamlit-autorefresh 2>&1 | tail -5
```

- [ ] **Step 2: `dashboard/app.py` 생성**

```python
# dashboard/app.py
"""
Monologue Dashboard - 메인 진입점
실행: streamlit run dashboard/app.py
"""
import streamlit as st

# 페이지 설정 (가장 먼저 호출해야 함)
st.set_page_config(
    page_title="Monologue",
    page_icon="🖤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 다크 미니멀 전역 CSS
DARK_CSS = """
<style>
    /* 전체 배경 */
    .stApp {
        background-color: #0F0F0F;
        color: #F5F0E8;
    }

    /* 사이드바 */
    [data-testid="stSidebar"] {
        background-color: #1A1A1A;
        border-right: 1px solid #2C2C2C;
    }

    /* 카드 스타일 */
    .monologue-card {
        background: #1A1A1A;
        border: 1px solid #2C2C2C;
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
    }

    .monologue-card-gold {
        background: #1A1A1A;
        border: 1px solid #C9A96E;
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
    }

    /* 타이머 */
    .timer-display {
        font-size: 48px;
        font-weight: 300;
        color: #C9A96E;
        text-align: center;
        letter-spacing: 4px;
        font-family: monospace;
    }

    /* 버튼 */
    .stButton > button {
        background: transparent;
        border: 1px solid #C9A96E;
        color: #C9A96E;
        border-radius: 8px;
        padding: 8px 24px;
        font-weight: 500;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background: #C9A96E;
        color: #0F0F0F;
    }

    /* 텍스트 색상 */
    h1, h2, h3, h4 { color: #F5F0E8 !important; }
    p, span, label { color: #F5F0E8; }
    .sub-text { color: #8B7355; font-size: 0.85rem; }

    /* 메트릭 */
    [data-testid="metric-container"] {
        background: #1A1A1A;
        border: 1px solid #2C2C2C;
        border-radius: 8px;
        padding: 12px;
    }

    /* 구분선 */
    hr { border-color: #2C2C2C; }

    /* 토글/체크박스 */
    .stCheckbox label { color: #F5F0E8 !important; }

    /* 입력 필드 */
    .stTextInput input, .stNumberInput input, .stTextArea textarea {
        background: #1A1A1A !important;
        border: 1px solid #2C2C2C !important;
        color: #F5F0E8 !important;
        border-radius: 8px;
    }

    /* 셀렉트박스 */
    .stSelectbox > div { background: #1A1A1A; }

    /* 성공/에러 */
    .success-text { color: #4CAF50; }
    .error-text { color: #E57373; }
    .gold-text { color: #C9A96E; }
</style>
"""

st.markdown(DARK_CSS, unsafe_allow_html=True)

# 사이드바 로고 + 네비게이션
with st.sidebar:
    st.markdown("""
    <div style="padding: 20px 0; text-align: center;">
        <h2 style="color: #C9A96E; letter-spacing: 4px; font-weight: 300;">MONOLOGUE</h2>
        <p style="color: #8B7355; font-size: 0.75rem;">당신의 고요한 독백의 시간</p>
    </div>
    <hr>
    """, unsafe_allow_html=True)

# 메인 홈 화면
st.markdown("""
<div style="text-align: center; padding: 60px 0;">
    <h1 style="font-weight: 200; letter-spacing: 6px; color: #F5F0E8;">MONOLOGUE</h1>
    <p style="color: #8B7355; font-size: 1.1rem;">당신의 소란스러운 하루 끝, 고요한 독백의 시간</p>
</div>
""", unsafe_allow_html=True)

from dashboard.state import load_state

state = load_state()
col1, col2, col3 = st.columns(3)

with col1:
    agent_state = state.get("agent_state", "idle")
    color = "#4CAF50" if agent_state == "idle" else "#C9A96E"
    st.markdown(f"""
    <div class="monologue-card">
        <p class="sub-text">에이전트 상태</p>
        <h3 style="color: {color};">● {agent_state.upper()}</h3>
    </div>
    """, unsafe_allow_html=True)

with col2:
    history = state.get("post_history", [])
    today_posts = len([h for h in history if h.get("posted_at", "")[:10] == __import__('datetime').date.today().isoformat()])
    st.markdown(f"""
    <div class="monologue-card">
        <p class="sub-text">오늘 포스팅</p>
        <h3 style="color: #F5F0E8;">{today_posts}회</h3>
    </div>
    """, unsafe_allow_html=True)

with col3:
    pending = state.get("pending_content")
    pending_status = "대기 중" if pending else "없음"
    pending_color = "#C9A96E" if pending else "#8B7355"
    st.markdown(f"""
    <div class="monologue-card">
        <p class="sub-text">대기 콘텐츠</p>
        <h3 style="color: {pending_color};">{pending_status}</h3>
    </div>
    """, unsafe_allow_html=True)

last_run = state.get("last_run")
if last_run:
    st.markdown(f'<p class="sub-text" style="text-align:center; margin-top: 20px;">마지막 실행: {last_run[:19].replace("T", " ")}</p>', unsafe_allow_html=True)
```

- [ ] **Step 3: 대시보드 실행 테스트**

```bash
cd c:/Users/user/Desktop/autogram-main && streamlit run dashboard/app.py --server.headless true &
sleep 3 && curl -s http://localhost:8501 | head -5
```
Expected: HTML 응답 수신

- [ ] **Step 4: 커밋**

```bash
git add dashboard/app.py
git commit -m "feat: Streamlit 다크 미니멀 메인 앱 + CSS 테마"
```

---

### Task 5: 슬라이드 카드 + 상태 뱃지 컴포넌트

**Files:**
- Create: `dashboard/components/__init__.py`
- Create: `dashboard/components/slide_card.py`
- Create: `dashboard/components/status_badge.py`

- [ ] **Step 1: `dashboard/components/__init__.py` 생성** (빈 파일)

- [ ] **Step 2: `dashboard/components/slide_card.py` 생성**

```python
# dashboard/components/slide_card.py
"""
슬라이드 카드 컴포넌트 - 5슬라이드 미리보기
"""
from pathlib import Path
from typing import Dict, Any, Optional
import streamlit as st
import base64


ROLE_LABELS = {
    "Hook": ("🎯", "훅"),
    "Context": ("🌍", "맥락"),
    "Insight": ("💡", "통찰"),
    "Action": ("✨", "행동"),
    "Outro": ("💬", "마무리"),
}


def render_slide_card(slide: Dict[str, Any], index: int) -> None:
    """슬라이드 1개 카드 렌더링"""
    role = slide.get("role", "")
    icon, label = ROLE_LABELS.get(role, ("📄", role))
    text = slide.get("text", "")
    image_path = slide.get("image_path")

    # 이미지 base64 인코딩 (있으면)
    img_html = ""
    if image_path and Path(image_path).exists():
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        img_html = f'<img src="data:image/jpeg;base64,{b64}" style="width:100%; border-radius:8px; margin-bottom:12px;">'
    else:
        # 플레이스홀더
        img_html = f"""
        <div style="width:100%; aspect-ratio:1; background:#2C2C2C; border-radius:8px;
             display:flex; align-items:center; justify-content:center; margin-bottom:12px;">
            <span style="font-size:2rem;">{icon}</span>
        </div>
        """

    st.markdown(f"""
    <div style="background:#1A1A1A; border:1px solid #2C2C2C; border-radius:12px;
         padding:16px; height:100%;">
        <p style="color:#8B7355; font-size:0.75rem; margin:0 0 8px 0;">
            P{index+1} · {icon} {label}
        </p>
        {img_html}
        <p style="color:#F5F0E8; font-size:0.9rem; line-height:1.6; margin:0;">
            {text}
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_five_slides(slides: list) -> None:
    """5슬라이드 가로 배열 렌더링"""
    if not slides:
        st.markdown('<p style="color:#8B7355; text-align:center;">생성된 슬라이드 없음</p>', unsafe_allow_html=True)
        return

    cols = st.columns(len(slides))
    for i, (col, slide) in enumerate(zip(cols, slides)):
        with col:
            render_slide_card(slide, i)
```

- [ ] **Step 3: `dashboard/components/status_badge.py` 생성**

```python
# dashboard/components/status_badge.py
"""
에이전트 상태 뱃지 컴포넌트
"""
import streamlit as st

STATE_CONFIG = {
    "idle":              {"color": "#4CAF50", "label": "대기 중",      "dot": "●"},
    "collecting_news":   {"color": "#C9A96E", "label": "뉴스 수집 중", "dot": "●"},
    "analyzing_content": {"color": "#C9A96E", "label": "분석 중",      "dot": "●"},
    "generating_content":{"color": "#2196F3", "label": "생성 중",      "dot": "●"},
    "posting_content":   {"color": "#9C27B0", "label": "포스팅 중",    "dot": "●"},
    "error":             {"color": "#E57373", "label": "오류",          "dot": "●"},
}


def render_status_badge(state: str) -> None:
    """에이전트 상태 뱃지 렌더링"""
    config = STATE_CONFIG.get(state, {"color": "#8B7355", "label": state, "dot": "●"})
    st.markdown(f"""
    <div style="display:inline-flex; align-items:center; gap:8px;
         background:#1A1A1A; border:1px solid #2C2C2C;
         border-radius:20px; padding:6px 16px;">
        <span style="color:{config['color']}; font-size:0.7rem;">{config['dot']}</span>
        <span style="color:#F5F0E8; font-size:0.85rem;">{config['label']}</span>
    </div>
    """, unsafe_allow_html=True)
```

- [ ] **Step 4: import 확인**

```bash
cd c:/Users/user/Desktop/autogram-main && python -c "
from dashboard.components.slide_card import render_five_slides
from dashboard.components.status_badge import render_status_badge
print('컴포넌트 import OK')
"
```
Expected: `컴포넌트 import OK`

- [ ] **Step 5: 커밋**

```bash
git add dashboard/components/__init__.py dashboard/components/slide_card.py dashboard/components/status_badge.py
git commit -m "feat: 슬라이드 카드 + 상태 뱃지 컴포넌트 구현"
```

---

## Chunk 3: 대시보드 페이지 구현

### Task 6: Page 1 - 콘텐츠 미리보기 + 자동 포스팅 타이머

**Files:**
- Create: `dashboard/pages/01_preview.py`

- [ ] **Step 1: `dashboard/pages/` 디렉터리 생성 및 파일 작성**

```python
# dashboard/pages/01_preview.py
"""
Page 1: 콘텐츠 미리보기 + 자동 포스팅 타이머
"""
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dashboard.state import load_state, save_state
from dashboard.components.slide_card import render_five_slides

st.set_page_config(page_title="미리보기 · Monologue", page_icon="📱", layout="wide")

# 다크 CSS (app.py와 동일)
st.markdown("""
<style>
.stApp { background-color: #0F0F0F; color: #F5F0E8; }
[data-testid="stSidebar"] { background-color: #1A1A1A; border-right: 1px solid #2C2C2C; }
h1, h2, h3 { color: #F5F0E8 !important; }
.stButton > button { background: transparent; border: 1px solid #C9A96E; color: #C9A96E; border-radius: 8px; }
.stButton > button:hover { background: #C9A96E; color: #0F0F0F; }
.stCheckbox label { color: #F5F0E8 !important; }
.stNumberInput input { background: #1A1A1A !important; border: 1px solid #2C2C2C !important; color: #F5F0E8 !important; }
[data-testid="metric-container"] { background: #1A1A1A; border: 1px solid #2C2C2C; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# 5초마다 자동 갱신
st_autorefresh(interval=5000, key="preview_refresh")

st.markdown("## 📱 콘텐츠 미리보기")
st.markdown('<hr style="border-color:#2C2C2C;">', unsafe_allow_html=True)

state = load_state()
pending = state.get("pending_content")

if not pending:
    st.markdown("""
    <div style="text-align:center; padding:80px 0;">
        <p style="color:#8B7355; font-size:1.1rem;">대기 중인 콘텐츠가 없습니다</p>
        <p style="color:#2C2C2C; font-size:0.85rem;">에이전트가 콘텐츠를 생성하면 여기에 표시됩니다</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# 콘텐츠 생성 시각
created_at = pending.get("created_at", "")
if created_at:
    st.markdown(f'<p style="color:#8B7355; font-size:0.85rem;">생성: {created_at[:19].replace("T", " ")}</p>', unsafe_allow_html=True)

# 5슬라이드 렌더링
render_five_slides(pending.get("slides", []))

st.markdown('<hr style="border-color:#2C2C2C; margin: 24px 0;">', unsafe_allow_html=True)

# 캡션 미리보기
with st.expander("📝 캡션 미리보기", expanded=False):
    caption = pending.get("instagram_caption", "")
    hashtags = " ".join(pending.get("hashtags", []))
    st.markdown(f"""
    <div style="background:#1A1A1A; border:1px solid #2C2C2C; border-radius:8px; padding:16px;">
        <p style="color:#F5F0E8; line-height:1.8;">{caption}</p>
        <p style="color:#8B7355;">{hashtags}</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<hr style="border-color:#2C2C2C; margin: 24px 0;">', unsafe_allow_html=True)

# --- 자동 포스팅 타이머 ---
st.markdown("### ⏱ 자동 포스팅 설정")

col_timer, col_platform = st.columns([1, 1])

with col_platform:
    st.markdown('<p style="color:#8B7355; font-size:0.85rem; margin-bottom:8px;">포스팅 플랫폼</p>', unsafe_allow_html=True)
    platforms = state.get("settings", {}).get("platforms", {})
    post_ig = st.checkbox("📸 Instagram", value=platforms.get("instagram", {}).get("enabled", True))
    post_threads = st.checkbox("🧵 Threads", value=platforms.get("threads", {}).get("enabled", False))

with col_timer:
    settings = state.get("settings", {})
    default_delay = settings.get("auto_post_delay_minutes", 30)
    delay_minutes = st.number_input(
        "자동 포스팅까지 대기 시간 (분)",
        min_value=1, max_value=1440,
        value=default_delay,
        step=1
    )

# 타이머 상태 관리
if "auto_post_at" not in st.session_state:
    st.session_state.auto_post_at = None
if "timer_started" not in st.session_state:
    st.session_state.timer_started = False

# 타이머 카운트다운 표시
if st.session_state.timer_started and st.session_state.auto_post_at:
    remaining = st.session_state.auto_post_at - datetime.now()
    if remaining.total_seconds() > 0:
        mins = int(remaining.total_seconds() // 60)
        secs = int(remaining.total_seconds() % 60)
        st.markdown(f"""
        <div style="text-align:center; padding:24px 0;">
            <p style="color:#8B7355; font-size:0.85rem; margin-bottom:8px;">자동 포스팅까지</p>
            <div style="font-size:56px; font-weight:300; color:#C9A96E;
                 font-family:monospace; letter-spacing:4px;">
                {mins:02d}:{secs:02d}
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # 타이머 만료 → 자동 포스팅
        st.session_state.timer_started = False
        st.session_state.auto_post_at = None
        st.markdown('<p style="color:#C9A96E; text-align:center;">🚀 자동 포스팅 실행 중...</p>', unsafe_allow_html=True)
        # 포스팅 실행 (동기 방식으로 단순화)
        _do_post(state, post_ig, post_threads)
        st.rerun()

# 버튼 행
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    if not st.session_state.timer_started:
        if st.button("⏱ 타이머 시작", use_container_width=True):
            st.session_state.auto_post_at = datetime.now() + timedelta(minutes=delay_minutes)
            st.session_state.timer_started = True
            # 설정 저장
            state["settings"]["auto_post_delay_minutes"] = delay_minutes
            save_state(state)
            st.rerun()
    else:
        if st.button("⏹ 타이머 중지", use_container_width=True):
            st.session_state.timer_started = False
            st.session_state.auto_post_at = None
            st.rerun()

with col2:
    if st.button("🚀 지금 바로 포스팅", use_container_width=True):
        st.session_state.timer_started = False
        _do_post(state, post_ig, post_threads)
        st.rerun()

with col3:
    if st.button("🗑 건너뛰기", use_container_width=True):
        st.session_state.timer_started = False
        state["pending_content"] = None
        save_state(state)
        st.success("건너뛰었습니다.")
        st.rerun()


def _do_post(state: dict, post_ig: bool, post_threads: bool) -> None:
    """실제 포스팅 실행 (동기 래퍼)"""
    import os
    from dotenv import load_dotenv
    load_dotenv()

    pending = state.get("pending_content", {})
    caption = pending.get("instagram_caption", "") + "\n\n" + " ".join(pending.get("hashtags", []))
    image_paths = [Path(p) for p in pending.get("image_paths", []) if Path(p).exists()]
    success_ig = False
    success_threads = False

    if post_ig:
        try:
            from instagrapi import Client
            ig = Client()
            ig.login(os.getenv("IG_USERNAME", ""), os.getenv("IG_PASSWORD", ""))
            if len(image_paths) > 1:
                ig.album_upload(image_paths, caption)
            elif len(image_paths) == 1:
                ig.photo_upload(image_paths[0], caption)
            success_ig = True
            st.success("✅ Instagram 포스팅 완료!")
        except Exception as e:
            st.error(f"Instagram 오류: {e}")

    if post_threads:
        try:
            from core.threads_publisher import ThreadsPublisher
            publisher = ThreadsPublisher(
                access_token=os.getenv("THREADS_ACCESS_TOKEN", ""),
                user_id=os.getenv("THREADS_USER_ID", "")
            )
            result = asyncio.run(publisher.publish(caption, image_paths))
            if result:
                success_threads = True
                st.success("✅ Threads 포스팅 완료!")
        except Exception as e:
            st.error(f"Threads 오류: {e}")

    # 히스토리 저장
    history_item = {
        "posted_at": datetime.now().isoformat(),
        "caption": caption[:100],
        "platforms": (["instagram"] if success_ig else []) + (["threads"] if success_threads else []),
        "success": success_ig or success_threads
    }
    state["post_history"].insert(0, history_item)
    state["post_history"] = state["post_history"][:50]
    state["pending_content"] = None
    save_state(state)
```

- [ ] **Step 2: 커밋**

```bash
git add dashboard/pages/01_preview.py
git commit -m "feat: 콘텐츠 미리보기 + 자동 포스팅 타이머 페이지"
```

---

### Task 7: Page 2 - 에이전트 모니터링

**Files:**
- Create: `dashboard/pages/02_monitor.py`

- [ ] **Step 1: `dashboard/pages/02_monitor.py` 생성**

```python
# dashboard/pages/02_monitor.py
"""
Page 2: 에이전트 상태 모니터링 + 로그
"""
import streamlit as st
from streamlit_autorefresh import st_autorefresh
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from dashboard.state import load_state, save_state
from dashboard.components.status_badge import render_status_badge

st.set_page_config(page_title="모니터링 · Monologue", page_icon="📊", layout="wide")

st.markdown("""
<style>
.stApp { background-color: #0F0F0F; color: #F5F0E8; }
[data-testid="stSidebar"] { background-color: #1A1A1A; border-right: 1px solid #2C2C2C; }
h1, h2, h3 { color: #F5F0E8 !important; }
.stButton > button { background: transparent; border: 1px solid #C9A96E; color: #C9A96E; border-radius: 8px; }
.stButton > button:hover { background: #C9A96E; color: #0F0F0F; }
[data-testid="metric-container"] { background: #1A1A1A; border: 1px solid #2C2C2C; border-radius: 8px; padding: 12px; }
</style>
""", unsafe_allow_html=True)

# 5초마다 자동 갱신
st_autorefresh(interval=5000, key="monitor_refresh")

st.markdown("## 📊 에이전트 모니터링")
st.markdown('<hr style="border-color:#2C2C2C;">', unsafe_allow_html=True)

state = load_state()

# 상태 뱃지
col_badge, col_time = st.columns([1, 2])
with col_badge:
    render_status_badge(state.get("agent_state", "idle"))
with col_time:
    last_run = state.get("last_run")
    if last_run:
        st.markdown(f'<p style="color:#8B7355; padding-top:8px;">마지막 실행: {last_run[:19].replace("T"," ")}</p>', unsafe_allow_html=True)

st.markdown('<br>', unsafe_allow_html=True)

# 메트릭
history = state.get("post_history", [])
from datetime import date
today = date.today().isoformat()
today_posts = [h for h in history if h.get("posted_at", "")[:10] == today]
success_count = len([h for h in history if h.get("success")])
total_count = len(history)
success_rate = f"{(success_count/total_count*100):.0f}%" if total_count > 0 else "N/A"

col1, col2, col3, col4 = st.columns(4)
col1.metric("오늘 포스팅", f"{len(today_posts)}회")
col2.metric("전체 포스팅", f"{total_count}회")
col3.metric("성공률", success_rate)
col4.metric("대기 콘텐츠", "있음" if state.get("pending_content") else "없음")

st.markdown('<hr style="border-color:#2C2C2C; margin:24px 0;">', unsafe_allow_html=True)

# 에이전트 제어
st.markdown("### 🎛 에이전트 제어")
col_start, col_stop, _ = st.columns([1, 1, 3])

with col_start:
    if st.button("▶ 에이전트 시작", use_container_width=True):
        try:
            subprocess.Popen(
                [sys.executable, "main.py"],
                cwd=str(Path(__file__).parent.parent.parent)
            )
            st.success("에이전트를 시작했습니다.")
        except Exception as e:
            st.error(f"시작 실패: {e}")

with col_stop:
    if st.button("⏹ 에이전트 중지", use_container_width=True):
        try:
            subprocess.run(["taskkill", "/F", "/IM", "python.exe"], capture_output=True)
            state["agent_state"] = "idle"
            save_state(state)
            st.success("에이전트를 중지했습니다.")
        except Exception as e:
            st.error(f"중지 실패: {e}")

st.markdown('<hr style="border-color:#2C2C2C; margin:24px 0;">', unsafe_allow_html=True)

# 로그
st.markdown("### 📋 최근 포스팅 기록")
if history:
    for item in history[:10]:
        posted_at = item.get("posted_at", "")[:19].replace("T", " ")
        success = item.get("success", False)
        platforms = ", ".join(item.get("platforms", []))
        caption = item.get("caption", "")[:60]
        color = "#4CAF50" if success else "#E57373"
        icon = "✅" if success else "❌"
        st.markdown(f"""
        <div style="background:#1A1A1A; border:1px solid #2C2C2C; border-radius:8px;
             padding:12px 16px; margin-bottom:8px; display:flex; align-items:center; gap:12px;">
            <span style="font-size:1rem;">{icon}</span>
            <div style="flex:1;">
                <p style="color:#F5F0E8; margin:0; font-size:0.9rem;">{caption}...</p>
                <p style="color:#8B7355; margin:0; font-size:0.75rem;">{posted_at} · {platforms}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.markdown('<p style="color:#8B7355; text-align:center; padding:40px 0;">포스팅 기록 없음</p>', unsafe_allow_html=True)
```

- [ ] **Step 2: 커밋**

```bash
git add dashboard/pages/02_monitor.py
git commit -m "feat: 에이전트 모니터링 페이지 구현"
```

---

### Task 8: Page 3 - 설정

**Files:**
- Create: `dashboard/pages/03_settings.py`

- [ ] **Step 1: `dashboard/pages/03_settings.py` 생성**

```python
# dashboard/pages/03_settings.py
"""
Page 3: 플랫폼 설정
"""
import streamlit as st
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from dashboard.state import load_state, save_state

st.set_page_config(page_title="설정 · Monologue", page_icon="⚙️", layout="wide")

st.markdown("""
<style>
.stApp { background-color: #0F0F0F; color: #F5F0E8; }
[data-testid="stSidebar"] { background-color: #1A1A1A; border-right: 1px solid #2C2C2C; }
h1, h2, h3 { color: #F5F0E8 !important; }
.stButton > button { background: transparent; border: 1px solid #C9A96E; color: #C9A96E; border-radius: 8px; }
.stButton > button:hover { background: #C9A96E; color: #0F0F0F; }
.stTextInput input, .stNumberInput input { background: #1A1A1A !important; border: 1px solid #2C2C2C !important; color: #F5F0E8 !important; border-radius: 8px; }
.stCheckbox label { color: #F5F0E8 !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("## ⚙️ 설정")
st.markdown('<hr style="border-color:#2C2C2C;">', unsafe_allow_html=True)

state = load_state()
settings = state.get("settings", {})

# .env 파일 경로
env_path = Path(__file__).parent.parent.parent / ".env"

def read_env() -> dict:
    env = {}
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env

def write_env(env: dict) -> None:
    lines = [f"{k}={v}" for k, v in env.items()]
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

env = read_env()

# --- AI 설정 ---
st.markdown("### 🤖 AI 설정")
gemini_key = st.text_input(
    "Gemini API Key",
    value=env.get("GEMINI_API_KEY", ""),
    type="password"
)

st.markdown('<hr style="border-color:#2C2C2C; margin:24px 0;">', unsafe_allow_html=True)

# --- Instagram ---
st.markdown("### 📸 Instagram")
col1, col2 = st.columns(2)
with col1:
    ig_username = st.text_input("사용자명", value=env.get("IG_USERNAME", ""))
with col2:
    ig_password = st.text_input("비밀번호", value=env.get("IG_PASSWORD", ""), type="password")

ig_enabled = st.checkbox(
    "Instagram 포스팅 활성화",
    value=settings.get("platforms", {}).get("instagram", {}).get("enabled", True)
)

st.markdown('<hr style="border-color:#2C2C2C; margin:24px 0;">', unsafe_allow_html=True)

# --- Threads ---
st.markdown("### 🧵 Threads")
col3, col4 = st.columns(2)
with col3:
    threads_token = st.text_input("Access Token", value=env.get("THREADS_ACCESS_TOKEN", ""), type="password")
with col4:
    threads_user_id = st.text_input("User ID", value=env.get("THREADS_USER_ID", ""))

threads_enabled = st.checkbox(
    "Threads 포스팅 활성화",
    value=settings.get("platforms", {}).get("threads", {}).get("enabled", False)
)

st.markdown('<hr style="border-color:#2C2C2C; margin:24px 0;">', unsafe_allow_html=True)

# --- 블로그 (Coming Soon) ---
st.markdown("### 📝 블로그")
st.markdown("""
<div style="background:#1A1A1A; border:1px dashed #2C2C2C; border-radius:12px;
     padding:24px; text-align:center;">
    <p style="color:#8B7355; font-size:0.9rem; margin:0;">Coming Soon</p>
    <p style="color:#2C2C2C; font-size:0.8rem; margin:4px 0 0 0;">Phase 2에서 네이버/블로그 포스팅이 추가될 예정입니다</p>
</div>
""", unsafe_allow_html=True)

st.markdown('<hr style="border-color:#2C2C2C; margin:24px 0;">', unsafe_allow_html=True)

# --- 에이전트 설정 ---
st.markdown("### 🕐 에이전트 설정")
post_frequency = st.number_input(
    "하루 포스팅 횟수",
    min_value=1, max_value=24,
    value=settings.get("post_frequency", 3)
)
auto_delay = st.number_input(
    "자동 포스팅 기본 대기 시간 (분)",
    min_value=1, max_value=1440,
    value=settings.get("auto_post_delay_minutes", 30)
)

st.markdown('<br>', unsafe_allow_html=True)

# 저장 버튼
if st.button("💾 설정 저장", use_container_width=False):
    # .env 업데이트
    env.update({
        "GEMINI_API_KEY": gemini_key,
        "IG_USERNAME": ig_username,
        "IG_PASSWORD": ig_password,
        "THREADS_ACCESS_TOKEN": threads_token,
        "THREADS_USER_ID": threads_user_id,
    })
    write_env(env)

    # dashboard_state.json 설정 업데이트
    state["settings"]["post_frequency"] = post_frequency
    state["settings"]["auto_post_delay_minutes"] = auto_delay
    state["settings"]["platforms"]["instagram"]["enabled"] = ig_enabled
    state["settings"]["platforms"]["threads"]["enabled"] = threads_enabled
    save_state(state)

    st.success("✅ 설정이 저장되었습니다.")
```

- [ ] **Step 2: 커밋**

```bash
git add dashboard/pages/03_settings.py
git commit -m "feat: 플랫폼 설정 페이지 구현 (IG, Threads, Coming Soon 블로그)"
```

---

### Task 9: requirements.txt 업데이트 + 최종 검증

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: requirements.txt에 신규 패키지 추가**

`requirements.txt`를 읽고 아래 패키지가 없으면 추가:

```
streamlit>=1.32.0
streamlit-autorefresh>=1.0.1
```

- [ ] **Step 2: 설치 확인**

```bash
cd c:/Users/user/Desktop/autogram-main && pip install streamlit streamlit-autorefresh 2>&1 | tail -3
```

- [ ] **Step 3: 전체 테스트 실행**

```bash
cd c:/Users/user/Desktop/autogram-main && python -m pytest tests/ -v 2>&1 | tail -15
```
Expected: 25 passed (기존 17 + dashboard 4 + threads 4)

- [ ] **Step 4: 대시보드 실행 최종 확인**

```bash
cd c:/Users/user/Desktop/autogram-main && streamlit run dashboard/app.py
```
브라우저에서 `http://localhost:8501` 접속 확인

- [ ] **Step 5: 최종 커밋**

```bash
git add requirements.txt
git commit -m "feat: Monologue Dashboard Phase 1 완성 - Streamlit 다크 미니멀 대시보드"
```

---

## 실행 순서 요약

| # | Task | 핵심 산출물 |
|---|---|---|
| 1 | State 기반 | `dashboard/state.py`, `dashboard_state.json` |
| 2 | Agent 연동 | `core/agent.py` → JSON 저장 |
| 3 | ThreadsPublisher | `core/threads_publisher.py` |
| 4 | 메인 앱 + CSS | `dashboard/app.py` 다크 테마 |
| 5 | 컴포넌트 | `slide_card.py`, `status_badge.py` |
| 6 | Page 1: 미리보기 | 5슬라이드 + 타이머 + 포스팅 |
| 7 | Page 2: 모니터링 | 상태 + 로그 + 에이전트 제어 |
| 8 | Page 3: 설정 | IG + Threads + Coming Soon 블로그 |
| 9 | 최종 검증 | requirements.txt, 전체 테스트 |
