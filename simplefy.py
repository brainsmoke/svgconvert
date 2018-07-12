# (c) 2018 Erik Bosman
# License: https://opensource.org/licenses/MIT

import sys, math, itertools

def dist(a, b):
    ax, ay = a
    bx, by = b
    return math.sqrt((ax-bx)**2 + (ay-by)**2)

def cross_product(a, b, c):
    ax, ay = a
    bx, by = b
    cx, cy = c
    return (bx-ax) * (cy-ay) - (by-ay) * (cx-ax)

def counter_clockwise(a, b, c):
    z = cross_product(a, b, c)
    if z > 0:
        return 1
    elif z < 0:
        return -1
    else:
        return 0

def intersect(l1, l2):
    a, b = l1
    c, d = l2
    return ( counter_clockwise(a,c,d) != counter_clockwise(b,c,d) and 
             counter_clockwise(a,b,c) != counter_clockwise(a,b,d) )

def interpolate(pos1, pos2, d):
    x1, y1 = pos1
    x2, y2 = pos2
    return ( x1*(1-d) + x2*d, y1*(1-d) + y2*d )

def vector_add(a, b):
    return tuple( i+j for i, j in zip(a,b) )

def vector_sub(a, b):
    return tuple( i-j for i, j in zip(a,b) )

def get_coords(s):
    return [float(x) for x in s]

def quadrant(p):
    px,py = p
    if py < 0:
        return int(px>0)
    else:
        return 3-int(px>0)

def polygon_rotations(poly, center):
    r = 0
    x, y = vector_sub(poly[0], center)
    q = quadrant( (x, y) )
    for p in poly[1:]:
        lastx, lasty = x, y
        lastq = q

        x, y = vector_sub(p, center)
        q = quadrant( (x, y) )

        if x|y == 0:
            return 0
        elif q == lastq:
            pass
        elif q == (lastq+1)%4:
            r += 1
        elif q == (lastq+3)%4:
            r -= 1
        elif (lastx*y < x*lasty) == (y*lasty > 0):
            r += 2
        else:
            r -= 2
    if not -1 <= r % 4 <= 1:
        sys.stderr.write("MEH r="+str(r) + str([poly]) + '\n')
        sys.exit(1)
    return r//4

def polygon_crossproduct_sum(poly):
    total = 0
    a = poly[0]
    for i in range(len(poly)-2):
        b,c = poly[i+1:i+3]
        total += cross_product(a, b, c)
    return total

def remove_subsubsets(subsets):
    sets = list(subsets.keys())
    for s_a in sets:
        for s_b in sets:
            for s_c in sets:
                if s_a in subsets[s_b] and s_b in subsets[s_c] and s_a in subsets[s_c]:
                    subsets[s_c].remove(s_a)

def nest_depth(parentset, key):
    if parentset[key] == []:
        return 0
    else:
        return 1+nest_depth(parentset, parentset[key][0])

def get_cutout_mapping(polygon_list):
    parents = dict( (n,[]) for n in range(len(polygon_list)) )
    children = dict( (n,[]) for n in range(len(polygon_list)) )
    bboxes = [ ( min(x for x,y in p),
                 min(y for x,y in p),
                 max(x for x,y in p),
                 max(y for x,y in p) ) for p in polygon_list ]

    for a, p_a, in enumerate(polygon_list):
        for b, p_b, in enumerate(polygon_list):
            if a != b:
                min_ax, min_ay, max_ax, max_ay = bboxes[a]
                min_bx, min_by, max_bx, max_by = bboxes[b]
                if ( min_bx <= min_ax <= max_ax <= max_bx and
                     min_by <= min_ay <= max_ay <= max_by ):

                    r = polygon_rotations(p_b, p_a[0])
                    if r == 1:
                        sys.stderr.write("orientation weird\n")
                        sys.exit(1)
                    if r != 0:
                        parents[a].append(b)
                        children[b].append(a)

    remove_subsubsets(parents)
    remove_subsubsets(children)

    for p in list(children.keys()):
        if nest_depth(parents, p) & 1 == 1:
            del children[p]

    return children

def close_polygons(polygons):
    for polygon in polygons:
        if tuple(polygon[0]) != tuple(polygon[-1]):
            polygon.append(polygon[0])
    return polygons

def counter_clockwise(polygons):
    for polygon in polygons:
        if polygon_crossproduct_sum(polygon) > 0:
            polygon.reverse()
    return polygons

def weakly_simplefy_polygon(polygon, cutouts):
    for c in cutouts:
        c.reverse()
    while len(cutouts) > 0:
        distlist = [ (dist(pp, cp), pn, cn, c) for pn,pp in enumerate(polygon[:-1]) for c in cutouts for cn,cp in enumerate(c[:-1]) ]
        distlist.sort(key=lambda x: x[0])
        sys.stderr.write( str(len(distlist)) + '\n' )
        for _, pn, cn, c in distlist:
            line1 = (polygon[pn], c[cn])

            for line2 in itertools.chain( zip(p[:-1], p[1:]) for p in [polygon]+cutouts ):
                if polygon[pn] not in line1 and intersect(line1, line2):
                    break
            else:
                sys.stderr.write( str(polygon[pn]) + ' '+ str(c[cn]) + str(_) + '\n')
                polygon[pn:pn] = [polygon[pn]] + c[cn:-1] + c[:cn+1] 
                cutouts.remove(c)
                break
    return polygon

def weakly_simplefy(polygons):
    polygons = close_polygons(polygons)
    polygons = counter_clockwise(polygons)
    # slow
    mapping = get_cutout_mapping(polygons)
    mapping_keys = list(mapping.keys())
    mapping_keys.sort()
    sys.stderr.write(str(mapping)+'\n')
    # slow as hell
    return [ weakly_simplefy_polygon(polygons[num], [polygons[x] for x in mapping[num]]) for num in mapping_keys ]
#    # new kicad can handle cutouts? nope :-/
#    for plist in mapping.values():
#        for poly_cutout in plist:
#            polygons[poly_cutout].reverse()
#            sys.stderr.write(str(poly_cutout)+'  XX\n')
#            
#    return polygons

