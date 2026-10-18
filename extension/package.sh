#!/bin/sh
# Zips the extension for upload to addons.mozilla.org: only the files the extension needs,
# with manifest.json at the top level of the zip (the store rejects a zip with a folder inside).
set -e
cd "$(dirname "$0")"
version=$(python3 -c "import json; print(json.load(open('manifest.json'))['version'])")
mkdir -p ../extension-build
out="../extension-build/huntboard-$version.zip"
rm -f "$out"
zip -q -r "$out" manifest.json popup.html popup.css popup.js icons -x "*.DS_Store"
echo "Built $out"
