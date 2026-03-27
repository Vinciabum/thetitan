"""
Slide Generator - Design System v3 (@onestepahead.mag 스타일)
  전슬라이드: B&W 빈티지 풀블리드 사진 + 텍스트 오버레이
  레퍼런스: research/reference_design_analysis.md
"""
import asyncio
from pathlib import Path
from typing import List, Optional

from PIL import Image, ImageDraw, ImageFont

from core.image_generator import ImageGenerator
from core.psychological_engine import MonologueContent, SlideContent


CANVAS_SIZE = (1080, 1080)
W, H        = CANVAS_SIZE

WHITE       = (255, 255, 255)
WHITE_DIM   = (200, 200, 200)   # 본문 텍스트 (살짝 어둡게)
GREY        = (135, 135, 135)   # 레이블, 페이지 번호, 브랜드

FONT_BOLD    = r"C:\Windows\Fonts\malgunbd.ttf"
FONT_REGULAR = r"C:\Windows\Fonts\malgun.ttf"

# 슬라이드 상단 레이블 (영문 소캡스)
ROLE_LABEL = {
    "Hook":    "",           # 커버 — 레이블 없음
    "Context": "CONTEXT",
    "Insight": "INSIGHT",
    "Action":  "ACTION",
    "Outro":   "OUTRO",
}


def _load(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


class SlideGenerator:
    """5슬라이드 카드뉴스 이미지 생성 — onestepahead.mag 스타일"""

    def __init__(self, image_generator: ImageGenerator, output_dir: Path):
        self.image_generator = image_generator
        self.output_dir      = output_dir

    # ── public ──────────────────────────────────────────────────
    async def generate_slide_images(self, content: MonologueContent) -> List[Path]:
        tasks   = [self._generate_one(slide) for slide in content.slides]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if isinstance(r, Path)]

    # ── private ─────────────────────────────────────────────────
    async def _generate_one(self, slide: SlideContent) -> Optional[Path]:
        out = self.output_dir / f"slide_{slide.page:02d}_{slide.role.lower()}.jpg"
        try:
            bg_path   = self.output_dir / f"_bg_{slide.page:02d}.jpg"
            bg_result = await self.image_generator.generate(slide.image_prompt, bg_path)

            if bg_result and Path(bg_result).exists():
                # PIL로 흑백 변환 (L → RGB)
                bg = Image.open(bg_result).convert("L").convert("RGB")
            else:
                bg = Image.new("RGB", CANVAS_SIZE, (28, 28, 28))

            img = await asyncio.to_thread(self._composite, bg, slide)
            img.save(out, "JPEG", quality=95)

            if bg_path.exists():
                bg_path.unlink()
            return out

        except Exception as e:
            print(f"[SlideGenerator] slide {slide.page} 실패: {e}")
            return None

    # ── 합성 메인 ────────────────────────────────────────────────
    def _composite(self, bg: Image.Image, slide: SlideContent) -> Image.Image:
        # 1. 풀블리드 흑백 배경
        canvas = bg.resize(CANVAS_SIZE, Image.LANCZOS).convert("RGBA")

        # 2. 하단 그라디언트 오버레이 — 텍스트 가독성 확보
        overlay = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
        ov      = ImageDraw.Draw(overlay)
        g_top   = int(H * 0.28)   # 그라디언트 시작 y
        for y in range(g_top, H):
            t     = (y - g_top) / (H - g_top)
            alpha = int(t ** 0.65 * 200)
            ov.line([(0, y), (W, y)], fill=(0, 0, 0, alpha))
        canvas = Image.alpha_composite(canvas, overlay).convert("RGB")

        draw = ImageDraw.Draw(canvas)

        # 폰트
        f_meta  = _load(FONT_REGULAR, 19)   # 레이블·페이지·브랜드
        f_hook  = _load(FONT_BOLD,    70)   # Hook 대형 제목
        f_title = _load(FONT_BOLD,    52)   # Body 소제목
        f_body  = _load(FONT_REGULAR, 30)   # Body 본문

        # 3. 상단: 역할 레이블(좌) + 페이지 번호(우)
        label = ROLE_LABEL.get(slide.role, "")
        if label:
            draw.text((60, 52), label, font=f_meta, fill=GREY)

        page_str = f"{slide.page:02d} / 05"
        pw       = draw.textlength(page_str, font=f_meta)
        draw.text((W - 60 - pw, 52), page_str, font=f_meta, fill=GREY)

        # 4. 본문 텍스트 배치
        if slide.role == "Hook":
            self._draw_hook(draw, slide.text, f_hook, f_meta)
        else:
            self._draw_body(draw, slide.text, f_title, f_body, f_meta)

        return canvas

    # ── Hook (커버) ──────────────────────────────────────────────
    def _draw_hook(self, draw: ImageDraw.ImageDraw,
                   text: str,
                   f_hook: ImageFont.FreeTypeFont,
                   f_meta: ImageFont.FreeTypeFont) -> None:
        """커버 슬라이드: 대형 Bold 후킹 텍스트 + 브랜드"""
        max_w  = W - 120
        lines  = self._wrap(text, f_hook, draw, max_w)[:3]
        line_h = 86
        y      = int(H * 0.50)
        for line in lines:
            draw.text((60, y), line, font=f_hook, fill=WHITE)
            y += line_h
        # 브랜드 하단 좌측
        draw.text((60, H - 58), "MONOLOGUE", font=f_meta, fill=GREY)

    # ── Body / Outro ─────────────────────────────────────────────
    def _draw_body(self, draw: ImageDraw.ImageDraw,
                   text: str,
                   f_title: ImageFont.FreeTypeFont,
                   f_body: ImageFont.FreeTypeFont,
                   f_meta: ImageFont.FreeTypeFont) -> None:
        """본문 슬라이드: 소제목(Bold) + 본문(Regular)

        text 포맷: "소제목\\n\\n본문 설명 2~3문장"
        소제목이 없는 경우(\\n\\n 없음): 전체를 소제목 스타일로 표시
        """
        max_w = W - 120

        if "\n\n" in text:
            parts     = text.split("\n\n", 1)
            title_raw = parts[0].strip()
            body_raw  = parts[1].strip()
        else:
            title_raw = text.strip()
            body_raw  = ""

        y = int(H * 0.54)

        # 소제목 (Bold, 흰색)
        t_lines = self._wrap(title_raw, f_title, draw, max_w)[:3]
        for line in t_lines:
            draw.text((60, y), line, font=f_title, fill=WHITE)
            y += 66

        # 본문 (Regular, 살짝 어두운 흰색)
        if body_raw:
            y += 20
            b_lines = self._wrap(body_raw, f_body, draw, max_w)[:4]
            for line in b_lines:
                draw.text((60, y), line, font=f_body, fill=WHITE_DIM)
                y += 44

        # 브랜드 하단 좌측
        draw.text((60, H - 58), "MONOLOGUE", font=f_meta, fill=GREY)

    # ── 텍스트 래핑 ──────────────────────────────────────────────
    @staticmethod
    def _wrap(text: str, font: ImageFont.FreeTypeFont,
              draw: ImageDraw.ImageDraw, max_w: int) -> List[str]:
        """어절 단위 줄바꿈 (\\n 명시적 줄바꿈 존중)"""
        lines: List[str] = []
        for para in text.replace("\\n", "\n").split("\n"):
            words, current = para.split(), ""
            for word in words:
                candidate = (current + " " + word).strip() if current else word
                if draw.textlength(candidate, font=font) > max_w and current:
                    lines.append(current)
                    current = word
                else:
                    current = candidate
            if current:
                lines.append(current)
        return lines or [""]
