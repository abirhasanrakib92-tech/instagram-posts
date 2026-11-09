#!/usr/bin/env python3
"""Render a dashboard motion reel (1080x1350 4:5, 30 fps) from a design and its reel.json.

Usage:
  python3 tools/reel.py designs/<dir> <out.mp4> [--frames t1,t2,...]   (--frames: save stills only, for checking)

Style (owner's reference): light dashboard floating on #EEEEEE, enters with a 3D tilt, content builds in,
camera glides and zooms between cards, highlight rings, a cursor that clicks, zoom out, then the CTA card.
Every frame is drawn deterministically from t (no CSS transitions), so renders are repeatable.
"""
import asyncio, json, math, pathlib, subprocess, sys, threading, functools, http.server, socketserver, base64
from playwright.async_api import async_playwright
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import render as R
import carousel as C

W, H, FPS = 1080, 1350, 30
ROOT = R.ROOT

STAGE = """<!doctype html><html><head><meta charset=utf-8><style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1350px;overflow:hidden;background:#EEEEEE}
#persp{position:absolute;inset:0;perspective:2200px}
#cam{position:absolute;left:0;top:0;width:1440px;height:960px;transform-origin:0 0}
#win{width:1440px;height:960px;border-radius:26px;overflow:hidden;background:#fff;
 box-shadow:0 0 0 1px rgba(0,0,0,.05),0 60px 120px -40px rgba(20,20,40,.35),0 20px 40px -20px rgba(20,20,40,.18)}
#win iframe{width:1440px;height:960px;border:0;display:block}
#end{position:absolute;left:0;top:0;width:1080px;height:1350px;opacity:0}
</style></head><body><div id="persp"><div id="cam"><div id="win"><iframe id="f" src="SRC"></iframe></div></div></div>
<img id="end" src="END"></body></html>"""

INJECT = r"""
(()=>{
const D=document, cfg=window.__REEL;
const ease=x=>x<.5?4*x*x*x:1-Math.pow(-2*x+2,3)/2, cl=x=>Math.max(0,Math.min(1,x));
const span=(t,a,b)=>cl((t-a)/(b-a));
// build targets
const build=[];cfg.build_sel.forEach(s=>D.querySelectorAll(s).forEach(e=>build.push(e)));
// count-ups
const counts=[];D.querySelectorAll(cfg.count_sel||'').forEach(e=>{const n=[...e.childNodes].find(x=>x.nodeType==3&&/\d/.test(x.textContent));if(!n)return;
 const m=n.textContent.match(/[\d,]+(\.\d+)?/);counts.push({n,orig:n.textContent,m:m[0],v:parseFloat(m[0].replace(/,/g,'')),dec:(m[1]||'').length-1,comma:m[0].includes(','),el:e})});
// growing svg rects
const grows=(cfg.grow||[]).map(g=>({t:g.t,els:[...D.querySelectorAll(g.sel)].map(r=>({r,y:+r.getAttribute('y'),h:+r.getAttribute('height')}))}));
const shows=(cfg.show||[]).map(s=>({t:s.t,els:[...D.querySelectorAll(s.sel)]}));
const bars=(cfg.bars||[]).map(b=>({t:b.t,els:[...D.querySelectorAll(b.sel)].map(e=>({e,w:e.style.width}))}));
// overlays
const ring=D.createElement('div');ring.style.cssText='position:absolute;pointer-events:none;border-radius:20px;z-index:50;opacity:0';D.body.appendChild(ring);
const cur=D.createElement('div');cur.style.cssText='position:absolute;z-index:60;width:34px;height:40px;opacity:0;pointer-events:none';
cur.innerHTML='<svg width="34" height="40" viewBox="0 0 34 40"><path d="M3 2 L3 32 L11 25 L17 38 L23 35 L17 23 L28 23 Z" fill="#111" stroke="#fff" stroke-width="2.5" stroke-linejoin="round"/></svg>';D.body.appendChild(cur);
const rect=s=>{const e=D.querySelector(s);const r=e.getBoundingClientRect();return {x:r.left,y:r.top,w:r.width,h:r.height,e}};
window.__rect=rect;
window.__frame=function(t){
 const n=build.length,[b0,b1]=cfg.build;
 build.forEach((e,i)=>{const s=b0+(b1-b0-0.7)*i/Math.max(1,n-1),p=ease(span(t,s,s+0.7));e.style.opacity=p;e.style.transform=`translateY(${(1-p)*26}px)`});
 counts.forEach((c,i)=>{const idx=build.findIndex(b=>b.contains(c.el));const s=idx<0?b0:b0+(b1-b0-0.7)*idx/Math.max(1,n-1);const p=ease(span(t,s+0.2,s+1.4));
  let v=(c.v*p).toFixed(Math.max(0,c.dec));if(c.comma)v=Number(v).toLocaleString('en-US',{minimumFractionDigits:Math.max(0,c.dec)});c.n.textContent=c.orig.replace(c.m,v)});
 grows.forEach(g=>{g.els.forEach((o,i)=>{const s=g.t[0]+(g.t[1]-g.t[0]-0.6)*i/Math.max(1,g.els.length-1),p=ease(span(t,s,s+0.6));const h=o.h*p;o.r.setAttribute('height',Math.max(0.01,h));o.r.setAttribute('y',o.y+o.h-h)})});
 bars.forEach(b=>b.els.forEach((o,i)=>{const s=b.t+i*0.12,p=ease(span(t,s,s+0.7));o.e.style.width=`calc(${o.w} * ${p})`}));
 shows.forEach(s=>s.els.forEach(e=>{const p=ease(span(t,s.t,s.t+0.45));e.style.opacity=p;e.style.transform=`translateY(${(1-p)*14}px) scale(${.96+.04*p})`}));
 // ring
 ring.style.opacity=0;
 for(const r of cfg.rings||[]){if(t>=r.t[0]&&t<=r.t[1]){const q=rect(r.sel),pad=r.pad??8,a=ease(span(t,r.t[0],r.t[0]+.35))*(1-ease(span(t,r.t[1]-.35,r.t[1])));
   ring.style.left=q.x-pad+'px';ring.style.top=q.y-pad+'px';ring.style.width=q.w+2*pad+'px';ring.style.height=q.h+2*pad+'px';
   ring.style.borderRadius=(r.radius??22)+'px';ring.style.border=`3px solid ${cfg.accent}`;ring.style.boxShadow=`0 0 0 ${6+4*a}px ${cfg.accent}22`;ring.style.opacity=a;}}
 // cursor
 cur.style.opacity=0;const cp=cfg.cursor;
 if(cp){const ks=cp.path;for(let i=0;i<ks.length-1;i++){const [ta,sa,oa]=ks[i],[tb,sb,ob]=ks[i+1];if(t>=ta&&t<=tb){
   const A=pt(sa,oa),B=pt(sb,ob),p=ease(span(t,ta,tb));cur.style.left=A[0]+(B[0]-A[0])*p+'px';cur.style.top=A[1]+(B[1]-A[1])*p+'px';cur.style.opacity=1;}}
  const vis=t>=ks[0][0]-.3&&t<=ks[ks.length-1][0]+.4;if(vis&&t<ks[0][0]){const A=pt(ks[0][1],ks[0][2]);cur.style.left=A[0]+'px';cur.style.top=A[1]+'px';cur.style.opacity=span(t,ks[0][0]-.3,ks[0][0])}
  if(vis&&t>ks[ks.length-1][0]){const L=ks[ks.length-1],A=pt(L[1],L[2]);cur.style.left=A[0]+'px';cur.style.top=A[1]+'px';cur.style.opacity=1-span(t,L[0]+.2,L[0]+.4)}
  for(const c of cp.click||[]){const k=span(t,c,c+.18),k2=span(t,c+.18,c+.4),press=t>=c&&t<=c+.4?(t<c+.18?k:1-k2):0;
   cur.style.transform=`scale(${1-.18*press})`;const btn=D.querySelector(cp.target);if(btn){btn.style.transform=`scale(${1-.06*press})`;btn.style.boxShadow=t>c?`0 0 0 ${8*(1-span(t,c,c+.8))}px ${cfg.accent}55`:''}}}
};
function pt(sel,off){if(Array.isArray(sel))return sel;const q=rect(sel);return [q.x+q.w*(off?.[0]??.6),q.y+q.h*(off?.[1]??.6)]}
window.__frame(0);
})();
"""


def serve():
    h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
    h.log_message = lambda *a: None
    srv = socketserver.TCPServer(('127.0.0.1', 0), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def ease(x): return 4 * x * x * x if x < .5 else 1 - pow(-2 * x + 2, 3) / 2


async def main(design_dir, out, frames=None):
    d = pathlib.Path(design_dir).resolve()
    cfg = json.loads((d / 'reel.json').read_text())
    (d / 'screen.rendered.html').write_text(R.expand_icons((d / 'screen.html').read_text()))
    work = ROOT / '.render' / d.name
    work.mkdir(parents=True, exist_ok=True)
    srv = serve()
    port = srv.server_address[1]
    rel = d.relative_to(ROOT).as_posix()
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=R.CHROME)
        cta = await C.cta_slide(b, work)
        cta.save(work / 'cta.png')
        (work / 'stage.html').write_text(STAGE.replace('SRC', f'http://127.0.0.1:{port}/{rel}/screen.rendered.html')
                                         .replace('END', f'http://127.0.0.1:{port}/.render/{d.name}/cta.png'))
        pg = await b.new_page(viewport={'width': W, 'height': H}, device_scale_factor=1)
        await pg.goto(f'http://127.0.0.1:{port}/.render/{d.name}/stage.html')
        fr = pg.frame_locator('#f')
        f = pg.frames[1]
        await f.wait_for_load_state('load')
        await f.evaluate('document.fonts.ready')
        await f.wait_for_timeout(400)
        await f.evaluate(f'window.__REEL={json.dumps(cfg)}')
        await f.evaluate(INJECT)
        # resolve camera keys to (cx, cy, scale)
        keys = []
        for k in cfg['camera']:
            t, target = k[0], k[1]
            zoom = k[2] if len(k) > 2 else 1.0
            if target == 'full':
                keys.append((t, 720, 480, (W - 120) / 1440 * zoom))
            else:
                r = await f.evaluate(f'(()=>{{const q=window.__rect({json.dumps(target)});return [q.x,q.y,q.w,q.h]}})()')
                x, y, w, h = r
                s = min((W - 150) / w, (H * 0.78) / h) * zoom
                keys.append((t, x + w / 2, y + h / 2, s))

        def cam(t):
            if t <= keys[0][0]: return keys[0][1:]
            for a, bb in zip(keys, keys[1:]):
                if a[0] <= t <= bb[0]:
                    q = ease((t - a[0]) / (bb[0] - a[0]))
                    # interpolate scale in log space so zooms feel even
                    s = math.exp(math.log(a[3]) + (math.log(bb[3]) - math.log(a[3])) * q)
                    return (a[1] + (bb[1] - a[1]) * q, a[2] + (bb[2] - a[2]) * q, s)
            return keys[-1][1:]

        dur = cfg['duration']
        e0, e1 = cfg['end']
        tilt = cfg.get('tilt', 1.4)

        async def draw(t):
            cx, cy, s = cam(t)
            pin = min(1, t / tilt)
            q = ease(pin)
            rx, ry, z, op = 22 * (1 - q), -16 * (1 - q), -260 * (1 - q), min(1, t / 0.5)
            await pg.evaluate(f"""(()=>{{const c=document.getElementById('cam');
             c.style.transform='translate({W/2 - cx*s}px,{H/2 - cy*s}px) scale({s}) translateZ({z}px) rotateX({rx}deg) rotateY({ry}deg)';
             c.style.opacity={op};document.getElementById('end').style.opacity={ease(min(1,max(0,(t-e0)/(e1-e0))))};
             document.getElementById('persp').style.opacity={1-ease(min(1,max(0,(t-e0)/(e1-e0))))};}})()""")
            await f.evaluate(f'window.__frame({t})')

        if frames:
            for t in frames:
                await draw(t)
                await pg.screenshot(path=str(work / f'still-{t:05.2f}.jpg'), type='jpeg', quality=92)
                print('still', t)
        else:
            tmp = str(out) + '.part.mp4'
            ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'image2pipe', '-framerate', str(FPS), '-c:v', 'mjpeg', '-i', '-',
                                   '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', tmp],
                                  stdin=subprocess.PIPE)
            n = int(dur * FPS)
            for i in range(n):
                await draw(i / FPS)
                ff.stdin.write(await pg.screenshot(type='jpeg', quality=92))
            ff.stdin.close()
            if ff.wait() == 0:
                pathlib.Path(tmp).rename(out)
                print('wrote', out, n, 'frames')
        await b.close()
    srv.shutdown()
    (d / 'screen.rendered.html').unlink()


if __name__ == '__main__':
    a = sys.argv[1:]
    fr = None
    if '--frames' in a:
        i = a.index('--frames'); fr = [float(x) for x in a[i + 1].split(',')]; a = a[:i] + a[i + 2:]
    asyncio.run(main(a[0], pathlib.Path(a[1]).resolve() if len(a) > 1 else None, fr))
