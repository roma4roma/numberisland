#!/usr/bin/env bash
# Builds index.html (the game students load) from source/number-island.html.
# Usage:  ./build.sh            then commit index.html + version.txt and push.
# Needs: python3, node (npx downloads svgo the first time).
set -e
cd "$(dirname "$0")"
SHEET_URL='https://script.google.com/macros/s/AKfycbxBGj1Bd8BZhVjb7ia4wGrT3oNzbjIii0qxEi4LsmdEy5DE8WNbypQhKGP0hBJaug/exec'
V=$(TZ=Asia/Seoul date +%Y%m%d%H%M)

# 1. wrap the source in a full HTML page
python3 tools/build.py source/number-island.html index.html
# 2. shrink the OpenMoji pictures (once) and pack them inside index.html, so each tablet downloads one file
if [ ! -d .emoji-min ]; then npx --yes svgo -q -f emoji -o .emoji-min --multipass; fi
node tools/embed_emoji.js index.html .emoji-min
# 3. connect the class Google Sheet and stamp the version (tablets reload themselves when version.txt changes)
sed -i "s|const CLASS_SHEET_URL = '';|const CLASS_SHEET_URL = '$SHEET_URL';|; s|const BUILD_ID = 'dev';|const BUILD_ID = '$V';|" index.html
echo "$V" > version.txt
echo "Built index.html (version $V)"
