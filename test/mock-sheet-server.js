// Simulates Google Sheets + Apps Script web app well enough to run class-sheet-script.gs unchanged.
const fs = require('fs'), http = require('http'), vm = require('vm');
const sheets = {};
function Sheet(name) {
  this.name = name; this.data = [];
}
Sheet.prototype.getLastRow = function () { let n = this.data.length; while (n > 0 && this.data[n - 1].every(v => v === '' || v == null)) n--; return n; };
Sheet.prototype.getLastColumn = function () { return Math.max(0, ...this.data.map(r => { let n = r.length; while (n > 0 && (r[n - 1] === '' || r[n - 1] == null)) n--; return n; })); };
Sheet.prototype.getDataRange = function () { return this.getRange(1, 1, this.getLastRow() || 1, this.getLastColumn() || 1); };
Sheet.prototype.clearContents = function () { this.data = []; return this; };
Sheet.prototype.getParent = function () { return ss; };
Sheet.prototype.getRange = function (r, c, nr = 1, nc = 1) {
  const sh = this;
  if (typeof r === 'string') return { setNumberFormat() { return this; } };
  return {
    getValues() { return Array.from({ length: nr }, (_, i) => Array.from({ length: nc }, (_, j) => { const row = sh.data[r - 1 + i] || []; const v = row[c - 1 + j]; return v == null ? '' : v; })); },
    getValue() { return this.getValues()[0][0]; },
    setValue(v) { return this.setValues([[v]]); },
    setValues(vals) { vals.forEach((row, i) => { const ri = r - 1 + i; while (sh.data.length <= ri) sh.data.push([]); row.forEach((v, j) => { sh.data[ri][c - 1 + j] = v; }); }); return this; },
    setFontWeight() { return this; }, setNumberFormat() { return this; }, insertCheckboxes() { return this; },
    setBackgrounds(b) { sh.bg = b; return this; },
    clearContent() { for (let i = 0; i < nr; i++) { const row = sh.data[r - 1 + i]; if (row) for (let j = 0; j < nc; j++) row[c - 1 + j] = ''; } return this; }
  };
};
Sheet.prototype.deleteRow = function (r) { this.data.splice(r - 1, 1); return this; };
Sheet.prototype.deleteRows = function (r, n) { this.data.splice(r - 1, n); return this; };
['setFrozenRows', 'setFrozenColumns', 'setColumnWidth', 'hideSheet', 'hideColumns'].forEach(m => Sheet.prototype[m] = function () { return this; });
const ss = { getSheetByName: n => sheets[n] || null, insertSheet: n => (sheets[n] = new Sheet(n)), getName: () => 'Number Island', copy: name => { copies.push(name); return { getName: () => name }; } };
const copies = [];
// a clock that tests can move: GET /clock?t=<ISO time>
let clockOffset = 0;
class FakeDate extends Date { constructor(...a) { if (a.length) super(...a); else super(Date.now() + clockOffset); } static now() { return Date.now() + clockOffset; } }
const ctx = {
  SpreadsheetApp: { getActiveSpreadsheet: () => ss, getUi: () => ({ createMenu: () => ({ addItem() { return this; }, addToUi() {} }), alert: () => 'YES', ButtonSet: { YES_NO: 1 }, Button: { YES: 'YES' } }) },
  Utilities: { formatDate: (d, tz, f) => { // Seoul time (UTC+9); supports the patterns the script uses
      const k = new Date(d.getTime() + 9 * 3600000), p = n => String(n).padStart(2, '0');
      const Y = k.getUTCFullYear(), M = p(k.getUTCMonth() + 1), D = p(k.getUTCDate()), H = k.getUTCHours(), mi = p(k.getUTCMinutes());
      if (!f || f === 'yyyy-MM-dd') return `${Y}-${M}-${D}`;
      if (f === 'u') return String(k.getUTCDay() || 7);
      if (f === 'HH:mm') return `${p(H)}:${mi}`;
      if (f === 'H:mm') return `${H}:${mi}`;
      return `${Y}-${M}-${D}`;
    }, getUuid: () => require('crypto').randomUUID() }, Session: { getScriptTimeZone: () => 'Asia/Seoul' },
  LockService: { getScriptLock: () => ({ waitLock() {}, releaseLock() {} }) },
  ContentService: { MimeType: { JSON: 'json' }, createTextOutput: t => ({ text: t, setMimeType() { return this; } }) },
  JSON, Date: FakeDate, String, Math
};
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(process.argv[2], 'utf8'), ctx);
ctx.setup();
sheets['Roster'].getRange(2, 1, 3, 2).setValues([['Alex', '111'], ['Sam', '007'], ['Kim', '']]);
let down = false; const stash = {};
http.createServer((req, res) => {
  const cors = { 'Access-Control-Allow-Origin': '*' };
  if (req.url.startsWith('/dump')) { res.writeHead(200, { ...cors, 'Content-Type': 'application/json' }); return res.end(JSON.stringify(Object.fromEntries(Object.entries(sheets).map(([k, v]) => [k, v.data])))); }
  if (req.url.startsWith('/set')) { const q = new URL(req.url, 'http://x').searchParams; const sh = sheets[q.get('tab')]; sh.data[+q.get('r') - 1][+q.get('c') - 1] = q.get('v') === 'true' ? true : q.get('v') === 'false' ? false : q.get('v'); res.writeHead(200, cors); return res.end('ok'); }
  if (req.url.startsWith('/newyear')) { ctx.newSchoolYear(); res.writeHead(200, cors); return res.end(JSON.stringify(copies)); }
  if (req.url.startsWith('/clock')) { const t = new URL(req.url, 'http://x').searchParams.get('t'); clockOffset = t ? new Date(t).getTime() - Date.now() : 0; res.writeHead(200, cors); return res.end('ok'); }
  if (req.url.startsWith('/down')) { down = true; res.writeHead(200, cors); return res.end('down'); }
  if (req.url.startsWith('/up')) { down = false; res.writeHead(200, cors); return res.end('up'); }
  if (req.url.startsWith('/echo')) { const id = req.url.split('id=')[1]; res.writeHead(200, { ...cors, 'Content-Type': 'application/json' }); return res.end(stash[id]); }
  if (down) { req.socket.destroy(); return; }
  let body = ''; req.on('data', d => body += d); req.on('end', () => {
    const out = req.method === 'POST' ? ctx.doPost({ postData: { contents: body } }) : ctx.doGet();
    const id = Math.random().toString(36).slice(2); stash[id] = out.text;
    // Like Apps Script: no CORS on the first response, just a redirect to a CORS-enabled echo URL
    res.writeHead(302, { ...cors, Location: '/echo?id=' + id }); res.end();
  });
}).listen(8765, () => console.log('mock sheet on 8765'));
