# dashboard/app.py
"""
Monologue Dashboard - 메인 진입점
실행: streamlit run dashboard/app.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

st.set_page_config(
    page_title="Monologue",
    page_icon="🖤",
    layout="wide",
    initial_sidebar_state="expanded"
)

DARK_CSS = """
<style>
    .stApp { background-color: #0F0F0F; color: #F5F0E8; }
    [data-testid="stSidebar"] { background-color: #1A1A1A; border-right: 1px solid #2C2C2C; }
    .monologue-card {
        background: #1A1A1A; border: 1px solid #2C2C2C;
        border-radius: 12px; padding: 20px; margin: 10px 0;
    }
    .monologue-card-gold {
        background: #1A1A1A; border: 1px solid #C9A96E;
        border-radius: 12px; padding: 20px; margin: 10px 0;
    }
    .timer-display {
        font-size: 48px; font-weight: 300; color: #C9A96E;
        text-align: center; letter-spacing: 4px; font-family: monospace;
    }
    .stButton > button {
        background: transparent; border: 1px solid #C9A96E;
        color: #C9A96E; border-radius: 8px; padding: 8px 24px;
    }
    .stButton > button:hover { background: #C9A96E; color: #0F0F0F; }
    h1, h2, h3, h4 { color: #F5F0E8 !important; }
    p, span, label { color: #F5F0E8; }
    .sub-text { color: #8B7355; font-size: 0.85rem; }
    [data-testid="metric-container"] {
        background: #1A1A1A; border: 1px solid #2C2C2C;
        border-radius: 8px; padding: 12px;
    }
    hr { border-color: #2C2C2C; }
    .stCheckbox label { color: #F5F0E8 !important; }
    .stTextInput input, .stNumberInput input, .stTextArea textarea {
        background: #1A1A1A !important; border: 1px solid #2C2C2C !important;
        color: #F5F0E8 !important; border-radius: 8px;
    }
    .success-text { color: #4CAF50; }
    .error-text { color: #E57373; }
    .gold-text { color: #C9A96E; }
</style>
"""

st.markdown(DARK_CSS, unsafe_allow_html=True)

with st.sidebar:
    st.markdown("""
    <div style="padding: 20px 0; text-align: center;">
        <h2 style="color: #C9A96E; letter-spacing: 4px; font-weight: 300;">MONOLOGUE</h2>
        <p style="color: #8B7355; font-size: 0.75rem;">당신의 고요한 독백의 시간</p>
    </div>
    <hr>
    """, unsafe_allow_html=True)

st.markdown("""
<div style="text-align: center; padding: 60px 0;">
    <h1 style="font-weight: 200; letter-spacing: 6px; color: #F5F0E8;">MONOLOGUE</h1>
    <p style="color: #8B7355; font-size: 1.1rem;">당신의 소란스러운 하루 끝, 고요한 독백의 시간</p>
</div>
""", unsafe_allow_html=True)

from dashboard.state import load_state
import datetime

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
    today = datetime.date.today().isoformat()
    today_posts = len([h for h in history if h.get("posted_at", "")[:10] == today])
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
