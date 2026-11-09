#!/usr/bin/env python3
"""Render a carousel: slide 1 = the locked mockup (tools/render.py), slides 2..4 = close-ups.

Usage:
  python3 tools/carousel.py <design_dir> <app|dashboard|website> <out_prefix>
    -> <out_prefix>-1.jpg (cover), <out_prefix>-2.jpg ... (details)

Mark 2-3 elements in screen.html with data-detail="Short label", e.g.
  <div class="card" data-detail="Ward capacity">...</div>
They become close-up slides in document order (max 3). The label is shown as a small pill above the card.
"""
import asyncio, sys, pathlib, base64, html as H_
from PIL import Image
from playwright.async_api import async_playwright
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import render as R

VIEW = {'app': ({'width': 393, 'height': 852}, 4, False),
        'dashboard': ({'width': 1440, 'height': 960}, 2, False),
        'website': ({'width': 1440, 'height': 900}, 1.5, True)}

DETAIL_CSS = R.STAGE_CSS + """
.wrapc{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:22px}
.lbl{display:inline-flex;align-items:center;gap:8px;height:40px;padding:0 18px;border-radius:999px;background:#fff;
  box-shadow:0 0 0 1px rgba(0,0,0,.05),0 8px 20px -12px rgba(20,20,30,.25);font:600 17px 'Inter Tight';color:#17171C;letter-spacing:-.2px}
.lbl i{width:8px;height:8px;border-radius:50%;background:#17171C;display:block}
.frame.st{position:relative}
"""


def detail_stage(img_uri, w, h, label):
    max_w, max_h = 960, 1100
    s = min(max_w / w, max_h / h)
    cw, ch = round(w * s), round(h * s)
    lab = f'<div class="lbl"><i></i>{H_.escape(label)}</div>' if label else ''
    return f"""<!doctype html><html><head><meta charset=utf-8><link rel=stylesheet href="{(R.ROOT/'assets/fonts.css').as_uri()}"><style>{DETAIL_CSS}</style></head>
<body><div class="stage"><div class="wrapc">{lab}
<div class="frame st" style="border-radius:30px;padding:8px"><div class="inner" style="width:{cw}px;height:{ch}px;border-radius:22px;
background:url({img_uri}) 0 0/100% 100% no-repeat"></div></div></div></div></body></html>"""


async def main(design_dir, kind, prefix):
    d = pathlib.Path(design_dir).resolve()
    prefix = str(pathlib.Path(prefix).resolve())
    await R.main(design_dir, kind, prefix + '-1.jpg')
    vp, dsf, full = VIEW[kind]
    work = R.ROOT / '.render' / d.name
    rendered = d / 'screen.rendered.html'
    rendered.write_text(R.expand_icons((d / 'screen.html').read_text()))
    shot = work / 'screen.png'          # already rendered by R.main at the same viewport/scale
    big = Image.open(shot).convert('RGB')
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=R.CHROME)
        pg = await b.new_page(viewport=vp, device_scale_factor=dsf)
        await pg.goto(rendered.as_uri())
        await pg.evaluate('document.fonts.ready')
        dets = await pg.evaluate("""()=>[...document.querySelectorAll('[data-detail]')].slice(0,3).map(e=>{
            const r=e.getBoundingClientRect();return {l:e.dataset.detail,x:r.left+scrollX,y:r.top+scrollY,w:r.width,h:r.height,
            rad:parseFloat(getComputedStyle(e).borderTopLeftRadius)||0}})""")
        n = 1
        for det in dets:
            pad = 18 if det['rad'] else 6
            x0, y0 = max(0, det['x'] - pad), max(0, det['y'] - pad)
            x1, y1 = det['x'] + det['w'] + pad, det['y'] + det['h'] + pad
            crop = big.crop((round(x0 * dsf), round(y0 * dsf), round(x1 * dsf), round(y1 * dsf)))
            cp = work / f'detail-{n}.png'
            crop.save(cp)
            uri = 'data:image/png;base64,' + base64.b64encode(cp.read_bytes()).decode()
            st = work / f'detail-{n}.html'
            st.write_text(detail_stage(uri, x1 - x0, y1 - y0, det['l']))
            sp = await b.new_page(viewport={'width': R.W, 'height': R.H}, device_scale_factor=2)
            await R.shoot(sp, st.as_uri(), work / f'detail-{n}-stage.png')
            n += 1
            out = f'{prefix}-{n}.jpg'
            Image.open(work / f'detail-{n-1}-stage.png').convert('RGB').resize((R.W, R.H), Image.LANCZOS).save(out, quality=95)
            print('wrote', out)
        await b.close()
    rendered.unlink()


if __name__ == '__main__':
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    asyncio.run(main(*sys.argv[1:]))
