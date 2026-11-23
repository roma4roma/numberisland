import math, importlib.util, sys
spec=importlib.util.spec_from_file_location('m','make_city_sheets.py')
src=open('make_city_sheets.py').read()
src=src[:src.index("cv = canvas.Canvas(")]
ns={}; exec(src, ns)
def curve(pts, straight=False, n=40):
    out=[]
    if straight:
        for a,b in zip(pts,pts[1:]):
            for k in range(n+1): out.append((a[0]+(b[0]-a[0])*k/n, a[1]+(b[1]-a[1])*k/n))
        return out
    for i in range(len(pts)-1):
        p0=pts[i-1] if i>0 else pts[i]; p1=pts[i]; p2=pts[i+1]; p3=pts[i+2] if i+2<len(pts) else pts[i+1]
        c1=(p1[0]+(p2[0]-p0[0])/6, p1[1]+(p2[1]-p0[1])/6); c2=(p2[0]-(p3[0]-p1[0])/6, p2[1]-(p3[1]-p1[1])/6)
        for k in range(n+1):
            t=k/n; mt=1-t
            out.append((mt**3*p1[0]+3*mt*mt*t*c1[0]+3*mt*t*t*c2[0]+t**3*p2[0], mt**3*p1[1]+3*mt*mt*t*c1[1]+3*mt*t*t*c2[1]+t**3*p2[1]))
    return out
segs=[(w/2+.15, curve(pts, 'straight' in f)) for w,pts,*f in ns['ROADS']]
segs+=[(ns['STREAM_W']/2+.15, curve(st)) for st in ns['STREAMS']]
TC=ns['TOWER_C']; RR=ns['ROUNDABOUT_R']
def blocked(x,y):
    for hw,pts in segs:
        for (px,py) in pts:
            if abs(px-x)<hw+1 and abs(py-y)<hw+1 and math.hypot(px-x,py-y)<hw: return True
    for (px,py,rx,ry) in ns['PONDS']:
        if ((x-px)/(rx+.75))**2+((y-py)/(ry+.75))**2<1: return True
    if math.hypot(x-TC[0],y-TC[1])<RR+ns['MAIN']/2+.1: return True
    return False
def free(sheet):
    i='ABC'.index(sheet[0]); j=int(sheet[1])-1
    g=[]
    for r in range(14):
        row=[]
        for c in range(20):
            x0=j*20+c; y0=i*14+r
            pts=[(x0+a,y0+b) for a in (.1,.5,.9) for b in (.1,.5,.9)]
            row.append(not any(blocked(x,y) for x,y in pts))
        g.append(row)
    return g
if __name__=='__main__':
    g=free(sys.argv[1])
    print('   '+''.join(str(c%10) for c in range(20)))
    for r,row in enumerate(g): print(f'{r:2d} '+''.join('.' if f else '#' for f in row))
