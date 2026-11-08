#!/bin/sh
# Render an SVG to PNG on the site's paper colour for review: render.sh out/x.svg
f="$1"; w=$(grep -o 'width="[0-9]*"' "$f" | head -1 | tr -dc 0-9); h=$(grep -o 'height="[0-9]*"' "$f" | head -1 | tr -dc 0-9)
html="/tmp/fig-$$.html"
printf '<html><body style="margin:0;background:#0a0b0e"><img src="file://%s" width="%s" height="%s"></body></html>' "$(cd "$(dirname "$f")" && pwd)/$(basename "$f")" "$w" "$h" > "$html"
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --hide-scrollbars --force-device-scale-factor=2 --allow-file-access-from-files --window-size="$w,$h" --screenshot="${f%.svg}.png" "file://$html" >/dev/null 2>&1
rm -f "$html"; echo "${f%.svg}.png"
