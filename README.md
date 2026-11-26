# Cleeng agent skills

Agent skills for publishers and integrators using [Cleeng](https://cleeng.com). Each skill is a folder with a `SKILL.md` that follows the [Agent Skills](https://agentskills.io) format, so it works in Claude, Claude Code, Codex, Cursor, Gemini CLI and other agents that load skills.

## Skills

| Skill | What it does |
|---|---|
| [`cleeng-migration-assistant`](skills/cleeng-migration-assistant/SKILL.md) | Turns a Recurly or Vimeo OTT subscriber export into the Cleeng user-import CSV, validates every row, and walks the publisher through the dashboard import. |

## Install

### Any agent, with the `skills` CLI

```bash
npx skills add cleeng/skills
```

Install one skill, or install for one agent only:

```bash
npx skills add cleeng/skills --skill cleeng-migration-assistant
npx skills add cleeng/skills --skill cleeng-migration-assistant -a claude-code
```

Update later with `npx skills update`.

### Claude Code plugin

```
/plugin marketplace add cleeng/skills
/plugin install cleeng@cleeng
```

### Claude.ai

1. Download `cleeng-migration-assistant.zip` from the [latest release](https://github.com/Cleeng/skills/releases/latest).
2. In Claude.ai, open **Customize → Skills**, click **+**, choose **Upload a skill** and select the ZIP.
3. Start a new chat and say, for example, *"I need to migrate my subscribers from Recurly to Cleeng."*

The migration assistant needs code execution, which Claude.ai turns on by default for skills.

### Manual copy

Copy `skills/<name>/` into your agent's skills folder, for example `~/.claude/skills/` or `.agents/skills/` in a project.

Install each skill through one channel only. An agent that loads the same skill from two places treats them as two skills.

## Data handling

The migration assistant processes the subscriber export you upload, which contains names, emails and possibly IP addresses and password hashes. The file is handled by the agent and model provider you use. Check that your data-processing terms allow this before uploading production data.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Report security issues as described in [SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE)
