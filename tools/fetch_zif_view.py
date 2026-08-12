#!/usr/bin/env python3
"""Render a virtual-slide field of view straight from the server, with no browser.

A histologyguide slide is one `.zif` file — Zoomify Image Format, which is a BigTIFF holding the
whole pyramid: one IFD per resolution tier, each tier stored as JPEG tiles. The viewer never
downloads it; it pulls the tiles it needs with HTTP range requests. So can we, and then a field of
view is arithmetic rather than a screenshot: no blank tiles, no settle timers, no clamped zoom, and
the same coordinates give the same image every time.

    python3 tools/fetch_zif_view.py views.json -o shots

`views.json` is a list of views, each `{name, slide, x, y, z, w, h}`:

    [{"name": "ner-01.jpg", "slide": "UCSF-163-spinal-cord",
      "x": 12976, "y": 9802, "z": 3.433, "w": 940, "h": 940}]

`x`, `y` are full-resolution image pixels and `z` is a **percentage**, exactly as the site writes
them into a slideview URL and into `annotations.xml` — paste the numbers across unchanged. `w`, `h`
are the output size in pixels; the field of view they cover is `w/(z/100)` by `h/(z/100)` of the
original image. Tiles come from the smallest tier that still has more detail than the output needs,
so the result is downsampled rather than blown up.

Needs Pillow: `python3 -m venv .venv && .venv/bin/pip install Pillow`.
"""
import http.client
import io
import json
import os
import struct
import sys
import time
import urllib.parse

from PIL import Image

SLIDE_URL = "https://histologyguide.org/slides/{slide}.zif"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"

TAG_IMAGE_WIDTH, TAG_IMAGE_LENGTH = 256, 257
TAG_TILE_WIDTH, TAG_TILE_LENGTH = 322, 323
TAG_TILE_OFFSETS, TAG_TILE_BYTE_COUNTS = 324, 325
TAG_JPEG_TABLES = 347

# BigTIFF field types, as (struct code, byte width). Only the ones a ZIF actually uses.
FIELD_TYPES = {1: ("B", 1), 2: ("c", 1), 3: ("H", 2), 4: ("I", 4), 7: ("B", 1),
               16: ("Q", 8), 17: ("q", 8), 18: ("Q", 8)}


class RangeReader:
    """Byte-range reads against one remote file, over a connection kept open between reads.

    A tier's tiles are stored consecutively, so `prefetch` pulls everything one field of view
    needs in a single range request; without it a 6x5 field is thirty round trips and the server
    starts resetting the connection.
    """

    MAX_PREFETCH = 32 << 20         # one range request per field, but never a runaway one

    def __init__(self, url):
        parts = urllib.parse.urlsplit(url)
        self.host = parts.netloc
        self.path = parts.path + (f"?{parts.query}" if parts.query else "")
        self.chunks = []            # [(start, bytes)] — few and large, so a linear scan is fine
        self.connection = None

    def _fetch(self, start, length):
        for attempt in range(4):
            try:
                if self.connection is None:
                    self.connection = http.client.HTTPSConnection(self.host, timeout=30)
                self.connection.request("GET", self.path, headers={
                    "Range": f"bytes={start}-{start + length - 1}",
                    "User-Agent": USER_AGENT, "Connection": "keep-alive"})
                response = self.connection.getresponse()
                data = response.read()
                if response.status not in (200, 206):
                    raise OSError(f"HTTP {response.status} on bytes {start}+{length}")
                return data
            except (OSError, http.client.HTTPException) as error:
                if self.connection:
                    self.connection.close()
                self.connection = None
                if attempt == 3:
                    raise SystemExit(f"range read failed at {start}+{length}: {error}")
                time.sleep(1 + attempt)

    def prefetch(self, start, end):
        if end - start <= self.MAX_PREFETCH:
            self.chunks.append((start, self._fetch(start, end - start)))

    def read(self, start, length):
        for chunk_start, chunk in self.chunks:
            if chunk_start <= start and start + length <= chunk_start + len(chunk):
                offset = start - chunk_start
                return chunk[offset:offset + length]
        data = self._fetch(start, length)
        self.chunks.append((start, data))
        return data[:length]

    def forget(self):
        """Drop cached bytes between fields; the pyramid metadata is re-read on demand."""
        self.chunks = []


def read_ifd(reader, offset):
    """One BigTIFF IFD -> ({tag: values}, offset of the next IFD)."""
    entry_count = struct.unpack("<Q", reader.read(offset, 8))[0]
    block = reader.read(offset + 8, entry_count * 20 + 8)
    tags = {}
    for i in range(entry_count):
        tag, field_type, count = struct.unpack_from("<HHQ", block, i * 20)
        payload = block[i * 20 + 12:i * 20 + 20]
        if field_type not in FIELD_TYPES:
            continue
        code, width = FIELD_TYPES[field_type]
        total = count * width
        raw = payload[:total] if total <= 8 else reader.read(
            struct.unpack("<Q", payload)[0], total)
        tags[tag] = (raw if field_type in (2, 7)
                     else list(struct.unpack("<" + code * count, raw)))
    next_offset = struct.unpack_from("<Q", block, entry_count * 20)[0]
    return tags, next_offset


def read_tiers(reader):
    """Every resolution tier in the file, largest first."""
    signature, version, offset_size, zero = struct.unpack("<2sHHH", reader.read(0, 8))
    if signature != b"II" or version != 43 or offset_size != 8 or zero != 0:
        raise SystemExit(f"not a little-endian BigTIFF: {signature!r} v{version}")
    offset = struct.unpack("<Q", reader.read(8, 8))[0]

    tiers = []
    while offset:
        tags, offset = read_ifd(reader, offset)
        if TAG_TILE_OFFSETS not in tags:                 # a thumbnail or metadata IFD
            continue
        tiers.append({
            "width": tags[TAG_IMAGE_WIDTH][0],
            "height": tags[TAG_IMAGE_LENGTH][0],
            "tile_width": tags[TAG_TILE_WIDTH][0],
            "tile_height": tags[TAG_TILE_LENGTH][0],
            "offsets": tags[TAG_TILE_OFFSETS],
            "byte_counts": tags[TAG_TILE_BYTE_COUNTS],
            "jpeg_tables": tags.get(TAG_JPEG_TABLES, b""),
        })
    return sorted(tiers, key=lambda tier: -tier["width"])


def decode_tile(reader, tier, index):
    """One JPEG tile. The tables live once per tier, so each tile needs them spliced back in."""
    length = tier["byte_counts"][index]
    if not length:
        return None
    data = reader.read(tier["offsets"][index], length)
    tables = tier["jpeg_tables"]
    if tables:
        # Tables end with EOI and the tile starts with SOI; drop both so the result is one stream.
        data = bytes(tables[:-2]) + data[2:]
    return Image.open(io.BytesIO(data)).convert("RGB")


def render(reader, tiers, x, y, zoom_percent, width, height):
    scale = zoom_percent / 100.0
    full_width = tiers[0]["width"]

    # The smallest tier that still holds at least as much detail as the output asks for.
    tier = next((t for t in reversed(tiers) if t["width"] / full_width >= scale), tiers[0])
    tier_scale = tier["width"] / full_width

    # The requested field of view, in this tier's pixels.
    region_width = width / scale * tier_scale
    region_height = height / scale * tier_scale
    left = x * tier_scale - region_width / 2
    top = y * tier_scale - region_height / 2

    tile_width, tile_height = tier["tile_width"], tier["tile_height"]
    columns = -(-tier["width"] // tile_width)
    first_column, last_column = int(left // tile_width), int((left + region_width) // tile_width)
    first_row, last_row = int(top // tile_height), int((top + region_height) // tile_height)

    rows = -(-tier["height"] // tile_height)
    wanted = [(row, column, row * columns + column)
              for row in range(first_row, last_row + 1)
              for column in range(first_column, last_column + 1)
              if 0 <= row < rows and 0 <= column < columns]

    # These tiles sit next to each other in the file, so ask for the whole span at once.
    spans = [(tier["offsets"][i], tier["offsets"][i] + tier["byte_counts"][i])
             for _, _, i in wanted if tier["byte_counts"][i]]
    if spans:
        reader.prefetch(min(s for s, _ in spans), max(e for _, e in spans))

    canvas = Image.new("RGB", ((last_column - first_column + 1) * tile_width,
                               (last_row - first_row + 1) * tile_height), "white")
    for row, column, index in wanted:
        tile = decode_tile(reader, tier, index)
        if tile:
            canvas.paste(tile, ((column - first_column) * tile_width,
                                (row - first_row) * tile_height))
    reader.forget()

    crop_left = left - first_column * tile_width
    crop_top = top - first_row * tile_height
    field = canvas.crop((round(crop_left), round(crop_top),
                         round(crop_left + region_width), round(crop_top + region_height)))
    return field.resize((width, height), Image.LANCZOS)


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("-")]
    output_dir = "shots"
    if "-o" in argv:
        output_dir = argv[argv.index("-o") + 1]
        args = [a for a in args if a != output_dir]
    if len(args) != 1:
        print("usage: fetch_zif_view.py views.json [-o output_dir]", file=sys.stderr)
        return 2
    os.makedirs(output_dir, exist_ok=True)

    with open(args[0]) as handle:
        views = json.load(handle)

    readers, pyramids = {}, {}
    for view in views:
        slide = view["slide"]
        if slide not in readers:
            readers[slide] = RangeReader(view.get("url", SLIDE_URL.format(slide=slide)))
            pyramids[slide] = read_tiers(readers[slide])
            top_tier = pyramids[slide][0]
            print(f"{slide}: {top_tier['width']}x{top_tier['height']}, "
                  f"{len(pyramids[slide])} tiers", flush=True)
        image = render(readers[slide], pyramids[slide], view["x"], view["y"],
                       view["z"], view["w"], view["h"])
        path = os.path.join(output_dir, view["name"])
        image.save(path, quality=88)
        print(f"  {view['name']}  {os.path.getsize(path) // 1024} KB", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
