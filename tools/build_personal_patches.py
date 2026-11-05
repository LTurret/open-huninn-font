#!/usr/bin/env python3
"""Build named personal 2.1 patch fonts from the unmodified upstream TTF."""
from copy import deepcopy
from pathlib import Path
import argparse

from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates

WIDTHS = {
    0x0060: 400, 0x00A8: 1024, 0x00AF: 320, 0x00B4: 400,
    0x00B8: 400, 0x02BB: 400, 0x02BC: 400, 0x02BE: 400,
    0x02BF: 400, 0x02C6: 400, 0x02C8: 200, 0x02CC: 200,
    0x02D8: 400, 0x02D9: 560, 0x02DA: 400, 0x02DB: 240,
    0x02DC: 400, 0x02DD: 450,
}

def fix_accents(font):
    assert font['head'].unitsPerEm == 1024
    cmap = font.getBestCmap()
    for cp, width in WIDTHS.items():
        glyph = cmap[cp]
        advance, lsb = font['hmtx'][glyph]
        assert advance == 0, (hex(cp), advance)
        font['hmtx'][glyph] = width, lsb

def fix_lowercase_k_caron(font):
    cmap = font.getBestCmap()
    assert cmap[0x01E8] == cmap[0x01E9] == 'uni01E8'
    glyf = font['glyf']
    base = deepcopy(glyf['k'])
    accent_source = glyf[cmap[0x021F]]
    base_pts, base_ends, base_flags = base.getCoordinates(glyf)
    src_pts, src_ends, src_flags = accent_source.getCoordinates(glyf)
    assert len(src_ends) == 2
    start = src_ends[0] + 1
    dx = (font['hmtx']['k'][0] - font['hmtx'][cmap[0x021F]][0]) // 2
    accent_pts = [(x + dx, y) for x, y in src_pts[start:]]
    base.coordinates = GlyphCoordinates(list(base_pts) + accent_pts)
    base.endPtsOfContours = list(base_ends) + [len(base.coordinates) - 1]
    base.flags = bytearray(list(base_flags) + list(src_flags[start:]))
    base.numberOfContours = len(base.endPtsOfContours)
    base.recalcBounds(glyf)
    glyf.glyphs['uni01E9'] = base
    font.setGlyphOrder(font.getGlyphOrder() + ['uni01E9'])
    font['hmtx']['uni01E9'] = font['hmtx']['k']
    for table in font['cmap'].tables:
        if table.isUnicode() and 0x01E9 in table.cmap:
            table.cmap[0x01E9] = 'uni01E9'

def rename(font, label):
    """Retain the upstream language records and append the patch identifier."""
    suffix = label.rsplit('.', 1)[-1]
    patch_version = f"2.1.patch.{suffix}"
    chinese_name = f"jf open 粉圓 {patch_version}"
    for record in font['name'].names:
        if record.langID == 0x0404:
            if record.nameID in (1, 4, 16):
                value = chinese_name
            else:
                continue
        elif record.langID == 0x0409:
            if record.nameID in (1, 4, 6, 16):
                value = label
            elif record.nameID == 3:
                value = f"{label};Regular;{patch_version};2024-09-19;justfont Co., LTD."
            elif record.nameID == 5:
                value = patch_version
            else:
                continue
        else:
            continue
        record.string = value.encode(record.getEncoding())



def make(source, destination, patch2=False):
    font = TTFont(source)
    fix_accents(font)
    if patch2:
        fix_lowercase_k_caron(font)
    label = 'jf-openhuninn-2.1.patch.2' if patch2 else 'jf-openhuninn-2.1.patch.1'
    rename(font, label)
    destination.parent.mkdir(parents=True, exist_ok=True)
    font.save(destination)
    font.close()
    with TTFont(destination) as check:
        for name_id in (1, 4, 16):
            assert check['name'].getName(name_id, 3, 1, 0x0404).toUnicode() == f"jf open 粉圓 2.1.patch.{2 if patch2 else 1}"
            assert check['name'].getName(name_id, 3, 1, 0x0409).toUnicode() == label
        assert check['name'].getName(6, 3, 1, 0x0409).toUnicode() == label
        for cp, expected in WIDTHS.items():
            assert check['hmtx'][check.getBestCmap()[cp]][0] == expected
        assert (check.getBestCmap()[0x01E9] == 'uni01E9') == patch2
        print(destination, len(check.getGlyphOrder()))

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('source', type=Path)
    p.add_argument('output_root', type=Path)
    args = p.parse_args()
    for num in (1, 2):
        name = f'jf-openhuninn-2.1.patch.{num}'
        make(args.source, args.output_root / f'{name}.ttf', patch2=num == 2)
