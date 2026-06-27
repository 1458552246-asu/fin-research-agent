"""
Subscription Manager

Manages social media subscriptions with email notifications.
Migrated from aichat-kb-search with API URL abstraction.
"""

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum

import requests


class SubscriptionPlatform(str, Enum):
    """Supported subscription platforms."""
    TWITTER = "twitter"
    SUBSTACK = "substack"
    YOUTUBE = "youtube"


class SubscriptionStatus(str, Enum):
    """Subscription status."""
    ACTIVE = "active"
    PAUSED = "paused"


@dataclass
class Subscription:
    """A subscription record."""
    id: int
    platform: str
    screen_name: str
    display_name: str = ""
    filter_keywords: List[str] = field(default_factory=list)
    status: str = "active"
    notify_emails: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


class APIError(Exception):
    """API call error."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class SubscriptionManager:
    """Manages social media subscriptions via API."""

    def __init__(self, base_url: Optional[str] = None, username: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize subscription manager.

        Args:
            base_url: API base URL (from env KB_API_BASE_URL if not provided)
            username: API username (from env KB_API_USERNAME if not provided)
            password: API password (from env KB_API_PASSWORD if not provided)
        """
        self.base_url = (base_url or os.getenv("KB_API_BASE_URL", "")).rstrip("/")
        self.username = username or os.getenv("KB_API_USERNAME", "")
        self.password = password or os.getenv("KB_API_PASSWORD", "")
        self._token: Optional[str] = None

    def _ensure_auth(self):
        """Ensure we have a valid auth token."""
        if self._token:
            return

        if not self.base_url or not self.username or not self.password:
            raise APIError("API credentials not configured. Set KB_API_BASE_URL, KB_API_USERNAME, KB_API_PASSWORD.")

        # Login to get token
        try:
            response = requests.post(
                f"{self.base_url}/auth/login/",
                json={"username": self.username, "password": self.password},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            self._token = data.get("access") or data.get("token")
            if not self._token:
                raise APIError("Login failed: no token returned")
        except requests.RequestException as e:
            raise APIError(f"Login failed: {e}")

    def _headers(self) -> Dict[str, str]:
        """Get request headers with auth."""
        headers = {"Content-Type": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Make authenticated API request."""
        self._ensure_auth()

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = requests.request(
                method, url,
                headers=self._headers(),
                timeout=30,
                **kwargs
            )
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.RequestException as e:
            status_code = getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            raise APIError(f"API request failed: {e}", status_code)

    # ------------------------------------------------------------------
    # Subscription CRUD
    # ------------------------------------------------------------------

    def list_subscriptions(
        self,
        platform: Optional[str] = None,
        status: Optional[str] = None,
        query: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        List all subscriptions.

        Args:
            platform: Filter by platform (twitter, substack, youtube)
            status: Filter by status (active, paused)
            query: Search query
            page: Page number
            page_size: Results per page

        Returns:
            Dict with 'results' list and pagination info
        """
        params = {"page": page, "page_size": page_size}
        if platform:
            params["platform"] = platform
        if status:
            params["status"] = status
        if query:
            params["q"] = query

        return self._request("GET", "subscriptions/", params=params)

    def create_subscription(
        self,
        platform: str,
        screen_name: str,
        filter_keywords: Optional[List[str]] = None,
        notify_emails: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new subscription.

        Args:
            platform: Platform (twitter, substack, youtube)
            screen_name: Account name to subscribe to
            filter_keywords: Keywords to filter content (optional)
            notify_emails: Email addresses for notifications (required)

        Returns:
            Created subscription data
        """
        if not notify_emails:
            raise ValueError("notify_emails is required for subscriptions")

        payload = {
            "platform": platform,
            "screen_name": screen_name,
            "notify_emails": ",".join(notify_emails)
        }

        if filter_keywords:
            payload["filter_keywords"] = ",".join(filter_keywords)

        return self._request("POST", "subscriptions/create/", json=payload)

    def get_subscription(self, sub_id: int) -> Dict[str, Any]:
        """Get subscription details."""
        return self._request("GET", f"subscriptions/{sub_id}/")

    def update_subscription(
        self,
        sub_id: int,
        display_name: Optional[str] = None,
        filter_keywords: Optional[List[str]] = None,
        status: Optional[str] = None,
        notify_emails: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Update a subscription.

        Args:
            sub_id: Subscription ID
            display_name: New display name
            filter_keywords: New filter keywords
            status: New status (active, paused)
            notify_emails: New notification emails

        Returns:
            Updated subscription data
        """
        payload = {}
        if display_name is not None:
            payload["display_name"] = display_name
        if filter_keywords is not None:
            payload["filter_keywords"] = ",".join(filter_keywords)
        if status is not None:
            payload["status"] = status
        if notify_emails is not None:
            payload["notify_emails"] = ",".join(notify_emails)

        return self._request("PUT", f"subscriptions/{sub_id}/update/", json=payload)

    def delete_subscription(self, sub_id: int) -> Dict[str, Any]:
        """Delete a subscription."""
        return self._request("DELETE", f"subscriptions/{sub_id}/delete/")

    def toggle_subscription(self, sub_id: int) -> Dict[str, Any]:
        """Toggle subscription active/paused status."""
        return self._request("POST", f"subscriptions/{sub_id}/toggle/")

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------

    def parse_subscription(self, data: Dict[str, Any]) -> Subscription:
        """Parse API response into Subscription object."""
        keywords = data.get("filter_keywords", "")
        if isinstance(keywords, str):
            keywords = [k.strip() for k in keywords.split(",") if k.strip()]

        emails = data.get("notify_emails", "")
        if isinstance(emails, str):
            emails = [e.strip() for e in emails.split(",") if e.strip()]

        return Subscription(
            id=data.get("id", 0),
            platform=data.get("platform", ""),
            screen_name=data.get("screen_name", ""),
            display_name=data.get("display_name", ""),
            filter_keywords=keywords,
            status=data.get("status", "active"),
            notify_emails=emails,
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", "")
        )


# ------------------------------------------------------------------
# Mock data for demo mode
# ------------------------------------------------------------------

MOCK_SUBSCRIPTIONS = [
    {
        "id": 1,
        "platform": "twitter",
        "screen_name": "elonmusk",
        "display_name": "Elon Musk",
        "filter_keywords": "Tesla,FSD,Robotaxi,xAI",
        "status": "active",
        "notify_emails": "analyst@example.com",
        "created_at": "2025-06-01T10:00:00Z",
        "updated_at": "2025-06-15T08:30:00Z"
    },
    {
        "id": 2,
        "platform": "twitter",
        "screen_name": "jensen_huang",
        "display_name": "Jensen Huang",
        "filter_keywords": "NVIDIA,Blackwell,AI,GPU",
        "status": "active",
        "notify_emails": "analyst@example.com",
        "created_at": "2025-06-02T11:00:00Z",
        "updated_at": "2025-06-20T09:00:00Z"
    },
    {
        "id": 3,
        "platform": "substack",
        "screen_name": "kyla_scanlon",
        "display_name": "Kyla Scanlon",
        "filter_keywords": "macro,fed,economy",
        "status": "paused",
        "notify_emails": "team@example.com",
        "created_at": "2025-06-05T14:00:00Z",
        "updated_at": "2025-06-10T16:00:00Z"
    },
    {
        "id": 4,
        "platform": "youtube",
        "screen_name": "AllInPodcast",
        "display_name": "All-In Podcast",
        "filter_keywords": "AI,startup,tech",
        "status": "active",
        "notify_emails": "analyst@example.com,team@example.com",
        "created_at": "2025-06-08T09:00:00Z",
        "updated_at": "2025-06-25T12:00:00Z"
    }
]


class MockSubscriptionManager:
    """Mock subscription manager for demo mode."""

    def __init__(self):
        self._subscriptions = list(MOCK_SUBSCRIPTIONS)
        self._next_id = 100

    def list_subscriptions(
        self,
        platform: Optional[str] = None,
        status: Optional[str] = None,
        query: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        results = self._subscriptions.copy()

        if platform:
            results = [s for s in results if s["platform"] == platform]
        if status:
            results = [s for s in results if s["status"] == status]
        if query:
            query_lower = query.lower()
            results = [s for s in results if
                       query_lower in s["screen_name"].lower() or
                       query_lower in s.get("display_name", "").lower()]

        start = (page - 1) * page_size
        end = start + page_size
        paged = results[start:end]

        return {
            "count": len(results),
            "results": paged,
            "page": page,
            "page_size": page_size
        }

    def create_subscription(
        self,
        platform: str,
        screen_name: str,
        filter_keywords: Optional[List[str]] = None,
        notify_emails: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        new_sub = {
            "id": self._next_id,
            "platform": platform,
            "screen_name": screen_name,
            "display_name": screen_name,
            "filter_keywords": ",".join(filter_keywords) if filter_keywords else "",
            "status": "active",
            "notify_emails": ",".join(notify_emails) if notify_emails else "",
            "created_at": "2025-06-27T00:00:00Z",
            "updated_at": "2025-06-27T00:00:00Z"
        }
        self._next_id += 1
        self._subscriptions.append(new_sub)
        return new_sub

    def get_subscription(self, sub_id: int) -> Dict[str, Any]:
        for sub in self._subscriptions:
            if sub["id"] == sub_id:
                return sub
        raise APIError(f"Subscription {sub_id} not found", 404)

    def update_subscription(
        self,
        sub_id: int,
        display_name: Optional[str] = None,
        filter_keywords: Optional[List[str]] = None,
        status: Optional[str] = None,
        notify_emails: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        for sub in self._subscriptions:
            if sub["id"] == sub_id:
                if display_name is not None:
                    sub["display_name"] = display_name
                if filter_keywords is not None:
                    sub["filter_keywords"] = ",".join(filter_keywords)
                if status is not None:
                    sub["status"] = status
                if notify_emails is not None:
                    sub["notify_emails"] = ",".join(notify_emails)
                return sub
        raise APIError(f"Subscription {sub_id} not found", 404)

    def delete_subscription(self, sub_id: int) -> Dict[str, Any]:
        for i, sub in enumerate(self._subscriptions):
            if sub["id"] == sub_id:
                self._subscriptions.pop(i)
                return {"success": True}
        raise APIError(f"Subscription {sub_id} not found", 404)

    def toggle_subscription(self, sub_id: int) -> Dict[str, Any]:
        for sub in self._subscriptions:
            if sub["id"] == sub_id:
                sub["status"] = "paused" if sub["status"] == "active" else "active"
                return sub
        raise APIError(f"Subscription {sub_id} not found", 404)

    def parse_subscription(self, data: Dict[str, Any]) -> Subscription:
        keywords = data.get("filter_keywords", "")
        if isinstance(keywords, str):
            keywords = [k.strip() for k in keywords.split(",") if k.strip()]

        emails = data.get("notify_emails", "")
        if isinstance(emails, str):
            emails = [e.strip() for e in emails.split(",") if e.strip()]

        return Subscription(
            id=data.get("id", 0),
            platform=data.get("platform", ""),
            screen_name=data.get("screen_name", ""),
            display_name=data.get("display_name", ""),
            filter_keywords=keywords,
            status=data.get("status", "active"),
            notify_emails=emails,
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", "")
        )


def get_subscription_manager(use_mock: bool = False) -> "SubscriptionManager | MockSubscriptionManager":
    """
    Get appropriate subscription manager.

    Args:
        use_mock: If True, return mock manager for demo mode

    Returns:
        SubscriptionManager or MockSubscriptionManager instance
    """
    if use_mock:
        return MockSubscriptionManager()
    return SubscriptionManager()
