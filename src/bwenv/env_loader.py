"""Resolve a profile name to a Bitwarden folder and extract env vars from it.

A "profile" is a Bitwarden folder. Two kinds of items inside that folder become
env vars:

- Secure Note items: the item's name is the var name, its note body is the
  value (one var per item).
- Any item's custom fields: field name -> var name, field value -> var value
  (lets multiple vars live on one item).
"""

from __future__ import annotations

import re
import sys
from typing import Any

from bwenv import bw_client
from bwenv.exceptions import ProfileNotFoundError

_VALID_VAR_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# Bitwarden item types: 1 = login, 2 = secure note, 3 = card, 4 = identity.
_SECURE_NOTE_TYPE = 2

# Bitwarden custom field types: 0 = text, 1 = hidden, 2 = boolean, 3 = linked.
_STRING_FIELD_TYPES = {0, 1}


def _find_folder(folders: list[dict[str, Any]], profile: str) -> dict[str, Any]:
    matches = [f for f in folders if (f.get("name") or "").lower() == profile.lower()]
    if not matches:
        available = [f["name"] for f in folders if f.get("name")]
        raise ProfileNotFoundError(profile, available)
    return matches[0]


def _add_var(env_vars: dict[str, str], name: str | None, value: Any, source: str | None) -> None:
    if not name or value is None:
        return

    if not _VALID_VAR_NAME.match(name):
        print(
            f"bwenv: skipping {name!r} on item {source!r} (not a valid env var name)",
            file=sys.stderr,
        )
        return

    if name in env_vars:
        print(
            f"bwenv: duplicate var {name!r} on item {source!r}, overriding previous value",
            file=sys.stderr,
        )

    env_vars[name] = str(value)


def _extract_env_vars(items: list[dict[str, Any]]) -> dict[str, str]:
    env_vars: dict[str, str] = {}
    for item in items:
        item_name = item.get("name")

        if item.get("type") == _SECURE_NOTE_TYPE and item.get("notes") is not None:
            _add_var(env_vars, item_name, item["notes"], item_name)

        for field in item.get("fields") or []:
            field_type = field.get("type")
            if field_type not in _STRING_FIELD_TYPES:
                continue
            _add_var(env_vars, field.get("name"), field.get("value"), item_name)

    if not env_vars:
        print("bwenv: warning: profile has no usable env vars", file=sys.stderr)

    return env_vars


def load_profile_env(profile: str, session: str) -> dict[str, str]:
    folders = bw_client.list_folders(session)
    folder = _find_folder(folders, profile)
    items = bw_client.list_items(session, folder["id"])
    return _extract_env_vars(items)


def list_profile_names(session: str) -> list[str]:
    folders = bw_client.list_folders(session)
    return sorted(f["name"] for f in folders if f.get("name"))
