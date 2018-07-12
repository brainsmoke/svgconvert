#!/usr/bin/env python3
# (c) 2018 Erik Bosman
# License: https://opensource.org/licenses/MIT
#
# Usage: python3 svgtokicadzone.py zonename < file.svg > tmpfile
#
# replace existing zone polygons with tmpfile in the .kicad_pcb
#
# will extract paths with zones from layers named "zone:<zonename>"

import sys

import svgextract, kicad

layer_name = sys.argv[1]

zones = svgextract.extract_pcb_zone(sys.stdin, layer_name)
kicad.print_zones(sys.stdout, zones)
