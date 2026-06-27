"""
Secure KB API Client

This client reads credentials ONLY from environment variables.
No secrets are hardcoded - safe for open source.

Required environment variables:
- KB_API_BASE_URL: API base URL
- KB_API_USERNAME: API username
- KB_API_PASSWORD: API password

For demo mode, set DEMO_MODE=true to use mock data instead.
"""

import os
from typing import Any, Dict, List, Optional
import requests


class KBClientError(Exception):
    """KB API error."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class KBClient:
    """
    Secure KB API client.

    Credentials are read from environment variables only.
    This file contains NO secrets and is safe for open source distribution.
    """

    def __init__(self):
        """Initialize client from environment variables."""
        self.base_url = os.getenv("KB_API_BASE_URL", "").rstrip("/")
        self._username = os.getenv("KB_API_USERNAME", "")
        self._password = os.getenv("KB_API_PASSWORD", "")
        self._token: Optional[str] = None

    def is_configured(self) -> bool:
        """Check if API credentials are configured."""
        return bool(self.base_url and self._username and self._password)

    def _ensure_auth(self):
        """Ensure we have a valid auth token."""
        if self._token:
            return

        if not self.is_configured():
            raise KBClientError(
                "API not configured. Set KB_API_BASE_URL, KB_API_USERNAME, KB_API_PASSWORD environment variables."
            )

        try:
            response = requests.post(
                f"{self.base_url}/auth/login/",
                json={"username": self._username, "password": self._password},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            self._token = data.get("token") or data.get("access")
            if not self._token:
                raise KBClientError("Login failed: no token in response")
        except requests.RequestException as e:
            raise KBClientError(f"Login failed: {e}")

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

            # Handle 401 - try re-login once
            if response.status_code == 401:
                self._token = None
                self._ensure_auth()
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
            raise KBClientError(f"API request failed: {e}", status_code)

    # ------------------------------------------------------------------
    # File Operations
    # ------------------------------------------------------------------

    def list_files(
        self,
        q: Optional[str] = None,
        kb: Optional[int] = None,
        source: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        List files from knowledge base.

        Args:
            q: Search query
            kb: Knowledge base ID to filter by
            source: Source type filter
            page: Page number
            page_size: Results per page

        Returns:
            Dict with 'results' list and pagination info
        """
        params = {"page": page, "page_size": page_size}
        if q:
            params["q"] = q
        if kb:
            params["kb"] = kb
        if source:
            params["source"] = source

        data = self._request("GET", "files/", params=params)
        # Normalize response format: API returns 'files', we use 'results'
        if "files" in data and "results" not in data:
            data["results"] = data.pop("files")
        if "total" in data and "count" not in data:
            data["count"] = data["total"]
        return data

    def get_file(self, file_id: int) -> Dict[str, Any]:
        """Get file details by ID."""
        return self._request("GET", f"files/{file_id}/")

    def list_kb_files(
        self,
        kb_id: int,
        q: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """List files in a specific knowledge base."""
        params = {"page": page, "page_size": page_size}
        if q:
            params["q"] = q
        data = self._request("GET", f"knowledge-bases/{kb_id}/files/", params=params)
        # Normalize response format
        if "files" in data and "results" not in data:
            data["results"] = data.pop("files")
        if "total" in data and "count" not in data:
            data["count"] = data["total"]
        return data

    # ------------------------------------------------------------------
    # Knowledge Base Operations
    # ------------------------------------------------------------------

    def list_kbs(
        self,
        q: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """List knowledge bases."""
        params = {"page": page, "page_size": page_size}
        if q:
            params["q"] = q
        data = self._request("GET", "knowledge-bases/", params=params)
        # Normalize response format
        if "knowledge_bases" in data and "results" not in data:
            data["results"] = data.pop("knowledge_bases")
        if "total" in data and "count" not in data:
            data["count"] = data["total"]
        return data

    # ------------------------------------------------------------------
    # RAG Search
    # ------------------------------------------------------------------

    def create_conversation(self, kb_ids: List[int]) -> Dict[str, Any]:
        """Create a new RAG conversation."""
        return self._request("POST", "conversations/create/", json={"kb_ids": kb_ids})

    def send_message(
        self,
        conversation_id: int,
        message: str,
        stream: bool = False
    ) -> Dict[str, Any]:
        """Send message to conversation for RAG search."""
        return self._request(
            "POST",
            f"conversations/{conversation_id}/send/",
            json={"message": message, "stream": "true" if stream else "false"}
        )

    def delete_conversation(self, conversation_id: int) -> Dict[str, Any]:
        """Delete a conversation."""
        return self._request("DELETE", f"conversations/{conversation_id}/delete/")


def get_kb_client() -> Optional[KBClient]:
    """
    Get KB client if configured, None otherwise.

    Usage:
        client = get_kb_client()
        if client:
            files = client.list_files(page_size=50)
        else:
            # Use mock data
            pass
    """
    client = KBClient()
    if client.is_configured():
        return client
    return None


# ------------------------------------------------------------------
# Convenience function for demo/production switching
# ------------------------------------------------------------------

def is_demo_mode() -> bool:
    """Check if running in demo mode (no real API)."""
    # 只有当环境变量 DEMO_MODE=true 或 KB 未配置时才使用 demo mode
    if os.getenv("DEMO_MODE", "").lower() == "true":
        return True
    client = KBClient()
    return not client.is_configured()
