# core/threads_publisher.py
"""
Threads Publisher - Meta Threads API 포스팅
"""
import asyncio
import logging
from pathlib import Path
from typing import List, Optional

import aiohttp

logger = logging.getLogger(__name__)

THREADS_API_BASE = "https://graph.threads.net/v1.0"


class ThreadsPublisher:
    """Meta Threads API를 통한 포스팅"""

    def __init__(self, access_token: str, user_id: str):
        self.access_token = access_token
        self.user_id = user_id

    @property
    def is_configured(self) -> bool:
        return bool(self.access_token and self.user_id)

    async def publish(self, caption: str, image_paths: List[Path]) -> bool:
        """Threads에 텍스트 포스팅. 실패 시 False 반환."""
        if not self.is_configured:
            logger.warning("Threads 미설정 - 포스팅 건너뜀")
            return False

        try:
            container_id = await self._create_container(caption)
            if not container_id:
                return False
            return await self._publish_container(container_id)
        except Exception as e:
            logger.error(f"Threads 포스팅 실패: {e}")
            return False

    async def _create_container(self, caption: str) -> Optional[str]:
        """Threads 미디어 컨테이너 생성"""
        url = f"{THREADS_API_BASE}/{self.user_id}/threads"
        params = {
            "media_type": "TEXT",
            "text": caption,
            "access_token": self.access_token
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=params) as resp:
                if resp.status != 200:
                    logger.error(f"컨테이너 생성 실패: {resp.status}")
                    return None
                data = await resp.json()
                return data.get("id")

    async def _publish_container(self, container_id: str) -> bool:
        """생성된 컨테이너 게시"""
        url = f"{THREADS_API_BASE}/{self.user_id}/threads_publish"
        params = {
            "creation_id": container_id,
            "access_token": self.access_token
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=params) as resp:
                if resp.status != 200:
                    logger.error(f"게시 실패: {resp.status}")
                    return False
                data = await resp.json()
                return bool(data.get("id"))
