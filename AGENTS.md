# Working in this repo

This turns course material into Anki cloze cards. **There is no program to run.** The method is
three markdown files, meant to be read and followed — by an agent in any harness, or by a person
with no agent at all.

## What you need

**Anki, running, with the [AnkiConnect](https://foosoft.net/projects/anki-connect/) add-on**
(code `2055492159`). AnkiConnect is a plain HTTP endpoint on
`localhost:8765`, so anything that can POST JSON can read and write cards:

```bash
curl -s localhost:8765 -d '{"action":"deckNames","version":6}'
```

**The `Custom Cloze` note type.** A stock Anki does not have it, and every insert fails without it.
Create it once:

```bash
curl -s localhost:8765 -d @anki/custom-cloze.json
```

See [`anki/README.md`](anki/README.md) for what it is and why its CSS matters.
`method/3-cards.md` has the payload shape for inserting notes.

**Optional:** [`anki-mcp-server/`](anki-mcp-server/) wraps that endpoint as an MCP server, if your
harness speaks MCP. It is a convenience over `curl`, nothing more — the method never depends on it.

**Optional:** [`tools/`](tools/) converts a handout of virtual-slide links into card images. Plain
Python and a browser snippet, no agent required. See [`tools/README.md`](tools/README.md).

The method reads what is already text. Anything else has to be converted first —
[`SETUP.md`](SETUP.md) has the commands.

## The method

Read these in order. Each one ends by handing off to the next.

| | | produces |
|---|---|---|
| 1 | [`method/1-extract.md`](method/1-extract.md) | `inventory.md` — every fact, with a verbatim quote and its source |
| 2 | [`method/2-organize.md`](method/2-organize.md) | `plan.md` — one line per card as `ENTITY \| ASPECT \| VALUE \| source`, plus every cut and why |
| 3 | [`method/3-cards.md`](method/3-cards.md) | `deck.json`, then the notes in Anki |

**Do not skip to step 3.** Going straight from a source to a card makes the card inherit the source
sentence's shape; the split exists to stop that, and the reasoning is in the README.

Each step writes its artifact into the lecture folder, so a session can resume at any step. Step 3
also runs alone, against live cards, to repair a deck already in Anki.

## Conventions

- Course material is **not** in this repo. `coursework/` is a symlink to a folder outside it, and
  `.gitignore` is a whitelist — assume anything you add outside the allowed paths will not commit,
  and never work around that.
- Card style is defined by the **seven reference cards** at the top of `method/3-cards.md`. Where a
  written rule and those cards disagree, the cards win.
- Deck and tag names in the docs are placeholders (`<Course>::Test N::<Subject>::<Lecture>`).
  Substitute your own; do not commit real ones.

## If you are Claude Code

`.claude/skills/` holds the three method files themselves — frontmatter plus the full method — so
invoking a skill puts its rules in context. `method/1-extract.md` and its two siblings are symlinks
to them: one copy, two paths, nothing to drift. They used to be pointers, and a pointer is a rule an
agent can decline to read.

Two more pieces exist because a rule left to diligence eventually gets skipped by a session that
believes the work is already clean:

- **A hook** (`.claude/settings.json` → `tools/hooks/on_deck_write.sh`) runs `check_deck.py` on
  every write of a `deck.json` and feeds the report back — the structural check is not a step
  anyone remembers, it just happens.
- **`.claude/agents/deck-auditor.md`** is the standing brief for step 3's independent read —
  truth, fluency, coverage, and style against the seven reference cards. It is a file, not a
  prompt improvised per session, because the one session that improvised it left an angle out.

Neither writes a card. The judgment stays in the method; these only make its checks non-optional.
