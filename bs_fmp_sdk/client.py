from __future__ import annotations

import logging
import warnings
from collections.abc import Mapping, Sequence
from typing import Any

import fmrest
from urllib3.exceptions import InsecureRequestWarning

from .config import FileMakerConfig
from .exceptions import FileMakerAuthError, FileMakerError, FileMakerLayoutError
from .layouts import Layouts

logger = logging.getLogger(__name__)


class FileMakerClient:
    """
    Hardened low-level FileMaker Data API client.

    This wrapper is intentionally usable on its own for quick scripts and
    notebooks, while also serving as the transport layer for higher-level
    business workflows.
    """

    MAX_RETRIES = 3

    def __init__(self, config: FileMakerConfig) -> None:
        self._config = config
        self._server: fmrest.Server | None = None
        warnings.filterwarnings("ignore", category=InsecureRequestWarning)
        fmrest.utils.TIMEOUT = config.timeout

    @property
    def default_layout(self) -> str | None:
        return self._config.default_layout

    def ping(self, layout_name: str | None = None) -> bool:
        try:
            self._ensure_server(self._resolve_layout(layout_name))
            return True
        except FileMakerAuthError:
            raise
        except Exception:
            return False

    def check_layout(self, layout_name: str) -> bool:
        try:
            self._ensure_server(layout_name)
            return True
        except FileMakerLayoutError:
            return False
        except Exception as exc:
            logger.warning("Layout check failed for '%s': %s", layout_name, exc)
            return False

    def logout(self) -> None:
        if self._server and self._server._token:
            try:
                self._server.logout()
            except Exception:
                pass
        self._server = None

    def __enter__(self) -> "FileMakerClient":
        return self

    def __exit__(self, *_: Any) -> None:
        self.logout()

    def get_records(
        self,
        *,
        layout_name: str | None = None,
        limit: int | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        resolved_layout = self._resolve_layout(layout_name)
        if limit is None:
            limit = self._config.fetch_limit

        foundset = self._call(
            "get_records",
            resolved_layout,
            allow_not_found=True,
            limit=limit,
            **kwargs,
        )
        if foundset is None:
            return []
        return self._foundset_to_dicts(foundset)

    def find(
        self,
        query: Sequence[Mapping[str, Any]],
        *,
        layout_name: str | None = None,
        limit: int | None = None,
        sort: Sequence[Mapping[str, str]] | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        resolved_layout = self._resolve_layout(layout_name)
        if limit is None:
            limit = self._config.fetch_limit

        foundset = self._call(
            "find",
            resolved_layout,
            allow_not_found=True,
            query=list(query),
            sort=list(sort) if sort is not None else None,
            limit=limit,
            **kwargs,
        )
        if foundset is None:
            return []
        return self._foundset_to_dicts(foundset)

    def get_record(
        self,
        record_id: int | str,
        *,
        layout_name: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any] | None:
        resolved_layout = self._resolve_layout(layout_name)
        record = self._call(
            "get_record",
            resolved_layout,
            allow_not_found=True,
            record_id=int(record_id),
            request_layout=resolved_layout,
            **kwargs,
        )
        if record is None:
            return None
        return dict(record)

    def create_record(
        self,
        field_data: Mapping[str, Any],
        *,
        layout_name: str | None = None,
        **kwargs: Any,
    ) -> Any:
        resolved_layout = self._resolve_layout(layout_name)
        return self._call(
            "create_record",
            resolved_layout,
            field_data=dict(field_data),
            **kwargs,
        )

    def edit_record(
        self,
        record_id: int | str,
        field_data: Mapping[str, Any],
        *,
        layout_name: str | None = None,
        **kwargs: Any,
    ) -> Any:
        resolved_layout = self._resolve_layout(layout_name)
        return self._call(
            "edit_record",
            resolved_layout,
            record_id=int(record_id),
            field_data=dict(field_data),
            request_layout=resolved_layout,
            **kwargs,
        )

    def delete_record(
        self,
        record_id: int | str,
        *,
        layout_name: str | None = None,
        **kwargs: Any,
    ) -> Any:
        resolved_layout = self._resolve_layout(layout_name)
        return self._call(
            "delete_record",
            resolved_layout,
            record_id=int(record_id),
            request_layout=resolved_layout,
            **kwargs,
        )

    def find_matching(
        self,
        criteria: Mapping[str, Any],
        *,
        layout_name: str | None = None,
        limit: int | None = None,
        sort: Sequence[Mapping[str, str]] | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        query = self.build_exact_query(criteria)
        return self.find(
            query,
            layout_name=layout_name,
            limit=limit,
            sort=sort,
            **kwargs,
        )

    @staticmethod
    def build_exact_query(criteria: Mapping[str, Any]) -> list[dict[str, Any]]:
        if not criteria:
            raise ValueError("At least one search criterion is required.")

        query: dict[str, Any] = {}
        for field_name, value in criteria.items():
            if value is None:
                continue
            query[field_name] = _coerce_query_value(value)

        if not query:
            raise ValueError("At least one non-null search criterion is required.")
        return [query]

    def _resolve_layout(self, layout_name: str | None) -> str:
        if layout_name:
            return layout_name
        if self._config.default_layout:
            return self._config.default_layout
        return Layouts.PROJECTS

    def _ensure_server(self, layout_name: str) -> fmrest.Server:
        if self._server is None or self._server.layout != layout_name:
            if self._server is not None and self._server._token:
                try:
                    self._server.logout()
                except Exception:
                    pass

            self._server = fmrest.Server(
                url=self._config.host,
                user=self._config.user,
                password=self._config.password,
                database=self._config.database,
                layout=layout_name,
                api_version=self._config.api_version,
                verify_ssl=self._config.verify_ssl,
                timeout=self._config.timeout,
            )
            fmrest.utils.TIMEOUT = self._config.timeout
            self._login()
        elif not self._server._token:
            self._login()

        return self._server

    def _login(self) -> None:
        if self._server is None:
            raise FileMakerError("Cannot log in before creating the server session.")

        for attempt in range(self.MAX_RETRIES):
            try:
                success = self._server.login()
                if success:
                    return
            except fmrest.exceptions.FileMakerError as exc:
                if "212" in str(exc):
                    raise FileMakerAuthError(
                        f"FileMaker authentication failed. ({exc})"
                    ) from exc
                if "105" in str(exc):
                    raise FileMakerLayoutError(
                        f"FileMaker layout not found or not accessible: '{self._server.layout}'. ({exc})"
                    ) from exc
                if attempt == self.MAX_RETRIES - 1:
                    raise FileMakerError(
                        f"FileMaker login failed after {self.MAX_RETRIES} attempts: {exc}"
                    ) from exc
            except Exception as exc:
                if attempt == self.MAX_RETRIES - 1:
                    raise FileMakerError(
                        f"FileMaker login error after {self.MAX_RETRIES} attempts: {exc}"
                    ) from exc
            logger.warning(
                "FileMaker login attempt %d/%d failed; retrying.",
                attempt + 1,
                self.MAX_RETRIES,
            )

    def _call(
        self,
        method_name: str,
        layout_name: str,
        *,
        allow_not_found: bool = False,
        **kwargs: Any,
    ) -> Any:
        last_exc: Exception | None = None
        for attempt in range(self.MAX_RETRIES):
            try:
                server = self._ensure_server(layout_name)
                method = getattr(server, method_name)
                return method(**kwargs)
            except fmrest.exceptions.FileMakerError as exc:
                exc_str = str(exc)
                if "401" in exc_str and allow_not_found:
                    return None
                if "952" in exc_str:
                    logger.info(
                        "FileMaker token expired during %s; re-authenticating (attempt %d).",
                        method_name,
                        attempt + 1,
                    )
                    if self._server and self._server._token:
                        try:
                            self._server.logout()
                        except Exception:
                            pass
                    self._server = None
                    last_exc = exc
                    continue
                if "212" in exc_str:
                    raise FileMakerAuthError(
                        f"FileMaker auth error during {method_name}: {exc}"
                    ) from exc
                if "105" in exc_str:
                    raise FileMakerLayoutError(
                        f"FileMaker layout '{layout_name}' not accessible during {method_name}: {exc}"
                    ) from exc
                last_exc = exc
                logger.warning(
                    "FileMaker error on attempt %d/%d for %s on layout '%s': %s",
                    attempt + 1,
                    self.MAX_RETRIES,
                    method_name,
                    layout_name,
                    exc,
                )
            except Exception as exc:
                last_exc = exc
                logger.warning(
                    "Error on attempt %d/%d for %s on layout '%s': %s",
                    attempt + 1,
                    self.MAX_RETRIES,
                    method_name,
                    layout_name,
                    exc,
                )

        raise FileMakerError(
            f"FileMaker {method_name} on layout '{layout_name}' failed after {self.MAX_RETRIES} attempts."
        ) from last_exc

    @staticmethod
    def _foundset_to_dicts(foundset: Any) -> list[dict[str, Any]]:
        return [dict(record) for record in foundset]


def _coerce_query_value(value: Any) -> Any:
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.startswith(("==", ">=", "<=", ">", "<", "!", "*")):
            return stripped
        return f"=={stripped}"
    return f"=={value}"
