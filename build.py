import argparse
import copy
import hashlib
import re
from pathlib import Path

from fontTools.subset import Options, Subsetter
from fontTools.ttLib import TTCollection


ROOT = Path(__file__).resolve().parent
CHARSET_FILES = (
    ROOT / "unicode/msyh-unicode-superset.txt",
    ROOT / "unicode/msyhui-unicode-superset.txt",
)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Build a shared-table Microsoft YaHei TTC subset."
    )
    parser.add_argument("input_font", type=Path, help="Source Microsoft YaHei TTC path.")
    parser.add_argument("output_font", type=Path, help="Output TTC path.")
    arguments = parser.parse_args()

    source = arguments.input_font.resolve()
    output = arguments.output_font.resolve()
    if not source.is_file():
        parser.error(f"Input font does not exist: {source}")
    if source == output:
        parser.error("Input and output font paths must be different.")
    output.parent.mkdir(parents=True, exist_ok=True)
    return source, output


def read_codepoints(path):
    values = set()
    for line in path.read_text(encoding="ascii").splitlines():
        match = re.fullmatch(r"U\+([0-9A-F]{4,6})", line)
        if match is None:
            raise ValueError(f"Invalid Unicode entry in {path.name}: {line!r}")
        values.add(int(match.group(1), 16))
    return values


def cmap(font):
    result = {}
    for table in font["cmap"].tables:
        if table.isUnicode():
            result.update(table.cmap)
    return result


def glyph_fingerprint(font, glyph_name):
    glyph = font["glyf"][glyph_name]
    coordinates, endpoints, flags = glyph.getCoordinates(font["glyf"])
    program = getattr(glyph, "program", None)
    instructions = program.getBytecode() if program is not None else b""
    payload = repr(
        (
            glyph.numberOfContours,
            list(coordinates),
            list(endpoints),
            bytes(flags),
            instructions,
            font["hmtx"].metrics[glyph_name],
            font["vmtx"].metrics[glyph_name],
        )
    ).encode()
    return hashlib.sha256(payload).digest()


SOURCE, OUTPUT = parse_arguments()
collection = TTCollection(SOURCE, lazy=False)
regular, ui = collection.fonts
regular_order = regular.getGlyphOrder()[:]
ui_order = ui.getGlyphOrder()[:]
regular_cmap = cmap(regular)
ui_cmap = cmap(ui)
regular_requested = read_codepoints(CHARSET_FILES[0])
ui_requested = read_codepoints(CHARSET_FILES[1])
regular_supported = regular_requested & set(regular_cmap)
ui_supported = ui_requested & set(ui_cmap)

# Most codepoints share identical glyphs between faces. Preserve the few UI-only
# glyph variants under distinct names so both variants can coexist in one GID set.
ui_variant_names = {}
for codepoint in ui_supported & regular_supported:
    regular_name = regular_cmap[codepoint]
    ui_name = ui_cmap[codepoint]
    if glyph_fingerprint(regular, regular_name) != glyph_fingerprint(ui, ui_name):
        variant_name = f"ui.variant.{codepoint:04X}"
        ui_variant_names[codepoint] = variant_name
        regular["glyf"].glyphs[variant_name] = copy.deepcopy(ui["glyf"][ui_name])
        regular["hmtx"].metrics[variant_name] = ui["hmtx"].metrics[ui_name]
        regular["vmtx"].metrics[variant_name] = ui["vmtx"].metrics[ui_name]

if ui_variant_names:
    regular.setGlyphOrder(regular_order + list(ui_variant_names.values()))

for table_tag in ("hdmx", "LTSH", "VDMX"):
    if table_tag in regular:
        del regular[table_tag]

options = Options()
options.hinting = True
options.name_languages = [0x0409, 0x0804]
options.recalc_timestamp = False
subsetter = Subsetter(options=options)
subsetter.populate(unicodes=regular_supported, glyphs=set(ui_variant_names.values()))
subsetter.subset(regular)
canonical_order = regular.getGlyphOrder()[:]
old_gid_to_new_gid = subsetter.glyph_index_map

# UI-only mapped characters from the original 6.31 face are not supported by
# the requested charset; all requested UI characters can now use the canonical
# regular GID set, with the preserved variants above where required.
new_ui_cmap = copy.deepcopy(ui["cmap"])
for subtable in new_ui_cmap.tables:
    if not subtable.isUnicode():
        continue
    rewritten = {}
    for codepoint, ui_name in subtable.cmap.items():
        if codepoint not in ui_supported:
            continue
        if codepoint in ui_variant_names:
            canonical_name = ui_variant_names[codepoint]
        else:
            regular_name = regular_cmap[codepoint]
            old_gid = regular_order.index(regular_name)
            canonical_name = canonical_order[old_gid_to_new_gid[old_gid]]
        rewritten[codepoint] = canonical_name
    subtable.cmap = rewritten
ui["cmap"] = new_ui_cmap
ui.setGlyphOrder(canonical_order)

# Share every GID-dependent table. Keep each face's own naming and metrics
# header tables, as in the reference TTC.
for table_tag in (
    "glyf",
    "loca",
    "hmtx",
    "vmtx",
    "maxp",
    "GDEF",
    "GPOS",
    "GSUB",
    "cvt ",
    "fpgm",
    "prep",
    "gasp",
    "vhea",
    "post",
):
    if table_tag in regular:
        ui[table_tag] = regular[table_tag]
ui["hhea"].numberOfHMetrics = regular["hhea"].numberOfHMetrics

for font in (regular, ui):
    for table_tag in ("hdmx", "LTSH", "VDMX", "MERG", "meta", "kern"):
        if table_tag in font:
            del font[table_tag]

collection.save(OUTPUT)
print(f"regular: requested={len(regular_requested)} supported={len(regular_supported)}")
print(f"ui: requested={len(ui_requested)} supported={len(ui_supported)}")
print(f"ui variants retained={len(ui_variant_names)}")
print(OUTPUT)
