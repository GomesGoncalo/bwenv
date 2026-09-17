"""Launch the user's shell with extra environment variables merged in."""

from __future__ import annotations

import os
import shutil

from bwenv.exceptions import ShellNotFoundError

DEFAULT_SHELL = "/bin/sh"


def resolve_shell(shell_override: str | None = None) -> str:
    shell = shell_override or os.environ.get("SHELL") or DEFAULT_SHELL
    resolved = shutil.which(shell)
    if resolved is None:
        raise ShellNotFoundError(shell)
    return resolved


def _merged_env(extra_env: dict[str, str]) -> dict[str, str]:
    return {**os.environ, **extra_env}


def exec_shell_with_env(extra_env: dict[str, str], shell_override: str | None = None) -> None:
    """Replace the current process with the resolved shell, environment merged
    from the current process env plus `extra_env` (which takes precedence)."""
    shell = resolve_shell(shell_override)
    env = _merged_env(extra_env)
    os.execvpe(shell, [shell], env)


def exec_command_with_env(command: list[str], extra_env: dict[str, str]) -> None:
    """Replace the current process with `command`, environment merged from the
    current process env plus `extra_env` (which takes precedence)."""
    env = _merged_env(extra_env)
    os.execvpe(command[0], command, env)
