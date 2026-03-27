"""
Threads API 포스팅 모듈
- 텍스트 단독 포스팅
- 이미지 카루셀 포스팅 (최대 20장)
"""
import asyncio
import logging
import time
import requests
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

THREADS_BASE = "https://graph.threads.net/v1.0"


class ThreadsPublisher:
    """Meta Threads API 퍼블리셔"""

    def __init__(self, access_token: str, user_id: str):
        self.token   = access_token
        self.user_id = user_id

    @property
    def is_configured(self) -> bool:
        return bool(self.token and self.user_id)

    # ── 내부 헬퍼 ─────────────────────────────────────────────
    def _post(self, path: str, data: dict) -> dict:
        data["access_token"] = self.token
        resp = requests.post(f"{THREADS_BASE}/{path}", data=data, timeout=30)
        if not resp.ok:
            err = resp.json().get("error", {})
            raise RuntimeError(f"Threads API {resp.status_code}: {err.get('message', resp.text)}")
        return resp.json()

    def _get(self, path: str, params: dict) -> dict:
        params["access_token"] = self.token
        resp = requests.get(f"{THREADS_BASE}/{path}", params=params, timeout=15)
        if not resp.ok:
            err = resp.json().get("error", {})
            raise RuntimeError(f"Threads API {resp.status_code}: {err.get('message', resp.text)}")
        return resp.json()

    def _wait_for_ready(self, container_id: str, max_wait: int = 60) -> bool:
        """컨테이너 상태가 FINISHED 될 때까지 폴링"""
        for _ in range(max_wait):
            data = self._get(container_id, {"fields": "status,error_message"})
            status = data.get("status", "")
            if status == "FINISHED":
                return True
            if status in ("ERROR", "EXPIRED"):
                raise RuntimeError(f"컨테이너 오류: {data.get('error_message', status)}")
            time.sleep(1)
        raise RuntimeError("컨테이너 준비 시간 초과")

    # ── 텍스트 포스팅 ─────────────────────────────────────────
    def post_text(self, text: str) -> str:
        """텍스트 단독 포스팅 → media_id 반환"""
        container = self._post(f"{self.user_id}/threads", {
            "media_type": "TEXT",
            "text": text,
        })
        result = self._post(f"{self.user_id}/threads_publish", {
            "creation_id": container["id"],
        })
        return result["id"]

    # ── 카루셀 포스팅 ─────────────────────────────────────────
    def post_carousel(self, image_urls: List[str], text: str = "") -> str:
        """이미지 카루셀 포스팅 (최대 20장) → media_id 반환
        image_urls: 공개 접근 가능한 URL 리스트
        """
        if not image_urls:
            raise ValueError("이미지 URL이 없습니다")
        image_urls = image_urls[:20]

        # 1. 각 이미지 아이템 컨테이너 생성
        item_ids = []
        for url in image_urls:
            item = self._post(f"{self.user_id}/threads", {
                "media_type":       "IMAGE",
                "image_url":        url,
                "is_carousel_item": "true",
            })
            item_ids.append(item["id"])

        # 아이템 준비 대기
        for item_id in item_ids:
            self._wait_for_ready(item_id)

        # 2. 카루셀 컨테이너 생성
        carousel = self._post(f"{self.user_id}/threads", {
            "media_type": "CAROUSEL",
            "children":   ",".join(item_ids),
            "text":       text,
        })

        # 3. 게시
        result = self._post(f"{self.user_id}/threads_publish", {
            "creation_id": carousel["id"],
        })
        return result["id"]

    # ── async 래퍼 (agent.py 호환) ────────────────────────────
    async def publish(self, caption: str, image_urls: Optional[List[str]] = None) -> bool:
        """비동기 포스팅 인터페이스"""
        if not self.is_configured:
            logger.warning("Threads 미설정 — 포스팅 건너뜀")
            return False
        try:
            if image_urls:
                media_id = await asyncio.to_thread(self.post_carousel, image_urls, caption)
            else:
                media_id = await asyncio.to_thread(self.post_text, caption)
            logger.info(f"Threads 포스팅 성공: {media_id}")
            return True
        except Exception as e:
            logger.error(f"Threads 포스팅 실패: {e}")
            return False

    # ── 계정 정보 ─────────────────────────────────────────────
    def get_profile(self) -> dict:
        return self._get("me", {"fields": "id,username,threads_biography"})

    def get_recent_posts(self, limit: int = 10) -> List[dict]:
        data = self._get(f"{self.user_id}/threads", {
            "fields": "id,text,timestamp,media_type,permalink",
            "limit":  limit,
        })
        return data.get("data", [])
