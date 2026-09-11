from __future__ import annotations

import json
import subprocess

import pytest
from pytest_mock import MockerFixture

from bwenv import bw_client
from bwenv.exceptions import BwNotInstalledError, NotLoggedInError, UnlockFailedError


def _completed(stdout: str, returncode: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=["bw"], returncode=returncode, stdout=stdout, stderr="")


def test_check_bw_installed_raises_when_missing(mocker: MockerFixture) -> None:
    mocker.patch("shutil.which", return_value=None)
    with pytest.raises(BwNotInstalledError):
        bw_client.check_bw_installed()


def test_check_bw_installed_ok_when_present(mocker: MockerFixture) -> None:
    mocker.patch("shutil.which", return_value="/usr/bin/bw")
    bw_client.check_bw_installed()  # should not raise


def test_get_status_parses_json(mocker: MockerFixture) -> None:
    status_json = json.dumps({"status": "unlocked"})
    run = mocker.patch("subprocess.run", return_value=_completed(status_json))
    status = bw_client.get_status(session="abc")
    assert status == {"status": "unlocked"}
    args = run.call_args.args[0]
    assert args == ["bw", "status", "--session", "abc"]


def test_unlock_interactively_returns_session(mocker: MockerFixture) -> None:
    mocker.patch("subprocess.run", return_value=_completed("the-session-key\n"))
    assert bw_client.unlock_interactively() == "the-session-key"


def test_unlock_interactively_raises_on_failure(mocker: MockerFixture) -> None:
    mocker.patch("subprocess.run", return_value=_completed("", returncode=1))
    with pytest.raises(UnlockFailedError):
        bw_client.unlock_interactively()


def test_resolve_session_reuses_env_session_when_unlocked(mocker: MockerFixture) -> None:
    mocker.patch.dict("os.environ", {"BW_SESSION": "existing-session"})
    mocker.patch("bwenv.bw_client.get_status", return_value={"status": "unlocked"})
    unlock = mocker.patch("bwenv.bw_client.unlock_interactively")
    assert bw_client.resolve_session() == "existing-session"
    unlock.assert_not_called()


def test_resolve_session_unlocks_when_locked(mocker: MockerFixture) -> None:
    mocker.patch.dict("os.environ", {}, clear=True)
    mocker.patch("bwenv.bw_client.get_status", return_value={"status": "locked"})
    mocker.patch("bwenv.bw_client.unlock_interactively", return_value="fresh-session")
    assert bw_client.resolve_session() == "fresh-session"


def test_resolve_session_raises_when_unauthenticated(mocker: MockerFixture) -> None:
    mocker.patch("bwenv.bw_client.get_status", return_value={"status": "unauthenticated"})
    with pytest.raises(NotLoggedInError):
        bw_client.resolve_session()


def test_list_folders_parses_json(mocker: MockerFixture) -> None:
    folders = [{"id": "1", "name": "prod"}]
    mocker.patch("subprocess.run", return_value=_completed(json.dumps(folders)))
    assert bw_client.list_folders("sess") == folders


def test_list_items_parses_json(mocker: MockerFixture) -> None:
    items = [{"id": "1", "name": "api", "fields": []}]
    run = mocker.patch("subprocess.run", return_value=_completed(json.dumps(items)))
    assert bw_client.list_items("sess", "folder-1") == items
    args = run.call_args.args[0]
    assert args == ["bw", "list", "items", "--folderid", "folder-1", "--session", "sess"]
