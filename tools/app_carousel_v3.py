#!/usr/bin/env python3
"""App carousel v3 (owner, 2026-11-20): brand bar on slide 1 only, fixed CTA last.

Usage: python3 tools/app_carousel_v3.py <design_dir> <out_prefix>

design_dir: screen.html (slide 1, hand mockup), carousel.json, and the 3x screen export named in
carousel.json "screen" (1179x2556).
  1 hand holding phone + "Designed by" bar
  2 intro: full-bleed app gradient, huge name, tilted phone, floating components
  3 zoom: the most interesting band of the screen blown up, bleeding off the edge
  4 exploded components on the app's dark colour
  5 style guide: gradient "Aa" + overlapping colour discs
  6 fixed CTA (unchanged)
"""
import asyncio, sys, json, pathlib, base64, io, random
from PIL import Image, ImageDraw
from playwright.async_api import async_playwright
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import render as R
import carousel as C

W, H = 1080, 1350
S = 3  # export scale


def uri(img):
    b = io.BytesIO(); img.save(b, 'PNG')
    return 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode()


def element(shot, box, radius, shape='rect'):
    """Cut one UI element out of the 3x screen with its own rounded mask (so it floats)."""
    x, y, w, h = box
    c = shot.crop((round(x*S), round(y*S), round((x+w)*S), round((y+h)*S))).convert('RGBA')
    k = 4; m = Image.new('L', (c.width*k, c.height*k), 0); d = ImageDraw.Draw(m)
    if shape == 'circle': d.ellipse([0, 0, c.width*k-1, c.height*k-1], fill=255)
    else: d.rounded_rectangle([0, 0, c.width*k-1, c.height*k-1], radius*S*k, fill=255)
    c.putalpha(m.resize(c.size, Image.LANCZOS))
    return c


def grain(op=.07):
    random.seed(4)
    dots = ''.join(f'<circle cx="{random.random()*W:.0f}" cy="{random.random()*H:.0f}" r=".9" fill="#fff"/>' for _ in range(2600))
    return f'<svg style="position:absolute;inset:0;opacity:{op}" width="{W}" height="{H}">{dots}</svg>'


def page(body, bg, css=''):
    return f"""<!doctype html><html><head><meta charset=utf-8>
<link rel=stylesheet href="{(R.ROOT/'assets/fonts.css').as_uri()}"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{W}px;height:{H}px;overflow:hidden;-webkit-font-smoothing:antialiased}}
.s{{position:relative;width:{W}px;height:{H}px;overflow:hidden;background:{bg}}}
.ab{{position:absolute}}
.fl{{position:absolute;filter:drop-shadow(0 40px 50px rgba(40,10,0,.35)) drop-shadow(0 6px 10px rgba(40,10,0,.15))}}
{css}</style></head><body><div class="s">{body}</div></body></html>"""


async def shot(b, work, name, html):
    p = work / f'{name}.html'; p.write_text(html)
    png = work / f'{name}.png'
    await C.shot_html(b, p, png, {'width': W, 'height': H}, 2)
    return Image.open(png).resize((W, H), Image.LANCZOS)


def phone(img, w):
    """Screen inside a thin graphite bezel."""
    r = w * 0.135
    return f"""<div style="width:{w}px;padding:{w*0.032:.0f}px;border-radius:{r:.0f}px;background:linear-gradient(145deg,#3a3a3c,#111 40%,#2b2b2d);box-shadow:inset 0 0 0 2px #55555a">
<img src="{uri(img)}" style="display:block;width:100%;border-radius:{r*0.82:.0f}px"></div>"""


async def main(design_dir, prefix):
    d = pathlib.Path(design_dir).resolve()
    prefix = str(pathlib.Path(prefix).resolve())
    cfg = json.loads((d / 'carousel.json').read_text())['v3']
    scr = Image.open(d / cfg['screen']).convert('RGBA')
    work = R.ROOT / '.render' / (d.name + '-v3'); work.mkdir(parents=True, exist_ok=True)
    el = {k: element(scr, v['box'], v.get('r', 0), v.get('shape', 'rect')) for k, v in cfg['elements'].items()}
    E = lambda k, w, x, y, rot=0, z=1: f'<img class="fl" src="{uri(el[k])}" style="left:{x}px;top:{y}px;width:{w}px;transform:rotate({rot}deg);z-index:{z}">'
    font, pal = cfg['font'], cfg['palette']
    g1, g2, g3, dark = cfg['gradient']

    await R.main(design_dir, 'app', prefix + '-1.jpg')
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=R.CHROME)

        # 2 intro
        s2 = await shot(b, work, 's2', page(f"""
{grain(.08)}
<div class="ab" style="left:80px;top:96px;color:#fff">
 <div style="font:500 24px '{font}';letter-spacing:3px;text-transform:uppercase;opacity:.7">{cfg['category']}</div>
 <div style="font:600 168px/0.9 '{font}';letter-spacing:-9px;margin-top:22px">{cfg['name']}</div>
 <div style="font:400 32px/1.35 '{font}';opacity:.82;margin-top:26px;width:520px">{cfg['tagline']}</div>
</div>
<div class="fl" style="left:500px;top:430px;transform:rotate(-9deg)">{phone(scr, 500)}</div>
{E('card', 300, 70, 760, 7, 3)}
{E('chip', 470, 40, 1110, -4, 3)}""",
            f"radial-gradient(120% 80% at 85% 10%,{g1} 0%,{g2} 45%,{g3} 80%,{dark} 100%)"))
        C.save(s2, prefix + '-2.jpg')

        # 3 zoom
        zx, zy, zw, zh = cfg['zoom']
        k = 1120 / zw
        band = scr.crop((round(zx*S), round(zy*S), round((zx+zw)*S), round((zy+zh)*S)))
        s3 = await shot(b, work, 's3', page(f"""
<div class="ab" style="left:80px;top:96px">
 <div style="font:500 24px '{font}';letter-spacing:3px;text-transform:uppercase;color:{dark};opacity:.55">Close-up</div>
 <div style="font:500 64px/1.05 '{font}';letter-spacing:-2.5px;color:{dark};margin-top:18px;width:820px">{cfg['zoom_title']}</div>
</div>
<div class="ab" style="left:80px;top:380px;width:1120px;height:{zh*k:.0f}px;border-radius:64px 0 0 64px;overflow:hidden;box-shadow:0 50px 80px -40px rgba(60,15,0,.45)">
 <img src="{uri(band)}" style="display:block;width:1120px"></div>
""", cfg['paper']))
        C.save(s3, prefix + '-3.jpg')

        # 4 exploded components
        s4 = await shot(b, work, 's4', page(f"""
{grain(.06)}
<div class="ab" style="left:80px;top:96px;color:#fff">
 <div style="font:500 24px '{font}';letter-spacing:3px;text-transform:uppercase;opacity:.6">Components</div>
 <div style="font:500 64px/1.05 '{font}';letter-spacing:-2.5px;margin-top:18px">Soft glass,<br>warm light.</div>
</div>
{E('bell', 150, 820, 110, 0)}
{E('card', 330, 80, 400, -6)}
{E('card2', 330, 450, 380, 5)}
{E('chip', 860, 110, 790, -2)}
{E('mood', 380, 90, 1010, 0)}
{E('orb', 260, 700, 950, 0)}""",
            f"radial-gradient(90% 70% at 20% 30%,{g3} 0%,{dark} 75%)"))
        C.save(s4, prefix + '-4.jpg')

        # 5 style guide
        discs = ''.join(f"""<div style="position:relative;width:210px;height:210px;margin-left:{0 if i==0 else -64}px;border-radius:50%;background:{h};box-shadow:0 0 0 6px {cfg['paper']},0 30px 50px -30px rgba(60,15,0,.4);z-index:{10-i}"></div>""" for i, (h, n) in enumerate(pal))
        labels = ''.join(f'<div style="width:162px"><div style="font:500 22px \'{font}\';color:{dark}">{n}</div><div style="font:400 19px \'JetBrains Mono\';color:{dark};opacity:.55;margin-top:4px">{h}</div></div>' for h, n in pal)
        s5 = await shot(b, work, 's5', page(f"""
<div class="ab" style="left:80px;right:80px;top:96px;display:flex;justify-content:space-between;font:500 24px '{font}';letter-spacing:3px;text-transform:uppercase;color:{dark};opacity:.55"><span>Style guide</span><span>{cfg['name']}</span></div>
<div class="ab" style="left:66px;top:170px;font:500 400px/1 '{font}';letter-spacing:-22px;background:linear-gradient(135deg,{g1},{g2} 50%,{dark});-webkit-background-clip:text;color:transparent">Aa</div>
<div class="ab" style="left:600px;top:250px;width:400px;color:{dark}">
 <div style="font:600 64px '{font}';letter-spacing:-2.5px">{font}</div>
 <div style="font:400 26px/1.4 '{font}';opacity:.6;margin-top:12px">{cfg['font_note']}</div>
 <div style="display:flex;flex-wrap:wrap;gap:10px;margin-top:26px">{''.join(f'<span style="font:{w} 22px \'{font}\';padding:10px 18px;border-radius:999px;border:1.5px solid {dark}33">{n}</span>' for w, n in [(300,'Light'),(400,'Regular'),(500,'Medium'),(600,'Semibold')])}</div>
</div>
<div class="ab" style="left:80px;top:800px;display:flex">{discs}</div>
<div class="ab" style="left:80px;top:1060px;display:flex;flex-wrap:nowrap;gap:26px 0;width:980px">{labels}</div>""", cfg['paper']))
        C.save(s5, prefix + '-5.jpg')

        C.make_room(f'{prefix}-1.jpg', 'shift')
        await C.brand(b, work, f'{prefix}-1.jpg', wa=False)
        C.save(await C.cta_slide(b, work), f'{prefix}-6.jpg')
        await b.close()


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    asyncio.run(main(*sys.argv[1:]))
