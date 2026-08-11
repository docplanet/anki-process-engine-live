#!/usr/bin/env python3
"""Structural check for a deck before it reaches Anki.

Recognises the three card shapes in method/3-cards.md and applies the rules that belong to each,
so the seven reference exemplars all pass — which method/3-cards.md requires of any check.

  prose   ref-01..ref-05  a subject in <b>, an answer in <i>, one to three clozes, every cloze hinted
  ref-06  image inside c1, no hint on it, no <b>, makes two cards
  ref-07  image visible, exactly one cloze, no <b>, nothing on the front naming the answer

Accepts a bare list of notes, {"notes": [...]}, or an AnkiConnect {"params": {"notes": [...]}}
payload. Exits non-zero if anything fails, so it can gate a pipeline.

    python3 tools/check_deck.py [--no-media] deck.json
    ANKI_MEDIA=/path/to/collection.media python3 tools/check_deck.py deck.json
"""
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


def clozes(text):
    """[(number, value, hint_or_None)] — the hint is whatever follows the last '::'."""
    out = []
    for match in CLOZE.finditer(text):
        # Anki splits at the FIRST "::", so anything after it is hint, "::" and all.
        value, separator, hint = match.group(2).partition("::")
        out.append((match.group(1), value, hint if separator else None))
    return out


def shape_of(text):
    stripped = text.lstrip()
    if stripped.startswith("{{c1::<img"):
        return "ref-06"
    if stripped.startswith("<img"):
        return "ref-07"
    return "prose"


def check(note, check_media=True):
    """Return a list of problem strings for one note."""
    problems = []
    fields = note["fields"]
    text = fields["Text"]
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

    if len(numbers) > 3:
        problems.append(f"{len(numbers)} cloze numbers; never more than three")

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
    args = [a for a in argv[1:] if not a.startswith("-")]
    flags = {a for a in argv[1:] if a.startswith("-")}
    if len(args) != 1 or flags - {"--no-media"}:
        print("usage: check_deck.py [--no-media] deck.json", file=sys.stderr)
        return 2

    check_media = "--no-media" not in flags and os.path.isdir(MEDIA_DIR)
    if not check_media and "--no-media" not in flags:
        print(f"note: {MEDIA_DIR} not found - skipping the media check", file=sys.stderr)

    notes = load(args[0])
    if not notes:
        print(f"{args[0]} contains no notes", file=sys.stderr)
        return 2
    findings = [(i, p) for i, note in enumerate(notes, 1) for p in check(note, check_media)]

    # On a recognition card the first non-image cloze IS the answer; on a prose card it is the
    # subject. Counting them in one column would be counting two different things.
    subjects, answers = Counter(), Counter()
    for note in notes:
        text = note["fields"]["Text"]
        first = next((re.sub(r"<[^>]+>", "", v) for _, v, _ in clozes(text)
                      if not IMAGE_TAG.search(v)), None)
        if first:
            (answers if shape_of(text) != "prose" else subjects)[first] += 1

    print(f"notes: {len(notes)}")
    for label, counter in (("answer", answers), ("subject", subjects)):
        for value, count in counter.most_common():
            print(f"  {count:3d}  {label:8s} {value}")
    print("PROBLEMS:" if findings else "clean")
    for position, problem in findings:
        print(f"   note {position}: {problem}")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
