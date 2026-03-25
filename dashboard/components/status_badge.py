# dashboard/components/status_badge.py
"""
에이전트 상태 뱃지 컴포넌트
"""
import streamlit as st

STATE_CONFIG = {
    "idle":               {"color": "#4CAF50", "label": "대기 중"},
    "collecting_news":    {"color": "#C9A96E", "label": "뉴스 수집 중"},
    "analyzing_content":  {"color": "#C9A96E", "label": "분석 중"},
    "generating_content": {"color": "#2196F3", "label": "생성 중"},
    "posting_content":    {"color": "#9C27B0", "label": "포스팅 중"},
    "error":              {"color": "#E57373", "label": "오류"},
}


def render_status_badge(state: str) -> None:
    """에이전트 상태 뱃지 렌더링"""
    config = STATE_CONFIG.get(state, {"color": "#8B7355", "label": state})
    st.markdown(f"""
    <div style="display:inline-flex; align-items:center; gap:8px;
         background:#1A1A1A; border:1px solid #2C2C2C;
         border-radius:20px; padding:6px 16px;">
        <span style="color:{config['color']}; font-size:0.7rem;">●</span>
        <span style="color:#F5F0E8; font-size:0.85rem;">{config['label']}</span>
    </div>
    """, unsafe_allow_html=True)
