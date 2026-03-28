"""
download_photos.py — 빈티지 B&W 인물 사진 자동 다운로드
  Unsplash API (무료 플랜)를 사용하여 레퍼런스 스타일 사진을 photos/vintage_portraits/ 에 저장

사용법:
  1. https://unsplash.com/developers 에서 무료 앱 등록 → Access Key 발급
  2. 아래 UNSPLASH_ACCESS_KEY에 입력 또는 환경변수 UNSPLASH_ACCESS_KEY 설정
  3. python download_photos.py

  또는 API 없이 수동 다운로드:
  - Unsplash(https://unsplash.com), Pexels(https://pexels.com) 에서
    "vintage portrait black white woman 1950s" 검색 후
    photos/vintage_portraits/ 폴더에 직접 저장
"""

import os
import time
import urllib.request
import urllib.parse
import json
from pathlib import Path

# ── 설정 ────────────────────────────────────────────────────────
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "zv-3Z0CAPQJCX0BDYIIgAuxGwNh2-oq1srnYwzJMwG0")
PHOTO_DIR = Path("photos/vintage_portraits")
TARGET_COUNT = 50   # 다운로드할 사진 수

# 레퍼런스 스타일에 맞는 검색 쿼리 목록
SEARCH_QUERIES = [
    "vintage portrait woman black white 1950s",
    "vintage film photography woman contemplative",
    "black white portrait woman 1960s classic",
    "vintage woman photography monochrome",
    "classic portrait black white feminine",
]


def download_via_unsplash_api(access_key: str, target: int = 20) -> int:
    """Unsplash API로 사진 다운로드"""
    PHOTO_DIR.mkdir(parents=True, exist_ok=True)
    downloaded = 0

    for query in SEARCH_QUERIES:
        if downloaded >= target:
            break

        per_page = min(10, target - downloaded)
        encoded_query = urllib.parse.quote(query)
        url = (
            f"https://api.unsplash.com/search/photos"
            f"?query={encoded_query}"
            f"&per_page={per_page}"
            f"&orientation=squarish"
        )

        req = urllib.request.Request(url, headers={
            "Authorization": f"Client-ID {access_key}"
        })

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
                results = data.get("results", [])

            for photo in results:
                if downloaded >= target:
                    break

                photo_id   = photo["id"]
                photo_url  = photo["urls"]["regular"]   # 1080px 수준
                out_path   = PHOTO_DIR / f"vintage_{photo_id}.jpg"

                if out_path.exists():
                    print(f"  이미 존재: {out_path.name}")
                    downloaded += 1
                    continue

                print(f"  다운로드 중: {out_path.name} ...")
                urllib.request.urlretrieve(photo_url, out_path)
                downloaded += 1
                time.sleep(0.3)   # API 레이트 리밋 방지

        except Exception as e:
            print(f"  [오류] '{query}' 검색 실패: {e}")
            continue

    return downloaded


def show_manual_guide():
    """API 없이 수동 다운로드 가이드 출력"""
    print("\n" + "=" * 60)
    print("📸 수동 사진 다운로드 가이드")
    print("=" * 60)
    print(f"\n저장 위치: {PHOTO_DIR.resolve()}\n")
    print("추천 무료 사이트:")
    print("  • Unsplash: https://unsplash.com/s/photos/vintage-portrait-woman")
    print("  • Pexels:   https://pexels.com/search/vintage%20portrait%20black%20white/")
    print("  • Pixabay:  https://pixabay.com/images/search/vintage%20portrait/")
    print("\n검색 키워드 (복사해서 사용):")
    for q in SEARCH_QUERIES:
        print(f"  → {q}")
    print("\n권장 사진 스타일:")
    print("  ✓ 흑백 또는 컬러 무관 (자동으로 흑백 변환됩니다)")
    print("  ✓ 1950~60년대 빈티지 감성 인물 사진")
    print("  ✓ 여성 인물 클로즈업 또는 반신")
    print("  ✓ 사색적, 조용한 분위기")
    print("  ✓ 고해상도 권장 (최소 1080x1080)")
    print(f"\n사진을 위 폴더에 저장 후 에이전트를 실행하면 자동으로 사용됩니다.")
    print("=" * 60 + "\n")


def main():
    print("🖼️  Monologue 빈티지 사진 풀 다운로더")
    print("-" * 40)

    PHOTO_DIR.mkdir(parents=True, exist_ok=True)
    existing = list(PHOTO_DIR.glob("*.jpg")) + list(PHOTO_DIR.glob("*.png"))
    print(f"현재 저장된 사진: {len(existing)}장")

    if UNSPLASH_ACCESS_KEY == "YOUR_ACCESS_KEY_HERE":
        print("\n⚠️  Unsplash API 키가 설정되지 않았습니다.")
        show_manual_guide()
        return

    need = max(0, TARGET_COUNT - len(existing))
    if need == 0:
        print(f"✅ 이미 {len(existing)}장의 사진이 있습니다. 추가 다운로드가 필요 없습니다.")
        return

    print(f"\n{need}장 추가 다운로드 시작...")
    count = download_via_unsplash_api(UNSPLASH_ACCESS_KEY, need)
    print(f"\n✅ 완료! {count}장 다운로드됨 (총 {len(existing) + count}장)")


if __name__ == "__main__":
    main()
