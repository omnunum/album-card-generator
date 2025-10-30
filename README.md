# Album Card Generator

Generate printable cassette j-cards from Navidrome albums and playlists.

## Features

- Fetch album metadata and artwork from Navidrome server
- Generate print-ready PDF j-cards (8.5" x 11" with centered card)
- Support for 4-panel and 5-panel cassette j-cards
- **Python API for programmatic card creation with per-card styling**
- **Google Fonts support with automatic downloading and caching**
- **Gradient backgrounds extracted from album art**
- Configurable themes and output templates
- High-quality output (300-1200 DPI)
- Optional crop marks and fold guides
- **Batch processing: multiple cards in one multi-page PDF**

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

## Python API

You can programmatically create cards with custom styling using the Python API. This is useful for batch processing, custom workflows, or when you want fine-grained control over each card's appearance.

### Quick Start

```python
from cardgen import Theme, create_card, load_config, render_cards_to_pdf, NavidromeClient, JCard4Panel, AlbumArt

# Load config (for Navidrome credentials)
config = load_config()

# Create a card with custom styling
card = create_card(
    "album/abc123",
    config,
    JCard4Panel,
    Theme(
        title_google_font="Orbitron",
        title_font_weight=900,
        use_gradient=True,
    ),
)

# Render to PDF
render_cards_to_pdf([card], "my_card.pdf")
```

### Multiple Cards with Different Styling

```python
from cardgen import Theme, create_card_from_album, render_cards_to_pdf, load_config, NavidromeClient, JCard4Panel, JCard5Panel, AlbumArt

config = load_config()
client = NavidromeClient(config.navidrome)

# Card 1: Orbitron font with gradient
album1 = client.get_album("abc123")
art1 = AlbumArt(album1.cover_art)
card1 = create_card_from_album(
    album1, art1, JCard5Panel,
    Theme(
        title_google_font="Orbitron",
        title_font_weight=900,
        use_gradient=True,
    )
)

# Card 2: Custom colors, fullscale cover art
album2 = client.get_album("xyz789")
art2 = AlbumArt(album2.cover_art)
card2 = create_card_from_album(
    album2, art2, JCard4Panel,
    Theme(
        background_color=(0.95, 0.95, 0.95),
        text_color=(0.1, 0.1, 0.1),
        cover_art_mode="fullscale",
        cover_art_align="left",
    )
)

# Card 3: All defaults
album3 = client.get_album("def456")
art3 = AlbumArt(album3.cover_art)
card3 = create_card_from_album(album3, art3, JCard4Panel)

# Render all to a single multi-page PDF (2 cards per page)
render_cards_to_pdf([card1, card2, card3], "my_cards.pdf", dpi=720)
```

### Available Configuration Options

All parameters in `Theme` are optional. Override only what you need:

**Fonts:**
- `font_family`: Base font (default: "Helvetica")
- `title_google_font`, `title_font_weight`: Google Font for album title
- `artist_google_font`, `artist_font_weight`: Google Font for artist name
- `title_font_size`, `artist_font_size`, `track_font_size`, `metadata_font_size`

**Colors:**
- `background_color`, `text_color`, `accent_color`: RGB tuples (0-1 range)
- `use_gradient`: Extract gradient from album art (bool)
- `gradient_text_color`, `gradient_accent_color`: Colors for gradient mode
- `gradient_indices`: Which colors from palette to use (tuple)

**Cover Art:**
- `cover_art_mode`: "square" or "fullscale"
- `cover_art_align`: "center", "left", or "right" (for fullscale)

**Card Settings:**
- `tape_length`: Cassette length in minutes (60, 90, 120, etc.)
- `dolby_logo`: Show Dolby NR logo (bool)
- `track_title_overflow`: "truncate" or "wrap"
- `min_track_title_char_spacing`: Character spacing (negative = compressed)

### Google Fonts

Google Fonts are automatically downloaded and cached on first use:

```python
Theme(
    title_google_font="Orbitron",    # Font family name
    title_font_weight=900,           # 100-900 (Thin to Black)
    artist_google_font="Roboto",
    artist_font_weight=400,
)
```

Browse fonts at [fonts.google.com](https://fonts.google.com).

Common weights: 100 (Thin), 300 (Light), 400 (Regular), 700 (Bold), 900 (Black)

### Examples

See the `examples/` directory for complete working examples:
- `simple_example.py`: Minimal single card example
- `multi_card_example.py`: Multiple cards with different styling
- `manual_album_example.py`: Create cards without Navidrome

### API Reference

**`create_card(url, config, card_class, theme=None)`**
- Create card from Navidrome album URL
- Arguments:
  - `url`: Album URL (e.g., "album/abc123")
  - `config`: Config object with Navidrome credentials
  - `card_class`: Card class (JCard4Panel or JCard5Panel)
  - `theme`: Theme object for styling
- Returns: `Card` object

**`create_card_from_album(album, album_art, card_class, theme=None)`**
- Create card from manually constructed Album object
- Arguments:
  - `album`: Album object with metadata
  - `album_art`: AlbumArt object for cover image
  - `card_class`: Card class (JCard4Panel or JCard5Panel)
  - `theme`: Theme object for styling
- Returns: `Card` object

**`render_cards_to_pdf(cards, output_path, dpi=600, include_crop_marks=True, page_size="letter")`**
- Render multiple cards to multi-page PDF
- 2 cards per page, stacked vertically

**`load_config(config_path=None)`**
- Load configuration from config.toml
- Returns: `Config` object with Navidrome credentials

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
- [ ] Support for other music servers (Plex, Jellyfin)

## Requirements

- Python 3.11+
- Navidrome server (or compatible Subsonic API server)

## License

[Add your license here]
