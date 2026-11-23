"""Builds pigeon.html (Banpo Pigeon, with Math Island questions) from source/banpo-pigeon-original.html.
Usage: python3 tools/pigeon_patch.py source/banpo-pigeon-original.html pigeon.html
Adds: a pause switch in the game loop, a math question on every snack (right = +2 min, wrong/slow = it flies away,
15 s each), a 3-minute flight clock, and the link to Math Island (ticket in, result out via localStorage)."""
import sys
src, out = sys.argv[1], sys.argv[2]
s=open(src).read()
def rep(a,b):
    global s
    assert s.count(a)==1, (s.count(a), a[:80])
    s=s.replace(a,b)
# pause switch + snack hook inside the game's own code
rep("if(Si&&!Fs)__(t,e);else{","if(window.__paused);else if(Si&&!Fs)__(t,e);else{")
# fewer, more spread-out snacks: skip any snack within 80 m of one already placed (the game used 6 m)
rep("p.some(R=>Math.hypot(R.x-y[0],R.z-y[1])<6)","p.some(R=>Math.hypot(R.x-y[0],R.z-y[1])<80)")
old='if(M<2.2&&Math.abs(b.y-F.y)<2.2){b.got=!0,Fl++;for(let x of oa[b.t])x.setMatrixAt(b.idx,c_);xf(),'
rep(old,'if(M<2.2&&Math.abs(b.y-F.y)<2.2&&window.__snackQ){b.got=!0;window.__snackQ(b,function(ok){for(let x of oa[b.t])x.setMatrixAt(b.idx,c_);if(ok){Fl++;xf();xn(["Ramyeon!","Coffee!","Bread!"][b.t]+" +2 minutes!")}else xn("The snack flew away! Find food somewhere else.")});continue}'+old)
rep("fly over the real streets of Banpo, Nonhyeon and Gangnam. Collect 🍜 ☕ 🥐 outside real shops.</p>\n", "fly over the real streets of Banpo, Nonhyeon and Gangnam. Collect 🍜 ☕ 🥐 outside real shops.</p>\n    <p class=\"intro mathnote\">🧮 Every snack asks a math question. Right answer = <b>+2 minutes</b> of flying! Wrong answer, and the snack flies away.<br>🪙 Every snack you get right = <b>10 coins</b> on Math Island.</p>\n")
rep("explore the real streets of Banpo, Nonhyeon and Gangnam on foot. Collect 🍜 ☕ 🥐 outside real shops.</p>",
    "explore the real streets of Banpo, Nonhyeon and Gangnam on foot. Collect 🍜 ☕ 🥐 outside real shops.</p>\n    <p class=\"intro mathnote\">🧮 Every snack asks a math question. Right answer = <b>+2 minutes</b>! Wrong answer, and the snack runs away.<br>🪙 Every snack you get right = <b>10 coins</b> on Math Island.</p>")
css = """
  /* ---- Math Island additions ---- */
  .mathnote { background: #FFF5C2; border-radius: 12px; padding: 8px 10px; }
  #miClock { position: fixed; top: 12px; left: 50%; transform: translateX(-50%); z-index: 40; background: #fff; color: #1E2A33; border: 3px solid #1E2A33; border-radius: 999px; padding: 4px 16px; font: 800 22px system-ui, sans-serif; box-shadow: 0 3px 0 #1E2A33; display: none; }
  body.playing #miClock { display: block; }
  #miClock.low { background: #FFE3E3; color: #B3261E; animation: miPulse .6s ease-in-out infinite alternate; }
  @keyframes miPulse { to { transform: translateX(-50%) scale(1.08); } }
  #miClock.plus::after { content: ' +2:00'; color: #1E8A4C; }
  #miBack { position: fixed; top: 60px; left: 50%; transform: translateX(-50%); z-index: 40; border: 0; border-radius: 999px; padding: 6px 14px; font: 700 14px system-ui, sans-serif; background: rgba(255,255,255,.92); color: #1E2A33; border: 3px solid #1E2A33; }
  #miBack:not(.end) { top: 12px; left: 12px; transform: none; }
  #miBack.end { background: #E8463C; color: #fff; box-shadow: 0 2px 8px rgba(0,0,0,.2); cursor: pointer; }
  #miQ, #miEnd, #miGate { position: fixed; inset: 0; z-index: 80; display: none; align-items: center; justify-content: center; background: rgba(20,30,40,.55); touch-action: manipulation; }
  #miQ.show, #miEnd.show, #miGate.show { display: flex; }
  .miCard { background: #FFFBEF; border: 4px solid #1E2A33; border-radius: 22px; padding: 16px 18px; width: min(380px, 92vw); text-align: center; box-shadow: 0 8px 0 #1E2A33; font-family: system-ui, sans-serif; color: #1E2A33; }
  .miCard h2 { margin: 2px 0 8px; font-size: 20px; }
  .miQtext { font-size: 38px; font-weight: 900; margin: 4px 0 8px; }
  .miAns { min-height: 52px; border: 3px solid #7C5CFF; border-radius: 14px; background: #fff; font-size: 34px; font-weight: 800; display: flex; align-items: center; justify-content: center; margin-bottom: 8px; }
  .miBar { height: 12px; border: 2px solid #1E2A33; border-radius: 99px; overflow: hidden; background: #fff; margin-bottom: 10px; }
  .miBar i { display: block; height: 100%; width: 100%; background: #3FBF6A; }
  .miBar i.low { background: #E8463C; }
  .miPad { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
  .miPad button, .miBtn { font: 800 26px system-ui, sans-serif; padding: 10px 0; border: 3px solid #1E2A33; border-radius: 14px; background: #fff; box-shadow: 0 3px 0 #1E2A33; cursor: pointer; color: #1E2A33; }
  .miPad .ok { background: #23A866; color: #fff; }
  .miPad .del { background: #F5E6C8; }
  .miFb { min-height: 26px; font-weight: 800; font-size: 18px; margin-top: 8px; }
  .miFb.good { color: #1E8A4C; } .miFb.bad { color: #B3261E; }
  .miBtn { font-size: 18px; padding: 12px 20px; background: #23A866; color: #fff; margin-top: 12px; }
  .miLines { text-align: left; margin: 8px auto; display: grid; gap: 4px; font-size: 17px; }
</style>"""
rep("</style>", css)
html = """
<div id="miClock">⏱ 3:00</div>
<button id="miBack" type="button">🛑 End game</button>
<div id="miQ" role="dialog" aria-label="Math question"><div class="miCard">
  <h2 id="miQhead">🍜 Snack question!</h2>
  <div class="miBar"><i id="miQbar"></i></div>
  <div class="miQtext" id="miQtext"></div>
  <div class="miAns" id="miAns"></div>
  <div class="miPad">${PAD}</div>
  <div class="miFb" id="miFb"></div>
</div></div>
<div id="miEnd"><div class="miCard"><h2 id="miEndHead">🐦 Time to land!</h2><div class="miLines" id="miEndLines"></div><button class="miBtn" id="miHome" type="button">🏝️ Back to Math Island</button></div></div>
<div id="miGate"><div class="miCard"><h2>🐦 Banpo Pigeon</h2><p>Open Banpo Pigeon from the Math Island main screen to play.</p><button class="miBtn" id="miGateBtn" type="button">🏝️ Go to Math Island</button></div></div>
"""
pad = ''.join(f'<button type="button" data-k="{k}">{k}</button>' for k in [7,8,9,4,5,6,1,2,3]) + '<button type="button" class="del" data-k="del">⌫</button><button type="button" data-k="0">0</button><button type="button" class="ok" data-k="ok">✓</button>'
html = html.replace('${PAD}', pad)
js = r"""
<script>
/* Math Island link: Math Island writes a "ticket" (student, questions at their level) before opening this page,
   and reads the "result" when they come back. Snacks ask a question: right = +2 minutes, wrong or too slow = it flies away. */
(function () {
  const START_SECS = 180, BONUS_SECS = 120, Q_SECS = 15;
  const $ = id => document.getElementById(id);
  let ticket = null;
  try { ticket = JSON.parse(localStorage.getItem('numberIsland.pigeonTicket') || 'null'); } catch (e) {}
  const home = () => { location.href = './?from=pigeon'; };
  if (!ticket || !ticket.qs || !ticket.qs.length || Date.now() - (ticket.at || 0) > 15 * 60000) {
    $('miGate').classList.add('show'); $('miGateBtn').addEventListener('click', home); window.__paused = true; return;
  }
  try { localStorage.removeItem('numberIsland.pigeonTicket'); } catch (e) {}
  let left = START_SECS, last = performance.now(), qi = 0, over = false, current = null;
  const log = [];
  const fmt = n => String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  function saveResult() {
    const r = { pid: ticket.pid, at: Date.now(), snacks: log.filter(x => x.ok).length, right: log.filter(x => x.ok).length, wrong: log.filter(x => !x.ok && !x.slow).length, slow: log.filter(x => x.slow).length, log };
    try { localStorage.setItem('numberIsland.pigeonResult', JSON.stringify(r)); } catch (e) {}
    return r;
  }
  function clock(now) {
    if (!over && document.body.classList.contains('playing') && !window.__paused) {
      left -= Math.min(.25, (now - last) / 1000);
      if (left <= 0) { left = 0; finish("⏰ Time's up! Time to land."); }
    }
    last = now;
    const s = Math.ceil(left); $('miClock').textContent = `⏱ ${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
    $('miClock').classList.toggle('low', s <= 20 && !over);
    const playing = document.body.classList.contains('playing'), bt = playing ? '🛑 End game' : '🏝️ Back to Math Island';
    if ($('miBack').textContent !== bt) { $('miBack').textContent = bt; $('miBack').classList.toggle('end', playing); }
    requestAnimationFrame(clock);
  }
  requestAnimationFrame(clock);
  function finish(head) {
    if (over) return; over = true; window.__paused = true;
    if (current) { clearInterval(current.timer); $('miQ').classList.remove('show'); }
    const r = saveResult();
    $('miEndHead').textContent = head;
    $('miEndLines').innerHTML = `<div>🍜 Snacks eaten: <b>${r.snacks}</b></div><div>✅ Right answers: <b>${r.right}</b> of ${log.length}</div><div>🪙 Coins you earned: <b>${fmt(r.right * 10)}</b> <small>(10 for each snack)</small></div>`;
    $('miEnd').classList.add('show');
  }
  $('miHome').addEventListener('click', home);
  $('miBack').addEventListener('click', () => {
    if (over) return;
    if (document.body.classList.contains('playing')) finish('🛑 Game over! Time to land.'); else { saveResult(); home(); }
  });
  /* the game calls this when the pigeon reaches a snack */
  window.__snackQ = function (snack, done) {
    if (over) return done(false);
    const q = ticket.qs[qi++ % ticket.qs.length];
    window.__paused = true;
    current = { q, done, val: '', t0: performance.now(), timer: 0 };
    $('miQhead').textContent = ['🍜 Ramyeon question!', '☕ Coffee question!', '🥐 Bread question!'][snack.t] || '🍜 Snack question!';
    $('miQtext').textContent = q.text + ' = ?'; $('miAns').textContent = ''; $('miFb').textContent = ''; $('miFb').className = 'miFb';
    const bar = $('miQbar'); bar.style.transition = 'none'; bar.style.width = '100%'; bar.classList.remove('low');
    requestAnimationFrame(() => requestAnimationFrame(() => { bar.style.transition = `width ${Q_SECS}s linear`; bar.style.width = '0%'; }));
    current.timer = setInterval(() => {
      const t = (performance.now() - current.t0) / 1000;
      if (t > Q_SECS - 4) bar.classList.add('low');
      if (t >= Q_SECS) answer(true);
    }, 200);
    $('miQ').classList.add('show');
  };
  function answer(slow) {
    const c = current; if (!c || c.answered) return; c.answered = true; clearInterval(c.timer);
    const ok = !slow && c.val !== '' && Number(c.val) === c.q.answer;
    log.push({ skill: c.q.skill, text: c.q.text, answer: c.q.answer, ok, slow: !!slow });
    const fb = $('miFb');
    if (ok) { left += BONUS_SECS; fb.textContent = '✅ Yes! +2 minutes!'; fb.className = 'miFb good'; $('miClock').classList.add('plus'); setTimeout(() => $('miClock').classList.remove('plus'), 1800); }
    else { fb.textContent = (slow ? '⏰ Too slow! ' : '❌ Not quite! ') + `${c.q.text} = ${fmt(c.q.answer)}`; fb.className = 'miFb bad'; }
    saveResult();
    setTimeout(() => { $('miQ').classList.remove('show'); current = null; if (!over) { window.__paused = false; last = performance.now(); } c.done(ok); }, ok ? 900 : 1700);
  }
  function press(k) {
    const c = current; if (!c || c.answered) return;
    if (k === 'ok') { if (c.val !== '') answer(false); return; }
    if (k === 'del') c.val = c.val.slice(0, -1); else if (c.val.length < 5) c.val += k;
    $('miAns').textContent = c.val;
  }
  document.querySelectorAll('#miQ .miPad button').forEach(b => {
    b.addEventListener('click', () => press(b.dataset.k));
    b.addEventListener('touchend', e => { e.preventDefault(); press(b.dataset.k); }, { passive: false });
  });
  // while a question is up, the keyboard types answers and the game doesn't see the keys
  const keyStop = e => {
    if (!current) return;
    e.stopPropagation(); e.stopImmediatePropagation();
    if (e.type !== 'keydown') return;
    e.preventDefault();
    if (/^[0-9]$/.test(e.key)) press(e.key); else if (e.key === 'Backspace') press('del'); else if (e.key === 'Enter') press('ok');
  };
  window.addEventListener('keydown', keyStop, true); window.addEventListener('keyup', keyStop, true);
})();
</script>
"""
i = s.rindex('</body>')
s = s[:i] + html + js + s[i:]
open(out,'w').write(s)
print('written', len(s))
