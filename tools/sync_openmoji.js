// Switches the game's emoji pictures to OpenMoji (color SVG). Finds every emoji in the game, maps it to an
// OpenMoji file, copies the files into emoji/, rewrites EMOJI_FILES and the CSS picture links in the game.
// Run it after adding a new emoji to the game:
//   npm pack openmoji && tar xzf openmoji-*.tgz      (gives package/color/svg)
//   node tools/sync_openmoji.js package/color/svg     then  rm -rf .emoji-min  and  ./build.sh
const fs = require('fs'), path = require('path');
const root = path.join(__dirname, '..');
const game = path.join(root, 'source', 'number-island.html'), out = path.join(root, 'emoji');
const om = process.argv[2] || path.join(root, 'package', 'color', 'svg');
let src = fs.readFileSync(game, 'utf8');
const i0 = src.indexOf('const EMOJI_FILES = '), i1 = src.indexOf(';\n', i0);
const oldTable = JSON.parse(src.slice(i0 + 'const EMOJI_FILES = '.length, i1));
const body = src.slice(0, i0) + src.slice(i1);
const found = [...new Set(body.match(/\p{RGI_Emoji}/gv))];
const hex = e => [...e].map(c => c.codePointAt(0).toString(16).toUpperCase()).join('-');
const table = {}, missing = [];
for (const e of found) {
  const h = hex(e), tries = [h, h.replace(/-FE0F/g, ''), h + '-FE0F'];
  const f = tries.map(t => t + '.svg').find(f => fs.existsSync(path.join(om, f)));
  if (!f) { missing.push(e + ' ' + h); continue; }
  table[e] = f; table[e.replace(/️/g, '')] ??= f;
}
// fresh emoji folder with only the files the game uses
for (const f of fs.readdirSync(out)) if (/\.(png|svg)$/.test(f)) fs.unlinkSync(path.join(out, f));
for (const f of new Set(Object.values(table))) fs.copyFileSync(path.join(om, f), path.join(out, f));
// CSS links like url(emoji/1f33b.png) -> the OpenMoji file for the same emoji
for (const [e, oldF] of Object.entries(oldTable)) if (table[e]) src = src.split(`url(emoji/${oldF})`).join(`url(emoji/${table[e]})`);
const j0 = src.indexOf('const EMOJI_FILES = '), j1 = src.indexOf(';\n', j0);
src = src.slice(0, j0) + 'const EMOJI_FILES = ' + JSON.stringify(table) + src.slice(j1);
fs.writeFileSync(game, src);
fs.writeFileSync(path.join(out, 'LICENSE-NOTE.txt'), 'Emoji pictures in this folder are from OpenMoji (https://openmoji.org), the open-source emoji project.\nLicense: CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/).\n');
// pictures used only in the styling (url(emoji/...)) are kept too
for (const u of src.match(/url\(emoji\/[^)]+\)/g) || []) { const f = u.slice(10, -1); if (fs.existsSync(path.join(om, f))) fs.copyFileSync(path.join(om, f), path.join(out, f)); }
const left = (src.match(/url\(emoji\/[^)]+\)/g) || []).filter(u => !fs.existsSync(path.join(out, u.slice(10, -1))));
console.log('emoji:', found.length, '| files:', new Set(Object.values(table)).size, '| missing in OpenMoji:', missing.join(', ') || 'none', '| broken CSS links:', left.join(' ') || 'none');
