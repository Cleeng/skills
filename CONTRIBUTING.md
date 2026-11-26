# Contributing

Cleeng staff maintain these skills. External contributions are not accepted yet; open an issue to report a problem or suggest a skill.

## Adding a skill

1. Create `skills/cleeng-<name>/SKILL.md` with `name` and `description` frontmatter. Write the description as what the skill does and when to use it, with the words a user would say.
2. Put long material in `references/`, deterministic steps in `scripts/` (Python standard library only), and static data in `assets/`.
3. Add the folder to `plugins[0].skills` in `.claude-plugin/marketplace.json`.
4. Add tests for any script under `tests/`, with fixtures in `tests/fixtures/`.
5. Run the checks listed in AGENTS.md.
6. Try the skill in at least one agent with a fresh session, using the prompts a publisher would type.

## Releasing

1. Set the new version in `.claude-plugin/marketplace.json`.
2. Tag `vX.Y.Z` on `main` and push the tag. The release workflow creates a GitHub release with generated notes and one ZIP per skill for Claude.ai upload.
3. Edit the release notes on GitHub if the generated list needs context.
