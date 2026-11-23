"""One filled-in EXAMPLE sheet (uses sheet A1's roads) to show the class."""
src = open('make_city_sheets.py').read(); src = src[:src.index("cv = canvas.Canvas(")]
ns = {}; exec(src, ns); globals().update(ns)
from freemap import free
g = free('A1')
B = [  # col, row, w, h, colour, floors, name/label, kind
    (2, 2, 2, 2, '#F6A04D', 3, 'Raccoon Cafe', 'shop'),
    (5, 2, 3, 2, '#B7A3E0', 12, 'Apartments', 'bld'),
    (9, 2, 2, 1, '#F7A8C4', 2, 'House', 'bld'),
    (12, 2, 4, 2, None, 0, 'Park', 'park'),
    (10, 4, 3, 2, '#7FB0E0', 18, 'Office', 'bld'),
    (2, 7, 3, 1, '#F6D55C', 2, 'Sunny Bakery', 'shop'),
    (7, 8, 2, 1, None, 0, 'Pool', 'water'),
    (2, 9, 4, 3, '#F6D55C', 4, 'School', 'bld'),
    (7, 10, 4, 3, None, 0, 'Park', 'park'),
    (2, 13, 2, 1, '#F7A8C4', 2, '', 'bld'),
    (5, 13, 2, 1, '#F2B880', 3, '', 'bld'),
    (17, 8, 2, 2, '#5FA8E8', 32, 'Sky Tower', 'bld'),
    (19, 11, 1, 1, '#FFFFFF', 0, 'L: Giant 67 statue', 'landmark'),
    (13, 13, 3, 1, '#E8583C', 2, 'Ramyeon King', 'shop'),
]
for c, r, w, h, *_ in B:
    for cc in range(c, c + w):
        for rr in range(r, r + h):
            assert g[rr][cc], f'not free: {(cc, rr)} for {(c, r, w, h)}'
cv = canvas.Canvas('Our_City_EXAMPLE.pdf', pagesize=landscape(A3)); cv.setTitle('Our City: example sheet')
grid_sheet(cv, 'A1', title='EXAMPLE sheet  ·  how a finished sheet could look')
for c, r, w, h, col, fl, name, kind in B:
    x, y = cell(c, r + h - 1); bw, bh = w * SQ, h * SQ
    if kind == 'park':
        cv.setFillColor(HexColor('#7BC67E')); cv.setStrokeColor(HexColor('#2E7D32')); cv.setLineWidth(1.2); cv.rect(x, y, bw, bh, stroke=1, fill=1)
        import random; random.seed(c * 31 + r)
        for k in range(w * h * 2):
            tx, ty = x + 8 + random.random() * (bw - 16), y + 8 + random.random() * (bh - 16)
            cv.setFillColor(HexColor('#2E8B3A')); cv.circle(tx, ty, 6, stroke=0, fill=1)
        cv.setFillColor(HexColor('#1B5E20')); cv.setFont('Helvetica-Bold', 11); cv.drawCentredString(x + bw / 2, y + bh / 2 - 4, name)
        continue
    if kind == 'water':
        cv.setFillColor(WATER); cv.setStrokeColor(WATER_D); cv.setLineWidth(1.2); cv.rect(x, y, bw, bh, stroke=1, fill=1)
        cv.setFillColor(HexColor('#0D4F8B')); cv.setFont('Helvetica-Bold', 10); cv.drawCentredString(x + bw / 2, y + bh / 2 - 4, name); continue
    cv.setFillColor(HexColor(col)); cv.setStrokeColor(INK); cv.setLineWidth(2.4); cv.rect(x, y, bw, bh, stroke=1, fill=1)
    cv.setFillColor(INK)
    if kind == 'landmark':
        cv.setFont('Helvetica-Bold', 16); cv.drawCentredString(x + bw / 2, y + bh / 2 - 6, 'L')
    else:
        cv.setFont('Helvetica-Bold', 20 if max(w, h) > 1 else 15); cv.drawCentredString(x + bw / 2, y + bh / 2 - 7, str(fl))
    if kind == 'shop': star(cv, x + bw - 9, y + bh - 9, 8, HexColor('#FFD23C'))
    if name and kind in ('shop', 'landmark') or name in ('School', 'Sky Tower', 'Apartments', 'Office'):
        cv.setFont('Helvetica-Bold', 10); tw = cv.stringWidth(name, 'Helvetica-Bold', 10)
        lx, ly = x + bw / 2 - tw / 2, y - 12
        if kind == 'landmark': lx, ly = x - tw - 6, y + bh / 2 - 4
        if r + h >= 14: ly = y + bh + 4  # bottom row: label above
        cv.setFillColor(white); cv.rect(lx - 3, ly - 3, tw + 6, 13, stroke=0, fill=1); cv.setFillColor(INK); cv.drawString(lx, ly, name)
# callout notes in the margins
cv.setFillColor(white); cv.rect(0, 0, W, GY - 1, stroke=0, fill=1)   # replace the normal footer
cv.setFont('Helvetica-Bold', 11.5); cv.setFillColor(HexColor('#C9302C'))
cv.drawString(GX, 5.5 * mm, 'Just an example: make YOUR sheet your own!   Numbers = floors  ·  Star + name = snack shop  ·  Green + circles = park & trees  ·  L = landmark  ·  Only ONE building over 20 floors')
cv.showPage(); cv.save(); print('ok')
