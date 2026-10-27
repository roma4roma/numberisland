/**
 * Number Island: class progress sheet
 * ---------------------------------------------------------------
 * Paste this whole file into Extensions > Apps Script in your Google Sheet,
 * click Save, then run "setup" once (see the setup guide).
 *
 * Tabs it creates:
 *   Roster          You type each student's name and an optional secret code.
 *                   Column C: type a number like 50 or -30 to add or take away coins.
 *                   It's added the next time that student's game checks in, then the cell clears
 *                   (only after the game confirms the coins arrived, so a gift is never lost or doubled).
 *   Class Progress  One row per student: level and recent accuracy for every skill.
 *   Activity        One row each time a student finishes a game.
 *   Games           Tick a box to unlock a game for every student. Untick to lock it.
 *   Boss Battles    How many hits each student landed on each week's boss.
 *   Needs Help      Who's struggling, which facts they keep missing, and minutes practiced this week.
 *   Settings        Boss Battle day, boss health, coin rate, island visits, Today's Challenge,
 *                   and which numbers the fact games use (Fact Runner, Math Driver, Memory Reef, Boss Battle).
 *   Island Reactions  Who left which reaction on whose island (one per visitor per island).
 *
 * The "Number Island" menu at the top of the sheet has "Start a new school year…".
 *   Save Data       The game's save files. Hidden. Please don't edit it.
 */

var TABS = { roster: 'Roster', progress: 'Class Progress', help: 'Needs Help', activity: 'Activity', games: 'Games', boss: 'Boss Battles', settings: 'Settings', data: 'Save Data', reacts: 'Island Reactions' };
var REACTIONS = ['⭐', '❤️', '🦝', '🔥', '🤩'];
var BOSS_HP_PER_STUDENT = 100; // starting value; change it any time on the Settings tab

// The games in Number Island. Games the app adds later are added to the Games tab automatically, locked.
var DEFAULT_GAMES = [
  ['driver', 'Math Driver', 'Facts: ×, ÷, + and −'],
  ['runner', 'Fact Runner', 'Multiplication facts'],
  ['memory', 'Memory Reef', 'Multiplication facts'],
  ['arrays', 'Array Garden', 'Arrays and area'],
  ['tens', 'Tens Tower', 'Multiplying by multiples of 10'],
  ['partial', 'Area Builder', 'Partial products and area models'],
  ['estimate', 'Estimation Station', 'Estimating products'],
  ['column', 'Column Cliffs', 'Multi-digit addition and subtraction'],
  ['divide', 'Treasure Split', 'Division with remainders'],
  ['story', 'Story Problems', 'Multi-step word problems'],
  ['boss', 'Boss Battle', 'Whole-class team-up on mixed facts (great for Fun Friday)'],
  ['factors', 'Factor Forest', 'Topic 7: factors, multiples, prime and composite'],
  ['fracbakery', 'Fraction Bakery', 'Topic 8: equivalent fractions, comparing and ordering'],
  ['frackitchen', 'Fraction Kitchen', 'Topics 9-10: adding and subtracting fractions, mixed numbers, multiplying by a whole number'],
  ['lineplot', 'Line Plot Lab', 'Topic 11: line plots with fractions'],
  ['decimals', 'Decimal Docks', 'Topic 12: decimals, tenths and hundredths, money'],
  ['measure', 'Measure Mountain', 'Topic 13: unit conversions, area and perimeter'],
  ['patterns', 'Pattern Path', 'Topic 14: number patterns and rules'],
  ['angles', 'Angle Arcade', 'Topic 15: angles and angle measurement'],
  ['shapes', 'Shape Safari', 'Topic 16: lines, angles and shapes']
];
// Games that start locked even on a brand-new sheet
var START_LOCKED = ['boss', 'factors', 'fracbakery', 'frackitchen', 'lineplot', 'decimals', 'measure', 'patterns', 'angles', 'shapes'];

function onOpen() {
  SpreadsheetApp.getUi().createMenu('Number Island')
    .addItem('Set up tabs', 'setup')
    .addItem('Start a new school year…', 'newSchoolYear')
    .addToUi();
}

/** Run this once from the Apps Script editor. Safe to run again. */
function setup() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var roster = tab_(ss, TABS.roster, ['Student name', 'Secret code (optional)']);
  rosterCoinColumn_(roster);
  roster.getRange('B:B').setNumberFormat('@'); // keep codes like 007 exactly as typed
  roster.setColumnWidth(1, 200); roster.setColumnWidth(2, 180);
  if (roster.getLastRow() < 2) roster.getRange(2, 1, 1, 2).setValues([['Sample Student', '123']]);
  tab_(ss, TABS.progress, ['Student', 'Last played']);
  tab_(ss, TABS.activity, ['Time', 'Student', 'Game', 'Result', 'Stars', 'Skill', 'Skill level after']);
  setupGames_(ss, null);
  settingsTab_(ss);
  var data = tab_(ss, TABS.data, ['Student', 'Updated', 'Saved game (do not edit)']);
  try { data.hideSheet(); } catch (e) {}
}

function tab_(ss, name, headers) {
  var sh = ss.getSheetByName(name);
  if (!sh) sh = ss.insertSheet(name);
  if (sh.getLastRow() === 0) {
    sh.getRange(1, 1, 1, headers.length).setValues([headers]).setFontWeight('bold');
    sh.setFrozenRows(1);
  }
  return sh;
}

/** Lets the game's "Test connection" button check the link. */
function doGet() {
  return out_({ ok: true, app: 'number-island', v: 1 });
}

/** The game sends everything here. */
function doPost(e) {
  var req;
  try { req = JSON.parse(e.postData.contents); } catch (err) { return out_({ ok: false, error: 'bad_request' }); }
  var lock = LockService.getScriptLock();
  try {
    lock.waitLock(20000);
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    if (!ss.getSheetByName(TABS.roster)) setup();
    setupGames_(ss, null); // makes sure every game in this script is listed
    if (req.games && req.games.length) setupGames_(ss, req.games); // and any newer ones the app knows about
    var who = findStudent_(ss, req.name, req.code);
    if (who === 'bad_code') return out_({ ok: false, error: 'bad_code' });
    if (!who) return out_({ ok: false, error: 'not_on_roster' });
    var coinAdjust = 0, coinId = '';
    var staleSave = req.action === 'save' && req.profile && (Number(req.profile.dataVersion) || 1) < readSettings_(ss).version;
    if (req.coinAck && !staleSave) ackCoinAdjust_(ss, who, String(req.coinAck)); // the game confirmed it added these coins
    if (Number(req.coinV) >= 2 && !staleSave && (req.action === 'load' || req.action === 'boss' || req.action === 'save')) {
      var ca = peekCoinAdjust_(ss, who); if (ca) { coinAdjust = ca.n; coinId = ca.id; }
    }
    if (req.action === 'load') return out_({ ok: true, name: who, profile: loadSave_(ss, who), games: readGames_(ss), settings: readSettings_(ss), coinAdjust: coinAdjust, coinId: coinId, myReactions: reactionsFor_(ss, who), boards: boards_(ss) });
    if (req.action === 'setCode') { // a student changes their own secret code (already checked their current one above)
      if (!readSettings_(ss).codeChange) return out_({ ok: false, error: 'off' });
      var nc = String(req.newCode == null ? '' : req.newCode).trim();
      if (!/^\d{3,8}$/.test(nc)) return out_({ ok: false, error: 'bad_new_code' });
      setRosterCode_(ss, who, nc);
      var act = ss.getSheetByName(TABS.activity);
      if (act) act.getRange(act.getLastRow() + 1, 1, 1, 7).setValues([[new Date(), who, 'Secret code', 'Student changed their code', '', '', '']]);
      return out_({ ok: true });
    }
    if (req.action === 'islands') {
      if (!readSettings_(ss).islandVisits) return out_({ ok: true, off: true });
      return out_({ ok: true, islands: allIslands_(ss, who) });
    }
    if (req.action === 'react') {
      if (!readSettings_(ss).islandVisits) return out_({ ok: true, off: true });
      return out_(react_(ss, who, req.target, req.reaction));
    }
    if (req.action === 'boss') {
      if (req.week && req.hits > 0) addBossHits_(ss, req.week, who, req.hits);
      return out_({ ok: true, boss: bossStatus_(ss, req.week, who), games: readGames_(ss), settings: readSettings_(ss), coinAdjust: coinAdjust, coinId: coinId });
    }
    if (req.action === 'save') {
      var st = readSettings_(ss);
      if (req.profile && (Number(req.profile.dataVersion) || 1) < st.version) {
        return out_({ ok: true, stale: true, settings: st, games: readGames_(ss) }); // saved before a new school year began
      }
      if (req.boss && req.boss.week && req.boss.hits > 0) addBossHits_(ss, req.boss.week, who, req.boss.hits);
      if (req.profile) writeSave_(ss, who, req.profile);
      if (req.summary) { writeSummary_(ss, who, req.summary); buildNeedsHelp_(ss); }
      if (req.activity && req.activity.length) writeActivity_(ss, who, req.activity);
      return out_({ ok: true, games: readGames_(ss), settings: readSettings_(ss), coinAdjust: coinAdjust, coinId: coinId, boss: req.boss && req.boss.week ? bossStatus_(ss, req.boss.week, who) : null, myReactions: reactionsFor_(ss, who), boards: boards_(ss) });
    }
    return out_({ ok: false, error: 'bad_action' });
  } catch (err) {
    return out_({ ok: false, error: 'server', message: String(err) });
  } finally {
    try { lock.releaseLock(); } catch (e2) {}
  }
}

function out_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}
function normName_(s) { return String(s == null ? '' : s).trim().replace(/\s+/g, ' ').toLowerCase(); }
function normCode_(s) { return String(s == null ? '' : s).trim().replace(/^0+(?=\d)/, ''); }

/** Returns the roster spelling of the name, 'bad_code', or null. */
function findStudent_(ss, name, code) {
  var want = normName_(name);
  if (!want) return null;
  var sh = ss.getSheetByName(TABS.roster);
  var last = sh.getLastRow();
  if (last < 2) return null;
  var rows = sh.getRange(2, 1, last - 1, 2).getValues();
  for (var i = 0; i < rows.length; i++) {
    if (normName_(rows[i][0]) === want) {
      var needed = normCode_(rows[i][1]);
      if (needed && needed !== normCode_(code)) return 'bad_code';
      return String(rows[i][0]).trim().replace(/\s+/g, ' ');
    }
  }
  return null;
}

function rowFor_(sh, who) {
  var last = sh.getLastRow();
  if (last < 2) return -1;
  var names = sh.getRange(2, 1, last - 1, 1).getValues();
  var want = normName_(who);
  for (var i = 0; i < names.length; i++) if (normName_(names[i][0]) === want) return i + 2;
  return -1;
}

function loadSave_(ss, who) {
  var sh = ss.getSheetByName(TABS.data);
  var r = rowFor_(sh, who);
  if (r < 0) return null;
  try { return JSON.parse(sh.getRange(r, 3).getValue()); } catch (e) { return null; }
}

function writeSave_(ss, who, profile) {
  var sh = ss.getSheetByName(TABS.data);
  var r = rowFor_(sh, who);
  if (r < 0) r = sh.getLastRow() + 1;
  sh.getRange(r, 1, 1, 3).setValues([[who, new Date(), JSON.stringify(profile)]]);
}

/** summary = { cols: [column names], vals: [values] } */
function writeSummary_(ss, who, summary) {
  var sh = ss.getSheetByName(TABS.progress);
  var header = ['Student', 'Last played'].concat(summary.cols);
  var current = sh.getRange(1, 1, 1, header.length).getValues()[0];
  if (current.join('|') !== header.join('|')) {
    sh.getRange(1, 1, 1, header.length).setValues([header]).setFontWeight('bold');
    sh.setFrozenRows(1); sh.setFrozenColumns(1);
  }
  var r = rowFor_(sh, who);
  if (r < 0) r = sh.getLastRow() + 1;
  var row = [who, new Date()].concat(summary.vals);
  sh.getRange(r, 1, 1, row.length).setValues([row]);
  // Color the recent-accuracy cells: green 80%+, yellow 60-79%, red under 60%
  var colors = row.map(function (v, i) {
    if (header[i].indexOf('%') < 0 || v === '' || v === null) return null;
    return v >= 80 ? '#D5F5E3' : v >= 60 ? '#FFF0B8' : '#FFE1DB';
  });
  sh.getRange(r, 1, 1, row.length).setBackgrounds([colors]);
}

function writeActivity_(ss, who, list) {
  var sh = ss.getSheetByName(TABS.activity);
  var rows = list.slice(0, 50).map(function (a) {
    return [a.time ? new Date(a.time) : new Date(), who, a.game || '', a.result || '', a.stars || '', a.skill || '', a.level || ''];
  });
  if (rows.length) sh.getRange(sh.getLastRow() + 1, 1, rows.length, 7).setValues(rows);
}

/** Makes the Games tab and adds any games it doesn't list yet. */
function setupGames_(ss, fromApp) {
  var sh = tab_(ss, TABS.games, ['Game', 'Unlocked', 'What it practices', 'Game ID (do not change)']);
  sh.setColumnWidth(1, 170); sh.setColumnWidth(3, 300);
  var last = sh.getLastRow();
  var have = {};
  if (last >= 2) sh.getRange(2, 4, last - 1, 1).getValues().forEach(function (r) { have[String(r[0])] = true; });
  var firstTime = last < 2;
  var list = fromApp ? fromApp.map(function (g) { return [g.id, g.name, g.practices || '']; }) : DEFAULT_GAMES;
  var add = [];
  list.forEach(function (g) {
    if (!g[0] || have[g[0]]) return;
    have[g[0]] = true;
    add.push([g[1], firstTime && START_LOCKED.indexOf(g[0]) < 0, g[2], g[0]]); // games added later start locked
  });
  if (add.length) {
    var start = sh.getLastRow() + 1;
    sh.getRange(start, 1, add.length, 4).setValues(add);
    sh.getRange(start, 2, add.length, 1).insertCheckboxes();
  }
}

/** { gameId: true/false } from the Games tab. */
function readGames_(ss) {
  var sh = ss.getSheetByName(TABS.games), out = {};
  if (!sh || sh.getLastRow() < 2) return out;
  sh.getRange(2, 1, sh.getLastRow() - 1, 4).getValues().forEach(function (r) {
    if (r[3]) out[String(r[3])] = r[1] === true || String(r[1]).toUpperCase() === 'TRUE';
  });
  return out;
}

/* ---------- Boss Battle: one shared health bar per week for the whole class ---------- */
function bossTab_(ss) { return tab_(ss, TABS.boss, ['Week', 'Student', 'Hits']); }
function bossHpPerStudent_(sh) { return readSettings_(sh.getParent()).bossHp; }

function addBossHits_(ss, week, who, hits) {
  hits = Math.max(0, Math.min(500, Math.round(Number(hits) || 0)));
  if (!hits) return;
  var sh = bossTab_(ss), last = sh.getLastRow();
  if (last >= 2) {
    var rows = sh.getRange(2, 1, last - 1, 3).getValues();
    for (var i = 0; i < rows.length; i++) {
      if (String(rows[i][0]) === String(week) && normName_(rows[i][1]) === normName_(who)) {
        sh.getRange(i + 2, 3).setValue((Number(rows[i][2]) || 0) + hits);
        return;
      }
    }
  }
  sh.getRange(last + 1, 1, 1, 3).setValues([[String(week), who, hits]]);
}

function bossStatus_(ss, week, who) {
  var sh = bossTab_(ss), last = sh.getLastRow(), total = 0, mine = 0, helpers = 0;
  if (last >= 2) sh.getRange(2, 1, last - 1, 3).getValues().forEach(function (r) {
    if (String(r[0]) !== String(week)) return;
    var h = Number(r[2]) || 0; total += h; if (h > 0) helpers++;
    if (normName_(r[1]) === normName_(who)) mine += h;
  });
  var roster = ss.getSheetByName(TABS.roster), students = 0;
  if (roster.getLastRow() >= 2) roster.getRange(2, 1, roster.getLastRow() - 1, 1).getValues().forEach(function (r) { if (String(r[0]).trim()) students++; });
  return { week: String(week), total: total, max: Math.max(60, Math.round(students * bossHpPerStudent_(sh))), mine: mine, helpers: helpers };
}

/* ---------- Settings tab ---------- */
// Rows added in later versions (row 6 onward). They're filled in automatically if missing.
var EXTRA_ROWS = [
  ['Island visits', 'On', 'On = students can visit classmates\' islands and leave a reaction (⭐ ❤️ 🦝 🔥 🤩). Off = turn it off.'],
  ['Today\'s challenge', 'Auto', 'Auto = a different practice game each day. Or type a game name, like Story Problems or Tens Tower. Off = no challenge. The challenge game pays double coins all day, plus a bonus for the first round.'],
  ['× and ÷ facts: first number', 'Auto', 'Auto = each student\'s level picks the facts. Or type numbers: 2-9, or 6-9, or 3,4,6,7,8. For two-digit facts (no single digits) try 11-20.'],
  ['× and ÷ facts: second number', 'Auto', 'The other number in each fact. Example: first number 11-20 and second number 2-9 gives facts like 14 × 6 and 84 ÷ 6.'],
  ['+ and − numbers', 'Auto', 'Auto = by level. Or a range like 10-99 (two-digit numbers) or 100-999 (three-digit numbers). Used in Math Driver and Boss Battle.'],
  ['Play days', 'Mon-Fri', 'Days students can play. Examples: Mon-Fri, or Mon,Tue,Thu, or Every day.'],
  ['Play hours', '8:00-16:00', 'Times students can play on those days. Examples: 8:30-15:30, or 9:00-12:00, 13:00-15:00 (two times a day). Any time = no limit.'],
  ['Can always play', '', 'Names that can play any time, like a test account. Separate names with commas. These names are also left off the top 3 lists.'],
  ['Top 3 lists', 'On', 'On = each game shows this week\'s top 3 (it starts fresh every Monday). Off = hide them.'],
  ['Hide from top 3', '', 'Other names to leave off the top 3 lists. Separate names with commas.'],
  ['Students can change their code', 'On', 'On = students can change their own secret code from the home screen (they must type their current code first). The new code shows on the Roster, so you can always look it up. Off = only you can change codes.'],
  ['Boss questions', 'Mixed', 'Mixed = ×, ÷, + and − (plus tens × tens once Tens Tower is unlocked). Or choose: × ÷  or  × only  or  + −  or  ×, ÷, tens.'],
  ['Boss × and ÷: first number', 'Same', 'Same = use the × and ÷ numbers above. Auto = by each student\'s level. Or type numbers like 6-9 or 11-20 just for Boss Battle.'],
  ['Boss × and ÷: second number', 'Same', 'The other number in each Boss Battle fact. Example: first 11-20 and second 2-9 gives 14 × 6 and 84 ÷ 6.'],
  ['Boss + and − numbers', 'Same', 'Same = use the + and − numbers above. Auto = by level. Or a range like 100-999 just for Boss Battle.'],
  ['Boss Battle hours', 'All day', 'All day = Boss Battle is open all day on Boss Battle day. Or a time like 13:00-14:00 (or 1pm-2pm). Before then, students see a countdown.']
];
function settingsTab_(ss) {
  var sh = ss.getSheetByName(TABS.settings);
  if (sh) {
    EXTRA_ROWS.forEach(function (row, i) {
      if (String(sh.getRange(6 + i, 1).getValue()) !== row[0]) {
        sh.getRange(6 + i, 2).setNumberFormat('@'); // plain text, so 2-9 doesn't turn into a date
        sh.getRange(6 + i, 1, 1, 3).setValues([row]);
      }
    });
    return sh;
  }
  var hp = BOSS_HP_PER_STUDENT, boss = ss.getSheetByName(TABS.boss);
  if (boss) { var old = Number(boss.getRange(1, 6).getValue()); if (old > 0) hp = old; } // keep a value set in the older version
  sh = ss.insertSheet(TABS.settings);
  sh.getRange(1, 1, 5, 3).setValues([
    ['Setting', 'Value', 'What it does'],
    ['Boss Battle day', 'Friday', 'The day Boss Battle opens. Type Monday, Tuesday, Wednesday, Thursday, Friday, or Any day.'],
    ['Boss HP per student', hp, 'How tough the weekly boss is. A bigger number makes it harder.'],
    ['Coin rate', 1, '1 = normal coins. 2 = double coins. 0.5 = half coins.'],
    ['Data version (do not change)', 1, 'Goes up by itself when you start a new school year.']
  ]);
  sh.getRange(6, 2, EXTRA_ROWS.length, 1).setNumberFormat('@');
  sh.getRange(6, 1, EXTRA_ROWS.length, 3).setValues(EXTRA_ROWS);
  sh.getRange(1, 1, 1, 3).setFontWeight('bold'); sh.setFrozenRows(1);
  sh.setColumnWidth(1, 230); sh.setColumnWidth(2, 120); sh.setColumnWidth(3, 520);
  return sh;
}
function readSettings_(ss) {
  var v = settingsTab_(ss).getRange(2, 2, 4 + EXTRA_ROWS.length, 1).getValues().map(function (r) { return r[0]; });
  return { bossDay: String(v[0] || 'Friday'), bossHp: Number(v[1]) > 0 ? Number(v[1]) : BOSS_HP_PER_STUDENT,
           coinRate: Number(v[2]) > 0 ? Number(v[2]) : 1, version: Number(v[3]) > 0 ? Number(v[3]) : 1,
           islandVisits: !/^(off|no|false|0)$/i.test(String(v[4]).trim()),
           challenge: text_(v[5], 'Auto'), multA: text_(v[6], 'Auto'), multB: text_(v[7], 'Auto'), addRange: text_(v[8], 'Auto'),
           playDays: text_(v[9], 'Every day'), playHours: text_(v[10], 'Any time'), alwaysPlay: text_(v[11], ''),
           top3: !/^(off|no|false|0)$/i.test(String(v[12]).trim()), hideTop3: text_(v[13], ''),
           codeChange: !/^(off|no|false|0)$/i.test(String(v[14]).trim()),
           bossTypes: text_(v[15], 'Mixed'), bossA: text_(v[16], 'Same'), bossB: text_(v[17], 'Same'), bossAdd: text_(v[18], 'Same'),
           bossHours: text_(v[19], 'All day') };
}
/** Cell to text. If Sheets turned "2-9" into a date (Feb 9), turn it back into "2-9". */
function text_(x, dflt) {
  if (x instanceof Date) {
    if (x.getFullYear() < 1901) return Utilities.formatDate(x, Session.getScriptTimeZone(), 'H:mm'); // a time like 8:30 typed into the cell
    return (x.getMonth() + 1) + '-' + x.getDate();
  }
  var t = String(x == null ? '' : x).trim();
  return t || dflt;
}

/* ---------- Needs Help tab, rebuilt from Class Progress after every save ---------- */
function isoWeek_(d) {
  var t = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate())), day = t.getUTCDay() || 7;
  t.setUTCDate(t.getUTCDate() + 4 - day);
  var y0 = new Date(Date.UTC(t.getUTCFullYear(), 0, 1)), n = Math.ceil(((t - y0) / 86400000 + 1) / 7);
  return t.getUTCFullYear() + '-W' + (n < 10 ? '0' : '') + n;
}
function buildNeedsHelp_(ss) {
  var src = ss.getSheetByName(TABS.progress);
  if (!src || src.getLastRow() < 2) return;
  var data = src.getDataRange().getValues(), h = data[0];
  var iS = h.indexOf('Student'), iL = h.indexOf('Last played'), iN = h.indexOf('Needs help with'),
      iT = h.indexOf('Tricky facts'), iM = h.indexOf('Minutes this week'), iW = h.indexOf('Minutes week');
  if (iN < 0) return;
  var week = isoWeek_(new Date());
  var rows = data.slice(1).filter(function (r) { return r[iS]; }).map(function (r) {
    var mins = String(r[iW]) === week ? Number(r[iM]) || 0 : 0;
    return [r[iS], r[iN] || '', r[iT] || '', mins, r[iL]];
  });
  var count = function (x) { return x ? String(x).split(',').length : 0; };
  rows.sort(function (a, b) { return count(b[1]) - count(a[1]) || a[3] - b[3]; });
  var sh = ss.getSheetByName(TABS.help) || ss.insertSheet(TABS.help, 1);
  sh.clearContents();
  var out = [['Student', 'Needs help with (under 60% lately)', 'Tricky facts (missed lately)', 'Minutes practiced this week', 'Last played']].concat(rows);
  sh.getRange(1, 1, out.length, 5).setValues(out);
  sh.getRange(1, 1, 1, 5).setFontWeight('bold'); sh.setFrozenRows(1);
  sh.getRange(1, 1, out.length, 5).setBackgrounds(out.map(function (r, i) {
    var c = i === 0 ? null : r[1] ? '#FFE1DB' : r[3] < 20 ? '#FFF0B8' : '#D5F5E3';
    return [c, c, c, c, c];
  }));
}

/* ---------- New school year ---------- */
function newSchoolYear() {
  var ui = SpreadsheetApp.getUi();
  var answer = ui.alert('Start a new school year?',
    'This saves a copy of this whole spreadsheet (with all of this year\'s progress) in your Google Drive. ' +
    'Then it clears Class Progress, Needs Help, Activity, Boss Battles and saved games here, so every student starts fresh. ' +
    'Your Roster, Games and Settings stay. Continue?', ui.ButtonSet.YES_NO);
  if (answer !== ui.Button.YES) return;
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var copy = ss.copy(ss.getName() + ' (archive ' + Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyy-MM-dd') + ')');
  [TABS.progress, TABS.help, TABS.activity, TABS.boss, TABS.data, TABS.reacts].forEach(function (name) {
    var sh = ss.getSheetByName(name);
    if (sh && sh.getLastRow() > 1) sh.getRange(2, 1, sh.getLastRow() - 1, Math.max(1, sh.getLastColumn())).clearContent();
  });
  var st = settingsTab_(ss);
  st.getRange(5, 2).setValue((Number(st.getRange(5, 2).getValue()) || 1) + 1);
  ui.alert('Done! This year\'s progress was saved as "' + copy.getName() + '" in your Google Drive. Now update the Roster with your new class.');
}

/* ---------- Teacher coin adjustments (Roster column C) ---------- */
function rosterCoinColumn_(roster) {
  if (String(roster.getRange(1, 3).getValue()) !== 'Add or remove coins') {
    roster.getRange(1, 3).setValue('Add or remove coins').setFontWeight('bold');
    roster.setColumnWidth(3, 180);
  }
  if (String(roster.getRange(1, 4).getValue()) !== 'Coin check (automatic)') {
    roster.getRange(1, 4).setValue('Coin check (automatic)');
    try { roster.hideColumns(4); } catch (e) {}
  }
}
/** Reads (but does not clear) a student's coin adjustment: { n, id } or null.
 *  A hidden column D remembers an id for the current amount, so the game can confirm it. */
function peekCoinAdjust_(ss, who) {
  var sh = ss.getSheetByName(TABS.roster); rosterCoinColumn_(sh);
  var last = sh.getLastRow(); if (last < 2) return null;
  var rows = sh.getRange(2, 1, last - 1, 4).getValues();
  for (var i = 0; i < rows.length; i++) {
    if (normName_(rows[i][0]) !== normName_(who)) continue;
    var n = Math.round(Number(String(rows[i][2]).replace(/[^0-9.\-]/g, '')) || 0);
    if (!n) { if (rows[i][3]) sh.getRange(i + 2, 4).setValue(''); return null; }
    n = Math.max(-100000, Math.min(100000, n));
    var tag = String(rows[i][3] || ''), parts = tag.split('|');
    if (parts.length !== 2 || Number(parts[0]) !== n) { tag = n + '|' + Utilities.getUuid(); sh.getRange(i + 2, 4).setValue(tag); }
    return { n: n, id: tag };
  }
  return null;
}
/** The game added the coins: clear the cell and note it on the Activity tab. */
function ackCoinAdjust_(ss, who, id) {
  var sh = ss.getSheetByName(TABS.roster);
  var last = sh.getLastRow(); if (last < 2) return;
  var rows = sh.getRange(2, 1, last - 1, 4).getValues();
  for (var i = 0; i < rows.length; i++) {
    if (normName_(rows[i][0]) !== normName_(who) || String(rows[i][3]) !== id) continue;
    var n = Number(id.split('|')[0]) || 0;
    sh.getRange(i + 2, 3, 1, 2).setValues([['', '']]);
    var act = ss.getSheetByName(TABS.activity);
    if (act) act.getRange(act.getLastRow() + 1, 1, 1, 7).setValues([[new Date(), who, 'Teacher', 'Coins ' + (n > 0 ? '+' : '') + n, '', '', '']]);
    return;
  }
}

/* ---------- Island visits: see classmates' islands and leave one reaction each ---------- */
function reactTab_(ss) { return tab_(ss, TABS.reacts, ['Visitor', 'Island owner', 'Reaction', 'Time']); }
function reactRows_(ss) {
  var sh = ss.getSheetByName(TABS.reacts);
  if (!sh || sh.getLastRow() < 2) return [];
  return sh.getRange(2, 1, sh.getLastRow() - 1, 3).getValues();
}
/** { '⭐': 3, '❤️': 1 } for one student's island. */
function reactionsFor_(ss, who) {
  var out = {};
  reactRows_(ss).forEach(function (r) { if (normName_(r[1]) === normName_(who) && REACTIONS.indexOf(String(r[2])) >= 0) out[r[2]] = (out[r[2]] || 0) + 1; });
  return out;
}
/** Every saved island: just the animal and the island things (no coins, levels or codes). */
function allIslands_(ss, who) {
  var sh = ss.getSheetByName(TABS.data);
  if (!sh || sh.getLastRow() < 2) return [];
  var rows = reactRows_(ss), list = [];
  sh.getRange(2, 1, sh.getLastRow() - 1, 3).getValues().forEach(function (r) {
    if (!r[0]) return;
    var p; try { p = JSON.parse(r[2]); } catch (e) { return; }
    if (!p) return;
    var reacts = {}, mine = null, owner = normName_(r[0]);
    rows.forEach(function (x) {
      if (normName_(x[1]) !== owner) return;
      reacts[x[2]] = (reacts[x[2]] || 0) + 1;
      if (normName_(x[0]) === normName_(who)) mine = String(x[2]);
    });
    list.push({ name: String(r[0]), me: owner === normName_(who), avatar: p.avatar || '🙂',
                owned: p.owned || [], islandCount: p.islandCount || {}, islandPos: p.islandPos || {}, reacts: reacts, mine: mine });
  });
  list.sort(function (a, b) { return a.name.localeCompare(b.name); });
  return list;
}
/** One reaction per visitor per island. Sending the same one again takes it back. */
function react_(ss, who, target, reaction) {
  reaction = String(reaction || '');
  if (REACTIONS.indexOf(reaction) < 0) return { ok: false, error: 'bad_reaction' };
  var data = ss.getSheetByName(TABS.data), owner = null;
  if (data && data.getLastRow() >= 2) data.getRange(2, 1, data.getLastRow() - 1, 1).getValues().forEach(function (r) { if (normName_(r[0]) === normName_(target)) owner = String(r[0]); });
  if (!owner) return { ok: false, error: 'no_island' };
  if (normName_(owner) === normName_(who)) return { ok: false, error: 'own_island' };
  var sh = reactTab_(ss), rows = reactRows_(ss), mine = reaction;
  for (var i = 0; i < rows.length; i++) {
    if (normName_(rows[i][0]) === normName_(who) && normName_(rows[i][1]) === normName_(owner)) {
      if (String(rows[i][2]) === reaction) { sh.deleteRow(i + 2); mine = null; }
      else sh.getRange(i + 2, 3, 1, 2).setValues([[reaction, new Date()]]);
      return { ok: true, reacts: reactionsFor_(ss, owner), mine: mine };
    }
  }
  sh.getRange(sh.getLastRow() + 1, 1, 1, 4).setValues([[who, owner, reaction, new Date()]]);
  return { ok: true, reacts: reactionsFor_(ss, owner), mine: mine };
}

/* ---------- Weekly top 3: each game's best scores this week (starts fresh every Monday) ---------- */
function boards_(ss) {
  var st = readSettings_(ss);
  if (!st.top3) return { off: true };
  var hidden = {};
  (st.alwaysPlay + ',' + st.hideTop3).split(/[,;]/).forEach(function (n) { if (normName_(n)) hidden[normName_(n)] = true; });
  var week = isoWeek_(new Date()), all = {};
  var sh = ss.getSheetByName(TABS.data);
  if (sh && sh.getLastRow() >= 2) sh.getRange(2, 1, sh.getLastRow() - 1, 3).getValues().forEach(function (r) {
    if (!r[0] || hidden[normName_(r[0])]) return;
    var p; try { p = JSON.parse(r[2]); } catch (e) { return; }
    var wb = p && p.weekBest;
    if (!wb || wb.week !== week || !wb.s) return;
    Object.keys(wb.s).forEach(function (k) {
      var v = Number(wb.s[k]); if (!(v > 0)) return;
      (all[k] = all[k] || []).push({ name: String(r[0]), avatar: p.avatar || '🙂', score: v });
    });
  });
  var b = {};
  Object.keys(all).forEach(function (k) {
    var low = k === 'memory'; // fewest moves wins
    b[k] = all[k].sort(function (x, y) { return (low ? x.score - y.score : y.score - x.score) || x.name.localeCompare(y.name); }).slice(0, 3);
  });
  return { week: week, b: b };
}

/** Writes a student's new secret code into Roster column B (as text, so 007 stays 007). */
function setRosterCode_(ss, who, code) {
  var sh = ss.getSheetByName(TABS.roster), last = sh.getLastRow();
  if (last < 2) return;
  var names = sh.getRange(2, 1, last - 1, 1).getValues();
  for (var i = 0; i < names.length; i++) {
    if (normName_(names[i][0]) === normName_(who)) { sh.getRange(i + 2, 2).setNumberFormat('@').setValue(code); return; }
  }
}
