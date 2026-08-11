#!/usr/bin/env python3
"""Download the unlabeled base image from slides that keep their labels in a separate layer.

Some slide collections publish two images per slide: the photomicrograph itself, and a transparent
overlay carrying the labels, toggled by a "hide labels" control. That is exactly what a recognition
card needs — the base image is already an unlabeled question, and the page's own slide title is the
answer, so neither has to be invented.

Written for medcell.org (Histology@Yale), whose pages expose `images/<slug>.jpg` alongside
`images/<slug>_labels.png`.

    python3 tools/fetch_unlabeled_slides.py <lab_path> <slug> [<slug> ...] [-o DIR] [-p PREFIX]
    python3 tools/fetch_unlabeled_slides.py blood_bone_marrow_lab erythrocytes neutrophil -o shots
"""
import argparse
import io
import json
import os
import re
import urllib.error
import urllib.request

from PIL import Image

USER_AGENT = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                            "AppleWebKit/537.36 Chrome/120 Safari/537.36"}
SITE = "https://medcell.org/histology/"
MAX_WIDTH = 1200


def fetch(url, binary=False):
    try:
        data = urllib.request.urlopen(urllib.request.Request(url, headers=USER_AGENT), timeout=40).read()
    except urllib.error.HTTPError as error:
        raise SystemExit(f"{error.code} fetching {url} — check the lab path and slug")
    except urllib.error.URLError as error:
        raise SystemExit(f"could not reach {url}: {error.reason}")
    return data if binary else data.decode("utf-8", "replace")


def fetch_slide(base_url, slug, index, output_dir, prefix):
    page = fetch(f"{base_url}{slug}.php")

    def require(pattern, what):
        match = re.search(pattern, page, re.S)
        if not match:
            raise SystemExit(f"{slug}: no {what} on the page — has the site's markup changed?")
        return match.group(1)

    title = require(r'<div class="slide-title">(.*?)</div>', "slide title").strip()
    description = re.search(r'<span itemprop="description">(.*?)</span>', page, re.S)
    description = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", description.group(1))).strip() if description else ""

    image_path = require(r'<div id="slide-image">\s*<img src="([^"]+)"', "base image")
    # Not an assert: this vanishes under `python -O`, and grabbing the label overlay would put
    # the answer onto the question.
    if "_labels" in image_path:
        raise SystemExit(f"{slug}: matched the label overlay, not the base image")

    image = Image.open(io.BytesIO(fetch(base_url + image_path, binary=True))).convert("RGB")
    if image.width > MAX_WIDTH:
        image = image.resize((MAX_WIDTH, round(image.height * MAX_WIDTH / image.width)), Image.LANCZOS)

    filename = os.path.basename(f"{prefix}-{index:02d}-{slug.replace(chr(95), chr(45))}.jpg")
    image.save(os.path.join(output_dir, filename), quality=90)
    return {"slug": slug, "title": title, "file": filename, "size": image.size, "description": description}


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("lab", help='lab path, e.g. "blood_bone_marrow_lab"')
    parser.add_argument("slugs", nargs="+", help="page slugs, e.g. erythrocytes neutrophil")
    parser.add_argument("-o", "--out", default="shots", help="output directory")
    parser.add_argument("-p", "--prefix", default="slide", help="filename prefix")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)
    base_url = f"{SITE}{args.lab}/"

    slides = []
    for index, slug in enumerate(args.slugs, 1):
        slide = fetch_slide(base_url, slug, index, args.out, args.prefix)
        slides.append(slide)
        print(f"{slide['file']:38s} {str(slide['size']):12s} {slide['title']}")

    manifest = os.path.join(args.out, f"{args.prefix}_manifest.json")
    json.dump(slides, open(manifest, "w"), indent=1)
    print(f"\n{len(slides)} slides -> {manifest}")


if __name__ == "__main__":
    main()
