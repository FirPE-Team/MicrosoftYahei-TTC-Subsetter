# Microsoft YaHei TTC Subsetter

[简体中文](README.zh.md) | English

Build a compact Microsoft YaHei 6.31 TTC while preserving TrueType hinting,
localized naming, and shared tables between the Microsoft YaHei and Microsoft
YaHei UI faces.

## Character set files

The build script reads the following Unicode lists, one `U+XXXX` codepoint per
line:

- `unicode/msyh-unicode-superset.txt`: Microsoft YaHei (13,736 characters)
- `unicode/msyhui-unicode-superset.txt`: Microsoft YaHei UI (13,759 characters)

Note: Only characters that exist in the input TTC are retained. Requested
codepoints unsupported by the input font are reported during the build; their
glyphs cannot be created from nothing.

## Requirements

- Python 3.12 or later
- [FontTools](https://github.com/fonttools/fonttools)

Create a virtual environment and install the dependencies:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Build

```powershell
build.py <input-font.ttc> <output-font.ttc>
```

Example:

```powershell
build.py .\msyh.ttc .\target\msyh.ttc
```

The output retains `cvt `, `fpgm`, `prep`, and `gasp` hinting data and removes
the device-specific `hdmx`, `LTSH`, and `VDMX` metric tables. It also retains
the Simplified Chinese localized name for Microsoft YaHei and makes both font
faces share their core glyph and layout tables.

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.
