"""Exceptions raised by bwenv."""

from __future__ import annotations


class BwenvError(Exception):
    """Base class for all bwenv errors."""


class BwNotInstalledError(BwenvError):
    """The `bw` CLI is not on PATH."""

    def __init__(self) -> None:
        super().__init__(
            "The Bitwarden CLI (`bw`) was not found on PATH.\n"
            "Install it from https://bitwarden.com/help/cli/ "
            "(e.g. `brew install bitwarden-cli`, `npm install -g @bitwarden/cli`, "
            "or `snap install bw`)."
        )


class NotLoggedInError(BwenvError):
    """The vault has no active login session at all."""

    def __init__(self) -> None:
        super().__init__("Not logged in to Bitwarden. Run `bw login` first.")


class UnlockFailedError(BwenvError):
    """`bw unlock` did not produce a usable session key."""

    def __init__(self, detail: str) -> None:
        super().__init__(f"Failed to unlock the Bitwarden vault: {detail}")


class ProfileNotFoundError(BwenvError):
    """No folder matches the requested profile name."""

    def __init__(self, profile: str, available: list[str]) -> None:
        choices = ", ".join(sorted(available)) or "(no folders found)"
        super().__init__(
            f"No Bitwarden folder named {profile!r} was found. Available folders: {choices}"
        )


class ShellNotFoundError(BwenvError):
    """Neither $SHELL nor the fallback shell could be resolved on PATH."""

    def __init__(self, shell: str) -> None:
        super().__init__(f"Could not find shell executable {shell!r} on PATH.")
