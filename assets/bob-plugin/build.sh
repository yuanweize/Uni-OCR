#!/bin/bash
# Builds the Bob plugin zip file

cd "$(dirname "$0")"

PLUGIN_NAME="uniocr.bobplugin"

echo "Building Bob Plugin: $PLUGIN_NAME"

# Zip the required files
zip -q -r "$PLUGIN_NAME" info.json main.js

echo "Done! Double-click $PLUGIN_NAME to install it into Bob."
