// Capture Zoomify virtual-slide fields of view to files, one page load per run.
//
// Paste into the page's console (or run via a browser tool) after navigating to the FIRST view by
// URL: .../05-slide-1.html?x=<X>&y=<Y>&z=<ZOOM>   ← z here is a PERCENTAGE, as the site writes it.
//
// Edit VIEWS and NEXT_SLIDE below. VIEWS[0] is the view already on screen, so its coordinates are
// ignored; every later entry is reached with zoomAndPanToView, whose zoom is a 0–1 FRACTION
// (75.567% -> 0.75567). Passing the percentage silently clamps to 1 and yields a blurry
// wrong-tier image rather than an error.
//
// Start the receiver first:  python3 tools/capture_server.py shots 8799

(async () => {
  const CAPTURE_SERVER = 'http://127.0.0.1:8799/';

  const VIEWS = [
    // [filename,                    x,         y,         zoomFraction, width, height]
    ['cart-01-wide.jpg',             57100,     18712,     0.029,        1040,  780],
    ['cart-02-perichondrium.jpg',    68229.898, 5942.152,  0.50,          860,  860],
  ];
  // Set to '' to stop here; otherwise the page navigates on, so the next run starts on a fresh load.
  const NEXT_SLIDE = 'https://histologyguide.org/slideview/MH-110-trachea-and-esophagus/17-slide-1.html?x=21490&y=22963&z=2.0';

  const SETTLE_MS = 6500;        // after a pan, before the first read
  const RETRY_MS = 3500;         // between redraws while the image is still blank
  const MIN_DATAURL_CHARS = 40000;  // base64 chars, not bytes: a blank tier is under 7 K

  // Composite every tile canvas in the viewport, cropped to the centre of the viewer.
  function drawViewport(width, height) {
    const tiles = [...document.querySelectorAll('canvas')].filter(
      canvas => canvas.parentElement.id === 'viewportContainer0' &&
                canvas.width > 400 && canvas.getBoundingClientRect().width > 400);
    const viewer = document.getElementById('ViewerDisplay').getBoundingClientRect();

    const output = document.createElement('canvas');
    output.width = width;
    output.height = height;
    const context = output.getContext('2d');
    context.fillStyle = '#fff';
    context.fillRect(0, 0, width, height);

    const cropLeft = viewer.x + viewer.width / 2 - width / 2;
    const cropTop = viewer.y + viewer.height / 2 - height / 2;
    for (const tile of tiles) {
      const box = tile.getBoundingClientRect();
      const scale = tile.width / box.width;   // backing pixels per CSS pixel
      context.drawImage(tile,
        (cropLeft - box.x) * scale, (cropTop - box.y) * scale, width * scale, height * scale,
        0, 0, width, height);
    }
    // The tiles arrive as data: URIs, so the canvas is never tainted and this always succeeds.
    return output.toDataURL('image/jpeg', 0.86);
  }

  async function captureTo(filename, width, height) {
    let dataUrl = drawViewport(width, height);
    for (let attempt = 0; attempt < 4 && dataUrl.length < MIN_DATAURL_CHARS; attempt++) {
      await new Promise(done => setTimeout(done, RETRY_MS));
      dataUrl = drawViewport(width, height);
    }
    const response = await fetch(CAPTURE_SERVER, {
      method: 'POST',
      headers: { 'Content-Type': 'text/plain' },   // simple request: no CORS preflight
      body: JSON.stringify({ name: filename, dataurl: dataUrl }),
    });
    return await response.text();
  }

  // Wait for the viewer to exist, then for its first tiles.
  for (let i = 0; i < 50 && !(window.Z && Z.Viewport && Z.Viewport.getZoom); i++) {
    await new Promise(done => setTimeout(done, 200));
  }
  await new Promise(done => setTimeout(done, 3000));

  const results = [];
  for (let i = 0; i < VIEWS.length; i++) {
    const [filename, x, y, zoomFraction, width, height] = VIEWS[i];
    if (i > 0) {                                   // VIEWS[0] arrived via the URL already
      Z.Viewport.zoomAndPanToView(x, y, zoomFraction);
      await new Promise(done => setTimeout(done, SETTLE_MS));
    }
    results.push(await captureTo(filename, width, height));
  }
  if (NEXT_SLIDE) location.href = NEXT_SLIDE;
  return JSON.stringify(results);
})();
