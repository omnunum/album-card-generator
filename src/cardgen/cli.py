"""CLI interface for album card generator."""

from pathlib import Path

import click

from cardgen.api import NavidromeClient
from cardgen.api.builder import create_card_from_album, render_cards_to_pdf
from cardgen.config import Theme, format_output_name, load_config
from cardgen.design import JCard4Panel, JCard5Panel
from cardgen.fonts import register_fonts
from cardgen.utils.album_art import AlbumArt
from cardgen.utils.dimensions import PAGE_SIZES


@click.group()
@click.version_option()
def main() -> None:
    """Generate printable cassette j-cards from Navidrome albums and playlists."""
    # Register custom fonts at startup
    register_fonts()


@main.command()
@click.argument("urls", nargs=-1, required=True)
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=Path),
    help="Output PDF file path. If not specified, uses template from config.",
)
@click.option(
    "--output-name",
    type=str,
    default="default",
    help="Named output template from config (default, dated, simple).",
)
@click.option(
    "--config",
    type=click.Path(exists=True, path_type=Path),
    help="Path to config.toml file. Defaults to ./config.toml",
)
@click.option(
    "--card-type",
    type=str,
    help="Card type override (jcard_4panel, jcard_5panel). Uses config default if not specified.",
)
@click.option(
    "--gradient",
    is_flag=True,
    help="Use gradient background with colors extracted from album art.",
)
@click.option(
    "--gradient-colors",
    type=str,
    default="0,1",
    help="Gradient color indices as '0,1' (0-based). Uses top 2 most frequent colors by default.",
)
@click.option(
    "--dpi",
    type=int,
    help="DPI for image rendering (300-1200). Uses config default if not specified.",
)
@click.option(
    "--no-crop-marks",
    is_flag=True,
    help="Disable crop marks and fold guides.",
)
@click.option(
    "--page-size",
    type=click.Choice(list(PAGE_SIZES.keys()), case_sensitive=False),
    help="Page size for printing.",
)
@click.option(
    "--tape-length",
    type=int,
    default=90,
    help="Cassette tape length in minutes (default: 90 for C90).",
)
@click.option(
    "--cover-art-mode",
    type=click.Choice(["square", "fullscale"], case_sensitive=False),
    help="Album art display mode: 'square' (default) or 'fullscale' (top-to-bottom with crop).",
)
@click.option(
    "--cover-art-align",
    type=click.Choice(["center", "left", "right"], case_sensitive=False),
    help="Horizontal alignment for fullscale mode: 'center' (default), 'left', or 'right'.",
)
@click.option(
    "--dolby-logo",
    is_flag=True,
    help="Show Dolby NR logo on the spine (takes up half the spine height).",
)
def album(
    urls: tuple[str, ...],
    output: Path | None,
    output_name: str,
    config: Path | None,
    card_type: str | None,
    gradient: bool,
    gradient_colors: str,
    dpi: int | None,
    no_crop_marks: bool,
    page_size: str | None,
    tape_length: int,
    cover_art_mode: str | None,
    cover_art_align: str | None,
    dolby_logo: bool,
) -> None:
    """
    Generate j-cards from one or more Navidrome albums.

    Cards are stacked vertically (2 per page) for efficient printing.

    URL can be either:
    - Simple format: album/abc123
    - Full URL: http://server/app/#/album/abc123

    Multiple albums can be specified to print on one PDF.
    """
    try:
        # Load configuration
        cfg = load_config(config)

        # Initialize Navidrome client
        client = NavidromeClient(cfg.navidrome)

        # Fetch all albums
        albums = []
        for url in urls:
            # Extract album ID from URL
            resource_type, resource_id = NavidromeClient.extract_id_from_url(url)

            if resource_type != "album":
                click.echo(f"Error: URL is for a {resource_type}, not an album. Use `cardgen playlist` instead.", err=True)
                raise SystemExit(1)

            # Fetch album data
            click.echo(f"Fetching album {resource_id}...")
            album_data = client.get_album(resource_id)
            # Set Dolby logo flag if requested
            album_data.show_dolby_logo = dolby_logo
            click.echo(f"  Found: {album_data.artist} - {album_data.title}")
            albums.append(album_data)

        # Determine output path
        if output is None:
            # Simple default template
            templates = {
                "default": "{artist} - {album}.pdf",
                "dated": "{artist} - {album} ({year}).pdf",
                "simple": "{album}.pdf",
            }
            template = templates.get(output_name, templates["default"])

            # Use first album for filename
            output_filename = format_output_name(
                template,
                albums[0].artist,
                albums[0].title,
                albums[0].year,
            )
            # If multiple albums, add suffix
            if len(albums) > 1:
                output_filename = output_filename.replace(".pdf", f"_and_{len(albums)-1}_more.pdf")
            output = Path(output_filename)

        # Select card type (default to jcard_5panel)
        selected_card_type = card_type or "jcard_5panel"
        if selected_card_type not in ("jcard_4panel", "jcard_5panel"):
            click.echo(f"Error: Unsupported card type '{selected_card_type}'. Supported: jcard_4panel, jcard_5panel", err=True)
            raise SystemExit(1)

        # Parse gradient color indices
        gradient_indices = (0, 1)  # Default to first two colors (most frequent)
        if gradient:
            try:
                parts = gradient_colors.split(',')
                if len(parts) != 2:
                    raise ValueError("Expected two comma-separated values")
                # Parse as 0-based indices directly
                idx1 = int(parts[0].strip())
                idx2 = int(parts[1].strip())
                if idx1 < 0 or idx2 < 0:
                    raise ValueError("Indices must be non-negative")
                gradient_indices = (idx1, idx2)
            except ValueError as e:
                click.echo(f"Error: Invalid --gradient-colors format '{gradient_colors}': {e}", err=True)
                click.echo("Expected format: '0,1' (two 0-based indices separated by comma)", err=True)
                raise SystemExit(1)

        # Build theme configuration with CLI option overrides
        theme_updates = {}
        if gradient:
            theme_updates["use_gradient"] = True
            theme_updates["gradient_indices"] = gradient_indices
        if cover_art_mode:
            theme_updates["cover_art_mode"] = cover_art_mode
        if cover_art_align:
            theme_updates["cover_art_align"] = cover_art_align
        if dolby_logo:
            theme_updates["dolby_logo"] = True

        theme_updates["tape_length"] = tape_length

        # Create theme with defaults + CLI overrides
        theme = Theme(**theme_updates)

        # Select card class
        card_class = JCard4Panel if selected_card_type == "jcard_4panel" else JCard5Panel

        # Create cards for each album
        cards = []
        for album_data in albums:
            # Create AlbumArt object from cover art bytes
            album_art_obj = AlbumArt(album_data.cover_art)

            # Show gradient info if enabled
            if gradient:
                click.echo(f"  Extracting color palette from album art...")
                click.echo(f"  Using gradient colors at indices {gradient_indices[0]} and {gradient_indices[1]}")

            # Create card using builder function (handles gradient extraction, font registration, etc.)
            card = create_card_from_album(album_data, album_art_obj, card_class, theme)
            cards.append(card)

        # Render PDF with defaults or CLI overrides
        render_dpi = dpi or 720  # Default to 720 DPI
        include_marks = not no_crop_marks  # Invert the flag (no_crop_marks=True means include_marks=False)
        selected_page_size = page_size or "letter"  # Default to letter

        click.echo(f"Generating PDF with {len(cards)} card(s) at {render_dpi} DPI on {selected_page_size} page...")
        render_cards_to_pdf(cards, output, dpi=render_dpi, page_size=selected_page_size, include_crop_marks=include_marks)

        click.echo(f"✓ J-card(s) saved to: {output}")

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@main.command()
@click.argument("url")
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=Path),
    help="Output PDF file path.",
)
@click.option(
    "--config",
    type=click.Path(exists=True, path_type=Path),
    help="Path to config.toml file. Defaults to ./config.toml",
)
def playlist(url: str, output: Path | None, config: Path | None) -> None:
    """
    Generate j-card from Navidrome playlist URL (NOT YET IMPLEMENTED).

    URL should be the full web interface URL, e.g.:
    http://server/app/#/playlist/xyz789
    """
    click.echo("Error: Playlist support is not yet implemented.", err=True)
    click.echo("Use `cardgen album` for now.", err=True)
    raise SystemExit(1)


if __name__ == "__main__":
    main()
