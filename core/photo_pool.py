"""
photo_pool.py — 빈티지 B&W 인물 사진 풀 관리자
  레퍼런스(@onestepahead.mag) 스타일 구현을 위해
  AI 생성 이미지 대신 로컬 큐레이션 사진을 슬라이드에 사용
"""
import random
import numpy as np
from pathlib import Path
from typing import Optional

from PIL import Image, ImageEnhance, ImageFilter

CANVAS_SIZE = (1080, 1080)
SUPPORTED_EXT = {".jpg", ".jpeg", ".png", ".webp"}


class PhotoPool:
    """로컬 폴더의 사진들을 관리하고 슬라이드에 맞게 공급"""

    def __init__(self, pool_dir: Path):
        self.pool_dir = Path(pool_dir)
        self._cache: list[Path] = []
        self._used: list[Path] = []   # 같은 세션에서 중복 방지

    def _load(self) -> list[Path]:
        if not self.pool_dir.exists():
            return []
        return [
            p for p in self.pool_dir.iterdir()
            if p.suffix.lower() in SUPPORTED_EXT
        ]

    def available(self) -> bool:
        """사진 풀에 사용 가능한 사진이 있는지 확인"""
        return len(self._load()) > 0

    def count(self) -> int:
        return len(self._load())

    def pick(self, seed: Optional[int] = None) -> Optional[Path]:
        """
        중복 없이 사진 한 장 선택.
        모든 사진을 다 쓰면 다시 처음부터.
        """
        all_photos = self._load()
        if not all_photos:
            return None

        # 아직 사용하지 않은 사진 우선
        unused = [p for p in all_photos if p not in self._used]
        if not unused:
            self._used.clear()
            unused = all_photos

        rng = random.Random(seed)
        chosen = rng.choice(unused)
        self._used.append(chosen)
        return chosen

    def pick_for_slide(self, page: int) -> Optional[Path]:
        """슬라이드 번호 기반으로 일관된 사진 선택 (같은 페이지 → 같은 사진)"""
        all_photos = self._load()
        if not all_photos:
            return None
        idx = (page - 1) % len(all_photos)
        return sorted(all_photos)[idx]

    def prepare_image(self, photo_path: Path, output_path: Path) -> Optional[Path]:
        """
        사진을 1080x1080 빈티지 B&W로 변환 후 저장
        - Smart crop: 중앙 정사각형 크롭
        - 흑백 변환 + 빈티지 후처리:
            ① 대비 강화 (하이콘트라스트 필름 느낌)
            ② 비네팅 (모서리 어둡게 — 레퍼런스 감성)
            ③ 필름 그레인 (아날로그 질감)
        """
        try:
            img = Image.open(photo_path)

            # ── 1. Smart crop ──────────────────────────────
            w, h = img.size
            side   = min(w, h)
            left   = (w - side) // 2
            top    = (h - side) // 2
            img    = img.crop((left, top, left + side, top + side))
            img    = img.resize(CANVAS_SIZE, Image.LANCZOS)

            # ── 2. 흑백 변환 ───────────────────────────────
            img = img.convert("L")

            # ── 3. 대비 강화 (필름 하이콘트라스트) ──────────
            img = ImageEnhance.Contrast(img).enhance(1.5)
            img = ImageEnhance.Brightness(img).enhance(0.82)

            # ── 3-1. 드림 블러 (살짝 부드럽게 — 필름 감성) ──
            img = img.filter(ImageFilter.GaussianBlur(radius=0.8))

            # ── 4. 비네팅 (모서리 → 중앙으로 어두워지는 효과) ──
            W_, H_ = CANVAS_SIZE
            arr = np.array(img, dtype=np.float32)

            xs = np.linspace(-1, 1, W_)
            ys = np.linspace(-1, 1, H_)
            xv, yv = np.meshgrid(xs, ys)
            dist   = np.sqrt(xv**2 + yv**2)          # 0(중앙) ~ √2(모서리)
            # 비네팅 강도: 모서리로 갈수록 최대 50% 어둡게
            vignette = np.clip(1.0 - dist * 0.38, 0.5, 1.0)
            arr = np.clip(arr * vignette, 0, 255).astype(np.uint8)
            img = Image.fromarray(arr, mode="L")

            # ── 5. 필름 그레인 (아날로그 질감) ──────────────
            grain = np.random.normal(0, 9, (H_, W_)).astype(np.float32)
            arr2  = np.array(img, dtype=np.float32)
            arr2  = np.clip(arr2 + grain, 0, 255).astype(np.uint8)
            img   = Image.fromarray(arr2, mode="L").convert("RGB")

            img.save(output_path, "JPEG", quality=95)
            return output_path

        except Exception as e:
            print(f"[PhotoPool] 이미지 준비 실패 ({photo_path.name}): {e}")
            return None
