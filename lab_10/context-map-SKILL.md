---
name: context-map
description: Draw a simple map of what is in the agent's context window right now and explain which parts survive /compact, /clear, and a new session. Use when the user asks to map, show, draw, or explain the context window, context, or memory.
---

# Context map

Explain the context window to a student who is new to coding agents. Read only: do not create, change, or delete any file, and do not install anything.

## Steps

1. Find what is loaded at the start of a session, without changing anything:
   - The memory files: `CLAUDE.md` in the current folder and its parent folders, and `~/.claude/CLAUDE.md`. For each one that exists, give its path and count its lines.
   - The skills: list the folders in `.claude/skills/` and `~/.claude/skills/`.
   - The MCP servers: run `claude mcp list`.
   - The conversation so far: say roughly how many messages it has and which files you have read in it.

2. Draw the context window as one text diagram, inside a code block, with one box per category in this order: system prompt and tools, MCP tools, memory (`CLAUDE.md`), skills, messages, free space. Make each box roughly as wide as its share. If the user pasted the output of `/context`, use those numbers; if not, label the widths as estimates and suggest running `/context` for the real numbers.

3. Under the diagram, add a short table with one row per category and three columns: what happens after `/compact`, after `/clear`, and in a new session. For example, messages are summarized after `/compact` and gone after `/clear`, while `CLAUDE.md` is read again every time.

4. End with two plain sentences: one on when to use `/compact` and one on when to use `/clear`. Add one sentence on what belongs in `CLAUDE.md` rather than in a prompt.

Keep the whole answer short enough to read in one screen. Use plain words and no jargon beyond the category names above.
