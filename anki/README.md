# The `Custom Cloze` note type

The method writes into a note type called **`Custom Cloze`**, with three fields — `Text`, `Extra`,
`Source` — and CSS that gives the three roles three colours. A stock Anki install does not have it:
it ships `Cloze` with `Text` / `Back Extra`, so an insert would fail with
`model was not found: Custom Cloze`.

**Create it once, before writing any cards:**

```bash
curl -s localhost:8765 -d @anki/custom-cloze.json
```

`null` means it worked. `Model name already exists` means you already have it — nothing to do.
Anki must be running with [AnkiConnect](https://foosoft.net/projects/anki-connect/) installed.

## Why the CSS matters

It is not decoration. `method/3-cards.md` marks three roles — `<b>` subject, `<u>` facet,
`<i>` value — and the styling is what makes them distinguishable on the rendered card:

```css
.cloze { font-weight: bold; color: MediumSeaGreen; }
b { color: #C695C6 !important; }
i { color: IndianRed !important; }
u { color: #5EB3B3 !important; }
```

That `.cloze` rule is also the reason for the strictest markup rule in the method — **a role tag
must sit directly on the text it styles, never wrapping a cloze.** Anki renders a revealed cloze as
its own `<span class="cloze">`, and that span sets `color` on itself, so a colour merely *inherited*
from an enclosing `<b>` is overridden and the role disappears on screen. With the stock Cloze
styling there is no colour to lose and the rule looks arbitrary; with this CSS you can see it fail.

## One thing to know about the colours

Measured against the card background `#333B45`, the contrast ratios are:

| role | colour | contrast |
|---|---|---|
| `<b>` subject | `#C695C6` | 4.60:1 |
| `<u>` facet | `#5EB3B3` | 4.63:1 |
| `.cloze` | MediumSeaGreen | 4.25:1 |
| **`<i>` value** | **IndianRed** | **2.85:1** |
| body text | `#D7DEE9` | 8.38:1 |

`<i>` is the *answer* — the most important text on the card — and at 2.85:1 it is below the WCAG AA
floor for body text (4.5:1) and below even the large-text floor (3:1). It is legible on a good
screen and tiring on a bad one. `#DD9292` is the same hue and saturation with the lightness raised
until it clears the floor (4.64:1); the shipped value is left alone so that decks already built
against it do not change colour under their author. Change both together if you change either.

(`.cloze` at 4.25:1 is also under the body-text floor, but it is a *blank* — a short span the eye is
hunting for, not prose to read — so it is left as is.)

## Fields

| field | holds |
|---|---|
| `Text` | the card. On a recognition card the image goes **here**, not in `Extra` |
| `Extra` | back only: the slide image or context, and the verbatim `Source:` quote |
| `Source` | a short provenance label, e.g. `Slide 12` or `Notes` |

`Extra` renders on the back, so anything parked there is invisible exactly when it is the question —
which is why a recognition card's image lives in `Text`, and why everything that would leak the
answer (organ, stain, magnification) belongs in `Extra`.

## Changing it later

The MCP server in this repo is read-only about note types on purpose (`modelNames`,
`modelFieldNames`), and AnkiConnect cannot restyle templates safely once cards exist. Edit the note
type in Anki's own **Tools → Manage Note Types**, then re-export it here:

```bash
curl -s localhost:8765 -d '{"action":"modelStyling","version":6,"params":{"modelName":"Custom Cloze"}}'
```
