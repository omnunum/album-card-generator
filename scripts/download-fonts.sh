#!/usr/bin/env bash
# Download and extract Iosevka fonts for album-card-generator

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FONTS_DIR="$PROJECT_ROOT/src/cardgen/fonts"
TEMP_DIR=$(mktemp -d)

# Iosevka version to download
IOSEVKA_VERSION="32.3.1"

# Package to download (default Iosevka)
PACKAGE_NAME="${1:-Iosevka}"

# GitHub release URL
DOWNLOAD_URL="https://github.com/be5invis/Iosevka/releases/download/v${IOSEVKA_VERSION}/PkgTTF-${PACKAGE_NAME}-${IOSEVKA_VERSION}.zip"

echo "📦 Downloading Iosevka fonts..."
echo "   Version: ${IOSEVKA_VERSION}"
echo "   Package: ${PACKAGE_NAME}"
echo "   URL: ${DOWNLOAD_URL}"
echo ""

# Download
cd "$TEMP_DIR"
echo "⬇️  Downloading..."
curl -L -o iosevka.zip "$DOWNLOAD_URL"

# Extract
echo "📂 Extracting..."
unzip -q iosevka.zip

# Find and copy the files we need
echo "📝 Copying font files..."

# Look for Regular and heavier weight (Heavy, ExtraBold, or Bold)
REGULAR_FILE=$(find . -iname "*regular.ttf" | head -n 1)

# Try to find Heavy first, then ExtraBold, then Bold
BOLD_FILE=$(find . -iname "*heavy.ttf" | grep -v "Oblique" | grep -v "Italic" | head -n 1)
if [ -z "$BOLD_FILE" ]; then
    BOLD_FILE=$(find . -iname "*extrabold.ttf" | grep -v "Oblique" | grep -v "Italic" | head -n 1)
fi
if [ -z "$BOLD_FILE" ]; then
    BOLD_FILE=$(find . -iname "*bold.ttf" | grep -v "Oblique" | grep -v "Italic" | head -n 1)
fi

if [ -z "$REGULAR_FILE" ]; then
    echo "❌ Error: Could not find Regular font file"
    rm -rf "$TEMP_DIR"
    exit 1
fi

if [ -z "$BOLD_FILE" ]; then
    echo "❌ Error: Could not find Bold/Heavy font file"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Show which weight was found
WEIGHT_NAME=$(basename "$BOLD_FILE" | sed 's/.*-\(.*\)\.ttf/\1/')
echo "   Using weight: $WEIGHT_NAME for bold"

# Create fonts directory if it doesn't exist
mkdir -p "$FONTS_DIR"

# Copy and rename files
cp "$REGULAR_FILE" "$FONTS_DIR/iosevka-regular.ttf"
cp "$BOLD_FILE" "$FONTS_DIR/iosevka-bold.ttf"

# Cleanup
rm -rf "$TEMP_DIR"

echo ""
echo "✅ Successfully installed Iosevka fonts!"
echo "   📄 iosevka-regular.ttf"
echo "   📄 iosevka-bold.ttf"
echo ""
echo "Files installed in: $FONTS_DIR"
echo ""
echo "You can now run: cardgen album <album-url>"
