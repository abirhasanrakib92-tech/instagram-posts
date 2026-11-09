#!/usr/bin/env python3
"""Render a design into a finished 1080x1350 Instagram post.

Usage:
  python3 tools/render.py <design_dir> <app|dashboard|website> <out.jpg>

The design dir holds screen.html (plus any images it uses).
  app        -> screen.html is a 393x852 phone screen; composited into the hand-holding-phone photo
  dashboard  -> screen.html is a 1440x960 web app; shown in a browser window, plus a zoom card of
                the element marked data-zoom (optional)
  website    -> screen.html is a 1440px-wide landing page, 4500-6500px tall; shown as two long cards

Icons: write {{icon:<lucide-name>:<size>:<#hex>[:<stroke-width>]}} anywhere in the HTML.
Mock URL for the browser bar: <meta name="mock-url" content="app.example.com">.
"""
import asyncio, re, sys, pathlib, base64, io
import numpy as np
from PIL import Image, ImageDraw
from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
CHROME = '/usr/bin/google-chrome'
BG = '#EEEEEE'
W, H = 1080, 1350


def expand_icons(html):
    def icon(m):
        name, size, color, sw = m.group(1), m.group(2), m.group(3), m.group(4) or '2'
        p = ROOT / f'node_modules/lucide-static/icons/{name}.svg'
        if not p.exists():
            raise SystemExit(f'unknown lucide icon: {name}')
        svg = re.sub(r'<!--.*?-->', '', p.read_text(), flags=re.S)
        svg = re.sub(r'width="\d+"', f'width="{size}"', svg, count=1)
        svg = re.sub(r'height="\d+"', f'height="{size}"', svg, count=1)
        svg = svg.replace('stroke="currentColor"', f'stroke="{color}"')
        svg = re.sub(r'stroke-width="[\d.]+"', f'stroke-width="{sw}"', svg)
        svg = re.sub(r'class="[^"]*"', 'style="display:block;flex:none"', svg)
        return svg.strip()
    return re.sub(r'\{\{icon:([a-z0-9-]+):(\d+):(#[0-9A-Fa-f]{3,8})(?::([\d.]+))?\}\}', icon, html)


async def shoot(page, url, path, full=False):
    await page.goto(url)
    await page.evaluate('document.fonts.ready')
    await page.wait_for_timeout(500)
    await page.screenshot(path=str(path), full_page=full)


def b64(path):
    return 'data:image/png;base64,' + base64.b64encode(pathlib.Path(path).read_bytes()).decode()


# ---------- app: hand-holding-phone photo ----------
def compose_app(screen_png, out):
    ref = Image.open(ROOT / 'assets/mockups/hand-phone.png').convert('RGB')
    # 4:5 crop around the phone, then scale to 1080 wide
    cx0, cw = 255, 957
    s = W / cw
    base = ref.crop((cx0, 0, cx0 + cw, 1196)).resize((W, H), Image.LANCZOS)
    X0, Y0, SW, SH, R = (538 - cx0) * s, 43 * s, 392 * s, 853 * s, 60 * s
    X0, Y0, SWi, SHi = round(X0), round(Y0), round(SW), round(SH)
    scr = Image.open(screen_png).convert('RGB').resize((SWi, SHi), Image.LANCZOS)
    k = 4
    m = Image.new('L', (SWi * k, SHi * k), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, SWi * k - 1, SHi * k - 1], R * k, fill=255)
    m = m.resize((SWi, SHi), Image.LANCZOS)
    o = base.copy()
    o.paste(scr, (X0, Y0), m)
    # restore the dynamic island from the photo
    a0 = np.array(base).astype(float)
    o = np.array(o).astype(float)
    ix0, ix1, iy0, iy1 = round((664 - cx0) * s), round((804 - cx0) * s), round(46 * s), round(96 * s)
    reg = a0[iy0:iy1, ix0:ix1]
    al = np.clip((120 - reg.mean(2)) / 90, 0, 1)[..., None]
    o[iy0:iy1, ix0:ix1] = reg * al + o[iy0:iy1, ix0:ix1] * (1 - al)
    Image.fromarray(o.round().astype(np.uint8)).save(out, quality=95)


STAGE_CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1350px;overflow:hidden;background:#EEEEEE;font-family:'Inter Tight',sans-serif;-webkit-font-smoothing:antialiased}
.stage{position:relative;width:1080px;height:1350px;background:#EEEEEE}
.frame{position:absolute;padding:7px;border-radius:26px;background:rgba(255,255,255,.55);
  box-shadow:0 0 0 1px rgba(0,0,0,.04),0 40px 80px -30px rgba(20,20,30,.28),0 12px 24px -12px rgba(20,20,30,.12)}
.inner{border-radius:19px;overflow:hidden;background:#fff;box-shadow:0 0 0 1px rgba(0,0,0,.06)}
.bar{height:38px;display:flex;align-items:center;padding:0 14px;gap:12px;background:#F7F7F8;border-bottom:1px solid #EBEBEE}
.dots{display:flex;gap:7px}.dots i{width:11px;height:11px;border-radius:50%;display:block}
.url{flex:1;display:flex;justify-content:center}
.url span{display:flex;align-items:center;gap:6px;height:24px;padding:0 70px;border-radius:7px;background:#EDEDF0;color:#6E6E78;font-size:11.5px;font-weight:500;letter-spacing:.1px}
.side{display:flex;gap:12px;color:#9A9AA3}
.shot{display:block;width:100%}
.crop{background-repeat:no-repeat}
"""
LOCK = '<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#8C8C96" stroke-width="2.6" stroke-linecap="round"><rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/></svg>'
BAR_ICONS = ('<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#9A9AA3" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/><polyline points="16 6 12 2 8 6"/><line x1="12" x2="12" y1="2" y2="15"/></svg>'
             '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#9A9AA3" stroke-width="2" stroke-linecap="round"><path d="M5 12h14"/><path d="M12 5v14"/></svg>')


def dashboard_stage(shot, url, zoom):
    # window: 1440x960 design scaled to inner width 952
    iw = 952
    sc = iw / 1440
    ih = round(960 * sc) + 38
    fw, fh = iw + 14, ih + 14
    fx = (W - fw) // 2
    zoom_html = ''
    if zoom:
        zx, zy, zw, zh = zoom
        zs = min(1.55 * sc / sc, 1.0) * 1.0  # zoom card shows the element at 1.0 of the 1440 layout (=1.51x the window)
        zs = 0.98
        cw, ch = round(zw * zs), round(zh * zs)
        if cw > 640:  # keep the card within the canvas
            zs = 640 / zw
            cw, ch = round(zw * zs), round(zh * zs)
        overlap = min(170, ch // 2)
        total = fh + ch - overlap
        fy = max(60, (H - total) // 2)
        cy = fy + fh - overlap
        cx = W - 54 - cw - 14
        zoom_html = (f'<div class="frame" style="left:{cx}px;top:{cy}px;border-radius:24px">'
                     f'<div class="inner crop" style="width:{cw}px;height:{ch}px;border-radius:17px;'
                     f'background-image:url({shot});background-size:{round(1440*zs)}px auto;'
                     f'background-position:-{round(zx*zs)}px -{round(zy*zs)}px"></div></div>')
    else:
        fy = (H - fh) // 2
    return f"""<!doctype html><html><head><meta charset=utf-8><link rel=stylesheet href="{(ROOT/'assets/fonts.css').as_uri()}"><style>{STAGE_CSS}</style></head>
<body><div class="stage">
<div class="frame" style="left:{fx}px;top:{fy}px"><div class="inner" style="width:{iw}px">
 <div class="bar"><div class="dots"><i style="background:#FF5F57"></i><i style="background:#FEBC2E"></i><i style="background:#28C840"></i></div>
 <div class="url"><span>{LOCK}{url}</span></div><div class="side">{BAR_ICONS}</div></div>
 <img class="shot" src="{shot}" style="height:{ih-38}px">
</div></div>
{zoom_html}
</div></body></html>"""


def website_stage(shot, page_h):
    cw = 640
    sc = cw / 1440
    main_h = H - 120 - 14                  # main card visible height
    seg = round(main_h / sc)               # page px shown on main card
    back_top = 150
    back_h = H - back_top + 40
    back_start = min(seg, max(0, page_h - round(back_h / sc)))
    return f"""<!doctype html><html><head><meta charset=utf-8><style>{STAGE_CSS}</style></head>
<body><div class="stage">
<div class="frame" style="left:560px;top:{back_top}px;border-radius:24px"><div class="inner crop" style="width:{cw}px;height:{back_h}px;border-radius:17px;
  background-image:url({shot});background-size:{cw}px auto;background-position:0 -{round(back_start*sc)}px"></div></div>
<div class="frame" style="left:64px;top:60px;border-radius:24px"><div class="inner crop" style="width:{cw}px;height:{main_h}px;border-radius:17px;
  background-image:url({shot});background-size:{cw}px auto;background-position:0 0"></div></div>
</div></body></html>"""


async def main(design_dir, kind, out):
    d = pathlib.Path(design_dir).resolve()
    html = expand_icons((d / 'screen.html').read_text())
    rendered = d / 'screen.rendered.html'
    rendered.write_text(html)
    work = ROOT / '.render' / d.name
    work.mkdir(parents=True, exist_ok=True)
    out = pathlib.Path(out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME)
        if kind == 'app':
            pg = await b.new_page(viewport={'width': 393, 'height': 852}, device_scale_factor=4)
            await shoot(pg, rendered.as_uri(), work / 'screen.png')
            compose_app(work / 'screen.png', out)
        elif kind == 'dashboard':
            pg = await b.new_page(viewport={'width': 1440, 'height': 960}, device_scale_factor=2)
            await shoot(pg, rendered.as_uri(), work / 'screen.png')
            zoom = await pg.evaluate("""()=>{const e=document.querySelector('[data-zoom]');if(!e)return null;
              const r=e.getBoundingClientRect();const p=Number(e.dataset.zoomPad||16);
              return [r.left-p,r.top-p,r.width+2*p,r.height+2*p]}""")
            url = await pg.evaluate("()=>document.querySelector('meta[name=mock-url]')?.content||'app.example.com'")
            stage = work / 'stage.html'
            stage.write_text(dashboard_stage(b64(work / 'screen.png'), url, zoom))
            sp = await b.new_page(viewport={'width': W, 'height': H}, device_scale_factor=2)
            await shoot(sp, stage.as_uri(), work / 'stage.png')
            Image.open(work / 'stage.png').convert('RGB').resize((W, H), Image.LANCZOS).save(out, quality=95)
        elif kind == 'website':
            pg = await b.new_page(viewport={'width': 1440, 'height': 900}, device_scale_factor=1.5)
            await shoot(pg, rendered.as_uri(), work / 'screen.png', full=True)
            page_h = await pg.evaluate('document.documentElement.scrollHeight')
            stage = work / 'stage.html'
            stage.write_text(website_stage(b64(work / 'screen.png'), page_h))
            sp = await b.new_page(viewport={'width': W, 'height': H}, device_scale_factor=2)
            await shoot(sp, stage.as_uri(), work / 'stage.png')
            Image.open(work / 'stage.png').convert('RGB').resize((W, H), Image.LANCZOS).save(out, quality=95)
        else:
            raise SystemExit('kind must be app, dashboard or website')
        await b.close()
    rendered.unlink()
    print('wrote', out)


if __name__ == '__main__':
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    asyncio.run(main(*sys.argv[1:]))
