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
.stTextInput input, .stNumberInput input {
    background: #1A1A1A !important; border: 1px solid #2C2C2C !important;
    color: #F5F0E8 !important; border-radius: 8px;
}
.stCheckbox label { color: #F5F0E8 !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("## ⚙️ 설정")
st.markdown('<hr style="border-color:#2C2C2C;">', unsafe_allow_html=True)

state = load_state()
settings = state.get("settings", {})

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

# AI 설정
st.markdown("### 🤖 AI 설정")
gemini_key = st.text_input("Gemini API Key", value=env.get("GEMINI_API_KEY", ""), type="password")

st.markdown('<hr style="border-color:#2C2C2C; margin:24px 0;">', unsafe_allow_html=True)

# Instagram
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

# Threads
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

# 블로그 Coming Soon
st.markdown("### 📝 블로그")
st.markdown("""
<div style="background:#1A1A1A; border:1px dashed #2C2C2C; border-radius:12px;
     padding:24px; text-align:center;">
    <p style="color:#8B7355; font-size:0.9rem; margin:0;">Coming Soon</p>
    <p style="color:#2C2C2C; font-size:0.8rem; margin:4px 0 0 0;">Phase 2에서 네이버/블로그 포스팅이 추가될 예정입니다</p>
</div>
""", unsafe_allow_html=True)

st.markdown('<hr style="border-color:#2C2C2C; margin:24px 0;">', unsafe_allow_html=True)

# 에이전트 설정
st.markdown("### 🕐 에이전트 설정")
post_frequency = st.number_input("하루 포스팅 횟수", min_value=1, max_value=24, value=settings.get("post_frequency", 3))
auto_delay = st.number_input("자동 포스팅 기본 대기 시간 (분)", min_value=1, max_value=1440, value=settings.get("auto_post_delay_minutes", 30))

st.markdown('<br>', unsafe_allow_html=True)

if st.button("💾 설정 저장"):
    env.update({
        "GEMINI_API_KEY": gemini_key,
        "IG_USERNAME": ig_username,
        "IG_PASSWORD": ig_password,
        "THREADS_ACCESS_TOKEN": threads_token,
        "THREADS_USER_ID": threads_user_id,
    })
    write_env(env)

    state["settings"]["post_frequency"] = post_frequency
    state["settings"]["auto_post_delay_minutes"] = auto_delay
    state["settings"]["platforms"]["instagram"]["enabled"] = ig_enabled
    state["settings"]["platforms"]["threads"]["enabled"] = threads_enabled
    save_state(state)
    st.success("✅ 설정이 저장되었습니다.")
