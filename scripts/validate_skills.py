#!/usr/bin/env python3
"""Repo checks the Agent Skills validator does not cover. Standard library only.

- frontmatter keys are spec fields only; name matches the folder and the `cleeng-` prefix
- description <= 1024 chars, compatibility <= 500 chars, SKILL.md <= 500 lines
- every references/, scripts/ or assets/ path named in SKILL.md exists
- .claude-plugin/marketplace.json lists every skill folder and nothing else
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ALLOWED_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
NAME_RE = re.compile(r"^cleeng(-[a-z0-9]+)+$")
PATH_RE = re.compile(r"`((?:references|scripts|assets)/[^`\s]+)`")


def check_skill(skill_dir: Path) -> list[str]:
    problems = []
    skill_md = skill_dir / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        return [f"{skill_md}: missing YAML frontmatter"]
    frontmatter = match.group(1)
    keys = re.findall(r"^([A-Za-z][\w-]*):", frontmatter, re.M)
    fields = dict(re.findall(r"^([A-Za-z][\w-]*):[ \t]*(.*)$", frontmatter, re.M))
    for key in set(keys) - ALLOWED_KEYS:
        problems.append(f"{skill_md}: frontmatter key '{key}' is not in the Agent Skills spec (use metadata)")
    name = fields.get("name", "").strip()
    if name != skill_dir.name:
        problems.append(f"{skill_md}: name '{name}' does not match folder '{skill_dir.name}'")
    if not NAME_RE.match(name) or len(name) > 64:
        problems.append(f"{skill_md}: name '{name}' must be kebab-case, start with 'cleeng-' and be <= 64 chars")
    description = fields.get("description", "").strip()
    if not description or description in (">", "|", ">-", "|-"):
        problems.append(f"{skill_md}: description must be a non-empty single-line value")
    elif len(description) > 1024:
        problems.append(f"{skill_md}: description is {len(description)} chars, limit 1024")
    if len(fields.get("compatibility", "")) > 500:
        problems.append(f"{skill_md}: compatibility is over 500 chars")
    lines = text.count("\n")
    if lines > 500:
        problems.append(f"{skill_md}: {lines} lines, limit 500")
    for path in sorted(set(PATH_RE.findall(text))):
        if not (skill_dir / path).exists():
            problems.append(f"{skill_md}: references missing file {path}")
    return problems


def main() -> int:
    skill_dirs = sorted(p.parent for p in (ROOT / "skills").glob("*/SKILL.md"))
    problems = [p for d in skill_dirs for p in check_skill(d)]

    marketplace = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
    listed = {Path(s).name for plugin in marketplace["plugins"] for s in plugin.get("skills", [])}
    present = {d.name for d in skill_dirs}
    for missing in sorted(present - listed):
        problems.append(f".claude-plugin/marketplace.json: skill '{missing}' is not listed")
    for extra in sorted(listed - present):
        problems.append(f".claude-plugin/marketplace.json: lists '{extra}', which has no skills/{extra}/SKILL.md")

    for problem in problems:
        print(problem, file=sys.stderr)
    print(f"{len(skill_dirs)} skills checked, {len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
