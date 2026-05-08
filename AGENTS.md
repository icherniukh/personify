# AGENTS.md instructions for /Users/ivan/proj/personify

- Always show progress before requesting input.
- Task tracking: use `bd` (beads) by default. Never use TodoWrite or markdown task files.
  - If the project uses GitHub issues as its primary tracker, prefer `gh issue` for project-facing work items: bugs, features, anything that needs a PR reference or team visibility. Use beads for personal/cross-project tracking in that case.
  - Do not mirror the same item in both. Pick one per project and stay consistent.
- Project status: use `bd ready` for unblocked work and `bd list --status=in_progress` for active work. Never infer status from git or file timestamps.

## Beads When GitHub Issues Is Primary

When a project uses GitHub issues as its canonical tracker, beads still has a role:

- Session todos: things to do this session that do not warrant a GitHub issue.
- Cross-project/personal tasks: work that spans repos or personal workflow.
- Scratch capture: quick `bd q "..."` to not lose a thought mid-task; close it the same session.
- `bd remember`: cross-session insights that are not tied to a specific GitHub issue.

What beads is not for in this mode: bugs, features, backlog items. Those go to GitHub issues.

## Context Recovery

When picking up previous work, search in this order:

1. GitHub issues, if project uses them, or `bd list` / `bd show <id>`.
2. Git history.
3. Ask the user only if the above yield nothing.

## Factual Grounding

- When summarizing or analyzing documents, extract supporting quotes before synthesizing. Reason from quotes, not memory.
- Say "I don't have enough information" rather than guess. Never fabricate details to fill gaps.
- When making factual claims about code, configs, or external systems, verify by reading the source instead of relying on recollection.
- Do not supplement document analysis with general knowledge unless explicitly asked.
