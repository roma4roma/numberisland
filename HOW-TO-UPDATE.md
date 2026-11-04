# Mr. Romanek's Math Island Adventure: how to make changes

This file is for whoever changes the game next: a future Claude chat, a helper, or Mr. Romanek.
**If you are an AI assistant, read all of this before you change anything.**

## What's where

| Path | What it is |
|---|---|
| `source/number-island.html` | **The game's source. Edit this file**, never `index.html` directly. |
| `index.html` | The built game that students load (made by `build.sh`). |
| `version.txt` | The build's version number. Tablets check it every minute and reload themselves when it changes. |
| `class-sheet-script.gs` | The Google Apps Script behind the class Google Sheet. |
| `emoji/` | OpenMoji pictures (CC BY-SA 4.0, see `emoji/LICENSE-NOTE.txt`). They're packed into `index.html` at build time. |
| `tools/` | Build helpers (`build.py`, `embed_emoji.js`, `sync_openmoji.js`). |
| `test/mock-sheet-server.js` | A fake Google Sheet for testing without touching the real class sheet. |

Live game: https://roma4roma.github.io/numberisland/

## Changing the game

1. Edit `source/number-island.html`. It's one file of HTML, CSS and JavaScript, all inside one IIFE. It saves progress in `localStorage` under the key `numberIsland.v1`.
2. Run `./build.sh`. It needs python3 and node; the first run downloads `svgo` through npx.
3. Commit `index.html` and `version.txt` together with your source change, then push. GitHub Pages updates in about a minute, and the tablets reload themselves within another minute or two. They never reload in the middle of a game.

If you add a new emoji to the game, run `tools/sync_openmoji.js` (the instructions are at the top of that file), then `rm -rf .emoji-min` and `./build.sh`.

## Changing the Google Sheet script

1. Edit `class-sheet-script.gs` and commit it.
2. In the Google Sheet, open Extensions → Apps Script, paste the new code over the old, and save.
3. Click **Deploy → Manage deployments → ✏️ → Version: New version → Deploy.** Without a new deployment, the change does nothing. The web app URL stays the same.

Settings rows are made automatically. New settings go at the end of `EXTRA_ROWS`, from row 6 down. Never insert one in the middle, because `readSettings_` reads them by position. Add the new key to `readSettings_` as well.

## Testing safely

```
node test/mock-sheet-server.js class-sheet-script.gs     # fake sheet on port 8765, roster: Alex/111, Sam/007, Kim/(no code)
```

- Build a test copy with `CLASS_SHEET_URL` set to `'http://127.0.0.1:8765/exec'` and serve it with `python3 -m http.server 8766`.
- Test it with Playwright.
- The mock server has helper URLs:
  - `/dump` shows all tabs;
  - `/set?tab=&r=&c=&v=` changes a cell;
  - `/clock?t=<ISO time>` fakes the date, for Boss Fridays and Race Day Thursdays;
  - `/down` and `/up` simulate going offline.

## Things the teacher has asked for (keep these true)

- **Account and data:**
  - "Wolfgang" is Mr. Romanek's own test account. It's kept out of the top 3 lists and Race Day winners through the Settings rows "Can always play" and "Hide from top 3".
  - Don't put student names or student data in this repo. It's public.
- **Look and wording:**
  - Use metric units only.
  - Emoji use OpenMoji: the class chose it. Samsung emoji aren't allowed for licensing reasons.
  - The teacher cartoon is the simple SVG `teacherSVG()`. Don't use real photos or the raccoon painting in the game.
  - Raccoon items stay as top-tier shop items. No ramen raccoon mascot.
- **Game rules:**
  - Penalty Shootout: the goalie wanders at random and must never move toward the right answer.
  - Fact Runner: never reveal a missed answer; the question just comes back later.
  - Race Day: Thursdays, 2 minutes, +1 right / −1 wrong, best score of the day. Winners are decided at the results time (14:20) and everyone tied for first wins. The Race Day card is first on race day; on other days Boss Battle is first.
  - Boss Battle: Fridays (set in Settings). Helpers get that week's boss pet and 150 coins. Students who weren't online when the boss fell get it the next time they open the game, including from the previous week.
- **Behaviour:**
  - Device clock tampering is not a concern.
  - School hours are enforced with the device clock.

## How the game and the sheet talk

- The game POSTs JSON to the Apps Script web app.
  - Actions: `load`, `save`, `boss`, `islands`, `react`, `setCode`, `suggest`, `raceScore`.
- `save` responses carry:
  - `games` (which games are unlocked), `settings` and `boards` (weekly top 3);
  - `race`, `boss` and `myReactions`;
  - teacher coin gifts.
- **Coin gifts:** these use an acknowledgement so they're never lost or doubled. The Roster's hidden column D holds `amount|id`; the game sends `coinAck`, and the request must include `coinV: 2`.
  - Race Day prizes work the same way with `raceAck`.
- The hub shows a status pill at the top ("Updating with your class…" / "✅ Up to date").
  - It checks the sheet when the game opens and every minute on the hub.
  - It shows a pop-up when the teacher turns on a new game.
