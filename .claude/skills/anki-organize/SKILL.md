---
name: anki-organize
description: Step 2 of 3. Turn an extracted fact inventory into a card plan — decide what earns a card, and name the entity, aspect and value for each. Use after anki-extract and before anki-cards.
---

# Step 2 — Organize

_Turn the fact inventory into a card plan: decide what earns a card, and name its entity, aspect and value._

# What this produces

A **card plan**. One line per card:

```
ENTITY       | ASPECT    | VALUE                                     | source
Osteoid      | —         | unmineralized bone matrix                 | Slide 12
Muscle       | types     | skeletal, cardiac and smooth              | Slide 5
Tropomodulin | —         | caps the free end of the actin filament   | Notes
```

**The plan says what each card is *about*; `inventory.md` beside it keeps the verbatim quote and
the slide image.** Step 3 needs both for the `Extra` field, so the two files travel together — the
plan does not copy them, and step 3 opens both.

A card whose question is a picture has no entity and no aspect, so it takes a row of its own:

```
IMAGE                               | ANSWER            | source
<course>-cart-02-perichondrium.jpg  | hyaline cartilage | MH-136 trachea, 50x
```

Decide **ref-06 or ref-07 once for the whole deck**, not per card, and write which at the top of
the plan — step 3 explains the choice. A slide practical is ref-07.

No markup. The entity will become the `<b>` subject, the aspect the `<u>` facet, the value the
`<i>` answer — but that is step 3's problem. Here you decide only **what each card is about** and
**which facts deserve one**.

This step exists because both of those decisions are ruined by having markup in front of you. Once
a sentence exists you start editing the sentence.

**ASPECT is often empty, and an empty one is not a gap to fill.** It names the angle the fact is
taken from — *where found*, *function*, *in cross section* — and plenty of facts have none: the
entity simply is, or does, the value. A row with four columns invites filling all four, and the
thing nearest to hand is the sentence's verb — which then becomes a `<u>` in step 3 and strips the
verb out of the answer. *"Tropomodulin | caps | the free end of the actin filament" should be
"Tropomodulin | — | caps the free end of the actin filament": what the protein does is the whole
recall, not a heading over it.* Leave it blank and let the value carry the verb.

# The entity is what the SENTENCE is about — never the lecture topic

This is the most damaging error in the pipeline and it is invisible from inside a card.

Working under a heading called "smooth muscle" makes that phrase the most available noun in your
head, and it lands in the subject slot on card after card. *One deck ran 24 of 31 cards as
"Smooth muscle …" with the identical hint `which muscle?`. That is not 24 cards; it is one card
asked 24 ways, in a section where "which muscle?" is already answered by context.*

"Smooth muscle has no T-tubules" is **about T tubules**:

```
ENTITY: T tubules   ASPECT: where absent   VALUE: smooth muscle
```

The entity is a real thing rather than a heading, and one source sentence still proves it —
*and one source states it directly.* **Do not upgrade this into a distribution summary**
("T tubules are found in skeletal and cardiac muscle") unless a single source states it: that
sentence is true but appears nowhere, and a card built on it has no verbatim quote to carry.

**A description is not an entity either.** The slide writes "Maternal component: decidua basalis",
and a card that inherits that ordering — "The maternal component of the placenta is {{the decidua
basalis}}" — has the roles reversed: the name lands in the answer slot and a definite description
takes the subject. The entity is the **named thing**; its role, identity or fate is the value:

```
Decidua basalis | — | the maternal component of the placenta | Slide N
```

The tell is a value slot holding a proper name. Reversed, the deck never asks the one question the
term exists to answer — "The decidua basalis is [what?]" — and the subject cloze degrades to an
adjective blank ("The [which component?] component of the placenta…"). *Three placenta-lecture
cards shipped reversed and the owner flipped them by hand; the source ordering is what reversed
them, which is exactly the sentence-shape inheritance this pipeline exists to break.*

**Check before handing the plan on: if a single entity appears in more than a quarter of the lines,
the entities are wrong.** Go back through fact by fact and ask what the sentence is about.

The wrong entity is also the source of nearly every deformed card, because filler is needed to bolt
a fact onto a subject that is not its subject:

| written | real entity | what the wrong entity forced |
|---|---|---|
| "A **muscle fiber**'s plasma membrane is called the sarcolemma" | sarcolemma | a possessive |
| "In cross section, **skeletal muscle** fibers appear polygonal" | the cross-section appearance | a preamble |
| "Of the three fiber types, **Type IIb** has the fewest…" | mitochondria content | a premise |
| "**Smooth muscle** differs from striated muscle in having no tubule system" | T tubules | an invented — and untrue — comparison |

# What earns a card

- The bar is not "is it true" but **"did the teacher signal this as need-to-know."**
- **A slide bullet is not a fact.** A ten-bullet slide is one or two cards, not ten. Ask what an
  exam question on that slide looks like and plan *that* — usually a few parallel cards on the axes
  that discriminate. *Three fiber-type slides once produced 25 cards this way; the exam-shaped
  version is about 15.*
- **Discrimination is an inclusion gate and it runs first.** If a fact is true of its subject and of
  everything else in the course, there is no card. *"Cells cut through cytoplasm show no nucleus"
  is a sectioning artifact true of every tissue.* Keep a fact whose **forward** direction
  discriminates even when the reverse does not — "each smooth muscle cell has one nucleus" is
  specific against skeletal's multinucleate fibers.
- Cut vague values — "generate high peak muscle tension", "provides support and protection". If the
  value is not a term, a number, or a definite phrase, there is nothing to produce.
- Cut anecdotes, slide furniture, and restatements of a card you already planned.
- **Zero cards for a slide is fine. Zero for a taught topic is a failure.**
- If the instructor said not to memorise it, or that a value will be given, it does not get a card.
- **Nothing is dropped silently.** A cut fact stays in the plan under a `## Cut` heading with
  its reason, so step 3 can tell a planned card from a rejected one.
- **A cut reason must be a checkable claim, not a label.** If the reason is "covered elsewhere",
  name the card that covers it; if it is "slide furniture", the slide element must genuinely be
  structure — a header or an agenda — and not content that happens to be laid out as an outline.
  *"Calcium is found in the SR and the cytosol" was cut as furniture whose mechanism cards carried
  it. The slide was an outline but the line was a fact, and no card in the plan contained the word
  cytosol at all — the storage half was covered three times and the destination not once.*

# Two facts or one

Two independent properties are two cards, however the slide punctuated them — "many mitochondria
and abundant myoglobin" is a bullet, not a fact. **The punctuation is not evidence about the fact
count.** A multi-item value is one card only when the *set* is what is recalled: the three classes,
the five zones.

Two cards teaching one fact are one card. A shared sentence frame is not a shared fact — parallel
cards on contrasting terms are correct and wanted.

# Using what you know

Your knowledge of the field **selects, structures, audits and finds gaps**; the sources supply the
words. It tells you which five of fifty true statements matter, that a fiber-type slide is one
comparison matrix rather than ten bullets, that "H zone" and "H band" are the same thing — and,
most valuably, what an objective demands that the lecture never said, so you know where to look.
*A lecture skipped smooth-muscle innervation entirely; knowing the topic exists is what sent the
search to the textbook, which had it verbatim.*

What it must never do is put a fact in the plan that no source states. If nothing in the sources
covers an objective, that is a gap to report to the user, not one to fill from memory.

**Where the course material and biology disagree, biology wins the card face** — a wrong fact
rehearsed daily is a wrong fact learned, whatever the exam says. The course's contrary wording
goes on the back as a flag that names the course as the contradictor — "the slide says 'skull is
tall and short'" — never a flag that frames reality as the dissenter. The student then produces
what is true and still recognizes the exam's version on sight. **Neither side is ever silently
dropped**: a face that quietly corrects the slide, or a face that quietly repeats its error, are
the same failure — the disagreement is surfaced, on the card and at handover.

# Precedence and scope

**objectives** (the coverage contract) ▸ **slides** (the anchor) ▸ **notes** (emphasis) ▸
**textbook** (precision). Where sources conflict on fact, plan what the slides and textbook agree
on and raise the conflict. Never ship both sides.

Scope by **session**, not topic: everything taught in it, including material carrying
over from last week. Slides the lecture never reached belong to the next deck.

# Handing off

Write the plan to **`<folder>/plan.md`** — the deck name carried over from `inventory.md`, then the
planned cards as `ENTITY | ASPECT | VALUE | source` — or `IMAGE | ANSWER | source` for a
recognition deck, with the ref-06/ref-07 decision at the top — and the cuts under `## Cut`.

Then **copy `inventory.md`'s `## Carried to handover` section forward, verbatim, and append to
it** — do not summarise it, and do not drop an item because it looks handled. Add:

- **every source conflict you raised** — what the sources disagree on, and which one the plan follows
- **every cut**, with its reason

That section is the only channel to the user, and it is now yours to pass on intact. Step 3 reports
whatever is in it, and keeps no list of its own — so anything you leave out reaches nobody.

Then go on to **[step 3 — cards](3-cards.md)**.
