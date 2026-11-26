"""Build 'Our City' for the Banpo Pigeon engine.

Takes the original Banpo Pigeon game (same bird, flying, landing, walking, controls)
and swaps its Seoul map for the class's city (city.json from build_city.py).

usage: python3 make_pigeon_city.py ORIGINAL.html city.json OUT.html
"""
import json, math, sys, random

src, city_path, out = sys.argv[1:4]
SNACK_SPACING = 30   # metres between snacks in the Math Island version (the original Banpo build used 80)
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
    if any(k in n for k in ('bake', 'bread', 'cake', 'pie', 'donut', 'cookie', 'croissant', 'muffin', 'dessert', 'sweet', 'candy', 'ice', 'baskin', 'baguette')): return 'bakery'
    return 'convenience'

TX, TZ = C['tower']
import re
STYLES = [  # (pattern, background, text colour) -- first match wins
    (r'bank|money', '#d4a017', '#1e2a33'),
    (r'airport', '#1f3a93', '#ffffff'),
    (r'hospital', '#ffffff', '#e8282d'),
    (r'hotel', '#3b3f6b', '#ffd98a'),
    (r'movie|theat', '#1e1e2e', '#ffd23c'),
    (r'barber', '#ffffff', '#d63031'),
    (r'^cu$', '#7b4fc0', '#b8f070'),
    (r'baskin', '#ff5ca8', '#ffffff'),
    (r'7-eleven', '#ffffff', '#e8582c'),
    (r'phone|tablet', '#2b2f36', '#7fd8ff'),
    (r'decorat', '#f5a3d0', '#ffffff'),
    (r'rent', '#4a5560', '#ffd23c'),
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
# sky bridges between buildings you can fly under: [x0, z0, x1, z1 (the open gap), bottom, top, colour]
SKYBRIDGES = [
    [59.4, 381, 70.6, 389, 12.8, 16.0, '#9cc3dd'],   # C1: 10-storey tower <-> Cake Cake
]
# ...plus every sky bridge the students drew ('bridge' items): span the gap between the two buildings at its ends
for it in C['items']:
    if it['k'] != 'bridge': continue
    x, z, w, d, f = it['x'], it['z'], it['w'], it['d'], it['f']
    lo, hi = (f - 1) * FLOOR, f * FLOOR
    along_x = w >= d
    c0, c1 = (x, x + w) if along_x else (z, z + d)
    mid = (c0 + c1) / 2
    ends = []
    for o in C['items']:
        if o['k'] not in ('b', 's') or o['s'] != it['s']: continue
        a0, a1 = (o['x'] + .6, o['x'] + o['w'] - .6) if along_x else (o['z'] + .6, o['z'] + o['d'] - .6)
        b0, b1 = (o['z'], o['z'] + o['d']) if along_x else (o['x'], o['x'] + o['w'])
        q0, q1 = (z, z + d) if along_x else (x, x + w)
        if a1 > c0 - 1 and a0 < c1 + 1 and b1 > q0 and b0 < q1: ends.append((a0, a1))
    left = max([a1 for a0, a1 in ends if a1 <= mid] or [c0]); right = min([a0 for a0, a1 in ends if a0 >= mid] or [c1])
    cc = (z + d / 2) if along_x else (x + w / 2); half = max(2, min(4, d / 2 - .5 if along_x else w / 2 - .5))
    SKYBRIDGES.append([left, cc - half, right, cc + half, lo, hi, '#9cc3dd'] if along_x else [cc - half, left, cc + half, right, lo, hi, '#9cc3dd'])
print('sky bridges:', SKYBRIDGES)
# living things: soccer players on every soccer field, pigeons in Pigeon Park, an elephant walking round each zoo
CRITTERS = []
for it in C['items']:
    n = (it['n'] or '').lower()
    if it['k'] == 'f': CRITTERS.append(['soccer', it['x'], it['z'], it['w'], it['d']])
    elif it['k'] in ('p', 'g') and 'pigeon' in n: CRITTERS.append(['pigeons', it['x'], it['z'], it['w'], it['d']])
    elif it['k'] in ('b', 's') and re.search(r'\bzoo\b', n): CRITTERS.append(['elephant', it['x'], it['z'], it['w'], it['d']])
print('critters:', [c[0] for c in CRITTERS])
AIR = [it for it in C['items'] if 'airport' in (it['n'] or '').lower()]
PLANES = []
if AIR:
    ax0 = min(i['x'] for i in AIR) + .6; ax1 = max(i['x'] + i['w'] for i in AIR) - .6
    az0 = min(i['z'] for i in AIR) + .6; az1 = max(i['z'] + i['d'] for i in AIR) - .6
    roof = max(i['f'] for i in AIR) * FLOOR
    along_z = (az1 - az0) >= (ax1 - ax0)
    # the narrowest part of the roof decides where the plane can sit
    cx = (max(i['x'] for i in AIR) + min(i['x'] + i['w'] for i in AIR)) / 2 if along_z else (ax0 + ax1) / 2
    cx = (min(i['x'] for i in AIR) + min(i['x'] + i['w'] for i in AIR)) / 2 if along_z else cx
    cz = (az0 + az1) / 2
    PLANES.append([round(cx, 1), round(cz, 1), roof, 1 if along_z else 0, round(ax0, 1), round(az0, 1), round(ax1, 1), round(az1, 1)])
print('planes:', PLANES)

buildings = [[128.0, 1, 5, 4, ccw(rect(TX - 9, TZ - 9, 18, 18)), '', 0x5b6b7a, 1, 0]]   # g=1: flat clean roof to start on   # index 0 = Start Tower (the nest)
areas, trees, snacks, solids, deco = [], [], [], [], []

for it in C['items']:
    k, x, z, w, d, f, c, n = (it[q] for q in 'kxzwdfcn')
    cx, cz = x + w / 2, z + d / 2
    if k in ('b', 's'):
        h = max(1, f) * FLOOR
        style = 2 if k == 's' else (3 if f <= 3 else 6)
        pitched = 1 if (k == 'b' and f <= 3 and not n) else 0
        clean = 1 if 'airport' in (n or '').lower() else 0   # g=1: no rooftop boxes (the plane needs a clear roof)
        mx, mz, nx, nz, L = best_side(x + .6, z + .6, w - 1.2, d - 1.2)   # the front door side (faces the nearest road)
        if re.fullmatch(r'\s*barn\s*', n or '', re.I):   # a real barn: red walls, white trim, curved (gambrel) roof, silo
            deco.append(['barn', x, z, w, d, c, n, round(math.atan2(nx, nz), 3)])
            solids.append([x + .6, z + .6, x + w - .6, z + d - .6, max(9, h * .75)])
        else:
            if re.search(r'disco', n or '', re.I): deco.append(['discoball', x, z, w, d, c, n, round(h, 1)])
            buildings.append([round(h, 1), clean, 5, style, ccw(rect(x, z, w, d, .6)), n or '', hexcol(c), 1 if (k == 's' or clean) else 0, pitched])
        if n and n not in ('House', 'Apartment'):
            bg, fg = sign_style(n)
            sw = round(max(2.5, min(L - .8, 9, 1.6 + .55 * len(n))), 1)
            signs.append([round(mx + nx * .02, 2), round(mz + nz * .02, 2), round(math.atan2(nx, nz), 3), 0, sw, bg, fg, n, 'SH'])
        if k == 's':
            snacks.append([snack_kind(n), n or 'Shop', round(mx + nx * 2.5, 1), round(mz + nz * 2.5, 1)])   # by the entrance, under the sign
    elif k in ('p', 'g', 'f'):
        areas.append([2 if k == 'f' else 0, ccw(rect(x, z, w, d))])
        if k != 'f':
            for _ in range(max(1, round(w * d / (45 if k == 'p' else 120)))):
                trees.append([round(x + 2 + random.random() * (w - 4), 1), round(z + 2 + random.random() * (d - 4), 1)])
        deco.append([k, x, z, w, d, c, n])
        if n:
            mx, mz, nx, nz, L = best_side(x, z, w, d)
            parksigns.append([round(mx - nx * 1.5, 1), round(mz - nz * 1.5, 1), round(math.atan2(nx, nz), 3), n])
    elif k in ('pool', 'waterpark'):
        deco.append([k, x, z, w, d, c, n])
        if k == 'pool': areas.append([1, ccw(rect(x, z, w, d, 2.2))])
        else: areas.append([1, ccw(rect(x + 2, z + d * .48, w - 4, d * .52 - 2.2))])
        if n:
            mx, mz, nx, nz, L = best_side(x, z, w, d)
            parksigns.append([round(mx - nx * 1.2, 1), round(mz - nz * 1.2, 1), round(math.atan2(nx, nz), 3), n])
        if k == 'waterpark':   # the slide tower is solid (you can land on top)
            solids.append([x + w * .3 - 3, z + 3, x + w * .3 + 3, z + 9, 13])
    elif k in ('camp', 'cornfarm', 'policecar'):
        deco.append([k, x, z, w, d, c, n])
        if n:
            mx, mz, nx, nz, L = best_side(x, z, w, d)
            parksigns.append([round(mx - nx * 1.2, 1), round(mz - nz * 1.2, 1), round(math.atan2(nx, nz), 3), n])
    elif k == 'redpanda':
        deco.append([k, x, z, w, d, c, n])
        solids.append([x + 1.5, z + 1.5, x + w - 1.5, z + d - 1.5, min(w, d) / 11 * 10.5 + 1.4])
    elif k in ('raccoon', 'cat', 'L67', 'LOL', 'pigeonstatue', 'pig'):
        deco.append([k, x, z, w, d, c, n, it.get('rot')])
        h = {'raccoon': 34, 'cat': 34, 'L67': 22, 'LOL': 22, 'pigeonstatue': 30, 'pig': 22}[k]
        m = min(w, d) / 26 if k in ('raccoon', 'cat', 'pigeonstatue', 'pig') else 1
        r = (13 * max(.7, m)) if k in ('raccoon', 'cat', 'pigeonstatue', 'pig') else None
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
        roads.append([r['w'], 1, pts, r.get('name') or NAMES[mi % len(NAMES)], 0, 2]); mi += 1
    else:
        roads.append([r['w'], 0, pts, r.get('name') or 'Lane', 0, 1])
ring = []
for t in range(49):
    a = 2 * math.pi * t / 48; ring += [round(TX + C['rr'] * math.cos(a), 1), round(TZ + C['rr'] * math.sin(a), 1)]
roads.append([C['mainw'], 1, ring, 'Roundabout', 0, 2])

# street trees along the lanes (kept off buildings by the engine's own check when walking)
terrain = C.get('terrain') or {'x0': -700, 'z0': -700, 'step': 20, 'nx': 101, 'nz': 91, 'dm': [0] * (101 * 91)}
NAT = C.get('nature')
def mountain_flat(q):
    T_ = C['terrain']; i_ = round((q[0] - T_['x0']) / T_['step']); j_ = round((q[1] - T_['z0']) / T_['step'])
    return all(T_['dm'][min(T_['nz'] - 1, max(0, j_ + b_)) * T_['nx'] + min(T_['nx'] - 1, max(0, i_ + a_))] < 5 for a_ in (-2, 0, 2) for b_ in (-2, 0, 2))
if NAT:   # the ring's countryside: river + lake are water, forest trees, signs
    R, hw = [q for q in NAT['river'] if mountain_flat(q)], NAT['riverW'] / 2   # flat water only below the waterfall
    Lp, Rp = [], []
    for a in range(len(R)):
        p0, p1 = R[max(0, a - 1)], R[min(len(R) - 1, a + 1)]
        dx, dz = p1[0] - p0[0], p1[1] - p0[1]; l = math.hypot(dx, dz) or 1
        Lp.append((R[a][0] - dz / l * hw, R[a][1] + dx / l * hw)); Rp.append((R[a][0] + dz / l * hw, R[a][1] - dx / l * hw))
    areas.append([1, ccw([v for q in Lp + Rp[::-1] for v in q])])
    lx, lz, lrx, lrz = NAT['lake']
    areas.append([1, ellipse(lx, lz, lrx, lrz, 64)])
    trees += NAT['trees']
    face = lambda x, z: round(math.atan2(300 - x, 210 - z), 3)
    for x, z, n in [(688, 420, 'Pigeon Lake'), (-118, 432, 'Pigeon Farm'), (-128, 70, 'Raccoon Forest')]:
        parksigns.append([x, z, face(x, z), n])
city = {'home': -1, 'bounds': C.get('bounds') or [-40.0, -40.0, 640.0, 460.0], 'nature': NAT, 'buildings': buildings, 'roads': roads, 'areas': areas,
        'rails': [], 'stations': [], 'snacks': snacks, 'signs': signs, 'trees': trees, 'crosswalks': [], 'dong': [],
        'billboards': [], 'terrain': terrain, 'parksigns': parksigns, 'skybridges': SKYBRIDGES, 'critters': CRITTERS, 'planes': PLANES, 'solids': solids, 'deco': deco}
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
g.scale.setScalar(Math.max(.7,S));g.position.set(x+w/2,0,z+d/2);g.rotation.y=o.rot!=null?o.rot:.7;$t.add(g)}
function redpanda(x,z,w,d){const g=new T.Group(),R='#c1440e',K='#3a1d12',W='#fff4e6',L2='#e8a070';const lx=w<d,len=lx?d:w,wid=lx?w:d,S=Math.min(wid/11,len/21);
const add=(geo,c,px,py,pz,sx=1,sy=1,sz=1)=>{const m=new T.Mesh(geo,mat(c));m.position.set(px,py,pz);m.scale.set(sx,sy,sz);g.add(m);return m};
add(new T.Box(10,1.4,20),'#cfc8b8',0,.7,0);add(new T.Sph(1,20,16),R,0,6.2,-1,3.2,2.6,5.2);add(new T.Sph(1,16,12),K,0,4.8,-1,2.6,1.4,4.4);
[[-1.8,-4],[1.8,-4],[-1.8,2],[1.8,2]].forEach(([a,b])=>{add(new T.Cyl(.85,.75,4.2,10),K,a,3.5,b);add(new T.Sph(.95,10,8),K,a,1.6,b-.25,1,.6,1.3)});
add(new T.Sph(2.6,20,16),R,0,8.3,-6.9,1.1,.95,1);add(new T.Sph(1.4,16,12),W,0,7.3,-8.9,1.35,.8,.9);add(new T.Sph(.45,10,8),K,0,7.7,-10.1);
[-1,1].forEach(s=>{add(new T.Sph(.55,10,8),W,s*1.15,9.4,-8.8);add(new T.Sph(.38,10,8),K,s*1.05,8.7,-9.1);add(new T.Sph(.4,8,6),'#8a2c08',s*1.25,7.6,-8.8,.6,1.6,.5);
const e=add(new T.Cone(1.15,1.9,12),R,s*1.9,10.6,-6.6);e.rotation.z=-s*.3;const ei=add(new T.Cone(.7,1.2,10),W,s*1.85,10.45,-7.05);ei.rotation.z=-s*.3});
for(let i=0;i<8;i++){const t=i/7;add(new T.Sph(1.55-t*.45,14,10),i%2?L2:R,0,6.4+Math.sin(t*Math.PI*.85)*3.6,3.8+i*.9)}
g.scale.setScalar(S);lx||(g.rotation.y=Math.PI/2);g.position.set(x+w/2,0,z+d/2);$t.add(g)}
const shp=p=>{const s=new T.Shape();s.moveTo(...p[0]);p.slice(1).forEach(q=>s.lineTo(...q));return s};
const ring=(cx,cy,r1,r2)=>{const s=new T.Shape();s.absarc(cx,cy,r2,0,Math.PI*2);const h=new T.Path();h.absarc(cx,cy,r1,0,Math.PI*2,!0);s.holes.push(h);return s};
const SIX=[ring(4.5,5,2.2,4.5),shp([[.2,5],[2.4,5],[6,15],[3.6,15.6]])],SEVEN=shp([[0,13],[9,13],[9,11.4],[4.2,0],[1.6,0],[6.2,11],[0,11]]),ELL=shp([[0,0],[8,0],[8,2.6],[2.6,2.6],[2.6,14],[0,14]]),OH=ring(4.5,7,2.6,5.6);
function letters(x,z,w,d,parts){const g=new T.Group();box(Math.max(w,8),2,Math.max(d,6),'#cfc8b8',0,1,0,g);const step=11,st=-(parts.length-1)*step/2;
parts.forEach(([sh,c],i)=>{const m=new T.Mesh(new T.Ext(sh,{depth:3,bevelEnabled:!0,bevelSize:.4,bevelThickness:.4,bevelSegments:2}),mat(c));m.position.set(st+i*step-4.5,2,-1.5);g.add(m)});
const sc=Math.min(1.2,Math.max(.6,w/(parts.length*11)));g.scale.set(sc,sc*1.3,sc);g.position.set(x+w/2,0,z+d/2);g.rotation.y=-.5;$t.add(g)}
for(const[k,x,z,w,d,c,n,f]of ie.deco||[]){const cx=x+w/2,cz=z+d/2;
if(k==='raccoon')animal(x,z,w,d,{body:'#8e959c',belly:'#e9e6e0',nose:'#1e2124',mask:!0,stripes:!0,rot:f});
else if(k==='barn'){const g=new T.Group(),R='#b8322a',Wt='#fbf6ec',RF='#4a3b36';const long=w>=d,len=(long?w:d)-1.2,wid=(long?d:w)-1.2,H=Math.max(7,wid*.42);
box(len,H,wid,R,0,H/2,0,g);
const sh=new T.Shape(),hw=wid/2+.5,r1=H*.55,r2=H*1.05;sh.moveTo(-hw,0);sh.lineTo(-hw*.72,r1*.62);sh.lineTo(0,r1);sh.lineTo(hw*.72,r1*.62);sh.lineTo(hw,0);sh.lineTo(-hw,0);
const roof=new T.Mesh(new T.Ext(sh,{depth:len+1,bevelEnabled:!1}),mat(RF));roof.rotation.y=Math.PI/2;roof.position.set(-len/2-.5,H,0);g.add(roof);
const gs=new T.Shape(),gw=wid/2-.05;gs.moveTo(-gw,0);gs.lineTo(-gw*.72,r1*.6);gs.lineTo(0,r1*.96);gs.lineTo(gw*.72,r1*.6);gs.lineTo(gw,0);gs.lineTo(-gw,0);
for(const s of[-1,1]){const gb=new T.Mesh(new T.Ext(gs,{depth:.2,bevelEnabled:!1}),mat(R));gb.rotation.y=Math.PI/2;gb.position.set(s*(len/2+.01)-(s<0?.2:0),H,0);g.add(gb);
const dx=s*(len/2+.12),dw=Math.min(wid*.42,7),dh=Math.min(H*.72,6.5);box(.15,dh+.5,dw+.5,Wt,dx,dh/2+.25,0,g);box(.2,dh,dw,'#8e231c',dx+s*.05,dh/2,0,g);
for(const a of[1,-1]){const x2=box(.25,Math.hypot(dw,dh),.35,Wt,dx+s*.12,dh/2,0,g);x2.rotation.x=a*Math.atan2(dw,dh)}box(.25,.35,dw,Wt,dx+s*.12,dh/2,0,g);
box(.15,1.6,1.6,Wt,dx,H+r1*.45,0,g);box(.2,1.2,1.2,'#3a2a22',dx+s*.04,H+r1*.45,0,g)}
for(const s of[-1,1]){box(len+.2,.3,.3,Wt,0,H,s*(wid/2+.05),g);for(const e of[-1,1])box(.35,H,.35,Wt,e*len/2,H/2,s*wid/2,g)}
const si=new T.Mesh(new T.Cyl(2.6,2.6,H*1.9,18),mat('#c9ced3'));si.position.set(0,H*.95,wid/2+3.2);g.add(si);for(let k=1;k<5;k++){const rg=new T.Mesh(new T.Cyl(2.66,2.66,.25,18),mat('#9aa3ab'));rg.position.set(0,k*H*1.9/5,wid/2+3.2);g.add(rg)}
const dm=new T.Mesh(new T.Sph(2.6,18,10,0,6.3,0,1.6),mat('#b8322a'));dm.position.set(0,H*1.9,wid/2+3.2);g.add(dm);
box(.12,1.6,.12,'#333',0,H+r1+1,0,g);box(1.4,.08,.08,'#333',0,H+r1+1.4,0,g);
for(let k=0;k<4;k++){const hb=new T.Mesh(new T.Cyl(.75,.75,1.2,12),mat('#e9cf6a'));hb.rotation.z=Math.PI/2;hb.position.set(len/2+2.2,.75,-wid/2+1+k*1.7);g.add(hb)}
g.position.set(x+w/2,0,z+d/2);g.rotation.y=long?0:Math.PI/2;$t.add(g)}
else if(k==='pig'){const g=new T.Group(),S=Math.min(w,d)/26,P='#f7a8b8',D='#e8879c';const add=(geo,c,px,py,pz,sx=1,sy=1,sz=1)=>{const m=new T.Mesh(geo,mat(c));m.position.set(px,py,pz);m.scale.set(sx,sy,sz);g.add(m);return m};
add(new T.Box(24,3,24),'#cfc8b8',0,1.5,0);add(new T.Sph(8,24,18),P,0,12,0,1,.9,1.35);[[-4,-6],[4,-6],[-4,6],[4,6]].forEach(([a,b])=>{add(new T.Cyl(1.8,1.6,6,10),P,a,6,b);add(new T.Cyl(1.7,1.7,.8,10),'#8a5a4a',a,3.4,b)});
add(new T.Sph(5.8,20,16),P,0,15,11);add(new T.Cyl(2.4,2.6,2,16),D,0,14.2,16.3).rotation.x=Math.PI/2;[-1,1].forEach(s=>{add(new T.Sph(.5,8,6),'#8a3a4a',s*.9,14.3,17.35);add(new T.Sph(.8,10,8),'#1e2124',s*2.4,17,15.5);add(new T.Sph(.45,8,6),'#ffffff',s*2.5,17.3,16.1);
const e=add(new T.Cone(2,3.2,10),D,s*3.6,20.2,9.5);e.rotation.z=-s*.5;e.rotation.x=.4});for(let k=0;k<6;k++){const t=k/5;add(new T.Sph(.7,8,6),D,Math.sin(t*9)*1.2,14+t*2.5,-11-Math.cos(t*9)*1.2)}
g.scale.setScalar(Math.max(.7,S));g.position.set(x+w/2,0,z+d/2);g.rotation.y=f!=null?f:0;$t.add(g)}
else if(k==='pigeonstatue'){const g=new T.Group(),S=Math.min(w,d)/26;const add=(geo,c,px,py,pz,sx=1,sy=1,sz=1)=>{const m=new T.Mesh(geo,mat(c));m.position.set(px,py,pz);m.scale.set(sx,sy,sz);g.add(m);return m};
add(new T.Box(24,3,24),'#cfc8b8',0,1.5,0);add(new T.Box(20,2,20),'#b9b2a2',0,4,0);
add(new T.Sph(7,24,18),'#8a96a8',0,15,-1,1,1.05,1.45);add(new T.Sph(5.2,20,16),'#5fb39a',0,19.5,4.5,1,1.1,.9);add(new T.Sph(4.6,20,16),'#6d7b90',0,24.5,7);
const bk=add(new T.Cone(1,3.4,12),'#f2b23c',0,24,11.6);bk.rotation.x=Math.PI/2;add(new T.Sph(1.1,12,10),'#e8e8e8',0,25.5,10.2,1,.6,.8);
[-1,1].forEach(s=>{add(new T.Sph(1.2,12,10),'#ff7a3c',s*2.7,25.6,9.3);add(new T.Sph(.55,10,8),'#1e2124',s*3,25.7,10.2);const wg=add(new T.Sph(5,18,14),'#9aa6b8',s*6.2,15.5,-2,.35,.75,1.5);wg.rotation.z=s*.15;
for(let k=0;k<3;k++)add(new T.Box(.5,2.2,4.6-k),'#4d5866',s*6.9,12.4+k*1.3,-6.5-k*.8);const lg=add(new T.Cyl(.6,.6,5,8),'#e2725b',s*2.5,7,0);for(const t of[-1,0,1])add(new T.Box(.7,.6,3),'#e2725b',s*2.5+t*1.1,5.2,1.2).rotation.y=t*.4});
add(new T.Box(7,1.4,9),'#6d7b90',0,13.5,-11).rotation.x=.35;
if(/\bsir\b/i.test(n||'')){add(new T.Cyl(5.4,5.8,.9,24),'#5fae4a',0,28.6,6.6);add(new T.Sph(3.8,18,12,0,6.3,0,1.6),'#7cc95e',0,28.9,6.6,1,.9,1);
const fe=add(new T.Sph(1,12,8),'#3b8fd9',-2.4,31.2,3.4,1,.6,4.2);fe.rotation.x=-.5;fe.rotation.z=.5;
const sw=new T.Group();sw.position.set(-7.4,15,4.5);sw.rotation.z=.55;sw.rotation.x=-.25;g.add(sw);const sa=(geo,c,y)=>{const m=new T.Mesh(geo,mat(c));m.position.y=y;sw.add(m);return m};
sa(new T.Box(1.1,13,.35),'#d8dde3',7.5);sa(new T.Cone(.78,2,4),'#d8dde3',15).rotation.y=Math.PI/4;sa(new T.Box(4.2,.7,.9),'#e0b040',.6);sa(new T.Cyl(.38,.38,3,8),'#7a4f2c',-1.2);sa(new T.Sph(.6,10,8),'#e0b040',-2.9)}
g.scale.setScalar(Math.max(.7,S));g.position.set(x+w/2,0,z+d/2);g.rotation.y=f!=null?f:0;$t.add(g)}
else if(k==='cat')animal(x,z,w,d,{body:'#f2a65a',belly:'#fff1dc',nose:'#f27a8a',mask:!1,stripes:!1});
else if(k==='redpanda')redpanda(x,z,w,d);
else if(k==='L67')letters(x,z,w,d,[[SIX,'#8fd8ff'],[SEVEN,'#ff9acd']]);
else if(k==='LOL')letters(x,z,w,d,[[ELL,'#ffd23c'],[OH,'#ff7a5a'],[ELL,'#7fc8ff']]);
else if(k==='f'){const L=(a,b,X,Z)=>box(a,.06,b,'#ffffff',X,.13,Z);L(w-4,.5,cx,z+2);L(w-4,.5,cx,z+d-2);L(.5,d-4,x+2,cz);L(.5,d-4,x+w-2,cz);w>d?L(.5,d-4,cx,cz):L(w-4,.5,cx,cz);const lg=w>d;[-1,1].forEach(s=>{const gx=lg?cx+s*(w/2-2.5):cx,gz=lg?cz:cz+s*(d/2-2.5);box(lg?.3:7,.3,lg?7:.3,'#ffffff',gx,2.4,gz);for(const o of[-3.4,3.4])box(.3,2.4,.3,'#ffffff',lg?gx:gx+o,1.2,lg?gz+o:gz)})}
else if(k==='g'){for(let q=0;q<w*d/6;q++){const fl=new T.Mesh(new T.Sph(.5,8,6),mat(c||'#e8463c'));fl.position.set(x+1+Wt(q+x)*(w-2),.4,z+1+Wt(q*7+z)*(d-2));$t.add(fl)}}
else if(k==='dock'){box(w,.6,d,'#8a5a3a',cx,.5,cz)}
}
for(const[x0,z0,x1,z1,lo,hi,c]of ie.skybridges||[]){const L=x1-x0+1.2,W=z1-z0,cx=(x0+x1)/2,cz=(z0+z1)/2,H=hi-lo;
box(L,.5,W,'#e9ecef',cx,lo+.25,cz);box(L,.5,W,'#e9ecef',cx,hi-.25,cz);box(L,H-1,W-.3,c,cx,(lo+hi)/2,cz);for(let k=0;k<=Math.round(L/2.5);k++){const xx=x0-.6+k*L/Math.round(L/2.5);box(.25,H,W+.05,'#e9ecef',xx,(lo+hi)/2,cz)}}

{const LIVE=[];const rnd=Math.random,clampv=(v,a,b)=>Math.max(a,Math.min(b,v));
const part=(g,geo,c,x,y,z,sx=1,sy=1,sz=1)=>{const m=new T.Mesh(geo,mat(c));m.position.set(x,y,z);m.scale.set(sx,sy,sz);g.add(m);return m};
const pivot=(g,x,y,z)=>{const p=new T.Group();p.position.set(x,y,z);g.add(p);return p};
function person(shirt){const g=new T.Group(),skin=['#f1c7a0','#d9a47a','#a86f4a','#f6d6b8'][Math.floor(rnd()*4)];
const legs=[-1,1].map(s=>{const p=pivot(g,s*.13,.85,0);part(p,new T.Box(.16,.8,.18),'#22262b',0,-.4,0);part(p,new T.Box(.18,.12,.3),'#ffffff',0,-.82,.06);return p});
part(g,new T.Box(.48,.62,.28),shirt,0,1.18,0);part(g,new T.Box(.5,.2,.3),'#22262b',0,.85,0);
const arms=[-1,1].map(s=>{const p=pivot(g,s*.31,1.45,0);part(p,new T.Box(.13,.6,.14),shirt,0,-.28,0);part(p,new T.Sph(.08,8,6),skin,0,-.62,0);return p});
part(g,new T.Sph(.2,12,10),skin,0,1.68,0);part(g,new T.Sph(.21,12,10),['#2b1d14','#111','#6b4426','#c9a15a'][Math.floor(rnd()*4)],0,1.74,-.04,1,.7,1);
$t.add(g);return{g,legs,arms}}
function soccer(x,z,w,d){const long=w>=d,L=(long?w:d)-6,Wd=(long?d:w)-6,cx=x+w/2,cz=z+d/2;
const P=(u,v)=>long?[cx+u,cz+v]:[cx+v,cz+u];   // u = along the pitch, v = across
const ball=new T.Mesh(new T.Sph(.22,12,10),mat('#ffffff'));$t.add(ball);const B={u:0,v:0,tu:0,tv:0,sp:0,h:0};
const team=[['#e8463c',-1],['#2f6fdf',1]],pl=[];
for(const[col,side]of team){for(let k=0;k<5;k++){const keeper=k===0;const home=keeper?[side*(L/2-1),0]:[side*(L*(.12+.22*(k%2))),(k<3?-1:1)*Wd*(.18+.12*(k>>1&1))];
const p=person(keeper?'#ffd23c':col);p.side=side;p.keeper=keeper;p.home=home;p.u=home[0];p.v=home[1];p.ph=rnd()*6;p.cool=0;pl.push(p)}}
const kick=p=>{const tu=-p.side*(L/2)*(.2+rnd()*.85),tv=(rnd()-.5)*Wd*.9;B.tu=clampv(tu,-L/2,L/2);B.tv=tv;B.sp=7+rnd()*7;p.cool=1.2};
LIVE.push(dt=>{const du=B.tu-B.u,dv=B.tv-B.v,dd=Math.hypot(du,dv);if(dd>.05&&B.sp>0){const st=Math.min(dd,B.sp*dt);B.u+=du/dd*st;B.v+=dv/dd*st;B.sp=Math.max(1.5,B.sp-3*dt)}else B.sp=0;
if(Math.abs(B.u)>L/2-.5){B.u=0;B.v=0;B.tu=0;B.tv=0}   // goal! back to the middle
const[bx,bz]=P(B.u,B.v);ball.position.set(bx,.3,bz);ball.rotation.x+=B.sp*dt*2;
for(const s of[-1,1]){let best=null,bd=1e9;for(const p of pl)if(p.side===s&&!p.keeper){const q=Math.hypot(p.u-B.u,p.v-B.v);q<bd&&(bd=q,best=p)}for(const p of pl)if(p.side===s)p.chase=p===best}
for(const p of pl){p.cool-=dt;let tu,tv;if(p.keeper){tu=p.home[0];tv=clampv(B.v,-3,3)}else if(p.chase){tu=B.u;tv=B.v}else{tu=p.home[0]+B.u*.45;tv=p.home[1]+B.v*.3}
const a=tu-p.u,b=tv-p.v,q=Math.hypot(a,b),spd=p.chase?5.5:3.2,mv=Math.min(q,spd*dt);if(q>.3){p.u+=a/q*mv;p.v+=b/q*mv}
if(p.chase&&q<.7&&p.cool<=0)kick(p);
const moving=q>.3;p.ph+=dt*(moving?(p.chase?11:8):0);const sw=moving?Math.sin(p.ph)*.7:0;p.legs[0].rotation.x=sw;p.legs[1].rotation.x=-sw;p.arms[0].rotation.x=-sw*.8;p.arms[1].rotation.x=sw*.8;
const[px,pz]=P(p.u,p.v);p.g.position.set(px,.08,pz);const[lx,lz]=P(p.keeper||!moving?B.u:tu,p.keeper||!moving?B.v:tv);p.g.rotation.y=Math.atan2(lx-px,lz-pz)}})}
function pigeons(x,z,w,d){for(let k=0;k<12;k++){const g=new T.Group();
part(g,new T.Sph(.13,10,8),'#8a96a8',0,.16,0,1,.85,1.5);const head=pivot(g,0,.27,.16);part(head,new T.Sph(.075,10,8),'#5d6a7e',0,0,0);part(head,new T.Sph(.07,8,6),'#5fb39a',0,-.06,-.02,1,1,.8);
const bk=part(head,new T.Cone(.022,.08,6),'#f2b23c',0,0,.09);bk.rotation.x=Math.PI/2;part(head,new T.Sph(.018,6,5),'#ff7a3c',.05,.02,.04);part(head,new T.Sph(.018,6,5),'#ff7a3c',-.05,.02,.04);
part(g,new T.Box(.12,.03,.18),'#5d6a7e',0,.17,-.2);for(const s of[-1,1])part(g,new T.Cyl(.012,.012,.1,5),'#e2725b',s*.05,.05,0);
g.scale.setScalar(1.6);$t.add(g);const b={g,head,x:x+3+rnd()*(w-6),z:z+3+rnd()*(d-6),yaw:rnd()*6.3,t:rnd()*2,hop:0,fx:0,fz:0,peck:0};
LIVE.push(dt=>{b.t-=dt;if(b.hop>0){b.hop=Math.max(0,b.hop-dt*2.6);b.x+=b.fx*dt*2.6;b.z+=b.fz*dt*2.6}else if(b.t<=0){const r=rnd();if(r<.55){b.yaw+=(rnd()-.5)*2.2;const st=.35+rnd()*.5;b.fx=Math.sin(b.yaw)*st;b.fz=Math.cos(b.yaw)*st;
const nx=b.x+b.fx,nz=b.z+b.fz;if(nx<x+2||nx>x+w-2||nz<z+2||nz>z+d-2){b.yaw+=Math.PI;b.fx=-b.fx;b.fz=-b.fz}b.hop=1}else if(r<.85)b.peck=1;b.t=.35+rnd()*1.1}
b.peck=Math.max(0,b.peck-dt*2.2);g.position.set(b.x,.08+Math.sin(b.hop*Math.PI)*.28,b.z);g.rotation.y=b.yaw;b.head.rotation.x=Math.sin(b.peck*Math.PI)*1.1})}}
function elephant(x,z,w,d){const g=new T.Group(),C='#8f9196';
part(g,new T.Sph(1,16,12),C,0,2,0,1.15,1.05,1.7);
const legs=[[-.65,1.05],[.65,1.05],[-.65,-1.05],[.65,-1.05]].map(([lx,lz])=>{const p=pivot(g,lx,1.55,lz);part(p,new T.Cyl(.32,.36,1.55,10),C,0,-.78,0);part(p,new T.Cyl(.38,.38,.1,10),'#c9c4b8',0,-1.5,0);return p});
const head=pivot(g,0,2.55,1.85);part(head,new T.Sph(.82,14,12),C,0,0,0);
for(const s of[-1,1]){const e=part(head,new T.Sph(.75,12,10),'#a3a0a6',s*.75,.05,-.25,.15,1.05,.95);e.rotation.y=s*.35;part(head,new T.Sph(.1,8,6),'#1e2124',s*.42,.2,.62);
const tk=part(head,new T.Cone(.09,.75,8),'#fffaf0',s*.32,-.5,.6);tk.rotation.x=Math.PI*.62}
let seg=head;const trunk=[];for(let k=0;k<5;k++){const p=pivot(seg,0,k?-.42:-.35,k?0:.62);part(p,new T.Cyl(.22-k*.03,.25-k*.03,.46,8),C,0,-.21,0);trunk.push(p);seg=p}
const tail=pivot(g,0,2.3,-1.65);part(tail,new T.Cyl(.04,.04,.8,5),C,0,-.4,0);
g.scale.setScalar(1.25);$t.add(g);(window.__elephants=window.__elephants||[]).push(g);const o=3.3,X0=x-o,X1=x+w+o,Z0=z-o,Z1=z+d+o,per=2*(X1-X0+Z1-Z0);let s=rnd()*per,ph=0;
LIVE.push(dt=>{s=(s+dt*1.4)%per;ph+=dt*4.2;let q=s,px,pz,yaw;const a=X1-X0,b=Z1-Z0;
if(q<a){px=X0+q;pz=Z0;yaw=Math.PI/2}else if((q-=a)<b){px=X1;pz=Z0+q;yaw=0}else if((q-=b)<a){px=X1-q;pz=Z1;yaw=-Math.PI/2}else{q-=a;px=X0;pz=Z1-q;yaw=Math.PI}
let dy=yaw-g.rotation.y;dy=Math.atan2(Math.sin(dy),Math.cos(dy));g.rotation.y+=dy*Math.min(1,dt*3);g.position.set(px,0,pz);
legs.forEach((l,k)=>l.rotation.x=Math.sin(ph+(k===0||k===3?0:Math.PI))*.35);trunk.forEach((t,k)=>{t.rotation.x=.12+Math.sin(ph*.5+k*.6)*.18;t.rotation.z=Math.sin(ph*.35+k)*.12});tail.rotation.z=Math.sin(ph*1.3)*.4;head.rotation.y=Math.sin(ph*.25)*.15})}

const WATER2=new T.Mat({color:new Pt('#3fd0e6')});
function poolBase(x0,z0,x1,z1,deck){const w=x1-x0,d=z1-z0,cx=(x0+x1)/2,cz=(z0+z1)/2;box(w,.5,d,'#e9e4d6',cx,.25,cz);
const wt=new T.Mesh(new Hn(w-2*deck,d-2*deck),WATER2);wt.rotation.x=-Math.PI/2;wt.position.set(cx,.52,cz);$t.add(wt);
for(let k=1;k<Math.floor((w-2*deck)/2.5);k++)box(.12,.02,d-2*deck-1,'#ffffff',x0+deck+k*2.5,.54,cz)}
function floats(x0,z0,x1,z1,n){for(let k=0;k<n;k++){const r=new T.Mesh(new Vo(.5,.2,8,16),mat(['#ff5a5a','#ffd23c','#5ac8ff','#7fe08a'][k%4]));r.rotation.x=Math.PI/2;$t.add(r);
const ox=x0+1+rnd()*(x1-x0-2),oz=z0+1+rnd()*(z1-z0-2),ph=rnd()*6;let t=0;LIVE.push(dt=>{t+=dt;r.position.set(ox+Math.sin(t*.3+ph)*.8,.62+Math.sin(t*2+ph)*.06,oz+Math.cos(t*.25+ph)*.8)})}}
function umbrella(x,z,c){const p=new T.Mesh(new T.Cyl(.06,.06,2.4,6),mat('#ffffff'));p.position.set(x,1.7,z);$t.add(p);const u=new T.Mesh(new T.Cone(1.4,.7,10),mat(c));u.position.set(x,3,z);$t.add(u);box(.7,.15,1.8,'#ffffff',x+1.1,.75,z)}
function pool(x,z,w,d){poolBase(x,z,x+w,z+d,2.2);floats(x+2.2,z+2.2,x+w-2.2,z+d-2.2,Math.max(2,Math.round(w*d/120)));
umbrella(x+1.1,z+1.1,'#ff5a5a');umbrella(x+w-1.1,z+d-1.1,'#ffd23c')}
function slidePath(pts,c){for(let k=1;k<pts.length;k++){const a=pts[k-1],b=pts[k],L=Math.hypot(b[0]-a[0],b[1]-a[1],b[2]-a[2]);const g=new T.Group();g.position.set((a[0]+b[0])/2,(a[1]+b[1])/2,(a[2]+b[2])/2);g.lookAt(b[0],b[1],b[2]);
const m=new T.Mesh(new T.Cyl(.75,.75,L+.15,12,1,!0,Math.PI*.15,Math.PI*1.7),mat(c));m.material.side=2;m.rotation.x=Math.PI/2;m.rotation.y=Math.PI;g.add(m);$t.add(g)}}
function along(pts){const seg=[];let tot=0;for(let k=1;k<pts.length;k++){const a=pts[k-1],b=pts[k],L=Math.hypot(b[0]-a[0],b[1]-a[1],b[2]-a[2]);seg.push([a,b,L,tot]);tot+=L}
return[tot,s=>{for(const[a,b,L,o]of seg)if(s<=o+L){const t=(s-o)/L;return[a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t,a[2]+(b[2]-a[2])*t]}const e=pts[pts.length-1];return e}]}
function waterpark(x,z,w,d){const py=z+d*.48;poolBase(x,py-2.2+2.2,x+w,z+d,2.2);box(w,.5,d*.48,'#e9e4d6',x+w/2,.25,z+d*.24);floats(x+2.2,py+2.2,x+w-2.2,z+d-2.2,5);
const tx=x+w*.3,tz=z+6,H=12;for(const[a,b]of[[-2.6,-2.6],[2.6,-2.6],[-2.6,2.6],[2.6,2.6]])box(.5,H,.5,'#ff8a3c',tx+a,H/2,tz+b);box(6,.6,6,'#ffd23c',tx,H,tz);
for(const[a,b,ww,dd]of[[0,-3,6,.15],[0,3,6,.15],[-3,0,.15,6]])box(ww,1.1,dd,'#ffffff',tx+a,H+.85,tz+b);const rf=new T.Mesh(new T.Cone(4.6,2.4,4),mat('#5ac8ff'));rf.rotation.y=Math.PI/4;rf.position.set(tx,H+4.6,tz);$t.add(rf);
for(const[a,b]of[[-2.6,-2.6],[2.6,-2.6],[-2.6,2.6],[2.6,2.6]])box(.25,3.4,.25,'#ff8a3c',tx+a,H+1.7,tz+b);
for(let k=0;k<9;k++)box(1.6,.25,1.1,'#ffffff',tx-3.6,1+k*1.25,tz+3.4-k*.75);
const end=z+d-5;const A=[[tx+3.2,H+.4,tz]];for(let k=1;k<=22;k++){const a=k/22*Math.PI*3,r=5.2;A.push([tx+Math.cos(a)*r,H+.4-k*.42,tz+Math.sin(a)*r])}A.push([tx+5,2.8,py+1]);A.push([tx+4,1.2,Math.min(end,py+6)]);
const B=[[tx,H+.4,tz+3.2]];for(let k=1;k<=12;k++){const t=k/12;B.push([tx-1.5+Math.sin(t*Math.PI*3)*2.6,H+.4-t*(H-1.6),tz+3.2+t*(py+3-tz-3.2)])}B.push([tx-2,1.2,Math.min(end,py+7)]);
slidePath(A,'#ff4d4d');slidePath(B,'#ffd23c');
for(const P of[A,B]){const[tot,at]=along(P);for(let q=0;q<2;q++){const rider=new T.Group();const ring=new T.Mesh(new Vo(.45,.2,8,14),mat(['#7fe08a','#5ac8ff','#ff8ad8'][Math.floor(rnd()*3)]));ring.rotation.x=Math.PI/2;rider.add(ring);
const hd=new T.Mesh(new T.Sph(.25,10,8),mat('#f1c7a0'));hd.position.y=.45;rider.add(hd);$t.add(rider);let s=q*tot/2;LIVE.push(dt=>{s+=dt*(4+s*.35);if(s>tot+3)s=0;const p=at(Math.min(s,tot));rider.position.set(p[0],p[1]+.45+(s>tot?-.3:0),p[2]);rider.visible=s<tot+2.5})}}
const bx=x+w*.78,bz=z+7;for(const[a,b]of[[-2,-2],[2,-2],[-2,2],[2,2]])box(.4,8,.4,'#5ac8ff',bx+a,4,bz+b);box(4.8,.4,4.8,'#5ac8ff',bx,8,bz);
const bk=pivot($t,bx,9.6,bz);const bucket=new T.Mesh(new T.Cyl(1.5,1.1,2,14),mat('#ffd23c'));bucket.position.y=.6;bk.add(bucket);
const fall=new T.Mesh(new T.Cyl(1.2,2,8,14),new T.Mat({color:new Pt('#9fe6ff'),transparent:!0,opacity:.6}));fall.position.set(bx+1.6,4.4,bz);fall.visible=!1;$t.add(fall);
for(let k=0;k<6;k++){const j=new T.Mesh(new T.Sph(.25,8,6),new T.Mat({color:new Pt('#bff0ff'),transparent:!0,opacity:.8}));$t.add(j);const ox=x+3+rnd()*(w-6),oz=z+11+rnd()*(d*.48-13);let t=rnd()*3;LIVE.push(dt=>{t=(t+dt)%1.6;j.position.set(ox,.5+Math.sin(t/1.6*Math.PI)*3,oz)})}
let bt=0;LIVE.push(dt=>{bt=(bt+dt)%9;const tip=bt>7?Math.sin((bt-7)/2*Math.PI)*2:0;bk.rotation.z=-tip;fall.visible=bt>7.4&&bt<8.6})}
function plane(cx,cz,h,az,x0,z0,x1,z1){const g=new T.Group();const add=(geo,c,px,py,pz)=>{const m=new T.Mesh(geo,mat(c));m.position.set(px,py,pz);g.add(m);return m};
const len=az?z1-z0:x1-x0;box(az?6:len-6,.06,az?len-6:6,'#3a3f48',(x0+x1)/2,h+.03,(z0+z1)/2);for(let k=-len/2+6;k<len/2-6;k+=6)box(az?.4:3,.07,az?3:.4,'#ffffff',az?(x0+x1)/2:(x0+x1)/2+k,h+.04,az?(z0+z1)/2+k:(z0+z1)/2);
const y=h+3.4;add(new T.Cyl(2,2,26,18),'#ffffff',0,y,0).rotation.x=Math.PI/2;const no=add(new T.Sph(2,18,14),'#ffffff',0,y,13);no.scale.set(1,1,1.7);
const tc=add(new T.Cone(2,7,18),'#ffffff',0,y+.4,-16.4);tc.rotation.x=-Math.PI/2;add(new T.Box(4.06,.4,25),'#2f6fdf',0,y-.3,0);
const wg=add(new T.Box(30,.45,5.5),'#dfe4ea',0,y-.9,1);for(const s of[-1,1]){const e=add(new T.Cyl(.9,.9,3.6,14),'#8a96a8',s*7,y-1.9,2.4);e.rotation.x=Math.PI/2;add(new T.Box(.3,.9,1.6),'#8a96a8',s*7,y-1.3,2.4)}
add(new T.Box(.45,6,4.6),'#2f6fdf',0,y+4.6,-16.6);add(new T.Box(11,.3,3),'#dfe4ea',0,y+1,-17);
for(let i=0;i<15;i++)for(const s of[-1,1])add(new T.Box(.1,.6,.6),'#1e2a33',s*1.98,y+.8,-9.5+i*1.4);add(new T.Box(2.4,.6,.5),'#1e2a33',0,y+1.2,14.2);
for(const[a,b]of[[0,11],[-2.5,0],[2.5,0]]){add(new T.Cyl(.12,.12,1.6,6),'#555',a,h+1.2,b);const wh=add(new T.Cyl(.55,.55,.5,12),'#222',a,h+.55,b);wh.rotation.z=Math.PI/2}
const cv=document.createElement('canvas');cv.width=512;cv.height=96;const c2=cv.getContext('2d');c2.fillStyle='#ffffff';c2.fillRect(0,0,512,96);c2.fillStyle='#1f3a93';c2.font='bold 60px sans-serif';c2.textAlign='center';c2.textBaseline='middle';c2.fillText('OUR CITY AIR',256,50);
const tx2=new Pe(cv);tx2.colorSpace=me;const tm=new Be({map:tx2});for(const s of[-1,1]){const pl=new T.Mesh(new Hn(10,1.9),tm);pl.position.set(s*2.03,y+.75,-1);pl.rotation.y=s*Math.PI/2;g.add(pl)}
g.position.set(cx,0,cz);az||(g.rotation.y=Math.PI/2);$t.add(g);
const cl=(a,b,c,d,top)=>{a=Math.max(a,x0);b=Math.max(b,z0);c=Math.min(c,x1);d=Math.min(d,z1);if(a<c&&b<d)extra.push([a,b,c,d,top])};const extra=[];
if(az){cl(cx-2.2,cz-20,cx+2.2,cz+16.5,y+2.1);cl(cx-15,cz-1.8,cx+15,cz+3.8,y-.6)}else{cl(cx-20,cz-2.2,cx+16.5,cz+2.2,y+2.1);cl(cx-1.8,cz-15,cx+3.8,cz+15,y-.6)}
for(const[a,b,c,d,top]of extra){const i0=Math.max(0,Math.floor((a-Yt)/Zt)),i1=Math.min(fe-1,Math.floor((c-Yt)/Zt)),j0=Math.max(0,Math.floor((b-jt)/Zt)),j1=Math.min(Ke-1,Math.floor((d-jt)/Zt));for(let zz=j0;zz<=j1;zz++)for(let xx=i0;xx<=i1;xx++){const q=zz*fe+xx;$i[q]<top&&($i[q]=top)}}}
for(const[k,x,z,w,d]of ie.deco||[])k==='pool'?pool(x,z,w,d):k==='waterpark'&&waterpark(x,z,w,d);
// disco ball on the roof: mirror tiles, spinning, sparkles
for(const[k,x,z,w,d,c,n,h]of ie.deco||[]){if(k!=='discoball')continue;const cv=document.createElement('canvas');cv.width=256;cv.height=128;const x2=cv.getContext('2d');
for(let i=0;i<32;i++)for(let j=0;j<16;j++){const v=150+Math.floor(rnd()*105);x2.fillStyle=rnd()<.08?['#ff6ad5','#6ad5ff','#fff06a'][Math.floor(rnd()*3)]:`rgb(${v},${v},${v+10})`;x2.fillRect(i*8,j*8,7,7)}
const tx=new Pe(cv);tx.colorSpace=me;const r=Math.min(w,d)/2-2,cx=x+w/2,cz=z+d/2;box(.4,3,.4,'#555',cx,h+1.5,cz);const ball=new T.Mesh(new T.Sph(r,32,20),new Be({map:tx}));ball.position.set(cx,h+3+r,cz);$t.add(ball);
const sp=[];for(let q=0;q<10;q++){const m=new T.Mesh(new T.Sph(.35,6,4),new Be({color:new Pt(['#ff6ad5','#6ad5ff','#fff06a','#ffffff'][q%4])}));$t.add(m);sp.push([m,rnd()*6.3,rnd()*2])}
LIVE.push(dt=>{ball.rotation.y+=dt*.8;const t=performance.now()/1e3;for(const[m,a,o]of sp){const tt=(t*.7+o)%2;m.position.set(cx+Math.cos(a+t)*(r+1+tt*4),h+3+r+Math.sin(a*3)*r,cz+Math.sin(a+t)*(r+1+tt*4));m.visible=tt<1.4}})}
// corn farm: rows of corn, a wooden fence, and a big pile of seeds
for(const[k,x,z,w,d]of ie.deco||[]){if(k!=='cornfarm')continue;const pl=new T.Mesh(new Hn(w,d),mat('#8a6a3e'));pl.rotation.x=-Math.PI/2;pl.position.set(x+w/2,.08,z+d/2);$t.add(pl);
const stalk=new T.Cyl(.12,.16,2.6,5),leaf=new T.Box(.9,.06,.25),cob=new T.Cyl(.2,.2,.7,6);
for(let ix=x+2;ix<x+w-9;ix+=1.6)for(let iz=z+2;iz<z+d-2;iz+=1.3){const g=new T.Group();g.position.set(ix,0,iz);g.rotation.y=rnd()*6;const s=new T.Mesh(stalk,mat('#5f9e3a'));s.position.y=1.3;g.add(s);
const l=new T.Mesh(leaf,mat('#79b84a'));l.position.y=1.5;l.rotation.z=.5;g.add(l);if(rnd()<.6){const cb=new T.Mesh(cob,mat('#f2c94c'));cb.position.set(.18,1.7,0);cb.rotation.z=-.3;g.add(cb)}$t.add(g)}
const sx=x+w-5,sz=z+d/2;const pile=new T.Mesh(new T.Cone(4,3.2,20),mat('#d9b56a'));pile.position.set(sx,1.6,sz);$t.add(pile);for(let q=0;q<60;q++){const a=rnd()*6.3,rr=rnd()*3.6,sd=new T.Mesh(new T.Sph(.16,5,4),mat(['#8a5a2a','#f2e2b0','#c99a4a'][q%3]));sd.position.set(sx+Math.cos(a)*rr,.1+(3.2*(1-rr/4)),sz+Math.sin(a)*rr);$t.add(sd)}
const post=(px,pz)=>box(.25,1.4,.25,'#8a5a3a',px,.7,pz),rail=(ax,az,bx,bz)=>{for(const y of[.6,1.15])box(Math.abs(bx-ax)+.1||.12,.12,Math.abs(bz-az)+.1||.12,'#a87a4a',(ax+bx)/2,y,(az+bz)/2)};
const X0=x+.5,X1=x+w-.5,Z0=z+.5,Z1=z+d-.5;rail(X0,Z0,X1,Z0);rail(X0,Z1,X1,Z1);rail(X0,Z0,X0,Z1);rail(X1,Z0,X1,Z1);for(let px=X0;px<=X1+.01;px+=2.5){post(px,Z0);post(px,Z1)}for(let pz=Z0;pz<=Z1+.01;pz+=2.5){post(X0,pz);post(X1,pz)}}
// campsite: tents, a campfire and logs
for(const[k,x,z,w,d]of ie.deco||[]){if(k!=='camp')continue;const pl=new T.Mesh(new Hn(w,d),mat('#9ccf7a'));pl.rotation.x=-Math.PI/2;pl.position.set(x+w/2,.07,z+d/2);$t.add(pl);
const cols=['#ff8a3c','#3b8fd9','#e8463c','#7fc94a'];const n=Math.max(2,Math.round(w*d/180));for(let q=0;q<n;q++){const tx=x+3.5+((q%2)*(w-7)),tz=z+4+Math.floor(q/2)*((d-8)/Math.max(1,Math.ceil(n/2)-1||1));
const sh=new T.Shape();sh.moveTo(-1.8,0);sh.lineTo(1.8,0);sh.lineTo(0,2.4);sh.lineTo(-1.8,0);const tm=new T.Mesh(new T.Ext(sh,{depth:3.6,bevelEnabled:!1}),mat(cols[q%4]));tm.position.set(tx,0,Math.min(tz,z+d-4)-1.8);$t.add(tm);
box(.9,1.4,.05,'#2a2a2a',tx,.7,Math.min(tz,z+d-4)+1.82)}
const fx=x+w/2,fz=z+d/2;for(let q=0;q<6;q++){const lg=new T.Mesh(new T.Cyl(.12,.12,1.4,6),mat('#6b4426'));lg.position.set(fx,.3,fz);lg.rotation.z=1.1;lg.rotation.y=q;$t.add(lg)}
const fire=new T.Mesh(new T.Cone(.55,1.3,8),new Be({color:new Pt('#ffb020')}));fire.position.set(fx,.8,fz);$t.add(fire);LIVE.push(dt=>{const t=performance.now()/1e3;fire.scale.set(1,.8+Math.sin(t*11)*.2,1);fire.rotation.y+=dt*3});
for(const s of[-1,1]){const lg=new T.Mesh(new T.Cyl(.3,.3,2.4,8),mat('#7a4f2c'));lg.rotation.z=Math.PI/2;lg.position.set(fx,.3,fz+s*2.2);$t.add(lg)}}
// police car with flashing lights
for(const[k,x,z,w,d]of ie.deco||[]){if(k!=='policecar')continue;const g=new T.Group();g.position.set(x+w/2,0,z+d/2);g.rotation.y=w>d?Math.PI/2:0;$t.add(g);
box(2,.9,4.4,'#ffffff',0,.75,0,g);box(2.02,.5,1.6,'#1e2a40',0,.75,1.3,g);box(2.02,.5,1.6,'#1e2a40',0,.75,-1.3,g);box(1.7,.7,2.2,'#ffffff',0,1.5,-.2,g);box(1.72,.5,2,'#7fb8e8',0,1.5,-.2,g);
const cv=document.createElement('canvas');cv.width=256;cv.height=64;const c2=cv.getContext('2d');c2.fillStyle='#ffffff';c2.fillRect(0,0,256,64);c2.fillStyle='#1f3a93';c2.font='bold 44px sans-serif';c2.textAlign='center';c2.textBaseline='middle';c2.fillText('POLICE',128,34);
const t2=new Pe(cv);t2.colorSpace=me;for(const s of[-1,1]){const pl=new T.Mesh(new Hn(2.2,.55),new Be({map:t2}));pl.position.set(s*1.02,.85,0);pl.rotation.y=s*Math.PI/2;g.add(pl)}
for(const[a,b]of[[-.9,1.4],[.9,1.4],[-.9,-1.4],[.9,-1.4]]){const wh=new T.Mesh(new T.Cyl(.42,.42,.3,12),mat('#222'));wh.rotation.z=Math.PI/2;wh.position.set(a,.42,b);g.add(wh)}
const red=new Be({color:new Pt('#ff2a2a')}),blue=new Be({color:new Pt('#2a6aff')}),off=new Be({color:new Pt('#552222')}),off2=new Be({color:new Pt('#222255')});
const L1=new T.Mesh(new T.Box(.6,.3,.4),red),L2=new T.Mesh(new T.Box(.6,.3,.4),blue);L1.position.set(-.35,2,-.2);L2.position.set(.35,2,-.2);g.add(L1);g.add(L2);
LIVE.push(()=>{const on=Math.floor(performance.now()/350)%2;L1.material=on?red:off;L2.material=on?off2:blue})}

for(const P of ie.planes||[])plane(...P);

if(ie.nature){const N=ie.nature;
const addSolid=(a,b,c,d,top)=>{const i0=Math.max(0,Math.floor((a-Yt)/Zt)),i1=Math.min(fe-1,Math.floor((c-Yt)/Zt)),j0=Math.max(0,Math.floor((b-jt)/Zt)),j1=Math.min(Ke-1,Math.floor((d-jt)/Zt));for(let zz=j0;zz<=j1;zz++)for(let xx=i0;xx<=i1;xx++){const q=zz*fe+xx;$i[q]<top&&($i[q]=top)}};
const seg=(x0,z0,x1,z1,w,h,y,c,m)=>{const L=Math.hypot(x1-x0,z1-z0);const b=new T.Mesh(new T.Box(w,h,L+.3),m||mat(c));b.position.set((x0+x1)/2,y,(z0+z1)/2);b.rotation.y=Math.atan2(x1-x0,z1-z0);$t.add(b);return b};
// tunnels: road, walls, roof, lights, stone portals
const LAMP=new Be({color:new Pt('#fff2b0')});
for(const P of N.tunnels){for(let k=1;k<P.length;k++){const[a,b]=P[k-1],[c,d]=P[k];seg(a,b,c,d,12.5,.3,.25,'#3a3f46');const L=Math.hypot(c-a,d-b),nx=-(d-b)/L,nz=(c-a)/L;
for(const s of[-1,1])seg(a+nx*s*7.6,b+nz*s*7.6,c+nx*s*7.6,d+nz*s*7.6,.6,9,4.5,'#8b8f94');seg(a,b,c,d,16,.6,9.2,'#6d7177');if(k%4===0)seg(a,b,a+(c-a)*.08,b+(d-b)*.08,1.2,.2,8.8,null,LAMP)}
for(const e of[0,1]){const q=e?P[P.length-1]:P[0],r=e?P[P.length-2]:P[1],yaw=Math.atan2(q[0]-r[0],q[1]-r[1]),g=new T.Group();g.position.set(q[0],0,q[1]);g.rotation.y=yaw;$t.add(g);
for(const s of[-1,1])box(5,11,3,'#9a9590',s*10.3,5.5,0,g);box(26,4,3,'#9a9590',0,12.5,0,g);box(26,1,3.4,'#7a7570',0,14.8,0,g);const t2=new T.Mesh(new T.Box(15.6,9,.2),new Be({color:new Pt('#111418')}));t2.position.set(0,4.5,-1.6);g.add(t2)}}
const TS=[];for(const P of N.tunnels)for(let k=1;k<P.length;k++)TS.push([P[k-1][0],P[k-1][1],P[k][0],P[k][1]]);
const inTunnel=(x,z)=>{for(const[a,b,c,d]of TS){const dx=c-a,dz=d-b,L=dx*dx+dz*dz||1;let t=((x-a)*dx+(z-b)*dz)/L;t=t<0?0:t>1?1:t;const px=a+dx*t-x,pz=b+dz*t-z;if(px*px+pz*pz<56)return!0}return!1};
window.__inTunnel=inTunnel;
// welcome signs over the road: two towers + a beam with the sign (fly under it!)
for(const[ax,az,bx,bz,H,col,txt]of N.gantries||[]){const L=Math.hypot(bx-ax,bz-az),yaw=Math.atan2(bx-ax,bz-az),g=new T.Group();g.position.set((ax+bx)/2,0,(az+bz)/2);g.rotation.y=yaw;$t.add(g);
for(const s of[-1,1]){box(9,H,9,col,0,H/2,s*L/2,g);box(10,1,10,'#e9d8b0',0,H+.5,s*L/2,g)}
addSolid(ax-4.5,az-4.5,ax+4.5,az+4.5,H+1);addSolid(bx-4.5,bz-4.5,bx+4.5,bz+4.5,H+1);
box(2.4,1.4,L-8,col,0,H-1.2,0,g);
const cv=document.createElement('canvas');cv.width=1024;cv.height=200;const x2=cv.getContext('2d');x2.fillStyle='#2f7d3a';x2.fillRect(0,0,1024,200);x2.strokeStyle='#ffe9a8';x2.lineWidth=12;x2.strokeRect(12,12,1000,176);
x2.fillStyle='#ffffff';x2.textAlign='center';x2.textBaseline='middle';let fs=110;x2.font='bold '+fs+'px sans-serif';while(x2.measureText(txt).width>950&&fs>40){fs-=4;x2.font='bold '+fs+'px sans-serif'}x2.fillText(txt,512,104);
const tx=new Pe(cv);tx.colorSpace=me;const tm=new Be({map:tx});const bw=Math.min(L-12,26),bh=bw*200/1024,sy=H+bh/2+.1;box(.5,bh+.8,bw+.8,'#ffe9a8',0,sy,0,g);
for(const s of[-1,1]){const pl=new T.Mesh(new Hn(bw,bh),tm);pl.position.set(s*.3,sy,0);pl.rotation.y=s*Math.PI/2;g.add(pl)}
for(const s of[-1,1])box(.4,bh+1.2,.4,col,0,H+bh/2,s*(bw/2+.6),g);
window.__gantries=(window.__gantries||[]).concat([[ax,az,bx,bz,H-2]])}
// the Mountain Road: drawn as its own ribbon a little above the slope (the game's road follows the ground too closely on steep hills)
if(N.mroad){const P=N.mroad,V=[],I=[],hw=4.6,ASP=new T.Mat({color:new Pt('#4a4f56')}),CURB=new T.Mat({color:new Pt('#b9b4aa')});
const rib=(w,dy,m)=>{const V=[],I=[];P.forEach(([x,z],k)=>{const p0=P[Math.max(0,k-1)],p1=P[Math.min(P.length-1,k+1)],dx=p1[0]-p0[0],dz=p1[1]-p0[1],l=Math.hypot(dx,dz)||1,nx=-dz/l,nz=dx/l;
const W2=hw+1.5,y=Math.max(ne(x+nx*W2,z+nz*W2),ne(x-nx*W2,z-nz*W2),ne(x,z))+dy;V.push(x+nx*w,y,z+nz*w,x-nx*w,y,z-nz*w);if(k){const o=(k-1)*2;I.push(o,o+2,o+1,o+1,o+2,o+3)}});
const g=new oe;g.setAttribute('position',new Ut(V,3));g.setIndex(I);g.computeVertexNormals();const m2=new T.Mesh(g,m);m2.material.side=2;$t.add(m2)};
rib(hw+1,.9,CURB);rib(hw,1.05,ASP);
for(let k=2;k<P.length;k+=3){const[x,z]=P[k],y=Math.max(ne(x,z),ne(x+3,z),ne(x-3,z),ne(x,z+3),ne(x,z-3))+1.12;box(.3,.03,2.2,'#ffd23c',x,y,z).rotation.y=Math.atan2(P[k][0]-P[k-1][0],P[k][1]-P[k-1][1])}}
// the lookout at the top of the mountain road
{const[x,z]=N.lookout,y=ne(x,z),g=new T.Group();g.position.set(x,y,z);$t.add(g);for(const[a,b]of[[-3.5,-3.5],[3.5,-3.5],[-3.5,3.5],[3.5,3.5]])box(.5,4,.5,'#7a4f2c',a,2,b,g);box(8.4,.5,8.4,'#a0703f',0,4.2,0,g);
for(const[a,b,w,d]of[[0,-4,8.4,.15],[0,4,8.4,.15],[-4,0,.15,8.4],[4,0,.15,8.4]])box(w,1.1,d,'#ffffff',a,5,b,g);const rf=new T.Mesh(new T.Cone(6.4,2.6,4),mat('#d94b3c'));rf.rotation.y=Math.PI/4;rf.position.y=9;g.add(rf);
for(const[a,b]of[[-3.5,-3.5],[3.5,-3.5],[-3.5,3.5],[3.5,3.5]])box(.3,3.4,.3,'#7a4f2c',a,6.1,b,g);const sc=new T.Mesh(new T.Cyl(.25,.4,1.6,10),mat('#2f3a44'));sc.position.set(0,5.6,2.2);sc.rotation.x=-1.1;g.add(sc);addSolid(x-4.2,z-4.2,x+4.2,z+4.2,y+4.5)}
// farm: crop fields, a red barn and a silo
{const tex=['#e9d27a','#9cc46b','#c7df8a','#e6a04a'].map((c,k)=>{const cv=document.createElement('canvas');cv.width=cv.height=128;const x2=cv.getContext('2d');x2.fillStyle=c;x2.fillRect(0,0,128,128);x2.fillStyle=k===3?'#7aa04a':'rgba(90,70,30,.35)';for(let r=0;r<128;r+=16)x2.fillRect(0,r,128,k===3?6:4);if(k===3){x2.fillStyle='#f08a24';for(let q=0;q<40;q++){x2.beginPath();x2.arc(Math.random()*128,Math.floor(Math.random()*8)*16+3,4,0,7);x2.fill()}}const t=new Pe(cv);t.wrapS=t.wrapT=1e3;t.repeat.set(4,4);t.colorSpace=me;return new T.Mat({map:t})});
for(const[x,z,w,d,k]of N.fields){const pl=new T.Mesh(new Hn(w,d),tex[k]);pl.rotation.x=-Math.PI/2;if(k%2)pl.rotation.z=Math.PI/2*0;pl.position.set(x+w/2,ne(x+w/2,z+d/2)+.09,z+d/2);$t.add(pl)}
if(N.barn){const[x,z]=N.barn,y=ne(x,z),g=new T.Group();g.position.set(x,y,z);$t.add(g);box(18,9,24,'#c0392b',0,4.5,0,g);const sh=new T.Shape();sh.moveTo(-10,0);sh.lineTo(10,0);sh.lineTo(0,7);sh.lineTo(-10,0);
const rf=new T.Mesh(new T.Ext(sh,{depth:26,bevelEnabled:!1}),mat('#5a3a2a'));rf.position.set(0,9,-13);g.add(rf);box(7,7,.3,'#ffffff',0,3.5,12.1,g);box(6,6,.4,'#8e2a20',0,3.2,12.2,g);
const si=new T.Mesh(new T.Cyl(3.6,3.6,18,16),mat('#b8c4ce'));si.position.set(14,9,-6);g.add(si);const dm=new T.Mesh(new T.Sph(3.6,16,8,0,6.3,0,1.6),mat('#8a96a8'));dm.position.set(14,18,-6);g.add(dm);addSolid(x-9,z-12,x+9,z+12,y+14);addSolid(x+10.4,z-9.6,x+17.6,z-2.4,y+21.6)}}
// the beach: umbrellas and towels on the city side, swan boats on the lake
{const[lx,lz,rx,rz]=N.lake;const cols=['#ff5a5a','#ffd23c','#5ac8ff','#7fe08a','#ff8ad8'];for(let k=0;k<9;k++){const a=Math.PI*.95+k*.075*Math.PI,x=lx+Math.cos(a)*(rx+11),z=lz+Math.sin(a)*(rz+11);umbrella(x,z,cols[k%5])}
for(let k=0;k<3;k++){const g=new T.Group();box(3,1.2,4.4,'#ffffff',0,.6,0,g);const nk=new T.Mesh(new T.Cyl(.35,.45,3,8),mat('#ffffff'));nk.position.set(0,2.2,1.8);nk.rotation.x=-.2;g.add(nk);const hd=new T.Mesh(new T.Sph(.6,10,8),mat('#ffffff'));hd.position.set(0,3.7,2.1);g.add(hd);const bk=new T.Mesh(new T.Cone(.25,.7,8),mat('#f28c28'));bk.rotation.x=Math.PI/2;bk.position.set(0,3.6,2.8);g.add(bk);$t.add(g);
let t=k*2.1;LIVE.push(dt=>{t+=dt*.05;const x=lx+Math.cos(t)*rx*.55,z=lz+Math.sin(t)*rz*.5;g.position.set(x,.35+Math.sin(t*40)*.08,z);g.rotation.y=Math.atan2(-Math.sin(t)*rx,Math.cos(t)*rz)})}}}

for(const[k,x,z,w,d]of ie.critters||[])k==='soccer'?soccer(x,z,w,d):k==='pigeons'?pigeons(x,z,w,d):k==='elephant'&&elephant(x,z,w,d);
let lt=performance.now();const tick=now=>{const dt=Math.min(.05,(now-lt)/1e3);lt=now;for(const f of LIVE)f(dt);requestAnimationFrame(tick)};requestAnimationFrame(tick)}
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
rep('bi=en.spaceAt;', 'bi=en.spaceAt;{const SB=ie.skybridges||[];if(SB.length){const old=bi;bi=(x,z,y)=>{for(const[x0,z0,x1,z1,lo,hi]of SB)if(x>x0&&x<x1&&z>z0&&z<z1)return y<(lo+hi)/2?{f:He(x,z),c:lo,name:null}:{f:hi,c:1e4,name:null};return old?old(x,z,y):null}}}')
if NAT:
    rep('{let i=new Ft({color:12245655}),t=(o,a,c,l,f,h)=>{let u=[],p=[];for(let _=0;_<f;_++)for(let m=0;m<l;m++){let d=o+m*c,E=a+_*c;u.push(d,ne(d,E)+h(d,E),E)}',
        '{let i=new Ft({color:16777215,vertexColors:!0}),t=(o,a,c,l,f,h)=>{let u=[],p=[],cc=[];for(let _=0;_<f;_++)for(let m=0;m<l;m++){let d=o+m*c,E=a+_*c,y=ne(d,E);u.push(d,y+h(d,E),E);const k=groundCol(d,E,y);cc.push(k.r,k.g,k.b)}')
    rep('g.setAttribute("position",new Ut(u,3)),g.setIndex(p)', 'g.setAttribute("position",new Ut(u,3)),g.setAttribute("color",new Ut(cc,3)),g.setIndex(p)')
    rep('function d_(){', r'''function groundCol(x,z,y){const N=ie.nature,G=groundCol.c||(groundCol.c={grass:new Pt('#bad997'),forest:new Pt('#86b86f'),farm:new Pt('#c9b77a'),sand:new Pt('#f0dfa8'),hill:new Pt('#a3bb7c'),rock:new Pt('#a49a7c'),grey:new Pt('#8f8a86'),snow:new Pt('#ffffff')}),inP=(P,x,z)=>{let c=!1;for(let a=0,b=P.length-1;a<P.length;b=a++){const[xa,za]=P[a],[xb,zb]=P[b];za>z!=zb>z&&x<(xb-xa)*(z-za)/(zb-za)+xa&&(c=!c)}return c};
if(!N)return G.grass;const[lx,lz,rx,rz]=N.lake,b=N.beach;if(((x-lx)/(rx+b))**2+((z-lz)/(rz+b))**2<1)return G.sand;if(y<6){if(inP(N.forest,x,z))return G.forest;if(inP(N.farm,x,z))return G.farm;return G.grass}
const st=[[6,G.grass],[60,G.hill],[150,G.rock],[230,G.grey],[275,G.grey],[300,G.snow]];for(let k=1;k<st.length;k++)if(y<st[k][0]){const t=(y-st[k-1][0])/(st[k][0]-st[k-1][0]);return st[k-1][1].clone().lerp(st[k][1],t)}return G.snow}
function d_(){''')
    rep('F.y=Math.min(x,420)', 'F.y=Math.min(x,800)')
    rep('r.position.set(0,1.9,-2410),$t.add(r)', 'r.position.set(0,1.9,-2410)')   # no Han River out in the countryside          # high enough to fly over Mt. Pigeon
    rep('t=1800,e=new ce(.18,.25,4,5,1,!0)', 't=6000,e=new ce(.18,.25,4,5,1,!0)')   # a forest needs more trees on screen
    # the tunnel: room to fly through under the mountain
    rep('bi=en.spaceAt;{const SB=', 'bi=en.spaceAt;{const old0=bi;bi=(x,z,y)=>{if(window.__inTunnel&&y<9.5&&window.__inTunnel(x,z))return{f:.3,c:8.6,name:null};for(const[a,b,c,d,lo]of window.__gantries||[]){const dx=c-a,dz=d-b,L=dx*dx+dz*dz;let t=((x-a)*dx+(z-b)*dz)/L;if(t>.08&&t<.92){const px=a+dx*t-x,pz=b+dz*t-z;if(px*px+pz*pz<2.2){const f0=old0?old0(x,z,y):null;return y<lo+1?{f:f0?f0.f:He(x,z),c:lo,name:null}:{f:lo+4.2,c:1e4,name:null}}}}return old0?old0(x,z,y):null}}{const SB=')
# ---- Pigeon Pigeon: the name, a P P logo, and snack spacing that suits a small city
rep('<h1>Banpo Pigeon</h1>', '<h1>Pigeon Pigeon</h1>')
rep('<h1>Seocho Person</h1>', '<h1>Pigeon Person</h1>')
rep('aria-label="Banpo Pigeon logo"', 'aria-label="Pigeon Pigeon logo"')
BEE = 'M0 0 h17 a14 14 0 0 1 3 27.5 a15.5 15.5 0 0 1 -3 32.5 h-17 z M9 9 v15 h7 a7.5 7.5 0 0 0 0 -15 z M9 33 v18 h8 a9 9 0 0 0 0 -18 z'
PEE = 'M0 0 h16 a15 15 0 0 1 0 30 h-7 v30 h-9 z M9 9 v12 h7 a6 6 0 0 0 0 -12 z'
rep(BEE, PEE, 2)
if 'R.z-y[1])<80)' in s: rep('R.z-y[1])<80)', 'R.z-y[1])<SPACING)'.replace('SPACING', str(SNACK_SPACING)))   # Math Island build: spread the snacks out a bit
# words on the screens
rep('<title>Banpo Pigeon · Seocho Person</title>', '<title>Pigeon Pigeon</title>')
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
