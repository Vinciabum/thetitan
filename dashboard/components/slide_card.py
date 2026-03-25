# dashboard/components/slide_card.py
"""
슬라이드 카드 컴포넌트 - 5슬라이드 미리보기
"""
from pathlib import Path
from typing import Dict, Any
import base64
import streamlit as st


ROLE_LABELS = {
    "Hook":    ("🎯", "훅"),
    "Context": ("🌍", "맥락"),
    "Insight": ("💡", "통찰"),
    "Action":  ("✨", "행동"),
    "Outro":   ("💬", "마무리"),
}


def render_slide_card(slide: Dict[str, Any], index: int) -> None:
    """슬라이드 1개 카드 렌더링"""
    role = slide.get("role", "")
    icon, label = ROLE_LABELS.get(role, ("📄", role))
    text = slide.get("text", "")
    image_path = slide.get("image_path")

    img_html = ""
    if image_path and Path(image_path).exists():
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        img_html = f'<img src="data:image/jpeg;base64,{b64}" style="width:100%; border-radius:8px; margin-bottom:12px;">'
    else:
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
