# Agent Instructions — PyLoxone

## Project Documentation

This project maintains living documentation in `docs/`. Always read the relevant docs before making changes, and **keep them up to date** when your work affects what they describe.

| Document                                        | Covers                                                          |
| ----------------------------------------------- | --------------------------------------------------------------- |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md)         | Component structure, data flow, module responsibilities         |
| [API_LAYER.md](docs/API_LAYER.md)               | `pyloxone_api/` internals — connection, crypto, message parsing |
| [HA_INTEGRATION.md](docs/HA_INTEGRATION.md)     | Home Assistant platform entities, config flow, coordinator      |
| [LIGHTS_SUBSYSTEM.md](docs/LIGHTS_SUBSYSTEM.md) | Light entity hierarchy, color pickers, mood handling            |
| [ISSUES_AND_TODOS.md](docs/ISSUES_AND_TODOS.md) | Known bugs, improvements, quick wins, testing strategy          |
| [WORKLOG.md](docs/WORKLOG.md)                   | Session-by-session record of decisions, changes, investigations |

## Loxone API Reference

- [API overview](https://www.loxone.com/enen/kb/api/) — links to the WebSocket protocol PDF, structure file spec, user management docs
- [Web Services](https://www.loxone.com/enen/kb/web-services/) — HTTP command reference for controlling VIs, querying status, system commands
- [Communicating with the Miniserver (PDF)](https://www.loxone.com/wp-content/uploads/datasheets/CommunicatingWithMiniserver.pdf) — WebSocket protocol details (encryption, binary message parsing, token auth)
- [Structure File (PDF)](https://www.loxone.com/wp-content/uploads/datasheets/StructureFile.pdf) — LoxAPP3.json format spec

## Deployment

Home Assistant runs on a remote machine. After making code changes, **ask the user if they'd like to deploy and test** before moving on to the next task.

The deploy script requires a `.deploy.env` file in the repo root (gitignored). If it doesn't exist, tell the user to create one with `HA_URL`, `HA_SSH`, `HA_CONFIG`, and `HA_TOKEN`. Example:

```
HA_URL="http://your-ha-host:8123"
HA_SSH="your-ha-host"
HA_CONFIG="/config"
HA_TOKEN="your-long-lived-access-token"
```

Create `HA_TOKEN` in HA: Profile → Security → Long-Lived Access Tokens.

To deploy, run `scripts/deploy` from the repo root (or from anywhere — it auto-resolves the repo root):

- **`scripts/deploy`** — Syncs files and restarts Home Assistant Core (~30-60s). **This is the default** because Python source changes require a full restart to take effect.
- **`scripts/deploy --reload`** — Syncs files and reloads the integration via the HA REST API (~2s). Requires `HA_TOKEN`. **Only use this when you haven't changed any `.py` files** (e.g. YAML-only tweaks, `services.yaml`, `strings.json`). A reload does NOT re-import Python modules.

## Testing

Tests use `pytest-homeassistant-custom-component` and live in `tests/components/loxone/`. Run them from the repo root:

```bash
source .venv/bin/activate   # if not already active
python -m pytest tests/ -v
```

To install the test venv from scratch:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements_test.txt
```

## Rules

1. **Read before writing.** Before changing a file, check the docs above for context on that area of the codebase.
2. **Update docs with code.** If a code change requires a doc update, include both in the same commit.
3. **Run tests after changes.** After modifying code in `custom_components/` or `tests/`, run `python -m pytest tests/ -v` and fix any failures before considering the task done. When adding new functionality, add or update tests to cover it.
4. **Update the worklog.** At the end of each session (or when asked to commit), add an entry to `docs/WORKLOG.md` with the date, a title, and sections for decisions, changes, and investigations. Newest entries go at the top.

## Commit Messages

Use this format for all commit messages:

```
<Descriptive PR title>
<description of the change — the why & how>

## What's changed
<bullet list of changes — the what>

## Testplan
<bullet list of how we've tested the change>
```

The testplan can reference unit tests, but should often also include a manual test step (e.g. "Deploy and verify in HA UI").

## ISSUES_AND_TODOS.md — Living Document

This is the project's source of truth for what's broken, what needs improvement, and what's been done. Treat it as a living document:

- **Add issues as you find them.** When you encounter a bug, smell, or improvement opportunity while working on something else, add it to the appropriate section (Critical Bugs, High/Medium/Low Priority, Quick Wins). Use the next available ID in that section's sequence.
- **Mark items done when you fix them.** Use strikethrough + checkmark + commit hash. For quick wins table rows, strikethrough the entire row and append ✅.
- **Move completed items to the bottom.** Each major section should end with a "Completed" subsection. Move finished items there so the active items stay prominent and the document stays readable. Example:

  ```markdown
  ## Critical Bugs

  ### BUG-005: ... ← active items at the top

  ### BUG-006: ...

  ### Completed

  - ~~BUG-001: description~~ ✅ (`abc1234`)
  - ~~BUG-003: description~~ ✅ (`def5678`)
  ```

- **Keep the Quick Wins table clean.** Completed quick wins accumulate at the bottom of the table, strikethrough. If more than half the table is done, move completed rows to a separate "Completed Quick Wins" table below it.
- **Don't remove items.** Even completed work stays in the doc (struck through) so there's a record of what was done and when.
