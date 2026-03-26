# dashboard/pages/02_monitor.py
"""
Page 2: 에이전트 상태 모니터링 + 로그
"""
import streamlit as st
from streamlit_autorefresh import st_autorefresh
import subprocess
import sys
from pathlib import Path
from datetime import date

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

st_autorefresh(interval=5000, key="monitor_refresh")

st.markdown("## 📊 에이전트 모니터링")
st.markdown('<hr style="border-color:#2C2C2C;">', unsafe_allow_html=True)

state = load_state()

col_badge, col_time = st.columns([1, 2])
with col_badge:
    render_status_badge(state.get("agent_state", "idle"))
with col_time:
    last_run = state.get("last_run")
    if last_run:
        st.markdown(f'<p style="color:#8B7355; padding-top:8px;">마지막 실행: {last_run[:19].replace("T"," ")}</p>', unsafe_allow_html=True)

st.markdown('<br>', unsafe_allow_html=True)

history = state.get("post_history", [])
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
st.markdown("### 🎛 에이전트 제어")

col_start, col_stop, col_msg = st.columns([1, 1, 3])

with col_start:
    if st.button("▶ 에이전트 시작", use_container_width=True):
        try:
            project_root = str(Path(__file__).parent.parent.parent)
            proc = subprocess.Popen(
                [sys.executable, "main.py"],
                cwd=project_root,
                stdout=open(project_root + "/agent_run.log", "w"),
                stderr=subprocess.STDOUT,
            )
            # 즉시 상태 파일에 반영
            state["agent_state"] = "collecting_news"
            state["agent_log"] = state.get("agent_log", [])
            state["agent_log"].insert(0, f"[{__import__('datetime').datetime.now().strftime('%H:%M:%S')}] 에이전트 시작 (PID: {proc.pid})")
            state["agent_log"] = state["agent_log"][:20]
            save_state(state)
            with col_msg:
                st.success(f"에이전트 시작됨 (PID: {proc.pid}) — 5초 후 상태가 업데이트됩니다.")
        except Exception as e:
            with col_msg:
                st.error(f"시작 실패: {e}")

with col_stop:
    if st.button("⏹ 에이전트 중지", use_container_width=True):
        try:
            subprocess.run(
                ["taskkill", "/F", "/FI", "IMAGENAME eq python.exe", "/FI", "WINDOWTITLE eq main*"],
                capture_output=True
            )
            # main.py 프로세스만 종료 시도
            subprocess.run(
                ["wmic", "process", "where", "commandline like '%main.py%'", "delete"],
                capture_output=True
            )
            state["agent_state"] = "idle"
            save_state(state)
            with col_msg:
                st.success("에이전트를 중지했습니다.")
        except Exception as e:
            with col_msg:
                st.error(f"중지 실패: {e}")

st.markdown('<hr style="border-color:#2C2C2C; margin:24px 0;">', unsafe_allow_html=True)
st.markdown("### 📜 에이전트 로그")
agent_log = state.get("agent_log", [])
if agent_log:
    log_html = "".join(
        f'<div style="font-family:monospace; font-size:0.8rem; color:#8B7355; padding:2px 0;">{entry}</div>'
        for entry in agent_log[:10]
    )
    st.markdown(f'<div style="background:#1A1A1A; border:1px solid #2C2C2C; border-radius:8px; padding:12px;">{log_html}</div>', unsafe_allow_html=True)

    # agent_run.log 파일이 있으면 마지막 5줄 보여주기
    log_file = Path(__file__).parent.parent.parent / "agent_run.log"
    if log_file.exists():
        lines = log_file.read_text(encoding="utf-8", errors="ignore").strip().splitlines()
        if lines:
            recent = lines[-5:]
            recent_html = "".join(
                f'<div style="font-family:monospace; font-size:0.75rem; color:#C9A96E; padding:1px 0;">{l}</div>'
                for l in recent
            )
            st.markdown(f'<div style="background:#1A1A1A; border:1px solid #C9A96E; border-radius:8px; padding:12px; margin-top:8px;">{recent_html}</div>', unsafe_allow_html=True)
else:
    st.markdown('<p style="color:#8B7355; font-size:0.85rem;">로그 없음</p>', unsafe_allow_html=True)

st.markdown('<hr style="border-color:#2C2C2C; margin:24px 0;">', unsafe_allow_html=True)
st.markdown("### 📋 최근 포스팅 기록")

if history:
    for item in history[:10]:
        posted_at = item.get("posted_at", "")[:19].replace("T", " ")
        success = item.get("success", False)
        platforms = ", ".join(item.get("platforms", []))
        caption = item.get("caption", "")[:60]
        icon = "✅" if success else "❌"
        st.markdown(f"""
        <div style="background:#1A1A1A; border:1px solid #2C2C2C; border-radius:8px;
             padding:12px 16px; margin-bottom:8px;">
            <span>{icon}</span>
            <span style="color:#F5F0E8; font-size:0.9rem; margin-left:8px;">{caption}...</span>
            <br>
            <span style="color:#8B7355; font-size:0.75rem;">{posted_at} · {platforms}</span>
        </div>
        """, unsafe_allow_html=True)
else:
    st.markdown('<p style="color:#8B7355; text-align:center; padding:40px 0;">포스팅 기록 없음</p>', unsafe_allow_html=True)
