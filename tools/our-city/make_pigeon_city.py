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
    (r'arcade', '#2b1b4a', '#ff5ad1'),
    (r'museum', '#7a1f2b', '#f3e2b0'),
    (r'ticket', '#e8463c', '#ffffff'),
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
stand_count = []
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
    elif it['k'] == 'p' and re.search(r'\bcat\b', n): CRITTERS.append(['bigcats', it['x'], it['z'], it['w'], it['d']])
    elif it['k'] == 'court': CRITTERS.append(['basketball', it['x'], it['z'], it['w'], it['d']])
    elif it['k'] == 'playground': CRITTERS.append(['playground', it['x'], it['z'], it['w'], it['d']])
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
            poly = rect(x, z, w, d, .6)
            for sc_ in C['items']:
                if sc_['k'] == 'secret' and x < sc_['x'] + 1 < x + w and z < sc_['z'] + 1 < z + d:   # cut the corner out for the secret room
                    sx0, sz0 = sc_['x'], sc_['z']; x1_, z1_ = x + w - .6, z + d - .6
                    poly = [x + .6, z + .6, x + .6, z1_, sx0, z1_, sx0, sz0, x1_, sz0, x1_, z + .6]
            buildings.append([round(h, 1), clean, 5, style, ccw(poly), n or '', hexcol(c), 1 if (k == 's' or clean) else 0, pitched])
        if n and n not in ('House', 'Apartment'):
            bg, fg = sign_style(n)
            sw = round(max(2.5, min(L - .8, 9, 1.6 + .55 * len(n))), 1)
            signs.append([round(mx + nx * .02, 2), round(mz + nz * .02, 2), round(math.atan2(nx, nz), 3), 0, sw, bg, fg, n, 'SH'])
        if k == 's':
            snacks.append([snack_kind(n), n or 'Shop', round(mx + nx * 2.5, 1), round(mz + nz * 2.5, 1)])   # by the entrance, under the sign
    elif k in ('p', 'g', 'f'):
        areas.append([2 if k == 'f' else 0, ccw(rect(x, z, w, d))])
        if k != 'f':
            for _ in range(max(1, round(w * d / ((160 if re.search(r'\bcat\b', n or '', re.I) else 45) if k == 'p' else 120)))):   # big cat park: open grass so you can see the cats
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
    elif k == 'stand':   # little snack stand (kiosk with a striped awning)
        mx, mz, nx, nz, L = best_side(x, z, w, d)
        deco.append([k, x, z, w, d, c, n, round(math.atan2(nx, nz), 3)])
        solids.append([x + .5, z + .5, x + w - .5, z + d - .5, 3.6])
        if n:
            kind = 'apple' if re.search(r'apple|grape|melon|fruit|berr', n, re.I) else 'cafe' if re.search(r'milk|coffee|juice|tea', n, re.I) else 'bakery'
            snacks.append([kind, n, round(mx + nx * 2, 1), round(mz + nz * 2, 1)])
        elif stand_count.append(1) or len(stand_count) % 5 == 1:   # only 1 in 5 of the unnamed stands has food
            kind = random.choice(['cafe', 'bakery', 'convenience'])
            snacks.append([kind, {'cafe': 'Star Coffee Stand', 'bakery': 'Star Treats Stand', 'convenience': 'Star Snack Stand'}[kind], round(mx + nx * 2, 1), round(mz + nz * 2, 1)])
    elif k == 'fishing':   # a wooden fishing pier: people fishing, a snack stand at the land end
        deco.append([k, x, z, w, d, c, n])
        solids.append([x + .5, z + .5, x + w - .5, z + d - .5, 1.6])
        mx, mz, nx, nz, L = best_side(x, z, w, d)
        snacks.append(['convenience', n or 'Fishing Place', round(mx + nx * 2.5, 1), round(mz + nz * 2.5, 1)])
        if n: parksigns.append([round(mx + nx * 1.2, 1), round(mz + nz * 1.2, 1), round(math.atan2(nx, nz), 3), n])
    elif k in ('museum', 'rocket'):   # built in the game; collision comes from their real shape
        mx, mz, nx, nz, L = best_side(x, z, w, d)
        deco.append([k, x, z, w, d, c, n, round(math.atan2(nx, nz), 3), f])
        if k == 'museum':
            snacks.append(['cafe', 'Museum Cafe', round(mx + nx * 3, 1), round(mz + nz * 3, 1)])
            snacks.append(['bakery', 'Dino Bites', round(x + w / 2 + nx * 2, 1), round(z + d / 2 + nz * 2, 1), 2.6])   # inside, by the T-rex
    elif k in ('balloon', 'merrygoround', 'towerride', 'parking'):
        deco.append([k, x, z, w, d, c, n, f])
        if k == 'towerride': solids.append([x + w / 2 - 2.2, z + d / 2 - 2.2, x + w / 2 + 2.2, z + d / 2 + 2.2, f * FLOOR + 4])
        if n and k != 'towerride':
            mx, mz, nx, nz, L = best_side(x, z, w, d)
            parksigns.append([round(mx - nx * 1.2, 1), round(mz - nz * 1.2, 1), round(math.atan2(nx, nz), 3), n])
    elif k == 'secret':
        host = [o for o in C['items'] if o['k'] in ('b', 's') and o['x'] < x + 1 < o['x'] + o['w'] and o['z'] < z + 1 < o['z'] + o['d']]
        H_ = max(1, host[0]['f']) * FLOOR if host else 20
        deco.append([k, x, z, w, d, c, n, H_])
        snacks.append(['bakery', 'Secret treasure', round(x + w / 2 - 1, 1), round(z + d / 2 - 1.5, 1), 1.1])
    elif k == 'roof67':
        deco.append([k, x, z, w, d, c, n, f * FLOOR])
    elif k in ('picnic', 'train', 'aquarium'):
        deco.append([k, x, z, w, d, c, n, f])
        mx, mz, nx, nz, L = best_side(x, z, w, d)
        if k == 'aquarium':
            solids.append([x + .6, z + .6, x + w - .6, z + d - .6, f * FLOOR + 1])
            snacks.append(['convenience', 'Aquarium', round(mx + nx * 3, 1), round(mz + nz * 3, 1)])
            signs.append([round(mx + nx * .7, 2), round(mz + nz * .7, 2), round(math.atan2(nx, nz), 3), 0, 9, '#0b3d6b', '#7fe0ff', 'AQUARIUM', 'SH'])
        if k == 'picnic':
            snacks.append(['bakery', 'Picnic', round(x + w / 2, 1), round(z + d / 2, 1)])
            parksigns.append([round(mx - nx * 1.2, 1), round(mz - nz * 1.2, 1), round(math.atan2(nx, nz), 3), 'Picnic'])
    elif k == 'channel':
        areas.append([1, ccw(rect(x, z, w + 4, d))])
    elif k == 'pond':
        areas.append([1, ellipse(x + w / 2, z + d / 2, w / 2, d / 2)])
    elif k in ('court', 'playground', 'garbage'):
        deco.append([k, x, z, w, d, c, n])
        if k == 'garbage': solids.append([x + 3, z + 3, x + w - 3, z + d - 3, 4])
        if n:
            mx, mz, nx, nz, L = best_side(x, z, w, d)
            parksigns.append([round(mx - nx * 1.2, 1), round(mz - nz * 1.2, 1), round(math.atan2(nx, nz), 3), n])
    elif k in ('camp', 'cornfarm', 'policecar'):
        deco.append([k, x, z, w, d, c, n])
        if k == 'cornfarm': snacks.append(['bakery', 'Seed Pile', round(x + w - 5, 1), round(z + d / 2, 1), 3.9])   # on top of the seed pile
        if n:
            mx, mz, nx, nz, L = best_side(x, z, w, d)
            parksigns.append([round(mx - nx * 1.2, 1), round(mz - nz * 1.2, 1), round(math.atan2(nx, nz), 3), n])
    elif k == 'redpanda':
        deco.append([k, x, z, w, d, c, n])
        # (collision comes from the statue's real shape, worked out in the game)
    elif k in ('raccoon', 'cat', 'L67', 'LOL', 'pigeonstatue', 'pig', 'stickman'):
        deco.append([k, x, z, w, d, c, n, it.get('rot')])
        # collision comes from the statue's real shape (a fine height map made in the game), not a box
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

# round off sharp corners: each bend of more than ~20 degrees becomes a smooth curve (radius 18 m main, 12 m lanes)
def _fillet(P, R, avoid):
    P = [tuple(q) for q in P]
    closed = len(P) > 3 and math.dist(P[0], P[-1]) < .5
    def turn(k, Q):
        a_, b_, c_ = Q[k - 1], Q[k], Q[k + 1]
        u = (b_[0] - a_[0], b_[1] - a_[1]); v = (c_[0] - b_[0], c_[1] - b_[1])
        lu, lv = math.hypot(*u), math.hypot(*v)
        if lu < 1e-6 or lv < 1e-6: return 0
        return math.acos(max(-1, min(1, (u[0] * v[0] + u[1] * v[1]) / lu / lv)))
    if closed:   # start the loop half-way along a straight bit so no corner sits at the seam
        Q = P[:-1]; n = len(Q)
        ang = []
        for k in range(n):
            a_, b_, c_ = Q[k - 1], Q[k], Q[(k + 1) % n]
            ang.append(turn(1, [a_, b_, c_]))
        if max(ang) < .35: return [v for q in P for v in q]
        corners = [k for k in range(n) if ang[k] > .35]
        far = max(range(n), key=lambda k: min(min(abs(k - c), n - abs(k - c)) for c in corners))
        Q = Q[far:] + Q[:far]; P = Q + [Q[0]]
    D = [0.0]
    for k in range(1, len(P)): D.append(D[-1] + math.dist(P[k - 1], P[k]))
    cs = [(k, turn(k, P)) for k in range(1, len(P) - 1)]
    cs = [(k, t) for k, t in cs if t > .35]
    if not cs: return [v for q in P for v in q]
    def at(d):
        d = max(0, min(D[-1], d))
        for k in range(1, len(P)):
            if D[k] >= d:
                t = (d - D[k - 1]) / ((D[k] - D[k - 1]) or 1)
                return (P[k - 1][0] + (P[k][0] - P[k - 1][0]) * t, P[k - 1][1] + (P[k][1] - P[k - 1][1]) * t)
        return P[-1]
    cut = []
    for i, (k, t) in enumerate(cs):
        d = R * math.tan(t / 2)
        prev = D[cs[i - 1][0]] if i else 0; nxt = D[cs[i + 1][0]] if i + 1 < len(cs) else D[-1]
        lim_a = (D[k] - prev) * (.48 if i else .9); lim_b = (nxt - D[k]) * (.48 if i + 1 < len(cs) else .9)
        d = min(d, lim_a, lim_b)
        for e in avoid:   # another road joins near this corner: keep the curve short of it
            de = math.dist(P[k], e)
            if de < d + 6: d = min(d, de - 8)
        if d > .5: cut.append((D[k] - d, D[k] + d, P[k]))
    out = []; ci = 0; k = 0
    while k < len(P):
        if ci < len(cut) and D[k] >= cut[ci][0]:
            A, B, Cn = at(cut[ci][0]), at(cut[ci][1]), cut[ci][2]
            m = max(4, int((cut[ci][1] - cut[ci][0]) / 2.5))
            for j in range(m + 1):
                t = j / m
                out.append(((1 - t) ** 2 * A[0] + 2 * (1 - t) * t * Cn[0] + t * t * B[0], (1 - t) ** 2 * A[1] + 2 * (1 - t) * t * Cn[1] + t * t * B[1]))
            while k < len(P) and D[k] <= cut[ci][1]: k += 1
            ci += 1
            continue
        out.append(P[k]); k += 1
    return [round(v, 2) for q in out for v in q]
_ends = [(r_[2][i_], r_[2][i_ + 1]) for r_ in roads for i_ in (0, len(r_[2]) - 2)]
for r_ in roads:
    if r_[3] == 'Roundabout': continue
    P_ = [(r_[2][i_], r_[2][i_ + 1]) for i_ in range(0, len(r_[2]), 2)]
    own = {P_[0], P_[-1]}
    r_[2] = _fillet(P_, 18 if r_[1] else 12, [e for e in _ends if e not in own])

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
    for ax_, az_ in NAT.get('apples', []): snacks.append(['apple', 'Raccoon Forest apple', ax_ + 1.5, az_ + 1.5, 1.1])
    # the river boat: from the foot of the mountain down the river and out into the lake
    route = [list(q) for q in R] + [[lx - lrx * .1, lz - lrz * .2], [lx + lrx * .25, lz + lrz * .1]]
    NAT['boat'] = route
    # bridges: every stretch of road over the river or lake becomes a bridge 7.5 m up (with 25 m ramps),
    # so the boat fits underneath and nothing stands in the water
    RIVPOLY = Lp + Rp[::-1]
    def in_poly(P, x, z):
        c = False
        for k_ in range(len(P)):
            (x1, z1), (x2, z2) = P[k_ - 1], P[k_]
            if (z1 > z) != (z2 > z) and x < (x2 - x1) * (z - z1) / (z2 - z1) + x1: c = not c
        return c
    def wet(x, z): return ((x - lx) / (lrx + 3)) ** 2 + ((z - lz) / (lrz + 3)) ** 2 < 1 or in_poly(RIVPOLY, x, z)
    BH, RAMP, GR = 7.5, 26.0, 2.0
    # roads that end out in the water stop at the bank instead of hanging in mid-air
    for r_ in roads:
        P_ = [(r_[2][i_], r_[2][i_ + 1]) for i_ in range(0, len(r_[2]), 2)]
        if len(P_) < 2 or r_[3] == 'Roundabout': continue
        for rev in (0, 1):
            if wet(*P_[-1]):
                k_ = len(P_) - 1
                while k_ > 0 and wet(*P_[k_]): k_ -= 1
                P_ = P_[:k_ + 1]
            P_ = P_[::-1]
        r_[2] = [v for q in P_ for v in q] if len(P_) >= 2 else r_[2]
    # every road as 2 m samples with its distance along the road
    RD = []
    for rw, major, pts, *_ in roads:
        P_ = [(pts[i_], pts[i_ + 1]) for i_ in range(0, len(pts), 2)]
        S_ = []
        for a_, b_ in zip(P_, P_[1:]):
            L_ = math.hypot(b_[0] - a_[0], b_[1] - a_[1]); n_ = max(1, int(L_ / 2))
            S_ += [(a_[0] + (b_[0] - a_[0]) * t_ / n_, a_[1] + (b_[1] - a_[1]) * t_ / n_) for t_ in range(n_)]
        S_.append(P_[-1])
        D_ = [0.0]
        for k_ in range(1, len(S_)): D_.append(D_[-1] + math.hypot(S_[k_][0] - S_[k_ - 1][0], S_[k_][1] - S_[k_ - 1][1]))
        W_ = [wet(x_, z_) for x_, z_ in S_]
        src = []   # [from, to, height]: flat at that height, smooth ramps down either side
        k_ = 0
        while k_ < len(S_):
            if W_[k_]:
                j_ = k_
                while j_ + 1 < len(S_) and W_[j_ + 1]: j_ += 1
                src.append([D_[k_] - 4, D_[j_] + 4, BH]); k_ = j_ + 1
            else: k_ += 1
        RD.append({'w': rw, 'major': major, 'S': S_, 'D': D_, 'src': src, 'jn': {}})
    def Hat(R_, d):
        h = 0
        for a_, b_, hh in list(R_['src']) + list(R_['jn'].values()):
            dd = max(a_ - d, d - b_, 0); t_ = max(0, 1 - dd / RAMP); h = max(h, hh * t_ * t_ * (3 - 2 * t_))
        return h
    # junctions: where a road's end meets another road, both share one height there (so side roads ramp up too)
    JN = []
    for ia, A_ in enumerate(RD):
        for end in (0, -1):
            ex, ez = A_['S'][end]
            best = None
            for ib, B_ in enumerate(RD):
                if ib == ia: continue
                for k_, (x_, z_) in enumerate(B_['S']):
                    dd = math.hypot(x_ - ex, z_ - ez)
                    if dd < B_['w'] / 2 + 1.5 and (best is None or dd < best[0]): best = (dd, ib, k_)
            if best: JN.append((ia, A_['D'][end], best[1], RD[best[1]]['D'][best[2]]))
    for it_ in range(6):
        for ia, da, ib, db in JN:
            h = max(Hat(RD[ia], da), Hat(RD[ib], db))
            if h > .05:
                RD[ia]['jn'][(ib, round(db))] = [da - RD[ib]['w'] / 2 - 1, da + RD[ib]['w'] / 2 + 1, h]
                RD[ib]['jn'][(ia, round(da))] = [db - RD[ia]['w'] / 2 - 1, db + RD[ia]['w'] / 2 + 1, h]
    for R_ in RD: R_['H'] = [round(Hat(R_, d), 2) for d in R_['D']]
    def deck(R_): return R_['w'] / 2 + (5.4 if R_['major'] else 1.0)
    def on_other(x, z, me):
        for ib, B_ in enumerate(RD):
            if ib == me: continue
            lim = (B_['w'] / 2 + (5.2 if B_['major'] else .5)) ** 2
            for x_, z_ in B_['S'][::1]:
                if (x_ - x) ** 2 + (z_ - z) ** 2 < lim: return True
        return False
    # the height grid: each 2 m cell takes the height of the road it is most "inside"
    best = {}
    for ia, R_ in enumerate(RD):
        if max(R_['H']) < .05: continue
        reach = deck(R_) + 1
        for (x_, z_), h_ in zip(R_['S'], R_['H']):
            for ci in range(int((x_ - reach) // GR), int((x_ + reach) // GR) + 1):
                for cj in range(int((z_ - reach) // GR), int((z_ + reach) // GR) + 1):
                    dd = math.hypot(ci * GR + GR / 2 - x_, cj * GR + GR / 2 - z_)
                    if dd < reach:
                        sc = dd - R_['w'] / 2
                        if (ci, cj) not in best or sc < best[(ci, cj)][0] - .01 or (abs(sc - best[(ci, cj)][0]) <= .01 and h_ > best[(ci, cj)][1]):
                            best[(ci, cj)] = (sc, h_)
    # any road near a raised cell also claims cells (so a flat road next to a ramp stays flat)
    for ia, R_ in enumerate(RD):
        if max(R_['H']) >= .05: continue
        reach = deck(R_) + 1
        for (x_, z_) in R_['S']:
            for ci in range(int((x_ - reach) // GR), int((x_ + reach) // GR) + 1):
                for cj in range(int((z_ - reach) // GR), int((z_ + reach) // GR) + 1):
                    if (ci, cj) in best:
                        dd = math.hypot(ci * GR + GR / 2 - x_, cj * GR + GR / 2 - z_); sc = dd - R_['w'] / 2
                        if sc < best[(ci, cj)][0] - .01: best[(ci, cj)] = (sc, 0)
    cells = {k_: v_[1] for k_, v_ in best.items() if v_[1] > .02}
    spans = []
    for ia, R_ in enumerate(RD):
        cur = []
        dh = deck(R_)
        for k_ in range(len(R_['S'])):
            if R_['H'][k_] > .05:
                x_, z_ = R_['S'][k_]
                p0, p1 = R_['S'][max(0, k_ - 1)], R_['S'][min(len(R_['S']) - 1, k_ + 1)]
                tx, tz = p1[0] - p0[0], p1[1] - p0[1]; tl = math.hypot(tx, tz) or 1; nx_, nz_ = -tz / tl, tx / tl
                fl = [0 if on_other(x_ + nx_ * sd * dh, z_ + nz_ * sd * dh, ia) else 1 for sd in (-1, 1)]
                cur.append([round(x_, 1), round(z_, 1), R_['H'][k_], fl[0], fl[1]])
            elif cur: spans.append([R_['w'] / 2, cur, round(dh, 2)]); cur = []
        if cur: spans.append([R_['w'] / 2, cur, round(dh, 2)])
    if cells:
        i0 = min(c[0] for c in cells); i1 = max(c[0] for c in cells); j0 = min(c[1] for c in cells); j1 = max(c[1] for c in cells)
        nxg, nzg = i1 - i0 + 1, j1 - j0 + 1
        grid = [0] * (nxg * nzg)
        for (ci, cj), h_ in cells.items(): grid[(cj - j0) * nxg + ci - i0] = h_
        bridges = {'x0': i0 * GR, 'z0': j0 * GR, 'r': GR, 'nx': nxg, 'nz': nzg, 'h': grid, 'spans': spans}
    else: bridges = {}
    print('bridge spans:', len(spans), 'grid', len(cells))
    face = lambda x, z: round(math.atan2(300 - x, 210 - z), 3)
    for x, z, n in [(688, 420, 'Pigeon Lake'), (-118, 432, 'Pigeon Farm'), (-128, 70, 'Raccoon Forest')]:
        parksigns.append([x, z, face(x, z), n])
city = {'home': -1, 'bounds': C.get('bounds') or [-40.0, -40.0, 640.0, 460.0], 'nature': NAT, 'buildings': buildings, 'roads': roads, 'areas': areas,
        'rails': [], 'stations': [], 'snacks': snacks, 'signs': signs, 'trees': trees, 'crosswalks': [], 'dong': [],
        'billboards': [], 'terrain': terrain, 'parksigns': parksigns, 'bridges': bridges if NAT else {}, 'skybridges': SKYBRIDGES, 'critters': CRITTERS, 'planes': PLANES, 'solids': solids, 'deco': deco}
s = s[:i + len(TAG)] + json.dumps(city, ensure_ascii=False, separators=(',', ':')) + s[j:]

# ---------- engine patches ----------
def rep(a, b, count=1):
    global s
    n = s.count(a)
    assert n == count, (a[:70], n)
    s = s.replace(a, b)

# no Seoul subway exits (Gangnam / Nonhyeon stations sit inside the bigger map)
rep('[10,-17.2,4.6,1]]}],t=[.359,.933]', '[10,-17.2,4.6,1]]}].filter(()=>!1),t=[.359,.933]')
# no Seoul underpasses
# camera: only aim down at the floor inside real indoor spaces (with a ceiling), not over roads, bridges, statues or boats
rep('b&&b.f<F.y-.2&&(xr.y=b.f+(f?1.2:.45))', 'b&&b.c<1e3&&b.f<F.y-.2&&(xr.y=b.f+(f?1.2:.45))')
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

// T-rex skeleton on a platform, facing +x, about S metres long
function trex(G,S,H){const B='#efe6d2',k=S/14;const g=new T.Group();g.scale.setScalar(k);G.add(g);const bone=(geo,px,py,pz)=>{const m=new T.Mesh(geo,mat(B));m.position.set(px,py,pz);g.add(m);return m};
const lim=(a,b,r)=>{const L=Math.hypot(b[0]-a[0],b[1]-a[1],b[2]-a[2]);const m=bone(new T.Cyl(r,r*.8,L,8),(a[0]+b[0])/2,(a[1]+b[1])/2,(a[2]+b[2])/2);m.lookAt(b[0],b[1],b[2]);m.rotateX(Math.PI/2);bone(new T.Sph(r*1.15,8,6),b[0],b[1],b[2])};
const pl=new T.Mesh(new T.Box(15,.5,5),mat('#5a4a3a'));pl.position.y=.25;g.add(pl);const sign=new T.Mesh(new T.Box(2.4,1,.15),mat('#3a2a1a'));sign.position.set(5.5,.9,2.6);sign.rotation.x=-.3;g.add(sign);
const sp=[];for(let i=0;i<=30;i++){const t=i/30,x=-7+t*12.2,y=4.6+Math.sin(t*Math.PI*.9)*1.2-(t<.35?(.35-t)*5:0)+(t>.85?(t-.85)*6:0);sp.push([x,y])}
sp.forEach(([x,y],i)=>{const r=i<10?.12+i*.03:i>25?.32:.42;bone(new T.Sph(r,8,6),x,y,0);if(i>8&&i<27&&i%2===0){const sp2=bone(new T.Cyl(.06,.1,.7,5),x,y+.45,0)}});
for(let i=11;i<=22;i++){const[x,y]=sp[i],r=1.1+Math.sin((i-11)/11*Math.PI)*.8;const rib=new T.Mesh(new Vo(r,.07,5,14,Math.PI*1.05),mat(B));rib.position.set(x,y-r*.95,0);rib.rotation.y=Math.PI/2;rib.rotation.z=Math.PI/2;g.add(rib)}
const[hx,hy]=sp[13];for(const s of[-1,1]){const hip=[hx,hy-.2,s*.7],kn=[hx+1.2,hy-2.4,s*.9],an=[hx-.4,hy-4.1,s*.9],ft=[hx+.6,.75,s*.95];lim(hip,kn,.32);lim(kn,an,.22);lim(an,ft,.16);
for(const o of[-.25,0,.25])lim(ft,[ft[0]+1,.55,ft[2]+o],.07)}
const[cx,cy]=sp[24];for(const s of[-1,1]){const sh=[cx,cy-.9,s*.6],el=[cx+.5,cy-1.6,s*.75];lim(sh,el,.09);lim(el,[cx+.9,cy-1.4,s*.75],.07)}
const[nx,ny]=sp[30],sk=new T.Group();sk.position.set(nx+.6,ny+.2,0);sk.rotation.z=-.15;g.add(sk);const sb=(geo,px,py,pz,sx=1,sy=1,sz=1)=>{const m=new T.Mesh(geo,mat(B));m.position.set(px,py,pz);m.scale.set(sx,sy,sz);sk.add(m);return m};
sb(new T.Box(2.4,.9,1.2),.8,.2,0);sb(new T.Box(1.4,.6,1),2.3,.05,0);const jaw=new T.Group();jaw.position.set(0,-.3,0);jaw.rotation.z=-.25;sk.add(jaw);const jb=new T.Mesh(new T.Box(3.4,.3,1),mat(B));jb.position.set(1.4,-.2,0);jaw.add(jb);
for(let i=0;i<7;i++){const tt=new T.Mesh(new T.Cone(.08,.35,5),mat('#ffffff'));tt.position.set(.6+i*.42,-.32,.42);tt.rotation.z=Math.PI;sk.add(tt);const t2=tt.clone();t2.position.z=-.42;sk.add(t2);const lb=new T.Mesh(new T.Cone(.07,.3,5),mat('#ffffff'));lb.position.set(.6+i*.42,0,.42);jaw.add(lb);const l2=lb.clone();l2.position.z=-.42;jaw.add(l2)}
for(const s of[-1,1]){const e=new T.Mesh(new T.Sph(.25,8,6),mat('#2a2018'));e.position.set(.6,.45,s*.55);sk.add(e)}
for(const p of[[-3,0],[3,0]]){const pole=new T.Mesh(new T.Cyl(.05,.05,4,5),mat('#555'));pole.position.set(p[0],2.5,0);g.add(pole)}
(function jw(){jaw.rotation.z=-.2-Math.max(0,Math.sin(performance.now()/1400))*.15;requestAnimationFrame(jw)})()}
function letters(x,z,w,d,parts){const g=new T.Group();box(Math.max(w,8),2,Math.max(d,6),'#cfc8b8',0,1,0,g);const step=11,st=-(parts.length-1)*step/2;
parts.forEach(([sh,c],i)=>{const m=new T.Mesh(new T.Ext(sh,{depth:3,bevelEnabled:!0,bevelSize:.4,bevelThickness:.4,bevelSegments:2}),mat(c));m.position.set(st+i*step-4.5,2,-1.5);g.add(m)});
const sc=Math.min(1.2,Math.max(.6,w/(parts.length*11)));g.scale.set(sc,sc*1.3,sc);g.position.set(x+w/2,0,z+d/2);g.rotation.y=-.5;$t.add(g)}
{const mark=(x,z)=>{const i=Math.floor((x-Yt)/Zt),j=Math.floor((z-jt)/Zt);if(i>=0&&j>=0&&i<fe&&j<Ke){const q=j*fe+i;$i[q]<.05&&($i[q]=.05)}};
for(const[t,P]of ie.areas||[]){if(t!==1)continue;let x0=1e9,z0=1e9,x1=-1e9,z1=-1e9;for(let k=0;k<P.length;k+=2){x0=Math.min(x0,P[k]);x1=Math.max(x1,P[k]);z0=Math.min(z0,P[k+1]);z1=Math.max(z1,P[k+1])}
for(let z=z0-2;z<=z1+2;z+=Zt)for(let x=x0-2;x<=x1+2;x+=Zt){let c=!1;for(let a=0,b=P.length-2;a<P.length;b=a,a+=2){const xa=P[a],za=P[a+1],xb=P[b],zb=P[b+1];za>z!=zb>z&&x<(xb-xa)*(z-za)/(zb-za)+xa&&(c=!c)}c&&mark(x,z)}}
const BG=ie.bridges||{};if(BG.h)for(let j=0;j<BG.nz;j++)for(let i=0;i<BG.nx;i++)BG.h[j*BG.nx+i]>.3&&mark(BG.x0+(i+.5)*BG.r,BG.z0+(j+.5)*BG.r)}
const n0=$t.children.length;
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
else if(k==='stickman'){const g=new T.Group(),S=Math.min(w,d)/26,K='#1e2124';const add=(geo,c,px,py,pz)=>{const m=new T.Mesh(geo,mat(c));m.position.set(px,py,pz);g.add(m);return m};
add(new T.Box(22,3,22),'#cfc8b8',0,1.5,0);const lim=(ax,ay,bx,by)=>{const L=Math.hypot(bx-ax,by-ay),m=add(new T.Cyl(.9,.9,L,10),K,(ax+bx)/2,(ay+by)/2,0);m.rotation.z=-Math.atan2(bx-ax,by-ay);add(new T.Sph(.9,10,8),K,bx,by,0)};
lim(-4,3,0,12);lim(4,3,0,12);lim(0,12,0,21);lim(0,19,-6,15);lim(0,19,6,25);add(new T.Sph(.9,10,8),K,0,12,0);
add(new T.Sph(3.4,20,16),'#ffffff',0,25.5,0);const ring=new T.Mesh(new Vo(3.4,.45,8,24),mat(K));ring.position.set(0,25.5,0);g.add(ring);
for(const s of[-1,1])add(new T.Sph(.5,8,6),K,s*1.2,26.3,3.1);const sm=new T.Mesh(new Vo(1.3,.22,6,16,Math.PI),mat(K));sm.position.set(0,25,3.2);sm.rotation.z=Math.PI;g.add(sm);
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
g.scale.setScalar(Math.max(.4,S));g.position.set(x+w/2,0,z+d/2);g.rotation.y=f!=null?f:0;$t.add(g)}
else if(k==='cat')animal(x,z,w,d,{body:'#f2a65a',belly:'#fff1dc',nose:'#f27a8a',mask:!1,stripes:!1});
else if(k==='redpanda')redpanda(x,z,w,d);
else if(k==='museum'){const g=new T.Group(),Wd=Math.abs(Math.sin(n2r(f)))>.5?d:w,Dp=Math.abs(Math.sin(n2r(f)))>.5?w:d,H=Math.max(3,(ie.deco.find(q=>q[0]==='museum'&&q[1]===x)||[])[8]||4)*3.2,M='#eeeae0',Mx='#d9d3c4';
function n2r(v){return v}const L=Wd-1.5,D=Dp-1.5,PD=Math.min(5,D*.3);box(L,1.4,D,Mx,0,.7,0,g);for(let i=0;i<4;i++)box(L*.7,.35,1,Mx,0,.18+i*.35,D/2+.4+(3-i)*.5,g);
{const HW=L-.6,HD=D-PD,zc=-PD/2,fz=zc+HD/2,bz=zc-HD/2,T2=.5,DW=7,DH=7.5;box(HW,H,T2,M,0,1.4+H/2,bz+T2/2,g);for(const s of[-1,1])box(T2,H,HD,M,s*(HW/2-T2/2),1.4+H/2,zc,g);
const sw=(HW-DW)/2;for(const s of[-1,1])box(sw,H,T2,M,s*(DW/2+sw/2),1.4+H/2,fz-T2/2,g);box(DW,H-DH,T2,M,0,1.4+DH+(H-DH)/2,fz-T2/2,g);
const fl=new T.Mesh(new Hn(HW-1,HD-1),mat('#c9b48a'));fl.rotation.x=-Math.PI/2;fl.position.set(0,1.42,zc);g.add(fl);for(let i=-2;i<=2;i++)box(HW-1.2,.02,.08,'#a8946a',0,1.44,zc+i*HD/5,g);
const ins=new T.Mesh(new Hn(HW-1,H-.2),mat('#f3ecdc'));ins.position.set(0,1.4+H/2,bz+T2+.01);g.add(ins);
for(const s of[-1,1])for(let k=0;k<3;k++){const fr=box(.1,2.6,3.4,['#8a5a2a','#3a6a8a','#6a3a5a'][k],s*(HW/2-T2-.06),1.4+4.2,zc-HD/3+k*HD/3,g);box(.12,2,2.8,['#e9cf8a','#bfe0f0','#f0c0d0'][k],s*(HW/2-T2-.12),1.4+4.2,zc-HD/3+k*HD/3,g)}
const g2=new T.Group();g2.position.set(0,1.4,zc-HD*.05);g.add(g2);trex(g2,Math.min(HW*.62,HD*1.1,17),H);
window.__MUSEUM=window.__MUSEUM||[];window.__MUSEUM.push({cx:x+w/2,cz:z+d/2,f,HW,HD,zc,fz,bz,H,DW,DH,top:1.4+H+1,L,D})}
box(L,1,D,'#cfc8b8',0,1.4+H+.5,0,g);const nc=Math.max(4,Math.round(L/3.2));for(let i=0;i<nc;i++){const cx2=-L/2+1+i*(L-2)/(nc-1);const c=new T.Mesh(new T.Cyl(.55,.62,H,14),mat(M));c.position.set(cx2,1.4+H/2,D/2-PD/2);g.add(c);box(1.4,.4,1.4,Mx,cx2,1.6,D/2-PD/2,g);box(1.5,.4,1.5,Mx,cx2,1.4+H-.2,D/2-PD/2,g)}
const sh=new T.Shape();sh.moveTo(-L/2,0);sh.lineTo(L/2,0);sh.lineTo(0,Math.min(5,L*.16));sh.lineTo(-L/2,0);const pd=new T.Mesh(new T.Ext(sh,{depth:PD,bevelEnabled:!1}),mat(M));pd.position.set(0,1.4+H+1,D/2-PD);g.add(pd);
const cv=document.createElement('canvas');cv.width=512;cv.height=96;const c2=cv.getContext('2d');c2.fillStyle='#e4ddcc';c2.fillRect(0,0,512,96);c2.fillStyle='#6b5a3a';c2.font='bold 64px serif';c2.textAlign='center';c2.textBaseline='middle';c2.fillText((n||'MUSEUM').toUpperCase(),256,52);
const tx=new Pe(cv);tx.colorSpace=me;const fr=new T.Mesh(new Hn(Math.min(L*.6,14),Math.min(L*.6,14)*96/512),new Be({map:tx}));fr.position.set(0,1.4+H+.5,D/2+.02);g.add(fr);
for(const s of[-1,1])box(1.4,2.4,.15,'#3a4a5a',s*L*.28,1.4+H*.5,D/2-PD+.03,g);
const dm=new T.Mesh(new T.Sph(Math.min(D,L)*.22,24,12,0,6.3,0,1.6),mat('#7fb7a0'));dm.position.set(0,1.4+H+1,-PD/2);g.add(dm);
for(const s of[-1,1]){const bn=box(.15,H*.55,2.2,s<0?'#c0392b':'#2f6fdf',s*(L/2-.2),1.4+H*.55,D/2-PD-.2,g);bn.rotation.y=Math.PI/2}
g.userData.hollow=!0;g.position.set(x+w/2,0,z+d/2);g.rotation.y=f;$t.add(g)}
else if(k==='rocket'){const g=new T.Group(),Rr=3.2,BH=48;box(16,1.2,16,'#8d8a85',0,.6,0,g);box(14,.3,14,'#ffd23c',0,1.25,0,g);
const body=new T.Mesh(new T.Cyl(Rr,Rr,BH,28),mat('#f4f4f4'));body.position.y=1.2+BH/2+4;g.add(body);for(const yy of[10,26,42]){const b=new T.Mesh(new T.Cyl(Rr+.05,Rr+.05,2,28),mat('#e8463c'));b.position.y=1.2+4+yy;g.add(b)}
const nose=new T.Mesh(new T.Cone(Rr,13,28),mat('#e8463c'));nose.position.y=1.2+4+BH+6.5;g.add(nose);const eng=new T.Mesh(new T.Cyl(Rr*.75,Rr*1.05,4,20),mat('#555b63'));eng.position.y=1.2+2;g.add(eng);
for(let i=0;i<4;i++){const a=i*Math.PI/2,fin=new T.Group();fin.rotation.y=a;g.add(fin);const sh=new T.Shape();sh.moveTo(0,0);sh.lineTo(5,-2);sh.lineTo(5,3);sh.lineTo(0,12);sh.lineTo(0,0);const m=new T.Mesh(new T.Ext(sh,{depth:.5,bevelEnabled:!1}),mat('#e8463c'));m.position.set(Rr-.2,5.2,-.25);fin.add(m)}
for(const yy of[30,36]){const wdw=new T.Mesh(new T.Sph(1.1,14,10),mat('#2f6fdf'));wdw.scale.set(1,1,.35);wdw.position.set(0,1.2+4+yy,Rr-.15);g.add(wdw);const rim=new T.Mesh(new Vo(1.15,.18,8,20),mat('#c9ced3'));rim.position.set(0,1.2+4+yy,Rr);g.add(rim)}
const cv=document.createElement('canvas');cv.width=128;cv.height=512;const c2=cv.getContext('2d');c2.fillStyle='#f4f4f4';c2.fillRect(0,0,128,512);c2.fillStyle='#1f3a93';c2.font='bold 80px sans-serif';c2.textAlign='center';'OURCITY'.split('').forEach((ch,i)=>c2.fillText(ch,64,70+i*66));
const tx=new Pe(cv);tx.colorSpace=me;const lab=new T.Mesh(new Hn(3,12),new Be({map:tx}));lab.position.set(0,1.2+4+18,Rr+.03);g.add(lab);
const S=Math.min(w,d)/16;g.scale.setScalar(Math.max(.8,Math.min(1.2,S)));g.position.set(x+w/2,0,z+d/2);g.rotation.y=f;$t.add(g)}
else if(k==='roof67'){letters(x,z,w,d,[[SIX,'#8fd8ff'],[SEVEN,'#ff9acd']]);const g=$t.children[$t.children.length-1];g.position.y=f;g.rotation.y=0}
else if(k==='L67')letters(x,z,w,d,[[SIX,'#8fd8ff'],[SEVEN,'#ff9acd']]);
else if(k==='LOL')letters(x,z,w,d,[[ELL,'#ffd23c'],[OH,'#ff7a5a'],[ELL,'#7fc8ff']]);
else if(k==='f'){const L=(a,b,X,Z)=>box(a,.06,b,'#ffffff',X,.13,Z);L(w-4,.5,cx,z+2);L(w-4,.5,cx,z+d-2);L(.5,d-4,x+2,cz);L(.5,d-4,x+w-2,cz);w>d?L(.5,d-4,cx,cz):L(w-4,.5,cx,cz);const lg=w>d;[-1,1].forEach(s=>{const gx=lg?cx+s*(w/2-2.5):cx,gz=lg?cz:cz+s*(d/2-2.5);box(lg?.3:7,.3,lg?7:.3,'#ffffff',gx,2.4,gz);for(const o of[-3.4,3.4])box(.3,2.4,.3,'#ffffff',lg?gx:gx+o,1.2,lg?gz+o:gz)})}
else if(k==='g'){for(let q=0;q<w*d/6;q++){const fl=new T.Mesh(new T.Sph(.5,8,6),mat(c||'#e8463c'));fl.position.set(x+1+Wt(q+x)*(w-2),.4,z+1+Wt(q*7+z)*(d-2));$t.add(fl)}}
else if(k==='dock'){box(w,.6,d,'#8a5a3a',cx,.5,cz)}
}
// statues: a 0.5 m height map from their actual triangles, so landing and bumping match what you see
{const R=.5;window.__STAT=[];for(const g of $t.children.slice(n0)){if(!g.isGroup||g.userData.hollow)continue;g.updateMatrixWorld(!0);const tris=[];let x0=1e9,z0=1e9,x1=-1e9,z1=-1e9;
g.traverse(o=>{if(!o.isMesh||!o.geometry)return;const P=o.geometry.attributes.position,I=o.geometry.index,e=o.matrixWorld.elements,V=[];for(let i=0;i<P.count;i++){const a=P.getX(i),b=P.getY(i),c=P.getZ(i);const X=e[0]*a+e[4]*b+e[8]*c+e[12],Y=e[1]*a+e[5]*b+e[9]*c+e[13],Z=e[2]*a+e[6]*b+e[10]*c+e[14];V.push(X,Y,Z);X<x0&&(x0=X);X>x1&&(x1=X);Z<z0&&(z0=Z);Z>z1&&(z1=Z)}
const n=I?I.count:P.count;for(let t=0;t<n;t+=3){const A=I?I.getX(t):t,B=I?I.getX(t+1):t+1,C=I?I.getX(t+2):t+2;tris.push(V[A*3],V[A*3+1],V[A*3+2],V[B*3],V[B*3+1],V[B*3+2],V[C*3],V[C*3+1],V[C*3+2])}});
if(!tris.length)continue;const nx=Math.ceil((x1-x0)/R)+1,nz=Math.ceil((z1-z0)/R)+1,H=new Float32Array(nx*nz);
for(let t=0;t<tris.length;t+=9){const ax=tris[t],ay=tris[t+1],az=tris[t+2],bx=tris[t+3],by=tris[t+4],bz=tris[t+5],cx=tris[t+6],cy=tris[t+7],cz=tris[t+8];
const den=(bz-cz)*(ax-cx)+(cx-bx)*(az-cz);const i0=Math.max(0,Math.floor((Math.min(ax,bx,cx)-x0)/R)),i1=Math.min(nx-1,Math.ceil((Math.max(ax,bx,cx)-x0)/R)),j0=Math.max(0,Math.floor((Math.min(az,bz,cz)-z0)/R)),j1=Math.min(nz-1,Math.ceil((Math.max(az,bz,cz)-z0)/R));
if(Math.abs(den)<1e-9){const top=Math.max(ay,by,cy);for(let j=j0;j<=j1;j++)for(let i=i0;i<=i1;i++){const px=x0+(i+.5)*R,pz=z0+(j+.5)*R;if(px>=Math.min(ax,bx,cx)-R/2&&px<=Math.max(ax,bx,cx)+R/2&&pz>=Math.min(az,bz,cz)-R/2&&pz<=Math.max(az,bz,cz)+R/2){const q=j*nx+i;H[q]<top&&(H[q]=top)}}continue}
for(let j=j0;j<=j1;j++)for(let i=i0;i<=i1;i++){const px=x0+(i+.5)*R,pz=z0+(j+.5)*R,l1=((bz-cz)*(px-cx)+(cx-bx)*(pz-cz))/den,l2=((cz-az)*(px-cx)+(ax-cx)*(pz-cz))/den,l3=1-l1-l2;
if(l1>=-.02&&l2>=-.02&&l3>=-.02){const y=l1*ay+l2*by+l3*cy,q=j*nx+i;H[q]<y&&(H[q]=y)}}}
window.__STAT.push({x0,z0,nx,nz,r:R,h:H})}}
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
// crops: real plants in rows (wheat, cabbages, corn, pumpkins), drawn with instancing so it stays fast
{const kinds=[ // [row gap, plant gap, parts: [geometry, colour, y, scale jitter]]
 [1.3,.9,[[new T.Cyl(.05,.07,1.3,4),'#c9a640',.65],[new T.Cone(.14,.5,5),'#e8c75a',1.45]]],
 [1.5,1.2,[[new T.Sph(.5,8,6),'#7cc95e',.38],[new T.Sph(.34,8,6),'#a9de7a',.62]]],
 [1.6,1.1,[[new T.Cyl(.08,.11,2.4,5),'#5f9e3a',1.2],[new T.Box(1,.05,.22),'#79b84a',1.4],[new T.Cyl(.15,.15,.55,6),'#f2c94c',1.75]]],
 [2.2,1.9,[[new T.Sph(.55,10,7),'#f08a24',.42],[new T.Box(1.3,.08,.9),'#4f8f3a',.15]]]];
const pos=[[],[],[],[]];for(const[x,z,w,d,k]of N.fields){const K=kinds[k],long=w>=d;const A=long?w:d,B=long?d:w;
for(let b=.8;b<B-.5;b+=K[0])for(let a=.8;a<A-.5;a+=K[1]){const px=long?x+a:x+b,pz=long?z+b:z+a;pos[k].push(px+(rnd()-.5)*.25,pz+(rnd()-.5)*.25,rnd()*6.28,.8+rnd()*.4)}}
const M4=new ee,Q=new T.Group();kinds.forEach((K,k)=>{const n=pos[k].length/4;if(!n)return;for(const[geo,col,y]of K[2]){const im=new on(geo,new T.Mat({color:new Pt(col)}),n);
for(let i=0;i<n;i++){const px=pos[k][i*4],pz=pos[k][i*4+1],r=pos[k][i*4+2],s=pos[k][i*4+3];Q.position.set(px,ne(px,pz)+y*s+.1,pz);Q.rotation.set(0,r,0);Q.scale.set(s,s,s);Q.updateMatrix();im.setMatrixAt(i,Q.matrix)}im.instanceMatrix.needsUpdate=!0;$t.add(im)}})}
// apple trees in Raccoon Forest
for(const[x,z]of N.apples||[]){const y=ne(x,z),g=new T.Group();g.position.set(x,y,z);$t.add(g);box(.8,4,.8,'#6b4426',0,2,0,g);
for(const[a,b,c,r]of[[0,5.2,0,2.6],[1.4,4.6,.6,1.8],[-1.3,4.7,-.4,1.9],[.2,6.4,-.3,1.7]]){const m=new T.Mesh(new T.Sph(r,10,8),mat('#4f9a3a'));m.position.set(a,b,c);g.add(m)}
for(let q=0;q<16;q++){const a=rnd()*6.3,h=3.6+rnd()*3.2,r=1.8+rnd()*.9,m=new T.Mesh(new T.Sph(.26,8,6),mat('#d9262a'));m.position.set(Math.cos(a)*r,h,Math.sin(a)*r);g.add(m)}
for(let q=0;q<4;q++){const m=new T.Mesh(new T.Sph(.26,8,6),mat('#d9262a'));m.position.set(-2+rnd()*4,.25,-2+rnd()*4);g.add(m)}}
// bridges: deck slab, railings and support piers along every raised stretch of road
for(const[hw,P,dh0]of BRS){const dh=dh0||hw+1.2;for(let i=1;i<P.length;i++){const[a,b,ha,la,ra]=P[i-1],[c,d,hc,lc,rc]=P[i],L=Math.hypot(c-a,d-b);if(L<.3||Math.max(ha,hc)<.6)continue;const ux=(c-a)/L,uz=(d-b)/L,nx=-uz,nz=ux,mx=(a+c)/2,mz=(b+d)/2,h=(ha+hc)/2;
const y0=ne(mx,mz)+h,yaw=Math.atan2(ux,uz),pit=Math.atan2(hc-ha,L);const sl=box(dh*2,1.1,L+.25,'#8d8a85',mx,y0-.5,mz);sl.rotation.order='YXZ';sl.rotation.y=yaw;sl.rotation.x=-pit;
for(const[s,f]of[[-1,la!==0&&lc!==0],[1,ra!==0&&rc!==0]]){if(!f)continue;const r=box(.3,1,L+.25,'#e9e4d6',mx+nx*s*(dh-.15),y0+.65,mz+nz*s*(dh-.15));r.rotation.order='YXZ';r.rotation.y=yaw;r.rotation.x=-pit}
if(i%9===0&&h>3)for(const s of[-1,1])box(1.4,h,1.4,'#b9b4aa',mx+nx*s*(hw-1),ne(mx,mz)+h/2-.6,mz+nz*s*(hw-1))}}
// the river boat: back and forth between the mountain and the lake; birds can ride on its deck
if(N.boat&&N.boat.length>1){const P=N.boat,seg=[];let tot=0;for(let k=1;k<P.length;k++){const L=Math.hypot(P[k][0]-P[k-1][0],P[k][1]-P[k-1][1]);seg.push([P[k-1],P[k],L,tot]);tot+=L}
const at=s=>{for(const[a,b,L,o]of seg)if(s<=o+L){const t=(s-o)/L;return[a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t,Math.atan2(b[0]-a[0],b[1]-a[1])]}const a=P[P.length-2],b=P[P.length-1];return[b[0],b[1],Math.atan2(b[0]-a[0],b[1]-a[1])]};
const g=new T.Group();$t.add(g);const DECK=1.7,BW=3.2,BL=7;box(BW*2,1.4,BL*2,'#ffffff',0,.6,0,g);box(BW*2+.1,.35,BL*2+.1,'#2f6fdf',0,.5,0,g);const bow=new T.Mesh(new T.Cyl(BW,BW,1.4,3,1,!1,0,Math.PI),mat('#ffffff'));bow.rotation.y=Math.PI/2;bow.scale.set(1,1,.9);bow.position.set(0,.6,BL);g.add(bow);
box(BW*2-.4,.15,BL*2-.4,'#b07a45',0,DECK-.3,0,g);box(3.4,2.2,3.6,'#f4efe4',0,DECK+.8,-3.2,g);box(3.8,.25,4,'#e8463c',0,DECK+2,-3.2,g);for(const s of[-1,1])box(.08,.7,3.6,'#7fb8e8',s*1.72,DECK+1.1,-3.2,g);
box(.12,1.4,.12,'#555',0,DECK+2.8,-4.6,g);box(1,.55,.06,'#ffd23c',.5,DECK+3.2,-4.6,g);for(const s of[-1,1])box(.12,.5,BL*2-1,'#ffffff',s*(BW-.15),DECK+.1,0,g);
const ring=new T.Mesh(new Vo(.5,.16,8,16),mat('#ff7a1a'));ring.position.set(BW,DECK-.1,2);ring.rotation.y=Math.PI/2;g.add(ring);
const B={x:0,z:0,yaw:0};let s=0,d=1,wait=0;window.__boat=B;
window.__boatAt=(x,z)=>{const dx=x-B.x,dz=z-B.z,c=Math.cos(B.yaw),sn=Math.sin(B.yaw),lx=dx*c-dz*sn,lz=dx*sn+dz*c;return Math.abs(lx)<BW&&Math.abs(lz)<BL+1?DECK:null};
LIVE.push(dt=>{const ox=B.x,oz=B.z,oy=B.yaw;if(wait>0)wait-=dt;else{s+=d*6*dt;if(s>=tot){s=tot;d=-1;wait=4}if(s<=0){s=0;d=1;wait=4}}const[x,z,yw]=at(s);let want=yw+(d<0?Math.PI:0),dy=want-B.yaw;dy=Math.atan2(Math.sin(dy),Math.cos(dy));
B.yaw+=dy*Math.min(1,dt*1.5);B.x=x;B.z=z;const t=performance.now()/1e3;g.position.set(x,.15+Math.sin(t*1.7)*.08,z);g.rotation.set(Math.sin(t*1.3)*.02,B.yaw,Math.sin(t*1.1)*.025);
const Pl=window.__game&&window.__game.P;if(Pl&&ox&&Pl.grounded&&Math.abs(Pl.y-DECK)<1.6){const rx=Pl.x-ox,rz=Pl.z-oz,c=Math.cos(oy),sn=Math.sin(oy),lx=rx*c-rz*sn,lz=rx*sn+rz*c;
if(Math.abs(lx)<BW+.3&&Math.abs(lz)<BL+1.3){const c2=Math.cos(B.yaw),s2=Math.sin(B.yaw);Pl.x=B.x+lx*c2+lz*s2;Pl.z=B.z-lx*s2+lz*c2;Pl.yaw+=B.yaw-oy}}})}
}


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
// car ramps: an A-frame ramp across the road, cars fly off it
{const RA=N.ramps||[],UP=7,FLY=26,RH=2.2,PK=6;for(const[cx,cz,ux,uz,hw]of RA){const g=new T.Group();g.position.set(cx,0,cz);g.rotation.y=Math.atan2(ux,uz);$t.add(g);
const sh=new T.Shape();sh.moveTo(-UP,0);sh.lineTo(0,RH);sh.lineTo(UP*.45,0);sh.lineTo(-UP,0);const m=new T.Mesh(new T.Ext(sh,{depth:hw*2,bevelEnabled:!1}),mat('#d9a441'));m.rotation.y=-Math.PI/2;m.position.set(hw,0,0);g.add(m);
for(let k=0;k<5;k++){const st=box(.5,.04,Math.hypot(UP,RH)*.9,k%2?'#ffd23c':'#1e2124',-hw+.6+k*(hw*2-1.2)/4,RH/2+.08,-UP/2);st.rotation.x=Math.atan2(RH,UP)}}
// two stunt cars that drive back and forth over the ramp all day
for(const R of RA){const P=R[5];if(!P||P.length<2)continue;const seg=[];let tot=0;for(let k=1;k<P.length;k++){const L=Math.hypot(P[k][0]-P[k-1][0],P[k][1]-P[k-1][1]);seg.push([P[k-1],P[k],L,tot]);tot+=L}
const at=s=>{for(const[a,b,L,o]of seg)if(s<=o+L){const t=(s-o)/L;return[a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t,Math.atan2(b[0]-a[0],b[1]-a[1])]}const a=P[P.length-2],b=P[P.length-1];return[b[0],b[1],Math.atan2(b[0]-a[0],b[1]-a[1])]};
[['#ff3b3b',0,1],['#3b8fff',.5,-1]].forEach(([col,st,dir])=>{const g=new T.Group();$t.add(g);box(2,.8,4.2,col,0,.75,0,g);box(1.7,.7,2,col,0,1.45,-.3,g);box(1.72,.5,1.8,'#9fd3ff',0,1.45,-.3,g);box(2.02,.12,4.22,'#ffffff',0,1,0,g);
for(const[a,b]of[[-.9,1.3],[.9,1.3],[-.9,-1.3],[.9,-1.3]]){const wh=new T.Mesh(new T.Cyl(.42,.42,.35,12),mat('#222'));wh.rotation.z=Math.PI/2;wh.position.set(a,.42,b);g.add(wh)}
let s=st*tot,d=dir;const lane=1.9;LIVE.push(dt=>{s+=d*14*dt;if(s>tot){s=tot;d=-1}if(s<0){s=0;d=1}const[x,z,yaw]=at(s),f=yaw+(d<0?Math.PI:0),ox=Math.cos(f)*lane,oz=-Math.sin(f)*lane,px=x+ox,pz=z+oz;
const fx=Math.sin(f)*2,fz=Math.cos(f)*2,hf=window.__JP(px+fx,pz+fz,f),hb=window.__JP(px-fx,pz-fz,f),h=window.__JP(px,pz,f);g.position.set(px,ne(px,pz)+Math.max(h,(hf+hb)/2),pz);g.rotation.set(0,0,0);g.rotation.y=f;g.rotateX(-Math.atan2(hf-hb,4))})})}
window.__JP=(x,z,f)=>{for(const[cx,cz,ux,uz,hw]of RA){const dx=x-cx,dz=z-cz,lat=Math.abs(dx*uz-dz*ux);if(lat>hw+1)continue;const s=Math.sin(f)*ux+Math.cos(f)*uz>0?1:-1,t=(dx*ux+dz*uz)*s;
if(t>-UP&&t<=0)return RH*(t+UP)/UP;if(t>0&&t<FLY){const k=t/FLY;return RH*(1-k)+4*PK*k*(1-k)}}return 0}}
// the Mountain Road: drawn as its own ribbon a little above the slope (the game's road follows the ground too closely on steep hills)
if(N.mroad){const P=N.mroad,n=P.length,hw=4.6,SH=1.3;
// one smooth height for the road (the ground grid is coarse, so follow it loosely and never dip under it)
const NR=P.map((_,k)=>{const a=P[Math.max(0,k-3)],b=P[Math.min(n-1,k+3)],dx=b[0]-a[0],dz=b[1]-a[1],l=Math.hypot(dx,dz)||1;return[-dz/l,dx/l]});
const G=P.map(([x,z],k)=>{const[nx,nz]=NR[k];let m=Math.max(ne(x,z),(N.mroadh||[])[k]||0);for(const o of[-hw-SH,-hw/2,hw/2,hw+SH])m=Math.max(m,ne(x+nx*o,z+nz*o));return m});
// where it crosses another road: a level crossing at that road's height
const XR=P.map(([x,z])=>{for(const[w,,F]of ie.roads)for(let i=2;i<F.length;i+=2){const a=F[i-2],b=F[i-1],dx=F[i]-a,dz=F[i+1]-b,L=dx*dx+dz*dz||1;let t=((x-a)*dx+(z-b)*dz)/L;t=t<0?0:t>1?1:t;if(Math.hypot(a+dx*t-x,b+dz*t-z)<w/2+1.5)return 1}return 0});
const W=6;let M=G.map((_,k)=>{let m=-1e9;for(let j=Math.max(0,k-W);j<=Math.min(n-1,k+W);j++)m=Math.max(m,XR[j]?-1e9:G[j]);return XR[k]?ne(P[k][0],P[k][1]):m});
let Y=M.slice();for(let it=0;it<2;it++){const Z=Y.slice();for(let k=0;k<n;k++){if(XR[k]){Y[k]=Z[k];continue}let s=0,c=0;for(let j=Math.max(0,k-W);j<=Math.min(n-1,k+W);j++){s+=Z[j];c++}Y[k]=Math.max(s/c,XR[k]?0:G[k])}}Y=Y.map((y,k)=>y+(XR[k]?.33:.3));
// start just outside the ring road so the two road surfaces do not overlap
let K0=0;while(K0<n-2&&Math.hypot(P[K0][0]-P[0][0],P[K0][1]-P[0][1])<6.6)K0++;
const strip=(o0,o1,dy,col,every)=>{const V=[],I=[];let q=0;for(let k=0;k<n;k++){const[x,z]=P[k],[nx,nz]=NR[k],y=Y[k]+dy;V.push(x+nx*o0,y,z+nz*o0,x+nx*o1,y,z+nz*o1);if(k>K0){const o=(k-1)*2;if(!every||Math.floor(k/every)%2===0)I.push(o,o+2,o+1,o+1,o+2,o+3)}}
const g=new oe;g.setAttribute('position',new Ut(V,3));g.setIndex(I);g.computeVertexNormals();const m=new Dt(g,new Ft({color:col,side:2}));$t.add(m);return m};
strip(-hw-SH,hw+SH,-.02,11776169);                       // shoulders (same grey as the city's sidewalks)
strip(-hw,hw,0,5198423);                                  // asphalt (same as the city's roads)
strip(-.37,-.07,.03,15909424);strip(.07,.37,.03,15909424); // double yellow centre line
strip(-hw+.25,-hw+.45,.03,15658732);strip(hw-.45,hw-.25,.03,15658732); // white edge lines
// retaining wall under each edge, down into the slope, so the road never floats
for(const s of[-1,1]){const V=[],I=[];for(let k=0;k<n;k++){const[x,z]=P[k],[nx,nz]=NR[k],ex=x+nx*s*(hw+SH),ez=z+nz*s*(hw+SH);V.push(ex,Y[k]-.02,ez,ex,Math.min(Y[k]-.02,ne(ex,ez))-1.5,ez);if(k>K0&&!XR[k]&&!XR[k-1]){const o=(k-1)*2;I.push(o,o+2,o+1,o+1,o+2,o+3)}}
const g=new oe;g.setAttribute('position',new Ut(V,3));g.setIndex(I);g.computeVertexNormals();$t.add(new Dt(g,new Ft({color:10524028,side:2})))}
// guard rails: a steel band on posts along both sides (open at the bottom and at the lookout)
{const RM=new Ft({color:13424094,side:2}),k0=14,k1=n-10;for(const s of[-1,1]){const V=[],I=[];for(let k=k0;k<=k1;k++){const[x,z]=P[k],[nx,nz]=NR[k],o=s*(hw+SH-.25),ex=x+nx*o,ez=z+nz*o;V.push(ex,Y[k]+.55,ez,ex,Y[k]+.85,ez);const nearX=j=>{for(let d=-4;d<=4;d++)if(XR[j+d])return 1;return 0};if(k>k0&&!nearX(k)&&!nearX(k-1)){const q=(k-k0-1)*2;I.push(q,q+2,q+1,q+1,q+2,q+3)}}
const g=new oe;g.setAttribute('position',new Ut(V,3));g.setIndex(I);g.computeVertexNormals();$t.add(new Dt(g,RM))}
const posts=[];for(let k=k0;k<=k1;k+=3)for(const s of[-1,1]){let nx0=0;for(let d=-4;d<=4;d++)XR[k+d]&&(nx0=1);if(nx0)continue;const[x,z]=P[k],[nx,nz]=NR[k],o=s*(hw+SH-.25);posts.push([x+nx*o,Y[k],z+nz*o])}
const im=new on(new Bt(.14,.8,.14).translate(0,.4,0),new Ft({color:8421504}),posts.length),Q=new ee;posts.forEach(([x,y,z],i)=>{Q.makeTranslation(x,y,z);im.setMatrixAt(i,Q)});$t.add(im)}
window.__mroad={P,Y,hw:hw+SH}}
// the lookout at the top of the mountain road
{const[x,z]=N.lookout,y=ne(x,z),g=new T.Group();g.position.set(x,y,z);$t.add(g);for(const[a,b]of[[-3.5,-3.5],[3.5,-3.5],[-3.5,3.5],[3.5,3.5]])box(.5,4,.5,'#7a4f2c',a,2,b,g);box(8.4,.5,8.4,'#a0703f',0,4.2,0,g);
for(const[a,b,w,d]of[[0,-4,8.4,.15],[0,4,8.4,.15],[-4,0,.15,8.4],[4,0,.15,8.4]])box(w,1.1,d,'#ffffff',a,5,b,g);const rf=new T.Mesh(new T.Cone(6.4,2.6,4),mat('#d94b3c'));rf.rotation.y=Math.PI/4;rf.position.y=9;g.add(rf);
for(const[a,b]of[[-3.5,-3.5],[3.5,-3.5],[-3.5,3.5],[3.5,3.5]])box(.3,3.4,.3,'#7a4f2c',a,6.1,b,g);const sc=new T.Mesh(new T.Cyl(.25,.4,1.6,10),mat('#2f3a44'));sc.position.set(0,5.6,2.2);sc.rotation.x=-1.1;g.add(sc);addSolid(x-4.2,z-4.2,x+4.2,z+4.2,y+4.5)}
// farm: crop fields, a red barn and a silo
{const tex=['#8a6a3e','#7d5f37','#8a6a3e','#7d5f37'].map((c,k)=>{const cv=document.createElement('canvas');cv.width=cv.height=128;const x2=cv.getContext('2d');x2.fillStyle=c;x2.fillRect(0,0,128,128);x2.fillStyle='rgba(60,40,20,.45)';for(let r=0;r<128;r+=16)x2.fillRect(0,r,128,5);if(false){x2.fillStyle='#f08a24';for(let q=0;q<40;q++){x2.beginPath();x2.arc(Math.random()*128,Math.floor(Math.random()*8)*16+3,4,0,7);x2.fill()}}const t=new Pe(cv);t.wrapS=t.wrapT=1e3;t.repeat.set(4,4);t.colorSpace=me;return new T.Mat({map:t})});
for(const[x,z,w,d,k]of N.fields){const pl=new T.Mesh(new Hn(w,d),tex[k]);pl.rotation.x=-Math.PI/2;if(k%2)pl.rotation.z=Math.PI/2*0;pl.position.set(x+w/2,ne(x+w/2,z+d/2)+.09,z+d/2);$t.add(pl)}
if(N.barn){const[x,z]=N.barn,y=ne(x,z),g=new T.Group();g.position.set(x,y,z);$t.add(g);box(18,9,24,'#c0392b',0,4.5,0,g);const sh=new T.Shape();sh.moveTo(-10,0);sh.lineTo(10,0);sh.lineTo(0,7);sh.lineTo(-10,0);
const rf=new T.Mesh(new T.Ext(sh,{depth:26,bevelEnabled:!1}),mat('#5a3a2a'));rf.position.set(0,9,-13);g.add(rf);box(7,7,.3,'#ffffff',0,3.5,12.1,g);box(6,6,.4,'#8e2a20',0,3.2,12.2,g);
const si=new T.Mesh(new T.Cyl(3.6,3.6,18,16),mat('#b8c4ce'));si.position.set(14,9,-6);g.add(si);const dm=new T.Mesh(new T.Sph(3.6,16,8,0,6.3,0,1.6),mat('#8a96a8'));dm.position.set(14,18,-6);g.add(dm);addSolid(x-9,z-12,x+9,z+12,y+14);addSolid(x+10.4,z-9.6,x+17.6,z-2.4,y+21.6)}}
// the beach: umbrellas and towels on the city side, swan boats on the lake
{const[lx,lz,rx,rz]=N.lake;const cols=['#ff5a5a','#ffd23c','#5ac8ff','#7fe08a','#ff8ad8'];for(let k=0;k<9;k++){const a=Math.PI*.95+k*.075*Math.PI,x=lx+Math.cos(a)*(rx+11),z=lz+Math.sin(a)*(rz+11);umbrella(x,z,cols[k%5])}
for(let k=0;k<3;k++){const g=new T.Group();box(3,1.2,4.4,'#ffffff',0,.6,0,g);const nk=new T.Mesh(new T.Cyl(.35,.45,3,8),mat('#ffffff'));nk.position.set(0,2.2,1.8);nk.rotation.x=-.2;g.add(nk);const hd=new T.Mesh(new T.Sph(.6,10,8),mat('#ffffff'));hd.position.set(0,3.7,2.1);g.add(hd);const bk=new T.Mesh(new T.Cone(.25,.7,8),mat('#f28c28'));bk.rotation.x=Math.PI/2;bk.position.set(0,3.6,2.8);g.add(bk);$t.add(g);
let t=k*2.1;LIVE.push(dt=>{t+=dt*.05;const x=lx+Math.cos(t)*rx*.55,z=lz+Math.sin(t)*rz*.5;g.position.set(x,.35+Math.sin(t*40)*.08,z);g.rotation.y=Math.atan2(-Math.sin(t)*rx,Math.cos(t)*rz)})}}}


// basketball court: painted court, two hoops, five players passing and shooting
function basketball(x,z,w,d){const long=w>=d,L=(long?w:d)-3,W=(long?d:w)-3,cx=x+w/2,cz=z+d/2,P=(u,v)=>long?[cx+u,cz+v]:[cx+v,cz+u];
const cv=document.createElement('canvas');cv.width=512;cv.height=320;const c=cv.getContext('2d');c.fillStyle='#d9824a';c.fillRect(0,0,512,320);c.strokeStyle='#ffffff';c.lineWidth=5;c.strokeRect(8,8,496,304);
c.beginPath();c.moveTo(256,8);c.lineTo(256,312);c.stroke();c.beginPath();c.arc(256,160,44,0,7);c.stroke();for(const s of[0,1]){c.fillStyle='#3b7dd8';c.fillRect(s?412:8,110,92,100);c.strokeRect(s?412:8,110,92,100);c.beginPath();c.arc(s?504:8,160,150,s?Math.PI/2:-Math.PI/2,s?Math.PI*1.5:Math.PI/2);c.stroke()}
const tx=new Pe(cv);tx.colorSpace=me;const pl=new T.Mesh(new Hn(L+2,W+2),new T.Mat({map:tx}));pl.rotation.x=-Math.PI/2;if(!long)pl.rotation.z=Math.PI/2;pl.position.set(cx,.1,cz);$t.add(pl);
const hoops=[-1,1].map(s=>{const[hx,hz]=P(s*(L/2+.4),0),g=new T.Group();g.position.set(hx,0,hz);g.rotation.y=long?(s<0?Math.PI/2:-Math.PI/2):(s<0?0:Math.PI);$t.add(g);box(.3,3.4,.3,'#555',0,1.7,0,g);box(1.8,1.1,.12,'#ffffff',0,3.3,.3,g);
const rim=new T.Mesh(new Vo(.35,.05,6,16),mat('#ff6a1a'));rim.rotation.x=Math.PI/2;rim.position.set(0,3.05,.75);g.add(rim);const[rx,rz]=P(s*(L/2-.35),0);return[rx,rz]});
const ball=new T.Mesh(new T.Sph(.16,10,8),mat('#e8742a'));$t.add(ball);const pl5=[];for(let k=0;k<5;k++){const p=person(['#e8463c','#2f6fdf'][k%2]);p.g.scale.setScalar(.95);p.u=(rnd()-.5)*L*.7;p.v=(rnd()-.5)*W*.7;p.ph=rnd()*6;pl5.push(p)}
let hold=0,t=0,from=null,to=null,shot=0,tgt=[0,0,0];LIVE.push(dt=>{t+=dt;const h=pl5[hold];
for(const p of pl5){if(!p.tu||rnd()<dt*.4){p.tu=(rnd()-.5)*L*.8;p.tv=(rnd()-.5)*W*.8}const a=p.tu-p.u,b=p.tv-p.v,q=Math.hypot(a,b),mv=Math.min(q,2.6*dt);if(q>.2){p.u+=a/q*mv;p.v+=b/q*mv}p.ph+=dt*(q>.2?9:0);const sw=q>.2?Math.sin(p.ph)*.6:0;p.legs[0].rotation.x=sw;p.legs[1].rotation.x=-sw;
const[px,pz]=P(p.u,p.v);p.g.position.set(px,.1,pz);const[bx,bz]=[ball.position.x,ball.position.z];p.g.rotation.y=Math.atan2(bx-px,bz-pz)}
if(!from){const[px,pz]=P(h.u,h.v);ball.position.set(px+.3,.25+Math.abs(Math.sin(t*7))*1,pz+.3);h.arms[0].rotation.x=-.6;if(t>1.6+rnd()*.05){t=0;const sh=rnd()<.35;from=[px,1.6,pz];if(sh){const hp=hoops[rnd()<.5?0:1];to=[hp[0],3.1,hp[1]];shot=1}else{let n=hold;while(n===hold)n=Math.floor(rnd()*5);const[qx,qz]=P(pl5[n].u,pl5[n].v);to=[qx,1.3,qz];shot=0;hold=n}}}
else{const k=Math.min(1,t/(shot?1.1:.6));ball.position.set(from[0]+(to[0]-from[0])*k,from[1]+(to[1]-from[1])*k+Math.sin(k*Math.PI)*(shot?3:1),from[2]+(to[2]-from[2])*k);if(k>=1){if(shot){from=[to[0],3,to[2]];to=[to[0]+(rnd()-.5)*3,.2,to[2]+(rnd()-.5)*3];shot=2;t=0}else{from=null;t=0;if(shot===2)hold=Math.floor(rnd()*5);shot=0}}}})}
// playground: slide, swings, seesaw, climbing frame and kids playing
function playground(x,z,w,d){const pl=new T.Mesh(new Hn(w-1,d-1),mat('#e6c48a'));pl.rotation.x=-Math.PI/2;pl.position.set(x+w/2,.09,z+d/2);$t.add(pl);const long=w>=d,L=long?w:d,P=(u,v)=>long?[x+u,z+d/2+v]:[x+w/2+v,z+u];
// slide
{const[sx,sz]=P(L*.18,0),g=new T.Group();g.position.set(sx,0,sz);g.rotation.y=long?0:Math.PI/2;$t.add(g);for(const[a,b]of[[-.8,-.8],[.8,-.8],[-.8,.8],[.8,.8]])box(.15,2.4,.15,'#3b7dd8',a,1.2,b,g);box(1.8,.15,1.8,'#ffd23c',0,2.4,0,g);
for(let k=0;k<6;k++)box(1.4,.08,.08,'#3b7dd8',-1.1,.35+k*.4,0,g).rotation.z=0;box(.08,2.4,.08,'#3b7dd8',-1.1,1.2,.7,g);box(.08,2.4,.08,'#3b7dd8',-1.1,1.2,-.7,g);const sl=box(4,.12,1.2,'#e8463c',2.6,1.25,0,g);sl.rotation.z=-.58;for(const s of[-1,1])box(4,.35,.08,'#e8463c',2.6,1.4,s*.6,g).rotation.z=-.58}
// swings
const sw=[];{const[sx,sz]=P(L*.5,0),g=new T.Group();g.position.set(sx,0,sz);g.rotation.y=long?Math.PI/2:0;$t.add(g);for(const s of[-1,1]){const a=box(.15,3.6,.15,'#7fc94a',s*2.4,1.7,.9,g);a.rotation.x=.25;const b=box(.15,3.6,.15,'#7fc94a',s*2.4,1.7,-.9,g);b.rotation.x=-.25}box(5,.15,.15,'#7fc94a',0,3.4,0,g);
for(const s of[-1,1]){const pv=pivot(g,s*1.1,3.4,0);box(.04,2.6,.04,'#444',-.25,-1.3,0,pv);box(.04,2.6,.04,'#444',.25,-1.3,0,pv);box(.7,.08,.35,'#333',0,-2.6,0,pv);const kid=person(['#ff8ad8','#5ac8ff'][s<0?0:1]);kid.g.scale.setScalar(.6);$t.remove(kid.g);kid.g.position.set(0,-3.2,0);kid.legs.forEach(l=>l.rotation.x=-1.2);pv.add(kid.g);sw.push([pv,rnd()*6])}}
// seesaw
let ss;{const[sx,sz]=P(L*.78,0),g=new T.Group();g.position.set(sx,0,sz);g.rotation.y=long?0:Math.PI/2;$t.add(g);box(.4,.7,.4,'#888',0,.35,0,g);ss=pivot(g,0,.75,0);box(4.4,.14,.4,'#ffd23c',0,0,0,ss);for(const s of[-1,1]){const k=person(s<0?'#7fe08a':'#ff8a3c');k.g.scale.setScalar(.6);$t.remove(k.g);k.g.position.set(s*1.9,0,0);k.g.rotation.y=s<0?Math.PI/2:-Math.PI/2;k.legs.forEach(l=>l.rotation.x=-1.2);ss.add(k.g)}}
// kids running around
const kids=[];for(let k=0;k<5;k++){const p=person(['#ff5a5a','#ffd23c','#5ac8ff','#7fe08a','#c77dff'][k]);p.g.scale.setScalar(.6);p.x=x+2+rnd()*(w-4);p.z=z+2+rnd()*(d-4);p.ph=rnd()*6;kids.push(p)}
LIVE.push(dt=>{const t=performance.now()/1e3;for(const[pv,o]of sw)pv.rotation.x=Math.sin(t*2.2+o)*.7;ss.rotation.z=Math.sin(t*1.6)*.32;
for(const p of kids){if(!p.tx||rnd()<dt*.5){p.tx=x+2+rnd()*(w-4);p.tz=z+2+rnd()*(d-4)}const a=p.tx-p.x,b=p.tz-p.z,q=Math.hypot(a,b),mv=Math.min(q,3.2*dt);if(q>.2){p.x+=a/q*mv;p.z+=b/q*mv}p.ph+=dt*12;const s2=q>.2?Math.sin(p.ph)*.8:0;p.legs[0].rotation.x=s2;p.legs[1].rotation.x=-s2;p.arms[0].rotation.x=-s2;p.arms[1].rotation.x=s2;p.g.position.set(p.x,.1+(q>.2?Math.abs(Math.sin(p.ph))*.12:0),p.z);p.g.rotation.y=Math.atan2(a,b)}})}
// big cats: a lion and a tiger wandering around the park
function bigcat(kind){const g=new T.Group(),C=kind==='lion'?'#d9a441':'#f08a24';const add=(geo,c,px,py,pz,sx=1,sy=1,sz=1)=>{const m=new T.Mesh(geo,mat(c));m.position.set(px,py,pz);m.scale.set(sx,sy,sz);g.add(m);return m};
add(new T.Sph(1,14,10),C,0,1.6,0,.75,.7,1.5);if(kind==='tiger')for(let k=-2;k<=2;k++)add(new T.Box(1.52,.18,.14),'#1e2124',0,1.75,k*.42).scale.set(1,1,1);
const legs=[[-.4,.8],[.4,.8],[-.4,-.8],[.4,-.8]].map(([lx,lz])=>{const p=pivot(g,lx,1.3,lz);part(p,new T.Cyl(.17,.15,1.2,8),C,0,-.6,0);part(p,new T.Sph(.2,8,6),C,0,-1.2,.08);return p});
const head=pivot(g,0,2.2,1.5);if(kind==='lion')part(head,new T.Sph(1,14,10),'#8a4f1e',0,0,-.15,1.1,1.1,.8);part(head,new T.Sph(.6,14,10),C,0,0,.1);part(head,new T.Sph(.3,10,8),'#f3e2c0',0,-.18,.55);part(head,new T.Sph(.1,8,6),'#2a1a10',0,-.05,.78);
for(const s of[-1,1]){part(head,new T.Sph(.08,8,6),'#1e2124',s*.22,.15,.52);part(head,new T.Sph(.17,8,6),C,s*.4,.48,0)}if(kind==='tiger')for(const s of[-1,1])part(head,new T.Box(.06,.3,.05),'#1e2124',s*.3,.3,.45);
const tail=pivot(g,0,1.9,-1.4);for(let k=0;k<5;k++)part(tail,new T.Sph(.12,8,6),kind==='tiger'&&k%2?'#1e2124':C,0,-k*.12,-k*.25);if(kind==='lion')part(tail,new T.Sph(.2,8,6),'#8a4f1e',0,-.6,-1.25);
g.scale.setScalar(1.5);$t.add(g);return{g,legs,head,tail}}
function bigcats(x,z,w,d){for(const kind of['lion','tiger']){const c=bigcat(kind);c.x=x+4+rnd()*(w-8);c.z=z+4+rnd()*(d-8);c.ph=rnd()*6;c.yaw=0;c.rest=0;
LIVE.push(dt=>{if(c.rest>0){c.rest-=dt}else{if(!c.tx||Math.hypot(c.tx-c.x,c.tz-c.z)<1){c.tx=x+4+rnd()*(w-8);c.tz=z+4+rnd()*(d-8);if(rnd()<.3)c.rest=2+rnd()*3}const a=c.tx-c.x,b=c.tz-c.z,q=Math.hypot(a,b);c.x+=a/q*1.6*dt;c.z+=b/q*1.6*dt;let dy=Math.atan2(a,b)-c.yaw;dy=Math.atan2(Math.sin(dy),Math.cos(dy));c.yaw+=dy*Math.min(1,dt*3);c.ph+=dt*5}
const mv=c.rest>0?0:1;c.legs.forEach((l,k)=>l.rotation.x=Math.sin(c.ph+(k===0||k===3?0:Math.PI))*.45*mv);c.tail.rotation.x=.3+Math.sin(performance.now()/600)*.2;c.tail.rotation.y=Math.sin(performance.now()/400)*.4;
c.head.rotation.y=Math.sin(performance.now()/1500+c.x)*.3;c.g.position.set(c.x,0,c.z);c.g.rotation.y=c.yaw})}}
// pile of garbage bags (with a few flies)
for(const[k,x,z,w,d]of ie.deco||[]){if(k!=='garbage')continue;const cx=x+w/2,cz=z+d/2;for(let q=0;q<34;q++){const a=rnd()*6.3,r=rnd()*Math.min(w,d)*.36,h=Math.max(0,(1-r/(Math.min(w,d)*.36))*3.2);
const b=new T.Mesh(new T.Sph(.9,10,8),mat(['#1e2124','#2a2f36','#2f4a34','#1e2124'][q%4]));b.scale.set(1.1,.85,1);b.position.set(cx+Math.cos(a)*r,.7+h*rnd(),cz+Math.sin(a)*r);b.rotation.set(rnd(),rnd(),rnd());$t.add(b);
const kn=new T.Mesh(new T.Cone(.25,.45,6),mat('#111'));kn.position.set(b.position.x,b.position.y+.85,b.position.z);$t.add(kn)}
for(let q=0;q<6;q++){const f=new T.Mesh(new T.Sph(.08,5,4),mat('#111'));$t.add(f);const o=rnd()*6;LIVE.push(()=>{const t=performance.now()/1e3+o;f.position.set(cx+Math.sin(t*3.1)*1.5,4.5+Math.sin(t*5)*.6,cz+Math.cos(t*2.3)*1.5)})}}

// fishing pier: wooden deck over the water, people fishing with bobbing floats, fish that jump
function fishing(x,z,w,d){const L=(ie.nature&&ie.nature.lake)||[x+w/2,z+d+40],lx=L[0],lz=L[1];const Y=1.1;
const deck=new T.Group();$t.add(deck);const long=w>=d;for(let q=0;q<(long?w:d);q+=1.1){const pl=long?box(1,.25,d,q%2.2<1.1?'#a8743f':'#9a6838',x+q+.5,Y,z+d/2,deck):box(w,.25,1,q%2.2<1.1?'#a8743f':'#9a6838',x+w/2,Y,z+q+.5,deck)}
for(let px=x+.4;px<=x+w-.3;px+=3)for(const pz of[z+.4,z+d-.4])box(.4,Y+1.5,.4,'#6b4426',px,(Y-1.5)/2+.2,pz,deck);for(let pz=z+.4;pz<=z+d-.3;pz+=3)for(const px of[x+.4,x+w-.4])box(.4,Y+1.5,.4,'#6b4426',px,(Y-1.5)/2+.2,pz,deck);
// the side that faces the lake
const sides=[[x+w/2,z,0,-1,w],[x+w/2,z+d,0,1,w],[x,z+d/2,-1,0,d],[x+w,z+d/2,1,0,d]];const sd=sides.reduce((b,s)=>((s[0]-lx)**2+(s[1]-lz)**2<(b[0]-lx)**2+(b[1]-lz)**2?s:b));
const[ex,ez,nx,nz,len]=sd,tx=-nz,tz=nx;for(const o of[-1,1]){}box(Math.abs(nx)?.15:len,.9,Math.abs(nx)?len:.15,'#8a5a2a',ex-nx*.2,Y+.55,ez-nz*.2);
const n=Math.max(2,Math.min(4,Math.floor(len/9)));for(let k=0;k<n;k++){const o=(k-(n-1)/2)*(len/(n+.4)),px=ex-nx*1.2+tx*o,pz=ez-nz*1.2+tz*o;
const p=person(['#3b7dd8','#e8463c','#7fc94a','#f2a541'][k%4]);p.g.position.set(px,Y+.12,pz);p.g.rotation.y=Math.atan2(nx,nz);p.arms[0].rotation.x=p.arms[1].rotation.x=-1.1;
const hat=new T.Mesh(new T.Cyl(.32,.32,.08,10),mat('#e9d27a'));hat.position.set(0,1.95,0);p.g.add(hat);
const rod=new T.Mesh(new T.Cyl(.03,.04,3.6,5),mat('#333'));const rx=px+nx*1.9,rz=pz+nz*1.9;rod.position.set((px+rx)/2+nx*.2,Y+2.2,(pz+rz)/2+nz*.2);rod.rotation.set(0,0,0);rod.lookAt(rx+nx*2,Y+3.6,rz+nz*2);rod.rotateX(Math.PI/2);$t.add(rod);
const fx=px+nx*4.2,fz=pz+nz*4.2;const ln=new T.Mesh(new T.Cyl(.012,.012,1,4),mat('#dddddd'));$t.add(ln);const bob=new T.Mesh(new T.Sph(.16,8,6),mat('#ff3b3b'));$t.add(bob);const ph=rnd()*6;
LIVE.push(()=>{const t=performance.now()/1e3+ph,by=.55+Math.sin(t*2)*.07-(Math.sin(t*.35)>.93?.25:0);bob.position.set(fx,by,fz);const top=[px+nx*3.3,Y+3.5,pz+nz*3.3],h=top[1]-by;ln.position.set((top[0]+fx)/2,(top[1]+by)/2,(top[2]+fz)/2);ln.scale.y=Math.hypot(h,top[0]-fx,top[2]-fz);ln.rotation.z=0;})}
// a fish jumps now and then
const fish=new T.Mesh(new T.Sph(.45,10,8),mat('#f2a541'));fish.scale.set(.5,.6,1.3);$t.add(fish);let ft=rnd()*6;LIVE.push(dt=>{ft+=dt;const c=ft%6;if(c<1){const s0=ex+nx*7+tx*((Math.floor(ft/6)%3)-1)*4,s1=ez+nz*7+tz*((Math.floor(ft/6)%3)-1)*4;fish.visible=!0;fish.position.set(s0+tx*(c*3-1.5),.4+Math.sin(c*Math.PI)*2.2,s1+tz*(c*3-1.5));fish.rotation.y=Math.atan2(tx,tz);fish.rotation.x=(c-.5)*1.6}else fish.visible=!1})}
for(const[k,x,z,w,d]of ie.deco||[])k==='fishing'&&fishing(x,z,w,d);

// hot air balloon: tethered, floats up and down all day
function balloon(x,z,w,d){const cx=x+w/2,cz=z+d/2,pad=new T.Mesh(new T.Cyl(Math.min(w,d)/2-1,Math.min(w,d)/2-1,.15,32),mat('#d9cfa8'));pad.position.set(cx,.08,cz);$t.add(pad);
const cv=document.createElement('canvas');cv.width=512;cv.height=256;const c2=cv.getContext('2d');const C=['#e8463c','#ffd23c','#2f6fdf','#7fc94a','#ff8a3c','#c77dff'];for(let i=0;i<12;i++){c2.fillStyle=C[i%6];c2.fillRect(i*512/12,0,512/12+1,256)}c2.fillStyle='rgba(255,255,255,.85)';c2.fillRect(0,150,512,14);
const tx=new Pe(cv);tx.colorSpace=me;const g=new T.Group();$t.add(g);const env=new T.Mesh(new T.Sph(8,32,20),new T.Mat({map:tx}));env.scale.set(1,1.18,1);env.position.y=16;g.add(env);
const neck=new T.Mesh(new T.Cyl(2.6,1.2,4,20,1,!0),new T.Mat({map:tx,side:2}));neck.position.y=6.6;g.add(neck);for(let i=0;i<4;i++){const a=i*Math.PI/2+Math.PI/4;const r=new T.Mesh(new T.Cyl(.04,.04,4.4,4),mat('#444'));r.position.set(Math.cos(a)*1.4,4.4,Math.sin(a)*1.4);r.rotation.z=-Math.cos(a)*.25;r.rotation.x=Math.sin(a)*.25;g.add(r)}
box(2.4,1.4,2.4,'#8a5a2a',0,1.6,0,g);box(2.6,.25,2.6,'#6b4426',0,2.35,0,g);const fl=new T.Mesh(new T.Cone(.35,1.1,8),new Be({color:new Pt('#ffb020')}));fl.position.y=3.4;g.add(fl);
for(let k=0;k<2;k++){const p=person(['#2f6fdf','#e8463c'][k]);$t.remove(p.g);p.g.scale.setScalar(.75);p.g.position.set(k?.5:-.5,1.2,0);g.add(p.g)}
const rope=new T.Mesh(new T.Cyl(.05,.05,1,4),mat('#d9c79a'));$t.add(rope);box(.4,1,.4,'#6b4426',cx+3,.5,cz+3);
LIVE.push(()=>{const t=performance.now()/1e3,k=.5-.5*Math.cos(t*.18),y=1+k*42;g.position.set(cx+Math.sin(t*.3)*.8*k,y,cz+Math.cos(t*.23)*.8*k);g.rotation.y=t*.05;fl.scale.y=.6+Math.abs(Math.sin(t*6))*.6+(Math.sin(t*.18)>0?.5:0);
const ax=cx+3,az=cz+3,bx=g.position.x,by=y+1,bz=g.position.z,L=Math.hypot(bx-ax,by-1,bz-az);rope.position.set((ax+bx)/2,(1+by)/2,(az+bz)/2);rope.scale.y=L;rope.lookAt(bx,by,bz);rope.rotateX(Math.PI/2)})}
// merry-go-round: spins, horses go up and down
function merry(x,z,w,d){const cx=x+w/2,cz=z+d/2,R=Math.min(w,d)/2-1.5;const base=new T.Mesh(new T.Cyl(R+1,R+1.3,1,40),mat('#e9d8b0'));base.position.set(cx,.5,cz);$t.add(base);
const rot=new T.Group();rot.position.set(cx,1,cz);$t.add(rot);const fl=new T.Mesh(new T.Cyl(R,R,.3,40),mat('#c0392b'));fl.position.y=.15;rot.add(fl);const pole=new T.Mesh(new T.Cyl(1.2,1.2,8,20),mat('#ffd23c'));pole.position.y=4;rot.add(pole);
const cv=document.createElement('canvas');cv.width=512;cv.height=64;const c2=cv.getContext('2d');for(let i=0;i<16;i++){c2.fillStyle=i%2?'#ffffff':'#e8463c';c2.fillRect(i*32,0,32,64)}const tx=new Pe(cv);tx.colorSpace=me;
const roof=new T.Mesh(new T.Cone(R+1,4.5,32,1,!0),new T.Mat({map:tx,side:2}));roof.position.y=8+2.25;rot.add(roof);const rim=new T.Mesh(new T.Cyl(R+1,R+1,1,32,1,!0),new T.Mat({map:tx,side:2}));rim.position.y=7.6;rot.add(rim);
const flag=new T.Mesh(new T.Sph(.6,10,8),mat('#ffd23c'));flag.position.y=12.8;rot.add(flag);const HC=['#ffffff','#f6d55c','#a0d8ff','#ffb3d1','#c9a46a','#ffffff','#b9f0b0','#ffd0a0'],hs=[];
for(let i=0;i<8;i++){const a=i/8*Math.PI*2,h=new T.Group();h.position.set(Math.cos(a)*(R-2.2),0,Math.sin(a)*(R-2.2));h.rotation.y=-a;rot.add(h);const p=new T.Mesh(new T.Cyl(.12,.12,7.4,6),mat('#e0b040'));p.position.y=3.9;h.add(p);
const hr=new T.Group();h.add(hr);const add=(geo,c,px,py,pz,sx=1,sy=1,sz=1)=>{const m=new T.Mesh(geo,mat(c));m.position.set(px,py,pz);m.scale.set(sx,sy,sz);hr.add(m);return m};const C=HC[i];
add(new T.Sph(1,12,8),C,0,0,0,.55,.55,1.2);add(new T.Sph(.45,10,8),C,0,.75,1.05,.8,1,1.3);for(const[a2,b2]of[[-.3,.6],[.3,.6],[-.3,-.6],[.3,-.6]])add(new T.Cyl(.12,.1,1.1,6),C,a2,-.75,b2);add(new T.Box(.15,.6,.5),'#c0392b',0,.7,.65);add(new T.Box(.7,.12,.8),'#2f6fdf',0,.55,0);hs.push([hr,i])}
LIVE.push(dt=>{rot.rotation.y-=dt*.55;const t=performance.now()/1e3;for(const[hr,i]of hs)hr.position.y=2.6+Math.sin(t*2.2+i*.8)*.6})}
// tower ride (drop tower): seats rise slowly, pause, then drop
function towerride(x,z,w,d,fl){const cx=x+w/2,cz=z+d/2,H=Math.max(20,(fl||10)*3.2)+4;const base=new T.Mesh(new T.Cyl(4.5,5,1,24),mat('#8d8a85'));base.position.set(cx,.5,cz);$t.add(base);
const col=new T.Mesh(new T.Cyl(1.6,1.8,H,16),mat('#e8463c'));col.position.set(cx,H/2+1,cz);$t.add(col);for(let k=4;k<H;k+=4){const b=new T.Mesh(new T.Cyl(1.65,1.65,1.2,16),mat('#ffffff'));b.position.set(cx,k,cz);$t.add(b)}
const cap=new T.Mesh(new T.Cone(2.4,3,16),mat('#ffd23c'));cap.position.set(cx,H+2.5,cz);$t.add(cap);const lt=new T.Mesh(new T.Sph(.5,10,8),new Be({color:new Pt('#ff3b3b')}));lt.position.set(cx,H+4.2,cz);$t.add(lt);
const ring=new T.Group();ring.position.set(cx,2,cz);$t.add(ring);const rr=new T.Mesh(new Vo(2.6,.5,10,24),mat('#2f6fdf'));rr.rotation.x=Math.PI/2;ring.add(rr);
for(let i=0;i<8;i++){const a=i/8*Math.PI*2,s=new T.Group();s.position.set(Math.cos(a)*3.1,0,Math.sin(a)*3.1);s.rotation.y=-a+Math.PI/2;ring.add(s);box(.9,1.2,.25,'#ffd23c',0,.2,.45,s);box(.9,.2,.8,'#ffd23c',0,-.4,0,s);
const p=person(['#e8463c','#2f6fdf','#7fc94a','#ff8ad8'][i%4]);$t.remove(p.g);p.g.scale.setScalar(.6);p.g.position.set(0,-.95,0);p.legs.forEach(l=>l.rotation.x=-1.4);s.add(p.g);p.arms.forEach(a2=>a2.rotation.x=-2.8)}
let t=0;LIVE.push(dt=>{t=(t+dt)%16;let y;if(t<8)y=2+(H-6)*(t/8);else if(t<10)y=H-4;else if(t<11.2){const k=(t-10)/1.2;y=H-4-(H-6)*k*k}else y=2;ring.position.y=y;ring.rotation.y+=dt*(t<8?.2:0)})}
// parking lot: asphalt, white lines, parked cars
function parking(x,z,w,d){const pl=new T.Mesh(new Hn(w-1,d-1),mat('#4a4f56'));pl.rotation.x=-Math.PI/2;pl.position.set(x+w/2,.1,z+d/2);$t.add(pl);const C=['#e8463c','#2f6fdf','#f4f4f4','#222','#ffd23c','#7fc94a','#a0a8b0'];
for(let r=0;r<2;r++){const zz=z+3+r*(d-6);for(let xx=x+2;xx<x+w-2;xx+=3){box(.12,.02,5,'#ffffff',xx,.12,zz+(r?-2.5:2.5));if(xx+3<x+w-1&&rnd()<.7){const cg=new T.Group();cg.position.set(xx+1.5,0,zz+(r?-2.5:2.5));$t.add(cg);const c=C[Math.floor(rnd()*C.length)];box(1.9,.8,4.2,c,0,.7,0,cg);box(1.7,.65,2.2,c,0,1.4,-.2,cg);box(1.72,.45,2,'#7fb8e8',0,1.42,-.2,cg)}}}}


// picnic: checkered blankets, baskets, a table and people having lunch
function picnic(x,z,w,d){const cv=document.createElement('canvas');cv.width=cv.height=128;const c=cv.getContext('2d');for(let i=0;i<8;i++)for(let j=0;j<8;j++){c.fillStyle=(i+j)%2?'#ffffff':'#e8282d';c.fillRect(i*16,j*16,16,16)}const tx=new Pe(cv);tx.colorSpace=me;
for(const[a,b]of[[.28,.3],[.72,.68],[.3,.75]]){const bl=new T.Mesh(new Hn(5,5),new T.Mat({map:tx}));bl.rotation.x=-Math.PI/2;bl.rotation.z=rnd();bl.position.set(x+w*a,.12,z+d*b);$t.add(bl);
const bk=box(1,.7,.7,'#b07a45',x+w*a+1.2,.45,z+d*b-1);const h=new T.Mesh(new Vo(.4,.06,6,12,Math.PI),mat('#8a5a2a'));h.position.set(x+w*a+1.2,.8,z+d*b-1);$t.add(h);
for(const[o,col]of[[-1,'#ffd23c'],[.6,'#f08a24']]){const f=new T.Mesh(new T.Sph(.25,8,6),mat(col));f.position.set(x+w*a+o*.6,.3,z+d*b+.4);$t.add(f)}
for(let k=0;k<2;k++){const p=person(['#2f6fdf','#7fc94a','#ff8ad8','#c77dff'][(k+Math.floor(a*10))%4]);p.g.position.set(x+w*a+(k?1.6:-1.6),-.55,z+d*b+(k?.8:-.6));p.g.rotation.y=k?-1.8:1.4;p.legs.forEach(l=>l.rotation.x=-1.5);p.arms[0].rotation.x=-.8}}
const tb=x+w*.72,tz=z+d*.25;box(3.2,.2,1.6,'#a8743f',tb,1.1,tz);for(const s of[-1,1]){box(3.2,.15,.5,'#a8743f',tb,.65,tz+s*1.2);box(.15,1.1,.15,'#6b4426',tb-1.3,.55,tz+s*.6);box(.15,1.1,.15,'#6b4426',tb+1.3,.55,tz+s*.6)}umbrella(tb,tz,'#e8282d')}
// little train going round a circular track
function train(x,z,w,d){const cx=x+w/2,cz=z+d/2,R=9;const tie=new T.Box(2.6,.15,.3);for(let k=0;k<44;k++){const a=k/44*Math.PI*2,m=new T.Mesh(tie,mat('#6b4426'));m.position.set(cx+Math.cos(a)*R,.1,cz+Math.sin(a)*R);m.rotation.y=-a;$t.add(m)}
for(const o of[-.7,.7]){const rl=new T.Mesh(new Vo(R+o,.09,4,64),mat('#9aa3ab'));rl.rotation.x=Math.PI/2;rl.position.set(cx,.25,cz);$t.add(rl)}
const mid=new T.Mesh(new T.Cyl(R-1.6,R-1.6,.12,40),mat('#8fd06a'));mid.position.set(cx,.1,cz);$t.add(mid);for(let k=0;k<6;k++){const f=new T.Mesh(new T.Sph(.45,8,6),mat(['#ff5a5a','#ffd23c','#ff8ad8'][k%3]));f.position.set(cx+Math.cos(k)*3,.4,cz+Math.sin(k)*3);$t.add(f)}
const C=['#e8463c','#2f6fdf','#ffd23c','#7fc94a'],cars=[];const eng=new T.Group();box(1.9,1.8,3.2,'#2a2f36',0,1.3,0,eng);box(2,1.2,1.4,'#e8463c',0,2.4,-.9,eng);const ch=new T.Mesh(new T.Cyl(.3,.4,1.2,10),mat('#2a2f36'));ch.position.set(0,2.8,1);eng.add(ch);$t.add(eng);cars.push(eng);
for(let i=1;i<4;i++){const g=new T.Group();box(1.8,1.2,2.8,C[i],0,1,0,g);const p=person(C[(i+1)%4]);$t.remove(p.g);p.g.scale.setScalar(.6);p.g.position.set(0,1.3,0);g.add(p.g);$t.add(g);cars.push(g)}
for(const g of cars)for(const s of[-1,1])for(const o of[-1,1]){const wh=new T.Mesh(new T.Cyl(.38,.38,.2,10),mat('#222'));wh.rotation.z=Math.PI/2;wh.position.set(s*.95,.4,o*.9);g.add(wh)}
const smoke=[];for(let k=0;k<5;k++){const m=new T.Mesh(new T.Sph(.4,8,6),new T.Mat({color:new Pt('#ffffff'),transparent:!0,opacity:.6}));$t.add(m);smoke.push(m)}
let a0=0;LIVE.push(dt=>{a0+=dt*.35;cars.forEach((g,i)=>{const a=a0-i*.36;g.position.set(cx+Math.cos(a)*R,0,cz+Math.sin(a)*R);g.rotation.y=-a+Math.PI});
const e=cars[0],t=performance.now()/1e3;smoke.forEach((m,i)=>{const k=(t*1.5+i/5)%1;m.position.set(e.position.x,3+k*3,e.position.z);m.scale.setScalar(.6+k);m.material.opacity=.6*(1-k)})})}
// secret room: a little door in the corner of a building, a hidden room with a glowing treasure chest
function secret(x,z,w,d,H){const cx=x+w/2,cz=z+d/2,RH=3.4;box(w-.6,H-RH,d-.6,'#9a8ad8',cx,RH+(H-RH)/2,cz);box(w-.6,.4,d-.6,'#7a6ab8',cx,RH,cz);
box(.3,RH,d-.6,'#9a8ad8',x+w-.45,RH/2,cz);box(w-2.8,RH,.3,'#9a8ad8',x+.3+(w-2.8)/2,RH/2,z+d-.45);box(1.6,RH,.3,'#9a8ad8',x+w-1.1,RH/2,z+d-.45);
const fl=new T.Mesh(new Hn(w-.8,d-.8),mat('#3a2a5a'));fl.rotation.x=-Math.PI/2;fl.position.set(cx,.12,cz);$t.add(fl);const dx=x+w-2.6;box(1.6,.25,.35,'#ffd23c',dx+.2,2.5,z+d-.4);
const ch=new T.Group();ch.position.set(cx-1,0,cz-1.5);$t.add(ch);box(1.6,.9,1,'#8a5a2a',0,.45,0,ch);box(1.7,.12,1.1,'#ffd23c',0,.9,0,ch);const lid=new T.Mesh(new T.Cyl(.5,.5,1.6,10,1,!1,0,Math.PI),mat('#8a5a2a'));lid.rotation.z=Math.PI/2;lid.position.set(0,.95,0);ch.add(lid);
for(let k=0;k<10;k++){const c=new T.Mesh(new T.Cyl(.18,.18,.05,10),new Be({color:new Pt('#ffd23c')}));c.position.set(-1+rnd()*2.4,.05,-.8+rnd()*1.8);$t.remove(c);c.position.x+=cx-1;c.position.z+=cz-1.5;$t.add(c)}
const glow=new T.Mesh(new T.Sph(.5,10,8),new Be({color:new Pt('#fff3a0'),transparent:!0,opacity:.5}));glow.position.set(cx-1,1.4,cz-1.5);$t.add(glow);LIVE.push(()=>glow.scale.setScalar(1+Math.sin(performance.now()/300)*.3));
const x0=x+.3,x1=x+w-.3,z0=z+.3,z1=z+d-.3,door0=dx-.6,door1=dx+1;(window.__SECRET=window.__SECRET||[]).push((px,pz,py)=>{if(px<x0||px>x1||pz<z0||pz>z1)return null;
const edge=px>x1-.5||pz>z1-.5;if(edge&&!(pz>z1-.5&&px>door0&&px<door1&&py<2.6))return{f:H,c:1e4,name:null};return py<RH-.2?{f:0,c:RH-.3,name:null}:{f:H,c:1e4,name:null}})}
// aquarium: glass building full of water, fish and a shark
function aquarium(x,z,w,d,fl){const H=(fl||10)*3.2,cx=x+w/2,cz=z+d/2,W=w-1.4,D=d-1.4;box(w,1,d,'#2b4d6b',cx,.5,cz);
const water=new T.Mesh(new T.Box(W-.4,H-1.6,D-.4),new T.Mat({color:new Pt('#5ec8f0'),transparent:!0,opacity:.32,depthWrite:!1}));water.position.set(cx,1+(H-1.6)/2,cz);$t.add(water);
const glass=new T.Mesh(new T.Box(W,H,D),new T.Mat({color:new Pt('#bfe8ff'),transparent:!0,opacity:.22,depthWrite:!1}));glass.position.set(cx,1+H/2,cz);$t.add(glass);
for(let y=1;y<=H+1;y+=H/5)box(W+.3,.4,D+.3,'#2b4d6b',cx,y,cz);for(const[a,b]of[[-1,-1],[1,-1],[-1,1],[1,1]])box(.5,H,.5,'#2b4d6b',cx+a*W/2,1+H/2,cz+b*D/2);
box(W+1,.8,D+1,'#0b3d6b',cx,H+1.4,cz);const dm=new T.Mesh(new T.Sph(Math.min(W,D)*.3,20,10,0,6.3,0,1.6),new T.Mat({color:new Pt('#9fe6ff'),transparent:!0,opacity:.5}));dm.position.set(cx,H+1.8,cz);$t.add(dm);
for(let k=0;k<14;k++){const a=rnd()*6.3,r=rnd()*Math.min(W,D)*.35;const sw=new T.Mesh(new T.Cone(.4,2+rnd()*4,5),mat(['#3f9a4a','#5fb85a','#e86a8a'][k%3]));sw.position.set(cx+Math.cos(a)*r,1.6+rnd(),cz+Math.sin(a)*r);$t.add(sw)}
for(let k=0;k<8;k++){const rk=new T.Mesh(new T.Sph(.8+rnd(),6,5),mat('#8a7a6a'));rk.scale.y=.5;rk.position.set(cx+(rnd()-.5)*W*.8,1.2,cz+(rnd()-.5)*D*.8);$t.add(rk)}
const fishes=[],FC=['#ff8a1a','#ffd23c','#3b8fff','#ff5ad1','#7fe0ff','#ffffff'];for(let k=0;k<26;k++){const f=new T.Group();const c=FC[k%FC.length];const b=new T.Mesh(new T.Sph(.4,8,6),mat(c));b.scale.set(.5,.8,1.3);f.add(b);const tl=new T.Mesh(new T.Cone(.35,.6,4),mat(c));tl.rotation.x=-Math.PI/2;tl.position.z=-.6;f.add(tl);
f.scale.setScalar(2.6);$t.add(f);fishes.push([f,rnd()*6.3,2+rnd()*(H-4),.6+rnd()*.8,Math.min(W,D)*(.15+rnd()*.25),rnd()<.5?1:-1])}
const sh=new T.Group();const sc='#7d8c99';const body=new T.Mesh(new T.Sph(1,12,8),mat(sc));body.scale.set(.9,1,3.2);sh.add(body);const belly=new T.Mesh(new T.Sph(.9,10,8),mat('#e9eef2'));belly.scale.set(.8,.6,2.6);belly.position.y=-.35;sh.add(belly);
const fin=new T.Mesh(new T.Cone(.7,1.6,4),mat(sc));fin.position.set(0,1.3,.3);fin.rotation.x=-.4;sh.add(fin);const tail=new T.Mesh(new T.Cone(.9,1.8,4),mat(sc));tail.rotation.x=-Math.PI/2;tail.position.z=-3.6;tail.scale.set(.3,1.5,1);sh.add(tail);
for(const s of[-1,1]){const e=new T.Mesh(new T.Sph(.13,6,5),mat('#111'));e.position.set(s*.55,.25,2.4);sh.add(e);const pf=new T.Mesh(new T.Box(1.4,.1,.7),mat(sc));pf.position.set(s*1,-.3,.8);pf.rotation.z=s*.4;sh.add(pf)}
const mouth=new T.Mesh(new T.Box(.7,.08,.3),mat('#ffffff'));mouth.position.set(0,-.25,2.8);sh.add(mouth);sh.scale.setScalar(2);$t.add(sh);const R=Math.min(W,D)*.33;
LIVE.push(dt=>{const t=performance.now()/1e3;for(const[f,ph,y,sp,r,dir]of fishes){const a=ph+t*sp*dir*.5;f.position.set(cx+Math.cos(a)*r,y+Math.sin(t*sp+ph)*.4,cz+Math.sin(a)*r);f.rotation.y=-a+(dir>0?0:Math.PI);f.children[1].rotation.y=Math.sin(t*8+ph)*.4}
const a=t*.25;sh.position.set(cx+Math.cos(a)*R,H*.5+Math.sin(t*.4)*2,cz+Math.sin(a)*R);sh.rotation.y=-a;tail.rotation.y=Math.sin(t*3)*.3})}
for(const[k,x,z,w,d,c,n,f]of ie.deco||[])k==='picnic'?picnic(x,z,w,d):k==='train'?train(x,z,w,d):k==='secret'?secret(x,z,w,d,f):k==='aquarium'&&aquarium(x,z,w,d,f);

for(const[k,x,z,w,d,c,n,f]of ie.deco||[])k==='balloon'?balloon(x,z,w,d):k==='merrygoround'?merry(x,z,w,d):k==='towerride'?towerride(x,z,w,d,f):k==='parking'&&parking(x,z,w,d);


// little snack stands: a kiosk with a striped awning and a snack on the counter
{const AW=[['#ff5a5a','#ffffff'],['#3b8fd9','#ffffff'],['#2e9e5b','#ffffff'],['#ffd23c','#ff7a3c'],['#ff8ad8','#ffffff']];let q=0;
for(let[k,x,z,w,d,c,n,f]of ie.deco||[]){if(k!=='stand')continue;n=n||'';const g=new T.Group();g.position.set(x+w/2,0,z+d/2);g.rotation.y=f;$t.add(g);const[a,b]=AW[q++%AW.length];
box(4,2.2,3,'#f4efe4',0,1.1,-.3,g);box(4.2,.25,1,'#a8743f',0,1.25,1.4,g);box(3.4,1.1,.1,'#3a3f48',0,1.9,1.21,g);
for(let i=0;i<6;i++){const s=box(.7,.12,1.8,i%2?b:a,-1.75+i*.7,3,.7,g);s.rotation.x=.35}box(4.3,1.2,.12,a,0,3.5,-1.8,g);box(4.3,.12,3.4,b,0,4.1,-.3,g);
const FR={apple:['#d9262a',.3],grape:['#7b3fb0',.22],melon:['#3f8f3a',.55],milk:['#ffffff',.3],egg:['#fbf3e0',.22],corn:['#f2c94c',.3]},key=Object.keys(FR).find(k2=>(n||'').toLowerCase().includes(k2));
if(key){const[fc,fr]=FR[key];for(let i=0;i<(key==='melon'?2:6);i++){const it=new T.Mesh(new T.Sph(fr,10,8),mat(fc));if(key==='egg')it.scale.set(1,1.3,1);if(key==='milk')it.scale.set(.8,1.4,.8);it.position.set(-1.4+i*(key==='melon'?1.4:.55),1.4+fr,1.4);g.add(it)}
const cv=document.createElement('canvas');cv.width=512;cv.height=128;const c2=cv.getContext('2d');c2.fillStyle=b;c2.fillRect(0,0,512,128);c2.fillStyle=a===b?'#1e2a33':a;c2.font='bold 76px sans-serif';c2.textAlign='center';c2.textBaseline='middle';
let fs=76;while(c2.measureText(n).width>480&&fs>30){fs-=4;c2.font='bold '+fs+'px sans-serif'}c2.fillText(n,256,68);const tx=new Pe(cv);tx.colorSpace=me;const pl=new T.Mesh(new Hn(4.2,1.05),new Be({map:tx}));pl.position.set(0,4.75,1.4);g.add(pl);box(4.3,1.2,.1,'#ffffff',0,4.75,1.33,g)}
else{const it=new T.Mesh(new T.Sph(.3,10,8),mat(['#f2b23c','#e8463c','#7a4f2c','#ff8ad8'][q%4]));it.position.set(.8,1.55,1.4);g.add(it)}}}

for(const[k,x,z,w,d]of ie.critters||[])k==='soccer'?soccer(x,z,w,d):k==='pigeons'?pigeons(x,z,w,d):k==='elephant'?elephant(x,z,w,d):k==='basketball'?basketball(x,z,w,d):k==='playground'?playground(x,z,w,d):k==='bigcats'&&bigcats(x,z,w,d);
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
    # bridges: roads (and cars) rise over the river so the boat fits underneath
    rep('var Ko=null,Er=[]', 'var BRG=ie.bridges||{},BRS=BRG.spans||[],BRH=(x,z)=>{if(!BRG.h)return 0;const fx=(x-BRG.x0)/BRG.r-.5,fz=(z-BRG.z0)/BRG.r-.5,i=Math.floor(fx),j=Math.floor(fz),u=fx-i,v=fz-j,g=(a,b)=>a<0||b<0||a>=BRG.nx||b>=BRG.nz?0:BRG.h[b*BRG.nx+a];return(g(i,j)*(1-u)+g(i+1,j)*u)*(1-v)+(g(i,j+1)*(1-u)+g(i+1,j+1)*u)*v};window.__BRS=BRS;window.__BRH=BRH;var Ko=null,Er=[]')
    rep('Ko=y?(P,L)=>Gi(L):null;', 'Ko=y?(P,L)=>Gi(L):BRH;')
    rep('}else{let y=$x[d];if(y!==void 0?Jx(y,m,g):h(m,g,.18,n),g>=4){for(let R of[-1,1])h(Ae(m,R*(g/2-.35)),.15,.24,o);Kl.push({w:g,flat:m})}}', '}else{Ko=BRH;let y=$x[d];if(y!==void 0?Jx(y,m,g):h(m,g,.18,n),g>=4){for(let R of[-1,1])h(Ae(m,R*(g/2-.35)),.15,.24,o);Kl.push({w:g,flat:m})}Ko=null}')
    rep('A=ne(E,S),w=ne(y,R);i.push(E,A+.2,S', 'A=ne(E,S)+(Ko?Ko(E,S):0),w=ne(y,R)+(Ko?Ko(y,R):0);i.push(E,A+.2,S')
    rep('m=.2,d=E=>m+ne(E[0],E[1]);', 'm=.2,d=E=>m+ne(E[0],E[1])+(Ko?Ko(E[0],E[1]):0);')
    # a 4th kind of snack: apples
    rep('r_={convenience:0,cafe:1,bakery:2}', 'r_={convenience:0,cafe:1,bakery:2,apple:3}')
    rep('[[f,14259775]]],u=[0,0,0]', '[[f,14259775]],[[new Le(.62,14,10),14164010],[new ce(.06,.06,.4,6).translate(0,.68,0),5913652],[new Le(.26,8,6).scale(1.4,.4,.8).translate(.28,.8,0),4891194]]],u=[0,0,0,0]')
    rep('for(let g=0;g<3;g++){let _=h[g]', 'for(let g=0;g<4;g++){let _=h[g]')
    rep('["Ramyeon!","Coffee!","Bread!"][b.t]', '["Ramyeon!","Coffee!","Bread!","Apple!"][b.t]')
    rep('S=ne(h+m,u+d)+E(u+d),y=ne(h-m,u-d)+E(u-d),R=ne(h,u)+E(u);', 'JF=window.__JP||(()=>0),S=ne(h+m,u+d)+E(u+d)+JF(h+m,u+d,f)+BRH(h+m,u+d),y=ne(h-m,u-d)+E(u-d)+JF(h-m,u-d,f)+BRH(h-m,u-d),R=ne(h,u)+E(u)+JF(h,u,f)+BRH(h,u);')   # cars jump the ramps
    rep('r.position.set(0,1.9,-2410),$t.add(r)', 'r.position.set(0,1.9,-2410)')   # no Han River out in the countryside          # high enough to fly over Mt. Pigeon
    rep('t=1800,e=new ce(.18,.25,4,5,1,!0)', 't=6000,e=new ce(.18,.25,4,5,1,!0)')   # a forest needs more trees on screen
    # the tunnel: room to fly through under the mountain
    rep('bi=en.spaceAt;{const SB=', 'bi=en.spaceAt;{const old0=bi;bi=(x,z,y)=>{for(const m of window.__MUSEUM||[]){const dx=x-m.cx,dz=z-m.cz,c=Math.cos(m.f),s=Math.sin(m.f),lx=dx*c-dz*s,lz=dx*s+dz*c;if(Math.abs(lx)<m.L/2&&lz>=m.fz+.4&&lz<m.D/2+2.6){const fl=lz<=m.D/2?1.4:1.4*Math.max(0,1-(lz-m.D/2)/2.6);return y<fl+m.H-.6?{f:fl,c:1.4+m.H-.1,name:null}:{f:m.top+5,c:1e4,name:null}}if(Math.abs(lx)<m.HW/2+.4&&lz>m.bz-.4&&lz<m.fz+.4){const inner=Math.abs(lx)<m.HW/2-.9&&lz>m.bz+.9&&lz<m.fz-.9,door=Math.abs(lx)<m.DW/2-.6&&y<1.4+m.DH-.5;if(inner||door)return y<1.4+m.H-.4?{f:1.4,c:1.4+m.H-.5,name:null}:{f:m.top,c:1e4,name:null};return{f:m.top,c:1e4,name:null}}}for(const sf of window.__SECRET||[]){const r=sf(x,z,y);if(r)return r}for(const S of window.__STAT||[]){const i=Math.floor((x-S.x0)/S.r),j=Math.floor((z-S.z0)/S.r);if(i>=0&&j>=0&&i<S.nx&&j<S.nz){const h=S.h[j*S.nx+i];if(h>.3)return{f:h,c:1e4,name:null}}}if(window.__boatAt){const dk=window.__boatAt(x,z);if(dk!=null&&y>dk-2.5)return{f:dk,c:1e4,name:null}}for(const[hw,P,dh]of window.__BRS||[]){for(let i=1;i<P.length;i++){const[a,b]=P[i-1],[c,d]=P[i],dx=c-a,dz=d-b,L=dx*dx+dz*dz||1;let t=((x-a)*dx+(z-b)*dz)/L;if(t<-.05||t>1.05)continue;t=t<0?0:t>1?1:t;const px=a+dx*t-x,pz=b+dz*t-z;if(px*px+pz*pz<(dh||hw+1.3)**2){const h=window.__BRH(x,z),g0=ne(x,z);if(h>1.5)return y<g0+h-1.3?{f:g0,c:g0+h-1.2,name:null}:{f:g0+h+.05,c:1e4,name:null}}}}{const MR=window.__mroad;if(MR){if(!MR.bb){let a=1e9,b=1e9,c=-1e9,d=-1e9;for(const[px,pz]of MR.P){a=Math.min(a,px);b=Math.min(b,pz);c=Math.max(c,px);d=Math.max(d,pz)}MR.bb=[a-8,b-8,c+8,d+8]}const B=MR.bb;if(x>B[0]&&x<B[2]&&z>B[1]&&z<B[3]){let bd=1e9,bk=-1;for(let k=0;k<MR.P.length;k++){const dx=MR.P[k][0]-x,dz=MR.P[k][1]-z,q=dx*dx+dz*dz;q<bd&&(bd=q,bk=k)}if(bd<MR.hw*MR.hw&&y>MR.Y[bk]-3)return{f:MR.Y[bk],c:1e4,name:null}}}}if(window.__inTunnel&&y<9.5&&window.__inTunnel(x,z))return{f:.3,c:8.6,name:null};for(const[a,b,c,d,lo]of window.__gantries||[]){const dx=c-a,dz=d-b,L=dx*dx+dz*dz;let t=((x-a)*dx+(z-b)*dz)/L;if(t>.08&&t<.92){const px=a+dx*t-x,pz=b+dz*t-z;if(px*px+pz*pz<2.2){const f0=old0?old0(x,z,y):null;return y<lo+1?{f:f0?f0.f:He(x,z),c:lo,name:null}:{f:lo+4.2,c:1e4,name:null}}}}return old0?old0(x,z,y):null}}{const SB=')
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
