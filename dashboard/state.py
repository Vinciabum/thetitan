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
        for key, val in DEFAULT_STATE.items():
            if key not in data:
                data[key] = val
        return data
    except Exception:
        return dict(DEFAULT_STATE)


def save_state(state: Dict[str, Any], path: Path = STATE_PATH) -> None:
    """상태를 JSON 파일로 저장."""
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


DashboardState = Dict[str, Any]
