// Build step: puts every emoji picture inside the built game file, so each tablet downloads one file.
// usage: node embed_emoji.js built.html   [minified-emoji-folder]  (made from emoji/ by build.sh)
const fs = require('fs'), path = require('path');
const out = process.argv[2], min = process.argv[3] || require('path').join(__dirname, '..', '.emoji-min');
let s = fs.readFileSync(out, 'utf8');
const uri = f => 'data:image/svg+xml,' + fs.readFileSync(path.join(min, f), 'utf8').replace(/"/g, "'").replace(/[%#<>{}\n\r]/g, c => encodeURIComponent(c));
const files = fs.readdirSync(min).filter(f => f.endsWith('.svg')), data = {};
files.forEach(f => { data[f] = uri(f); });
const marker = 'const EMOJI_DATA = {};';
if (!s.includes(marker)) throw new Error('marker missing');
s = s.replace(marker, () => 'const EMOJI_DATA = ' + JSON.stringify(data) + ';');
s = s.replace(/url\(emoji\/([^)]+)\)/g, (m, f) => data[f] ? `url("${data[f]}")` : m);
const used = [...new Set(Object.values(JSON.parse(s.match(/const EMOJI_FILES = (\{.*?\});/)[1])))];
const missing = used.filter(f => !data[f]);
fs.writeFileSync(out, s);
console.log('embedded', files.length, 'pictures | file size', (s.length / 1024 | 0) + ' KB | missing:', missing.join(' ') || 'none');
