#!/usr/bin/env python3
"""Fix zero advance widths of spacing accents in jf open huninn 2.1.

Install: python -m pip install fonttools
Usage: python tools/fix_spacing_accents.py font/jf-openhuninn-2.1.ttf output.ttf

Widths are proposed values (font units at 1024 UPM), not upstream-approved
design metrics. This intentionally does not change combining marks, outlines,
OpenType layout tables, glyph mappings, or font-family names.
"""

import argparse
from pathlib import Path

from fontTools.ttLib import TTFont

# Unicode codepoint -> proposed horizontal advance.
ADVANCES = {
    0x0060: 400,   # GRAVE ACCENT
    0x00A8: 1024,  # DIAERESIS
    0x00AF: 320,   # MACRON
    0x00B4: 400,   # ACUTE ACCENT
    0x00B8: 400,   # CEDILLA
    0x02BB: 400,   # MODIFIER LETTER TURNED COMMA
    0x02BC: 400,   # MODIFIER LETTER APOSTROPHE
    0x02BE: 400,   # MODIFIER LETTER RIGHT HALF RING
    0x02BF: 400,   # MODIFIER LETTER LEFT HALF RING
    0x02C6: 400,   # MODIFIER LETTER CIRCUMFLEX ACCENT
    0x02C8: 200,   # MODIFIER LETTER VERTICAL LINE
    0x02CC: 200,   # MODIFIER LETTER LOW VERTICAL LINE
    0x02D8: 400,   # BREVE
    0x02D9: 560,   # DOT ABOVE
    0x02DA: 400,   # RING ABOVE
    0x02DB: 240,   # OGONEK
    0x02DC: 400,   # SMALL TILDE
    0x02DD: 450,   # DOUBLE ACUTE ACCENT
}


def patch(source: Path, destination: Path) -> None:
    if source.resolve() == destination.resolve():
        raise ValueError("Use a separate output file; do not overwrite the original.")

    font = TTFont(source)
    try:
        if font["head"].unitsPerEm != 1024:
            raise ValueError("Expected jf open huninn 2.1 (1024 UPM).")

        cmap = font.getBestCmap()
        if cmap is None:
            raise ValueError("No Unicode cmap found.")

        for codepoint, width in ADVANCES.items():
            glyph_name = cmap.get(codepoint)
            if glyph_name is None:
                raise ValueError(f"Missing U+{codepoint:04X}")
            old_width, left_side_bearing = font["hmtx"].metrics[glyph_name]
            if old_width != 0:
                raise ValueError(
                    f"Unexpected width for U+{codepoint:04X}: {old_width} (expected 0)"
                )
            font["hmtx"].metrics[glyph_name] = (width, left_side_bearing)

        destination.parent.mkdir(parents=True, exist_ok=True)
        font.save(destination)
    finally:
        font.close()

    with TTFont(destination) as result:
        new_cmap = result.getBestCmap()
        for codepoint, width in ADVANCES.items():
            assert result["hmtx"][new_cmap[codepoint]][0] == width

    print(f"Patched {len(ADVANCES)} spacing accent advances: {destination}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    patch(args.source, args.destination)
