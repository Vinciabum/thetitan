"""
test_slides.py
──────────────
API 키 없이 로컬에서 5장 슬라이드 전체를 생성해 확인하는 테스트 스크립트.
외부 의존성(aiohttp, gnews 등) 없이 슬라이드 렌더링만 단독 실행.

사용법:
    python test_slides.py

결과물: ./output_test/ 폴더에 slide_01~05.jpg 저장
"""

import asyncio
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional

# 슬라이드 데이터 클래스 (agent 의존성 없이 직접 정의)
@dataclass
class SlideContent:
    page: int
    role: str
    text: str
    image_prompt: str = ""

@dataclass
class MonologueContent:
    slides: List[SlideContent]
    instagram_caption: str = ""
    hashtags: List[str] = None

# ── 테스트용 더미 콘텐츠 ──────────────────────────────────────
TEST_SLIDES = [
    SlideContent(
        page=1, role="Hook",
        text="오늘도\n버텨낸 것만으로\n충분합니다.",
    ),
    SlideContent(
        page=2, role="Context",
        text="지금 이 피로감에 대하여\n\n"
             "퇴근 후에도 머릿속이 비워지지 않는다면, "
             "그것은 의지의 문제가 아닙니다. "
             "현대인의 뇌는 쉬는 법을 잊어가고 있습니다.",
    ),
    SlideContent(
        page=3, role="Insight",
        text="멈추는 것도 능력입니다\n\n"
             "빅터 프랭클은 말했습니다. '고통을 선택할 수 없어도, "
             "그 고통에 반응하는 방식은 선택할 수 있다'고. "
             "오늘의 피로는 당신이 살아냈다는 증거입니다.",
    ),
    SlideContent(
        page=4, role="Action",
        text="지금 당장 하나만\n\n"
             "오늘 밤 핸드폰을 내려놓고 5분만 눈을 감아보세요. "
             "아무것도 하지 않는 그 시간이, "
             "내일의 당신을 만들어줍니다.",
    ),
    SlideContent(
        page=5, role="Outro",
        text="오늘 하루,\n당신의 감정은 안녕했나요?",
    ),
]


# ── 슬라이드 렌더러 (slide_generator.py 핵심만 인라인) ─────────
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import numpy as np

CANVAS_SIZE = (1080, 1080)
W, H = CANVAS_SIZE
WHITE     = (255, 255, 255, 255)
WHITE_DIM = (200, 200, 200, 255)
GREY      = (135, 135, 135)

FONT_PATHS_BOLD = [
    "C:/Windows/Fonts/malgunbd.ttf",          # Windows
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJKkr-Bold.otf",
]
FONT_PATHS_REG = [
    "C:/Windows/Fonts/malgun.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJKkr-Regular.otf",
]

def _load(paths, size):
    for p in paths:
        try: return ImageFont.truetype(p, size)
        except: pass
    return ImageFont.load_default()

def _prepare_photo(photo_path: Path) -> Image.Image:
    img = Image.open(photo_path)
    w, h = img.size; side = min(w, h)
    img  = img.crop(((w-side)//2,(h-side)//2,(w+side)//2,(h+side)//2))
    img  = img.resize(CANVAS_SIZE, Image.LANCZOS).convert("L")
    img  = ImageEnhance.Contrast(img).enhance(1.5)
    img  = ImageEnhance.Brightness(img).enhance(0.82)
    img  = img.filter(ImageFilter.GaussianBlur(radius=0.8))
    arr  = np.array(img, dtype=np.float32)
    xs,ys = np.linspace(-1,1,W), np.linspace(-1,1,H)
    xv,yv = np.meshgrid(xs,ys); dist = np.sqrt(xv**2+yv**2)
    arr  = np.clip(arr * np.clip(1.0-dist*0.38,0.5,1.0), 0, 255).astype(np.uint8)
    grain = np.random.normal(0, 9, (H, W)).astype(np.float32)
    arr2  = np.clip(np.array(Image.fromarray(arr,"L"),dtype=np.float32)+grain,0,255).astype(np.uint8)
    return Image.fromarray(arr2,"L").convert("RGB")

def _apply_gradient(canvas: Image.Image) -> Image.Image:
    canvas = canvas.convert("RGBA")
    ov_img = Image.new("RGBA", CANVAS_SIZE, (0,0,0,0))
    ov = ImageDraw.Draw(ov_img)
    for y in range(0, int(H*0.25)):
        t = 1-y/(H*0.25); ov.line([(0,y),(W,y)],fill=(0,0,0,int(t*55)))
    g_top = int(H*0.38)
    for y in range(g_top, H):
        t = (y-g_top)/(H-g_top); ov.line([(0,y),(W,y)],fill=(0,0,0,int(t**0.7*210)))
    return Image.alpha_composite(canvas, ov_img)

def _draw_glow_text(canvas_rgba, draw, y, text, font, fill, glow=True):
    tw = draw.textlength(text, font=font); x = (W-tw)/2
    if glow:
        gl = Image.new("RGBA", CANVAS_SIZE, (0,0,0,0))
        gd = ImageDraw.Draw(gl)
        for off, alpha in [(8,30),(5,55),(3,80)]:
            gd.text((x+off,y+off),text,font=font,fill=(0,0,0,alpha))
            gd.text((x-off,y+off),text,font=font,fill=(0,0,0,alpha))
        gl = gl.filter(ImageFilter.GaussianBlur(radius=10))
        canvas_rgba.paste(Image.alpha_composite(canvas_rgba, gl))
    draw.text((x, y), text, font=font, fill=fill)

def _wrap(text, font, draw, max_w):
    lines = []
    for para in text.replace("\\n","\n").split("\n"):
        words, cur = para.split(), ""
        for wd in words:
            cand = (cur+" "+wd).strip() if cur else wd
            if draw.textlength(cand,font=font)>max_w and cur:
                lines.append(cur); cur=wd
            else: cur=cand
        if cur: lines.append(cur)
    return lines or [""]

ROLE_LABEL = {"Context":"CONTEXT","Insight":"INSIGHT","Action":"ACTION","Outro":""}

def render_slide(slide: SlideContent, bg: Image.Image) -> Image.Image:
    f_meta  = _load(FONT_PATHS_REG, 19)
    f_hook  = _load(FONT_PATHS_BOLD, 70)
    f_title = _load(FONT_PATHS_BOLD, 52)
    f_body  = _load(FONT_PATHS_REG, 30)

    canvas = _apply_gradient(bg.resize(CANVAS_SIZE, Image.LANCZOS).convert("RGB"))
    draw   = ImageDraw.Draw(canvas)

    # 상단 레이블 + 페이지
    label = ROLE_LABEL.get(slide.role, "")
    if label:
        draw.text((60, 52), label, font=f_meta, fill=GREY)
    page_str = f"{slide.page:02d} / 05"
    pw = draw.textlength(page_str, font=f_meta)
    draw.text((W-60-pw, 52), page_str, font=f_meta, fill=GREY)

    if slide.role == "Hook":
        lines = _wrap(slide.text, f_hook, draw, W-160)[:3]
        y = int(H*0.52)
        for line in lines:
            _draw_glow_text(canvas, draw, y, line, f_hook, WHITE)
            y += 94
        bw = draw.textlength("MONOLOGUE", font=f_meta)
        draw.text((W-60-bw, H-58), "MONOLOGUE", font=f_meta, fill=GREY)

    elif slide.role == "Outro":
        parts    = slide.text.split("||", 1)
        question = parts[0].strip()
        cta      = parts[1].strip() if len(parts) > 1 else "하루 한 장, 당신을 위해"
        lines    = _wrap(question, f_title, draw, W-200)[:2]
        total_h  = len(lines)*76
        y        = (H-total_h)//2 - 36
        deco_w   = 40
        draw.line([(W//2-deco_w//2,y-28),(W//2+deco_w//2,y-28)],fill=(160,160,160),width=1)
        for line in lines:
            _draw_glow_text(canvas, draw, y, line, f_title, WHITE)
            y += 76
        draw.line([(W//2-deco_w//2,y+10),(W//2+deco_w//2,y+10)],fill=(160,160,160),width=1)
        cta_tw = draw.textlength(cta, font=f_meta)
        draw.text(((W-cta_tw)/2, y+40), cta, font=f_meta, fill=(155,155,155))
        bw = draw.textlength("MONOLOGUE", font=f_meta)
        draw.text((W-60-bw, H-58), "MONOLOGUE", font=f_meta, fill=GREY)

    else:  # Context / Insight / Action
        parts     = slide.text.split("\n\n", 1)
        title_raw = parts[0].strip()
        body_raw  = parts[1].strip() if len(parts) > 1 else ""
        y = int(H*0.56)
        for line in _wrap(title_raw, f_title, draw, W-160)[:2]:
            _draw_glow_text(canvas, draw, y, line, f_title, WHITE)
            y += 72
        if body_raw:
            y += 18
            lw = min(int((W-160)*0.35), 220)
            draw.line([(W//2-lw//2,y),(W//2+lw//2,y)],fill=(180,180,180),width=1)
            y += 22
            for line in _wrap(body_raw, f_body, draw, W-160)[:4]:
                _draw_glow_text(canvas, draw, y, line, f_body, WHITE_DIM, glow=False)
                y += 52
        bw = draw.textlength("MONOLOGUE", font=f_meta)
        draw.text((W-60-bw, H-58), "MONOLOGUE", font=f_meta, fill=GREY)

    return canvas.convert("RGB")


async def main():
    out_dir = Path("./output_test")
    out_dir.mkdir(exist_ok=True)

    photo_dir = Path("./photos/vintage_portraits")
    photos = sorted(photo_dir.glob("*.jpg")) if photo_dir.exists() else []
    fallback = Image.new("RGB", CANVAS_SIZE, (28, 28, 28))

    print("슬라이드 생성 중...\n")
    for slide in TEST_SLIDES:
        bg = _prepare_photo(photos[(slide.page-1) % len(photos)]) if photos else fallback
        img = render_slide(slide, bg)
        out = out_dir / f"slide_{slide.page:02d}_{slide.role.lower()}.jpg"
        img.save(out, "JPEG", quality=95)
        print(f"  ✓ {slide.page:02d} [{slide.role:8s}] → {out.name}")

    print(f"\n완료! output_test/ 폴더에서 확인하세요.")

if __name__ == "__main__":
    asyncio.run(main())
