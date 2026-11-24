import json, math
from freemap import curve, ns
import math as _m
_segs = [(w / 2 - .05, curve(pts, 'straight' in f)) for w, pts, *f in ns['ROADS']] + [(ns['STREAM_W'] / 2, curve(st)) for st in ns['STREAMS']]
def blocked(x, y):  # looser than the printed-sheet check: buildings may touch the kerb
    for hw, pts in _segs:
        for px, py in pts:
            if abs(px - x) < hw + 1 and abs(py - y) < hw + 1 and _m.hypot(px - x, py - y) < hw: return True
    for px, py, rx, ry in ns['PONDS']:
        if ((x - px) / (rx + .45)) ** 2 + ((y - py) / (ry + .45)) ** 2 < 1: return True
    tx, ty = ns['TOWER_C']
    return _m.hypot(x - tx, y - ty) < ns['ROUNDABOUT_R'] + ns['MAIN'] / 2
from sheets_data import SHEETS
SH = {n: ('ABC'.index(n[0]), int(n[1]) - 1) for n in [r + c for r in 'ABC' for c in '123']}
def fits(cx0, cy0, w, h):
    """sample points inside the rect (city squares) that hit a road, pond or roundabout"""
    bad = []
    nx, ny = max(2, int(w * 3)), max(2, int(h * 3))
    for i in range(nx):
        for j in range(ny):
            x, y = cx0 + (i + .5) * w / nx, cy0 + (j + .5) * h / ny
            if blocked(x, y): bad.append((x, y))
    return bad
def trim(x0, y0, w, h):
    step = .25
    for _ in range(80):
        bad = fits(x0, y0, w, h)
        if not bad or w < .6 or h < .6: break
        # remove the strip (left/right/top/bottom) holding the most blocked points
        cands = [('l', sum(1 for x, y in bad if x < x0 + w / 2)), ('r', sum(1 for x, y in bad if x >= x0 + w / 2)),
                 ('t', sum(1 for x, y in bad if y < y0 + h / 2)), ('b', sum(1 for x, y in bad if y >= y0 + h / 2))]
        side = max(cands, key=lambda c: c[1])[0]
        if side == 'l': x0 += step; w -= step
        elif side == 'r': w -= step
        elif side == 't': y0 += step; h -= step
        else: h -= step
    return x0, y0, w, h, not fits(x0, y0, w, h)
out = []; notes = []
for name, items in SHEETS.items():
    i, j = SH[name]
    for kind, c, r, w, d, fl, col, label in items:
        x0, y0 = j * 20 + c, i * 14 + r
        if kind not in ('dock', 'bridge'):
            nx0, ny0, nw, nd, ok = trim(x0, y0, w, d)
            if (nw, nd) != (w, d): notes.append(f'{name} {label or kind+str(fl)}: trimmed {w}x{d} -> {nw:.2f}x{nd:.2f}' + ('' if ok else ' (still touching)'))
            x0, y0, w, d = nx0, ny0, nw, nd
        out.append({'k': kind, 'x': round(x0 * 10, 1), 'z': round(y0 * 10, 1), 'w': round(w * 10, 1), 'd': round(d * 10, 1), 'f': fl, 'c': col, 'n': label, 's': name})
roads = [{'w': round(w * 10, 1), 'main': w == ns['MAIN'], 'pts': [[round(p[0] * 10, 1), round(p[1] * 10, 1)] for p in curve(pts, 'straight' in f, n=24)]} for w, pts, *f in ns['ROADS']]
streams = [[[round(p[0] * 10, 1), round(p[1] * 10, 1)] for p in curve(s, n=24)] for s in ns['STREAMS']]
ponds = [[px * 10, py * 10, rx * 10, ry * 10] for px, py, rx, ry in ns['PONDS']]
json.dump({'items': out, 'roads': roads, 'streams': streams, 'ponds': ponds, 'tower': [ns['TOWER_C'][0] * 10, ns['TOWER_C'][1] * 10],
           'rr': ns['ROUNDABOUT_R'] * 10, 'mainw': ns['MAIN'] * 10, 'done': list(SHEETS)}, open('/home/claude/work/mock3d/city.json', 'w'))
print(len(out), 'items'); print('\n'.join(notes))
