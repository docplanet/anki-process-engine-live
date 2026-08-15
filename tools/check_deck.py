#!/usr/bin/env python3
"""Structural check for a deck before it reaches Anki.

Recognises the three card shapes in method/3-cards.md and applies the rules that belong to each,
so the seven reference exemplars all pass — which method/3-cards.md requires of any check.

  prose   ref-01..ref-05  a subject in <b>, an answer in <i>, one to three clozes, every cloze hinted
  ref-06  image inside c1, no hint on it, no <b>, makes two cards
  ref-07  image visible, exactly one cloze, no <b>, nothing on the front naming the answer

Accepts a bare list of notes, {"notes": [...]}, or an AnkiConnect {"params": {"notes": [...]}}
payload. Exits non-zero if anything fails, so it can gate a pipeline.

Two of the checks are about what a card *claims* rather than how it is shaped, because both were
things a whole deck shipped with and no reading pass caught:

  - a magnification that is really the slide link's own zoom percentage ("50x" beside ?z=50)
  - a `Source:` quote whose words are not in the transcript it is attributed to (--transcript)

Beside the failures it reports two deck-wide numbers it cannot fail — the <u> facet count and
the slide-tag coverage — because both drifts shipped once and neither is visible per-card.

    python3 tools/check_deck.py [--no-media] deck.json
    python3 tools/check_deck.py --transcript "lecture.txt" deck.json
    ANKI_MEDIA=/path/to/collection.media python3 tools/check_deck.py deck.json
"""
import html
import json
import os
import re
import sys
from collections import Counter

DEFAULT_MEDIA = os.path.expanduser("~/Library/Application Support/Anki2/User 1/collection.media")
if not os.path.isdir(DEFAULT_MEDIA):                       # Linux / non-default profile
    DEFAULT_MEDIA = os.path.expanduser("~/.local/share/Anki2/User 1/collection.media")
MEDIA_DIR = os.environ.get("ANKI_MEDIA", DEFAULT_MEDIA)

# Body runs to the first "}}", so a cloze can never straddle into the next one.
CLOZE = re.compile(r"\{\{c(\d+)::((?:(?!\}\})[\s\S])*)\}\}")
IMAGE_TAG = re.compile(r"<img\b[^>]*>")
IMAGE_SRC = re.compile(r'''<img\b[^>]*\bsrc=["']([^"']+)["']''')

LINK_ZOOM = re.compile(r"[?&]z=([\d.]+)")
MAGNIFICATION = re.compile(r"\b(\d+)x\b")
# The label form ('Source (spoken): "..."') is how real decks write their quotes - in ASCII
# quotes, which the curly-quote forms here never matched, so for a while this check passed
# decks it had never read. The curly forms are kept for anything older.
QUOTED = re.compile(r"&ldquo;([\s\S]*?)&rdquo;|“([\s\S]*?)”|:\s*\"([\s\S]*?)\"")
# A quote is checked in pieces: "..." marks something left out, and "[]" marks a word repaired,
# so neither span is expected to appear in the source verbatim.
QUOTE_GAP = re.compile(r"\.\.\.|…|\[[^\]]*\]")
MIN_FRAGMENT_WORDS = 5                                     # shorter pieces match by accident


def clozes(text):
    """[(number, value, hint_or_None)] — the hint is whatever follows the last '::'."""
    out = []
    for match in CLOZE.finditer(text):
        # Anki splits at the FIRST "::", so anything after it is hint, "::" and all.
        value, separator, hint = match.group(2).partition("::")
        out.append((match.group(1), value, hint if separator else None))
    return out


def zoom_worn_as_magnification(extra):
    """['50x vs z=50'] — a stated objective that is really the slide link's zoom percentage.

    `?z=50` on a virtual slide is 50% zoom of the scan, not the 50x objective, and the two are
    unrelated numbers. Writing the zoom onto the card as "50x" reads perfectly and is wrong; the
    tell is that it equals the z in the card's own link. It survived six decks before anyone asked.
    """
    zoom = LINK_ZOOM.search(extra)
    if not zoom:
        return []
    stated = float(zoom.group(1))
    # The claim is the zoom rounded to something tidy, so allow for that: z=74.286 got written up
    # as "75x", z=19.475 as "20x". Anything this close to the link's own z is the zoom, not a lens.
    tolerance = max(1.0, 0.02 * stated)
    return [f"{claim}x vs z={zoom.group(1)}" for claim in set(MAGNIFICATION.findall(extra))
            if abs(float(claim) - stated) <= tolerance]


TIMESTAMP = re.compile(r"^\d{1,2}:\d{2}:\d{2}\s*-->\s*\d{1,2}:\d{2}:\d{2}\s*$")
SPEAKER = re.compile(r"^[^:]{1,40}:\s")


def words(text):
    return re.findall(r"[a-z0-9&]+", text)


def normalize(text):
    text = html.unescape(re.sub(r"<[^>]+>", " ", text)).lower()
    for fancy, plain in (("’", "'"), ("‘", "'"), ("“", '"'),
                         ("”", '"'), ("—", "-"), ("–", "-")):
        text = text.replace(fancy, plain)
    return re.sub(r"\s+", " ", text)


def load_transcript(path):
    """The spoken words alone, run together.

    A Zoom transcript wraps every utterance in a timestamp block and a speaker name, so a quote
    that runs across two lines - which most do, since the speaker pauses mid-sentence - never
    appears as one contiguous string until that scaffolding comes out.
    """
    with open(path, encoding="utf-8", errors="replace") as handle:
        lines = handle.read().splitlines()
    spoken = [SPEAKER.sub("", line).strip() for line in lines
              if line.strip() and not TIMESTAMP.match(line)]
    return words(normalize(" ".join(spoken)))


def find_words(fragment, transcript, start):
    """Where `fragment`'s words run, in order, from `start` on - or -1.

    Not a substring match. Speech is disfluent and the ASR punctuates it at random - a sentence
    comes back as "the outer layer here. is the capsule", or with an "oh." dropped into the middle
    of a clause - so a quote that tidies that up is still faithful. What must hold is that every
    word appears, in order, without much foreign material wedged in between, which fabricated or
    reordered text cannot satisfy.
    """
    slack = max(4, len(fragment) // 4)
    for begin in (i for i, word in enumerate(transcript[start:], start) if word == fragment[0]):
        at, skipped = begin, 0
        for word in fragment:
            while at < len(transcript) and transcript[at] != word:
                at, skipped = at + 1, skipped + 1
                if skipped > slack:
                    break
            if skipped > slack or at >= len(transcript):
                break
            at += 1
        else:
            return at
    return -1


def unsourced_quote_fragments(extra, transcript):
    """Pieces of the card's Source quote that are not in the transcript it claims to come from."""
    found = QUOTED.search(extra)
    if not found:
        return []
    quote = normalize(found.group(1) or found.group(2) or found.group(3))
    missing, cursor = [], 0
    for piece in QUOTE_GAP.split(quote):
        fragment = words(piece)
        if len(fragment) < MIN_FRAGMENT_WORDS:
            continue
        # Fragments must also appear in order, so a quote cannot be assembled back to front.
        position = find_words(fragment, transcript, cursor)
        if position < 0:
            text = " ".join(fragment)
            missing.append(text[:60] + ("..." if len(text) > 60 else ""))
        else:
            cursor = position
    return missing


def shape_of(text):
    stripped = text.lstrip()
    if stripped.startswith("{{c1::<img"):
        return "ref-06"
    if stripped.startswith("<img"):
        return "ref-07"
    return "prose"


def check(note, check_media=True, transcript=None):
    """Return a list of problem strings for one note."""
    problems = []
    fields = note["fields"]
    text = fields["Text"]
    extra = fields.get("Extra", "") or ""
    shape = shape_of(text)
    spans = clozes(text)
    numbers = sorted({n for n, _, _ in spans}, key=int)

    if not spans:
        return ["no cloze at all"]
    # Extra as well as Text: the method puts a slide image in Extra on prose cards, and an
    # unstaged one renders blank on the back exactly like an unstaged one on the front.
    for field in ("Text", "Extra"):
        for tag in IMAGE_TAG.findall(fields.get(field, "") or ""):
            source = IMAGE_SRC.search(tag)
            if not source:
                problems.append(f"an <img> with no src in {field}")
                continue
            if check_media and not os.path.exists(os.path.join(MEDIA_DIR, source.group(1))):
                problems.append(f"media missing from the collection: {source.group(1)} (in {field})")

    for claim in zoom_worn_as_magnification(extra):
        problems.append(f"states {claim}: a slideview z is a zoom percentage, not an objective")

    # Only a quote the card itself attributes to the lecture is checked against it - the
    # transcript is the wrong authority for a slide's text, so the gate is the Source field.
    if transcript is not None and "transcript" in fields.get("Source", "").lower():
        for fragment in unsourced_quote_fragments(extra, transcript):
            problems.append(f"quoted text is not in the transcript: {fragment!r}")

    for number, value, hint in spans:
        is_image = bool(IMAGE_TAG.search(value))
        if is_image:
            if hint:
                problems.append("the image cloze carries a hint; it should have none")
            continue
        if not re.search(r"<[biu]>", value):
            problems.append(f"c{number} has no role tag on {value[:40]!r}")
        shared = [(v, h) for n, v, h in spans if n == number]
        if hint is None and not (len(shared) > 1 and shared[0][1]):
            problems.append(f"c{number} carries no hint")
        if hint is not None:
            if not hint.endswith("?"):
                problems.append(f"c{number} hint does not end in '?': {hint!r}")
            elif "," in hint or len(hint.rstrip("?").split()) > 3:
                problems.append(f"c{number} hint is not one to three words: {hint!r}")

    if len(numbers) > 3:
        problems.append(f"{len(numbers)} cloze numbers; never more than three")

    # The card ends on its answer. Trailing scaffolding after the final cloze - ", running
    # dorsally on each side of the foregut" - is content the blank never asks for: it either
    # deserved its own card or belongs in Extra. Eleven cards in one deck shipped this way, and
    # no pass caught it because every one of them parsed cleanly.
    tail = html.unescape(re.sub(r"<[^>]+>", "", text[text.rfind("}}") + 2:])).strip()
    if tail:
        problems.append(f"text after the final cloze: {tail[:48]!r}")

    # A role tag never wraps a cloze. Anki renders a revealed cloze as its own span.cloze, which
    # sets colour on itself, so a colour merely inherited from an enclosing <b> is overridden and
    # the role silently vanishes on screen. The tag goes inside the braces (see anki/README.md).
    if re.search(r"<[biu]>[^<]*\{\{c\d", text):
        problems.append("a role tag wraps a cloze; the tag must sit directly on the text")

    # A possessive outside the bolded subject means the entity is wrong - with the right entity
    # there is nothing to possess, only to describe. Eponyms (Wharton's jelly) live inside <b>.
    if shape == "prose":
        bare = re.sub(r"<b>[\s\S]*?</b>", " ", text)
        bare = html.unescape(bare).replace("’", "'")
        if re.search(r"\w's\s", bare):
            problems.append("a possessive outside the subject; step 2 handed the wrong entity")

    # One subject, literally. Two <b> runs are legal for exactly one case: a single name split by
    # the cloze boundary ("<b>A</b> ... <b>band</b>", adjacent). A bolded noun, an unbolded
    # connective, and a second free-standing bold phrase is TWO subjects on the rendered face -
    # eight cards in one deck shipped that way, written once and inherited batch-wide, and every
    # gate passed them because none counted bold runs.
    if shape == "prose":
        flat = CLOZE.sub(lambda m: m.group(2).partition("::")[0], text)
        bolds = list(re.finditer(r"<b>(?:(?!</b>)[\s\S])*</b>", flat))
        for left, right in zip(bolds, bolds[1:]):
            gap = flat[left.end():right.start()]
            if re.sub(r"&nbsp;|\s", "", gap):
                problems.append(f"a second <b> run split from the subject by {gap.strip()[:24]!r}; "
                                "one subject, one name")
                break

    # An inline series has a ceiling. ref-04 blesses "embryonic, proper, and specialized types";
    # nine items in one <i> span is not that card, it is an unwritten list. Five or more items
    # (4+ commas) fail; exactly four items is close enough to judgment that it is only counted,
    # in the summary, not failed.
    if shape == "prose" and not re.search(r"(?m)^\s*\d\.", re.sub(r"<[^>]+>", "", text)):
        for _, value, _ in spans:
            if IMAGE_TAG.search(value):
                continue
            item_commas = re.sub(r"<[^>]+>", "", value).count(",")
            if item_commas >= 4:
                problems.append(f"a {item_commas + 1}-item series inline; ref-05 list form")
                break

    if shape == "prose":
        if "<b>" not in text:
            problems.append("no <b> subject on a card that is not a recognition card")
    else:
        if "<b>" in text:
            problems.append("a recognition card must carry no <b>; this one does")

    if shape == "ref-06" and numbers != ["1", "2"]:
        problems.append(f"image is clozed (ref-06) so expect c1 and c2, found {numbers}")

    if shape == "ref-07":
        if numbers != ["1"]:
            problems.append(f"image is visible (ref-07) so expect c1 alone, found {numbers}")
        answer = next((v for n, v, _ in spans if n == "1"), "")
        # The rendered front: text before the cloze plus whatever trails it, image tag removed.
        # The hint is excluded deliberately — a hint may name the category ("which tissue?")
        # even when the answer ends in that same word.
        trailing = text[text.rfind("}}") + 2:]
        front = IMAGE_TAG.sub(" ", text[:text.find("{{")]) + " " + trailing
        front = re.sub(r"<[^>]+>", " ", front).lower()
        for word in re.sub(r"<[^>]+>", "", answer).lower().split():
            if len(word) > 3 and word in front:
                problems.append(f"the answer word {word!r} is visible on the front")

    return problems


def load(path):
    try:
        with open(path) as handle:
            data = json.load(handle)
    except OSError as error:
        raise SystemExit(f"cannot read {path}: {error}")
    except json.JSONDecodeError as error:
        raise SystemExit(f"{path} is not valid JSON: {error}")
    if isinstance(data, dict):                              # {"notes": …} or AnkiConnect payload
        data = data.get("params", data).get("notes", [])
    if not isinstance(data, list):
        raise SystemExit(f"{path}: expected a list of notes")
    for position, note in enumerate(data, 1):
        if not isinstance(note, dict) or "Text" not in note.get("fields", {}):
            raise SystemExit(f"{path}: note {position} has no fields.Text")
    return data


def main(argv):
    transcript_path = None
    if "--transcript" in argv:
        position = argv.index("--transcript")
        transcript_path = argv[position + 1]
        argv = argv[:position] + argv[position + 2:]

    args = [a for a in argv[1:] if not a.startswith("-")]
    flags = {a for a in argv[1:] if a.startswith("-")}
    if len(args) != 1 or flags - {"--no-media"}:
        print("usage: check_deck.py [--no-media] [--transcript lecture.txt] deck.json",
              file=sys.stderr)
        return 2

    check_media = "--no-media" not in flags and os.path.isdir(MEDIA_DIR)
    if not check_media and "--no-media" not in flags:
        print(f"note: {MEDIA_DIR} not found - skipping the media check", file=sys.stderr)

    transcript = None
    if transcript_path:
        try:
            transcript = load_transcript(transcript_path)
        except OSError as error:
            raise SystemExit(f"cannot read {transcript_path}: {error}")

    notes = load(args[0])
    if not notes:
        print(f"{args[0]} contains no notes", file=sys.stderr)
        return 2
    findings = [(i, p) for i, note in enumerate(notes, 1)
                for p in check(note, check_media, transcript)]

    # On a recognition card the first non-image cloze IS the answer; on a prose card it is the
    # subject. Counting them in one column would be counting two different things.
    subjects, answers = Counter(), Counter()
    for note in notes:
        text = note["fields"]["Text"]
        first = next((re.sub(r"<[^>]+>", "", v) for _, v, _ in clozes(text)
                      if not IMAGE_TAG.search(v)), None)
        if first:
            (answers if shape_of(text) != "prose" else subjects)[first] += 1

    # Reported, not failed: a visible subject is legal only with a defence (two other terms that
    # answer its reverse question), and a script cannot read a defence. The method's floor is
    # roughly nine in ten clozed - if this list is long, the default slipped.
    visible = [i for i, note in enumerate(notes, 1)
               if shape_of(note["fields"]["Text"]) == "prose"
               and not re.search(r"\{\{c\d+::<b>", note["fields"]["Text"])]

    print(f"notes: {len(notes)}")
    for label, counter in (("answer", answers), ("subject", subjects)):
        for value, count in counter.most_common():
            print(f"  {count:3d}  {label:8s} {value}")
    if visible:
        print(f"subjects never clozed ({len(visible)} - each needs a defence): "
              + ", ".join(f"note {i}" for i in visible))

    # Reported, not failed, like the visible subjects above. A definition card carries no facet
    # legitimately, so a script cannot fail a card for the lack; what it can do is show the
    # deck-wide number. The drift this exists for sat at 11 of 125 against a plan that named an
    # aspect on 93 rows, and no per-card reading surfaced the cliff - only the count does.
    prose_notes = [note for note in notes if shape_of(note["fields"]["Text"]) == "prose"]
    if prose_notes:
        faceted = sum(1 for note in prose_notes if "<u>" in note["fields"]["Text"])
        print(f"facets: {faceted} of {len(prose_notes)} prose cards carry a <u>")

    # Reported, not failed: a negation inside a blank is usually a contrast bolted onto the
    # answer ("X - not Y"), which belongs in Extra as a **flag** line - but sometimes the
    # negative IS the fact ("red blood cells do not cross"), so a script can only count.
    # Nine live cards across three decks carried the bolted kind before anyone counted.
    negated = [i for i, note in enumerate(notes, 1)
               if any(re.search(r"\bnot\b|\bnever\b|rather than|instead of|unlike",
                                re.sub(r"<[^>]+>", "", v), re.I)
                      for _, v, _ in clozes(note["fields"]["Text"]))]
    if negated:
        print(f"negations inside a blank ({len(negated)} - contrast belongs in Extra "
              f"unless the negative is the fact): " + ", ".join(f"note {i}" for i in negated))

    # Also reported, not failed: which slides the deck covers, read off the slide:: tags. A
    # missing card is invisible in principle - no card shows you a card that does not exist -
    # and one deck claimed full slide coverage while a slide inside its range had none. Only
    # holes between the first and last carded slide are visible from the tags; the printed
    # range is the invitation to compare its far end against the deck's real last slide.
    slide_tag = re.compile(r"slide::.+-(\d+)$")
    carded = {int(m.group(1)) for note in notes for tag in note.get("tags", [])
              for m in [slide_tag.match(tag)] if m}
    if carded:
        low, high = min(carded), max(carded)
        holes = [str(s) for s in range(low, high + 1) if s not in carded]
        print(f"slide tags cover {low}-{high}"
              + (f"; no card for: {', '.join(holes)}" if holes else ""))
    print("PROBLEMS:" if findings else "clean")
    for position, problem in findings:
        print(f"   note {position}: {problem}")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
