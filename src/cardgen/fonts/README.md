# Fonts Directory

This directory contains custom fonts used by the album card generator.

## Iosevka

The default font for this project is **Iosevka**, a versatile typeface designed for code and terminal use.

### Required Files

Place the following Iosevka font files in this directory:

- `iosevka-regular.ttf` - Regular weight
- `iosevka-bold.ttf` - Bold weight

### Where to Get Iosevka

**Quick Setup (Recommended):**

Run the included download script from the project root:

```bash
./scripts/download-fonts.sh
```

This will automatically download and install the default Iosevka fonts.

**Other Variants:**

To use a different Iosevka variant (e.g., Iosevka Term):

```bash
./scripts/download-fonts.sh IosevkaTerm
```

Available variants: `Iosevka`, `IosevkaTerm`, `IosevkaFixed`, `IosevkaSlab`, etc.
See: https://github.com/be5invis/Iosevka/blob/main/doc/PACKAGE-LIST.md

**Manual Download:**

1. Download from: https://github.com/be5invis/Iosevka/releases
2. Extract the TTF package
3. Copy the Regular and Bold `.ttf` files to this directory
4. Rename them to `iosevka-regular.ttf` and `iosevka-bold.ttf`

### License

Iosevka is licensed under the SIL Open Font License 1.1, which allows:
- ✓ Free commercial and personal use
- ✓ Redistribution (font files can be included in this repo)
- ✓ Modification

See: https://github.com/be5invis/Iosevka/blob/main/LICENSE.md

### Fallback Font

If Iosevka files are not present, the generator will automatically fall back to **Helvetica** (PDF built-in font). You'll see a warning message in the console.

To use Helvetica instead of Iosevka, change `font_family = "Helvetica"` in your `config.toml`.

## Adding Your Own Fonts

You can use any TrueType font by:

1. Adding the `.ttf` files to this directory
2. Updating `src/cardgen/fonts/__init__.py` to register your fonts
3. Setting `font_family` in your `config.toml`

Make sure you have the appropriate license to use and distribute any custom fonts.
