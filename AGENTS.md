# Working in this repository

This repository publishes Cleeng agent skills. Read CONTRIBUTING.md before adding or changing a skill.

## Layout

- `skills/<name>/SKILL.md`: one folder per skill. `<name>` starts with `cleeng-` and equals the frontmatter `name`.
- `skills/<name>/references/`, `scripts/`, `assets/`: loaded or run on demand; link them from SKILL.md with paths relative to the skill folder.
- `.claude-plugin/marketplace.json`: Claude Code marketplace. List every skill folder in `plugins[0].skills`.
- `scripts/validate_skills.py`: repo rules. `tests/`: unit tests for skill scripts, with fixtures.

## Checks

Run before every commit:

```bash
python3 scripts/validate_skills.py
python3 -m unittest discover -s tests
claude plugin validate .
```

CI also runs `npx skills-ref@0.1.5 validate skills/<name>`.

## Rules

- This repository is public. Never add customer or publisher names, revenue or cost figures, internal hostnames, internal ticket keys, Confluence links or anything else from inside Cleeng.
- Skill scripts use the Python standard library only, take no interactive input, print JSON on stdout and errors on stderr.
- Call scripts as `python3 scripts/x.py`, never `./scripts/x.py`; executable bits are lost when skills are served over MCP.
- Keep SKILL.md under 500 lines. Move detail into `references/` and say in SKILL.md when to read each file.
- Do not add a top-level `version` to SKILL.md frontmatter. The plugin version lives in `.claude-plugin/marketplace.json`; release notes live in GitHub releases.
