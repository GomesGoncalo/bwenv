"""Thin wrapper around the `bw` (Bitwarden CLI) subprocess."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from typing import Any, cast

from bwenv.exceptions import (
    BwNotInstalledError,
    NotLoggedInError,
    UnlockFailedError,
)


def check_bw_installed() -> None:
    if shutil.which("bw") is None:
        raise BwNotInstalledError


def _run(args: list[str], *, session: str | None = None) -> subprocess.CompletedProcess[str]:
    cmd = ["bw", *args]
    if session is not None:
        cmd += ["--session", session]
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def get_status(session: str | None = None) -> dict[str, Any]:
    result = _run(["status"], session=session)
    return cast(dict[str, Any], json.loads(result.stdout))


def unlock_interactively() -> str:
    """Run `bw unlock` with an inherited TTY so the user can type their master
    password, capturing only the raw session key from stdout."""
    result = subprocess.run(
        ["bw", "unlock", "--raw"],
        stdout=subprocess.PIPE,
        stderr=None,
        stdin=None,
        text=True,
        check=False,
    )
    session = result.stdout.strip()
    if result.returncode != 0 or not session:
        raise UnlockFailedError(f"exit code {result.returncode}")
    return session


def resolve_session() -> str:
    """Return a usable Bitwarden session key: BW_SESSION.

    Reuses BW_SESSION from the environment if it is already unlocked; otherwise
    unlocks interactively and returns the ephemeral session key from that call.
    Never persists a session key anywhere.
    """
    env_session = os.environ.get("BW_SESSION")
    status = get_status(session=env_session)
    state = status.get("status")

    if state == "unauthenticated":
        raise NotLoggedInError

    if state == "unlocked" and env_session:
        return env_session

    return unlock_interactively()


def list_folders(session: str) -> list[dict[str, Any]]:
    result = _run(["list", "folders"], session=session)
    return cast(list[dict[str, Any]], json.loads(result.stdout))


def list_items(session: str, folder_id: str) -> list[dict[str, Any]]:
    result = _run(["list", "items", "--folderid", folder_id], session=session)
    return cast(list[dict[str, Any]], json.loads(result.stdout))
