# (c) 2018 Erik Bosman
# License: https://opensource.org/licenses/MIT

import svgpath, simplefy, sys, math, cmath

mapping = {

    "front_mask"   : "F.Mask",
    "front_silk"   : "F.SilkS",
    "front_paste"  : "F.Paste",
    "front_copper" : "F.Cu",

    "back_mask"    : "B.Mask",
    "back_silk"    : "B.SilkS",
    "back_copper"  : "B.Cu",
    "back_paste"   : "B.Paste",

    "edges"        : "Edge.Cuts",
}

scale = 1000000

def num_fmt(n):
    n = float(n)/scale
    return "{:.6f}".format(n)

def coord_fmt( coords ):
    x, y = coords
    return num_fmt(x)+' '+num_fmt(y)

def phase_fmt( t ):
    return "{:.6f}".format( (math.degrees(t))%360)

def pad_grid(coords, w, h, pitch):
    x, y = coords
    return [ (x+pitch*i, y+pitch*j) for i in range(w) for j in range(h) ]

def print_pad(f, coords, size, drill):
    print("(pad 1 thru_hole circle (at {:s}) (size {:s}) (drill {:s}) (layers *.Cu *.Mask) )".format(coord_fmt(coords), coord_fmt((size,size)), num_fmt(drill)), file=f)
#    print("(pad 1 thru_hole circle (at {:s}) (size {:s}) (drill {:s}) (layers *.Cu *.Mask F.SilkS) (zone_connect 2))".format(coord_fmt(coords), coord_fmt((size,size)), num_fmt(drill)), file=f)

def d(a, b):
    ax, ay = a
    bx, by = b
    return math.sqrt( (ax-bx)**2 + (ay-by)**2 )

def mid(a,b):
    ax, ay = a
    bx, by = b
    return ( (ax+bx)/2, (ay+by)/2 )

def phase(a, b):
    ax, ay = a
    bx, by = b
    return cmath.phase( complex(-(bx-ax), by-ay) )

def print_slot(f, a, b, size, drill):
    pos = mid(a,b)
    rotate = phase(a,b)
    drill_size = ( d(a,b)+drill, drill )
    copper_size = ( d(a,b)+size, size )
    print("(pad S1 thru_hole oval (at {:s} {:s}) (size {:s}) (drill oval {:s}) (layers *.Cu *.Mask) )".format(coord_fmt(pos), phase_fmt(rotate), coord_fmt(copper_size), coord_fmt(drill_size)), file=f)

def print_via(f, coords, size, drill):
    print("(pad 1 thru_hole circle (at {:s}) (size {:s}) (drill {:s}) (layers *.Cu))".format(coord_fmt(coords), coord_fmt((size,size)), num_fmt(drill)), file=f)

def print_hole(f, coords, drill):
    print("(pad \"\" np_thru_hole circle (at {:s}) (size {:s}) (drill {:s}) (layers *.Cu))".format(coord_fmt(coords), coord_fmt((drill,drill)), num_fmt(drill)), file=f)

def print_polygon(f, polygon, layer):
    print('(fp_poly (pts '+'\n'.join('(xy '+coord_fmt(point)+')' for point in polygon),file=f)
    print(') (layer '+layer+') (width 0.000001))', file=f)

def print_segments(f, polygon, layer, width):
    for from_, to in zip(polygon[:-1], polygon[1:]):
        print("(fp_line (start {:s}) (end {:s}) (layer {:s}) (width {:s}))".format( coord_fmt(from_), coord_fmt(to), layer, num_fmt(width)) , file=f)

def print_zone(f, polygon):
    print('\n'.join('(xy '+coord_fmt(point)+')' for point in polygon), file=f)

def roundint(x):
    return int(round(x))

esc_map = {
    '\"':'\\"',
    '\t':'\\t',
    '\n':'\\n',
    '\r':'\\r',
}

def escape_map(c):
    if c in esc_map:
        return esc_map[c]
    else:
        return c

def str_escape(s):
    return '"'+''.join(escape_map(c) for c in s)+'"'

def print_module(f, name, fill_paths, segment_paths, pads, vias, holes, slots):

    print ("""(module """+str_escape(name)+""" (layer F.Cu) (tedit 0)
  (fp_text reference "" (at 0 0) (layer F.SilkS)
    (effects (font (thickness 0.15)))
  )
  (fp_text value "" (at 0 0) (layer F.SilkS)
    (effects (font (thickness 0.15)))
  )""", file=f)

    for layer, polygons in fill_paths:
        print("Layer: ", layer, file=sys.stderr)
        polygons = svgpath.rescale_polygon_list(polygons, scale, conv=roundint)
        polygons = simplefy.weakly_simplefy(polygons)

        for p in polygons:
            if p[0] != p[-1]:
                p = p + [p[0]]
                print("warning polygon not closed ", file=sys.stderr)
            if len(p) > 3:
                print_polygon(f, p, mapping[layer])
                print("polygon ", p, file=sys.stderr)
            else:
                print("polygon to small, ingoring, ", p, file=sys.stderr)

    for layer, polygons, width in segment_paths:
        polygons = svgpath.rescale_polygon_list(polygons, scale, conv=roundint)
        for p in polygons:
            print_segments(f, p, mapping[layer], width*scale)

    for x, y, size, drill in pads:
        print_pad(f, svgpath.rescale_point((x,y), scale, conv=roundint), scale*size, scale*drill)

    for x, y, size, drill in vias:
        print_via(f, svgpath.rescale_point((x,y), scale, conv=roundint), scale*size, scale*drill)

    for x, y, drill in holes:
        print_hole(f, svgpath.rescale_point((x,y), scale, conv=roundint), scale*drill)

    for polygons, size, drill in slots:
        polygons = svgpath.rescale_polygon_list(polygons, scale, conv=roundint)
        for p in polygons:
            for a, b in zip(p[:-1], p[1:]):
                print_slot(f, a, b, size*scale, drill*scale)

    print(")", file=f)

def print_zones(f, zone_paths):

    for polygons in zone_paths:
        polygons = svgpath.rescale_polygon_list(polygons, scale, conv=roundint)
        polygons = simplefy.weakly_simplefy(polygons)
        for p in polygons:
            print_zone(f, p)

