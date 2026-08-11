# Anki cards from course material

```
                  ##
                 ####
                ######
               ########                  \  |  /
      ##########################o===========*
        ######################           /  |  \
          ##################
            ##############
            ##############
            ##############
           ######    ######
           ##            ##
```

Files go in, cards come out.

You put a lecture's material in a folder, say which files to card and which deck they belong in,
and get reviewed Anki cloze cards in that deck.

> This repo is the **method only**. Course material and the decks built from it are gitignored
> and stay local.

## Three steps, in order

There is no program to run. The work is three markdown files, and the order is the point.

| | | produces |
|---|---|---|
| 1 | [`method/1-extract.md`](method/1-extract.md) | `inventory.md` — every fact, with a verbatim quote and its source. No markup. |
| 2 | [`method/2-organize.md`](method/2-organize.md) | `plan.md` — one line per card as `ENTITY \| ASPECT \| VALUE \| source`, plus every cut and its reason. |
| 3 | [`method/3-cards.md`](method/3-cards.md) | `deck.json` — the notes as they will be inserted, then the notes in Anki. |

**Nothing here is tied to one assistant.** The method is prose: an agent in any harness can read it,
and so can you. It needs Anki with the AnkiConnect add-on — an HTTP endpoint anything can POST to —
and the `Custom Cloze` note type, which [`SETUP.md`](SETUP.md) creates in one command. [`AGENTS.md`](AGENTS.md) is the entry point;
[`.claude/skills/`](.claude/skills/) is a thin adapter that makes the same three files trigger
automatically in Claude Code, and holds no rules of its own.

Each step writes its artifact into the lecture folder and hands off to the next, so a session can
resume at any step. Step 3 also runs alone, against the live cards, to repair a deck already in
Anki — no plan involved.

**There is no styling step.** What a card looks like — bold subject, underlined facet, italic
answer, which spans are blanked — is the seven reference cards at the top of step 3, and they are the
whole style guide. Looking for a fourth skill is looking for something that was deliberately not
built: style is a property of the card being written, not a pass over it afterwards.

Everything the user must be told travels in one place: a `## Carried to handover` section that step
1 opens, step 2 copies forward and appends to, and step 3 reports in full. No step keeps its own
list of what it is owed, so an item reaches you if and only if it is written there.

**The three are one chain.** A change to what any step hands over is a change to the step that
receives it — read all three before shipping an edit to one. Twice now, a fix to a seam has opened
a new one because only the file being edited was in view.

**Why it is split.** Going straight from a source to a card makes the card inherit the *source
sentence's* shape — the slide's leading clause becomes a preamble, its bullet becomes a fused
answer, its terminal noun becomes the blank. The worst version is invisible from inside a card:
working under a heading called "smooth muscle" puts that phrase in the subject slot over and over.
One deck ran 24 of 31 cards as "Smooth muscle …" with the identical hint `which muscle?` — one card
asked 24 ways. Deciding what each card is *about* has to happen before any sentence exists, because
once a sentence is in front of you, you edit the sentence.

## How to use it

**Turn the material into text and images first.** The method reads what is in the folder; it does
not run converters. Whatever the material is, convert it first — [`SETUP.md`](SETUP.md) has the
commands, and [`tools/`](tools/) handles a handout that is only links.

Course material lives outside this repo; link it in once:

```bash
ln -s "/path/to/course material" coursework
```

Then put a lecture's material in a folder under it and say what to card and where it goes:

> Make cards for this week's histology lecture. The folder is
> `coursework/Exam 2/Histology/Week 5/Bone` — card the PowerPoint, notes, a table, and the
> textbook summary. Deck is `<Course>::Test 2::Histology::Bone`.

**You ask once.** That is enough to start, and there are not three commands to run: step 1 reads the
file list back before opening anything, then each step invokes the next when its artifact is
written. The deck name rides along to step 3.

Then: every source is read end to end and re-read against the inventory until nothing is missing;
the objectives are checked off one by one; each fact is judged for whether it earns a card and what
it is *about*; every card is written against the seven reference examples; and you see the whole deck
in a file, with every planned card accounted for, before a single note reaches Anki.

Scope is stated, never inferred. Naming the files is how you say what must be carded.

## Why there is no code

There was: 2,924 lines of Python and 80,412 characters of rulebook, orchestrating sub-agents to
produce cards that look like 1,737 characters of examples — machinery fifty times the size of the
thing it was reproducing.

One day of debugging turned up nine bugs, every one in the plumbing and none in the model's ability
to write a flashcard: a provenance check that parked honest cards before the reviewer could see
them, a scope flag that silently defaulted to "everything", a step documented after the step that
needed it, a retry limit at more than double the documented policy, a sub-process that died with an
empty error whenever it ran detached, and — the one that explains the rest — **the six example
cards sitting at 97% of the way into a 57,000-character prompt**, under an opening line telling the
agent to compare each card against the reference cards *below*.

An independent pass over the rulebook kept 34 instructions out of roughly 140. The rest was
history, post-mortems, rules about not writing rules, and descriptions of scripts that no longer
exist.

The deepest gap wasn't in the 140 either. Every one of them was a *prohibition* — not one described
what a normal card looks like. Nothing said a card has a bold subject and an italic answer. That is
why an agent could break no rule and still be wrong, and it is why step 3 now opens with what a
card *is*, and with seven worked examples, before it lists a single constraint.

Counting cards is not how you check them. A measured ratio — how many carry two clozes, how many
use a facet — describes whatever deck you measured, and a deck built by a broken process measures
its own defects. The finding is always in the cards.

**[`tools/`](tools/) is not a walking back of any of this.** None of it decides anything: it turns a
lab handout of virtual-slide links into image files on disk, which is the same job `soffice`
already does for a `.pptx`. The line that matters is not *no code*, it
is that **no code chooses what a card says** — the moment a script starts ranking facts or writing
sentences, it is the 2,924 lines again. What was actually rebuilt here was a converter, because a
link to a slide viewer is not yet material a skill can read.

## What's still here

| | |
|---|---|
| [`method/`](method/) | the three steps — the whole method |
| [`AGENTS.md`](AGENTS.md) | entry point for any agent or person |
| [`.claude/skills/`](.claude/skills/) | Claude Code adapter — frontmatter and a pointer, no rules |
| `coursework/<Exam>/<Subject>/<Week>/<Lecture>/` | a symlink to course material, outside this repo — plus `inventory.md`, `plan.md`, `deck.json` |
| [`SETUP.md`](SETUP.md) | Anki, AnkiConnect, and the converters that turn source material into text |
| [`tools/`](tools/) | turns a virtual-slide handout into card images — a converter, like `soffice`; [`tools/README.md`](tools/README.md) |
| `recaps/` | session history — local only, never committed |
