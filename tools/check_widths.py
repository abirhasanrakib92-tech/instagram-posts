"""QA (owner, 2026-11-21): lists every big block (>900px wide, >150px tall) with its left/right edges.
The footer and every full-width coloured/photo section must use the SAME left/right edges as the hero frame.
Usage: python3 tools/check_widths.py designs/<dir> [...]"""
import sys,asyncio,pathlib
sys.path.insert(0,'/home/claude/instagram-posts/tools')
import render as R
from playwright.async_api import async_playwright
async def m(d):
  d=pathlib.Path(d).resolve();t=d/'_w.html';t.write_text(R.expand_icons((d/'screen.html').read_text()))
  async with async_playwright() as p:
    b=await p.chromium.launch();pg=await b.new_page(viewport={'width':1440,'height':900})
    await pg.goto(t.as_uri());await pg.wait_for_timeout(500)
    r=await pg.evaluate("""()=>{const out=[];const walk=(el,dep)=>{for(const c of el.children){const r=c.getBoundingClientRect();if(r.height>150&&r.width>900){out.push([dep,c.tagName.toLowerCase()+'.'+(c.className||'').toString().split(' ')[0],Math.round(r.left),Math.round(r.right),Math.round(r.top),Math.round(r.height),getComputedStyle(c).backgroundColor,getComputedStyle(c).backgroundImage!='none']);if(dep<2)walk(c,dep+1)}}};walk(document.body,0);return out}""")
    for x in r: print(*x)
    await b.close()
  t.unlink()
for d in sys.argv[1:]:
  print('==',d.split('/')[-1]); asyncio.run(m(d))
