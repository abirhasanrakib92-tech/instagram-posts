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
  app       -> 5 slides: hand+phone cover, description + nav bar, typography, colors, CTA (owner's spec)
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


SLIDE_CSS = """*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1350px;overflow:hidden;background:#EEEEEE;color:#111114;-webkit-font-smoothing:antialiased}
.s{position:relative;width:1080px;height:1350px;padding:84px 80px}
.head{display:flex;justify-content:space-between;font:500 22px 'Inter Tight';letter-spacing:.6px;text-transform:uppercase;color:#111114}
"""


def _meta(html, name):
    import re
    m = re.search(rf'<meta name="{name}" content="([^"]*)"', html)
    return m.group(1) if m else ''


async def _slide(b, work, name, body, extra_css=''):
    p = work / f'{name}.html'
    p.write_text(f"""<!doctype html><html><head><meta charset=utf-8><link rel=stylesheet href="{(R.ROOT/'assets/fonts.css').as_uri()}">
<style>{SLIDE_CSS}{extra_css}</style></head><body><div class="s">{body}</div></body></html>""")
    png = work / f'{name}.png'
    await shot_html(b, p, png, {'width': W, 'height': H}, 2)
    return Image.open(png).resize((W, H), Image.LANCZOS)


async def cta_slide(b, work):
    body = """
<div class="head"><span>Abir Hasan Rakib</span><span>UI/UX Designer</span></div>
<div style="position:absolute;left:80px;right:80px;top:230px">
 <div style="font:600 30px 'Inter Tight';color:#6B6B74;letter-spacing:-.3px">Have a product in mind?</div>
 <div style="font:600 148px/0.95 'Inter Tight';letter-spacing:-6px;margin-top:22px">Open for<br>new <span style="color:#3D5AFE">projects</span></div>
 <div style="display:flex;gap:12px;margin-top:46px;flex-wrap:wrap">
  <span class="chip">Mobile Apps</span><span class="chip">Dashboards</span><span class="chip">Websites</span><span class="chip">Landing Pages</span>
 </div>
</div>
<div style="position:absolute;left:80px;right:80px;bottom:84px;display:flex;flex-direction:column;gap:14px">
 <div class="row"><span class="ic">{{wa}}</span><span><small>WhatsApp</small>+880 1730 402 994</span></div>
 <div class="row"><span class="ic">{{em}}</span><span><small>Email</small>abirhasanrakib92@gmail.com</span></div>
 <div class="row"><span class="ic">{{ig}}</span><span><small>Follow for daily UI</small>@abirhasanrakib_</span><span class="save">Save for later {{bm}}</span></div>
</div>"""
    body = body.replace('{{wa}}', R.expand_icons('{{icon:message-circle:30:#111114:2}}')) \
               .replace('{{em}}', R.expand_icons('{{icon:mail:30:#111114:2}}')) \
               .replace('{{ig}}', R.expand_icons('{{icon:at-sign:30:#111114:2}}')) \
               .replace('{{bm}}', R.expand_icons('{{icon:bookmark:24:#ffffff:2.2}}'))
    css = """.chip{font:500 24px 'Inter Tight';padding:14px 24px;border-radius:999px;border:1.5px solid #111114}
.row{display:flex;align-items:center;gap:20px;background:#fff;border-radius:28px;padding:22px 26px;font:600 34px 'Inter Tight';letter-spacing:-.6px}
.row small{display:block;font:500 20px 'Inter Tight';color:#8A8A93;letter-spacing:0;margin-bottom:4px}
.ic{width:68px;height:68px;border-radius:20px;background:#EEEEEE;display:grid;place-items:center;flex:none}
.save{margin-left:auto;display:flex;align-items:center;gap:10px;background:#111114;color:#fff;font:600 22px 'Inter Tight';padding:16px 22px;border-radius:999px;letter-spacing:0}"""
    return await _slide(b, work, 'cta', body, css)


async def app(d, work, prefix, b):
    """Owner's spec (2026-11-09): 1 hand+phone (cover), 2 description + nav bar close-up,
    3 typography, 4 colors, then the CTA slide."""
    html = (d / 'screen.html').read_text()
    name, desc = _meta(html, 'app-name'), _meta(html, 'app-desc')
    import re
    desc_html = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', desc)
    year = '2026'

    # nav bar cut out of the live screen with a transparent background
    rendered = d / 'screen.rendered.html'
    rendered.write_text(R.expand_icons(html).replace('</head>',
        '<style>html,body,.screen{background:transparent!important}.fade,.home{display:none!important}body *{visibility:hidden}[data-nav],[data-nav] *,.tab,.tab *{visibility:visible!important}.tab,[data-nav]{box-shadow:none!important}</style></head>'))
    pg = await b.new_page(viewport={'width': 393, 'height': 852}, device_scale_factor=6)
    await pg.goto(rendered.as_uri()); await pg.evaluate('document.fonts.ready'); await pg.wait_for_timeout(300)
    sel = await pg.evaluate("()=>document.querySelector('[data-nav]')?'[data-nav]':'.tab'")
    await pg.locator(sel).screenshot(path=str(work / 'nav.png'), omit_background=True)
    await pg.close(); rendered.unlink()
    nav = Image.open(work / 'nav.png')
    nav_uri = 'data:image/png;base64,' + base64.b64encode((work / 'nav.png').read_bytes()).decode()
    nav_w = 920
    s2 = await _slide(b, work, 'app2', f"""
<div class="desc">{desc_html}</div>
<img src="{nav_uri}" style="position:absolute;left:{(W-nav_w)//2}px;top:{H-300-round(nav.size[1]*nav_w/nav.size[0])}px;width:{nav_w}px;
 filter:drop-shadow(0 40px 50px rgba(0,0,0,.22))">""",
        ".desc{font:400 52px/1.2 'Inter Tight';letter-spacing:-1px;text-transform:uppercase;color:#A3A3AB}.desc b{color:#111114;font-weight:600}")
    save(s2, f'{prefix}-2.jpg')

    # typography
    fam, note = (_meta(html, 'fonts').split('|') + [''])[:2]
    weights = ''.join(f'<div class="w"><span style="font-weight:{w}">Aa</span><small>{n} · {w}</small></div>'
                      for w, n in [(400, 'Regular'), (500, 'Medium'), (600, 'Semibold'), (700, 'Bold')])
    s3 = await _slide(b, work, 'app3', f"""
<div class="head"><span>Typography</span><span>{year}</span></div>
<div style="font:600 190px/1 '{fam}';letter-spacing:-7px;margin-top:150px">{fam}</div>
<p style="font:400 34px/1.45 '{fam}';color:#8A8A93;margin-top:26px;max-width:860px">{note}</p>
<div class="ws">{weights}</div>
<div style="position:absolute;right:80px;bottom:84px;text-align:right;font:500 30px/1.6 '{fam}'">ABCDEFGHIJKLMNOPQRSTUVWXYZ<br>abcdefghijklmnopqrstuvwxyz<br>0123456789 $%&amp;@#*()+</div>""",
        f".ws{{display:flex;gap:16px;margin-top:70px}}.w{{flex:1;background:#fff;border-radius:28px;padding:26px 24px}}"
        f".w span{{display:block;font-family:'{fam}';font-size:96px;letter-spacing:-3px;line-height:1}}"
        f".w small{{display:block;font:500 20px 'Inter Tight';color:#8A8A93;margin-top:18px}}")
    save(s3, f'{prefix}-3.jpg')

    # colors
    sw = [c.split(':') for c in _meta(html, 'palette').split('|') if c]
    tiles = ''.join(f'<div class="t"><div class="c" style="background:{h}"></div><div class="l"><span>{n}</span><span>{h.upper()}</span></div></div>' for h, n in sw)
    s4 = await _slide(b, work, 'app4', f"""
<div class="head"><span>Colors</span><span>{year}</span></div>
<div class="g">{tiles}</div>""",
        ".g{display:grid;grid-template-columns:1fr 1fr;gap:34px 26px;margin-top:56px}"
        ".c{height:300px;border-radius:30px;box-shadow:inset 0 0 0 1.5px rgba(0,0,0,.07)}"
        ".l{display:flex;justify-content:space-between;font:500 24px 'Inter Tight';margin-top:16px;letter-spacing:.3px}"
        ".l span:first-child{color:#111114}.l span:last-child{color:#6B6B74;font-family:'JetBrains Mono';font-size:22px}")
    save(s4, f'{prefix}-4.jpg')
    save(await cta_slide(b, work), f'{prefix}-5.jpg')


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
