"""Build 'Our City' for the Banpo Pigeon engine.

Takes the original Banpo Pigeon game (same bird, flying, landing, walking, controls)
and swaps its Seoul map for the class's city (city.json from build_city.py).

usage: python3 make_pigeon_city.py ORIGINAL.html city.json OUT.html
"""
import json, math, sys, random

src, city_path, out = sys.argv[1:4]
s = open(src, encoding='utf-8').read()
C = json.load(open(city_path))
random.seed(67)

TAG = '<script type="application/json" id="city">'
i = s.index(TAG); j = s.index('</script>', i)

FLOOR = 3.2
def rect(x, z, w, d, inset=0.0):
    x0, z0, x1, z1 = x + inset, z + inset, x + w - inset, z + d - inset
    return [x0, z0, x0, z1, x1, z1, x1, z0]   # counter-clockwise in (x,z) like the original data
def ccw(p):
    a = sum(p[k] * p[(k + 3) % len(p)] - p[(k + 2) % len(p)] * p[k + 1] for k in range(0, len(p), 2))
    if a < 0:
        q = [(p[k], p[k + 1]) for k in range(0, len(p), 2)][::-1]; p = [v for xy in q for v in xy]
    return [round(v, 1) for v in p]
def ellipse(cx, cz, rx, rz, n=28):
    return ccw([v for t in range(n) for v in (cx + rx * math.cos(2 * math.pi * t / n), cz + rz * math.sin(2 * math.pi * t / n))])
def hexcol(c, default=0xc9cdd2):
    return int(c.lstrip('#'), 16) if c else default
def snack_kind(n):
    n = (n or '').lower()
    if any(k in n for k in ('coffee', 'cafe', 'caf', 'tea', 'juice', 'milk')): return 'cafe'
    if any(k in n for k in ('bake', 'bread', 'cake', 'pie', 'donut', 'cookie', 'croissant', 'muffin', 'dessert', 'sweet', 'candy', 'ice')): return 'bakery'
    return 'convenience'

TX, TZ = C['tower']
import re
STYLES = [  # (pattern, background, text colour) -- first match wins
    (r'bank|money', '#d4a017', '#1e2a33'),
    (r'school|wca|kids', '#1f3a93', '#ffd23c'),
    (r'station|train', '#0a7bd0', '#ffffff'),
    (r'gs25', '#00a6d6', '#ffffff'),
    (r'coffee|cafe|caf', '#6f4e37', '#fff3d6'),
    (r'cake|bake|bread|pie|donut|mochi', '#ff8fb1', '#ffffff'),
    (r'zoo|pet|cat shop', '#f39c12', '#1e2a33'),
    (r'pizza|food|hot ?dog|kimchi|pasta|spicy|yum|fish|cheese|restaurant|court|burger', '#d63031', '#ffffff'),
    (r'mart|market|store|shop', '#2e9e5b', '#ffffff'),
    (r'car', '#4a5560', '#ffffff'),
    (r'power|nuclear', '#ffd23c', '#1e2a33'),
    (r'bathroom|toilet', '#e8f4ff', '#1f3a93'),
]
def sign_style(n):
    for pat, bg, fg in STYLES:
        if re.search(pat, n, re.I): return bg, fg
    return '#ffffff', '#1e2a33'
segs = []
for r in C['roads']:
    for a in range(1, len(r['pts'])): segs.append((r['pts'][a - 1], r['pts'][a], r['w'] / 2))
def road_dist(x, z):
    best = 1e9
    for (ax, az), (bx, bz), hw in segs:
        dx, dz = bx - ax, bz - az; L = dx * dx + dz * dz or 1
        t = max(0, min(1, ((x - ax) * dx + (z - az) * dz) / L))
        best = min(best, math.hypot(x - ax - dx * t, z - az - dz * t) - hw)
    best = min(best, abs(math.hypot(x - TX, z - TZ) - C['rr']) - C['mainw'] / 2)
    return best
def best_side(x, z, w, d):
    """side of the rect that faces the nearest road: (mid x, mid z, outward nx, nz, side length)"""
    sides = [(x + w / 2, z, 0, -1, w), (x + w / 2, z + d, 0, 1, w), (x, z + d / 2, -1, 0, d), (x + w, z + d / 2, 1, 0, d)]
    def score(S):
        px, pz = S[0] + S[2] * 4, S[1] + S[3] * 4
        blocked = any(it['k'] in ('b', 's') and it['x'] < px < it['x'] + it['w'] and it['z'] < pz < it['z'] + it['d'] for it in C['items'])
        return road_dist(S[0] + S[2] * 5, S[1] + S[3] * 5) + (1000 if blocked else 0)
    return min(sides, key=score)
signs, parksigns = [], []

buildings = [[128.0, 1, 5, 4, ccw(rect(TX - 9, TZ - 9, 18, 18)), '', 0x5b6b7a, 1, 0]]   # g=1: flat clean roof to start on   # index 0 = Start Tower (the nest)
areas, trees, snacks, solids, deco = [], [], [], [], []

for it in C['items']:
    k, x, z, w, d, f, c, n = (it[q] for q in 'kxzwdfcn')
    cx, cz = x + w / 2, z + d / 2
    if k in ('b', 's'):
        h = max(1, f) * FLOOR
        style = 2 if k == 's' else (3 if f <= 3 else 6)
        pitched = 1 if (k == 'b' and f <= 3 and not n) else 0
        buildings.append([round(h, 1), 0, 5, style, ccw(rect(x, z, w, d, .6)), n or '', hexcol(c), 1 if k == 's' else 0, pitched])
        if n and n not in ('House', 'Apartment'):
            mx, mz, nx, nz, L = best_side(x + .6, z + .6, w - 1.2, d - 1.2)
            bg, fg = sign_style(n)
            sw = round(max(2.5, min(L - .8, 9, 1.6 + .55 * len(n))), 1)
            signs.append([round(mx + nx * .02, 2), round(mz + nz * .02, 2), round(math.atan2(nx, nz), 3), 0, sw, bg, fg, n, 'SH'])
        if k == 's':
            snacks.append([snack_kind(n), n or 'Shop', round(cx, 1), round(z + d + 3, 1)])
    elif k in ('p', 'g', 'f'):
        areas.append([2 if k == 'f' else 0, ccw(rect(x, z, w, d))])
        if k != 'f':
            for _ in range(max(1, round(w * d / (45 if k == 'p' else 120)))):
                trees.append([round(x + 2 + random.random() * (w - 4), 1), round(z + 2 + random.random() * (d - 4), 1)])
        deco.append([k, x, z, w, d, c, n])
        if n:
            mx, mz, nx, nz, L = best_side(x, z, w, d)
            parksigns.append([round(mx - nx * 1.5, 1), round(mz - nz * 1.5, 1), round(math.atan2(nx, nz), 3), n])
    elif k in ('raccoon', 'cat', 'L67', 'LOL'):
        deco.append([k, x, z, w, d, c, n])
        h = {'raccoon': 34, 'cat': 34, 'L67': 22, 'LOL': 22}[k]
        m = min(w, d) / 26 if k in ('raccoon', 'cat') else 1
        r = (13 * max(.7, m)) if k in ('raccoon', 'cat') else None
        if r: solids.append([cx - r, cz - r, cx + r, cz + r, h * max(.7, m)])
        else: solids.append([x + 1, z + 1, x + w - 1, z + d - 1, h])
    elif k in ('dock', 'bridge'):
        deco.append([k, x, z, w, d, c, n, f])

# water
for px, pz, rx, rz in C['ponds']:
    areas.append([1, ellipse(px, pz, rx, rz)])
for st in C['streams']:
    L, R = [], []
    for a in range(len(st)):
        p0, p1 = st[max(0, a - 1)], st[min(len(st) - 1, a + 1)]
        dx, dz = p1[0] - p0[0], p1[1] - p0[1]; l = math.hypot(dx, dz) or 1
        nx, nz = -dz / l * 3, dx / l * 3
        L.append((st[a][0] + nx, st[a][1] + nz)); R.append((st[a][0] - nx, st[a][1] - nz))
    areas.append([1, ccw([v for p in L + R[::-1] for v in p])])
# grass island inside the roundabout
areas.append([0, ellipse(TX, TZ, C['rr'] - C['mainw'] / 2 - 1, C['rr'] - C['mainw'] / 2 - 1)])

# roads: [width, major, flat pts, name, oneway, lanes]
roads = []
NAMES = ['North Road', 'South Road', 'West Road', 'East Road', 'Tower Road', 'Ring Road']
mi = 0
for r in C['roads']:
    flat = [round(v, 1) for p in r['pts'] for v in p]
    # drop repeated points
    pts = []
    for a in range(0, len(flat), 2):
        if not pts or math.hypot(flat[a] - pts[-2], flat[a + 1] - pts[-1]) > .3: pts += flat[a:a + 2]
    if r['main']:
        roads.append([r['w'], 1, pts, NAMES[mi % len(NAMES)], 0, 2]); mi += 1
    else:
        roads.append([r['w'], 0, pts, 'Lane', 0, 1])
ring = []
for t in range(49):
    a = 2 * math.pi * t / 48; ring += [round(TX + C['rr'] * math.cos(a), 1), round(TZ + C['rr'] * math.sin(a), 1)]
roads.append([C['mainw'], 1, ring, 'Roundabout', 0, 2])

# street trees along the lanes (kept off buildings by the engine's own check when walking)
terrain = {'x0': -700, 'z0': -700, 'step': 20, 'nx': 101, 'nz': 91, 'dm': [0] * (101 * 91)}
city = {'home': -1, 'bounds': [-40.0, -40.0, 640.0, 460.0], 'buildings': buildings, 'roads': roads, 'areas': areas,
        'rails': [], 'stations': [], 'snacks': snacks, 'signs': signs, 'trees': trees, 'crosswalks': [], 'dong': [],
        'billboards': [], 'terrain': terrain, 'parksigns': parksigns, 'solids': solids, 'deco': deco}
s = s[:i + len(TAG)] + json.dumps(city, ensure_ascii=False, separators=(',', ':')) + s[j:]

# ---------- engine patches ----------
def rep(a, b, count=1):
    global s
    n = s.count(a)
    assert n == count, (a[:70], n)
    s = s.replace(a, b)

# no Seoul underpasses
rep('var Ko=null,Er=[[[-441,-98.4],[-440.5,-94.4],[-475.9,-58.5],[-477.9,-56.5]],[[-478.5,-37.3],[-473,-34.5],[-431,-46.4],[-425.7,-47.4]]]', 'var Ko=null,Er=[]')
# light grassy ground instead of grey city ground
rep('let i=new Ft({color:9407881}),t=(o,a,c,l,f,h)=>', 'let i=new Ft({color:12245655}),t=(o,a,c,l,f,h)=>')
# statues, goals, dock + their collision boxes
STATUES = r'''
{const T={Mesh:Dt,Group:we,Box:Bt,Cyl:ce,Cone:Ho,Sph:Le,Ext:Is,Shape:zi,Path:zo,Mat:Ft};const M={};const mat=c=>M[c]||(M[c]=new T.Mat({color:new Pt(c)}));
for(const[x0,z0,x1,z1,h]of ie.solids||[]){const a=Math.max(0,Math.floor((x0-Yt)/Zt)),b=Math.min(fe-1,Math.floor((x1-Yt)/Zt)),c=Math.max(0,Math.floor((z0-jt)/Zt)),d=Math.min(Ke-1,Math.floor((z1-jt)/Zt));for(let zz=c;zz<=d;zz++)for(let xx=a;xx<=b;xx++){const q=zz*fe+xx;$i[q]<h&&($i[q]=h,ha[q]=0)}}
const box=(w,h,d,c,x,y,z,g)=>{const m=new T.Mesh(new T.Box(w,h,d),mat(c));m.position.set(x,y,z);(g||$t).add(m);return m};
function animal(x,z,w,d,o){const g=new T.Group(),S=Math.min(w,d)/26;const add=(geo,c,px,py,pz,sx=1,sy=1,sz=1)=>{const m=new T.Mesh(geo,mat(c));m.position.set(px,py,pz);m.scale.set(sx,sy,sz);g.add(m);return m};
add(new T.Box(26,3,26),'#cfc8b8',0,1.5,0);add(new T.Sph(8,24,18),o.body,0,13,0,1,1.25,.9);add(new T.Sph(4.2,18,14),o.belly,0,11,6.2,1,1.3,.5);add(new T.Sph(7,24,18),o.body,0,26,1);add(new T.Sph(3.4,16,12),o.belly,0,24.2,6.8,1.2,.8,.8);add(new T.Sph(1.1,12,10),o.nose,0,25,9.4);
[-1,1].forEach(s=>{if(o.mask)add(new T.Sph(2.6,16,12),'#1e2124',s*3,27,5.4,1.2,.8,.6);add(new T.Sph(1,12,10),o.mask?'#ffffff':'#9be36b',s*3,27.3,6.8);add(new T.Sph(.5,10,8),'#1e2124',s*3,27.3,7.7);const ear=add(new T.Cone(2.4,o.mask?4.5:6,o.mask?14:4),o.body,s*4.6,32.5,0);ear.rotation.z=-s*.35});
for(let i=0;i<6;i++)add(new T.Sph(2.6-i*.15,14,10),o.stripes&&i%2?'#1e2124':o.body,4+i*1.6,6+i*2.6,-8-Math.sin(i*.6)*3);
g.scale.setScalar(Math.max(.7,S));g.position.set(x+w/2,0,z+d/2);g.rotation.y=.7;$t.add(g)}
const shp=p=>{const s=new T.Shape();s.moveTo(...p[0]);p.slice(1).forEach(q=>s.lineTo(...q));return s};
const ring=(cx,cy,r1,r2)=>{const s=new T.Shape();s.absarc(cx,cy,r2,0,Math.PI*2);const h=new T.Path();h.absarc(cx,cy,r1,0,Math.PI*2,!0);s.holes.push(h);return s};
const SIX=[ring(4.5,5,2.2,4.5),shp([[.2,5],[2.4,5],[6,15],[3.6,15.6]])],SEVEN=shp([[0,13],[9,13],[9,11.4],[4.2,0],[1.6,0],[6.2,11],[0,11]]),ELL=shp([[0,0],[8,0],[8,2.6],[2.6,2.6],[2.6,14],[0,14]]),OH=ring(4.5,7,2.6,5.6);
function letters(x,z,w,d,parts){const g=new T.Group();box(Math.max(w,8),2,Math.max(d,6),'#cfc8b8',0,1,0,g);const step=11,st=-(parts.length-1)*step/2;
parts.forEach(([sh,c],i)=>{const m=new T.Mesh(new T.Ext(sh,{depth:3,bevelEnabled:!0,bevelSize:.4,bevelThickness:.4,bevelSegments:2}),mat(c));m.position.set(st+i*step-4.5,2,-1.5);g.add(m)});
const sc=Math.min(1.2,Math.max(.6,w/(parts.length*11)));g.scale.set(sc,sc*1.3,sc);g.position.set(x+w/2,0,z+d/2);g.rotation.y=-.5;$t.add(g)}
for(const[k,x,z,w,d,c,n,f]of ie.deco||[]){const cx=x+w/2,cz=z+d/2;
if(k==='raccoon')animal(x,z,w,d,{body:'#8e959c',belly:'#e9e6e0',nose:'#1e2124',mask:!0,stripes:!0});
else if(k==='cat')animal(x,z,w,d,{body:'#f2a65a',belly:'#fff1dc',nose:'#f27a8a',mask:!1,stripes:!1});
else if(k==='L67')letters(x,z,w,d,[[SIX,'#8fd8ff'],[SEVEN,'#ff9acd']]);
else if(k==='LOL')letters(x,z,w,d,[[ELL,'#ffd23c'],[OH,'#ff7a5a'],[ELL,'#7fc8ff']]);
else if(k==='f'){const L=(a,b,X,Z)=>box(a,.06,b,'#ffffff',X,.13,Z);L(w-4,.5,cx,z+2);L(w-4,.5,cx,z+d-2);L(.5,d-4,x+2,cz);L(.5,d-4,x+w-2,cz);w>d?L(.5,d-4,cx,cz):L(w-4,.5,cx,cz);const lg=w>d;[-1,1].forEach(s=>{const gx=lg?cx+s*(w/2-2.5):cx,gz=lg?cz:cz+s*(d/2-2.5);box(lg?.3:7,.3,lg?7:.3,'#ffffff',gx,2.4,gz);for(const o of[-3.4,3.4])box(.3,2.4,.3,'#ffffff',lg?gx:gx+o,1.2,lg?gz+o:gz)})}
else if(k==='g'){for(let q=0;q<w*d/6;q++){const fl=new T.Mesh(new T.Sph(.5,8,6),mat(c||'#e8463c'));fl.position.set(x+1+Wt(q+x)*(w-2),.4,z+1+Wt(q*7+z)*(d-2));$t.add(fl)}}
else if(k==='dock'){box(w,.6,d,'#8a5a3a',cx,.5,cz)}
}
for(const[x,z,r,n]of ie.parksigns||[]){const g=new T.Group();g.position.set(x,0,z);g.rotation.y=r;$t.add(g);
for(const o of[-2.1,2.1]){const p=new T.Mesh(new T.Cyl(.12,.12,2.7,8),mat('#7a4f2c'));p.position.set(o,1.35,0);g.add(p)}
box(4.8,1.5,.16,'#2f7d3a',0,2,0,g);box(5,.14,.3,'#7a4f2c',0,2.82,0,g);
const cv=document.createElement('canvas');cv.width=512;cv.height=160;const x2=cv.getContext('2d');x2.fillStyle='#2f7d3a';x2.fillRect(0,0,512,160);x2.strokeStyle='#ffe9a8';x2.lineWidth=8;x2.strokeRect(10,10,492,140);
x2.fillStyle='#ffffff';x2.textAlign='center';x2.textBaseline='middle';let fs=86;x2.font='bold '+fs+'px sans-serif';while(x2.measureText(n).width>460&&fs>30){fs-=4;x2.font='bold '+fs+'px sans-serif'}x2.fillText(n,256,84);
const tx=new Pe(cv);tx.colorSpace=me;const tm=new Be({map:tx});for(const s of[1,-1]){const pl=new T.Mesh(new Hn(4.6,1.4),tm);pl.position.set(0,2,s*.09);s<0&&(pl.rotation.y=Math.PI);g.add(pl)}}
}
'''
rep('var ff=new Float32Array(fe*Ke);', STATUES + 'var ff=new Float32Array(fe*Ke);')

# keep the bird over OUR city: turn back toward the city centre (not 0,0) and face the city at the start
rep('Math.atan2(-F.x,-F.z)', 'Math.atan2((Yt+gn)/2-F.x,(jt+bn)/2-F.z)', 2)
rep('yaw:Math.PI*.75}', 'yaw:1.75}')
# no low wall (parapet) around the roof edges, so you can see out when standing on a roof
rep('H=!L&&p>6&&g<1?p>30?1.3:.9:0', 'H=0')
# land in water -> "Wet bird!" + splash sound
WET = r"""var WATER=ie.areas.filter(a=>a[0]===1).map(a=>a[1]);function isWet(x,z){for(const p of WATER){let c=!1;for(let a=0,b=p.length-2;a<p.length;b=a,a+=2){const xa=p[a],za=p[a+1],xb=p[b],zb=p[b+1];za>z!=zb>z&&x<(xb-xa)*(z-za)/(zb-za)+xa&&(c=!c)}if(c)return!0}return!1}
function splashSound(){let i=eh();if(!i||vr)return;let t=i.currentTime,n=Math.floor(i.sampleRate*.5),bf=i.createBuffer(1,n,i.sampleRate),d=bf.getChannelData(0);for(let k=0;k<n;k++)d[k]=(Math.random()*2-1)*Math.pow(1-k/n,2.5);let src=i.createBufferSource();src.buffer=bf;let f=i.createBiquadFilter();f.type="lowpass";f.frequency.setValueAtTime(2600,t);f.frequency.exponentialRampToValueAtTime(400,t+.45);let g=i.createGain();g.gain.setValueAtTime(.55,t);g.gain.exponentialRampToValueAtTime(.001,t+.5);src.connect(f);f.connect(g);g.connect(i.destination);src.start(t);
for(let k=0;k<5;k++){let s0=t+.08+k*.07+Math.random()*.04,o=i.createOscillator(),gg=i.createGain(),f0=700+Math.random()*900;o.type="sine";o.frequency.setValueAtTime(f0,s0);o.frequency.exponentialRampToValueAtTime(f0*1.9,s0+.06);gg.gain.setValueAtTime(.12,s0);gg.gain.exponentialRampToValueAtTime(.001,s0+.08);o.connect(gg);gg.connect(i.destination);o.start(s0);o.stop(s0+.1)}}
"""
rep('function d_(){', WET + 'function d_(){')
rep('F.bank=Vn(F.bank,F.grounded?0:s*.55,5,i)', '(()=>{if(F.grounded){const w=isWet(F.x,F.z);w&&!F.wet&&(xn("\\u{1F4A6} Wet bird! \\u{1F4A6}"),splashSound());F.wet=w}else F.wet=!1})(),F.bank=Vn(F.bank,F.grounded?0:s*.55,5,i)')
# words on the screens
rep('<title>Banpo Pigeon · Seocho Person</title>', '<title>Our City · Pigeon</title>')
rep('Building the neighbourhood…', 'Building Our City…')
rep('<div class="ko">Sinsa → Gangnam, Seoul</div>', '<div class="ko">Our City · designed by our class</div>', 2)
rep('Take off from the roof of Urban Hive and fly over the real streets of Banpo, Nonhyeon and Gangnam. Collect 🍜 ☕ 🥐 outside real shops.',
    'Take off from the top of the Start Tower and fly over the city our class designed. Land anywhere and waddle around! Collect 🍜 ☕ 🥐 outside the shops.')
rep('Start at Urban Hive and explore the real streets of Banpo, Nonhyeon and Gangnam on foot. Collect 🍜 ☕ 🥐 outside real shops.',
    'Start next to the Start Tower and explore the city our class designed on foot. Collect 🍜 ☕ 🥐 outside the shops.')
rep('<div style="margin-top:12px;font-size:11px;color:#6b7785">Map © OpenStreetMap contributors · Places: Kakao Map · Building data: VWorld</div>', '', 2)
rep('<div id="credit" style="position:absolute;bottom:2px;left:50%;transform:translateX(-50%);font-size:10px;color:rgba(30,40,50,0.7);white-space:nowrap">© OpenStreetMap · Kakao Map · VWorld</div>', '')
rep('"\\u{1F3E2} Urban Hive (start)"', '"\\u{1F3E2} Start Tower"')
open(out, 'w', encoding='utf-8').write(s)
print('ok', len(buildings), 'buildings', len(snacks), 'snacks', len(roads), 'roads', len(areas), 'areas', len(trees), 'trees')
