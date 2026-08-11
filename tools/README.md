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
| histologyguide.org | the viewer canvas, at `?x=&y=&z=` | `<slide>/annotations.xml` — named structures at exact x/y/zoom |
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

**3b. Capture histologyguide fields of view.** Start the sink, then drive the viewer in a browser:

```bash
python3 tools/capture_server.py shots 8799
```

Navigate to the first view by URL (`…/05-slide-1.html?x=…&y=…&z=…`), then run
[`capture_views.js`](capture_views.js) in the page. It composites the tile canvases, retries while
the image is still blank, posts the bytes to the sink, and sets `location.href` to the next view —
so one call per page load, and the script survives a tool timeout.

Two traps, both silent:

- **`?z=75.567` is a percentage; `Z.Viewport.zoomAndPanToView(x, y, z)` wants a 0–1 fraction** and
  clamps anything larger to 1. Pass the percentage and you get a plausible, blurry, wrong-tier
  image — no error.
- **Programmatic pan/zoom only renders sharp on a freshly URL-loaded page.** Load the first view by
  URL, then `zoomAndPanToView` for the rest of that slide's views.

**4. Stage the images into Anki, write the cards, then check them.** `check_deck.py` fails any
card whose image is not already in `collection.media` — see the `storeMediaFile` call in
[`method/3-cards.md`](../method/3-cards.md).

```bash
python3 tools/check_deck.py deck.json
```

It looks for each card's image in Anki's `collection.media`. Point it elsewhere with
`ANKI_MEDIA=/path/to/collection.media`, or skip that check with `--no-media`.

Exactly one cloze, image present and unclozed, answer in `<i>` with a hint, and nothing on the
rendered front that names the answer. It deliberately ignores the hint — a hint
is allowed to name the category (`which tissue?`) even when the answer ends in that word.

## Dependencies

`read_slide_handout.py`, `capture_server.py` and `check_deck.py` are standard library only.
`fetch_overlay_slides.py` and `fetch_unlabeled_slides.py` need Pillow, and macOS system Python refuses to install into
itself (PEP 668), so give them a venv:

```bash
python3 -m venv .venv && .venv/bin/pip install Pillow
```
