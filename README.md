# Album Card Generator

Generate printable cassette j-cards from Navidrome albums and playlists.

## Features

- Fetch album metadata and artwork from Navidrome server
- Generate print-ready PDF j-cards (8.5" x 11" with centered card)
- Support for 4-panel cassette j-cards
- Configurable themes and output templates
- High-quality output (300-1200 DPI)
- Optional crop marks and fold guides

## Installation

1. Clone the repository:
```bash
git clone <repo-url>
cd album-card-generator
```

2. Install dependencies:
```bash
pip install -e .
```

3. Download Iosevka fonts:
```bash
./scripts/download-fonts.sh
```

This will download and install the default Iosevka font used for j-cards. The condensed monospace design helps fit long track titles. See `src/cardgen/fonts/README.md` for details.

## Configuration

1. Copy the example config:
```bash
cp config.toml.example config.toml
```

2. Edit `config.toml` with your Navidrome credentials:
```toml
[navidrome]
url = "https://your-navidrome-server.com"
username = "your_username"
password = "your_password"
```

## Usage

### Generate J-Card from Album

```bash
# Basic usage with simple format (uses default output template)
cardgen album "album/abc123"

# Using full URL also works
cardgen album "http://server/app/#/album/abc123"

# Specify output file
cardgen album "album/abc123" -o my_card.pdf

# Use named output template
cardgen album "album/abc123" --output-name dated

# Custom DPI
cardgen album "album/abc123" --dpi 1200

# Disable crop marks
cardgen album "album/abc123" --no-crop-marks
```

### Output Templates

Configure named output templates in `config.toml`:

```toml
[output.templates]
default = "{artist} - {album}.pdf"
dated = "{artist} - {album} ({year}).pdf"
simple = "{album}.pdf"
```

Available placeholders:
- `{artist}` - Artist name
- `{album}` - Album title
- `{year}` - Release year
- `{date}` - Alias for year

### J-Card Layout

The 4-panel j-card layout (left to right):

```
┌─────────┬─────────┬───┬─────────┐
│ Inside  │  Back   │ S │  Front  │
│         │         │ p │         │
│ Track   │ Meta-   │ i │  Album  │
│ Listing │ data    │ n │  Cover  │
│         │         │ e │         │
└─────────┴─────────┴───┴─────────┘
```

**Front Panel:**
- Album artwork (square, centered)
- Artist name
- Album title

**Spine:**
- Artist • Title • Year (vertical text)

**Back Panel:**
- Genre
- Label
- Year
- Total duration

**Inside Panel:**
- Track listing with track numbers
- Track durations

## Printing

1. Open the generated PDF
2. Print on 8.5" x 11" cardstock (90-100 lb recommended)
3. Cut along crop marks (if included)
4. Fold along fold lines
5. Insert into cassette case

## Configuration Options

See `config.toml.example` for all available options:

- Card types (currently only `jcard_4panel`)
- Themes (currently only `default`)
- DPI (300-1200, default: 600)
- Crop marks (enabled/disabled)
- Font settings
- Color schemes

## Development

### Project Structure

```
src/cardgen/
├── api/              # Navidrome API client
├── config.py         # Configuration loading
├── design/           # Card layouts and themes
│   ├── base.py      # Abstract base classes
│   ├── cards/       # Card layout implementations
│   └── themes/      # Theme implementations
├── render/           # PDF and image rendering
│   ├── image.py     # Image processing (Pillow)
│   └── pdf.py       # PDF generation (ReportLab)
├── utils/            # Utilities (dimensions, etc.)
└── cli.py            # CLI interface
```

### Type Checking

The project uses full type hints and is mypy-compatible:

```bash
mypy src/
```

## Future Features

- [ ] Playlist support
- [ ] 2-panel and 6-panel j-card layouts
- [ ] Additional themes
- [ ] Custom fonts
- [ ] Batch processing
- [ ] Support for other music servers (Plex, Jellyfin)

## Requirements

- Python 3.11+
- Navidrome server (or compatible Subsonic API server)

## License

[Add your license here]
