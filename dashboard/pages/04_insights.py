import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import os
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

from core.instagram_insights import InstagramInsightsClient, PostInsight

st.set_page_config(page_title="Instagram 인사이트", page_icon="📊", layout="wide")

# ── 토큰 확인 ─────────────────────────────────────────────────
ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN", "")
USER_ID      = os.getenv("IG_USER_ID", "")
PAGE_ID      = os.getenv("IG_PAGE_ID", "")

st.title("📊 Instagram 인사이트")

if not ACCESS_TOKEN or not USER_ID or not PAGE_ID:
    st.error("⚠️ Instagram Graph API 토큰이 설정되지 않았습니다.")
    st.markdown("""
    `.env` 파일에 아래 세 줄이 필요합니다:
    ```
    IG_ACCESS_TOKEN=...
    IG_USER_ID=...
    IG_PAGE_ID=...
    ```
    """)
    st.stop()

# ── 클라이언트 초기화 ─────────────────────────────────────────
client = InstagramInsightsClient(ACCESS_TOKEN, USER_ID, PAGE_ID)

# ── 새로고침 버튼 ─────────────────────────────────────────────
col_title, col_btn = st.columns([5, 1])
with col_btn:
    refresh = st.button("🔄 새로고침", use_container_width=True)

if "insights_data" not in st.session_state or refresh:
    with st.spinner("인사이트 데이터 불러오는 중..."):
        try:
            account = client.get_account()
            posts   = client.get_all_insights(limit=12)
            st.session_state["insights_data"]   = posts
            st.session_state["insights_account"] = account
            st.session_state["insights_error"]  = None
        except Exception as e:
            st.session_state["insights_error"] = str(e)

if st.session_state.get("insights_error"):
    st.error(f"API 오류: {st.session_state['insights_error']}")
    st.stop()

account: object = st.session_state.get("insights_account")
posts: list     = st.session_state.get("insights_data", [])

if not posts:
    st.info("게시물 인사이트 데이터가 없습니다.")
    st.stop()

# ══════════════════════════════════════════════════════════════
# 1. 계정 요약
# ══════════════════════════════════════════════════════════════
st.subheader(f"@{account.username}")
m1, m2, m3, m4 = st.columns(4)
m1.metric("팔로워",      f"{account.followers_count:,}")
m2.metric("총 게시물",   f"{account.media_count:,}")
m3.metric("7일 도달",    f"{account.reach_7d:,}")
m4.metric("프로필 방문", f"{account.profile_views_7d:,}")

st.divider()

# ══════════════════════════════════════════════════════════════
# 2. 핵심 지표 차트
# ══════════════════════════════════════════════════════════════
st.subheader("📈 게시물별 성과")

df = pd.DataFrame([{
    "날짜":       p.date_str,
    "저장":       p.saved,
    "좋아요":     p.like_count,
    "댓글":       p.comments_count,
    "공유":       p.shares,
    "도달":       p.reach,
    "노출":       p.impressions,
    "참여율(%)":  p.engagement_rate,
    "저장률(%)":  p.save_rate,
} for p in posts])

tab1, tab2, tab3 = st.tabs(["저장 · 참여율", "도달 · 노출", "좋아요 · 댓글 · 공유"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**저장 수** (알고리즘 1위 신호)")
        st.bar_chart(df.set_index("날짜")["저장"], color="#C9A96E")
    with col2:
        st.markdown("**참여율 (%)** — (좋아요+댓글+저장+공유) / 도달")
        st.bar_chart(df.set_index("날짜")["참여율(%)"], color="#7FBBF0")

with tab2:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**도달 (Reach)**")
        st.bar_chart(df.set_index("날짜")["도달"])
    with col2:
        st.markdown("**노출 (Impressions)**")
        st.bar_chart(df.set_index("날짜")["노출"])

with tab3:
    st.bar_chart(df.set_index("날짜")[["좋아요", "댓글", "공유"]])

st.divider()

# ══════════════════════════════════════════════════════════════
# 3. 베스트 게시물 TOP 3
# ══════════════════════════════════════════════════════════════
st.subheader("🏆 저장률 TOP 3")

sorted_posts = sorted(posts, key=lambda p: p.save_rate, reverse=True)[:3]
cols = st.columns(3)

for i, (col, post) in enumerate(zip(cols, sorted_posts)):
    with col:
        medal = ["🥇", "🥈", "🥉"][i]
        st.markdown(f"**{medal} {post.date_str}**")
        if post.thumbnail_url:
            st.image(post.thumbnail_url, use_container_width=True)
        st.caption(post.caption[:80] + "..." if len(post.caption) > 80 else post.caption)
        st.markdown(f"""
| 지표 | 수치 |
|------|------|
| 저장 | **{post.saved:,}** |
| 저장률 | **{post.save_rate}%** |
| 참여율 | {post.engagement_rate}% |
| 도달 | {post.reach:,} |
| 좋아요 | {post.like_count:,} |
        """)
        st.link_button("Instagram에서 보기", post.permalink)

st.divider()

# ══════════════════════════════════════════════════════════════
# 4. 전체 게시물 테이블
# ══════════════════════════════════════════════════════════════
st.subheader("📋 전체 게시물 상세")

df_display = df.copy()
df_display.index = range(1, len(df_display) + 1)
st.dataframe(
    df_display,
    use_container_width=True,
    column_config={
        "저장률(%)": st.column_config.ProgressColumn("저장률(%)", min_value=0, max_value=10),
        "참여율(%)": st.column_config.ProgressColumn("참여율(%)", min_value=0, max_value=20),
    }
)

# ══════════════════════════════════════════════════════════════
# 5. 인사이트 요약 (알고리즘 관점)
# ══════════════════════════════════════════════════════════════
st.divider()
st.subheader("💡 알고리즘 인사이트")

avg_save_rate = df["저장률(%)"].mean()
avg_eng_rate  = df["참여율(%)"].mean()
best_save     = df["저장"].max()
total_saves   = df["저장"].sum()

c1, c2, c3, c4 = st.columns(4)
c1.metric("평균 저장률",    f"{avg_save_rate:.1f}%",  help="3% 이상이면 알고리즘 최적화 수준")
c2.metric("평균 참여율",    f"{avg_eng_rate:.1f}%",   help="1.9% 이상이면 카루셀 평균 상회")
c3.metric("최고 저장 수",   f"{best_save:,}")
c4.metric("총 저장 누적",   f"{total_saves:,}")

if avg_save_rate >= 3.0:
    st.success("✅ 저장률이 Instagram 카루셀 업계 평균(3.4%)에 근접하거나 초과합니다. 알고리즘 노출에 유리합니다.")
elif avg_save_rate >= 1.5:
    st.warning("⚡ 저장률이 평균 이하입니다. Hook 문구와 CTA 강화를 권장합니다.")
else:
    st.error("🔴 저장률이 낮습니다. 콘텐츠 가치와 저장 유도 CTA를 점검하세요.")
