#!/usr/bin/env python3
"""Render a carousel in the owner's approved reference style.

Usage:
  python3 tools/carousel.py <design_dir> <app|dashboard|website> <out_prefix>
    -> <out_prefix>-1.jpg (cover = the locked single-post mockup), then close-up slides.

Style (from the owner's reference posts): every slide uses the same #EEEEEE background,
close-ups are BIG and bleed off the canvas edges, no labels, no extra text, and the slides
pan across the same design so people swipe through it.
  dashboard -> 3 slides: full window, left half, right half (owner's spec)
  website   -> whole home page in two columns, top of page large, then the whole page rotated 90°
               in consecutive bands through the footer (owner's spec)
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
    # Owner's spec: slide 1 = full screen, slide 2 = left half, slide 3 = right half.
    # The window is scaled to fill the canvas height; each half is cut exactly at the window's midline.
    k = (H - 2 * 64) / fh
    y = (H - fh * k) / 2
    views = [
        (k, W - fw * k / 2, y),        # left half: window midline sits on the canvas right edge
        (k, -fw * k / 2, y),           # right half: window midline sits on the canvas left edge
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
    """Owner's spec (2026-11-09): 1) whole home page in two columns, 2) top of the page large,
    3+) the whole home page rotated 90° in consecutive bands, through to the footer."""
    page = Image.open(work / 'screen.png').convert('RGB')     # 1440 css wide at 1.5x, from R.main
    pw, ph = page.size
    uri = lambda im: 'data:image/png;base64,' + base64.b64encode(_png_bytes(im)).decode()

    # slide 1: left column = page from the top (bleeds off the bottom), right column = page bottom-aligned
    # (ends at the footer), narrower, so together they show the whole home page.
    lw, rw, gap, top = 600, 360, 26, 70
    lx = (W - lw - rw - gap) // 2
    lsc, rsc = lw / pw, rw / pw
    left = page.crop((0, 0, pw, min(ph, round((H - top + 40) / lsc))))
    rh = H - top - 70                           # ends inside the frame so the footer shows
    right = page.crop((0, max(0, ph - round(rh / rsc)), pw, ph))
    html = f"""<!doctype html><html><head><meta charset=utf-8><style>{R.STAGE_CSS}
.col{{position:absolute;top:{top}px;background:#fff;border-radius:6px;overflow:hidden;
box-shadow:0 0 0 1px rgba(0,0,0,.05),0 30px 60px -30px rgba(20,20,30,.3)}}</style></head><body><div class="stage">
<div class="col" style="left:{lx}px;width:{lw}px;height:{H-top+40}px;background:url({uri(left)}) 0 0/100% auto no-repeat"></div>
<div class="col" style="left:{lx+lw+gap}px;width:{rw}px;height:{rh}px;background:url({uri(right)}) 0 100%/100% auto no-repeat"></div>
</div></body></html>"""
    p = work / 'web1.html'
    p.write_text(html)
    await shot_html(b, p, work / 'web1.png', {'width': W, 'height': H}, 2)
    save(Image.open(work / 'web1.png').resize((W, H), Image.LANCZOS), f'{prefix}-1.jpg')

    # slide 2: the top of the page, large, centred
    cw, ctop = 900, 110
    sc = cw / pw
    card_h = H - ctop - 90
    topimg = page.crop((0, 0, pw, round(card_h / sc)))
    html = f"""<!doctype html><html><head><meta charset=utf-8><style>{R.STAGE_CSS}
.col{{position:absolute;background:#fff;border-radius:6px;overflow:hidden;
box-shadow:0 0 0 1px rgba(0,0,0,.05),0 40px 80px -30px rgba(20,20,30,.3)}}</style></head><body><div class="stage">
<div class="col" style="left:{(W-cw)//2}px;top:{ctop}px;width:{cw}px;height:{card_h}px;background:url({uri(topimg)}) 0 0/100% auto no-repeat"></div>
</div></body></html>"""
    p = work / 'web2.html'
    p.write_text(html)
    await shot_html(b, p, work / 'web2.png', {'width': W, 'height': H}, 2)
    save(Image.open(work / 'web2.png').resize((W, H), Image.LANCZOS), f'{prefix}-2.jpg')

    # slides 3..10: whole page rotated 90° counter-clockwise (page top on the left), consecutive bands
    band = H - 2 * 100
    s = band / pw
    rot = page.rotate(90, expand=True).resize((round(ph * s), band), Image.LANCZOS)
    rw_total = rot.size[0]
    # The rotated page sits on a long strip with a 150px margin before its top and after its footer.
    # Split that strip into k equal canvas-wide windows (k = fewest that fit, max 8); any tiny overlap is spread evenly.
    import math
    span = rw_total + 300
    k = min(8, max(1, math.ceil(span / W)))
    step = (span - W) / (k - 1) if k > 1 else 0
    for i in range(k):
        c = Image.new('RGB', (W, H), BG)
        off = round(150 - i * step)                  # where the rotated page's left edge lands on this canvas
        a0 = max(0, -off)
        c.paste(rot.crop((a0, 0, min(rw_total, a0 + W - max(0, off)), band)), (max(0, off), 100))
        save(c, f'{prefix}-{i + 3}.jpg')
    x = rw_total if span <= 8 * W else 0
    if x < rw_total:
        print('WARNING: page longer than 8 rotated slides; shorten the page')


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
