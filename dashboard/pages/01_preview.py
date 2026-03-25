# dashboard/pages/01_preview.py
"""
Page 1: 콘텐츠 미리보기 + 자동 포스팅 타이머
"""
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dashboard.state import load_state, save_state
from dashboard.components.slide_card import render_five_slides

st.set_page_config(page_title="미리보기 · Monologue", page_icon="📱", layout="wide")

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

created_at = pending.get("created_at", "")
if created_at:
    st.markdown(f'<p style="color:#8B7355; font-size:0.85rem;">생성: {created_at[:19].replace("T", " ")}</p>', unsafe_allow_html=True)

render_five_slides(pending.get("slides", []))

st.markdown('<hr style="border-color:#2C2C2C; margin: 24px 0;">', unsafe_allow_html=True)

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
        value=default_delay, step=1
    )

if "auto_post_at" not in st.session_state:
    st.session_state.auto_post_at = None
if "timer_started" not in st.session_state:
    st.session_state.timer_started = False


def _do_post(state: dict, post_ig: bool, post_threads: bool) -> None:
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
        st.session_state.timer_started = False
        st.session_state.auto_post_at = None
        st.markdown('<p style="color:#C9A96E; text-align:center;">🚀 자동 포스팅 실행 중...</p>', unsafe_allow_html=True)
        _do_post(state, post_ig, post_threads)
        st.rerun()

col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    if not st.session_state.timer_started:
        if st.button("⏱ 타이머 시작", use_container_width=True):
            st.session_state.auto_post_at = datetime.now() + timedelta(minutes=delay_minutes)
            st.session_state.timer_started = True
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
