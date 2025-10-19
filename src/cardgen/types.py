"""Type aliases used across the cardgen package."""

from typing import Literal

# Cover art display options
CoverArtMode = Literal["square", "fullscale"]
CoverArtAlign = Literal["center", "left", "right"]

# Track title overflow options
TrackTitleOverflow = Literal["truncate", "wrap"]
