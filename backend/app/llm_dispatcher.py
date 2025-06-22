"""Maps LLM function-call events to actual CRUD operations."""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from .crud import create_move, create_task, get_moves, get_tasks
from .models import Move, Task, User
import os
import httpx


class FunctionCallError(Exception):
    """Raised when an LLM function-call event is invalid or unsupported."""


def _parse_date(val: str | None) -> date | None:
    if val is None:
        return None
    try:
        return date.fromisoformat(val)
    except (TypeError, ValueError):
        raise FunctionCallError(f"Invalid date format: {val!r} – expected YYYY-MM-DD")


def handle_function_call(name: str, args: dict[str, Any], *, db: Session) -> Any:
    """Dispatch an LLM function call to the appropriate CRUD helper.

    Parameters
    ----------
    name: str
        Name of the function (as emitted by the LLM)
    args: dict
        Arguments payload.
    db: Session
    user: User

    Returns
    -------
    Any – typically a SQLAlchemy model instance.
    """

    
    # Extend with more operations here ...
    if name == "external_api_call":
        endpoint = args.get("endpoint")
        method = args.get("method", "GET").upper()
        body = args.get("body") or {}
        base_url = os.getenv("EXTERNAL_API_BASE_URL")
        if not base_url:
            raise FunctionCallError("External API base URL not configured")
        url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        try:
            resp = httpx.request(method, url, json=body)
            resp.raise_for_status()
            try:
                data = resp.json()
            except ValueError:
                data = resp.text
            return {"status_code": resp.status_code, "body": data}
        except Exception as exc:
            raise FunctionCallError(f"External API request failed: {exc}")
    else:
        raise FunctionCallError(f"Unsupported function name: {name}")
