# (c) 2018 Erik Bosman
# License: https://opensource.org/licenses/MIT

import svgpath, simplefy, sys, math, cmath

scale = 1000000

def num_fmt(n):
    n = float(n)/scale
    return "{:.6f}".format(n)

def coord_fmt( coords ):
    x, y = coords
    return '['+num_fmt(x)+', '+num_fmt(y)+']'

def phase_fmt( t ):
    return "{:.6f}".format( (math.degrees(t))%360)

def pad_grid(coords, w, h, pitch):
    x, y = coords
    return [ (x+pitch*i, y+pitch*j) for i in range(w) for j in range(h) ]

def print_pad(f, coords, size, drill):
    print("// pad at {:s} size {:s} drill {:s}".format(coord_fmt(coords), coord_fmt((size,size)), num_fmt(drill)), file=f)
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
    print("// slot at {:s} rotated {:s} degrees size {:s} drill {:s}".format(coord_fmt(pos), phase_fmt(rotate), coord_fmt(copper_size), coord_fmt(drill_size)), file=f)

def print_circle(f, coords, drill):
    print("\t\ttranslate({:s}) circle(r={:s});".format(coord_fmt(coords), num_fmt(drill/2)), file=f)

def print_polygon(f, polygon, layer):
    points = polygon['outline']
    paths = [list(range(len(points)))]
    for p in polygon['cutouts']:
        paths += [ list(range(len(points),len(points)+len(p))) ]
        points += p
    print('\t\tpolygon(points=[{}],\n\t\t        paths=[{}]);'.format(','.join(coord_fmt(p) for p in points), ','.join('['+','.join(str(x) for x in  path)+']' for path in paths) ), file=f)

def print_segments(f, polygon, layer, width):
    print('\t\t' + ','.join(coord_fmt(p) for p in polygon), file=f)

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

    layers = ["front_mask", "front_silk", "front_paste", "front_copper", "back_mask", "back_silk", "back_copper", "back_paste", "edges"]

    for p in (fill_paths, segment_paths):
        for x in p:
            assert x[0] in layers
 
    for layer in layers:
        print("module {}_{}()".format(name, layer), file=f)
        print("{", file=f)
        print("\tunion()", file=f)
        print("\t{", file=f)

        for polygons in (p for l,p in fill_paths if layer == l):
            polygons = svgpath.rescale_polygon_list(polygons, scale, flipY=True, conv=roundint)
            polygons = simplefy.separate_cutouts(polygons)
            for p in polygons:
                print (layer,file = sys.stderr)
                print (p,file = sys.stderr)
                print_polygon(f, p, layer)

        print("\t};", file=f)
        print("};", file=f)

#        for polygons, width in (p,w for l,p,w segment_paths if layer == l):
#            print("layer_"+layer+"_segments = [\n\t[", file=f)
#            polygons = svgpath.rescale_polygon_list(polygons, scale, flipY=True, conv=roundint)
#            first=True
#            for p in polygons:
#                if not first:
#                    print("\t],[", file=f)
#                first=False
#                print_segments(f, p, mapping[layer], width*scale)
#            print("\t]", file=f)
#            print("];", file=f)
#            print(file=f)

    print("module {}_holes()".format(name, layer), file=f)
    print("{", file=f)
    print("\tunion()", file=f)
    print("\t{", file=f)

    for x, y, size, drill in pads:
        print("// pads", file=f)
        print_circle(f, svgpath.rescale_point((x,y), scale, flipY=True, conv=roundint), scale*drill)

    for x, y, size, drill in vias:
        print("// vias", file=f)
        print_circle(f, svgpath.rescale_point((x,y), scale, flipY=True, conv=roundint), scale*drill)

    for x, y, drill in holes:
        print("// holes", file=f)
        print_circle(f, svgpath.rescale_point((x,y), scale, flipY=True, conv=roundint), scale*drill)

    print("\t};", file=f)
    print("};", file=f)


    print("module {}_rings()".format(name, layer), file=f)
    print("{", file=f)
    print("\tunion()", file=f)
    print("\t{", file=f)

    for x, y, size, drill in pads:
        print("// pads", file=f)
        print_circle(f, svgpath.rescale_point((x,y), scale, flipY=True, conv=roundint), scale*size)

    for x, y, size, drill in vias:
        print("// vias", file=f)
        print_circle(f, svgpath.rescale_point((x,y), scale, flipY=True, conv=roundint), scale*size)

    print("\t};", file=f)
    print("};", file=f)

    for polygons, size, drill in slots:
        polygons = svgpath.rescale_polygon_list(polygons, scale, flipY=True, conv=roundint)
        for p in polygons:
            for a, b in zip(p[:-1], p[1:]):
                print_slot(f, a, b, size*scale, drill*scale)

