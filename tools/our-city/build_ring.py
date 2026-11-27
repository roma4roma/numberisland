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
    # foothills: next to the city the ground rises gently (about 1 in 8), getting steeper further out,
    # and blends smoothly into the real mountain shape (so no cliff wall facing the city)
    d = math.hypot(dx_, dz_) * M
    if d <= 15: return 0.0
    cap = .12 * (d - 15) + .0006 * (d - 15) ** 2
    r, k = raw_h(X, Z), 8.0
    return max(0.0, -k * math.log(math.exp(-r / k) + math.exp(-cap / k)))
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
def _radius(P, k, w=4):
    a, b, c = P[max(0, k - w)], P[k], P[min(len(P) - 1, k + w)]
    A, B, C = math.dist(a, b), math.dist(b, c), math.dist(a, c)
    ar = abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])) / 2
    return A * B * C / (4 * ar) if ar > 1e-6 else 1e9
# open up hairpins: a 9 m road needs bends of at least ~16 m radius
for _it in range(3000):
    tight = [k for k in range(4, len(_line) - 4) if _radius(_line, k) < 16]
    if not tight: break
    L_ = list(_line)
    for k in {j for t in tight for j in range(max(1, t - 12), min(len(_line) - 1, t + 13))}:
        _line[k] = ((L_[k - 1][0] + 2 * L_[k][0] + L_[k + 1][0]) / 4, (L_[k - 1][1] + 2 * L_[k][1] + L_[k + 1][1]) / 4)
# even spacing again (about 1.2 m)
_D = [0.0]
for k in range(1, len(_line)): _D.append(_D[-1] + math.dist(_line[k - 1], _line[k]))
_n = int(_D[-1] / 1.2); _rs = []; j = 0
for i in range(_n + 1):
    d = _D[-1] * i / _n
    while j < len(_D) - 2 and _D[j + 1] < d: j += 1
    t = (d - _D[j]) / ((_D[j + 1] - _D[j]) or 1)
    _rs.append((_line[j][0] + (_line[j + 1][0] - _line[j][0]) * t, _line[j][1] + (_line[j + 1][1] - _line[j][1]) * t))
_line = _rs
_prof = [mountain_h(x, z) for x, z in _line]
# the road's own height: follows the ground but never steeper than 15% (cuts in or builds up where needed)
_ds = [0] + [math.dist(_line[k - 1], _line[k]) for k in range(1, len(_line))]
for _pass in range(3):
    for k in range(1, len(_prof)): _prof[k] = min(max(_prof[k], _prof[k - 1] - .15 * _ds[k]), _prof[k - 1] + .15 * _ds[k])
    for k in range(len(_prof) - 2, -1, -1): _prof[k] = min(max(_prof[k], _prof[k + 1] - .15 * _ds[k + 1]), _prof[k + 1] + .15 * _ds[k + 1])
_prof[0] = 0.0
for j in range(T['nz']):
    for i in range(T['nx']):
        x, z = T['x0'] + i * T['step'], T['z0'] + j * T['step']
        best = min(range(len(_line)), key=lambda k: (_line[k][0] - x) ** 2 + (_line[k][1] - z) ** 2)
        d = math.hypot(_line[best][0] - x, _line[best][1] - z)
        if d < 30:
            q = j * T['nx'] + i; target = _prof[best] * 10
            t = 0 if d < 13 else (d - 13) / 17; t = t * t * (3 - 2 * t)
            T['dm'][q] = round(target + (T['dm'][q] - target) * t)

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
gantries, keepout, ramps = [], [], []
for name, items in RING_SHEETS.items():
    sc, sr = ns['RING'][name]; ox, oy = sc * 20, sr * 14
    for kind, c, r, w, d, fl, col, label in items:
        if kind == 'gantry':
            ax, az, bx, bz = (ox + c) * M, (oy + r) * M, (ox + w) * M, (oy + d) * M
            gantries.append([round(ax, 1), round(az, 1), round(bx, 1), round(bz, 1), fl * 3.2, col, label]); keepout += [(ax - 9, az - 9, 18, 18), (bx - 9, bz - 9, 18, 18)]
            continue
        if kind == 'ramp':
            cx_, cz_ = (ox + c + w / 2) * M, (oy + r + d / 2) * M
            best = None
            for rd in roads:
                for a_, b_ in zip(rd['pts'], rd['pts'][1:]):
                    dx_, dz_ = b_[0] - a_[0], b_[1] - a_[1]; L_ = dx_ * dx_ + dz_ * dz_ or 1
                    t_ = max(0, min(1, ((cx_ - a_[0]) * dx_ + (cz_ - a_[1]) * dz_) / L_)); px_, pz_ = a_[0] + dx_ * t_, a_[1] + dz_ * t_
                    dd = math.hypot(px_ - cx_, pz_ - cz_)
                    if best is None or dd < best[0]: L1 = math.sqrt(L_); best = (dd, px_, pz_, dx_ / L1, dz_ / L1, rd['w'] / 2, rd)
            path = [[round(q[0], 1), round(q[1], 1)] for q in best[6]['pts'] if math.hypot(q[0] - best[1], q[1] - best[2]) < 95]
            ramps.append([round(best[1], 1), round(best[2], 1), round(best[3], 4), round(best[4], 4), best[5], path])
            continue
        it = {'k': kind, 'x': round((ox + c) * M, 1), 'z': round((oy + r) * M, 1), 'w': round(w * M, 1), 'd': round(d * M, 1), 'f': fl,
              'c': None if kind in ('raccoon', 'pigeonstatue', 'pig', 'stickman', 'rocket', 'balloon', 'merrygoround', 'parking', 'picnic', 'train', 'secret', 'roof67', 'channel', 'aquarium', 'stadium', 'soccerstadium', 'military', 'rock', 'octopus', 'tigerstatue', 'coaster', 'wall', 'maze', 'box', 'treehouse') else col, 'n': label, 's': name}
        if kind in ('raccoon', 'pigeonstatue', 'pig', 'stickman'):
            it['rot'] = round(math.atan2(300 - (it['x'] + it['w'] / 2), 210 - (it['z'] + it['d'] / 2)), 3)   # face the middle of the city
        C['items'].append(it); keepout.append((it['x'] - 6, it['z'] - 6, it['w'] + 12, it['d'] + 12))
    C['done'].append(name)
def kept_out(x, z): return any(a < x < a + w and b < z < b + d for a, b, w, d in keepout)
# ---- forest
inside = ns['inside']
FOREST = [(x * M, z * M) for x, z in ns['FOREST']]
# apple trees in the north-west of Raccoon Forest (each has an apple to eat under it)
apples = []
_cand = [(x, z) for z in range(-170, 130, 9) for x in range(-210, 20, 9)]
random.Random(4).shuffle(_cand)
for x, z in _cand:
    if len(apples) >= 12: break
    if not inside(FOREST, x, z) or near_road(x, z, 12) or kept_out(x, z): continue
    if any(math.hypot(x - a_, z - b_) < 38 for a_, b_ in apples): continue
    apples.append((x, z)); keepout.append((x - 8, z - 8, 16, 16))
g = random.Random(7); trees = []
for z in range(-300, 400, 8):
    for x in range(-450, 100, 8):
        tx, tz = x + g.uniform(-3, 3), z + g.uniform(-3, 3)
        if inside(FOREST, tx, tz) and not near_road(tx, tz, 5) and not kept_out(tx, tz) and not any(((tx - px) / (rx + 6)) ** 2 + ((tz - pz) / (ry + 6)) ** 2 < 1 for px, pz, rx, ry in ponds):
            trees.append([round(tx, 1), round(tz, 1)])
# ---- farm fields
FARM = [(x * M, z * M) for x, z in ns['FARM']]
fields = []; barn = None
for fx in range(-450, -90, 70):
    for fz in range(430, 750, 60):
        mx, mz = fx + 35, fz + 30
        if not inside(FARM, mx, mz) or near_road(mx, mz, 30) or kept_out(mx, mz): continue
        if any(((mx - px) / (rx + 45)) ** 2 + ((mz - pz) / (ry + 40)) ** 2 < 1 for px, pz, rx, ry in ponds): continue
        fields.append([fx + 3, fz + 3, 64, 54, len(fields) % 4])
# smaller fields fill the farm squares on the sheets (S1 etc.), like the rows printed there
for fx in range(-188, -90, 24):
    for fz in range(424, 556, 22):
        mx, mz = fx + 11, fz + 10
        if not inside(FARM, mx, mz) or near_road(mx, mz, 13) or kept_out(mx, mz): continue
        if any(f[0] <= mx <= f[0] + f[2] and f[1] <= mz <= f[1] + f[3] for f in fields): continue
        if any(((mx - px) / (rx + 14)) ** 2 + ((mz - pz) / (ry + 14)) ** 2 < 1 for px, pz, rx, ry in ponds): continue
        fields.append([fx + 1, fz + 1, 22, 20, (fx // 24 + fz // 22) % 4])
# ---- river + lake
RIV = [[round(p[0] * M, 1), round(p[1] * M, 1)] for p in curve(ns['RIVER'], n=80)]
lx, ly, lrx, lry = ns['LAKE']
nature = {'forest': FOREST, 'farm': FARM, 'fields': fields, 'barn': barn, 'river': RIV, 'riverW': ns['RIVER_W'] * M,
          'lake': [lx * M, ly * M, lrx * M, lry * M], 'beach': 22, 'mountain': [cx * M, cy * M, RX * M, RY * M],
          'lookout': [880, -290], 'tunnels': tunnels, 'trees': trees,
          'mroad': [[round(x, 1), round(z, 1)] for x, z in _line], 'mroadh': [round(h, 2) for h in _prof], 'gantries': gantries, 'ramps': ramps, 'apples': [[float(x), float(z)] for x, z in apples]}
C.update({'roads': roads, 'streams': streams, 'ponds': ponds, 'terrain': T, 'nature': nature,
          'bounds': [-420.0, -1000.0, 1900.0, 750.0]})
json.dump(C, open(os.path.join(HERE, 'city_ring.json'), 'w'))
print('ring ok:', len(roads), 'roads,', len(tunnels), 'tunnel(s),', len(trees), 'forest trees,', len(fields), 'fields, barn', barn,
      '| peak', max(T['dm']) / 10, 'm')
