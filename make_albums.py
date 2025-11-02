from cardgen import load_config
from cardgen.api.builder import (
    create_double_album_card,
    create_card,
    render_cards_to_pdf,
)
from cardgen.design.cards import JCard4Panel
from cardgen.config import Theme

# Load configuration (assumes config.toml exists in current directory)
config = load_config()

# Option 2: Double album with gradient
print("\nCreating double album with gradient...")
lapalux = create_double_album_card(
    url1="album/5DRv0SE2iR4e2zempluBcH",
    url2="album/7bhEY9X9tSkcwkUpouGb4k",
    config=config,
    theme=Theme(
        use_gradient=True,
        gradient_indices=(1, 9),  # Use most frequent colors
        artist_font_size=16,
        album_title_font_size=18,
        tape_length=100,
        dolby_logo=True
    )
)
producer = create_card(
    url="album/6R5i94PdtgS5NpHODjPr3H/",
    config=config,
    card_class=JCard4Panel,
    theme=Theme(
        use_gradient=True,
        gradient_indices=(1, 2),  # Use most frequent colors
        tape_length=90,
        artist_font="stop",
        artist_font_size=18,
        title_font="jethose",
        album_title_font_size=28,
        label_logo="https://kagi.com/proxy/gb1qta628tre1.png?c=TklOzPjLPioJ5YMJT75bSqbOvNy81tkBsxLuoTItbsNXavdMe7R68XGmq94gzX0y",
        dolby_logo=True
    )
)
render_cards_to_pdf([lapalux, producer], "albums.pdf", dpi=720)

