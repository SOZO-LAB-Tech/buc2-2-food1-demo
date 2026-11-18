/* Demo site only: a scripted "Nescafé complaints in 2025" conversation for Chat with Evidence.
 *
 * Loaded after the Hub's own script. It wraps two Hub functions:
 *   ciAsk    - questions that match the demo get a scripted, streamed answer;
 *              everything else goes to the Hub's normal chat.
 *   cxRender - after the chat redraws, adds the demo's charts, download card and
 *              follow-up chips to its answers.
 * The flow: complaints overview -> breakdown by age / region / gender (donut + bars)
 * -> Excel download -> what to fix first. Numbers come from nescafe-2025.json,
 * which tools/build_demo_data.py writes together with the Excel file.
 */
(function () {
  'use strict';
  if (typeof ciAsk !== 'function' || typeof cxRender !== 'function') return;

  const PID = 'nescafe';
  const START = 'Did anyone complain about Nescafé in 2025?';
  let D = null;
  const ready = fetch('/assets/demo/nescafe-2025.json').then(r => r.json()).then(j => (D = j)).catch(() => null);

  const h = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const n0 = n => Number(n).toLocaleString('en-US');
  const pc = (a, b, d = 0) => (a / b * 100).toFixed(d) + '%';
  const low = s => s.charAt(0).toLowerCase() + s.slice(1);
  const norm = s => s.normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/đ/gi, 'd').toLowerCase();
  const sleep = (ms, sig) => new Promise((ok, no) => {
    const t = setTimeout(ok, ms);
    sig && sig.addEventListener('abort', () => { clearTimeout(t); no(new Error('stopped')); }, { once: true });
  });

  /* ---------- understanding the question ---------- */
  const RX = {
    brand: /nescafe|ca phe|coffee/,
    complaint: /complain|complaint|negative|unhappy|not happy|problem|issue|bad review|phan nan|khieu nai/,
    file: /download|excel|xlsx|spreadsheet|export|\bcsv\b|\bfile\b|tai ve|tai xuong/,
    fix: /fix first|what should we (do|fix)|prioriti|recommend|next step|where (do|should) we start/,
    age: /\bage|tuoi|younger|older|generation/,
    region: /region|city|cities|province|location|\barea|vung|tinh|thanh pho/,
    gender: /gender|\bmale|female|women|\bmen\b|gioi tinh/,
    demographic: /demograph/,
    chart: /\bpie\b|chart|graph|visual|break ?down|split/,
  };
  const chatOf = id => CHAT[id] || null;
  const shownDims = () => (chatOf(PID) ? chatOf(PID).m : []).flatMap(m => (m.demo && m.demo.dims) || []);
  const inDemo = () => !!(chatOf(PID) && chatOf(PID).m.some(m => m.demo));

  function route(P, q) {
    const t = norm(q), brand = P.id === PID || RX.brand.test(t);
    let dims = ['age', 'region', 'gender'].filter(k => RX[k].test(t));
    if (!dims.length && RX.demographic.test(t)) dims = ['gender', 'region'];
    if (!brand) return null;
    if (RX.file.test(t)) return { kind: 'file' };
    if (dims.length) return { kind: 'dims', dims };
    if (RX.fix.test(t) && inDemo()) return { kind: 'fix' };
    if (RX.chart.test(t) && inDemo()) return { kind: 'dims', dims: [shownDims().slice(-1)[0] || 'age'] };
    if (RX.complaint.test(t)) return { kind: 'overview' };
    return null;
  }

  /* ---------- the answers ---------- */
  const SHORT = s => s.replace(/ reviews$| Page$/, '').replace(/^Complaints system$/, 'the complaints system');
  const listJoin = a => a.length < 2 ? a.join('') : a.slice(0, -1).join(', ') + ' and ' + a[a.length - 1];
  const DIMLABEL = { age: 'age group', region: 'region', gender: 'gender' };
  const ACTION = {
    'Too sweet (3-in-1)': 'Offer a less-sweet 3-in-1',
    'Promotion price changes at checkout': 'Fix promotion prices at checkout with Shopee and Lazada',
    'Strength and caffeine labels unclear': 'Print strength and caffeine per sachet on the pack',
    'Sachets tear or powder clumps': 'Strengthen the sachets and add moisture protection',
    'Out of stock online': 'Keep the best sellers in stock online',
  };
  function nextChips(exclude) {
    const seen = new Set(shownDims().concat(exclude || []));
    const L = ['age', 'region', 'gender'].filter(k => !seen.has(k)).map(k => 'Show by ' + DIMLABEL[k]);
    if (!chatOf(PID) || !chatOf(PID).m.some(m => m.demo && m.demo.file)) L.push('Download as Excel');
    else if (!chatOf(PID).m.some(m => m.demo && m.demo.fix)) L.push('What should we fix first?');
    return L.slice(0, 3);
  }

  function overview() {
    const S = D.survey, F = D.feedback, T = D.themes.slice(0, 3);
    return {
      think: `Searching ${n0(F.total)} ${D.brand} feedback items from ${D.year}`,
      text: [
        `Yes. ${D.brand} received a steady stream of complaints in ${D.year}.`,
        '',
        `- In the **${S.name}**, **${pc(S.complained, S.respondents)}** of respondents (${n0(S.complained)} of ${n0(S.respondents)}) reported a complaint.`,
        `- Across ${listJoin(D.sources.map(s => SHORT(s.name)))}, **${n0(F.complaints)} reports** were complaints: ${pc(F.complaints, F.total, 1)} of all ${n0(F.total)} ${D.brand} feedback items.`,
        '',
        'The most common complaints:',
        ...T.map(t => `- **${t.name}**: ${pc(t.n, F.complaints)} of complaints. “${t.quote}”`),
        '',
        'Do you want to see this by **age group**, **region** or **gender**?',
      ].join('\n'),
      rich: { overview: true },
      next: ['Show by age group', 'Show by region', 'Show by gender'],
    };
  }

  function dimText(key) {
    const all = D.dims[key].groups, C = D.feedback.complaints, rate = x => x.n / x.total;
    const g = all.filter(x => !/not stated|unknown|prefer not/i.test(x.name)); // don't rank "unknown" groups
    const most = [...g].sort((a, b) => b.n - a.n)[0];
    const often = [...g].sort((a, b) => rate(b) - rate(a))[0];
    const least = [...g].sort((a, b) => rate(a) - rate(b))[0];
    const L = [`- **${most.name}** sent the most complaints: ${n0(most.n)}, or ${pc(most.n, C)} of the total. Their top issue: ${low(most.top)}.`];
    if (often !== most) L.push(`- **${often.name}** complain most often: ${pc(often.n, often.total, 1)} of their feedback was a complaint, mostly about ${low(often.top)}.`);
    else L.push(`- They also complain most often: ${pc(often.n, often.total, 1)} of their feedback was a complaint.`);
    const falling = g.every((x, i) => !i || rate(x) <= rate(g[i - 1]));
    if (D.dims[key].ordinal && falling) L.push(`- Complaint rates fall with age, down to ${pc(least.n, least.total, 1)} for ${least.name}.`);
    else L.push(`- **${least.name}** complain least often: ${pc(least.n, least.total, 1)}.`);
    return L;
  }

  function dims(r) {
    const names = r.dims.map(k => DIMLABEL[k]);
    const multi = r.dims.length > 1;
    const body = r.dims.flatMap(k => (multi ? ['', `**By ${DIMLABEL[k]}**`] : []).concat(dimText(k)));
    return {
      think: `Breaking down ${n0(D.feedback.complaints)} complaints by ${listJoin(names)}`,
      text: [`Here are ${D.brand}’s ${D.year} complaints by ${listJoin(names)}.`, ...(multi ? [] : ['']), ...body, '', 'Want this as an Excel file to share with the team?'].join('\n'),
      rich: { dims: r.dims },
      next: nextChips(r.dims),
    };
  }

  function file() {
    const F = D.file;
    return {
      think: 'Preparing the Excel file',
      text: `Here’s the ${D.year} ${D.brand} complaint data as an Excel file. It has ${F.sheets.length} sheets: a summary, the breakdowns by age group, region and gender (each with charts), and all ${n0(D.feedback.complaints)} complaints with their source, product and comment.`,
      rich: { file: true },
      next: null,
    };
  }

  function fix() {
    const C = D.feedback.complaints, age = D.dims.age.groups;
    const who = t => { const g = age.find(x => x.top === t.name); return g ? `, and the top issue for ${g.name}` : ''; };
    return {
      think: 'Weighing the complaint themes against who raises them',
      text: [
        `Based on the ${D.year} complaints, I’d start here:`,
        '',
        ...D.themes.slice(0, 3).map(t => `- **${ACTION[t.name] || t.name}.** ${pc(t.n, C)} of complaints are about ${low(t.name)}${who(t)}.`),
        '',
        `Together these three cover ${pc(D.themes.slice(0, 3).reduce((s, t) => s + t.n, 0), C)} of all ${D.brand} complaints in ${D.year}.`,
      ].join('\n'),
      rich: { fix: true },
      next: null,
    };
  }
  const BUILD = { overview, dims, file, fix };

  /* ---------- asking ---------- */
  const _ciAsk = ciAsk;
  window.ciAsk = function (P, q) {
    q = (q || '').trim();
    const r = q && P && !CIBUSY ? route(P, q) : null;
    if (!r) return _ciAsk(P, q);
    return run(q, r).catch(() => _ciAsk(P, q));
  };

  async function run(q, r) {
    await ready;
    const P = IIP.find(x => x.id === PID);
    if (!D || !P) throw new Error('demo data unavailable');
    if (CXW.pid !== PID) { CXW.pid = PID; CXW.recent = [PID, ...(CXW.recent || []).filter(x => x !== PID)].slice(0, 4); }
    const ans = BUILD[r.kind](r);
    const C = CHAT[PID] = CHAT[PID] || { m: [], draft: '' };
    C.draft = '';
    C.m.push({ role: 'user', content: q });
    const msg = { role: 'assistant', content: '', busy: 1, demoThink: ans.think };
    C.m.push(msg);
    const idx = C.m.length - 1, ctl = new AbortController(), E = ciEvidence(P);
    CIBUSY = { ctl, pid: PID };
    cxRender();
    try {
      await sleep(900 + Math.random() * 500, ctl.signal);
      const parts = ans.text.match(/\S+\s*/g) || [];
      for (let i = 0; i < parts.length; i += 2) {
        msg.content = parts.slice(0, i + 2).join('');
        const el = document.getElementById('cim-' + idx);
        if (el) { el.innerHTML = ciFmt(msg.content, E); const b = document.getElementById('cimsgs'); if (b) b.scrollTop = b.scrollHeight; }
        await sleep(22 + Math.random() * 18, ctl.signal);
      }
      msg.content = ans.text;
      msg.demo = ans.rich;
      msg.demoNext = ans.next;
    } catch (_) {
      msg.stopped = 1;
    }
    delete msg.busy;
    CIBUSY = null;
    cxRender();
  }

  /* ---------- drawing ---------- */
  const DL = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 2.5v8M4.5 7.5L8 11l3.5-3.5M3 13.5h10"/></svg>';
  const SHEET = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3.5" y="3.5" width="17" height="17" rx="2.5"/><path d="M3.5 9h17M3.5 14.5h17M9.5 9v11.5"/></svg>';

  function donut(groups, total, label) {
    const R = 46, C = 2 * Math.PI * R, GAP = 2.2;
    let off = 0;
    const segs = groups.map((g, i) => {
      const len = g.n / total * C;
      const s = `<circle cx="60" cy="60" r="${R}" fill="none" stroke="var(--dm${i + 1})" stroke-width="16" stroke-dasharray="${Math.max(len - GAP, .6).toFixed(2)} ${C.toFixed(2)}" stroke-dashoffset="${(-off).toFixed(2)}"><title>${h(g.name)}: ${n0(g.n)} complaints (${pc(g.n, total)})</title></circle>`;
      off += len;
      return s;
    }).join('');
    return `<svg class="dmx-ring" viewBox="0 0 120 120" role="img" aria-label="${h(label)}"><g transform="rotate(-90 60 60)">${segs}</g><text x="60" y="61" class="dmx-ct">${n0(total)}</text><text x="60" y="76" class="dmx-cs">complaints</text></svg>`;
  }

  function dimHTML(key, anim) {
    const d = D.dims[key], g = d.groups, C = D.feedback.complaints;
    const rates = g.map(x => x.n / x.total), max = Math.max(...rates);
    const lab = DIMLABEL[key];
    return `<section class="dmx-sec ${d.ordinal ? 'dmx-ord' : 'dmx-cat'}" aria-label="Complaints by ${h(lab)}">
      <div class="dmx-h"><b>Share of complaints by ${h(lab)}</b><span>${n0(C)} complaints · ${D.year}</span></div>
      <div class="dmx-pie">${donut(g, C, `Share of complaints by ${lab}`)}
        <ul class="dmx-leg">${g.map((x, i) => `<li><i style="background:var(--dm${i + 1})"></i><span>${h(x.name)}</span><b>${pc(x.n, C)}</b><em>${n0(x.n)}</em></li>`).join('')}</ul>
      </div>
      <div class="dmx-h"><b>Complaint rate by ${h(lab)}</b><span>% of each group’s feedback that was a complaint</span></div>
      <div class="dmx-bars">${g.map((x, i) => `<span>${h(x.name)}</span><span class="tr" title="${h(x.name)}: ${n0(x.n)} of ${n0(x.total)} feedback items were complaints"><i class="${anim ? 'grow' : ''}" style="width:${(rates[i] / max * 100).toFixed(1)}%;animation-delay:${anim ? i * 60 : 0}ms"></i></span><b>${(rates[i] * 100).toFixed(1)}%</b>`).join('')}</div>
    </section>`;
  }

  function fileHTML() {
    const F = D.file;
    return `<div class="dmf">
      <span class="dmf-ic">${SHEET}</span>
      <span class="dmf-t"><b>${h(F.name)}</b><span>Excel workbook · ${Math.round(F.bytes / 1024)} KB · ${n0(D.feedback.complaints)} rows</span></span>
      <a class="dmf-dl" href="${h(F.url)}" download="${h(F.name)}">${DL}Download</a>
    </div>
    <div class="dmf-sh">${F.sheets.map(s => `<span>${h(s)}</span>`).join('')}</div>`;
  }

  function richHTML(m) {
    const R = m.demo, anim = !m.demoShown;
    if (R.dims) return `<div class="dmx${anim ? ' dmx-in' : ''}">${R.dims.map(k => dimHTML(k, anim)).join('')}</div>`;
    if (R.file) return `<div class="dmx${anim ? ' dmx-in' : ''}">${fileHTML()}</div>`;
    return '';
  }

  function chipsHTML(L) {
    return `<div class="cxdfu dmx-fu"><span class="cxdsh">Ask next</span><div class="cxdfc">${L.map(q => `<button type="button" data-act="ciask" data-q="${h(q)}">${h(q)}</button>`).join('')}</div></div>`;
  }

  function decorate() {
    if (!CXW.open) return;
    const P = IIP.find(x => x.id === CXW.pid);
    // Empty chat: offer the demo question first.
    const sl = document.querySelector('#cxw .cxdsl');
    if (sl && !sl.querySelector('[data-dmx]')) {
      const tpl = sl.querySelector('button');
      if (tpl) {
        const b = tpl.cloneNode(true);
        b.dataset.q = START; b.dataset.dmx = '1';
        const sp = b.querySelector('span'); if (sp) sp.textContent = START;
        sl.prepend(b);
      }
    }
    if (!P || !D) return;
    const C = chatOf(P.id);
    if (!C) return;
    const last = C.m.map(m => m.role).lastIndexOf('assistant');
    C.m.forEach((m, i) => {
      if (m.role !== 'assistant') return;
      const el = document.getElementById('cim-' + i);
      if (!el) return;
      if (m.busy && m.demoThink && !m.content) el.innerHTML = `<p class="cithink">${h(m.demoThink)}<span class="cidots"><i></i><i></i><i></i></span></p>`;
      if (!m.demo || m.busy) return;
      const card = el.parentElement;
      if (!card.querySelector('.dmx')) card.insertAdjacentHTML('beforeend', richHTML(m));
      m.demoShown = 1;
      const L = i === last && !CIBUSY ? (m.demoNext || nextChips()) : null;
      if (L && L.length && card.parentElement && !card.parentElement.querySelector('.dmx-fu')) card.parentElement.insertAdjacentHTML('beforeend', chipsHTML(L));
    });
  }

  const _cxRender = cxRender;
  window.cxRender = function () {
    const out = _cxRender.apply(this, arguments);
    try { decorate(); } catch (e) { console.error('demo chat:', e); }
    return out;
  };

  /* ---------- styles ---------- */
  const css = `
  .dmx{margin-top:14px;padding-top:14px;border-top:1px solid var(--line);display:flex;flex-direction:column;gap:18px;
    --dmbar:#2a78d6;--dmfile:#1f7a4d}
  .dmx-in{animation:dmfade .45s ease both}
  .dmx-ord{--dm1:#6da7ec;--dm2:#3987e5;--dm3:#256abf;--dm4:#184f95;--dm5:#0d366b}
  .dmx-cat{--dm1:#2a78d6;--dm2:#eb6834;--dm3:#1baf7a;--dm4:#eda100;--dm5:#e87ba4}
  [data-theme="dark"] .dmx{--dmbar:#3987e5;--dmfile:#3fae73}
  [data-theme="dark"] .dmx-ord{--dm1:#cde2fb;--dm2:#9ec5f4;--dm3:#6da7ec;--dm4:#3987e5;--dm5:#256abf}
  [data-theme="dark"] .dmx-cat{--dm1:#3987e5;--dm2:#d95926;--dm3:#199e70;--dm4:#c98500;--dm5:#d55181}
  .dmx-sec{display:flex;flex-direction:column;gap:10px}
  .dmx-sec+.dmx-sec{padding-top:16px;border-top:1px dashed var(--line)}
  .dmx-h{display:flex;flex-direction:column;gap:1px}
  .dmx-h b{font-size:13.5px;font-weight:600;color:var(--fg)}
  .dmx-h span{font-size:12px;color:var(--fg2)}
  .dmx-pie{display:flex;align-items:center;gap:18px;flex-wrap:wrap;margin-bottom:6px}
  .dmx-ring{width:128px;height:128px;flex:none;overflow:visible}
  .dmx-ring circle{transition:opacity .15s}
  .dmx-ring:hover circle{opacity:.35}.dmx-ring circle:hover{opacity:1}
  .dmx-ct{font:600 18px var(--font,Roboto,Arial,sans-serif);fill:var(--fg);text-anchor:middle;font-variant-numeric:tabular-nums}
  .dmx-cs{font:400 10px var(--font,Roboto,Arial,sans-serif);fill:var(--fg2);text-anchor:middle}
  .dmx-leg{list-style:none;margin:0;padding:0;flex:1;min-width:200px;display:grid;grid-template-columns:10px 1fr auto auto;gap:7px 10px;align-items:center;font-size:13px}
  .dmx-leg li{display:contents}
  .dmx-leg i{width:10px;height:10px;border-radius:3px}
  .dmx-leg span{color:var(--fg)}
  .dmx-leg b{font-weight:600;color:var(--fg);text-align:right;font-variant-numeric:tabular-nums}
  .dmx-leg em{font-style:normal;color:var(--fg2);text-align:right;font-variant-numeric:tabular-nums;min-width:30px}
  .dmx-bars{display:grid;grid-template-columns:auto 1fr auto;gap:8px 12px;align-items:center;font-size:13px}
  .dmx-bars>span:not(.tr){color:var(--fg);white-space:nowrap}
  .dmx-bars .tr{position:relative;height:12px;border-left:1px solid var(--fg3,#9BA0AC)}
  .dmx-bars .tr i{position:absolute;left:0;top:1px;bottom:1px;background:var(--dmbar);border-radius:0 4px 4px 0;transform-origin:left}
  .dmx-bars .tr i.grow{animation:dmgrow .7s cubic-bezier(.2,.7,.2,1) both}
  .dmx-bars b{font-weight:600;color:var(--fg);text-align:right;font-variant-numeric:tabular-nums}
  .dmf{display:flex;align-items:center;gap:12px;padding:12px 14px;border-radius:12px;background:var(--panel,#fff);box-shadow:inset 0 0 0 1px var(--line)}
  .dmf-ic{width:40px;height:40px;border-radius:10px;display:grid;place-items:center;flex:none;color:#fff;background:var(--dmfile)}
  .dmf-ic svg{width:22px;height:22px}
  .dmf-t{display:flex;flex-direction:column;min-width:0;flex:1}
  .dmf-t b{font-size:14px;font-weight:600;color:var(--fg);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .dmf-t span{font-size:12.5px;color:var(--fg2)}
  .dmf-dl{display:inline-flex;align-items:center;gap:7px;height:36px;padding:0 14px;border-radius:9px;background:var(--fg);color:var(--panel,#fff);font-size:13.5px;font-weight:600;text-decoration:none;flex:none}
  .dmf-dl:hover{filter:brightness(1.15)}
  .dmf-dl svg{width:15px;height:15px}
  .dmf-sh{display:flex;flex-wrap:wrap;gap:6px;margin-top:-8px}
  .dmf-sh span{font-size:12px;color:var(--fg2);padding:3px 9px;border-radius:999px;box-shadow:inset 0 0 0 1px var(--line)}
  @keyframes dmgrow{from{transform:scaleX(0)}}
  @keyframes dmfade{from{opacity:0;transform:translateY(6px)}}
  @media (prefers-reduced-motion:reduce){.dmx-in,.dmx-bars .tr i.grow{animation:none}}`;
  const st = document.createElement('style');
  st.textContent = css;
  document.head.appendChild(st);
})();
