"""
Slide Generator - Design System v3 (@onestepahead.mag 스타일)
  전슬라이드: B&W 빈티지 풀블리드 사진 + 텍스트 오버레이
  레퍼런스: research/reference_design_analysis.md

  사진 우선순위:
    1순위) photos/vintage_portraits/ 로컬 큐레이션 사진 (일관된 빈티지 감성)
    2순위) AI 생성 이미지 (로컬 사진이 없을 때 폴백)
"""
import asyncio
from pathlib import Path
from typing import List, Optional

from PIL import Image, ImageDraw, ImageFont, ImageFilter

from core.image_generator import ImageGenerator
from core.photo_pool import PhotoPool
from core.psychological_engine import MonologueContent, SlideContent

# 기본 사진 풀 경로 (프로젝트 루트 기준)
DEFAULT_PHOTO_POOL_DIR = Path("photos/vintage_portraits")


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

    def __init__(self, image_generator: ImageGenerator, output_dir: Path,
                 photo_pool_dir: Optional[Path] = None):
        self.image_generator = image_generator
        self.output_dir      = output_dir
        # 사진 풀: 로컬 큐레이션 사진 우선 사용
        pool_dir = photo_pool_dir or DEFAULT_PHOTO_POOL_DIR
        self.photo_pool = PhotoPool(pool_dir)
        if self.photo_pool.available():
            print(f"[SlideGenerator] 📸 사진 풀 활성화: {self.photo_pool.count()}장 사용 가능 ({pool_dir})")
        else:
            print(f"[SlideGenerator] ⚠️  사진 풀 없음 → AI 생성 이미지 사용 ('{pool_dir}' 에 사진 추가 시 품질 향상)")

    # ── public ──────────────────────────────────────────────────
    async def generate_slide_images(self, content: MonologueContent) -> List[Path]:
        tasks   = [self._generate_one(slide) for slide in content.slides]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if isinstance(r, Path)]

    # ── private ─────────────────────────────────────────────────
    async def _generate_one(self, slide: SlideContent) -> Optional[Path]:
        out = self.output_dir / f"slide_{slide.page:02d}_{slide.role.lower()}.jpg"
        try:
            bg_path = self.output_dir / f"_bg_{slide.page:02d}.jpg"
            bg = await self._get_background(slide, bg_path)

            img = await asyncio.to_thread(self._composite, bg, slide)
            img.save(out, "JPEG", quality=95)

            if bg_path.exists():
                bg_path.unlink()
            return out

        except Exception as e:
            print(f"[SlideGenerator] slide {slide.page} 실패: {e}")
            return None

    async def _get_background(self, slide: SlideContent, bg_path: Path) -> Image.Image:
        """
        배경 이미지 획득 (우선순위):
          1. 로컬 사진 풀 (photos/vintage_portraits/)
          2. AI 생성 이미지 (폴백)
          3. 단색 배경 (최종 폴백)
        """
        # 1순위: 로컬 사진 풀
        if self.photo_pool.available():
            photo = self.photo_pool.pick_for_slide(slide.page)
            if photo:
                prepared = await asyncio.to_thread(
                    self.photo_pool.prepare_image, photo, bg_path
                )
                if prepared and prepared.exists():
                    print(f"  [Slide {slide.page}] 📸 로컬 사진 사용: {photo.name}")
                    return Image.open(prepared).convert("L").convert("RGB")

        # 2순위: AI 생성 이미지
        bg_result = await self.image_generator.generate(slide.image_prompt, bg_path)
        if bg_result and Path(bg_result).exists():
            print(f"  [Slide {slide.page}] 🤖 AI 생성 이미지 사용")
            return Image.open(bg_result).convert("L").convert("RGB")

        # 3순위: 단색 배경
        print(f"  [Slide {slide.page}] ⬛ 단색 배경 사용 (이미지 생성 실패)")
        return Image.new("RGB", CANVAS_SIZE, (28, 28, 28))

    # ── 합성 메인 ────────────────────────────────────────────────
    def _composite(self, bg: Image.Image, slide: SlideContent) -> Image.Image:
        # 1. 풀블리드 흑백 배경
        canvas = bg.resize(CANVAS_SIZE, Image.LANCZOS).convert("RGBA")

        # 2. 그라디언트 오버레이 — 2단 구조
        #    ① 상단 얕은 베일: 상단 20%를 약하게 어둡게 (레이블 가독성)
        #    ② 하단 텍스트 존: 텍스트 영역을 확실히 어둡게 (글씨-사진 자연스러운 융합)
        overlay = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
        ov      = ImageDraw.Draw(overlay)

        # 상단 얕은 베일 (0 ~ 25%)
        for y in range(0, int(H * 0.25)):
            t     = 1 - y / (H * 0.25)
            alpha = int(t * 55)
            ov.line([(0, y), (W, y)], fill=(0, 0, 0, alpha))

        # 하단 메인 그라디언트 (38% ~ 100%) — 텍스트가 자연스럽게 녹아드는 어둠
        g_top = int(H * 0.38)
        for y in range(g_top, H):
            t     = (y - g_top) / (H - g_top)
            alpha = int(t ** 0.7 * 210)   # 더 짙게 → 텍스트 가독성 + 이미지 융합
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

        # 4. 본문 텍스트 배치 (canvas RGBA 전달 → 글로우 합성용)
        canvas_rgba = canvas.convert("RGBA")
        if slide.role == "Hook":
            self._draw_hook(draw, slide.text, f_hook, f_meta, canvas_rgba)
        elif slide.role == "Outro":
            self._draw_outro(draw, slide.text, f_title, f_meta, canvas_rgba)
        else:
            self._draw_body(draw, slide.text, f_title, f_body, f_meta, canvas_rgba)

        return canvas_rgba.convert("RGB")

    # ── 텍스트 글로우 + 그림자 헬퍼 ─────────────────────────────
    @staticmethod
    def _draw_text_centered(draw: ImageDraw.ImageDraw, y: int,
                            text: str, font: ImageFont.FreeTypeFont,
                            fill: tuple, shadow: bool = True,
                            canvas: "Image.Image | None" = None) -> None:
        """수평 가운데 정렬 + 소프트 글로우 (텍스트-이미지 융합)
        canvas 가 주어지면 블러 글로우 레이어 합성 (더 자연스러운 녹아듦)
        """
        tw = draw.textlength(text, font=font)
        x  = (W - tw) / 2

        if shadow and canvas is not None:
            # ── 소프트 글로우: 텍스트를 별도 레이어에 그린 뒤 블러 합성
            glow_layer = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
            gd = ImageDraw.Draw(glow_layer)
            # 글로우 범위 3단계 (멀수록 넓고 투명)
            for offset, alpha in [(8, 30), (5, 55), (3, 80)]:
                gd.text((x + offset, y + offset), text, font=font, fill=(0, 0, 0, alpha))
                gd.text((x - offset, y + offset), text, font=font, fill=(0, 0, 0, alpha))
            glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=10))
            canvas.paste(Image.alpha_composite(
                Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0)), glow_layer
            ), mask=glow_layer.split()[3])

        elif shadow:
            # 글로우 없이 간단 그림자
            draw.text((x + 2, y + 2), text, font=font, fill=(0, 0, 0, 130))

        draw.text((x, y), text, font=font, fill=fill)

    # ── Hook (커버) ──────────────────────────────────────────────
    def _draw_hook(self, draw: ImageDraw.ImageDraw,
                   text: str,
                   f_hook: ImageFont.FreeTypeFont,
                   f_meta: ImageFont.FreeTypeFont,
                   canvas: "Image.Image | None" = None) -> None:
        """커버 슬라이드: 대형 Bold 후킹 텍스트 중앙 정렬 + 브랜드
        — 잘림 방지: 좌우 안전 여백 160px 확보 후 가운데 정렬
        """
        max_w = W - 160
        lines = self._wrap(text, f_hook, draw, max_w)[:3]
        line_h = 94

        # 텍스트 블록 전체를 52% 지점에서 시작
        y = int(H * 0.52)
        for line in lines:
            self._draw_text_centered(draw, y, line, f_hook, WHITE,
                                     shadow=True, canvas=canvas)
            y += line_h

        # 브랜드 하단 우측
        brand_w = draw.textlength("MONOLOGUE", font=f_meta)
        draw.text((W - 60 - brand_w, H - 58), "MONOLOGUE", font=f_meta, fill=GREY)

    # ── Body / Outro ─────────────────────────────────────────────
    def _draw_body(self, draw: ImageDraw.ImageDraw,
                   text: str,
                   f_title: ImageFont.FreeTypeFont,
                   f_body: ImageFont.FreeTypeFont,
                   f_meta: ImageFont.FreeTypeFont,
                   canvas: "Image.Image | None" = None) -> None:
        """본문 슬라이드: 소제목(Bold) + 본문(Regular) — 전체 가운데 정렬
        레퍼런스(@onestepahead.mag) 스타일:
          • 제목: 굵고 크게, 가운데, 소프트 글로우
          • 구분선: 제목 아래 얇은 1px 라인
          • 본문: 작고 가운데, 넉넉한 줄간격
        """
        max_w = W - 160

        if "\n\n" in text:
            parts     = text.split("\n\n", 1)
            title_raw = parts[0].strip()
            body_raw  = parts[1].strip()
        else:
            title_raw = text.strip()
            body_raw  = ""

        y = int(H * 0.56)   # 제목 시작: 56% 지점

        # 소제목 — Bold, 가운데, 소프트 글로우
        t_lines = self._wrap(title_raw, f_title, draw, max_w)[:2]
        for line in t_lines:
            self._draw_text_centered(draw, y, line, f_title, WHITE,
                                     shadow=True, canvas=canvas)
            y += 72

        # 구분선 — 제목과 본문 사이 얇은 1px 라인 (레퍼런스 감성)
        if body_raw:
            y += 18
            line_w = min(int(max_w * 0.35), 220)
            draw.line([(W // 2 - line_w // 2, y),
                       (W // 2 + line_w // 2, y)],
                      fill=(180, 180, 180), width=1)
            y += 22

            # 본문 — Regular, 가운데, 가벼운 글로우
            b_lines = self._wrap(body_raw, f_body, draw, max_w)[:4]
            for line in b_lines:
                self._draw_text_centered(draw, y, line, f_body, WHITE_DIM,
                                         shadow=False, canvas=canvas)
                y += 52

        # 브랜드 하단 우측
        brand_w = draw.textlength("MONOLOGUE", font=f_meta)
        draw.text((W - 60 - brand_w, H - 58), "MONOLOGUE", font=f_meta, fill=GREY)

    # ── Outro ────────────────────────────────────────────────────
    def _draw_outro(self, draw: ImageDraw.ImageDraw,
                    text: str,
                    f_title: ImageFont.FreeTypeFont,
                    f_meta: ImageFont.FreeTypeFont,
                    canvas: "Image.Image | None" = None) -> None:
        """아웃트로 슬라이드: 질문 형태 문구 (정중앙) + 작은 CTA (아래)
        text 포맷: "질문 문구||CTA 문구"
        """
        if "||" in text:
            question, cta = text.split("||", 1)
            question = question.strip()
            cta      = cta.strip()
        else:
            question = text.strip()
            cta      = "하루 한 장, 당신을 위해"

        max_w   = W - 200
        lines   = self._wrap(question, f_title, draw, max_w)[:2]
        line_h  = 76
        total_h = len(lines) * line_h

        # 질문 블록 — 정중앙에서 약간 위 (CTA 공간 확보)
        y = (H - total_h) // 2 - 36

        # 위 장식선
        deco_w = 40
        draw.line([(W//2 - deco_w//2, y - 28),
                   (W//2 + deco_w//2, y - 28)],
                  fill=(160, 160, 160), width=1)

        for line in lines:
            self._draw_text_centered(draw, y, line, f_title, WHITE,
                                     shadow=True, canvas=canvas)
            y += line_h

        # 아래 장식선
        draw.line([(W//2 - deco_w//2, y + 10),
                   (W//2 + deco_w//2, y + 10)],
                  fill=(160, 160, 160), width=1)

        # CTA — 작고 흐리게
        cta_y = y + 40
        self._draw_text_centered(draw, cta_y, cta, f_meta,
                                 (155, 155, 155), shadow=False)

        # 브랜드 하단 우측
        brand_w = draw.textlength("MONOLOGUE", font=f_meta)
        draw.text((W - 60 - brand_w, H - 58), "MONOLOGUE", font=f_meta, fill=GREY)

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
