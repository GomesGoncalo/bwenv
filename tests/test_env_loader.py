from __future__ import annotations

from typing import Any

import pytest
from pytest_mock import MockerFixture

from bwenv import env_loader
from bwenv.exceptions import ProfileNotFoundError

FOLDERS = [
    {"id": "f1", "name": "prod"},
    {"id": "f2", "name": "Staging"},
]


def _field(name: str, value: str, field_type: int = 0) -> dict[str, Any]:
    return {"name": name, "value": value, "type": field_type}


def _secure_note(name: str, notes: str | None) -> dict[str, Any]:
    return {"name": name, "type": 2, "notes": notes, "fields": []}


def test_find_folder_case_insensitive() -> None:
    folder = env_loader._find_folder(FOLDERS, "STAGING")
    assert folder["id"] == "f2"


def test_find_folder_raises_when_missing() -> None:
    with pytest.raises(ProfileNotFoundError):
        env_loader._find_folder(FOLDERS, "nope")


def test_extract_env_vars_collects_text_and_hidden_fields(
    capsys: pytest.CaptureFixture[str],
) -> None:
    items = [
        {
            "name": "api",
            "fields": [
                _field("DATABASE_URL", "postgres://x", field_type=0),
                _field("API_KEY", "secret", field_type=1),
                _field("SOME_BOOL", "true", field_type=2),
            ],
        }
    ]
    env_vars = env_loader._extract_env_vars(items)
    assert env_vars == {"DATABASE_URL": "postgres://x", "API_KEY": "secret"}


def test_extract_env_vars_collects_secure_notes(capsys: pytest.CaptureFixture[str]) -> None:
    items = [_secure_note("FOO", "bar"), _secure_note("EMPTY_NOTE", None)]
    env_vars = env_loader._extract_env_vars(items)
    assert env_vars == {"FOO": "bar"}


def test_extract_env_vars_skips_invalid_names(capsys: pytest.CaptureFixture[str]) -> None:
    items = [{"name": "api", "fields": [_field("not a var!", "x")]}]
    env_vars = env_loader._extract_env_vars(items)
    assert env_vars == {}
    assert "not a valid env var name" in capsys.readouterr().err


def test_extract_env_vars_last_duplicate_wins(capsys: pytest.CaptureFixture[str]) -> None:
    items: list[dict[str, Any]] = [
        {"name": "first", "fields": [_field("FOO", "one")]},
        _secure_note("FOO", "two"),
    ]
    env_vars = env_loader._extract_env_vars(items)
    assert env_vars == {"FOO": "two"}
    assert "duplicate var" in capsys.readouterr().err


def test_extract_env_vars_warns_when_empty(capsys: pytest.CaptureFixture[str]) -> None:
    env_vars = env_loader._extract_env_vars([{"name": "api", "fields": []}])
    assert env_vars == {}
    assert "no usable env vars" in capsys.readouterr().err


def test_load_profile_env_orchestrates_calls(mocker: MockerFixture) -> None:
    mocker.patch("bwenv.bw_client.list_folders", return_value=FOLDERS)
    list_items = mocker.patch(
        "bwenv.bw_client.list_items",
        return_value=[{"name": "api", "fields": [_field("FOO", "bar")]}],
    )
    env_vars = env_loader.load_profile_env("prod", "sess")
    assert env_vars == {"FOO": "bar"}
    list_items.assert_called_once_with("sess", "f1")


def test_list_profile_names(mocker: MockerFixture) -> None:
    mocker.patch("bwenv.bw_client.list_folders", return_value=FOLDERS)
    assert env_loader.list_profile_names("sess") == ["Staging", "prod"]
