# Turning a virtual-slide handout into card images

A lab handout is not slides and notes. It is a **list of links to virtual-slide viewers**, walked
through in the session. Nothing in it is an image yet, so the three skills have nothing to read:
this is a converter step, the same kind as `soffice` for a `.pptx`, and it belongs before step 1
rather than inside it.

Cards built this way are `ref-07` in [`method/3-cards.md`](../method/3-cards.md) — one
cloze, image visible, no reverse card. Read that first; it decides what you are capturing.

## What each source gives you

Every one of these hands over both an **unlabeled image** and **its own authoritative label**, by a
different route. That matters: the label is what makes the answer defensible, and it means you are
never inventing what a field of view shows.

| site | unlabeled image | its own label |
|---|---|---|
| histologyguide.org | tiles read out of `/slides/<slide>.zif` | `<slide>/annotations.xml` — named structures at exact x/y/zoom |
| digitalhistology.org (VCU) | the base image of each `subcontent-N` | `<h3 class="slide-title">`, one per pointer overlay |
| medcell.org (Histology@Yale) | `images/<slug>.jpg` | `<div class="slide-title">`; labels live in a separate `_labels.png` |
| histologyslides.med.umich.edu | viewer canvas, **whole-slide only** | none — it ignores zoom URL parameters |

**Always look at what you downloaded before carding it.** A couple of these print the answer onto
the image — a labelled TEM, a caption reading "Elastic fibers" across the middle. Build a contact
sheet of the batch and look at it; roughly one capture in ten also comes back blank or half-loaded.

## The steps

**1. Read the handout.** No dependencies, no browser.

```bash
python3 tools/read_slide_handout.py "coursework/.../Lab Handout.docx" -o slides.json
```

Prints every link with the section and caption it sits under, the instructor's own field of view
when the URL carries one, and every named structure on the slide with its coordinates.

**2. Decide which fields of view earn a card.** This is the judgement, and it is the notes' job.
The handout says what is *assigned*; the notes say what was *taught*. A slide earns a
card where the instructor stopped on it — and the asides are where the exam signals are: which
appearance is expected cold, which tissues must be known in both cross and longitudinal section.

**3a. Scrape the sites that are already flashcards.** VCU and Yale need no browser:

```bash
python3 tools/fetch_overlay_slides.py targets.json        # [["https://digitalhistology.org/.../hyaline-6/", "slug"], ...]
python3 tools/fetch_unlabeled_slides.py blood_bone_marrow_lab erythrocytes neutrophil -o shots -p blood
```

**3b. Render histologyguide fields of view.** No browser. A histologyguide slide is one `.zif` —
Zoomify Image Format, which is a BigTIFF holding the whole pyramid as JPEG tiles, and the server
takes range requests. So a field of view is arithmetic rather than a screenshot:

```bash
.venv/bin/python tools/fetch_zif_view.py views.json -o shots
```

`views.json` is `[{"name", "slide", "x", "y", "z", "w", "h"}, …]`. Paste `x`, `y`, `z` straight
across from `annotations.xml` or from a slideview URL — `z` is the percentage those write, and the
tool picks the tier itself. `read_slide_handout.py -o slides.json` gives you every coordinate on
every assigned slide, so the whole batch is one loop over that file.

Deterministic, so the same coordinates give the same image: no settle timers, no half-drawn tiles,
no clamped zoom. Look at the batch anyway — for what a field *contains*, not whether it rendered.

<details><summary>The browser route it replaced, still here for a viewer that is not Zoomify</summary>

Start the sink, navigate to the first view by URL (`…/05-slide-1.html?x=…&y=…&z=…`), then run
[`capture_views.js`](capture_views.js) in the page. It composites the tile canvases, retries while
the image is still blank, posts the bytes to [`capture_server.py`](capture_server.py), and sets
`location.href` to the next view — one call per page load, and the script survives a tool timeout.

```bash
python3 tools/capture_server.py shots 8799
```

Three traps, all silent:

- **`?z=75.567` is a percentage; `Z.Viewport.zoomAndPanToView(x, y, z)` wants a 0–1 fraction** and
  clamps anything larger to 1. Pass the percentage and you get a plausible, blurry, wrong-tier
  image — no error.
- **Programmatic pan/zoom only renders sharp on a freshly URL-loaded page.** Load the first view by
  URL, then `zoomAndPanToView` for the rest of that slide's views.
- **The browser may refuse to reach the sink at all.** A page on a public origin posting to
  `127.0.0.1` is subject to Private Network Access, and some embedded browsers block it outright
  (`net::ERR_BLOCKED_BY_CLIENT`) whatever the server replies. Check the network log before
  debugging the capture itself.

</details>

**4. Stage the images into Anki, write the cards, then check them.** `check_deck.py` fails any
card whose image is not already in `collection.media` — see the `storeMediaFile` call in
[`method/3-cards.md`](../method/3-cards.md).

```bash
python3 tools/check_deck.py --transcript "coursework/.../lecture.txt" deck.json
```

It looks for each card's image in Anki's `collection.media`. Point it elsewhere with
`ANKI_MEDIA=/path/to/collection.media`, or skip that check with `--no-media`.

In Claude Code the structural form of this runs by itself: a hook
([`hooks/on_deck_write.sh`](hooks/on_deck_write.sh), wired in `.claude/settings.json`) fires it on
every write of a `deck.json`. The full form above — media and `--transcript` — is still a step,
because only the writer knows where the transcript is.

`--transcript` checks each quote a card attributes to the lecture against the lecture's own words
— gated on the card's `Source` saying so, because the transcript is the wrong authority for a
slide's text. Beside the pass/fail checks it also reports, without failing, two deck-wide numbers
no single card can show: how many prose cards carry a `<u>` facet, and which slides between the
first and last carded one have no card at all. Both drifts shipped once; the counts are how they
get seen.

Exactly one cloze, image present and unclozed, answer in `<i>` with a hint, and nothing on the
rendered front that names the answer. It deliberately ignores the hint — a hint
is allowed to name the category (`which tissue?`) even when the answer ends in that word.

On prose cards it also holds the line that judgment keeps sliding off: **the card ends on its
answer** (a clause trailing the final cloze is content the blank never asked for — eleven cards in
one deck shipped that way and parsed cleanly), no role tag wrapping a cloze (the rendered colour
silently vanishes — see [`anki/README.md`](../anki/README.md)), hints one to three words ending in
`?`, and no possessive outside the bolded subject. Subjects never clozed are *reported*, not
failed — a visible subject is legal only with a defence, and a script cannot read a defence.

**Two of its checks are about what the card claims, not how it is built.** Both exist because a
deck shipped with the mistake and re-reading never caught it:

- **`?z=50` is 50% zoom, not the 50x objective.** Writing the zoom onto the back as a
  magnification reads perfectly and is wrong; it went through six decks. The tell is mechanical —
  the stated `Nx` equals the `z` in the card's own link — so the check just looks for that.
  State an objective only where a source states one: histologyguide's `annotations.xml` sometimes
  names it ("Motor Neuron (40x)" at `z=100`), and that ratio belongs to *that* scan, not to slides
  generally. Otherwise write low / mid / high power.
- **`--transcript` checks each `Source:` quote against the lecture it is attributed to.** Not as a
  substring: it strips the Zoom scaffolding, then requires the quote's words to appear in order
  without much foreign material between them, because speech is disfluent and the ASR punctuates
  it at random — tidying a stray "oh." out of the middle of a clause is faithful, inventing a
  sentence is not. Mark elisions with `...` and repairs with `[brackets]`, and bracket a **whole
  word** — `[Toluidine] Blue`, never `Tolu[idine] Blue` — or the check is left hunting half a
  word, and so are you.

Neither replaces reading. A quote can be word-perfect and attached to the wrong image, and a
description can name a feature that is not in the picture — this deck had both, and only an
independent pass over the images found them.

**5. Render the deck for review.** The handover step shows the user cards, not JSON:

```bash
python3 tools/render_review.py deck.json          # review.html beside deck.json
```

One page, every note: a front per cloze (that blank shown as its `[hint]`, siblings revealed),
the backs, the Source line, the Extra with its staged image. The Fronts view is where the
hint-fluency test runs — read each sentence with the blank in place and it must still be English.


## Dependencies

`read_slide_handout.py`, `capture_server.py`, `check_deck.py` and `render_review.py` are
standard library only.
`fetch_zif_view.py`, `fetch_overlay_slides.py` and `fetch_unlabeled_slides.py` need Pillow, and
macOS system Python refuses to install into itself (PEP 668), so give them a venv:

```bash
python3 -m venv .venv && .venv/bin/pip install Pillow
```
