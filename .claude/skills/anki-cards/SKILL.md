---
name: anki-cards
description: Step 3 of 3. Write Anki cloze cards from a card plan and insert them into your Anki study decks. Use after anki-organize, or on its own when repairing cards already in Anki.
---

# Step 3 — Cards

_Write the cards from the plan and insert them into Anki. Also runs alone, against live cards, to repair a deck._

# What a card is

A card makes the student **produce a key term from memory, inside a complete, true sentence.**
That term is the blank. Everything below serves that.

Check the sentence against that line before checking it against anything else. A card can parse,
carry every tag correctly, satisfy every rule below, and still fail it — that is the *common*
failure, not a rare one. Ask: is this sentence true standing alone, and is the blank a term worth
producing?

# The seven cards that define the style

These are the whole style guide. Where a written rule below and these cards disagree, **the cards
win.** Put your draft beside the one with the same shape — pulled up, not from memory.

They are canonical, so keep them correct: if one of them is wrong, fix it here rather than working
around it. *ref-05 once read "'plate' visible and not bolded", which is the opposite of the rule
below, and 24 cards were written to match it before anyone compared the two.* And whenever you
build a check of any kind, **run these seven through it first** — they are the regression test. A
check that fails ref-06 or ref-07 has not understood recognition cards; a check that passes a card
these seven would reject is not checking the right thing.

```
ref-01  {{c1::<b>Osteoid</b>::what?}} is {{c2::<i>unmineralized bone matrix</i>::what is it?}}

ref-02  {{c1::<b>Osteoclasts</b>::which cells?}} <u>function</u> to {{c2::<i>resorb bone matrix</i>::do what?}}

ref-03  {{c1::<b>Calcitonin</b>::which hormone?}} acts on bone to {{c2::<u>lower</u>::raise or lower?}} {{c3::<i>blood calcium levels</i>::which levels?}}

ref-04  {{c1::<b>Connective tissue</b>::which tissue?}} is <u>classified</u> into {{c2::<i>embryonic, proper, and specialized types</i>::which three classes?}}

ref-05  The {{c1::<b>epiphyseal growth</b>::which?}} <b>plate</b> has five <u>zones</u>:<br><br>1. {{c2::<i>resting cartilage</i>::which?}}<br>2. {{c2::<i>proliferating cartilage</i>}}<br>3. {{c2::<i>hypertrophic cartilage</i>}}<br>4. {{c2::<i>calcified cartilage</i>}}<br>5. {{c2::<i>ossification</i>}}

ref-06  {{c1::<img src="slide.jpg">}}<br><br>This is {{c2::<i>compact bone</i>::which tissue?}}

ref-07  <img src="slide.jpg"><br><br>This is {{c1::<i>compact bone</i>::which tissue?}}
```

**ref-01** subject + answer, the workhorse. **ref-02** a *visible* facet. **ref-03** an either/or
choice wears `<u>`, the value wears `<i>`. **ref-04** an inline set is **one** answer — the three
classes are recalled together, so they share a cloze instead of becoming three cards.
**ref-05** a list — numbers **outside** the braces and unstyled, one item per line, every item on
**one** cloze number, and hint on item 1 only. The whole subject — "epiphyseal growth plate" —
is bolded &mdash; in two `<b>` runs, because a cloze boundary cuts through it; only "epiphyseal
growth" is clozed, so "plate" stays visible to make the hint read. **ref-06** a
recognition card — the picture is a cloze with **no hint** and there is **no `<b>` at all**.
**ref-07** the same card with the picture **not** clozed, so it makes one card instead of two.

**ref-06 or ref-07 is a real choice, and it turns on whether the reverse card is worth answering.**
For a whole deck the plan has already made it — read it off the top of `plan.md` rather than
deciding again here, or half the deck ends up in the other shape.
Clozing the picture asks it both ways: name the tissue from the image, *and* produce the image from
the description. The second direction is worth having when the image is the one thing the deck is
teaching — a diagram, a named appearance, a single canonical picture. It is waste when the deck is a
**slide practical**, where dozens of different fields all answer "hyaline cartilage": nobody can
produce a particular field of view from "This is hyaline cartilage", and each note
would double its cards for a question the exam never asks. **A whole deck of one-image-one-answer
identification takes ref-07.** *A first pass at a 6-week histology practical built 37 cards on
ref-06 and had to be rewritten to 21 on ref-07.*

Where the identified thing is not a tissue, the hint follows it — `which cell?` on a blood smear —
but it stays **the same on every card in that deck**, or the odd hint tells you the answer is the
odd one out.

**And read what they have in common:** every subject is a **specific named entity** — Osteoid,
Osteoclasts, Calcitonin, the epiphyseal growth plate — and each card states **one property of it**.
Not one has a topic heading in the subject slot. Reading these seven for their markup and not for
that is how a deck ends up with the same subject on three-quarters of its cards.

# From plan to card

`ENTITY → <b>` · `ASPECT → <u>` · `VALUE → <i>`

- `<i>` on every card; `<b>` on every card but an image card. **One subject, never two** —
  which is not the same as one `<b>` tag; see the nesting rule below.
- Left to right the roles run **`<b>` → `<u>` → `<i>`**, and the card **ends on its answer**.
- **The article is a claim about number.** "The" fronts a unique structure — The sternum, The
  decidua, The cranial fold. A numerous class goes bare and plural: "Spiral arteries are…",
  "Vertebral arches fuse…", "Ear ossicles are…". Defaulting every subject to "The" reads singular
  grandeur onto things that occur by the dozen.
- **The subject opens the sentence**, behind at most an article. A clause in front of it means
  either a facet standing in the wrong place — "In cross section, `<b>`skeletal muscle`</b>` fibers
  appear polygonal" wants to be "`<b>`Skeletal muscle`</b>` fibers in `<u>`cross section`</u>`
  appear polygonal" — or filler to cut.
- **The whole subject is bolded; only the key identifier is clozed.** That is the rule about
  *what*. The rule about *how* is separate, and getting it wrong silently breaks the card:

  **A role tag must sit directly on the text it styles — never wrap a cloze.** Anki renders a
  revealed cloze as its own `<span class="cloze">`, and that span sets colour on itself, so a
  colour merely *inherited* from an enclosing `<b>` is overridden and the role is lost on screen.
  A subject that a cloze boundary cuts through therefore takes **two `<b>` runs**, one inside the
  braces and one outside. It is still one subject — and the runs are **adjacent**, separated by
  the cloze braces and whitespace alone. A bolded noun, an unbolded connective, and a second
  free-standing bold phrase is two subjects on the rendered face, whatever the writer meant:
  *eight cards in one deck shipped as "<b>noun</b> that <b>frame</b>", written once for a
  symmetric batch and inherited card to card, and every gate passed them because none counted
  bold runs.* The frame a subject sits in is the facet's job — mark it `<u>` or leave it plain.

  ```
  The {{c1::<b>A</b>::which?}} <b>band</b> is {{c2::<i>dark</i>::dark or light?}}
  {{c1::<b>Type IIb</b>::which?}} <b>muscle fibers</b> have the {{c2::<u>fewest</u>::most or fewest?}} {{c3::<i>mitochondria</i>::which organelle?}}
  The {{c1::<b>sarcomere</b>::which unit?}} is the {{c2::<i>functional unit of contraction</i>::what is it?}}
  ```

  *Written as `<b>{{c1::A::which?}} band</b>` it reads correctly in the source and renders wrong:
  148 of 172 cards shipped with the subject showing in the cloze colour instead of the subject
  colour. Nothing in the markup looks amiss — only the rendered card shows it.*

  "muscle fibers" and "band" are part of the subject's name, so they are **inside the bold**; they
  are not what distinguishes it, so they are **outside the cloze**. Where the subject is a single
  term the bold and the cloze coincide. *Getting these two nested the wrong way round — cloze
  outside, bold inside — is what produced `<b>A band</b>` blanked whole and `{{Type IIb}} muscle
  fibers` with the name broken in half.*
- Nothing unstyled goes inside the braces. An article belonging to the *sentence* stays outside;
  one belonging to the *answer phrase* travels with it. (An `<img>` is the one thing in a cloze
  wearing no role tag — ref-06.)
- **A contrast is not part of the answer.** "X — not Y", "X rather than Y", "X, unlike Z": the
  recall is X, and the not-Y is answer-*checking* material — put it in `Extra` as a flag
  line above the image, written `<i>**</i>flag<i>**</i>` — literal asterisks, italicized so they
  render in the answer colour, the text between them plain. That is the owner's own convention on
  live cards, and the flag also carries a scope or a synonym: `**In Cardiac and Skeletal
  muscle**`, `**also called the vitelline duct**`. A blank that contains its own contrast asks the student to recite a warning
  instead of produce a fact. *One card walked every wrong version of this: "…{{lateral plate
  mesoderm}}, not from sclerotome" trailed the cloze (fails the checker), a repair folded it into
  the blank ("{{…mesoderm — not sclerotome}}") to pass, and the owner had to fix it by hand to
  the right form: blank holds what the sternum IS, `**Not Sclerotome**` flags the back.* The
  exception is a card whose negative IS the fact — "myoblasts that never fuse", "plasma crosses
  while {{red blood cells do not}}" — which is precisely why the checker only counts negations
  and never fails them.
- **No possessives.** With the right entity there is nothing to possess, only to describe, so an
  apostrophe-s (or a "whose") means step 2 handed you the wrong entity — go back rather than patch.
- Assert only what the source states. No added qualifier, no inference, no invented comparison.

# Which spans get clozed

- **The subject is clozed. That is the default, not a call you make fresh on every card.** All five
  of the reference cards that have a subject cloze it, and across a finished deck it should run
  somewhere near nine in ten. A card asks two questions, forward and backward, and **the backward
  one does not exist unless the subject is blank** — a term nobody is ever asked to produce is a
  term the deck does not teach. Leaving it visible is not an easier card; it is half a card.
- **So a visible subject is the exception, and it owes an argument out loud: name two other terms
  that answer the reverse question.** If you cannot name two, the reverse discriminates and the
  subject gets clozed. Nine in ten is a prior, not a quota — it tells you which of the two choices
  has to be defended, and you still defend it card by card. *A 172-card deck left 22 subjects
  visible and about 9 of them were wrong — "what bundles 10 to 100 muscle fibers?" and "which
  muscle is identified by branching, intercalated discs and single nuclei?" each have exactly one
  answer. Those cards were written against ref-04, which for a long time left a discriminating subject
  visible and taught the wrong default to everything measured against it.* Unwritten, the test gets
  felt rather than run, and it is always felt in the same direction.
- **Cloze the whole value**, never a fragment with the explanation left as prose. *"…because the
  thin and thick filaments never form {{sarcomeres}}" is a 1-word answer with 11 words of
  explanation visible. The seven leave scaffolding visible, never explanation.*
- **When the card asks what something DOES, the verb is part of the answer.** `<u>` marks an
  *aspect* — function, location, section plane. Ask which
  question the card is really putting: if it is "what does X do?", the verb is inside the braces;
  if it is "what / where / how much?", the verb is only scaffolding and stays visible.

  ```
  {{c1::<b>Tropomodulin</b>::which protein?}} <u>caps</u> {{c2::<i>the free end of the actin filament</i>::which end?}}
  {{c1::<b>Tropomodulin</b>::which protein?}} {{c2::<i>caps the free end of the actin filament</i>::does what?}}
  ```

  The first asks for a location and never asks what the protein is for. The second is the card.
  "The <b>A band</b> <u>contains</u> …" is fine by the same test — *contains* is not the fact.
- **One recall per blank — the whole value, but ONE value.** A blank fusing independent facts with
  commas and dashes — "{{uterine-artery branches, risen from the basal into the functional layer,
  filling the intervillous space at arterial pressure}}" — is three recalls welded into a blob
  nobody can produce. The owner's form is the **chain**: the sentence carries up to three blanks,
  each wearing its role colour, so the card reads subject → link → payoff —

  ```
  {{c1::<b>Spiral arteries</b>::which arteries?}} are {{c2::<u>uterine-artery branches</u>::what?}} that {{c3::<i>fill the intervillous space at arterial pressure</i>::do what?}}
  ```

  — in a chain the middle link wears `<u>` even though it is not an either/or; the fact that does
  not fit the chain goes to the `Extra` flag (here: `**Rise from the basal into the functional
  layer**`), never into a longer blank. The test for a blob is **independence**: could the pieces
  be asked separately? A rich single fact — a why-clause, an inline set, a bounded range — is one
  recall however wordy, and stays whole.
- **A bounded value is one answer.** "between A and B", "from X to Y", "A to B" — blanking only the
  far end hands over half the fact. **A route or ordered sequence is also one answer, written as an
  arrow chain**: "chorionic plate vessels &rarr; umbilical vessels &rarr; the fetal heart", never
  "X, then Y, then Z" prose — the owner's lineage card ("paraxial mesoderm &rarr; somites &rarr;
  myotome") is the model. *"lie between the sarcolemma and {{the basal lamina}}" was
  written two cards after "{{Z line to Z line}}" was written correctly.*
- **The hint must be the question you meant to ask.** If you are writing a hint to fit a blank you
  already chose, you clozed by word-type instead of by answer — technical nouns *look* like answers
  and the eye lands on them.
- Cloze the facet only when it is a **value to produce**: ref-03 clozes `lower` because *raise or
  lower* is the recall; ref-02 leaves `function` visible because it only names the aspect. An
  either/or is ref-03 **only when a separate value survives it** — otherwise mark the aspect noun
  `<u>` and let the either/or be the `<i>` answer.
- **In a parallel set, the term that differs between the cards is a value to produce — cloze it.**
  That contrast is the whole reason the set exists. *Two cards read "Mitochondria in `<u>`skeletal`</u>`
  muscle make up 2%" and "…`<u>`cardiac`</u>`… 40%", with the muscle type visible on both — so neither
  card ever asked skeletal-or-cardiac, the one thing the pair was built to teach.*
- One to three cloze numbers. Never four.
- **Every miss above leans the same way: less clozed.** Leaving the subject visible, leaving the
  verb outside, blanking the shorter of two spans — each is the cheaper choice while writing and
  the easier card to answer, and none of them breaks a rule a checker can see. When a judgment call
  about a span feels balanced, it is not: you are standing on the slope. Cloze it.

# Hints

- **Hint every cloze, except an image cloze and list items that share a number** (they inherit
  item 1's). Those two carve-outs are the whole exception list.
- Questions ending in `?`, one to three words, no commas, reading as natural English substituted
  into the blank.
- **The hint supplies exactly what the visible sentence does not, and fluency is the test.** Read
  the sentence with the blank in place; if it does not read as English, the hint is wrong.
  `The {{c1::<b>A</b>::which band?}} <b>band</b>` gives *"the [which band?] band is dark"* — the
  noun is said twice. Because "band" is already visible, the hint is simply `which?`.
- Where the visible sentence already pins the kind of thing being named — a definition, or a frame
  only one kind of thing fits — a bare `what?` is fine and often best —
  `A {{c1::<b>muscle fascicle</b>::what?}} bundles skeletal muscle fibers…` reads cleanly. Where
  nothing names it, the hint must: `{{c1::<b>sarcolemma</b>::which membrane?}}`. **A hint that asks
  for nothing at all is not a hint** — `what else?` is the clearest failure. Otherwise a hint names the category (`which organelle?`),
  prompts an action (`do what?`), offers an either/or (`raise or lower?`), asks for a definition
  (`what is it?`), or asks a cause (`why?`, whose answer is a whole clause). A two-option hint is
  *not* a leak; it makes recall fast.
- **Hide each cloze in turn.** Nothing visible — including the sibling answers — may give it away.

# Working

**Building a deck: start from `<folder>/plan.md`, with `inventory.md` open beside it** — the plan
says what each card is about, the inventory holds the verbatim quote and the slide image that
`Extra` needs. Starting from the plan alone leaves every `Extra` empty.

The plan carries the deck name, the planned cards as `ENTITY | ASPECT | VALUE | source`, the
ref-06/ref-07 decision if the deck is a recognition deck, the cuts under `## Cut`, and the
`## Carried to handover` section. If `plan.md` is not there, the planning step has not run: go back
to **[step 2 — organize](2-organize.md)** rather than planning inline. Deciding what a card is
*about* while a sentence is in front of you is the failure the split exists to prevent.

**Repairing cards already in Anki: there is no `plan.md`, and there should not be one.** That gate
is for building. Here the live cards are the input — read them from Anki, fix them against the seven,
and re-read a card's current text before editing it. **When a repair flips a card's roles, keep each
cloze number attached to the content it currently tests** — c1 stays on whatever c1 was blanking,
wherever that content moves in the sentence — so every card's review history follows its content
through the edit; the owner's own repairs do this. The plan-to-cards check below does not apply,
and neither does the handover report; you owe the user the list of what you changed and why.

**Draft 10–15 cards per pass and re-read the seven at the start of every pass.** Not from memory:
pull them up. Quality does not decay gently inside a long response, it collapses, because after the
first pass your nearest exemplar stops being ref-01 and becomes **your own previous card** — so
errors inherit instead of scattering. *One 228-card sitting used the facet role in half the cards in
its first block of 20 and in none at all by the seventh, with the exemplars in context throughout.*

**There is no target ratio**, with one exception — the clozed subject above — and even that is a
floor rather than a quota: a deck that comes in well under it is wrong, a deck at ten in ten is not.
Never manufacture a distribution. Otherwise judge every card against the seven and the rules, and if a
whole block skips a role entirely, go and look at those cards — the finding is in the cards, never
in a percentage.

A review reports; fixing is a separate pass that gets reviewed again. A flag sends you back to the
source, not to the markup.

# Anki

**Create the note type before you write anything.** A stock Anki does not have `Custom Cloze`, and
every insert fails at the end of the session with `model was not found`. One command, once:
`curl -s localhost:8765 -d @anki/custom-cloze.json` — see [`anki/README.md`](../anki/README.md).

Note type `Custom Cloze`; fields `Text` (the card), `Extra` (slide image + verbatim `Source:`
quote), `Source` (e.g. "Slide 12"). Deck by lecture, `<Course>::Test N::<Subject>::<Lecture>` —
**the folder says `Exam`, the deck says `Test`**; check `anki_find_notes` for the existing deck
before creating a sibling. Tag every card `<course>::<subject>::<topic>`, `test::N`,
`slide::<slug>-NN` — the slug is a short name for the *slide deck* the card came from
(`ct-14`, `bone-03`), and is required because two slide decks in one folder both number from 1.
Slide images go into `collection.media` as `<course>-<slug>-slide-NN.jpg`. The `tools/` scripts
emit their own working names; rename on the way in, when you `storeMediaFile`.

**On a recognition card the image goes in `Text`, not `Extra`.** `Extra` renders on the back only,
so an image parked there is invisible exactly when it is the question. On ref-06 it is inside the
`c1` cloze; on ref-07 it sits ahead of the sentence, unclozed. What `Extra` carries instead is
everything that would **leak the answer** if it were on the front — organ, stain, magnification —
plus the `Source:` quote and a link back to the slide.

A practical spans the whole course rather than one lecture, so it gets its own tree,
`<Course>::Lab Practical::<Tissue>`, tagged `lab-practical`. Media as
`<course>-labprac-<topic>-NN-<slug>.jpg`.

Re-read a live card's current text from Anki before editing it.

**Getting the notes in.** `anki_find_notes` and `anki_add_notes` above are the MCP server in this
repo. It is a convenience, not a requirement: it wraps [AnkiConnect](https://foosoft.net/projects/anki-connect/),
which is a plain HTTP endpoint on `localhost:8765`. Anything that can POST JSON can insert cards —
an agent without MCP, a shell script, or you.

**Create the deck first.** AnkiConnect will not do it for you — `addNotes` fails the whole
batch with `deck was not found`, and on a fresh collection every deck is new:

```bash
curl -s localhost:8765 -d '{"action":"createDeck","version":6,
  "params":{"deck":"<Course>::Test 2::Histology::Bone"}}'
```

```bash
curl -s localhost:8765 -d '{"action":"addNotes","version":6,"params":{"notes":[
  {"deckName":"<Course>::Test 2::Histology::Bone","modelName":"Custom Cloze",
   "fields":{"Text":"…","Extra":"…","Source":"Notes"},
   "tags":["<course>::histology::bone","test::2"]}]}}'
```

`addNotes` returns an array of note IDs, index-aligned with the input; a `null` means that note
failed, most often as a duplicate. Other actions worth knowing: `findNotes`, `notesInfo`,
`updateNoteFields`, `createDeck`, `storeMediaFile`.

**Stage the images before inserting**, or the cards render blank and `tools/check_deck.py` fails
every one of them:

```bash
curl -s localhost:8765 -d '{"action":"storeMediaFile","version":6,
  "params":{"filename":"<course>-<slug>-slide-01.jpg","path":"/abs/path/to/slide.jpg"}}'
```

# Handover

**Check the plan back against the cards first.** Every line in `plan.md` that was not cut must have
a card. Steps 1 and 2 each read their sources back against their own output; this is that same
check for the last hop, and without it a planned card that never got written is invisible — nothing
downstream notices a card that does not exist.

**Then check every subject, card by card.** Confirm each subject has its key identifier inside a
cloze. A subject split across two `<b>` runs (ref-05) counts as clozed — check the clozed run, not
each `<b>`. For
every one that does not, write the two other terms that answer its reverse question into the
handover — a visible subject with nothing named beside it is a defect, not a decision, and it goes
back for fixing. This is its own pass rather than something to trust from the writing pass, because
while a sentence is in front of you the reverse test gets felt rather than run, and it is always
felt in the same direction. If the visible subjects come to much more than one card in ten, do not
audit them one at a time — the default slipped, and the block gets rewritten.

Then write the deck to **`<folder>/deck.json`** — the `anki_add_notes` payload itself, deck name,
model, fields and tags — so an interrupted session can be resumed and inserted without rebuilding
it.

**Then the run-sheet — fixed steps, in order.** The first one also runs itself: a hook
(`.claude/settings.json` → `tools/hooks/on_deck_write.sh`) fires the structural check on every
write of a `deck.json`, so its report arrives whether or not anyone remembers to ask. The steps
exist because every one of them was once left to memory, and each was eventually forgotten by a
session that believed the deck was already clean.

1. **Check** — `python3 tools/check_deck.py --transcript <lecture.txt> deck.json` — the full form:
   media staged, every `Source:` quote found in the transcript it is attributed to. Must end
   `clean`. Read the report lines above the verdict too: the facet count and the slide coverage
   are reported rather than failed, and a cliff in either is a finding even when the verdict says
   clean — one deck shipped 11 facets across 125 cards against a plan that named 93, and another
   claimed full slide coverage over a slide with no card.
2. **Render** — `python3 tools/render_review.py deck.json`, then open `review.html`. The user
   reviews cards, not JSON, and the Fronts view is where the hint-fluency test runs — a hint the
   sentence will not read with only shows itself on the face.
3. **Audit** — launch **`deck-auditor`** (`.claude/agents/deck-auditor.md`) on the lecture folder.
   The deck's writer does not clear the deck: a self-check is strong on bookkeeping and blind to
   premise. *A 284-card deck once passed its plan reconciliation, its shape checker and its
   coverage table while built on the wrong unit of extraction — one look from a reader who had
   written none of it exposed the defect class.* The auditor's brief — truth, fluency, coverage,
   and style against the seven — is fixed in its definition precisely so it is not re-improvised
   each session; the one session that improvised it left style out, and the drift that angle
   would have caught reached the owner instead.
4. **Fix — and the writer ratifies nothing.** A flag sends you back to the source, not to the
   markup, and the fix is a separate pass that gets reviewed again. Every finding ends in one of
   exactly two states: **fixed**, or **approved by a context that wrote none of the cards** — a
   fresh adjudicator given the finding, the card and its sources, or the owner. What the writer
   may not do is accept a finding away, however reasonable the acceptance reads: the session that
   wrote the card is judging the pattern it chose, not the card in front of it. *An auditor filed
   a bare either/or cloze as "a design choice, noted once"; the writer — whose choice it was —
   accepted it, and the card reached the owner still broken on every front the auditor had
   grouped away.* Re-run steps 1 and 2 after the fixes.

With the audited deck, **report `plan.md`'s `## Carried to handover` section in full — unprompted, once.** Every
item in it exists because something was decided on the user's behalf: a term overruled, an
objective nothing answered, a source conflict resolved, a fact cut. A decision like that is
reported at handover, not left in a note field or a file for them to find.

Report the section as it stands; do not keep a list here of what it should contain. Upstream owns
what goes in, this step owns that it arrives — that separation is why nothing falls between them.

Insert with `anki_add_notes` **only when the user says go** — never before, and never inferred.
