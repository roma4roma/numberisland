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
SHEETS = [r + c for r in 'ABC' for c in '123']   # A = top row of the city, C = bottom (river)


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


def mini_map(cv, x, y, size, here=None):
    """3x3 locator: rows A (top) to C (bottom), river on row C, tower on B2."""
    s = size / 3
    for i, name in enumerate(SHEETS):
        r, c = i // 3, i % 3
        bx, by = x + c * s, y + (2 - r) * s
        cv.setFillColor(HexColor('#FFE08A') if name == here else white)
        cv.setStrokeColor(INK); cv.setLineWidth(1.2)
        cv.rect(bx, by, s, s, stroke=1, fill=1)
        if name[0] == 'C':
            cv.setFillColor(WATER); cv.rect(bx + 1, by + s * .18, s - 2, s * .22, stroke=0, fill=1)
        if name == 'B2':
            cv.setFillColor(TOWER); cv.rect(bx + s * .72, by + s * .1, s * .18, s * .18, stroke=0, fill=1)
        cv.setFillColor(INK); cv.setFont('Helvetica-Bold', max(7, s * .28))
        cv.drawCentredString(bx + s / 2, by + s * .55, name)


def grid_sheet(cv, name):
    row = name[0]
    # header
    cv.setFillColor(INK); cv.setFont('Helvetica-Bold', 26)
    cv.drawString(GX, H - 17 * mm, f'Our City  ·  Sheet {name}')
    cv.setFont('Helvetica', 12); cv.setFillColor(SOFT)
    t = '1 square = 10 m × 10 m   ·   Write the number of floors inside every building   ·   '
    cv.drawString(GX, H - 24 * mm, t); tx = GX + cv.stringWidth(t, 'Helvetica', 12)
    star(cv, tx + 7, H - 24 * mm + 4, 7, HexColor('#FFD23C')); cv.setFillColor(SOFT); cv.setFont('Helvetica', 12)
    cv.drawString(tx + 17, H - 24 * mm, '= snack shop (give it a name!)')
    mini_map(cv, W - GX - 24 * mm, H - 27 * mm, 24 * mm, here=name)
    cv.setFont('Helvetica', 8); cv.setFillColor(SOFT)
    cv.drawRightString(W - GX - 26 * mm, H - 26 * mm, 'Where your sheet goes:')

    # river first (rows 9-11) on the bottom row of sheets
    if row == 'C':
        for r in RIVER_ROWS:
            for c in range(COLS):
                fill_cell(cv, c, r, WATER)
        x0, y0 = cell(0, RIVER_ROWS[-1]); cv.setStrokeColor(WATER_D); cv.setLineWidth(1.5)
        for k in range(1, 7):  # little waves
            wy = y0 + k * (3 * SQ) / 7
            for c in range(2, COLS - 2, 3):
                wx = GX + c * SQ
                p = cv.beginPath(); p.moveTo(wx, wy); p.curveTo(wx + SQ * .3, wy + 5, wx + SQ * .7, wy - 5, wx + SQ, wy); cv.drawPath(p, stroke=1, fill=0)
    # edge roads on all four sides
    for c in range(COLS):
        fill_cell(cv, c, 0, ROAD); fill_cell(cv, c, ROWS - 1, ROAD)
    for r in range(ROWS):
        fill_cell(cv, 0, r, ROAD); fill_cell(cv, COLS - 1, r, ROAD)
    if row == 'C':  # bridges where the side roads cross the river
        for c in (0, COLS - 1):
            for r in RIVER_ROWS:
                fill_cell(cv, c, r, ROAD)
            x, y = cell(c, RIVER_ROWS[-1]); cv.setFillColor(BRIDGE)
            cv.rect(x - .5, y, 3, 3 * SQ, stroke=0, fill=1); cv.rect(x + SQ - 2.5, y, 3, 3 * SQ, stroke=0, fill=1)
            cv.setFillColor(INK); cv.setFont('Helvetica-Bold', 8)
            cv.saveState(); cv.translate(x + SQ / 2 + 3, y + 1.5 * SQ); cv.rotate(90); cv.drawCentredString(0, 0, 'BRIDGE'); cv.restoreState()
    # dashed centre lines on the edge roads
    cv.setStrokeColor(ROAD_LINE); cv.setLineWidth(2); cv.setDash(6, 5)
    cv.line(GX, GY + (ROWS - .5) * SQ, GX + COLS * SQ, GY + (ROWS - .5) * SQ)
    cv.line(GX, GY + .5 * SQ, GX + COLS * SQ, GY + .5 * SQ)
    cv.line(GX + .5 * SQ, GY, GX + .5 * SQ, GY + ROWS * SQ)
    cv.line(GX + (COLS - .5) * SQ, GY, GX + (COLS - .5) * SQ, GY + ROWS * SQ)
    cv.setDash()
    # Start Tower on B2
    if name == 'B2':
        for c in (9, 10):
            for r in (6, 7):
                fill_cell(cv, c, r, TOWER)
        x, y = cell(9, 7); cv.setStrokeColor(INK); cv.setLineWidth(2.5); cv.rect(x, y, 2 * SQ, 2 * SQ, stroke=1, fill=0)
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
    cv.setStrokeColor(INK); cv.setLineWidth(2.2); cv.rect(GX, GY, COLS * SQ, ROWS * SQ, stroke=1, fill=0)
    # labels on the edge roads, and square numbers outside the grid
    cv.setFillColor(SOFT); cv.setFont('Helvetica-Bold', 8)
    for txt, x, y in [('EDGE ROAD · already done, don’t draw here', GX + 3 * SQ, GY + (ROWS - 1) * SQ + 6),
                      ('EDGE ROAD · join your roads to it', GX + 3 * SQ, GY + 6)]:
        cv.drawString(x, y, txt)
    # footer
    cv.setFont('Helvetica', 8)
    cv.drawRightString(W - GX, 5 * mm, f'Sheet {name}  ·  Write your first name on the BACK of this sheet  ·  Mr. Romanek’s Grade 4 · Banpo Pigeon: Our City')


def instructions(cv):
    m = 18 * mm
    cv.setFillColor(INK); cv.setFont('Helvetica-Bold', 34)
    cv.drawString(m, H - 26 * mm, 'Design Our City!')
    cv.setFont('Helvetica', 14); cv.setFillColor(SOFT)
    cv.drawString(m, H - 34 * mm, 'Everyone designs one part of the city. We put the 9 sheets together like a puzzle, and it becomes a 3D city you can fly over in Banpo Pigeon!')

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
    mini_map(cv, x1 + 14, top - 82 * mm, 58 * mm)
    lines(x1 + 14 + 62 * mm, top - 40, ['A = top row', 'B = middle row', 'C = bottom row', '', 'Row C has the', 'river and bridges.', '', 'B2 has the', 'Start Tower.', 'The pigeon takes', 'off from its roof!'], 11, 15)
    lines(x1 + 14, top - h1 + 34, ['Every sheet has an EDGE ROAD all around it,', 'so all the streets join up when we put them together.'], 10.5, 14)
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
    key = [(ROAD, ['Road: grey pencil, at least 1 square wide.', 'Every road must join an edge road.']),
           (HexColor('#7BC67E'), ['Park, grass, trees: green.', 'Draw small circles for trees.']),
           (WATER, ['Water: blue. Ponds, pools, fountains.']),
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
             '• Don’t draw on the grey EDGE ROADS,', '   the river or the bridges.',
             '• Leave some open space: parks and plazas', '   make the city fun to fly over.',
             '• Use made-up names for shops and places,', '   not real people’s names.',
             '• Write your first name on the BACK only.']
    lines(x2 + 14, top2 - 46, rules, 11.5, 17)

    box(x3, top2 - h2, col_w, h2, '6. Before you hand it in')
    checks = ['Every building has its number of floors', 'Every building touches a road or a park',
              'My roads join the edge roads', 'Snack shops have a star and a name (max 4)',
              'Nothing is taller than 39 floors', 'Only one building over 20 floors',
              'My first name is on the back']
    for i, t in enumerate(checks):
        cy = top2 - 50 - i * 24
        cv.setStrokeColor(INK); cv.setLineWidth(1.3); cv.setFillColor(white); cv.rect(x3 + 16, cy - 4, 14, 14, stroke=1, fill=1)
        cv.setFillColor(INK); cv.setFont('Helvetica', 12); cv.drawString(x3 + 40, cy, t)
    cv.setFont('Helvetica-Oblique', 10.5); cv.setFillColor(SOFT)
    cv.drawString(x3 + 14, top2 - h2 + 18, 'Tip: draw lightly in pencil first, then colour it in!')


cv = canvas.Canvas('Our_City_design_sheets.pdf', pagesize=landscape(A3))
cv.setTitle('Our City: design sheets'); cv.setAuthor('Mr. Romanek')
instructions(cv); cv.showPage()
for n in SHEETS:
    grid_sheet(cv, n); cv.showPage()
cv.save()
print('ok')
