import os, math, urllib.request
import pyarrow.parquet as pq
import pyarrow.compute as pc
import geo

layers = ["building", "segment", "land_use", "land", "infrastructure", "water", "address"]

def tile(lon, lat, z=14):
    n = 2 ** z
    return int((lon + 180) / 360 * n), int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)

for c in sorted(geo.CHUNKS):
    D = "data" if c == (0, 0) else f"data_c{c[0]}_{c[1]}"
    os.makedirs(f"{D}/dem", exist_ok=True)
    cx, cy = geo.chunk_center(c)
    r = geo.HALF + 300
    (x0, x1), (y0, y1) = geo.to_lonlat([cx-r, cx+r], [cy-r, cy+r])
    x0, x1, y0, y1 = map(float, (x0, x1, y0, y1))

    for typ in layers:
        src = f"data_all/{typ}.parquet"
        tb = pq.read_table(src)
        b = tb.column("bbox").combine_chunks()
        m = pc.and_(pc.and_(pc.less(b.field("xmin"), x1), pc.greater(b.field("xmax"), x0)),
                    pc.and_(pc.less(b.field("ymin"), y1), pc.greater(b.field("ymax"), y0)))
        out = tb.filter(m)
        pq.write_table(out, f"{D}/{typ}.parquet")
        print(D, typ, out.num_rows, flush=True)

    tx0, ty0 = tile(x0, y1)
    tx1, ty1 = tile(x1, y0)
    for x in range(tx0, tx1+1):
        for y in range(ty0, ty1+1):
            p = f"{D}/dem/14_{x}_{y}.png"
            if not os.path.exists(p):
                url = f"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/14/{x}/{y}.png"
                urllib.request.urlretrieve(url, p)
    print("Hotový štvorec:", c, flush=True)

print("Všetkých päť štvorcov je pripravených.")
