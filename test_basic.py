#!/usr/bin/env python3
"""Basic test script to verify the setup works."""

from cardgen.api import NavidromeClient
from cardgen.config import load_config

# Test config loading
print("Testing config loading...")
config = load_config()
print(f"✓ Config loaded: {config.navidrome.url}")

# Test Navidrome client initialization
print("\nTesting Navidrome client...")
client = NavidromeClient(config.navidrome)
print("✓ Client initialized")

# Test URL parsing
print("\nTesting URL parsing...")
test_url = "http://tower:4533/app/#/album/abc123"
resource_type, resource_id = NavidromeClient.extract_id_from_url(test_url)
print(f"✓ URL parsed: type={resource_type}, id={resource_id}")

print("\n✓ All basic tests passed!")
print("\nReady to generate cards! Try:")
print("  cardgen album 'http://tower:4533/app/#/album/<your-album-id>'")
