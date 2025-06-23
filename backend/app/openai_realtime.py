"""Utility helpers for interacting with the OpenAI Realtime REST API.

Currently only supports minting an *ephemeral* client token that a browser
can later use to establish a WebRTC session with the model.  The request is
performed server-side with the standard API key so that the secret never
reaches the client.

The code purposefully keeps I/O logic in one place so the rest of the app can
stay agnostic of the OpenAI HTTP contract.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

import httpx
from typing import Any, Optional, Dict, List


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


# When running in CI or without network access we allow a graceful *offline*
# fallback: set `OPENAI_OFFLINE=1` and the helper will return a stub session
# payload instead of calling the external API.  This lets developers poke the
# FastAPI endpoints locally without needing a real key.

OPENAI_OFFLINE = os.getenv("OPENAI_OFFLINE", "0") in {"1", "true", "yes"}

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY and not OPENAI_OFFLINE:
    # pragma: no cover – fail fast in dev/run when we *do* intend to hit the
    # real API.
    raise RuntimeError(
        "OPENAI_API_KEY environment variable missing. Provide one or set OPENAI_OFFLINE=1 for stub mode."
    )


# Default model – can be overridden through env var so that staging / prod can
# test newer versions without code changes.
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-realtime-preview-2025-06-03")

# Location of the prompt / instructions that we will pass to the Realtime
# model.  Keeping it in a plain-text file makes it easy for non-technical team
# members to iterate without redeploying the backend.
INSTRUCTIONS_FILE = Path(os.getenv("INSTRUCTIONS_PATH", Path(__file__).resolve().parent / "../instructions.txt")).resolve()


def _load_instructions() -> str | None:
    """Return the content of *instructions.txt* if it exists, else None."""

    if not INSTRUCTIONS_FILE.is_file():
        return None
    return INSTRUCTIONS_FILE.read_text(encoding="utf-8").strip() or None


# Cached version so we only hit the filesystem once per process boot.  If we
# ever want hot-reload we can add a simple watchdog later.
_CACHED_INSTRUCTIONS: Optional[str] = _load_instructions()

# Tool definitions exposed to the model for function-calling
# Replace the TOOLS list with:
TOOLS: List[Dict[str, Any]] = [
    {
        "name": "mcp_call",
        "description": "Execute an OpenTrons operation via MCP server. Can handle both simple API calls and complex workflows like protocol optimization.",
        "type": "function",
        "parameters": {
            "type": "object",
            "properties": {
                "tool_name": {
                    "type": "string",
                    "description": "MCP tool to call (e.g., 'get_robot_health', 'create_tartrazine_assay_protocol', 'run_parameter_optimization_experiment')"
                },
                "arguments": {
                    "type": "object",
                    "description": "Arguments to pass to the MCP tool",
                    "nullable": True
                }
            },
            "required": ["tool_name"]
        }
    }
]


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


async def create_ephemeral_session(*, voice: str | None = None, model: str | None = None) -> dict[str, Any]:
    """Call the OpenAI REST API to create a *realtime session*.

    Parameters
    ----------
    voice: str | None
        Optional voice name.  Passes straight through if supplied.
    model: str | None
        Realtime model id.  Defaults to the value of OPENAI_MODEL.

    Returns
    -------
    dict
        The JSON payload returned by OpenAI, including `client_secret.value` –
        what the browser needs to authenticate the WebRTC connection.
    """

    # ---------------------------------------------------------------------
    # Offline stub — skips the network round-trip and returns a fake payload.
    # ---------------------------------------------------------------------

    if OPENAI_OFFLINE:
        return {
            "id": "fake_session_123",
            "client_secret": {
                "value": "sk-ephemeral-fake",
                "expires_at": 9999999999,
            },
            "created_at": 0,
            "model": model or OPENAI_MODEL,
        }

    # ---------------------------------------------------------------------
    # Live call to OpenAI REST API
    # ---------------------------------------------------------------------

    url = "https://api.openai.com/v1/realtime/sessions"

    payload: Dict[str, Any] = {
        "model": model or OPENAI_MODEL,
        # Include available tools for function calling
        "tools": TOOLS,
        "tool_choice": "auto",
        # Allow both audio and text responses
        "modalities": ["audio", "text"],
    }
    if voice is not None:
        payload["voice"] = voice

    # Attach instructions if available.
    if _CACHED_INSTRUCTIONS is not None:
        payload["instructions"] = _CACHED_INSTRUCTIONS

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, json=payload, headers=headers)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:  # pragma: no cover
            msg = f"OpenAI realtime session creation failed: {exc.response.text}"
            raise RuntimeError(msg) from exc

        return resp.json()
