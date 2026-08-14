#!/usr/bin/env python3
"""Render a deck.json as one reviewable HTML page: every card's fronts and backs, in order.

The handover step of method/3-cards.md requires showing the user the cards, not the payload, with
a way to see the *faces* — the hint-fluency test only runs against the front of a card, and that is
the pass that catches a hint the sentence will not read with. This renders exactly that: for each
note, one front per cloze number (that cloze blanked to its [hint], siblings revealed), the backs,
the Source line and the Extra block. Buttons toggle Fronts/Backs/Extras.

Reads the same three payload shapes as check_deck.py. Images in Extra are resolved against the
Anki media dir (override with ANKI_MEDIA) so staged slides render in the browser.

    python3 tools/render_review.py deck.json              # writes review.html beside deck.json
    python3 tools/render_review.py deck.json out.html
"""
import html
import json
import os
import re
import sys

DEFAULT_MEDIA = os.path.expanduser("~/Library/Application Support/Anki2/User 1/collection.media")
if not os.path.isdir(DEFAULT_MEDIA):
    DEFAULT_MEDIA = os.path.expanduser("~/.local/share/Anki2/User 1/collection.media")
MEDIA_DIR = os.environ.get("ANKI_MEDIA", DEFAULT_MEDIA)

CLOZE = re.compile(r"\{\{c(\d+)::((?:(?!\}\})[\s\S])*)\}\}")
IMAGE_SRC = re.compile(r'''(<img\b[^>]*\bsrc=)["']([^"':]+)["']''')


def render(text, blank=None):
    """The card text with cloze `blank` shown as its [hint] and every other cloze revealed."""
    def sub(match):
        number, inner = match.group(1), match.group(2)
        value, separator, hint = inner.partition("::")
        if number == blank:
            return '<span class="blank">[%s]</span>' % (hint if separator else "&hellip;")
        return '<span class="cloze">%s</span>' % value
    return CLOZE.sub(sub, text)


def local_images(markup):
    """Point bare media filenames at the collection so the browser can render them."""
    return IMAGE_SRC.sub(
        lambda m: '%s"file://%s"' % (m.group(1), os.path.join(MEDIA_DIR, m.group(2))), markup)


def main(argv):
    if len(argv) not in (2, 3):
        print("usage: render_review.py deck.json [out.html]", file=sys.stderr)
        return 2
    with open(argv[1]) as handle:
        data = json.load(handle)
    if isinstance(data, dict):
        data = data.get("params", data).get("notes", [])
    out_path = argv[2] if len(argv) == 3 else os.path.join(os.path.dirname(argv[1]) or ".",
                                                           "review.html")
    articles = []
    for position, note in enumerate(data, 1):
        fields = note["fields"]
        text = fields["Text"]
        numbers = sorted({m.group(1) for m in CLOZE.finditer(text)}, key=int)
        fronts = "".join('<div class="face"><span class="cn">c%s</span>%s</div>'
                         % (n, local_images(render(text, n))) for n in numbers)
        backs = '<div class="face">%s</div>' % local_images(render(text))
        extra = fields.get("Extra", "")
        articles.append(
            '<article><div class="idx">%d &middot; %s</div>'
            '<div class="fronts">%s</div><div class="backs">%s</div>'
            '<div class="extra">%s</div></article>'
            % (position, html.escape(fields.get("Source", "")), fronts, backs,
               local_images(extra)))

    deck = html.escape(data[0].get("deck_name", "") if data else "")
    page = """<!doctype html><meta charset="utf-8"><title>%s &mdash; %d notes</title>
<style>:root{color-scheme:dark}
body{font-family:Menlo,ui-monospace,monospace;background:#333B45;color:#D7DEE9;margin:0;padding:24px 16px 80px;line-height:1.55}
.wrap{max-width:900px;margin:0 auto}h1{font-size:20px;margin:0 0 4px}
.sub{color:#839496;font-size:13px;margin-bottom:20px}
article{background:#2c343d;border-radius:8px;padding:14px 16px;margin:0 0 12px}
.idx{color:#6b7883;font-size:11px;margin-bottom:8px}.face{margin:6px 0;font-size:17px}
.cn{color:#6b7883;font-size:11px;margin-right:10px;vertical-align:2px}
b{color:#C695C6}i{color:IndianRed;font-style:normal}u{color:#5EB3B3}
.cloze{font-weight:bold;color:MediumSeaGreen}.blank{color:#E8C07D;font-weight:bold}
.extra{color:#9aa7b4;font-size:13px;border-top:1px solid #3d4753;margin-top:10px;padding-top:8px;display:none}
img{max-width:100%%;border-radius:6px;margin:8px 0}
body.x .extra{display:block}body.f .backs{display:none}body.b .fronts{display:none}
bar{position:fixed;bottom:0;left:0;right:0;background:#252c34;border-top:1px solid #3d4753;padding:10px;display:flex;gap:8px;justify-content:center}
button{background:#3b4654;color:#D7DEE9;border:1px solid #51606e;border-radius:6px;padding:6px 14px;font-family:inherit;font-size:13px;cursor:pointer}
button.on{background:#5EB3B3;color:#1d2329}</style>
<div class="wrap"><h1>%s</h1>
<div class="sub">%d notes &middot; <b>subject</b> &middot; <u>facet</u> &middot; <i>value</i> &middot; <span class="blank">[hint]</span></div>
%s</div>
<bar><button id="bf" class="on">Fronts</button><button id="bb">Backs</button><button id="bx">Extras</button></bar>
<script>const B=document.body;B.className='f';
function m(x){B.classList.remove('f','b');B.classList.add(x);
bf.classList.toggle('on',x==='f');bb.classList.toggle('on',x==='b')}
bf.onclick=()=>m('f');bb.onclick=()=>m('b');
bx.onclick=()=>{bx.classList.toggle('on',B.classList.toggle('x'))};</script>
""" % (deck, len(data), deck, len(data), "\n".join(articles))
    with open(out_path, "w") as handle:
        handle.write(page)
    print(f"wrote {out_path} ({len(data)} notes)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
