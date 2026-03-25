# tests/test_dashboard_state.py
import pytest
import json
from pathlib import Path
from dashboard.state import load_state, save_state


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
