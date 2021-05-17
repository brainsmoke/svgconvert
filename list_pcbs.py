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

import svgextract

if __name__ == '__main__':
    pcbs = svgextract.find_designs(sys.stdin)
    for name in pcbs:
        print(name)
