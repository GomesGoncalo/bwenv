from __future__ import annotations

import pytest
from pytest_mock import MockerFixture

from bwenv import cli


def test_main_requires_profile_or_list_flag(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = None
    try:
        cli.main([])
    except SystemExit as exc:
        exit_code = exc.code
    assert exit_code == 2
    assert "profile name is required" in capsys.readouterr().err


def test_main_list_profiles(mocker: MockerFixture, capsys: pytest.CaptureFixture[str]) -> None:
    mocker.patch("bwenv.bw_client.check_bw_installed")
    mocker.patch("bwenv.bw_client.resolve_session", return_value="sess")
    mocker.patch("bwenv.env_loader.list_profile_names", return_value=["prod", "staging"])

    assert cli.main(["--list-profiles"]) == 0
    out = capsys.readouterr().out
    assert out == "prod\nstaging\n"


def test_main_loads_profile_and_execs_shell(mocker: MockerFixture) -> None:
    mocker.patch("bwenv.bw_client.check_bw_installed")
    mocker.patch("bwenv.bw_client.resolve_session", return_value="sess")
    mocker.patch("bwenv.env_loader.load_profile_env", return_value={"FOO": "bar"})
    exec_shell = mocker.patch("bwenv.shell.exec_shell_with_env")

    assert cli.main(["prod", "--shell", "zsh"]) == 0
    exec_shell.assert_called_once_with({"FOO": "bar"}, "zsh")


def test_main_prints_bwenv_error_and_returns_1(
    mocker: MockerFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    from bwenv.exceptions import ProfileNotFoundError

    mocker.patch("bwenv.bw_client.check_bw_installed")
    mocker.patch("bwenv.bw_client.resolve_session", return_value="sess")
    mocker.patch(
        "bwenv.env_loader.load_profile_env",
        side_effect=ProfileNotFoundError("nope", ["prod"]),
    )

    assert cli.main(["nope"]) == 1
    assert "bwenv:" in capsys.readouterr().err
