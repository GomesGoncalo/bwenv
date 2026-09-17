"""bwenv: load a Bitwarden-folder profile as env vars and exec your shell."""

from __future__ import annotations

import argparse
import sys

from bwenv import bw_client, env_loader, shell
from bwenv.exceptions import BwenvError


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bwenv",
        description=(
            "Load environment variables from a Bitwarden folder (profile) and "
            "exec your shell with them set. Pass `-- <command>` to run a "
            "command with those vars instead of opening a shell."
        ),
    )
    parser.add_argument(
        "profile",
        nargs="?",
        help="Name of the Bitwarden folder to load as an env profile.",
    )
    parser.add_argument(
        "--shell",
        dest="shell_override",
        default=None,
        help="Shell to launch instead of $SHELL.",
    )
    parser.add_argument(
        "--list-profiles",
        action="store_true",
        help="List available Bitwarden folders (profiles) and exit.",
    )
    return parser


def _split_command(argv: list[str]) -> tuple[list[str], list[str]]:
    """Split argv on the first literal "--" into (bwenv args, command)."""
    if "--" in argv:
        idx = argv.index("--")
        return argv[:idx], argv[idx + 1 :]
    return argv, []


def main(argv: list[str] | None = None) -> int:
    raw_args = sys.argv[1:] if argv is None else argv
    parser_args, command = _split_command(raw_args)

    parser = _build_parser()
    args = parser.parse_args(parser_args)

    if not args.profile and not args.list_profiles:
        parser.error("a profile name is required (or pass --list-profiles)")

    try:
        bw_client.check_bw_installed()
        session = bw_client.resolve_session()

        if args.list_profiles:
            for name in env_loader.list_profile_names(session):
                print(name)
            return 0

        env_vars = env_loader.load_profile_env(args.profile, session)
        if command:
            shell.exec_command_with_env(command, env_vars)
        else:
            shell.exec_shell_with_env(env_vars, args.shell_override)
        return 0  # unreachable on success: execvpe replaces this process
    except BwenvError as exc:
        print(f"bwenv: {exc}", file=sys.stderr)
        return 1
    except FileNotFoundError as exc:
        print(f"bwenv: command not found: {exc.filename or command[0]}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
