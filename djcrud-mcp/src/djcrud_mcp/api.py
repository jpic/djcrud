from __future__ import annotations

from typing import Any, Callable

import httpx


def login(*, base_url: str, username: str, password: str, timeout: float = 30.0) -> str:
    url = f"{base_url.rstrip('/')}/api/login/"
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        response = client.post(
            url,
            json={"username": username, "password": password},
            headers={"Accept": "application/json"},
        )
        response.raise_for_status()
        payload = response.json()
    token = payload.get("token")
    if not isinstance(token, str) or not token:
        raise ValueError("login response missing token")
    return token


class CrudApi:
    def __init__(
        self,
        *,
        base_url: str,
        token: str,
        timeout: float = 30.0,
        extra_headers: dict[str, str] | Callable[[], dict[str, str]] | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout
        self._extra_headers = extra_headers

    def _resolved_extra_headers(self) -> dict[str, str]:
        if self._extra_headers is None:
            return {}
        if callable(self._extra_headers):
            return dict(self._extra_headers())
        return dict(self._extra_headers)

    def _headers(self, accept_json: bool = True) -> dict[str, str]:
        headers = {"Authorization": f"Bearer {self.token}"}
        if accept_json:
            headers["Accept"] = "application/json"
        headers.update(self._resolved_extra_headers())
        return headers

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> httpx.Response:
        url = f"{self.base_url}{path}"
        effective_timeout = self.timeout if timeout is None else timeout
        with httpx.Client(timeout=effective_timeout, follow_redirects=True) as client:
            return client.request(
                method.upper(),
                url,
                headers=self._headers(),
                params=params,
                json=json_body,
            )

    def fetch_schema(self) -> dict[str, Any]:
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/api/schema/",
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            return response.json()

    def fetch_json(self, path: str) -> Any:
        with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
            response = client.get(
                f"{self.base_url}{path}",
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            return response.json()


def list_profiles(*, base_url: str) -> list[str]:
    payload = CrudApi(base_url=base_url, token="").fetch_json("/api/mcp/profiles/")
    if isinstance(payload, dict):
        keys = payload.get("profiles", payload.get("keys", []))
    else:
        keys = payload
    return [str(key) for key in keys]


def fetch_profile(*, base_url: str, key: str):
    from .profiles import RegistryProfile

    normalized = key.strip().lower()
    payload = CrudApi(base_url=base_url, token="").fetch_json(
        f"/api/mcp/profiles/{normalized}/"
    )
    return RegistryProfile.from_dict(payload)


def fetch_viewsets(*, base_url: str) -> list[dict[str, str]]:
    payload = CrudApi(base_url=base_url, token="").fetch_json("/api/mcp/viewsets/")
    if isinstance(payload, dict):
        entries = payload.get("viewsets", [])
    else:
        entries = payload
    return [
        {
            "model": str(entry["model"]),
            "prefix": str(entry["prefix"]),
        }
        for entry in entries
    ]