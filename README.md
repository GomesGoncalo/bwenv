# bwenv

Load environment variables from a Bitwarden folder ("profile") and exec your
shell with them set — no plaintext `.env` files, secrets never touch disk.

![Terminal Demo](bwenv.webp)

## How it works

- A **profile** is a Bitwarden **folder** in your personal vault (e.g. `prod`,
  `staging`).
- Two kinds of items inside that folder become env vars:
  - **Secure Note** items: the item's name is the variable name, its note body
    is the value (one variable per item — the simplest option).
  - **Custom fields** on any item: field name -> variable name, field value ->
    variable value (lets several variables live on one item).
- `bwenv <profile>` unlocks the vault if needed, reads the folder's items, and
  replaces the current process with your `$SHELL`, with those variables set.
  Exiting the spawned shell (`exit` / Ctrl-D) returns you to wherever you ran
  `bwenv` from.
- `bwenv <profile> -- <command...>` runs `<command>` with those variables set
  instead of opening a shell, and exits when the command exits.

## Prerequisites

- [Bitwarden CLI](https://bitwarden.com/help/cli/) (`bw`) installed and logged
  in: `bw login`.
- Python 3.11+ and [uv](https://docs.astral.sh/uv/).

## Setting up a profile

1. In the Bitwarden vault (app or web), create a folder named after your
   profile, e.g. `prod`.
2. For each variable, either:
   - Add a **New Note** item named e.g. `DATABASE_URL`, filed under that
     folder, with the value in the note body; or
   - Add a custom field named e.g. `DATABASE_URL` (type "text" or "hidden") to
     any item filed under that folder.
3. Custom fields of type text or hidden are picked up; boolean and linked
   fields are ignored. Variable names (item name for notes, field name for
   custom fields) must be valid shell identifiers
   (`^[A-Za-z_][A-Za-z0-9_]*$`).

## Usage

```bash
uv sync                        # install
uv run bwenv prod              # unlock (if needed) and open a shell with prod's vars set
uv run bwenv prod --shell zsh  # use a specific shell instead of $SHELL
uv run bwenv prod -- npm run dev  # run a command with prod's vars set instead of a shell
uv run bwenv --list-profiles   # list available Bitwarden folders
```

If `BW_SESSION` is already set and unlocked in your environment, bwenv reuses
it. Otherwise it runs `bw unlock` interactively and keeps the resulting
session key only in memory for the duration of the run — it is **not**
exported into the shell it launches.

## Development

```bash
uv sync
uv run pytest
uv run ruff check .
uv run mypy src
```
