# (c) 2018 Erik Bosman
# License: https://opensource.org/licenses/MIT

import sys, math, itertools

cubic_sections = 32

def roundint(x):
    return int(round(x))

def dist(a, b):
    ax, ay = a
    bx, by = b
    return math.sqrt((ax-bx)**2 + (ay-by)**2)

def interpolate(pos1, pos2, d):
    x1, y1 = pos1
    x2, y2 = pos2
    return ( x1*(1-d) + x2*d, y1*(1-d) + y2*d )

def vector_add(a, b):
    return tuple( i+j for i, j in zip(a,b) )

def vector_sub(a, b):
    return tuple( i-j for i, j in zip(a,b) )

def scalar_div(a, d):
    return tuple( i/d for i in a )

def cubic_spline( start, guide1, guide2, end, scale ):
    n = min(int(dist(start, end)*scale*25.)+1, cubic_sections)

    v = []
    for i in range(1, n):
        d = i/float(n)
        a = interpolate(start, guide1, d)
        b = interpolate(guide1, guide2, d)
        c = interpolate(guide2, end, d)

        ab = interpolate(a, b, d)
        bc = interpolate(b, c, d)
        abc = interpolate(ab, bc, d)
        v.append(abc)

    v.append(end)
    return v

def quadratic_spline( start, guide, end, scale ):
    n = min(int(dist(start, end)*scale*25.)+1, cubic_sections)

    v = []
    for i in range(1, n):
        d = i/float(n)
        a = interpolate(start, guide, d)
        b = interpolate(guide, end, d)

        ab = interpolate(a, b, d)
        v.append(ab)

    v.append(end)
    return v

def arc_spline(start, end, rx, ry, rot, large_arc, sweep):
    rx, ry = abs(rx), abs(ry)
    if rx == 0. or ry == 0.:
        return [ end ]
    # https://www.w3.org/TR/SVG/implnote.html#ArcImplementationNotes
    sin_t, cos_t = math.sin(math.radians(rot)), math.cos(math.radians(rot))
    mid = scalar_div(vector_add(start, end), 2)
    px, py = vector_sub(start, mid)
    px, py = (cos_t*px - sin_t*py, sin_t*px + cos_t*py)
    coeff = math.sqrt( (rx*rx*ry*ry) / (rx*rx*py*py + px*px*ry*ry) - 1 )
    if large_arc == sweep:
        coeff = -coeff

    cx_prime, cy_prime = py * rx/ry, -px * ry/rx
    c = (cos_t*cx_prime + sin_t*cy_prime, sin_t*cx_prime - cos_t*cy_prime)
    c = vector_add(c, mid)
    v = []
    sys.stderr.write("ERROR: arc\n")
    sys.exit(1)
    v.append(end)
    return v

def get_coords(s):
    return [float(x) for x in s]

def pol_debug( p ):
    minx = min(x for x, y in p)
    maxx = max(x for x, y in p)
    miny = min(y for x, y in p)
    maxy = max(y for x, y in p)
    bbsz = (maxx-minx)*(maxy-miny)
    if bbsz < .3:
        print ( len(p), bbsz, p, file=sys.stderr )

def path_to_polygons(data, scale=1.):

    values = (x for x in data.replace(',', ' ').replace('\n',' ').split(' ') if x != '' )

    mode = 'z'
    cubic_ctrl = quad_ctrl = pos = (0.,0.)

    polygons = []
    p = []

    for x in values:

        if x[0] in 'zZ':
            pos = p[0]

        if x[0] in 'zZmM':
            p = remove_doubles(p)
            if x[0] in 'zZ':
                p = p + p[:1]

            if len(p) > 0:
                polygons.append( p )
                pol_debug( p )
                p = []

        if x[0] in 'zZmMlLhHvVcCsSqQtTaA':
            mode = x[0]
            x = x[1:]
            if x == '':
                continue

        if mode == 'm':
            mode = 'l'

        if mode == 'M':
            mode = 'L'

        if mode == 'l':
            pos = vector_add(pos, get_coords((x, next(values))))
            p.append( pos )

        elif mode == 'L':
            pos = get_coords((x, next(values)))
            p.append( pos )

        elif mode == 'H':
            pos = ( float(x), pos[1] )
            p.append( pos )

        elif mode == 'V':
            pos = ( pos[0], float(x) )
            p.append( pos )

        elif mode == 'h':
            pos = vector_add(pos, [float(x), 0])
            p.append( pos )

        elif mode == 'v':
            pos = vector_add(pos, [0, float(x)])
            p.append( pos )

        elif mode in 'cCsS':
            start  = pos
            if mode in 'sS':
                guide1 = cubic_ctrl
            else:
                guide1 = get_coords( (x, next(values)) )

            guide2 = get_coords( (next(values), next(values)) )
            end    = get_coords( (next(values), next(values)) )

            if mode in 'c':
                guide1 = vector_add(pos, guide1)

            if mode in 'cs':
                guide2 = vector_add(pos, guide2)
                end    = vector_add(pos, end)

            pos = end
            p.extend( cubic_spline(start, guide1, guide2, end, scale ) )
        elif mode in 'qQtT':
            start  = pos
            if mode in 'tT':
                guide = quad_ctrl
            else:
                guide = get_coords( (x, next(values)) )

            end = get_coords( (next(values), next(values)) )

            if mode in 'q':
                guide = vector_add(pos, guide)

            if mode in 'qt':
                end   = vector_add(pos, end)

            pos = end
            p.extend( quadratic_spline(start, guide, end, scale ) )
        elif mode in 'aA':
            start = pos
            rx, ry = float(x), float(next(values))
            rot = float(next(values))
            large_arc, sweep = float(next(values)), float(next(values))
            if large_arc not in (0,1) and sweep not in (0,1):
                sys.stderr.write("ERROR: arc\n")
                sys.exit(1)
            large_arc, sweep = bool(large_arc), bool(sweep)

            end = get_coords( (next(values), next(values)) )

            if mode in 'a':
                end   = vector_add(pos, end)

            pos = end
            p.extend( arc_spline(start, end, rx, ry, rot, large_arc, sweep) )
        else:
            sys.stderr.write("ERROR: " + x + '\n')
            sys.exit(1)

        cubic_ctrl = quad_ctrl = pos
        if mode in 'cCsS':
            cubic_ctrl = vector_sub(pos, vector_sub(guide2, pos))
        elif mode in 'qQtT':
            quad_ctrl = vector_sub(pos, vector_sub(guide, pos))

    if len(p) > 0:
        polygons.append( p )
        pol_debug(p)

    return polygons

def rescale_point(p, scale, flipX=False, flipY=False, conv=lambda x: x):
    x, y = p
    f_x = 1-2*int(flipX)
    f_y = 1-2*int(flipY)
    return ( conv(x*scale*f_x), conv(y*scale*f_y) )

def rescale_polygon(polygon, scale, flipX=False, flipY=False, conv=lambda x: x):
    rescaled = [ rescale_point(p, scale, flipX, flipY, conv) for p in polygon ]
    without_doubles = [ ]
    for i in range(len(polygon)):
        if rescaled[i-1] != rescaled[i] or polygon[i-1] == polygon[i]:
            without_doubles.append(rescaled[i])

    return without_doubles

def remove_doubles(p):
    return [ pa for pa, pb in zip(p, p[1:]+p[:1]) if pa != pb ]

def rescale_polygon_list(polygon_list, scale, flipX=False, flipY=False, conv=lambda x: x):
    return [ rescale_polygon(polygon, scale, flipX, flipY, conv) for polygon in polygon_list ]

#def transform_point(p, scale, translate, flipX, flipY, conv):
#    x, y = p
#    dx, dy = translate
#    scaleX, scaleY = scale, scale
#    if flipX:
#        scaleX = -scaleX
#    if flipY:
#        scaleY = -scaleY
#    return ( conv(dx+(x*scaleX)), conv(dy+(y*scaleY)) )
#
#def transform_polygon(polygon, scale, translate, flipX, flipY, conv):
#    return [ transform_point(p, scale, translate, flipX, flipY, conv) for p in polygon ]
#
#def transform_polygon_list(polygon_list, scale, translate=(0,0), flipX=False, flipY=False, conv=lambda x: x):
#    return [ transform_polygon(polygon, scale, translate, flipX, flipY, conv) for polygon in polygon_list ]
#
#def translate_polygon(polygon_list, translate):
#    dx, dy = translate
#    return [ (x+dx, y+dy) for x, y in polygon ]
#
#def translate_polygon_list(polygon_list, translate):
#    return [ translate_polygon(polygon, translate) for polygon in polygon_list ]
#
