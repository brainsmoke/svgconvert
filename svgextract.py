#!/usr/bin/env python3
# (c) 2018 Erik Bosman
# License: https://opensource.org/licenses/MIT

import xml.etree.ElementTree as ET
import math, cmath, itertools

import svgpath

import sys

fab_layers = [
    "front_mask",
    "front_silk",
    "front_paste",
    "front_copper",

    "back_mask",
    "back_silk",
    "back_copper",
    "back_paste",

    "edges",

#   "vias:<size>:<drillsize>"
#   "pads:<size>:<drillsize>"
#   "holes:<drillsize>"

]

def parse_style(s):
    """ sorry :-/ """
    style_elems = {}
    for x in s.split(';'):
        k, v = x.split(':',1)
        style_elems[k] = v
    return style_elems

def mmul(mA, mB):
    a11, a21, a12, a22, a13, a23 = mA
    b11, b21, b12, b22, b13, b23 = mB
    c11 = a11*b11 + a12*b21
    c21 = a21*b11 + a22*b21
    c12 = a11*b12 + a12*b22
    c22 = a21*b12 + a22*b22
    c13 = a11*b13 + a12*b23 + a13
    c23 = a21*b13 + a22*b23 + a23
    return [ c11, c21, c12, c22, c13, c23 ]

def parse_transform(s):
    """ sorry :-/ """
    s = s.replace('(', ' ( ').replace(')', ' ) ').replace(',',' ')
    tokens = ( x for x in s.split(' ') if x != '' )
    transforms = [ ]
    ok = True
    try:
        for t in tokens:
            ok = False
            if tokens.__next__() != '(':
                break

            arglist = []
            for arg in tokens:
                if arg == ')':
                    break
                arglist.append(arg)

            if t == 'matrix':
                if not len(arglist) == 6:
                    break
                transforms.append( [float(x) for x in arglist] )

            elif t == 'translate':
                if len(arglist) not in (1,2):
                    break
                x, y = float(arglist[0]), 0.
                if len(arglist) == 2:
                    y = float(arglist[1])
                transforms.append( [1, 0, 0, 1, x, y] )

            elif t == 'scale':
                if not 1 <= len(arg) <= 2:
                    break
                xscale = yscale = float(arglist[0])
                if len(arglist) == 2:
                    yscale = float(arglist[1])
                transforms.append( [xscale, 0, 0, yscale, 0, 0] )

            elif t == 'rotate':
                if len(arglist) not in (1,3):
                    break
                c = cmath.rect(1,math.radians(float(arglist[0])))
                if len(arglist) == 3:
                    x, y = float(arglist[1]), float(arglist[2])
                    transforms.append( [1, 0, 0, 1, x, y] )
                transforms.append( [c.real, c.imag, -c.imag, c.real, 0, 0] )
                if len(arglist) == 3:
                    transforms.append( [1, 0, 0, 1, -x, -y] )

            elif t == 'skewX':
                if len(arglist) == 1:
                    break
                transforms.append( [1, 0, math.tan(math.radians(arglist[0])), 1, 0, 0] )

            elif t == 'skewY':
                if len(arglist) == 1:
                    break
                transforms.append( [1, math.tan(math.radians(arglist[0])), 0, 1, 0, 0] )

            ok = True
    except StopIteration:
        pass


        if not ok:
            raise "meh."

    m = [1., 0., 0., 1., 0., 0.]
    for t in transforms:
        m = mmul(m, t)

    return m

def apply_transform(t, polygon):
    return [ (t[0]*x+t[2]*y+t[4],t[1]*x+t[3]*y+t[5]) for x,y in polygon]

def magnitude(t):
    return math.sqrt( (t[0]+t[2])**2 + (t[1]+t[3])**2 )

def get_transform(e, parent_map):
    m =  parse_transform(e.get('transform', ''))
    while e in parent_map:
        e = parent_map[e]
        #m = mmul(m, parse_transform(e.get('transform', '')))
        m = mmul(parse_transform(e.get('transform', '')),m)

    return m

def extract_pcb_data(f, parent_layer=None):

    tree = ET.parse(f)
    segments = []
    paths = []
    pads = []
    vias = []
    holes = []
    slots = []

    parent_map = { c:p for p in tree.iter() for c in p }

    for layer in tree.findall(".//*[@{http://www.inkscape.org/namespaces/inkscape}groupmode='layer']"):
        name = layer.get('{http://www.inkscape.org/namespaces/inkscape}label')
        if parent_map[layer].get('{http://www.inkscape.org/namespaces/inkscape}label', default=None) != parent_layer:
            continue
        print("Layer: ",name, file=sys.stderr)
        if name in fab_layers:
            for e in layer.findall(".//{http://www.w3.org/2000/svg}path"):
                d = e.get("d")
                style_elems = parse_style(e.get("style"))
                transform = get_transform(e, parent_map)
                polygons = [apply_transform(transform, p) for p in svgpath.path_to_polygons(d) ]
                if 'fill' in style_elems and style_elems['fill'] != 'none' and name != 'edges':
                    paths.append( (name, polygons) )
                if ('stroke' in style_elems and style_elems['stroke'] != 'none') or name == 'edges':
                    width = float(style_elems['stroke-width'])*magnitude(transform)
                    segments.append( (name, polygons, width) )
        namesplit = name.split(':')
        if len(namesplit) == 3 and namesplit[0] == 'pads':
            size, drill = float(namesplit[1]), float(namesplit[2])
            for e in itertools.chain(
					layer.findall(".//{http://www.w3.org/2000/svg}circle"),
					layer.findall(".//{http://www.w3.org/2000/svg}ellipse")):
                x = float(e.get("cx"))
                y = float(e.get("cy"))
                transform = get_transform(e, parent_map)
                x, y = apply_transform(transform, [(x,y)])[0]
                pads.append( (x, y, size, drill) )

        if len(namesplit) == 3 and namesplit[0] == 'vias':
            size, drill = float(namesplit[1]), float(namesplit[2])
            for e in itertools.chain(
					layer.findall(".//{http://www.w3.org/2000/svg}circle"),
					layer.findall(".//{http://www.w3.org/2000/svg}ellipse")):
                x = float(e.get("cx"))
                y = float(e.get("cy"))
                transform = get_transform(e, parent_map)
                x, y = apply_transform(transform, [(x,y)])[0]
                vias.append( (x, y, size, drill) )

        if len(namesplit) == 2 and namesplit[0] == 'holes':
            drill = float(namesplit[1])
            for e in itertools.chain(
					layer.findall(".//{http://www.w3.org/2000/svg}circle"),
					layer.findall(".//{http://www.w3.org/2000/svg}ellipse")):
                x = float(e.get("cx"))
                y = float(e.get("cy"))
                transform = get_transform(e, parent_map)
                x, y = apply_transform(transform, [(x,y)])[0]
                holes.append( (x, y, drill) )

        if len(namesplit) == 3 and namesplit[0] == 'slots':
            copper_width = float(namesplit[1])
            drill_width = float(namesplit[2])
            for e in layer.findall(".//{http://www.w3.org/2000/svg}path"):
                d = e.get("d")
                style_elems = parse_style(e.get("style"))
                transform = get_transform(e, parent_map)
                polygons = [apply_transform(transform, p) for p in svgpath.path_to_polygons(d) ]
                if ('stroke' in style_elems and style_elems['stroke'] != 'none') or name == 'edges':
                    slots.append( (polygons, copper_width, drill_width) )

    return (paths, segments, pads, vias, holes, slots)

def extract_pcb_zone(f, zonename):

    tree = ET.parse(f)
    zones = []

    parent_map = { c:p for p in tree.iter() for c in p }

    for layer in tree.findall(".//*[@{http://www.inkscape.org/namespaces/inkscape}groupmode='layer']"):
        name = layer.get('{http://www.inkscape.org/namespaces/inkscape}label')
        namesplit = name.split(':')
        if len(namesplit) == 2 and namesplit[0] == 'zone':
            if zonename == namesplit[1]:
                for e in layer.findall(".//{http://www.w3.org/2000/svg}path"):
                    d = e.get("d")
                    transform = get_transform(e, parent_map)
                    polygons = [ apply_transform(transform, p) for p in svgpath.path_to_polygons(d) ]
                    zones.append( polygons )

    return zones

