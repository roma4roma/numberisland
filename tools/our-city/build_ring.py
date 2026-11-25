"""Adds the RING (16 sheets around the first city) to city.json -> city_ring.json:
ring roads, ponds, streams, and the nature: Mt. Pigeon (real heights + tunnel), forest, farm, river + waterfall, lake + beach.
Students' ring designs go in sheets_data.py like the first 9 (sheet names N1-N5, S1-S5, W1-W3, E1-E3).
run from tools/:  PYTHONPATH=.:our-city python3 our-city/build_ring.py"""
import json, math, os, random
from freemap import curve, ns
from sheets_data import RING_SHEETS

HERE = os.path.dirname(os.path.abspath(__file__))
C = json.load(open(os.path.join(HERE, 'city.json')))
M = 10.0   # metres per square

# ---- the mountain: heights follow the bands printed on the sheets (0, 100 ... 500 m)
cx, cy = ns['MOUNTAIN_C']
RX, RY = 82, 72
g = random.Random(11); PH = [g.random() * 6.28 for _ in range(3)]
PROFILE = [(1, 0), (.8, 60), (.62, 130), (.45, 200), (.3, 260), (.17, 305), (0, 330)]   # wide and gradual, rounded top
def mountain_h(x, z):
    """height in metres at world metres (x, z). The whole city grid stays FLAT: the mountain only rises outside it."""
    X, Z = x / M, z / M
    dx_ = max(-20 - X, 0, X - 80); dz_ = max(-14 - Z, 0, Z - 56)
    ramp = min(1, max(0, (math.hypot(dx_, dz_) - 2) / 10)); ramp = ramp * ramp * (3 - 2 * ramp)
    return raw_h(X, Z) * ramp
def raw_h(X, Z):
    a = math.atan2((Z - cy) / RY, (X - cx) / RX)
    w = 1 + .025 * (math.sin(3 * a + PH[0]) + .6 * math.sin(5 * a + PH[1]) + .4 * math.sin(9 * a + PH[2]))
    r = math.hypot((X - cx) / RX, (Z - cy) / RY) / w
    if r >= 1: return 0.0
    for (r0, h0), (r1, h1) in zip(PROFILE, PROFILE[1:]):
        if r1 <= r <= r0:
            t = (r0 - r) / (r0 - r1)
            if r0 == 1: t = t * t * (3 - 2 * t)          # soft foot of the mountain
            return h0 + (h1 - h0) * t
    return PROFILE[-1][1]

T = {'x0': -700, 'z0': -1400, 'step': 10, 'nx': 291, 'nz': 221}
T['dm'] = [round(mountain_h(T['x0'] + i * T['step'], T['z0'] + j * T['step']) * 10) for j in range(T['nz']) for i in range(T['nx'])]
# carve a level shelf for the Mountain Road so it sits on the slope (the game smooths the ground, so carve wide)
_mr = [w_pts for w_pts in ns['RING_ROADS'] if 'over' in w_pts[2:]][0]
_line = [(x * M, z * M) for x, z in curve(_mr[1], n=60)]
_prof = [mountain_h(x, z) for x, z in _line]
for j in range(T['nz']):
    for i in range(T['nx']):
        x, z = T['x0'] + i * T['step'], T['z0'] + j * T['step']
        best = min(range(len(_line)), key=lambda k: (_line[k][0] - x) ** 2 + (_line[k][1] - z) ** 2)
        d = math.hypot(_line[best][0] - x, _line[best][1] - z)
        if d < 30:
            q = j * T['nx'] + i; target = _prof[best] * 10
            t = 0 if d < 14 else (d - 14) / 16
            T['dm'][q] = round(min(T['dm'][q], target + (T['dm'][q] - target) * t))

# ---- roads: the ring roads join the city's roads; the outer ring road goes into a tunnel under the mountain
roads = list(C['roads'])
tunnels = []
NAMES = {0: 'Outer Ring Road', 1: 'Loop Road'}
for k, (w, pts, *f) in enumerate(ns['RING_ROADS']):
    line = curve(pts, 'straight' in f, n=24)
    P = [[round(p[0] * M, 1), round(p[1] * M, 1)] for p in line]
    if k == 0:
        # dense points so the tunnel ends are exact
        dense = []
        for a, b in zip(P, P[1:]):
            L = math.hypot(b[0] - a[0], b[1] - a[1]); n = max(1, int(L / 4))
            dense += [[a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n] for i in range(n)]
        dense.append(P[-1])
        runs, cur, under = [], [], None
        for p in dense:
            u = mountain_h(*p) > 2.5
            if under is None or u == under: cur.append(p)
            else:
                runs.append((under, cur)); cur = [cur[-1], p]
            under = u
        runs.append((under, cur))
        for u, r in runs:
            r = [[round(a, 1), round(b, 1)] for a, b in r]
            if u: tunnels.append(r)
            else: roads.append({'w': round(w * M, 1), 'main': True, 'pts': r, 'name': NAMES[0]})
        continue
    if 'over' in f: continue
    roads.append({'w': round(w * M, 1), 'main': w == ns['MAIN'], 'pts': P, 'name': NAMES.get(k, 'Mountain Road' if 'over' in f else ('Ring Street' if w != ns['MAIN'] else 'Ring Avenue'))})

streams = C['streams'] + [[[round(p[0] * M, 1), round(p[1] * M, 1)] for p in curve(s, n=24)] for s in ns['RING_STREAMS']]
ponds = C['ponds'] + [[px * M, py * M, rx * M, ry * M] for px, py, rx, ry in ns['RING_PONDS']]

# road points, for keeping trees and fields off the roads
RP = []
for r in roads:
    for a, b in zip(r['pts'], r['pts'][1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1]); n = max(1, int(L / 6))
        RP += [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n, r['w'] / 2) for i in range(n + 1)]
def near_road(x, z, extra):
    return any(abs(px - x) < hw + extra and abs(pz - z) < hw + extra and math.hypot(px - x, pz - z) < hw + extra for px, pz, hw in RP)

# ---- the students' ring sheets
gantries, keepout = [], []
for name, items in RING_SHEETS.items():
    sc, sr = ns['RING'][name]; ox, oy = sc * 20, sr * 14
    for kind, c, r, w, d, fl, col, label in items:
        if kind == 'gantry':
            ax, az, bx, bz = (ox + c) * M, (oy + r) * M, (ox + w) * M, (oy + d) * M
            gantries.append([round(ax, 1), round(az, 1), round(bx, 1), round(bz, 1), fl * 3.2, col, label]); keepout += [(ax - 9, az - 9, 18, 18), (bx - 9, bz - 9, 18, 18)]
            continue
        it = {'k': kind, 'x': round((ox + c) * M, 1), 'z': round((oy + r) * M, 1), 'w': round(w * M, 1), 'd': round(d * M, 1), 'f': fl,
              'c': None if kind in ('raccoon', 'pigeonstatue') else col, 'n': label, 's': name}
        if kind in ('raccoon', 'pigeonstatue'):
            it['rot'] = round(math.atan2(300 - (it['x'] + it['w'] / 2), 210 - (it['z'] + it['d'] / 2)), 3)   # face the middle of the city
        C['items'].append(it); keepout.append((it['x'] - 6, it['z'] - 6, it['w'] + 12, it['d'] + 12))
    C['done'].append(name)
def kept_out(x, z): return any(a < x < a + w and b < z < b + d for a, b, w, d in keepout)
# ---- forest
inside = ns['inside']
FOREST = [(x * M, z * M) for x, z in ns['FOREST']]
g = random.Random(7); trees = []
for z in range(-300, 400, 8):
    for x in range(-450, 100, 8):
        tx, tz = x + g.uniform(-3, 3), z + g.uniform(-3, 3)
        if inside(FOREST, tx, tz) and not near_road(tx, tz, 5) and not kept_out(tx, tz) and not any(((tx - px) / (rx + 6)) ** 2 + ((tz - pz) / (ry + 6)) ** 2 < 1 for px, pz, rx, ry in ponds):
            trees.append([round(tx, 1), round(tz, 1)])
# ---- farm fields
FARM = [(x * M, z * M) for x, z in ns['FARM']]
fields = []; barn = None
for fx in range(-450, -100, 70):
    for fz in range(430, 750, 60):
        mx, mz = fx + 35, fz + 30
        if not inside(FARM, mx, mz) or near_road(mx, mz, 30): continue
        if barn is None and -200 < mx < -100 and mz < 560: barn = [mx, mz]; continue
        fields.append([fx + 3, fz + 3, 64, 54, len(fields) % 4])
# ---- river + lake
RIV = [[round(p[0] * M, 1), round(p[1] * M, 1)] for p in curve(ns['RIVER'], n=80)]
lx, ly, lrx, lry = ns['LAKE']
nature = {'forest': FOREST, 'farm': FARM, 'fields': fields, 'barn': barn, 'river': RIV, 'riverW': ns['RIVER_W'] * M,
          'lake': [lx * M, ly * M, lrx * M, lry * M], 'beach': 22, 'mountain': [cx * M, cy * M, RX * M, RY * M],
          'lookout': [880, -290], 'tunnels': tunnels, 'trees': trees,
          'mroad': [[round(x, 1), round(z, 1)] for x, z in _line], 'gantries': gantries}
C.update({'roads': roads, 'streams': streams, 'ponds': ponds, 'terrain': T, 'nature': nature,
          'bounds': [-420.0, -1000.0, 1900.0, 750.0]})
json.dump(C, open(os.path.join(HERE, 'city_ring.json'), 'w'))
print('ring ok:', len(roads), 'roads,', len(tunnels), 'tunnel(s),', len(trees), 'forest trees,', len(fields), 'fields, barn', barn,
      '| peak', max(T['dm']) / 10, 'm')
