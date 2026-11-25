"""Our City design sheets: 1 instruction page + 9 A3 grid sheets (A1..C3) that join into one 3x3 city.
Each sheet: 20 x 14 squares of 18 mm (1 square = 10 m), an edge road on all four sides,
a river across the bottom row of sheets (edge roads cross it as bridges), and the Start Tower on B2."""
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfgen import canvas

W, H = landscape(A3)
SQ = 18 * mm
COLS, ROWS = 20, 14
GX = (W - COLS * SQ) / 2           # left of grid
GY = 15 * mm                       # bottom of grid
INK = HexColor('#1E2A33')
GRID = HexColor('#C9D1D8')
GRID5 = HexColor('#9AA6B1')
ROAD = HexColor('#BFC3C7')
ROAD_LINE = HexColor('#FFFFFF')
WATER = HexColor('#8CCBF2')
WATER_D = HexColor('#4FA3DB')
BRIDGE = HexColor('#A9855F')
TOWER = HexColor('#5B6B7A')
SOFT = HexColor('#5A6772')
RIVER_ROWS = (9, 10, 11)           # rows counted from the top (0 = top edge road)
CITY_W, CITY_H = 60, 42
TOWER_C = (30, 20)               # Start Tower centre (B2), inside the roundabout
MAIN, SMALL = 1.25, .9           # road widths in squares
ROADS = [  # (width, points[, 'straight']) — smooth curves through these points
    (MAIN, [(.6, .6), (59.4, .6), (59.4, 41.4), (.6, 41.4), (.6, .6)], 'straight'),          # ring road around the city
    (MAIN, [(.6, 5), (9, 7), (17, 11.5), (27.0, 18.0)]),                                       # NW boulevard to the roundabout
    (MAIN, [(33.4, 21.1), (42, 24), (50, 27.5), (59.4, 29)]),                                  # ...and on to the east
    (MAIN, [(30, .6), (31.5, 7), (29.5, 12), (30, 16.4)]),                                       # north avenue
    (MAIN, [(30.3, 23.6), (32, 30), (29, 36), (31, 41.4)]),                                    # south avenue
    (MAIN, [(.6, 30), (9, 28.5), (18, 32), (25, 30), (31.2, 28.5)]),                           # south-west road
    (SMALL, [(17, .6), (16, 6), (12.5, 13), (12, 21), (15, 27), (18, 32)]),                   # winding west street
    (SMALL, [(12, 21), (5, 23.5), (.6, 22)]),
    (SMALL, [(47, .6), (44, 8), (46.5, 15), (54, 18), (59.4, 17)]),                           # winding east street
    (SMALL, [(44, 8), (37, 9.5), (31, 9)]),
    (SMALL, [(46.5, 15), (42, 24)]),
    (SMALL, [(30.5, 34), (38, 36.5), (45, 34), (50, 27.5)]),                                   # south-east curve
    (SMALL, [(16, 6), (23, 5), (31.3, 5.5)]),                                                 # cross street to the north avenue
    (SMALL, [(18, 32), (21, 41.4)]),
]
PONDS = [(52, 8, 2.3, 1.6), (6, 17.5, 2.6, 1.9), (15, 37, 1.6, 1.2), (53, 35.5, 2.2, 1.6), (24, 37, 2, 1.4), (24.5, 10, 2.1, 1.5), (51, 22.5, 2, 1.4)]  # x, y, rx, ry
STREAMS = [[(24.5, 10), (22.5, 11.8), (23.5, 13.4)], [(51, 22.5), (54, 24.5), (57.5, 23.8)], [(6, 17.5), (9, 19.8), (8.5, 24.5)]]
STREAM_W = .75
ROUNDABOUT_R = 3.6
# ---- the RING: 16 more sheets around the first city (5 x 5 sheets in all). Coordinates carry on past the old edges:
# x from -20 to 80, y from -14 to 56. N1-N5 along the top, S1-S5 along the bottom, W1-W3 left, E1-E3 right.
LOOP = [(-9, 21), (-10.5, 12), (-9, 3), (-6.5, -4), (0, -7), (10, -7.8), (20, -6.5), (30, -7.4), (40, -6.3), (50, -7.8), (57, -5), (61, -1.5),
        (64, 2.5), (67, 7), (70.5, 12), (69, 21), (70.5, 30), (69, 39), (66.5, 46), (60, 49), (50, 50), (40, 48.6), (30, 49.8), (20, 48.6), (10, 50), (0, 49),
        (-6.5, 46), (-9, 39), (-10.5, 30), (-9, 21)]
RING_ROADS = [
    (MAIN, [(-19.4, -13.4), (79.4, -13.4), (79.4, 55.4), (-19.4, 55.4), (-19.4, -13.4)], 'straight'),    # new outer ring road
    (MAIN, LOOP),                                                                                         # winding loop through every ring sheet
    (MAIN, [(30, .6), (28.5, -4), (31, -9.5), (30, -13.4)]),                                              # north avenue carries on
    (MAIN, [(31, 41.4), (33, 46), (30.5, 51.5), (31, 55.4)]),                                             # south avenue carries on
    (MAIN, [(.6, 22), (-4, 20.5), (-13.5, 23), (-19.4, 21.5)]),                                           # west
    (MAIN, [(59.4, 17), (64, 18.5), (74, 16), (79.4, 17.5)]),                                             # east
    (SMALL, [(17, .6), (15, -3.5), (16, -7.3)]),
    (SMALL, [(47, .6), (49, -3.5), (47.5, -6.8)]),
    (SMALL, [(10, -7.8), (8.5, -10.5), (10.5, -13.4)]),
    (SMALL, [(-6.5, -4), (-12, -7), (-19.4, -6)]),
    (SMALL, [(61, -1.5), (63.8, -4.5), (66, -8), (69, -15), (78, -19.5), (86, -18.5), (82, -24.5), (88, -29)], 'over'),                                          # mountain road up to the Lookout
    (SMALL, [(.6, 5), (-4, 3.5), (-9, 3)]),
    (SMALL, [(.6, 30), (-4.5, 32), (-10.5, 30)]),
    (SMALL, [(-9, 39), (-14, 41), (-19.4, 39.5)]),
    (SMALL, [(59.4, 29), (64.5, 31), (70.5, 30)]),
    (SMALL, [(67, 7), (72, 8.5), (79.4, 9)]),
    (SMALL, [(70.5, 30), (75, 33.5), (79.4, 32.5)]),
    (SMALL, [(21, 41.4), (18.5, 45), (20, 48.6)]),
    (SMALL, [(50, 50), (48, 52.5), (50.5, 55.4)]),
    (SMALL, [(-6.5, 46), (-11, 50), (-9, 55.4)]),
    (SMALL, [(66.5, 46), (71, 50.5), (69, 55.4)]),
]
RING_PONDS = [(4, -10.5, 1.8, 1.3), (38, -10.8, 1.7, 1.2), (-15, 12, 1.5, 2), (12, 52.5, 1.9, 1.3), (44, 45, 1.6, 1.2), (-14.5, -10.5, 1.4, 1.1), (64.5, 8.5, 1.4, 1.1), (-14.5, 47.5, 1.5, 1.1)]
RING_STREAMS = [[(38, -10.8), (41, -10.2), (43, -11.5)], [(-15, 12), (-16, 8.5), (-14, 6.5)], [(12, 52.5), (8.5, 52), (6, 53.2)]]
# ---- NATURE on the ring (it spreads past the edge of the city, like real nature would)
import math as _m, random as _r
def blob(cx, cy, rx, ry, seed, n=90, wob=.07):
    g = _r.Random(seed); ph = [g.random() * 6.28 for _ in range(3)]
    return [(cx + rx * (1 + wob * (_m.sin(3 * a + ph[0]) + .6 * _m.sin(5 * a + ph[1]) + .4 * _m.sin(9 * a + ph[2]))) * _m.cos(a),
             cy + ry * (1 + wob * (_m.sin(3 * a + ph[0]) + .6 * _m.sin(5 * a + ph[1]) + .4 * _m.sin(9 * a + ph[2]))) * _m.sin(a))
            for a in [2 * _m.pi * k / n for k in range(n)]]
def inside(poly, x, y):
    c = False
    for k in range(len(poly)):
        (x1, y1), (x2, y2) = poly[k - 1], poly[k]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1: c = not c
    return c
MOUNTAIN_C = (125, -55)       # the peak is on N5, the mountain spreads off the map
MOUNTAIN = [(blob(125, -55, 82 * f, 72 * f, 11 + k, wob=.025 - .002 * k), col, h) for k, (f, col, h) in enumerate(
    [(1, '#CFE0A4', 0), (.8, '#B9C98C', 100), (.62, '#A9A27C', 200), (.45, '#9C948C', 300), (.3, '#C9C9CF', 400), (.17, '#FFFFFF', 500)])]
FOREST = [(-45, -30), (9, -30), (9, -10), (1, -9.3), (-5.5, -6.8), (-10.5, -1), (-11.6, 8), (-12, 16), (-11.8, 25), (-12.6, 33), (-15, 38.5), (-45, 40)]
FARM = [(-45, 41.6), (-12, 42.6), (-9.4, 45), (-7.5, 49), (-4, 51.5), (1, 52.5), (2, 56), (2, 75), (-45, 75)]
RIVER = [(76, -3), (74.6, 3.6), (73.2, 8.5), (75.6, 16), (73.4, 24), (75.6, 32), (74, 39), (76.5, 45)]   # from the waterfall down to the lake
RIVER_W = 2.0
LAKE = (80, 52, 13, 9)       # x, y, rx, ry: the lake (with a beach) spreads off the map, bottom-right
_g = _r.Random(5)
FOREST_TREES = [(x, y, .45 + _g.random() * .35) for x, y in ((_g.uniform(-45, 10), _g.uniform(-30, 40)) for _ in range(5200)) if inside(FOREST, x, y)]
LABELS = [  # (x, y, text, size) in squares
    (71, -10.6, 'MT. PIGEON', 22), (71.5, -9.4, 'already made: don\u2019t draw here', 9),
    (63.5, -9.6, 'Road to the Lookout', 10), (72, 12, 'River', 13), (72, 28, 'River', 13),
    (69.5, 44.2, 'BEACH', 13), (78, 51.2, 'LAKE', 22), (75.5, 54.6, 'Lake Bridge', 10),
    (-16, -1, 'RACCOON FOREST', 20), (-16, 20, 'RACCOON FOREST', 20), (-12, -11.6, 'RACCOON FOREST', 16), (4, -12.2, 'Forest pond', 9),
    (-15, 51.5, 'FARM', 22), (-7, 55, 'FARM', 14), (58.5, -12.3, 'Tunnel', 11), (77.6, 6, 'Tunnel', 11)]
NATURE_NOTE = 'Nature (mountain, forest, farm, lake): you can add small things like a cabin, campsite, trail or lookout (max 2 floors).'

def draw_nature(cv):
    """Forest, farm, river, lake + beach (drawn under the roads)."""
    def poly(pts):
        p = cv.beginPath(); p.moveTo(*pts[0])
        for q in pts[1:]: p.lineTo(*q)
        p.close(); return p
    cv.setFillColor(HexColor('#A9D79B')); cv.drawPath(poly(FOREST), stroke=0, fill=1)
    for x, y, r in FOREST_TREES:
        cv.setFillColor(HexColor('#6FB46A')); cv.setStrokeColor(HexColor('#4E8F4A')); cv.setLineWidth(.05); cv.circle(x, y, r, stroke=1, fill=1)
    cv.saveState(); cv.clipPath(poly(FARM), stroke=0, fill=0)
    cv.setFillColor(HexColor('#D9C98A')); cv.rect(-46, 42, 36, 34, stroke=0, fill=1)
    g = _r.Random(3)
    for fx in range(-45, -10, 7):
        for fy in range(43, 76, 6):
            c = g.choice(['#EAD98A', '#B9D77A', '#9CC46B', '#E6C06A'])
            cv.setFillColor(HexColor(c)); cv.rect(fx + .3, fy + .3, 6.4, 5.4, stroke=0, fill=1)
            cv.setStrokeColor(HexColor('#8A7A4A')); cv.setLineWidth(.05)
            for k in range(1, 9): cv.line(fx + .3, fy + .3 + k * .6, fx + 6.7, fy + .3 + k * .6)
    cv.restoreState()
    lx, ly, rx, ry = LAKE
    cv.setFillColor(HexColor('#F3E3B0')); cv.ellipse(lx - rx - 2.2, ly - ry - 2.2, lx + rx + 2.2, ly + ry + 2.2, stroke=0, fill=1)
    cv.setStrokeColor(WATER); cv.setLineWidth(RIVER_W); cv.setLineCap(1)
    cv.drawPath(smooth_path(cv, RIVER), stroke=1, fill=0)
    cv.setFillColor(WATER); cv.setStrokeColor(WATER_D); cv.setLineWidth(.08); cv.ellipse(lx - rx, ly - ry, lx + rx, ly + ry, stroke=1, fill=1)

def draw_mountain(cv):
    """The mountain sits on top of the roads: the ring road goes through it in a tunnel."""
    def poly(pts):
        p = cv.beginPath(); p.moveTo(*pts[0])
        for q in pts[1:]: p.lineTo(*q)
        p.close(); return p
    for pts, col, h in MOUNTAIN:
        cv.setFillColor(HexColor(col)); cv.setStrokeColor(HexColor('#7A6A55')); cv.setLineWidth(.07)
        cv.drawPath(poly(pts), stroke=1, fill=1)
    # the tunnel: dashed outline of the ring road under the mountain, dark portals where it goes in
    base = MOUNTAIN[0][0]
    cv.setStrokeColor(HexColor('#5A4A3A')); cv.setLineWidth(.08); cv.setDash(.4, .3)
    (px1, _, _), (_, py2, _) = tunnel_portals()
    h = MAIN / 2
    cv.line(px1, -13.4 - h, 79.4 + h, -13.4 - h); cv.line(79.4 + h, -13.4 - h, 79.4 + h, py2)     # outer side
    cv.line(px1, -13.4 + h, 79.4 - h, -13.4 + h); cv.line(79.4 - h, -13.4 + h, 79.4 - h, py2)     # inner side
    cv.setDash()
    for (x, y, horiz) in tunnel_portals():
        cv.setFillColor(HexColor('#3A3530'))
        if horiz: cv.rect(x - .25, y - MAIN / 2 - .2, .5, MAIN + .4, stroke=0, fill=1)
        else: cv.rect(x - MAIN / 2 - .2, y - .25, MAIN + .4, .5, stroke=0, fill=1)
    # the river's waterfall
    cv.setStrokeColor(white); cv.setLineWidth(.12)


def tunnel_portals():
    base = MOUNTAIN[0][0]; out = []
    x = 50.0
    while x < 79.4:
        if inside(base, x, -13.4): out.append((x, -13.4, True)); break
        x += .05
    y = 20.0
    while y > -13.4:
        if inside(base, 79.4, y): out.append((79.4, y, False)); break
        y -= .05
    return out

RING = {**{f'N{k + 1}': (k - 1, -1) for k in range(5)}, **{f'S{k + 1}': (k - 1, 3) for k in range(5)},
        **{f'W{k + 1}': (-1, k) for k in range(3)}, **{f'E{k + 1}': (3, k) for k in range(3)}}   # name -> (sheet column, sheet row); A1 is (0, 0)

def smooth_path(cv, pts):
    """Catmull-Rom curve through pts, as Bezier curves."""
    p = cv.beginPath(); p.moveTo(*pts[0])
    for i in range(len(pts) - 1):
        p0 = pts[i - 1] if i > 0 else pts[i]; p1 = pts[i]; p2 = pts[i + 1]; p3 = pts[i + 2] if i + 2 < len(pts) else pts[i + 1]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        p.curveTo(c1[0], c1[1], c2[0], c2[1], p2[0], p2[1])
    return p

def road_path(cv, pts, flags):
    if 'straight' not in flags: return smooth_path(cv, pts)
    p = cv.beginPath(); p.moveTo(*pts[0])
    for q in pts[1:]: p.lineTo(*q)
    return p

def draw_city(cv, lines=True):
    """Draws river, roads and roundabout in city units (current transform: 1 unit = 1 square, y down)."""
    cv.setLineCap(1); cv.setLineJoin(1)
    draw_nature(cv)
    cv.setLineCap(1); cv.setLineJoin(1)
    cv.setStrokeColor(WATER); cv.setLineWidth(STREAM_W)
    for st in STREAMS + RING_STREAMS: cv.drawPath(smooth_path(cv, st), stroke=1, fill=0)
    for (px, py, rx, ry) in PONDS + RING_PONDS:
        cv.setFillColor(PARK); cv.ellipse(px - rx - .7, py - ry - .7, px + rx + .7, py + ry + .7, stroke=0, fill=1)
        cv.setFillColor(WATER); cv.setStrokeColor(WATER_D); cv.setLineWidth(.06); cv.ellipse(px - rx, py - ry, px + rx, py + ry, stroke=1, fill=1)
    circ = cv.beginPath(); circ.circle(*TOWER_C, ROUNDABOUT_R)
    for col, extra in ((HexColor('#7E858C'), .14), (ROAD, 0)):     # dark curb first, then the road on top
        cv.setStrokeColor(col)
        for w, pts, *f in ROADS + RING_ROADS:
            if 'over' in f: continue
            cv.setLineWidth(w + extra); cv.drawPath(road_path(cv, pts, f), stroke=1, fill=0)
        cv.setLineWidth(MAIN + extra); cv.drawPath(circ, stroke=1, fill=0)
    if lines:
        cv.setStrokeColor(ROAD_LINE); cv.setLineWidth(.07); cv.setDash(.35, .3)
        for w, pts, *f in ROADS + RING_ROADS:
            if w == MAIN and 'over' not in f: cv.drawPath(road_path(cv, pts, f), stroke=1, fill=0)
        cv.drawPath(circ, stroke=1, fill=0); cv.setDash()
    cv.setFillColor(HexColor('#BFE5B5')); cv.circle(*TOWER_C, ROUNDABOUT_R - MAIN / 2 - .07, stroke=0, fill=1)
    draw_mountain(cv)
    for col, extra in ((HexColor('#7E858C'), .14), (ROAD, 0)):
        cv.setStrokeColor(col)
        for w, pts, *f in RING_ROADS:
            if 'over' in f: cv.setLineWidth(w + extra); cv.drawPath(road_path(cv, pts, f), stroke=1, fill=0)
    pass

V_ROADS = (6, 13)                  # streets running up/down on every sheet (they line up from sheet to sheet)
H_ROAD = 7                         # street running across on rows A and B
H_ROAD_C = 8                       # on row C it runs along the river instead
BANK_ROW = 12                      # row C: riverbank park between the river and the bottom edge road
PARK = HexColor('#BFE5B5')  # light green (riverbank)
SHEETS = [r + c for r in 'ABC' for c in '123']   # A = top row of the city, C = bottom (river)


def sheet_pos(name):
    """(sheet column, sheet row) of a sheet; A1 = (0, 0), the ring goes from -1 to 3."""
    if name in RING: return RING[name]
    return int(name[1]) - 1, 'ABC'.index(name[0])


def cell(c, r):
    """Bottom-left corner of grid square (col c, row r counted from the top)."""
    return GX + c * SQ, GY + (ROWS - 1 - r) * SQ


def fill_cell(cv, c, r, color):
    x, y = cell(c, r)
    cv.setFillColor(color)
    cv.rect(x, y, SQ, SQ, stroke=0, fill=1)


def star(cv, cx, cy, r, color):
    import math
    p = cv.beginPath()
    for i in range(10):
        a = math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * .45
        x, y = cx + rr * math.cos(a), cy + rr * math.sin(a)
        p.moveTo(x, y) if i == 0 else p.lineTo(x, y)
    p.close()
    cv.setFillColor(color); cv.setStrokeColor(INK); cv.setLineWidth(1)
    cv.drawPath(p, fill=1, stroke=1)


def mini_map(cv, x, y, size, here=None, ring=False):
    """Locator map. 3x3 (A1..C3), or 5x5 with the ring sheets around it."""
    if ring: return mini_map5(cv, x, y, size, here)
    s = size / 3
    for i, name in enumerate(SHEETS):
        r, c = i // 3, i % 3
        bx, by = x + c * s, y + (2 - r) * s
        cv.setFillColor(HexColor('#FFE08A') if name == here else white)
        cv.setStrokeColor(INK); cv.setLineWidth(1.2)
        cv.rect(bx, by, s, s, stroke=1, fill=1)
    cv.saveState()
    clip = cv.beginPath(); clip.rect(x, y, size, size); cv.clipPath(clip, stroke=0, fill=0)
    cv.translate(x, y + size); cv.scale(size / CITY_W, -size / CITY_H)
    draw_city(cv, lines=False)
    cv.setFillColor(TOWER); cv.rect(TOWER_C[0] - 1, TOWER_C[1] - 1, 2, 2, stroke=0, fill=1)
    cv.restoreState()
    for i, name in enumerate(SHEETS):
        r, c = i // 3, i % 3
        bx, by = x + c * s, y + (2 - r) * s
        cv.setStrokeColor(INK); cv.setLineWidth(1.2); cv.rect(bx, by, s, s, stroke=1, fill=0)
        cv.setFillColor(INK); cv.setFont('Helvetica-Bold', max(7, s * .26))
        cv.drawCentredString(bx + s / 2, by + s * .62, name)


def mini_map5(cv, x, y, size, here=None, done_shade=True, font=None, ghost=False):
    sw, sh = size, size * 70 / 100       # 5 x 5 sheets, each 20 x 14 squares
    s, t = sw / 5, sh / 5
    names = {pos: n for n, pos in RING.items()}
    names.update({(c, r): f'{"ABC"[r]}{c + 1}' for r in range(3) for c in range(3)})
    for (c, r), n in names.items():
        bx, by = x + (c + 1) * s, y + (3 - r) * t
        if ghost:
            if n not in RING: cv.setFillColor(white); cv.setFillAlpha(.55); cv.rect(bx, by, s, t, stroke=0, fill=1); cv.setFillAlpha(1)
            continue
        cv.setFillColor(HexColor('#FFE08A') if n == here else (HexColor('#E3E8EC') if (done_shade and n[0] in 'ABC' and len(n) == 2 and n not in RING) else white))
        cv.rect(bx, by, s, t, stroke=0, fill=1)
    cv.saveState()
    if ghost: cv.restoreState(); cv.saveState(); cv.translate(-1e5, 0)
    clip = cv.beginPath(); clip.rect(x, y, sw, sh); cv.clipPath(clip, stroke=0, fill=0)
    cv.translate(x + s, y + 4 * t); cv.scale(s / 20, -t / 14)
    draw_city(cv, lines=False)
    cv.setFillColor(TOWER); cv.rect(TOWER_C[0] - 1, TOWER_C[1] - 1, 2, 2, stroke=0, fill=1)
    cv.restoreState()
    for (c, r), n in names.items():
        bx, by = x + (c + 1) * s, y + (3 - r) * t
        cv.setStrokeColor(INK); cv.setLineWidth(.8 if not font else 1.4); cv.rect(bx, by, s, t, stroke=1, fill=0)
        cv.setFillColor(INK); cv.setFont('Helvetica-Bold', font or max(5, t * .34))
        cv.drawCentredString(bx + s / 2, by + t * .55 - (font or 0) * .3, n)
    cv.setStrokeColor(INK); cv.setLineWidth(1.6 if font else 1); cv.rect(x + s, y + t, 3 * s, 3 * t, stroke=1, fill=0)


def grid_sheet(cv, name, title=None):
    row = name[0]
    # header
    cv.setFillColor(INK); cv.setFont('Helvetica-Bold', 26)
    cv.drawString(GX, H - 17 * mm, title or f'Our City  ·  Sheet {name}')
    cv.setFont('Helvetica', 12); cv.setFillColor(SOFT)
    t = '1 square = 10 m × 10 m   ·   Write the number of floors inside every building   ·   '
    cv.drawString(GX, H - 24 * mm, t); tx = GX + cv.stringWidth(t, 'Helvetica', 12)
    star(cv, tx + 7, H - 24 * mm + 4, 7, HexColor('#FFD23C')); cv.setFillColor(SOFT); cv.setFont('Helvetica', 12)
    cv.drawString(tx + 17, H - 24 * mm, '= snack shop (give it a name!)')
    if name in RING:
        mini_map5(cv, W - GX - 34 * mm, H - 27 * mm, 34 * mm, here=name)
        cv.setFont('Helvetica', 8); cv.setFillColor(SOFT)
        cv.drawRightString(W - GX - 36 * mm, H - 26 * mm, 'Where your sheet goes:')
    else:
        mini_map(cv, W - GX - 24 * mm, H - 27 * mm, 24 * mm, here=name)
        cv.setFont('Helvetica', 8); cv.setFillColor(SOFT)
        cv.drawRightString(W - GX - 26 * mm, H - 26 * mm, 'Where your sheet goes:')

    # roads + river: one city map, cut into this sheet's piece
    j, i = sheet_pos(name)
    cv.saveState()
    clip = cv.beginPath(); clip.rect(GX, GY, COLS * SQ, ROWS * SQ); cv.clipPath(clip, stroke=0, fill=0)
    cv.translate(GX - j * COLS * SQ, GY + ROWS * SQ + i * ROWS * SQ); cv.scale(SQ, -SQ)
    draw_city(cv)
    cv.restoreState()
    # Start Tower on B2
    if name == 'B2':
        for c in (9, 10):
            for r in (5, 6):
                fill_cell(cv, c, r, TOWER)
        x, y = cell(9, 6); cv.setStrokeColor(INK); cv.setLineWidth(2.5); cv.rect(x, y, 2 * SQ, 2 * SQ, stroke=1, fill=0)
        cv.setFillColor(white); cv.setFont('Helvetica-Bold', 11)
        cv.drawCentredString(x + SQ, y + SQ + 8, 'START'); cv.drawCentredString(x + SQ, y + SQ - 4, 'TOWER')
        cv.setFont('Helvetica-Bold', 9); cv.drawCentredString(x + SQ, y + SQ - 16, '40 floors')
    # grid lines (darker every 5 squares, for counting)
    for c in range(COLS + 1):
        cv.setStrokeColor(GRID5 if c % 5 == 0 else GRID); cv.setLineWidth(1 if c % 5 == 0 else .6)
        cv.line(GX + c * SQ, GY, GX + c * SQ, GY + ROWS * SQ)
    for r in range(ROWS + 1):
        cv.setStrokeColor(GRID5 if r % 5 == 0 else GRID); cv.setLineWidth(1 if r % 5 == 0 else .6)
        cv.line(GX, GY + r * SQ, GX + COLS * SQ, GY + r * SQ)
    # nature labels
    for (lx, ly, txt, size) in LABELS:
        px, py = GX + (lx - j * COLS) * SQ, GY + ROWS * SQ - (ly - i * ROWS) * SQ
        if GX + 10 < px < GX + COLS * SQ - 10 and GY + 10 < py < GY + ROWS * SQ - 10:
            cv.setFont('Helvetica-Bold', size); tw = cv.stringWidth(txt, 'Helvetica-Bold', size)
            cv.setFillColor(HexColor('#FFFFFFCC') if False else white); cv.setStrokeColor(white)
            cv.setFillAlpha(.75); cv.roundRect(px - tw / 2 - 4, py - 3, tw + 8, size + 3, 3, stroke=0, fill=1); cv.setFillAlpha(1)
            cv.setFillColor(HexColor('#3A4A2A')); cv.drawCentredString(px, py, txt)
    cv.setStrokeColor(INK); cv.setLineWidth(2.2); cv.rect(GX, GY, COLS * SQ, ROWS * SQ, stroke=1, fill=0)
    # labels on the edge roads, and square numbers outside the grid
    cv.setFillColor(SOFT); cv.setFont('Helvetica-Bold', 8)
    cv.setFillColor(white); cv.rect(GX + 2, GY + ROWS * SQ - 13, 300, 11, stroke=0, fill=1); cv.setFillColor(SOFT)
    cv.drawString(GX + 5, GY + ROWS * SQ - 10, 'Roads, ponds and streams are already drawn · design around them!')
    # footer
    cv.setFont('Helvetica', 8)
    cv.drawRightString(W - GX, 5 * mm, f'Sheet {name}  ·  Write your first name on the BACK of this sheet  ·  Mr. Romanek’s Grade 4 · Pigeon Pigeon: Our City')


def instructions(cv, ring=False):
    m = 18 * mm
    cv.setFillColor(INK); cv.setFont('Helvetica-Bold', 34)
    cv.drawString(m, H - 26 * mm, 'Design Our City!')
    cv.setFont('Helvetica', 14); cv.setFillColor(SOFT)
    cv.drawString(m, H - 34 * mm, 'Our city is growing! 16 new sheets go all the way around the first city. Design one, we join them like a puzzle, and you fly over it in Pigeon Pigeon!' if ring else
                  'Everyone designs one part of the city. We put the 9 sheets together like a puzzle, and it becomes a 3D city you can fly over in Banpo Pigeon!')

    def box(x, y, w, h, title):
        cv.setFillColor(HexColor('#F7F9FB')); cv.setStrokeColor(INK); cv.setLineWidth(1.5)
        cv.roundRect(x, y, w, h, 10, stroke=1, fill=1)
        cv.setFillColor(INK); cv.setFont('Helvetica-Bold', 16); cv.drawString(x + 12, y + h - 24, title)

    def lines(x, y, items, size=11.5, gap=17, bold_first=False):
        for i, t in enumerate(items):
            cv.setFont('Helvetica-Bold' if bold_first and i == 0 else 'Helvetica', size); cv.setFillColor(INK)
            cv.drawString(x, y - i * gap, t)

    col_w = (W - 2 * m - 2 * 10 * mm) / 3
    top = H - 42 * mm
    # 1. the puzzle
    x1 = m; h1 = 112 * mm
    box(x1, top - h1, col_w, h1, '1. The puzzle')
    if ring:
        mini_map5(cv, x1 + 12, top - 76 * mm, 64 * mm)
        lines(x1 + 16 + 66 * mm, top - 40, ['N = north (top)', 'S = south (bottom)', 'W = west (left)', 'E = east (right)', '', 'The grey middle', 'is the city we', 'already built!', '', 'NEW: Mt. Pigeon,', 'Raccoon Forest, a', 'farm, river + lake!'], 11, 15)
    else:
        mini_map(cv, x1 + 14, top - 82 * mm, 58 * mm)
        lines(x1 + 14 + 62 * mm, top - 40, ['A = top row', 'B = middle row', 'C = bottom row', '', 'Look for ponds', 'and streams!', '', 'B2 has the', 'Start Tower in', 'a roundabout. The', 'pigeon takes off', 'from its roof!'], 11, 15)
    if ring:
        lines(x1 + 14, top - h1 + 34, ['Roads and nature are already printed. Design around them!', 'In nature you may add a cabin, campsite, trail or lookout (max 2 floors).'], 10.5, 14)
    else:
        lines(x1 + 14, top - h1 + 34, ['The ROADS are already printed. They bend and curve and', 'join up from sheet to sheet. Design around them!'], 10.5, 14)
    # 2. size
    x2 = m + col_w + 10 * mm
    box(x2, top - h1, col_w, h1, '2. How big is a square?')
    lines(x2 + 14, top - 44, ['1 square = 10 m × 10 m  (about a classroom)', '1 floor = 3 m tall', '', 'Ideas for sizes:'], 11.5, 17)
    sizes = [('Small house', '1 × 1', '1–3 floors'), ('Shop or café', '1 × 2', '1–4 floors'), ('Apartment', '2 × 3', '10–25 floors'),
             ('School', '4 × 5', '3–5 floors'), ('Skyscraper', '2 × 2', 'up to 39 floors'), ('Soccer field', '6 × 10', 'park (green)'), ('Swimming pool', '2 × 3', 'water (blue)')]
    yy = top - 44 - 4 * 17
    for i, (a, b, c) in enumerate(sizes):
        cv.setFont('Helvetica-Bold', 11); cv.drawString(x2 + 24, yy - i * 16, a)
        cv.setFont('Helvetica', 11); cv.drawString(x2 + 24 + 34 * mm, yy - i * 16, b + ' squares'); cv.drawString(x2 + 24 + 62 * mm, yy - i * 16, c)
    # 3. colours
    x3 = m + 2 * (col_w + 10 * mm)
    box(x3, top - h1, col_w, h1, '3. Colour key')
    key = [(ROAD, ['Roads are already printed! Fit your buildings', 'around them. You can add a small path in grey.']),
           (HexColor('#7BC67E'), ['Park, grass, trees: green.', 'Draw small circles for trees.']),
           (WATER, ['Water: blue. Some ponds and streams are printed;', 'you can add pools or fountains too.']),
           (HexColor('#F28C6B'), ['Building: outline it in black along the lines,', 'then colour it ANY colour you like (red, orange,', 'yellow, pink, purple, brown). That is its 3D colour!']),
           ('num', ['Write the number of FLOORS inside', 'every building, like this.']),
           ('star', ['Snack shop: draw a star and write its name,', 'like "Raccoon Cafe". Up to 4 per sheet.']),
           ('L', ['Landmark: draw it and write L: and its name,', 'like "L: Giant 67 statue". 1 per sheet.'])]
    yy = top - 48
    for sw, txt in key:
        sy = yy - (len(txt) - 1) * 7 - 5
        cv.setStrokeColor(INK); cv.setLineWidth(1)
        if sw == 'num':
            cv.setFillColor(HexColor('#F28C6B')); cv.rect(x3 + 14, sy - 6, 22, 22, stroke=1, fill=1); cv.setFillColor(INK); cv.setFont('Helvetica-Bold', 13); cv.drawCentredString(x3 + 25, sy, '8')
        elif sw == 'star':
            star(cv, x3 + 25, sy + 5, 11, HexColor('#FFD23C'))
        elif sw == 'L':
            cv.setFillColor(white); cv.rect(x3 + 14, sy - 6, 22, 22, stroke=1, fill=1); cv.setFillColor(INK); cv.setFont('Helvetica-Bold', 12); cv.drawCentredString(x3 + 25, sy, 'L')
        else:
            cv.setFillColor(sw); cv.rect(x3 + 14, sy - 6, 22, 22, stroke=1, fill=1)
        cv.setFillColor(INK); cv.setFont('Helvetica', 11)
        for i, t in enumerate(txt): cv.drawString(x3 + 44, yy - i * 14, t)
        yy -= len(txt) * 14 + 10

    # 4. heights chart + 5. rules + 6. checklist
    top2 = top - h1 - 8 * mm; h2 = top2 - 12 * mm
    box(x1, top2 - h2, col_w, h2, '4. Building heights')
    base = top2 - h2 + 26; maxh = h2 - 105; fl = maxh / 40
    bars = [('House', 2, '#F2B880'), ('Shop', 4, '#F28C6B'), ('School', 5, '#F6D55C'), ('Apartment', 20, '#B7A3E0'), ('Skyscraper', 39, '#7FB0E0'), ('Start Tower', 40, '#5B6B7A')]
    bw = (col_w - 40) / len(bars)
    for i, (n, f, c) in enumerate(bars):
        bx = x1 + 22 + i * bw
        cv.setFillColor(HexColor(c)); cv.setStrokeColor(INK); cv.setLineWidth(1)
        cv.rect(bx + 6, base, bw - 14, f * fl, stroke=1, fill=1)
        cv.setFillColor(INK); cv.setFont('Helvetica-Bold', 10); cv.drawCentredString(bx + bw / 2 - 1, base + f * fl + 4, f'{f}')
        cv.setFont('Helvetica', 8.5); cv.drawCentredString(bx + bw / 2 - 1, base - 12, n)
    cv.setFont('Helvetica-Bold', 11); cv.drawString(x1 + 14, top2 - 44, 'Tallest allowed: 39 floors (nothing taller than the Start Tower!)')
    cv.setFont('Helvetica', 11); cv.drawString(x1 + 14, top2 - 60, 'Only ONE building over 20 floors on each sheet.')

    box(x2, top2 - h2, col_w, h2, '5. Rules')
    rules = ['• Use the grid lines: buildings are squares and', '   rectangles (no diagonal or round buildings).',
             '• Biggest building: 6 × 6 squares.',
             '• Every building must touch a road or a park,', '   so people (and pigeons!) can reach it.',
             '• Don’t draw on the printed roads, ponds or', '   streams. Half a square of road = road.',
             '• Leave some open space: parks and plazas', '   make the city fun to fly over.',
             '• Use made-up names for shops and places,', '   not real people’s names.',
             '• Write your first name on the BACK only.']
    lines(x2 + 14, top2 - 46, rules, 11.5, 17)

    box(x3, top2 - h2, col_w, h2, '6. Before you hand it in')
    checks = ['Every building has its number of floors', 'Every building touches a road or a park',
              'I didn’t draw on the printed roads', 'Snack shops have a star and a name (max 4)',
              'Nothing is taller than 39 floors', 'Only one building over 20 floors',
              'My first name is on the back']
    for i, t in enumerate(checks):
        cy = top2 - 50 - i * 24
        cv.setStrokeColor(INK); cv.setLineWidth(1.3); cv.setFillColor(white); cv.rect(x3 + 16, cy - 4, 14, 14, stroke=1, fill=1)
        cv.setFillColor(INK); cv.setFont('Helvetica', 12); cv.drawString(x3 + 40, cy, t)
    cv.setFont('Helvetica-Oblique', 10.5); cv.setFillColor(SOFT)
    cv.drawString(x3 + 14, top2 - h2 + 18, 'Tip: draw lightly in pencil first, then colour it in!')


def design_space():
    """How many squares on each ring sheet are free to design (not road, water, forest, farm or mountain)."""
    def curve(pts, straight=False, n=30):
        out = []
        if straight:
            for a, b in zip(pts, pts[1:]):
                out += [(a[0] + (b[0] - a[0]) * k / (n * 4), a[1] + (b[1] - a[1]) * k / (n * 4)) for k in range(n * 4 + 1)]
            return out
        for i in range(len(pts) - 1):
            p0 = pts[i - 1] if i > 0 else pts[i]; p1 = pts[i]; p2 = pts[i + 1]; p3 = pts[i + 2] if i + 2 < len(pts) else pts[i + 1]
            c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6); c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
            for k in range(n + 1):
                t = k / n; m = 1 - t
                out.append((m ** 3 * p1[0] + 3 * m * m * t * c1[0] + 3 * m * t * t * c2[0] + t ** 3 * p2[0], m ** 3 * p1[1] + 3 * m * m * t * c1[1] + 3 * m * t * t * c2[1] + t ** 3 * p2[1]))
        return out
    segs = [(w / 2 + .1, curve(pts, 'straight' in f)) for w, pts, *f in ROADS + RING_ROADS] + [(STREAM_W / 2 + .1, curve(st)) for st in STREAMS + RING_STREAMS] + [(RIVER_W / 2 + .1, curve(RIVER))]
    lx, ly, rx, ry = LAKE
    def blocked(x, y):
        if inside(FOREST, x, y) or inside(FARM, x, y) or inside(MOUNTAIN[0][0], x, y): return True
        if ((x - lx) / (rx + 2.2)) ** 2 + ((y - ly) / (ry + 2.2)) ** 2 < 1: return True
        for (px, py, prx, pry) in PONDS + RING_PONDS:
            if ((x - px) / (prx + .7)) ** 2 + ((y - py) / (pry + .7)) ** 2 < 1: return True
        for hw, pts in segs:
            for (px, py) in pts:
                if abs(px - x) < hw and abs(py - y) < hw and _m.hypot(px - x, py - y) < hw: return True
        return False
    out = {}
    for n, (j, i) in RING.items():
        out[n] = sum(1 for r in range(14) for c in range(20)
                     if not any(blocked(j * 20 + c + a, i * 14 + r + b) for a, b in ((.5, .5), (.15, .15), (.85, .15), (.15, .85), (.85, .85))))
    return out


def overview(cv):
    """Teacher page: the whole 5 x 5 puzzle with every sheet's name."""
    cv.setFillColor(INK); cv.setFont('Helvetica-Bold', 30); cv.drawString(18 * mm, H - 24 * mm, 'Our City: the big puzzle (25 sheets)')
    cv.setFont('Helvetica', 13); cv.setFillColor(SOFT)
    cv.drawString(18 * mm, H - 32 * mm, 'Faded = the first 9 sheets (already done). The 16 ring sheets around them show how much room each has to design. Roads join up across every edge.')
    size = min(W - 80 * mm, (H - 96 * mm) * 100 / 70)
    x0, y0 = (W - size) / 2, 24 * mm
    pad = 7   # squares of countryside shown around the city
    k = size / 100
    cv.saveState()
    clip = cv.beginPath(); clip.rect(x0 - pad * k, y0 - pad * k, size + 2 * pad * k, size * .7 + 2 * pad * k); cv.clipPath(clip, stroke=0, fill=0)
    cv.setFillColor(HexColor('#EEF3E6')); cv.rect(x0 - pad * k, y0 - pad * k, size + 2 * pad * k, size * .7 + 2 * pad * k, stroke=0, fill=1)
    cv.translate(x0 + 20 * k, y0 + size * .7 - 14 * k); cv.scale(k, -k)
    draw_city(cv, lines=False)
    cv.restoreState()
    mini_map5(cv, x0, y0, size, font=22, ghost=True)
    free = design_space()
    s5, t5 = size / 5, size * .7 / 5
    for n, (c, r) in RING.items():
        bx, by = x0 + (c + 1) * s5, y0 + (3 - r) * t5
        txt = f'{free[n]} squares to design' if free[n] >= 60 else ('Nature sheet' if free[n] < 25 else f'{free[n]} squares · mostly nature')
        cv.setFont('Helvetica-Bold', 10); tw = cv.stringWidth(txt, 'Helvetica-Bold', 10)
        cv.setFillColor(white); cv.setFillAlpha(.85); cv.roundRect(bx + s5 / 2 - tw / 2 - 4, by + t5 * .55 - 30, tw + 8, 14, 3, stroke=0, fill=1); cv.setFillAlpha(1)
        cv.setFillColor(HexColor('#2E6B3A') if free[n] < 60 else INK); cv.drawCentredString(bx + s5 / 2, by + t5 * .55 - 26, txt)
    print('design space:', free)
    cv.setFont('Helvetica-Oblique', 11); cv.setFillColor(SOFT)
    cv.drawCentredString(W / 2, y0 - pad * k - 14, 'The mountain, forest, farm and lake carry on past the edge of the city, like real countryside.')


import sys
if '--ring' in sys.argv:
    cv = canvas.Canvas('Our_City_ring_sheets.pdf', pagesize=landscape(A3))
    cv.setTitle('Our City: the ring (16 more sheets)'); cv.setAuthor('Mr. Romanek')
    instructions(cv, ring=True); cv.showPage()
    overview(cv); cv.showPage()
    for n in RING:
        grid_sheet(cv, n); cv.showPage()
    cv.save()
else:
    cv = canvas.Canvas('Our_City_design_sheets.pdf', pagesize=landscape(A3))
    cv.setTitle('Our City: design sheets'); cv.setAuthor('Mr. Romanek')
    instructions(cv); cv.showPage()
    for n in SHEETS:
        grid_sheet(cv, n); cv.showPage()
    cv.save()
print('ok')
