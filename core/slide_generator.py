"""
Slide Generator - 배경 이미지 생성(Gemini) + 디자인 합성(Pillow)
"""
import asyncio
import io
from pathlib import Path
from typing import List, Optional

from PIL import Image, ImageDraw, ImageFont

from core.image_generator import ImageGenerator
from core.psychological_engine import MonologueContent, SlideContent

# ── 디자인 상수 ──────────────────────────────────────────────
CANVAS_SIZE = (1080, 1080)
ACCENT       = (201, 169, 110)       # #C9A96E  웜 골드
TEXT_WHITE   = (255, 255, 255)
TEXT_SUB     = (180, 168, 150)       # 서브 텍스트
FONT_REGULAR = r"C:\Windows\Fonts\malgun.ttf"
FONT_BOLD    = r"C:\Windows\Fonts\malgunbd.ttf"


class SlideGenerator:
    """MonologueContent 각 슬라이드 → 배경 생성 후 Pillow 합성"""

    def __init__(self, image_generator: ImageGenerator, output_dir: Path):
        self.image_generator = image_generator
        self.output_dir = output_dir

    # ── public ──────────────────────────────────────────────────
    async def generate_slide_images(self, content: MonologueContent) -> List[Path]:
        tasks = [self._generate_one(slide) for slide in content.slides]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if isinstance(r, Path)]

    # ── private ─────────────────────────────────────────────────
    async def _generate_one(self, slide: SlideContent) -> Optional[Path]:
        output_path = self.output_dir / f"slide_{slide.page:02d}_{slide.role.lower()}.jpg"
        bg_path     = self.output_dir / f"_bg_{slide.page:02d}.jpg"

        # 1. 배경 이미지 생성
        bg_result = await self.image_generator.generate(slide.image_prompt, bg_path)

        # 2. Pillow 합성
        try:
            if bg_result and Path(bg_result).exists():
                bg_img = Image.open(bg_result).convert("RGB")
            else:
                bg_img = Image.new("RGB", CANVAS_SIZE, (18, 16, 14))

            final = await asyncio.to_thread(self._composite, bg_img, slide)
            final.save(output_path, "JPEG", quality=95)

            if bg_path.exists():
                bg_path.unlink()

            return output_path

        except Exception as e:
            print(f"[SlideGenerator] 합성 실패 slide {slide.page}: {e}")
            return None

    def _composite(self, bg: Image.Image, slide: SlideContent) -> Image.Image:
        W, H = CANVAS_SIZE
        bg = bg.resize(CANVAS_SIZE, Image.LANCZOS).convert("RGBA")

        # ── 1. 하단 다크 그라데이션 오버레이 ────────────────────
        overlay = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
        draw_ov = ImageDraw.Draw(overlay)
        grad_start = int(H * 0.28)
        for y in range(grad_start, H):
            alpha = int(195 * (y - grad_start) / (H - grad_start))
            draw_ov.line([(0, y), (W, y)], fill=(0, 0, 0, alpha))
        bg = Image.alpha_composite(bg, overlay).convert("RGB")
        draw = ImageDraw.Draw(bg)

        # ── 2. 폰트 로드 ────────────────────────────────────────
        def load(path, size):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                return ImageFont.load_default()

        f_quote = load(FONT_REGULAR, 118)
        f_body  = load(FONT_BOLD,    44)
        f_sub   = load(FONT_REGULAR, 23)

        # ── 3. 오프닝 따옴표 " ──────────────────────────────────
        draw.text((62, 48), "\u201c", font=f_quote, fill=ACCENT)

        # ── 4. 본문 텍스트 (자동 줄바꿈) ─────────────────────────
        margin   = 72
        max_w    = W - margin * 2
        lines    = self._wrap(slide.text, f_body, draw, max_w)
        line_h   = 62
        total_h  = len(lines) * line_h
        text_y   = max(int(H * 0.50), int(H * 0.72) - total_h)  # 하단 1/3 영역

        for i, line in enumerate(lines):
            draw.text((margin, text_y + i * line_h), line, font=f_body, fill=TEXT_WHITE)

        # ── 5. 클로징 따옴표 " ──────────────────────────────────
        close_y = text_y + total_h + 8
        close_x = W - 155
        draw.text((close_x, close_y), "\u201d", font=f_quote, fill=ACCENT)

        # ── 6. 하단 레이블 ───────────────────────────────────────
        draw.text((margin, H - 52), f"{slide.page}  /  5", font=f_sub, fill=TEXT_SUB)
        role_text = slide.role.lower()
        role_w = draw.textlength(role_text, font=f_sub)
        draw.text((W - margin - role_w, H - 52), role_text, font=f_sub, fill=ACCENT)

        return bg

    @staticmethod
    def _wrap(text: str, font: ImageFont.FreeTypeFont,
              draw: ImageDraw.ImageDraw, max_w: int) -> List[str]:
        """한국어 문자 단위 줄바꿈 (어절 우선)"""
        lines: List[str] = []
        for paragraph in text.replace("\\n", "\n").split("\n"):
            words = paragraph.split()
            current = ""
            for word in words:
                candidate = (current + " " + word).strip() if current else word
                w = draw.textlength(candidate, font=font)
                if w > max_w and current:
                    lines.append(current)
                    current = word
                else:
                    current = candidate
            if current:
                lines.append(current)
        return lines or [""]
