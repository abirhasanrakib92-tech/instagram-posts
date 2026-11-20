#!/usr/bin/env python3
"""Prototype of the new app carousel (owner request 2026-11-20).

Usage:
  python3 tools/app_carousel_v2.py <design_dir> <out_prefix>

<design_dir> holds screen.html (the hero screen for slide 1, same hand mockup as before) and
versions/v1*.png v2*.png v3*.png (3x exports of three screens of the same app, 1179x2556), plus
carousel.json with app name, tagline, callouts, component crops, fonts and palette.

Slides:
  1 hand holding phone (unchanged, locked)
  2 three screens side by side + app name
  3 one screen large and tilted with callout labels
  4 component bento: the best UI pieces cut out of the screens
  5 style guide: typeface + colour palette on one slide
  6 fixed CTA
"""
import asyncio, sys, json, pathlib, base64, io
from PIL import Image
from playwright.async_api import async_playwright
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import render as R
import carousel as C

W, H = 1080, 1350
TOP = C.BRAND_TOP          # room for the "Designed by" bar


def uri(img):
    b = io.BytesIO(); img.save(b, 'PNG')
    return 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode()


def page(body, css=''):
    return f"""<!doctype html><html><head><meta charset=utf-8>
<link rel=stylesheet href="{(R.ROOT/'assets/fonts.css').as_uri()}"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{W}px;height:{H}px;overflow:hidden;background:#EEEEEE;color:#111114;-webkit-font-smoothing:antialiased;font-family:'Inter Tight'}}
.s{{position:relative;width:{W}px;height:{H}px}}
.ph{{position:absolute;border-radius:56px;overflow:hidden;box-shadow:0 0 0 1px rgba(0,0,0,.04),0 40px 70px -40px rgba(30,20,10,.35)}}
.ph img{{display:block;width:100%}}
.lab{{font:500 22px 'Inter Tight';letter-spacing:.4px;text-transform:uppercase;color:#6B6B74}}
{css}</style></head><body><div class="s">{body}</div></body></html>"""


async def shot(b, work, name, html):
    p = work / f'{name}.html'; p.write_text(html)
    png = work / f'{name}.png'
    await C.shot_html(b, p, png, {'width': W, 'height': H}, 2)
    return Image.open(png).resize((W, H), Image.LANCZOS)


async def main(design_dir, prefix):
    d = pathlib.Path(design_dir).resolve()
    prefix = str(pathlib.Path(prefix).resolve())
    cfg = json.loads((d / 'carousel.json').read_text())
    shots = [Image.open(d / 'versions' / f).convert('RGBA') for f in cfg['screens']]
    S = shots[0].size[0] / 393                       # export scale (3x)
    work = R.ROOT / '.render' / (d.name + '-v2'); work.mkdir(parents=True, exist_ok=True)

    # 1: locked hand mockup
    await R.main(design_dir, 'app', prefix + '-1.jpg')

    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=R.CHROME)
        name, tag = cfg['name'], cfg['tagline']

        # 2: three screens side by side
        sw = 300; gap = 28; x0 = (W - 3 * sw - 2 * gap) // 2; y = 420
        phones = ''.join(f'<div class="ph" style="left:{x0+i*(sw+gap)}px;top:{y + (0 if i==1 else 40)}px;width:{sw}px;border-radius:44px"><img src="{uri(s)}"></div>' for i, s in enumerate(shots))
        s2 = await shot(b, work, 's2', page(f"""
<div style="position:absolute;left:80px;right:80px;top:{TOP+40}px">
 <div class="lab">{cfg['category']}</div>
 <div style="font:600 92px/1 'Inter Tight';letter-spacing:-4px;margin-top:18px">{name}</div>
 <div style="font:400 30px/1.35 'Inter Tight';color:#6B6B74;margin-top:16px;max-width:760px">{tag}</div>
</div>{phones}"""))
        C.save(s2, prefix + '-2.jpg')

        # 3: one screen large, tilted, with callouts
        hero = shots[cfg['closeup']['screen']]
        cw = 560
        callouts = ''
        for c in cfg['closeup']['callouts']:
            side = c['side']
            callouts += f"""<div style="position:absolute;top:{c['y']}px;{'left:56px' if side=='left' else 'right:56px'};display:flex;align-items:center;gap:14px;flex-direction:{'row' if side=='left' else 'row-reverse'}">
 <span style="background:#fff;border-radius:999px;padding:14px 22px;font:500 24px 'Inter Tight';box-shadow:0 10px 30px -18px rgba(0,0,0,.3);white-space:nowrap">{c['text']}</span>
 <span style="width:{c['line']}px;height:1.5px;background:#111114"></span><span style="width:12px;height:12px;border-radius:50%;background:#111114;margin-{'left' if side=='left' else 'right'}:-6px"></span></div>"""
        s3 = await shot(b, work, 's3', page(f"""
<div class="ph" style="left:{(W-cw)//2}px;top:{TOP+50}px;width:{cw}px;border-radius:78px;transform:rotate(-4deg)"><img src="{uri(hero)}"></div>
{callouts}"""))
        C.save(s3, prefix + '-3.jpg')

        # 4: component bento
        tiles = ''
        for t in cfg['components']:
            sh = shots[t['screen']]; x, y_, w, h = t['crop']
            crop = sh.crop((round(x*S), round(y_*S), round((x+w)*S), round((y_+h)*S)))
            tiles += f"""<div style="position:absolute;left:{t['box'][0]}px;top:{t['box'][1]}px;width:{t['box'][2]}px;height:{t['box'][3]}px;border-radius:40px;overflow:hidden;background:{t.get('bg','#fff')};box-shadow:0 30px 60px -40px rgba(0,0,0,.35)">
 <img src="{uri(crop)}" style="position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:{t['w']}px">
 <span style="position:absolute;right:20px;top:20px;font:500 19px 'Inter Tight';color:#111114;background:rgba(255,255,255,.88);border-radius:999px;padding:8px 14px;box-shadow:0 6px 16px -10px rgba(0,0,0,.4)">{t['label']}</span></div>"""
        s4 = await shot(b, work, 's4', page(f"""
<div class="lab" style="position:absolute;left:80px;top:{TOP+20}px">Components</div>{tiles}"""))
        C.save(s4, prefix + '-4.jpg')

        # 5: style guide (type + colours)
        fam, note = cfg['font'], cfg['font_note']
        sw_ = ''.join(f"""<div style="flex:1"><div style="height:{260 if i<3 else 180}px;border-radius:28px;background:{h};box-shadow:inset 0 0 0 1.5px rgba(0,0,0,.06)"></div>
 <div style="font:500 20px 'Inter Tight';margin-top:12px">{n}</div><div style="font:400 18px 'JetBrains Mono';color:#6B6B74;margin-top:2px">{h}</div></div>""" for i, (h, n) in enumerate(cfg['palette']))
        s5 = await shot(b, work, 's5', page(f"""
<div style="position:absolute;left:80px;right:80px;top:{TOP+20}px">
 <div style="display:flex;justify-content:space-between" class="lab"><span>Style guide</span><span>2026</span></div>
 <div style="display:flex;align-items:flex-end;gap:40px;margin-top:40px">
  <div style="font:500 210px/0.8 '{fam}';letter-spacing:-10px">Aa</div>
  <div><div style="font:600 56px '{fam}';letter-spacing:-2px">{fam}</div>
   <div style="font:400 24px/1.4 'Inter Tight';color:#6B6B74;margin-top:8px;max-width:520px">{note}</div>
   <div style="display:flex;gap:22px;margin-top:18px;font:24px '{fam}'"><span style="font-weight:300">Light</span><span style="font-weight:400">Regular</span><span style="font-weight:500">Medium</span><span style="font-weight:600">Semibold</span></div></div>
 </div>
 <div style="display:flex;gap:18px;margin-top:70px">{sw_[:sw_.find('</div></div>', sw_.find('</div></div>', sw_.find('</div></div>')+1)+1)+12]}</div>
 <div style="display:flex;gap:18px;margin-top:26px">{''.join(sw_.split('</div></div>')[i]+'</div></div>' for i in range(3,6))}</div>
</div>"""))
        C.save(s5, prefix + '-5.jpg')

        for i in range(1, 6):
            if i == 1:
                C.make_room(f'{prefix}-1.jpg', 'shift')
            await C.brand(b, work, f'{prefix}-{i}.jpg', wa=False)
        C.save(await C.cta_slide(b, work), f'{prefix}-6.jpg')
        await b.close()


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    asyncio.run(main(*sys.argv[1:]))
