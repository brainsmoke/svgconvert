#!/usr/bin/env python3
# (c) 2018-2021 Erik Bosman
# License: https://opensource.org/licenses/MIT
#
# Usage: python3 svgtokicadmod.py [--layer <layername>] file.svg > my_footprints.pretty/file.kicad_mod
#
# Layer names:
#
#     front_mask
#     front_silk
#     front_paste
#     front_copper
#     back_mask
#     back_silk
#     back_copper
#     back_paste
#     edges
#     vias:<size>:<drillsize> (uses centers of circles as via location)
#     pads:<size>:<drillsize> (uses centers of circles as pad location)
#     holes:<drillsize>       (uses centers of circles as hole location)

import sys

import svgextract, scad
import svgpath
#svgpath.cubic_sections = 16
svgpath.cubic_sections = 8

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--layer", help="extract module from sublayers of a specific layer", type=str)
    args = parser.parse_args()

    name = args.layer
    if name == None:
        name = 'pcb'

    (paths, segments, pads, vias, holes, slots) = svgextract.extract_pcb_data(sys.stdin, args.layer, edges_as_segments=False)
    scad.print_module(sys.stdout, name, paths, segments, pads, vias, holes, slots)
