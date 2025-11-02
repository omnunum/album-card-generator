# Double Album J-Card Examples

## CLI Usage

### Basic Double Album
```bash
cardgen album 'album/ID1,album/ID2' -o my_double_album.pdf
```

### With Options
```bash
# With gradient background
cardgen album 'album/ID1,album/ID2' --gradient -o output.pdf

# With Dolby logo
cardgen album 'album/ID1,album/ID2' --dolby-logo -o output.pdf

# High DPI
cardgen album 'album/ID1,album/ID2' --dpi 1200 -o output.pdf

# Custom tape length (C120)
cardgen album 'album/ID1,album/ID2' --tape-length 120 -o output.pdf

# Combine everything
cardgen album 'album/ID1,album/ID2' \
  --gradient \
  --dolby-logo \
  --dpi 1200 \
  --tape-length 120 \
  --cover-art-mode fullscale \
  -o output.pdf
```

### Mix Single and Double Albums
```bash
# Print 3 cards: single, double, single
cardgen album album/ID1 'album/ID2,album/ID3' album/ID4 -o mixed.pdf
```

## Python API Usage

See [double_album_example.py](./double_album_example.py) for complete examples.

### Quick Start
```python
from cardgen import load_config
from cardgen.api.builder import create_double_album_card, render_cards_to_pdf

config = load_config()

card = create_double_album_card(
    url1="album/FIRST_ALBUM_ID",
    url2="album/SECOND_ALBUM_ID",
    config=config,
)

render_cards_to_pdf([card], "output.pdf", dpi=600)
```

## Layout

The double album j-card uses a 5-panel layout:

```
Panel 1 (Back)    : Metadata for both albums (split vertically)
Panel 2 (Spine)   : Combined spine with album art on left and right
Panel 3 (Front)   : Cover art for both albums (split vertically)
Panel 4 (Inside)  : Combined tracklist from both albums
Panel 5 (Right)   : Genre/descriptors for both albums (split vertically)
```

Visual representation:
```
__________
M    A      G
    S     T
M    A      G
__________

M = Metadata
S = Spine (with art_left and art_right)
A = Album Cover
T = Tracklist
G = Genre/Descriptors
```

## Spine Section

The spine uses a modular layout with these components (left to right when rotated):
- `album_art_left` (optional)
- `text_lines` (auto-sized, can split)
- `dolby_logo` (optional)
- `album_art_right` (optional)

All components automatically adjust their spacing based on what's present.
