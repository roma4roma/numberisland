"""Our City 3D viewer: the Pigeon Pigeon city (same engine, same buildings, cars, people, animals) with a spin-around camera.
usage: python3 make_city_viewer.py OUR_CITY_PIGEON.html OUT.html
OUR_CITY_PIGEON.html = output of make_pigeon_city.py run on the original Banpo Pigeon file (no math patch)."""
import sys
src, out = sys.argv[1:3]
BIG = '--big' in sys.argv   # the city with the ring + countryside: see further, more trees
s = open(src, encoding='utf-8').read()

CSS = """<style>
#title,#hud,#fps{display:none!important}
#vw{position:fixed;inset:0;z-index:50;touch-action:none;cursor:grab}
#vw:active{cursor:grabbing}
#vwTop{position:fixed;top:12px;left:12px;z-index:60;font:800 20px system-ui,sans-serif;color:#1e2a33;background:#fffd;border:3px solid #1e2a33;border-radius:14px;padding:6px 14px;box-shadow:0 3px 0 #1e2a33}
#vwTop small{display:block;font-weight:600;font-size:12px;color:#4a5560}
#vwHelp{position:fixed;top:12px;right:12px;z-index:60;font:600 12px system-ui,sans-serif;color:#1e2a33;background:#fffd;border-radius:10px;padding:6px 10px;text-align:right}
</style>"""
HTML = """<div id="vw"></div>
<div id="vwTop">RomaCity · 3D<small>designed by Mr. Romanek's Grade 4</small></div>
<div id="vwHelp">Drag to spin · pinch or scroll to zoom<br>Two fingers or right-drag to move · H hides this</div>

<script>
(()=>{const C={x:300,z:210};const S={yaw:.6,pitch:.62,dist:520,tx:C.x,tz:C.z,ty:10,spin:!0};const home={...S};
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
function cam(){const cp=Math.cos(S.pitch);window.__cam={p:[S.tx+Math.sin(S.yaw)*cp*S.dist,S.ty+Math.sin(S.pitch)*S.dist,S.tz+Math.cos(S.yaw)*cp*S.dist],l:[S.tx,S.ty,S.tz]}}
let last=performance.now(),lastTouch=0;const pts=new Map();(function tick(t){const dt=Math.min(.05,(t-last)/1e3);last=t;if(!S.spin&&pts.size===0&&t-lastTouch>6000)S.spin=!0;if(S.spin)S.yaw+=dt*.12;cam();requestAnimationFrame(tick)})(last);
const el=document.getElementById('vw');let pinch0=0,mid0=null;
const pan=(dx,dy)=>{const k=S.dist/700,sy=Math.sin(S.yaw),cy=Math.cos(S.yaw);S.tx=clamp(S.tx-cy*dx*k-sy*dy*k,-50,650);S.tz=clamp(S.tz+sy*dx*k-cy*dy*k,-50,470)};
el.addEventListener('contextmenu',e=>e.preventDefault());
el.addEventListener('pointerdown',e=>{el.setPointerCapture(e.pointerId);pts.set(e.pointerId,{x:e.clientX,y:e.clientY,b:e.button});S.spin=!1;lastTouch=performance.now();if(pts.size===2){const[a,b]=[...pts.values()];pinch0=Math.hypot(a.x-b.x,a.y-b.y);mid0={x:(a.x+b.x)/2,y:(a.y+b.y)/2}}});
el.addEventListener('pointermove',e=>{const p=pts.get(e.pointerId);if(!p)return;lastTouch=performance.now();const dx=e.clientX-p.x,dy=e.clientY-p.y;
if(pts.size===1){if(p.b===2||e.shiftKey)pan(dx,dy);else{S.yaw-=dx*.006;S.pitch=clamp(S.pitch+dy*.005,.06,1.5)}p.x=e.clientX;p.y=e.clientY}
else if(pts.size===2){p.x=e.clientX;p.y=e.clientY;const[a,b]=[...pts.values()];const d=Math.hypot(a.x-b.x,a.y-b.y),m={x:(a.x+b.x)/2,y:(a.y+b.y)/2};if(pinch0){S.dist=clamp(S.dist*pinch0/d,25,900);pinch0=d}if(mid0){pan(m.x-mid0.x,m.y-mid0.y);mid0=m}}});
const up=e=>{pts.delete(e.pointerId);pinch0=0;mid0=null;if(pts.size===2){const[a,b]=[...pts.values()];pinch0=Math.hypot(a.x-b.x,a.y-b.y)}};
el.addEventListener('pointerup',up);el.addEventListener('pointercancel',up);
el.addEventListener('wheel',e=>{e.preventDefault();lastTouch=performance.now();S.spin=!1;S.dist=clamp(S.dist*Math.exp(e.deltaY*.0012),25,900)},{passive:!1});
addEventListener('keydown',e=>{const k=e.key;S.spin=k===' '?S.spin:!1;if(k==='ArrowLeft')S.yaw+=.08;else if(k==='ArrowRight')S.yaw-=.08;else if(k==='ArrowUp')S.pitch=clamp(S.pitch+.06,.06,1.5);else if(k==='ArrowDown')S.pitch=clamp(S.pitch-.06,.06,1.5);else if(k==='+'||k==='=')S.dist=clamp(S.dist*.85,25,900);else if(k==='-')S.dist=clamp(S.dist/.85,25,900);else if(k===' ')S.spin=!S.spin;else if(k==='h'||k==='H'){const v=document.getElementById('vwHelp'),t=document.getElementById('vwTop');v.hidden=t.hidden=!v.hidden}else return;lastTouch=performance.now();e.preventDefault()});
})();
</script>"""
assert s.count('</style>') >= 1 and s.count('</body>') == 1
s = s.replace('</body>', HTML + '\n</body>')
i = s.index('</style>') + len('</style>')
s = s[:i] + CSS + s[i:]
s = s.replace('<title>Pigeon Pigeon</title>', '<title>RomaCity · 3D</title>')
if BIG:
    for a, b in [('$t.fog=new Co(cf,260,1e3)', '$t.fog=new Co(cf,1500,4200)'), ('ue=new tn(65,1,.15,1500)', 'ue=new tn(65,1,.5,7000)'),
                 ('let p=330*330,g=0;', 'let p=2600*2600,g=0;'), ('t=6000,e=new ce(.18,.25,4,5,1,!0)', 't=12000,e=new ce(.18,.25,4,5,1,!0)')]:
        assert s.count(a) == 1, a
        s = s.replace(a, b)
    s = s.replace("const S={yaw:.6,pitch:.62,dist:520,", "const S={yaw:.6,pitch:.66,dist:1350,")
    s = s.replace(",25,900)", ",25,2600)").replace("clamp(S.tx-cy*dx*k-sy*dy*k,-50,650)", "clamp(S.tx-cy*dx*k-sy*dy*k,-450,1050)").replace("clamp(S.tz+sy*dx*k-cy*dy*k,-50,470)", "clamp(S.tz+sy*dx*k-cy*dy*k,-350,780)")
open(out, 'w', encoding='utf-8').write(s)
print('ok')
