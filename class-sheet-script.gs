/**
 * Number Island: class progress sheet
 * ---------------------------------------------------------------
 * Paste this whole file into Extensions > Apps Script in your Google Sheet,
 * click Save, then run "setup" once (see the setup guide).
 *
 * Tabs it creates:
 *   Roster          You type each student's name and an optional secret code.
 *                   Column C: type a number like 50 or -30 to add or take away coins.
 *                   It's applied the next time that student plays, then the cell clears.
 *   Class Progress  One row per student: level and recent accuracy for every skill.
 *   Activity        One row each time a student finishes a game.
 *   Games           Tick a box to unlock a game for every student. Untick to lock it.
 *   Boss Battles    How many hits each student landed on each week's boss.
 *   Needs Help      Who's struggling, which facts they keep missing, and minutes practiced this week.
 *   Settings        Boss Battle day, boss health, coin rate.
 *
 * The "Number Island" menu at the top of the sheet has "Start a new school year…".
 *   Save Data       The game's save files. Hidden. Please don't edit it.
 */

var TABS = { roster: 'Roster', progress: 'Class Progress', help: 'Needs Help', activity: 'Activity', games: 'Games', boss: 'Boss Battles', settings: 'Settings', data: 'Save Data' };
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
    var coinAdjust = 0;
    if (req.action === 'load' || req.action === 'boss' || (req.action === 'save' && !(req.profile && (Number(req.profile.dataVersion) || 1) < readSettings_(ss).version))) coinAdjust = takeCoinAdjust_(ss, who);
    if (req.action === 'load') return out_({ ok: true, name: who, profile: loadSave_(ss, who), games: readGames_(ss), settings: readSettings_(ss), coinAdjust: coinAdjust });
    if (req.action === 'boss') {
      if (req.week && req.hits > 0) addBossHits_(ss, req.week, who, req.hits);
      return out_({ ok: true, boss: bossStatus_(ss, req.week, who), games: readGames_(ss), settings: readSettings_(ss), coinAdjust: coinAdjust });
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
      return out_({ ok: true, games: readGames_(ss), settings: readSettings_(ss), coinAdjust: coinAdjust, boss: req.boss && req.boss.week ? bossStatus_(ss, req.boss.week, who) : null });
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
function settingsTab_(ss) {
  var sh = ss.getSheetByName(TABS.settings);
  if (sh) return sh;
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
  sh.getRange(1, 1, 1, 3).setFontWeight('bold'); sh.setFrozenRows(1);
  sh.setColumnWidth(1, 230); sh.setColumnWidth(2, 120); sh.setColumnWidth(3, 520);
  return sh;
}
function readSettings_(ss) {
  var v = settingsTab_(ss).getRange(2, 2, 4, 1).getValues().map(function (r) { return r[0]; });
  return { bossDay: String(v[0] || 'Friday'), bossHp: Number(v[1]) > 0 ? Number(v[1]) : BOSS_HP_PER_STUDENT,
           coinRate: Number(v[2]) > 0 ? Number(v[2]) : 1, version: Number(v[3]) > 0 ? Number(v[3]) : 1 };
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
  [TABS.progress, TABS.help, TABS.activity, TABS.boss, TABS.data].forEach(function (name) {
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
}
/** Reads and clears a student's coin adjustment. Returns the number (0 if none). */
function takeCoinAdjust_(ss, who) {
  var sh = ss.getSheetByName(TABS.roster); rosterCoinColumn_(sh);
  var last = sh.getLastRow(); if (last < 2) return 0;
  var rows = sh.getRange(2, 1, last - 1, 3).getValues();
  for (var i = 0; i < rows.length; i++) {
    if (normName_(rows[i][0]) !== normName_(who)) continue;
    var n = Math.round(Number(String(rows[i][2]).replace(/[^0-9.\-]/g, '')) || 0);
    if (!n) return 0;
    n = Math.max(-100000, Math.min(100000, n));
    sh.getRange(i + 2, 3).setValue('');
    var act = ss.getSheetByName(TABS.activity);
    if (act) act.getRange(act.getLastRow() + 1, 1, 1, 7).setValues([[new Date(), who, 'Teacher', 'Coins ' + (n > 0 ? '+' : '') + n, '', '', '']]);
    return n;
  }
  return 0;
}
