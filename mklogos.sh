#!/bin/sh

DIR="$(dirname -- $0)"

mkdir -p "$DIR/logos.pretty"

for i in "$DIR/"*.svg;
do
FILENAME="$(basename -- "$i")"
"$DIR/svgtokicadmod.py" < "$i" > "$DIR/logos.pretty/${FILENAME%.svg}.kicad_mod"
done
