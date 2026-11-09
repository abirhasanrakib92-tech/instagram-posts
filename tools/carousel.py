#!/usr/bin/env python3
"""Render a carousel in the owner's approved reference style.

Usage:
  python3 tools/carousel.py <design_dir> <app|dashboard|website> <out_prefix>
    -> <out_prefix>-1.jpg (cover = the locked single-post mockup), then close-up slides.

Style (from the owner's reference posts): every slide uses the same #EEEEEE background,
close-ups are BIG and bleed off the canvas edges, no labels, no extra text, and the slides
pan across the same design so people swipe through it.
  dashboard -> 4 slides: full window, zoom top-left, zoom top-right, zoom bottom
  website   -> 6 slides: two-card overview, top section zoom, then the long page rotated 90°
               in consecutive bands (page top on the left), bleeding off both sides
  app       -> 4 slides: hand+phone cover, then close-ups into the top, middle and bottom of the phone
"""
import asyncio, sys, pathlib, base64
from PIL import Image
from playwright.async_api import async_playwright
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import render as R

W, H = R.W, R.H
BG = (238, 238, 238)


def save(img, out):
    img.convert('RGB').save(out, quality=95)
    print('wrote', out)


async def shot_html(browser, html_path, png, vp, dsf, full=False):
    pg = await browser.new_page(viewport=vp, device_scale_factor=dsf)
    await R.shoot(pg, html_path.as_uri(), png, full=full)
    h = await pg.evaluate('document.documentElement.scrollHeight')
    await pg.close()
    return h


def window_html(shot_uri, url, k, x, y):
    """The dashboard browser window (same look as the cover) scaled by k and placed at x,y."""
    iw = 952
    ih = round(960 * iw / 1440) + 38
    return f"""<!doctype html><html><head><meta charset=utf-8><link rel=stylesheet href="{(R.ROOT/'assets/fonts.css').as_uri()}"><style>{R.STAGE_CSS}
.zoomw{{position:absolute;left:0;top:0;transform-origin:0 0;transform:translate({x}px,{y}px) scale({k})}}</style></head>
<body><div class="stage"><div class="zoomw"><div class="frame" style="position:relative"><div class="inner" style="width:{iw}px">
 <div class="bar"><div class="dots"><i style="background:#FF5F57"></i><i style="background:#FEBC2E"></i><i style="background:#28C840"></i></div>
 <div class="url"><span>{R.LOCK}{url}</span></div><div class="side">{R.BAR_ICONS}</div></div>
 <img class="shot" src="{shot_uri}" style="height:{ih-38}px">
</div></div></div></div></body></html>""", iw + 14, ih + 14


async def dashboard(d, work, prefix, b):
    rendered = d / 'screen.rendered.html'
    rendered.write_text(R.expand_icons((d / 'screen.html').read_text()))
    png = work / 'screen3x.png'
    await shot_html(b, rendered, png, {'width': 1440, 'height': 960}, 3)
    rendered.unlink()
    import re
    m = re.search(r'name="mock-url" content="([^"]+)"', (d / 'screen.html').read_text())
    url = m.group(1) if m else 'app.example.com'
    uri = R.b64(png)
    _, fw, fh = window_html(uri, url, 1, 0, 0)
    views = [
        (1.9, 64, 150),                                   # top-left: logo, nav, KPIs, chart start
        (1.9, W - 64 - fw * 1.9, 150),                    # top-right: KPIs, side cards
        (2.7, -fw * 2.7 * 0.33, H - 110 - fh * 2.7),      # deep zoom on the lower cards, bleeding on three sides
    ]
    n = 2
    for k, x, y in views:
        html, _, _ = window_html(uri, url, k, round(x), round(y))
        p = work / f'zoom{n}.html'
        p.write_text(html)
        await shot_html(b, p, work / f'zoom{n}.png', {'width': W, 'height': H}, 2)
        save(Image.open(work / f'zoom{n}.png').resize((W, H), Image.LANCZOS), f'{prefix}-{n}.jpg')
        n += 1


async def website(d, work, prefix, b):
    page = Image.open(work / 'screen.png').convert('RGB')     # 1440 css wide at 1.5x, from the cover render
    pw, ph = page.size
    # slide 2: the top of the page, large, in one card (like the reference's second slide)
    cw = 900
    sc = cw / pw
    card_h = H - 150 - 60
    top = page.crop((0, 0, pw, round(card_h / sc)))
    html = f"""<!doctype html><html><head><meta charset=utf-8><style>{R.STAGE_CSS}</style></head><body><div class="stage">
<div class="frame" style="left:{(W-cw-14)//2}px;top:150px;border-radius:24px"><div class="inner" style="width:{cw}px;height:{card_h}px;border-radius:17px;
background:url({'data:image/png;base64,' + base64.b64encode(_png_bytes(top)).decode()}) 0 0/100% auto no-repeat"></div></div></div></body></html>"""
    p = work / 'web2.html'
    p.write_text(html)
    await shot_html(b, p, work / 'web2.png', {'width': W, 'height': H}, 2)
    save(Image.open(work / 'web2.png').resize((W, H), Image.LANCZOS), f'{prefix}-2.jpg')
    # slides 3..6: page rotated 90° counter-clockwise (page top on the left), consecutive bands
    band = H - 2 * 96                       # rotated page height on canvas (= page width)
    s = band / pw
    rot = page.rotate(90, expand=True).resize((round(ph * s), band), Image.LANCZOS)
    # rot: x = page y (top at left), y = page x (left edge at bottom)
    seg = W - 70                             # each slide advances by this much; the next slide starts where this one bleeds off
    x = 0
    for n in range(3, 7):
        if x >= rot.size[0] - 200:
            break
        c = Image.new('RGB', (W, H), BG)
        start_x = 70 if n == 3 else 0        # first rotated slide shows a small margin on the left, like the reference
        piece = rot.crop((x, 0, min(x + W - start_x, rot.size[0]), band))
        c.paste(piece, (start_x, 96))
        save(c, f'{prefix}-{n}.jpg')
        x += W - start_x - 0
    return


def _png_bytes(img):
    import io
    bio = io.BytesIO()
    img.save(bio, 'PNG')
    return bio.getvalue()


async def app(d, work, prefix, b):
    scale = 2.4
    big = work / 'app-big.png'
    R.compose_app(work / 'screen.png', big, scale=scale)
    im = Image.open(big)
    bw, bh = im.size
    # phone screen centre on the big image (from compose_app geometry)
    s = W * scale / 957
    sx0, sy0, sw, sh = (538 - 255) * s, 43 * s, 392 * s, 853 * s
    cx = sx0 + sw / 2
    for n, fy in [(2, 0.05), (3, 0.38), (4, 0.70)]:
        top = sy0 + sh * fy - 120
        left = cx - W / 2
        top = max(0, min(bh - H, top))
        left = max(0, min(bw - W, left))
        save(im.crop((round(left), round(top), round(left) + W, round(top) + H)), f'{prefix}-{n}.jpg')


async def main(design_dir, kind, prefix):
    d = pathlib.Path(design_dir).resolve()
    prefix = str(pathlib.Path(prefix).resolve())
    await R.main(design_dir, kind, prefix + '-1.jpg')      # cover = locked single-post format
    work = R.ROOT / '.render' / d.name
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=R.CHROME)
        await {'dashboard': dashboard, 'website': website, 'app': app}[kind](d, work, prefix, b)
        await b.close()


if __name__ == '__main__':
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    asyncio.run(main(*sys.argv[1:]))
