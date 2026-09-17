from __future__ import annotations

import pytest
from pytest_mock import MockerFixture

from bwenv import shell
from bwenv.exceptions import ShellNotFoundError


def test_resolve_shell_uses_override(mocker: MockerFixture) -> None:
    mocker.patch("shutil.which", return_value="/usr/bin/zsh")
    assert shell.resolve_shell("zsh") == "/usr/bin/zsh"


def test_resolve_shell_falls_back_to_env(mocker: MockerFixture) -> None:
    mocker.patch.dict("os.environ", {"SHELL": "/bin/bash"})
    mocker.patch("shutil.which", return_value="/bin/bash")
    assert shell.resolve_shell() == "/bin/bash"


def test_resolve_shell_falls_back_to_default(mocker: MockerFixture) -> None:
    mocker.patch.dict("os.environ", {}, clear=True)
    mocker.patch("shutil.which", return_value="/bin/sh")
    assert shell.resolve_shell() == "/bin/sh"


def test_resolve_shell_raises_when_not_found(mocker: MockerFixture) -> None:
    mocker.patch("shutil.which", return_value=None)
    with pytest.raises(ShellNotFoundError):
        shell.resolve_shell("nonexistent-shell")


def test_exec_shell_with_env_merges_and_execs(mocker: MockerFixture) -> None:
    mocker.patch.dict("os.environ", {"EXISTING": "1"}, clear=True)
    mocker.patch("bwenv.shell.resolve_shell", return_value="/bin/bash")
    execvpe = mocker.patch("os.execvpe")

    shell.exec_shell_with_env({"FOO": "bar"})

    execvpe.assert_called_once()
    called_shell, argv, env = execvpe.call_args.args
    assert called_shell == "/bin/bash"
    assert argv == ["/bin/bash"]
    assert env == {"EXISTING": "1", "FOO": "bar"}


def test_exec_command_with_env_merges_and_execs(mocker: MockerFixture) -> None:
    mocker.patch.dict("os.environ", {"EXISTING": "1"}, clear=True)
    execvpe = mocker.patch("os.execvpe")

    shell.exec_command_with_env(["echo", "hi"], {"FOO": "bar"})

    execvpe.assert_called_once()
    called_cmd, argv, env = execvpe.call_args.args
    assert called_cmd == "echo"
    assert argv == ["echo", "hi"]
    assert env == {"EXISTING": "1", "FOO": "bar"}
