# Step 1 — Extract

_Read the course material and produce a fact inventory with verbatim sources. No cards yet._

# What this produces

A **fact inventory**: plain statements, each with a verbatim quote and its source.
**No card markup, no clozes, no decisions about what is worth learning.** Those are steps 2 and 3.

Going straight from a source to a card is what breaks decks. The card inherits the *source
sentence's* shape instead of the *fact's* — the slide's leading clause becomes a preamble, its
bullet becomes a fused answer, its terminal noun becomes the blank. Extraction exists to break that
link. By the time cards are written the source sentence should be gone, and only the fact and its
quote remain.

# Scope

1. **The user states the folder, which files, and the deck.** Never infer any of them from what
   happens to be in the directory. Never open Anki to decide what to card. The deck is needed two
   steps later, by the step that tags the notes, and nobody asks again — carry it into
   `inventory.md` now. *It was once needed at step 3 and requested at step 1 by nobody.* `test::N`
   you can derive, since it is in the deck name.
2. **Read the file list back before reading anything.** A lecture folder can hold files from two
   different sessions, alike in name and different in content.
   *A full deck was once drafted from the wrong one before anyone noticed.*
3. **Read every named source end to end.** Not the first pages, not a search — end to end.

# The inventory

One entry per fact:

| field | |
|---|---|
| `fact` | one plain sentence, no markup, no cloze |
| `entity` | the specific thing the fact is about, if obvious — leave blank if not; step 2 settles it |
| `source` | `Slide N` / `Notes` / textbook |
| `quote` | verbatim, see Fidelity |
| `image` | slide file, where there is one |
| `signal` | why it earns attention: objective / on a slide / stressed aloud / textbook only |

Facts, not sentences. If a bullet lists two independent properties, that is two entries. If a list
is itself the thing to be recalled — the three classes, the five zones — that is one.

# Emphasis

Weight by what the lecturer **stressed**, not by word count: phrases marking something as required
knowledge, a term spelled out aloud, a point made twice, the class quizzed on it, minutes spent on
one slide. Record the signal; do not act on it — step 2 decides what survives.

Record explicit **exclusions** with equal care: a topic named as off the exam, a section skipped for
the day, a value that will be supplied rather than recalled. These are instructions, and step 2 must
see them.

# Fidelity

- **Quote verbatim.** Never tidy. A paraphrase is not a quote — "in your 20s" written as "in your
  twenties" is altered, and so is a comma standing in for a full stop.
- **Never splice two separate cues into one sentence.** Eliding with `…` is fine as long as each
  fragment is word-for-word and in order.
- Machine-generated notes mangle technical terms. Quote the garble with the correction in
  `[brackets]`. Where the correction would be a guess, cite the slide instead.
- **Notes a converter produced are unreliable, so a claim that appears in them and nowhere else
  has one weak source, not one source.** Treat an odd-sounding term that only they carry as a
  probable conversion error and go looking for it in the slides, objectives or textbook. If it
  is not there, the written source's wording goes on the card and the notes' term goes in the note
  — do not put an uncorroborated term on the card face. Audible hedging and filler around the term
  is a further signal. *"Endomysium is areolar connective tissue" rested
  on one hedged sentence; the word appears in no slide, objective or textbook, and the course
  textbook says something else entirely.*
- **Record every override under `## Carried to handover`** (below) — the notes' term, the term
  used instead, and why. Overriding what the notes attribute to the instructor is a judgment about a
  source, not a conversion fix, so it is reported to the user rather than left in a note field
  to be discovered. Step 3 does the reporting; this step's job is to write it down, because a
  judgment nobody records is a judgment nobody sees. It is not a question to put back to the user,
  and it is not raised twice.
- For a fact that comes from the **notes**, quote the notes and label them as such, even when a
  slide is also on screen. Never cite a slide that does not state the fact.
- Slide text inside a rasterised figure will not extract as text. Read it visually and record it —
  and note that automated checks against the text layer will not find it.
- **A fact with no resolvable source does not enter the inventory.**

# Coverage — the step that matters most

Read each source back against the inventory and ask what was taught that has no entry. Repeat until
a source comes back with nothing.

Then take the **objectives** and list them one by one, marking which are covered. Include the ones
that nothing in the material answers — step 2 needs to see the holes, because an objective-backed
gap is a reason to go looking in another source, and a gap that no source fills is something the
user must be told about rather than something to invent around.

*Skipping the coverage pass once produced a deck that carded the textbook thoroughly and skimmed
the lecture, missing two-thirds of what the lecturer emphasised.*

# Handing off

Write the inventory to **`<folder>/inventory.md`** — the lecture's own folder, beside the material
it came from. Open it with the deck name and the file list you read back.

End it with a **`## Carried to handover`** section. This is the pipeline's one channel for things
the user must be told, and it travels intact: step 2 copies it forward and appends to it, step 3
reports whatever it holds. Nothing downstream keeps its own list of what it is owed, so an item
reaches the user if and only if it is written here. Put in it:

- **every notes-only term you overrode** with a written source — the term, the term used, why
- **every objective no source answers**

Then go on to **[step 2 — organize](2-organize.md)**. Do not carry on into planning or writing with the extraction rules
in context and the organizing rules absent: choosing the entity is step 2's whole job, and it is the
one decision this pipeline exists to protect.
