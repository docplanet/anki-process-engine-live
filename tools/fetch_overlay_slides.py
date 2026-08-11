#!/usr/bin/env python3
"""Composite slides that ship one pointer overlay per labelled structure.

Some slide collections are already pointer flashcards: an unlabeled base photomicrograph, plus a
transparent PNG per structure that draws an arrow or circle onto it, plus that structure's name.
Compositing base + overlay gives a card front asking "what is marked?", and the site's own label is
the answer — so neither the pointer nor the answer has to be invented.

Written for digitalhistology.org (VCU), whose pages carry one `subcontent-N` div per structure,
each holding the base image, its overlay, the name, and a caption.

    python3 tools/fetch_overlay_slides.py targets.json
    # targets.json: [["https://digitalhistology.org/.../hyaline-6/", "hyaline6"], ...]
    # writes <slug>_base.jpg and <slug>_pNN.jpg into $SLIDE_OUT (default ./shots)
"""
import html as html_module
import io
import json
import os
import re
import sys
import urllib.request

from PIL import Image

USER_AGENT = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                            "AppleWebKit/537.36 Chrome/120 Safari/537.36"}
OUTPUT_DIR = os.environ.get("SLIDE_OUT", "shots")
MAX_WIDTH = 1400
# Navigation controls share the markup of real structures; they are not answers.
NAVIGATION = re.compile(r"^(main slide|next image|previous image|image credit|back|return)\b", re.I)
SUBCONTENT_BLOCK = re.compile(
    r'<div id="subcontent-(\d+)"[^>]*background-image:\s*url\(([^)]+)\)[^>]*>'
    r'(.*?)(?=<div id="subcontent-|<!--SLIDE NAVIGATION)', re.S)

os.makedirs(OUTPUT_DIR, exist_ok=True)
_downloads = {}


def fetch(url, binary=False):
    """Fetch with a small cache — every structure on a page cites the same base image."""
    if url not in _downloads:
        request = urllib.request.Request(url, headers=USER_AGENT)
        _downloads[url] = urllib.request.urlopen(request, timeout=30).read()
    return _downloads[url] if binary else _downloads[url].decode("utf-8", "replace")


def tidy(markup):
    """Strip tags and entities from a label, and the ">" these pages use to mean "expand"."""
    text = html_module.unescape(markup or "").replace("&gt;", "").strip()
    return re.sub(r"\s+", " ", text).strip(" -–>")


def scrape(page_url, slug):
    page = fetch(page_url)
    blocks = SUBCONTENT_BLOCK.findall(page)
    if not blocks:
        return {"url": page_url, "slug": slug, "error": "no subcontent blocks found"}

    items, base_images, parent_label = [], {}, None
    for index, base_url, block in blocks:
        overlay = re.search(r'<img[^>]*id="overlay-\d+"[^>]*src="([^"]+)"', block)
        title = re.search(r'<h3 class="slide-title[^"]*">(.*?)</h3>', block, re.S)
        caption = re.search(r'<span class="sub-deep">(.*?)</span>', block, re.S)
        heading = tidy(re.sub(r"<[^>]+>", " ", title.group(1))) if title else ""
        caption = tidy(re.sub(r"<[^>]+>", " ", caption.group(1))) if caption else ""
        if not heading or NAVIGATION.match(heading):
            continue

        # "Fibrocartilage >" followed by " - Chondrocytes" is a parent heading and its sub-item,
        # so the sub-item alone ("Chondrocytes") would lose which tissue it belongs to.
        # Test the de-tagged text: tidy() has already stripped leading hyphens from `heading`,
        # and the raw markup may open with a tag rather than the hyphen.
        raw_heading = html_module.unescape(
            re.sub(r"<[^>]+>", " ", title.group(1))).strip() if title else ""
        if raw_heading.startswith(("-", "–")):
            label = f"{parent_label}: {tidy(heading)}" if parent_label else tidy(heading)
        else:
            parent_label = label = tidy(heading)

        base_url = base_url.strip().strip("'\"")
        if base_url not in base_images:
            base = Image.open(io.BytesIO(fetch(base_url, binary=True))).convert("RGBA")
            if base.width > MAX_WIDTH:
                base = base.resize((MAX_WIDTH, round(base.height * MAX_WIDTH / base.width)), Image.LANCZOS)
            base_images[base_url] = base
            filename = f"{slug}_base.jpg"
            base.convert("RGB").save(os.path.join(OUTPUT_DIR, filename), quality=88)
            items.append({"kind": "wide", "label": None, "file": filename, "caption": caption})
        base = base_images[base_url]

        if not overlay:
            continue
        try:
            pointer = Image.open(io.BytesIO(fetch(overlay.group(1), binary=True)))
            pointer = pointer.convert("RGBA").resize(base.size, Image.LANCZOS)
        except Exception as error:
            items.append({"kind": "pointer", "label": label, "error": repr(error)})
            continue

        composited = base.copy()
        composited.alpha_composite(pointer)
        filename = f"{slug}_p{int(index):02d}.jpg"
        composited.convert("RGB").save(os.path.join(OUTPUT_DIR, filename), quality=88)
        items.append({"kind": "pointer", "label": label, "file": filename, "caption": caption})

    size = list(next(iter(base_images.values())).size) if base_images else None
    return {"url": page_url, "slug": slug, "size": size, "items": items}


if __name__ == "__main__":
    targets = json.load(open(sys.argv[1]))          # [[page_url, slug], ...]
    print(json.dumps([scrape(url, slug) for url, slug in targets], indent=1))
