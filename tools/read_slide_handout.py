#!/usr/bin/env python3
"""Read a lab handout (.docx of virtual-slide links) and print what is in it.

For every link it recovers the section heading and caption it sits under, the instructor's own
field of view if the URL carries one, and — for histologyguide.org — the slide's own named points
of interest with exact coordinates, straight from `annotations.xml`.

That POI list is the useful part: it names each structure *and* gives the x/y/zoom that frames it,
so the field of view on a card is the site's own, not a guess.

    python3 tools/read_slide_handout.py "path/to/Lab Handout.docx" [-o slides.json]
"""
import argparse
import json
import re
import urllib.request
import zipfile
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36"}


def docx_lines(path):
    """Paragraph text, with hyperlinks rendered as [label](target) so nothing is lost."""
    z = zipfile.ZipFile(path)
    rels = {r.get("Id"): r.get("Target")
            for r in ET.fromstring(z.read("word/_rels/document.xml.rels"))}
    body = ET.fromstring(z.read("word/document.xml")).find(W + "body")
    for par in body.iter(W + "p"):
        buf, seen = "", set()
        # iter(), not direct children: a run inside <w:ins>/<w:del>/<w:smartTag> (tracked changes,
        # content controls) is nested, and walking only children drops it without a word.
        for node in par.iter():
            if node.tag == W + "hyperlink":
                txt = "".join(t.text or "" for t in node.iter(W + "t"))
                buf += f"[{txt}]({rels.get(node.get(R + 'id'), '')})"
                seen.update(id(t) for t in node.iter(W + "t"))
            elif node.tag == W + "t" and id(node) not in seen:
                buf += node.text or ""
        yield buf


def parse(path):
    """A URL inherits the nearest short line above it as its caption and the nearest
    numbered heading as its section — which is how the handout groups slides by tissue."""
    out, section, caption = [], None, None
    for raw in docx_lines(path):
        line = raw.strip()
        if not line:
            continue
        m = re.match(r"^(\d+)\.\s*(.+?):?\s*$", line)
        if m and len(line) < 80 and "http" not in line:
            section, caption = m.group(2).strip().rstrip(":"), None
            continue
        urls = re.findall(r"https?://[^\s\)\]]+", line)
        if urls:
            for u in urls:
                u = u.rstrip(".,")
                if u.startswith("https://commons.wikimedia.org/wiki/File:"):
                    continue                                   # attribution page, not the image
                if re.match(r"^https?://[^/]+/[A-Za-z]+$", u):
                    continue                                   # fragment of an unencoded-space URL
                out.append({"section": section, "caption": caption, "url": u})
            caption = None
        else:
            caption = line if (len(line) < 120 and not line.endswith(".")) else None
    return out


def fetch(url):
    try:
        response = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25)
        return response.read().decode("utf-8", "replace")
    except Exception:
        return None


def points_of_interest(url):
    """histologyguide ships <slide-path>/annotations.xml — named structures at exact x/y/zoom."""
    m = re.match(r"https://histologyguide\.org/(slideview|EM-view)/([^/]+)/([^.]+)\.html", url)
    if not m:
        return None, None
    stem = f"https://histologyguide.org/{m.group(1)}/{m.group(2)}/{m.group(3)}"
    xml = fetch(stem + "/annotations.xml") or ""
    found = []
    for tag in re.findall(r"<POI\b[^>]*>", xml):
        def attr(name, tag=tag):
            match = re.search(r"\b" + name + r'="([^"]*)"', tag)   # \b: NAME must not match FILENAME
            return match.group(1) if match else None
        name = attr("NAME")
        if name and name not in ("Whole Slide", "Whole Micrograph"):
            found.append({"name": name, "x": attr("X") or "?", "y": attr("Y") or "?",
                          "zoom": attr("ZOOM") or "?"})
    page = fetch(url.split("?")[0]) or ""
    title = re.search(r"<title>(.*?)</title>", page, re.S)
    return found, (re.sub(r"\s+", " ", title.group(1)).strip() if title else None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("docx")
    parser.add_argument("-o", "--out", help="also write the rows as JSON")
    args = parser.parse_args()

    rows = []
    for slide in parse(args.docx):
        coords = re.search(r"[?&]x=([\d.]+).*?[?&]y=([\d.]+).*?[?&]z=([\d.]+)", slide["url"])
        slide["instructor_view"] = (
            {"x": coords.group(1), "y": coords.group(2), "z": coords.group(3)} if coords else None)
        slide["pois"], slide["title"] = points_of_interest(slide["url"])
        rows.append(slide)
        print(f"\n## {slide['section']} | {slide['caption']}")
        print(f"   {slide['url']}")
        print(f"   view: {slide['instructor_view']}   title: {slide['title']}")
        for poi in slide["pois"] or []:
            print(f"      {poi['name']:44s} x={poi['x']:>12} y={poi['y']:>12} z={poi['zoom']}")

    total_pois = sum(len(slide["pois"] or []) for slide in rows)
    print(f"\n{len(rows)} links, {total_pois} named structures")
    if args.out:
        json.dump(rows, open(args.out, "w"), indent=1)
        print(f"-> {args.out}")


if __name__ == "__main__":
    main()
