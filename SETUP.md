# Setup

There is no program to run, and the method itself installs nothing — the packages below are only
for converting source files before the method reads them. The method is the three markdown files in
[`method/`](method/) — see [`AGENTS.md`](AGENTS.md) to start. This page lists the outside tools that
turn source files into something the method can read, and the commands to run them.

## Required

**Anki, running, with the AnkiConnect add-on** (code `2055492159`).

**The `Custom Cloze` note type** — create it once. See [`anki/README.md`](anki/README.md).

```bash
curl -s localhost:8765 -d @anki/custom-cloze.json
```

## Optional

[`anki-mcp-server/`](anki-mcp-server/) wraps AnkiConnect as an MCP server, if your harness speaks
MCP. A convenience over `curl`; the method never depends on it.

## Turning source files into text

```bash
brew install poppler                  # pdftoppm, pdftotext
brew install --cask libreoffice       # soffice
# textutil is built into macOS
```

Work in a `converted/` folder beside the material, so the originals stay untouched.

**`.doc` / `.docx` / `.rtf`**

```bash
textutil -convert txt -stdout "summary.rtf" > converted/summary.txt
```

**`.ppt` / `.pptx` — to PDF first, then take *both* the text and the images**

```bash
soffice --headless --convert-to pdf --outdir converted "Lecture.ppt"
pdftotext -layout converted/Lecture.pdf converted/slides.txt
mkdir -p converted/slides && pdftoppm -jpeg -r 110 converted/Lecture.pdf converted/slides/slide
```

**Take the speaker notes too — a PDF of slides does not have them.** The notes field is where an
instructor puts what the slide itself does not say, and one lecture's *"I put what I want you to
know about this slide in the note field down here"* was missed for a whole deck because neither
`pdftotext` nor `pdftoppm` can see it:

```bash
soffice --headless --convert-to pptx --outdir converted "Lecture.ppt"
python3 - <<'EOF' > converted/speaker-notes.txt
import zipfile, re, html
z = zipfile.ZipFile("converted/Lecture.pptx")
for name in sorted((n for n in z.namelist() if re.match(r"ppt/notesSlides/notesSlide\d+\.xml$", n)),
                   key=lambda s: int(re.search(r"\d+", s.split("/")[-1]).group())):
    number = int(re.search(r"\d+", name.split("/")[-1]).group())
    body = " ".join(html.unescape(t) for t in
                    re.findall(r"<a:t>(.*?)</a:t>", z.read(name).decode("utf-8", "replace"), re.S))
    body = re.sub(r"\s+", " ", body).replace("<number>", "").strip()
    if len(body) > 12:
        print(f"=== Slide {number} ===\n{body}\n")
EOF
```

**Render the images even when the text extracts cleanly.** A histology deck is mostly
photomicrographs and diagrams, and text baked into a figure is not in the text layer at all — a
62-slide deck can yield barely a thousand words, all of it titles. If `slides.txt` comes out
implausibly short for the page count, that is the normal case, not a failed conversion: the
substance is in the images and in what was said over them. `method/1-extract.md` says to read
those slides visually and to note that automated checks against the text layer will not find them.

**PDFs** need no conversion for text (`pdftotext -layout`), but still want `pdftoppm` for the figures.

## Turning a virtual-slide handout into images

A lab handout is a list of links to slide viewers, not slides. [`tools/`](tools/) converts it: read
the handout and its coordinates, capture fields of view, check the deck. See
[`tools/README.md`](tools/README.md). Standard library only, except:

```bash
# Pillow, for tools/fetch_overlay_slides.py and tools/fetch_unlabeled_slides.py.
# macOS system Python refuses to install into itself (PEP 668), so:
python3 -m venv .venv && .venv/bin/pip install Pillow
```

## Turning a recording into notes

```bash
brew install ffmpeg
uv tool install --python 3.13 mlx-whisper

mlx-whisper --model mlx-community/whisper-large-v3-mlx \
  --condition-on-previous-text False \
  --output-format txt --output-dir converted "Recording.m4a"
```

**Long recordings REQUIRE `--condition-on-previous-text False`**, or large-v3 silently loops a
phrase for minutes and still exits 0. Always check the output:

```bash
sort converted/Recording.txt | uniq -c | sort -rn | head
```
