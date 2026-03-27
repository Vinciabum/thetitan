"""
Instagram Graph API — 인사이트 조회 모듈
graph.facebook.com 엔드포인트 사용 (Business/Creator 계정)
"""
import requests
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime

GRAPH_BASE = "https://graph.facebook.com/v21.0"


@dataclass
class PostInsight:
    media_id: str
    timestamp: str
    caption: str
    media_type: str
    thumbnail_url: str
    permalink: str
    like_count: int
    comments_count: int
    reach: int
    saved: int
    shares: int

    @property
    def engagement_rate(self) -> float:
        if self.reach == 0:
            return 0.0
        return round((self.like_count + self.comments_count + self.saved + self.shares) / self.reach * 100, 2)

    @property
    def save_rate(self) -> float:
        if self.reach == 0:
            return 0.0
        return round(self.saved / self.reach * 100, 2)

    @property
    def date_str(self) -> str:
        try:
            dt = datetime.fromisoformat(self.timestamp.replace("Z", "+00:00"))
            return dt.strftime("%m/%d %H:%M")
        except Exception:
            return self.timestamp[:10]


@dataclass
class AccountInsight:
    username: str
    followers_count: int
    media_count: int
    reach_7d: int = 0
    profile_views_7d: int = 0


class InstagramInsightsClient:
    """Instagram Graph API 클라이언트 (Facebook Page Token 방식)"""

    def __init__(self, user_token: str, ig_user_id: str, page_id: str):
        self.ig_user_id = ig_user_id
        self.page_id    = page_id
        # 페이지 액세스 토큰 취득
        self.page_token = self._get_page_token(user_token, page_id)

    def _get_page_token(self, user_token: str, page_id: str) -> str:
        """User 토큰 → Page 액세스 토큰 교환"""
        try:
            resp = requests.get(
                f"{GRAPH_BASE}/me/accounts",
                params={"access_token": user_token},
                timeout=10
            )
            resp.raise_for_status()
            for page in resp.json().get("data", []):
                if page["id"] == page_id:
                    return page["access_token"]
        except Exception:
            pass
        return user_token  # fallback

    def _get(self, path: str, params: Dict[str, Any]) -> Dict:
        params["access_token"] = self.page_token
        resp = requests.get(f"{GRAPH_BASE}/{path}", params=params, timeout=15)
        if not resp.ok:
            err = resp.json().get("error", {})
            raise RuntimeError(f"API {resp.status_code}: {err.get('message', resp.text)}")
        return resp.json()

    # ── 계정 정보 ─────────────────────────────────────────────
    def get_account(self) -> AccountInsight:
        data = self._get(self.ig_user_id, {
            "fields": "username,followers_count,media_count"
        })
        account = AccountInsight(
            username=data.get("username", ""),
            followers_count=data.get("followers_count", 0),
            media_count=data.get("media_count", 0),
        )
        # 7일 계정 인사이트
        try:
            ins = self._get(f"{self.ig_user_id}/insights", {
                "metric": "reach,profile_views",
                "period": "day",
                "since": self._days_ago(7),
                "until": self._days_ago(0),
            })
            for metric in ins.get("data", []):
                total = sum(v.get("value", 0) for v in metric.get("values", []))
                if metric.get("name") == "reach":
                    account.reach_7d = total
                elif metric.get("name") == "profile_views":
                    account.profile_views_7d = total
        except Exception:
            pass
        return account

    # ── 최근 게시물 ───────────────────────────────────────────
    def get_recent_media(self, limit: int = 12) -> List[Dict]:
        data = self._get(f"{self.ig_user_id}/media", {
            "fields": "id,caption,media_type,timestamp,thumbnail_url,media_url,permalink,like_count,comments_count",
            "limit": limit,
        })
        return data.get("data", [])

    # ── 게시물 인사이트 ───────────────────────────────────────
    def get_post_insight(self, media: Dict) -> Optional[PostInsight]:
        media_id = media["id"]
        try:
            ins = self._get(f"{media_id}/insights", {
                "metric": "reach,saved,shares"
            })
        except Exception:
            ins = {"data": []}

        metrics: Dict[str, int] = {}
        for m in ins.get("data", []):
            val = m.get("values", [{}])[0].get("value", 0) if m.get("values") else m.get("value", 0)
            metrics[m["name"]] = val

        thumbnail = media.get("thumbnail_url") or media.get("media_url", "")
        return PostInsight(
            media_id=media_id,
            timestamp=media.get("timestamp", ""),
            caption=(media.get("caption") or "")[:120],
            media_type=media.get("media_type", "IMAGE"),
            thumbnail_url=thumbnail,
            permalink=media.get("permalink", ""),
            like_count=media.get("like_count", 0),
            comments_count=media.get("comments_count", 0),
            reach=metrics.get("reach", 0),
            saved=metrics.get("saved", 0),
            shares=metrics.get("shares", 0),
        )

    # ── 전체 인사이트 ─────────────────────────────────────────
    def get_all_insights(self, limit: int = 12) -> List[PostInsight]:
        results = []
        for m in self.get_recent_media(limit):
            try:
                insight = self.get_post_insight(m)
                if insight:
                    results.append(insight)
            except Exception:
                continue
        return results

    @staticmethod
    def _days_ago(n: int) -> int:
        from datetime import datetime, timedelta
        return int((datetime.utcnow() - timedelta(days=n)).timestamp())
