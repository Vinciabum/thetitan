"""
Slide Generator - 디자인 시스템 v2
  Hook  (slide 1) : 순수 블랙 + 초대형 볼드 텍스트  (이미지 없음)
  Body  (slide 2-4): Gemini 배경 이미지 상단 60% + 순수 블랙 하단 40% + 텍스트
  Outro (slide 5) : Body 동일 방식
"""
import asyncio
from pathlib import Path
from typing import List, Optional

from PIL import Image, ImageDraw, ImageFont

from core.image_generator import ImageGenerator
from core.psychological_engine import MonologueContent, SlideContent

# ── 디자인 상수 ────────────────────────────────────────────
CANVAS_SIZE = (1080, 1080)
W, H        = CANVAS_SIZE
ACCENT      = (201, 169, 110)   # #C9A96E  웜 골드
WHITE       = (255, 255, 255)
GREY        = (140, 130, 115)   # 서브텍스트
LGREY       = (80,  75,  68)    # 페이지 번호
BLACK       = (0,   0,   0)

FONT_BOLD    = r"C:\Windows\Fonts\malgunbd.ttf"
FONT_REGULAR = r"C:\Windows\Fonts\malgun.ttf"

IMAGE_SPLIT  = 0.60   # 이미지가 차지하는 상단 비율


def _load(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


class SlideGenerator:
    """5슬라이드 카드뉴스 이미지 생성"""

    def __init__(self, image_generator: ImageGenerator, output_dir: Path):
        self.image_generator = image_generator
        self.output_dir = output_dir

    # ── public ────────────────────────────────────────────────
    async def generate_slide_images(self, content: MonologueContent) -> List[Path]:
        tasks = [self._generate_one(slide) for slide in content.slides]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if isinstance(r, Path)]

    # ── private ───────────────────────────────────────────────
    async def _generate_one(self, slide: SlideContent) -> Optional[Path]:
        out = self.output_dir / f"slide_{slide.page:02d}_{slide.role.lower()}.jpg"
        try:
            if slide.role == "Hook":
                img = await asyncio.to_thread(self._make_hook, slide)
            else:
                img = await self._make_body(slide)

            img.save(out, "JPEG", quality=95)
            return out
        except Exception as e:
            print(f"[SlideGenerator] slide {slide.page} 실패: {e}")
            return None

    # ── Hook 슬라이드 ──────────────────────────────────────────
    def _make_hook(self, slide: SlideContent) -> Image.Image:
        img  = Image.new("RGB", CANVAS_SIZE, BLACK)
        draw = ImageDraw.Draw(img)

        f_huge = _load(FONT_BOLD,    84)
        f_sub  = _load(FONT_REGULAR, 34)
        f_tiny = _load(FONT_REGULAR, 22)

        # ① 메인 텍스트 (자동 줄바꿈, 상단 1/3에서 시작)
        lines  = self._split_hook(slide.text, f_huge, draw)
        y      = 170
        for line in lines:
            draw.text((70, y), line, font=f_huge, fill=WHITE)
            b  = draw.textbbox((0, 0), line, font=f_huge)
            y += (b[3] - b[1]) + 16

        # ② 골드 구분선
        sep_y = y + 36
        draw.line([(70, sep_y), (min(520, W - 70), sep_y)], fill=ACCENT, width=2)

        # ③ 서브텍스트 (슬라이드 text의 뒷부분이 있을 경우 활용, 없으면 생략)
        sub = getattr(slide, "sub_text", None)
        if sub:
            y2 = sep_y + 28
            for s in sub.split("\n"):
                draw.text((70, y2), s, font=f_sub, fill=GREY)
                b  = draw.textbbox((0, 0), s, font=f_sub)
                y2 += (b[3] - b[1]) + 8

        # ④ 하단 레이블
        self._draw_bottom_labels(draw, f_tiny, slide)

        return img

    # ── Body / Outro 슬라이드 ─────────────────────────────────
    async def _make_body(self, slide: SlideContent) -> Image.Image:
        bg_path = self.output_dir / f"_bg_{slide.page:02d}.jpg"

        # 배경 이미지 생성
        bg_result = await self.image_generator.generate(slide.image_prompt, bg_path)

        if bg_result and Path(bg_result).exists():
            bg = Image.open(bg_result).convert("RGB")
        else:
            bg = Image.new("RGB", CANVAS_SIZE, (18, 16, 14))

        img = await asyncio.to_thread(self._composite_body, bg, slide)

        if bg_path.exists():
            bg_path.unlink()

        return img

    def _composite_body(self, bg: Image.Image, slide: SlideContent) -> Image.Image:
        # ── 캔버스: 순수 블랙 ─────────────────────────────────
        canvas = Image.new("RGB", CANVAS_SIZE, BLACK)

        # ── 상단 60%: Gemini 이미지 ───────────────────────────
        img_h  = int(H * IMAGE_SPLIT)
        top    = bg.resize((W, H), Image.LANCZOS).crop((0, 0, W, img_h))
        canvas.paste(top, (0, 0))

        draw = ImageDraw.Draw(canvas)

        # ── 골드 구분선 ───────────────────────────────────────
        draw.line([(70, img_h), (W - 70, img_h)], fill=ACCENT, width=1)

        # ── 하단 텍스트 ───────────────────────────────────────
        f_body = _load(FONT_BOLD,    46)
        f_tiny = _load(FONT_REGULAR, 22)

        max_w = W - 140
        lines = self._wrap(slide.text, f_body, draw, max_w)
        line_h = 56
        total_h = len(lines) * line_h

        # 텍스트 블록을 하단 영역 중앙에 배치
        area_top    = img_h + 24
        area_bottom = H - 70
        area_mid    = (area_top + area_bottom) // 2
        y = area_mid - total_h // 2

        for line in lines:
            draw.text((70, y), line, font=f_body, fill=WHITE)
            y += line_h

        # ── 하단 레이블 ───────────────────────────────────────
        self._draw_bottom_labels(draw, f_tiny, slide)

        return canvas

    # ── 공통 하단 레이블 ──────────────────────────────────────
    def _draw_bottom_labels(self, draw: ImageDraw.ImageDraw,
                            font: ImageFont.FreeTypeFont,
                            slide: SlideContent) -> None:
        draw.text((70, H - 52), "MONOLOGUE", font=font, fill=ACCENT)

        page_str = f"{slide.page:02d}  /  05"
        pw = draw.textlength(page_str, font=font)
        draw.text((W - 70 - pw, H - 52), page_str, font=font, fill=LGREY)

        role_str = slide.role.lower()
        rw = draw.textlength(role_str, font=font)
        draw.text(((W - rw) // 2, H - 52), role_str, font=font, fill=GREY)

    # ── 텍스트 유틸 ───────────────────────────────────────────
    def _split_hook(self, text: str,
                    font: ImageFont.FreeTypeFont,
                    draw: ImageDraw.ImageDraw) -> List[str]:
        """Hook 텍스트를 2-3개의 임팩트 있는 짧은 라인으로 분할"""
        max_w = W - 140

        # 쉼표/마침표/공백 기준 분할 우선 시도
        import re
        parts = re.split(r'(?<=[,，。.!?])\s*', text.strip())
        parts = [p.strip() for p in parts if p.strip()]

        # 각 파트가 max_w 넘으면 다시 wrapping
        result = []
        for part in parts:
            result.extend(self._wrap(part, font, draw, max_w))

        # 라인이 1개면 강제로 중간에서 분할
        if len(result) == 1:
            result = self._wrap(text, font, draw, int(max_w * 0.55))

        return result[:4]   # 최대 4줄

    @staticmethod
    def _wrap(text: str, font: ImageFont.FreeTypeFont,
              draw: ImageDraw.ImageDraw, max_w: int) -> List[str]:
        """어절 단위 줄바꿈 (한국어)"""
        lines: List[str] = []
        for paragraph in text.replace("\\n", "\n").split("\n"):
            words   = paragraph.split()
            current = ""
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
