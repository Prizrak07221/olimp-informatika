(() => {
  'use strict';
  const D = window.OLY;
  const app = document.getElementById('app');

  // ---------- утилиты ----------
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const shuffle = (a) => { a = a.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };
  const hash = (s) => { let h = 5381; for (let i = 0; i < s.length; i++) h = (h * 33 + s.charCodeAt(i)) >>> 0; return h.toString(36); };
  const fmtTime = (sec) => { sec = Math.max(0, Math.floor(sec)); const h = Math.floor(sec / 3600), m = Math.floor(sec % 3600 / 60), s = sec % 60; return (h ? h + ':' + String(m).padStart(2, '0') : m) + ':' + String(s).padStart(2, '0'); };
  const plural = (n, a, b, c) => { const m10 = n % 10, m100 = n % 100; return n + ' ' + (m10 === 1 && m100 !== 11 ? a : m10 >= 2 && m10 <= 4 && (m100 < 10 || m100 >= 20) ? b : c); };
  const levelStr = (l) => '★'.repeat(l) + '<span class="muted">' + '★'.repeat(5 - l) + '</span>';
  const STATUS = { full: ['Полный разбор', 'full'], partial: ['Частичный разбор', 'partial'], none: ['Без разбора', 'none'] };

  D.quiz.forEach((q) => { q.id = hash(q.t + '|' + q.q + '|' + (q.code || '')); });
  const PROB = Object.fromEntries(D.problems.map((p) => [p.id, p]));
  const CONTEST = Object.fromEntries(D.contests.map((c) => [c.id, c]));

  // ---------- хранилище прогресса ----------
  const KEY = 'oly-progress-v1';
  let S;
  function loadStore() {
    let s = null;
    try { s = JSON.parse(localStorage.getItem(KEY)); } catch (e) { s = null; }
    S = Object.assign({ best: {}, quiz: {}, wrong: [], hints: {}, contest: null, history: [] }, s || {});
  }
  function save() { try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) { /* приватный режим */ } }
  const getCode = (pid) => { try { return localStorage.getItem('oly-code-' + pid); } catch (e) { return null; } };
  const setCode = (pid, v) => { try { localStorage.setItem('oly-code-' + pid, v); } catch (e) { /* ignore */ } };
  loadStore();

  // ---------- оценка задачи ----------
  // в оригинале подзадачи нумеруются с 0, если нулевая — «Примеры», иначе с 1
  const subNum = (p, i) => (p.subtasks[0] && /^Пример/.test(p.subtasks[0][1]) ? i : i + 1);
  function maxAuto(p) { return (p.testSubs || []).reduce((s, i) => s + (p.subtasks[i] ? p.subtasks[i][0] : 0), 0); }
  function scoreOf(p, results) {
    const bySub = {};
    results.forEach((r) => { if (r.sub >= 0) { bySub[r.sub] = bySub[r.sub] !== false && r.v === 'OK'; } });
    let sc = 0;
    Object.keys(bySub).forEach((k) => { if (bySub[k] && p.subtasks[k]) sc += p.subtasks[k][0]; });
    return { score: sc, bySub };
  }

  // ---------- проверка решений (Pyodide в Web Worker) ----------
  const Judge = {
    w: null, seq: 0, pending: new Map(), ready: null,
    start() {
      if (this.w) return this.ready;
      this.w = new Worker('js/judge-worker.js?v=3');
      this.w.onmessage = (e) => { const p = this.pending.get(e.data.id); if (p) { this.pending.delete(e.data.id); p.resolve(e.data); } };
      this.w.onerror = (e) => { this.pending.forEach((p) => p.reject(new Error(e.message || 'Ошибка воркера'))); this.pending.clear(); };
      this.ready = this.call({ type: 'init' }, 120000);
      return this.ready;
    },
    kill() { if (this.w) { this.w.terminate(); this.w = null; this.ready = null; } this.pending.forEach((p) => p.reject(new Error('stopped'))); this.pending.clear(); },
    call(msg, timeout) {
      const id = ++this.seq;
      return new Promise((resolve, reject) => {
        const t = setTimeout(() => { if (this.pending.has(id)) { this.pending.delete(id); reject(new Error('TL')); } }, timeout);
        this.pending.set(id, { resolve: (v) => { clearTimeout(t); resolve(v); }, reject: (e) => { clearTimeout(t); reject(e); } });
        this.w.postMessage(Object.assign({ id }, msg));
      });
    },
    async run(code, input, timeout = 10000) {
      await this.start();
      try {
        const r = await this.call({ type: 'run', code, input }, timeout);
        if (!r.ok) throw new Error(r.error);
        return r;
      } catch (e) {
        if (e.message === 'TL') { this.kill(); return { tl: true }; }
        throw e;
      }
    },
    async check(fn, inp, out, exp) {
      await this.start();
      const r = await this.call({ type: 'check', fn, inp, out, exp, checkers: D.checkers }, 20000);
      if (!r.ok) throw new Error(r.error);
      return r;
    },
  };
  const testCache = {};
  async function loadTests(pid) {
    if (!testCache[pid]) {
      const r = await fetch('data/tests/' + pid + '.json');
      if (!r.ok) throw new Error('Не удалось загрузить тесты');
      testCache[pid] = await r.json();
    }
    return testCache[pid];
  }
  const tokens = (s) => s.trim().split(/\s+/).filter(Boolean);
  function sameTokens(a, b, ci) {
    const x = tokens(a), y = tokens(b);
    if (x.length !== y.length) return false;
    for (let i = 0; i < x.length; i++) if (ci ? x[i].toUpperCase() !== y[i].toUpperCase() : x[i] !== y[i]) return false;
    return true;
  }

  // ---------- роутер ----------
  const routes = [];
  const route = (re, fn) => routes.push([re, fn]);
  let cleanup = [];
  function onLeave(fn) { cleanup.push(fn); }
  function render() {
    cleanup.forEach((f) => { try { f(); } catch (e) { /* ignore */ } });
    cleanup = [];
    const hashPath = (location.hash || '#/').slice(1);
    const [path, qs] = hashPath.split('?');
    const params = new URLSearchParams(qs || '');
    for (const [re, fn] of routes) {
      const m = path.match(re);
      if (m) {
        document.querySelectorAll('#nav a').forEach((a) => a.classList.toggle('on', path.startsWith('/' + a.dataset.nav)));
        fn(m, params);
        window.scrollTo(0, 0);
        return;
      }
    }
    app.innerHTML = '<div class="empty">Страница не найдена. <a href="#/">На главную</a></div>';
  }
  window.addEventListener('hashchange', render);

  // ---------- главная ----------
  function quizStats() {
    let r = 0, w = 0;
    Object.values(S.quiz).forEach((x) => { r += x.r; w += x.w; });
    return { r, w, n: Object.keys(S.quiz).length };
  }
  function topicAcc(t) {
    let r = 0, w = 0;
    D.quiz.forEach((q) => { if (q.t === t && S.quiz[q.id]) { r += S.quiz[q.id].r; w += S.quiz[q.id].w; } });
    return { r, w, acc: r + w ? r / (r + w) : null };
  }
  function nextProblem() {
    const cand = D.problems.filter((p) => p.status !== 'none' && (S.best[p.id] || 0) < maxAuto(p));
    cand.sort((a, b) => a.level - b.level);
    return cand[0];
  }

  route(/^\/$/, () => {
    const solved = D.problems.filter((p) => maxAuto(p) > 0 && (S.best[p.id] || 0) >= maxAuto(p)).length;
    const pts = D.problems.reduce((s, p) => s + (S.best[p.id] || 0), 0);
    const qs = quizStats();
    const np = nextProblem();
    const ct = S.contest;
    app.innerHTML = `
      <section class="hero">
        <div class="card">
          <h1>Готовимся к олимпиаде по информатике</h1>
          <p class="muted">${D.problems.length} задач Республиканской олимпиады (2–4 этапы, 2024–2026) с подсказками, разборами
          и проверкой решений на Python прямо в браузере. Плюс ${D.quiz.length} вопросов по темам и пробные туры на время.</p>
          <div class="row" style="margin-top:14px">
            <a class="btn primary" href="#/quiz/run?mode=daily">Тренировка дня · 10 вопросов</a>
            ${np ? `<a class="btn" href="#/problem/${np.id}">Следующая задача: ${esc(np.title)}</a>` : ''}
          </div>
          ${ct ? `<div class="note info" style="margin-top:14px">Идёт пробный тур «${esc(CONTEST[ct.cid].title)}». <a href="#/contest/${ct.cid}">Вернуться к туру →</a></div>` : ''}
        </div>
        <div class="card">
          <h3>Ваш прогресс</h3>
          <div class="stats">
            <div class="stat"><b>${solved} / ${D.problems.filter((p) => maxAuto(p) > 0).length}</b><span>задач на полный автобалл</span></div>
            <div class="stat"><b>${pts}</b><span>баллов по задачам</span></div>
            <div class="stat"><b>${qs.n} / ${D.quiz.length}</b><span>вопросов пройдено</span></div>
            <div class="stat"><b>${qs.r + qs.w ? Math.round(100 * qs.r / (qs.r + qs.w)) + '%' : '—'}</b><span>верных ответов</span></div>
          </div>
          <p class="small muted" style="margin-bottom:0">Ошибок на повторение: ${S.wrong.length}. ${S.wrong.length ? '<a href="#/quiz/run?mode=wrong">Разобрать →</a>' : ''}</p>
        </div>
      </section>
      <div class="grid">
        <a class="tile" href="#/problems"><h3>Задачи</h3><p>Условия, примеры, подзадачи, подсказки по шагам и разборы. Проверка решения на тестах.</p></a>
        <a class="tile" href="#/quiz"><h3>Тесты по темам</h3><p>Сложность алгоритмов, жадность, бинпоиск, ДП, графы, строки, биты… С объяснениями.</p></a>
        <a class="tile" href="#/theory"><h3>Теория</h3><p>Короткие шпаргалки с шаблонами кода — именно то, что встречается в этих задачах.</p></a>
        <a class="tile" href="#/contest"><h3>Пробный тур</h3><p>Реальный тур на время: 3 задачи, таймер, баллы по подзадачам.</p></a>
      </div>
      <h2>Туры</h2>
      <div class="grid">${D.contests.map((c) => {
        const ps = D.problems.filter((p) => p.contest === c.id);
        const got = ps.reduce((s, p) => s + (S.best[p.id] || 0), 0);
        return `<a class="tile" href="#/problems?contest=${c.id}"><h3>${esc(c.title)}</h3><p>${esc(c.date)} · ${ps.map((p) => p.letter).join(', ')}</p><p>Баллы: ${got} / ${ps.length * 100}</p></a>`;
      }).join('')}</div>`;
  });

  // ---------- список задач ----------
  route(/^\/problems$/, (m, params) => {
    const st = { topic: params.get('topic') || '', status: '', contest: params.get('contest') || '' };
    const draw = () => {
      const topicsUsed = [...new Set(D.problems.flatMap((p) => p.topics))];
      const chip = (key, val, label) => `<button class="chip ${st[key] === val ? 'on' : ''}" data-k="${key}" data-v="${val}">${label}</button>`;
      let html = `<h1>Задачи</h1>
        <p class="muted">Баллы считаются по подзадачам, для которых есть автотесты. Значок показывает, насколько полный разбор есть на сайте.</p>
        <div class="filters">${chip('topic', '', 'Все темы')}${topicsUsed.map((t) => chip('topic', t, esc(D.topics[t]))).join('')}</div>
        <div class="filters">${chip('status', '', 'Все')}${chip('status', 'todo', 'Нерешённые')}${chip('status', 'full', 'С полным разбором')}
          ${st.contest ? `<button class="chip on" data-k="contest" data-v="">${esc(CONTEST[st.contest].title)} ✕</button>` : ''}</div>`;
      let any = false;
      D.contests.forEach((c) => {
        if (st.contest && c.id !== st.contest) return;
        const ps = D.problems.filter((p) => p.contest === c.id
          && (!st.topic || p.topics.includes(st.topic))
          && (st.status !== 'full' || p.status === 'full')
          && (st.status !== 'todo' || (S.best[p.id] || 0) < Math.max(1, maxAuto(p))));
        if (!ps.length) return;
        any = true;
        html += `<section class="contest"><div class="contest-head"><h2>${esc(c.title)}</h2><span class="muted small">${esc(c.date)}</span>
          <span class="spacer"></span><a class="small" href="#/contest/${c.id}">Решать как тур →</a></div><div class="plist">`;
        ps.forEach((p) => {
          const best = S.best[p.id], mx = maxAuto(p);
          html += `<a class="prow" href="#/problem/${p.id}"><span class="letter">${p.letter}</span>
            <span><b>${esc(p.title)}</b><br><span class="small muted">${p.topics.map((t) => esc(D.topics[t])).join(' · ')}</span></span>
            <span class="meta"><span class="lvl" title="Сложность">${levelStr(p.level)}</span>
              <span class="badge ${STATUS[p.status][1]}">${STATUS[p.status][0]}</span>
              <span class="score ${best && best >= mx && mx ? 'done' : ''}">${best != null ? best : '—'}${mx ? ' / ' + mx : ''}</span></span></a>`;
        });
        html += '</div></section>';
      });
      if (!any) html += '<div class="empty">Под фильтр ничего не подошло.</div>';
      app.innerHTML = html;
      app.querySelectorAll('.chip').forEach((b) => b.onclick = () => { st[b.dataset.k] = b.dataset.v; draw(); });
    };
    draw();
  });

  // ---------- страница задачи ----------
  const STARTER = 'import sys\n\n\ndef main():\n    data = sys.stdin.read().split()\n    # ваше решение\n\n\nmain()\n';

  route(/^\/problem\/([\w-]+)$/, (m, params) => {
    const p = PROB[m[1]];
    if (!p) { app.innerHTML = '<div class="empty">Нет такой задачи.</div>'; return; }
    const c = CONTEST[p.contest];
    const inContest = S.contest && S.contest.cid === p.contest && Date.now() < S.contest.end;
    const mx = maxAuto(p);
    let tab = params.get('tab') || 'st';
    const shown = S.hints[p.id] || 0;

    const subsTable = `<div class="tbl-wrap"><table class="tbl"><tr><th>№</th><th>Ограничения</th><th>Баллы</th><th>Автотесты</th></tr>
      ${p.subtasks.map((s, i) => `<tr><td class="num">${subNum(p, i)}</td><td>${s[1]}</td><td class="num">${s[0]}</td>
        <td>${(p.testSubs || []).includes(i) ? '✓' : '<span class="muted">—</span>'}</td></tr>`).join('')}</table></div>`;
    const samples = p.samples.map((s, i) => `<div class="sample">
      <div><div class="lbl">Ввод ${i + 1}</div><pre><button class="copy" data-copy="${i}">копировать</button>${esc(s.in.replace(/\n$/, ''))}</pre></div>
      <div><div class="lbl">Вывод ${i + 1}</div><pre>${esc(s.out)}</pre></div></div>`).join('');

    app.innerHTML = `
      <div class="crumbs"><a href="#/problems">Задачи</a> / <a href="#/problems?contest=${c.id}">${esc(c.title)}</a></div>
      <div class="ptitle"><h1>${p.letter}. ${esc(p.title)}</h1></div>
      <div class="row" style="margin-bottom:6px">
        <span class="lvl">${levelStr(p.level)}</span>
        <span class="badge ${STATUS[p.status][1]}">${STATUS[p.status][0]}</span>
        ${p.topics.map((t) => `<a class="badge topic" href="#/problems?topic=${t}">${esc(D.topics[t])}</a>`).join('')}
        <span class="spacer"></span>
        <span class="small">Лучший результат: <b>${S.best[p.id] != null ? S.best[p.id] : '—'}</b>${mx ? ' / ' + mx : ''}</span>
      </div>
      ${p.partial_note ? `<div class="note warn">${p.partial_note}</div>` : ''}
      ${inContest ? `<div class="note info">Идёт пробный тур — подсказки и разбор скрыты. <a href="#/contest/${p.contest}">К туру →</a></div>` : ''}
      <div class="tabs" id="tabs">
        <button class="tab" data-t="st">Условие</button>
        ${inContest ? '' : '<button class="tab" data-t="hints">Подсказки</button><button class="tab" data-t="sol">Разбор и решение</button>'}
        <button class="tab" data-t="judge">Сдать решение</button>
      </div>
      <div id="tabbody"></div>`;

    const body = document.getElementById('tabbody');
    const tabs = {
      st: () => `<div class="statement card">
          <div class="limits"><span>Время: ${esc(p.tl)}</span><span>Память: ${esc(p.ml)}</span><span>Ввод/вывод: стандартный</span></div>
          ${p.legend}
          <h3>Входные данные</h3>${p.input}
          <h3>Выходные данные</h3>${p.output}
          <h3>Подзадачи</h3>${subsTable}
          <h3>Примеры</h3><div class="samples">${samples}</div>
          <p class="small muted" style="margin-top:14px">Условие пересказано кратко. Точные формулировки — в официальном PDF тура.</p>
        </div>`,
      hints: () => {
        const n = S.hints[p.id] || 0;
        return `<div class="card"><p class="muted">Открывайте подсказки по одной — каждая следующая ближе к решению.</p>
          ${p.hints.slice(0, n).map((h, i) => `<div class="hint"><b>Подсказка ${i + 1}.</b> ${h}</div>`).join('')}
          ${n < p.hints.length ? `<button class="btn" id="moreHint">Показать подсказку ${n + 1} из ${p.hints.length}</button>` : '<p class="muted">Подсказки закончились. Загляните в разбор.</p>'}</div>`;
      },
      sol: () => `<div class="card">
          ${p.status === 'none' ? '' : '<div class="note warn">Сначала попробуйте решить сами — разбор лучше читать после пары попыток.</div>'}
          <h3>Идея</h3>${p.idea}
          <p class="muted small">Сложность: ${esc(p.complexity)}</p>
          ${p.solution ? `<details class="fold"><summary>Решение на Python${p.status === 'partial' ? ' (частичное)' : ''}</summary><div class="in">
            <pre><code>${esc(p.solution)}</code></pre>
            <button class="btn sm" id="loadSol">Вставить в редактор</button></div></details>` : ''}
        </div>`,
      judge: () => `<div class="card">
          <p class="small muted">Пишите на Python 3: читайте из стандартного ввода, печатайте ответ. Код выполняется в вашем браузере (Pyodide).
          Тесты небольшие — они проверяют правильность, а не скорость; на олимпиаде те же идеи лучше писать на C++.</p>
          <textarea class="editor" id="code" spellcheck="false"></textarea>
          <div class="row" style="margin-top:10px">
            <button class="btn primary" id="submit">Проверить на ${p.testCount} тестах</button>
            <button class="btn" id="runOwn">Запустить на своём вводе</button>
            <span class="spacer"></span>
            <button class="btn sm" id="reset">Шаблон</button>
          </div>
          <div class="custom-io" id="customIo" hidden>
            <div><div class="lbl small muted">Ввод</div><textarea id="ownIn">${esc(p.samples[0] ? p.samples[0].in : '')}</textarea></div>
            <div><div class="lbl small muted">Вывод</div><textarea id="ownOut" readonly></textarea></div>
          </div>
          <div class="judge-status" id="jstatus"></div>
          <div id="jresult"></div>
        </div>`,
    };

    function show(t) {
      tab = t;
      document.querySelectorAll('#tabs .tab').forEach((b) => b.classList.toggle('on', b.dataset.t === t));
      body.innerHTML = tabs[t]();
      wire(t);
    }
    function wire(t) {
      body.querySelectorAll('[data-copy]').forEach((b) => b.onclick = () => {
        navigator.clipboard && navigator.clipboard.writeText(p.samples[+b.dataset.copy].in).then(() => { b.textContent = 'скопировано'; setTimeout(() => { b.textContent = 'копировать'; }, 1200); });
      });
      const more = document.getElementById('moreHint');
      if (more) more.onclick = () => { S.hints[p.id] = (S.hints[p.id] || 0) + 1; save(); show('hints'); };
      const ls = document.getElementById('loadSol');
      if (ls) ls.onclick = () => { if (!getCode(p.id) || confirm('Заменить ваш код в редакторе решением из разбора?')) { setCode(p.id, p.solution); show('judge'); } };
      if (t === 'judge') wireJudge();
    }

    function wireJudge() {
      const ta = document.getElementById('code');
      ta.value = getCode(p.id) || STARTER;
      ta.addEventListener('input', () => setCode(p.id, ta.value));
      ta.addEventListener('keydown', (e) => {
        if (e.key === 'Tab') {
          e.preventDefault();
          const s = ta.selectionStart, en = ta.selectionEnd;
          ta.value = ta.value.slice(0, s) + '    ' + ta.value.slice(en);
          ta.selectionStart = ta.selectionEnd = s + 4;
          setCode(p.id, ta.value);
        } else if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); submit(); }
      });
      document.getElementById('reset').onclick = () => { if (confirm('Вернуть пустой шаблон? Текущий код пропадёт.')) { ta.value = STARTER; setCode(p.id, STARTER); } };
      const status = document.getElementById('jstatus');
      const resBox = document.getElementById('jresult');
      let busy = false;
      const setBusy = (b) => { busy = b; document.getElementById('submit').disabled = b; document.getElementById('runOwn').disabled = b; };
      onLeave(() => { if (busy) Judge.kill(); });

      async function warm() {
        if (!Judge.w) status.innerHTML = '<span class="muted">Загружаю Python в браузер (≈10 МБ, только в первый раз)…</span>';
        await Judge.start();
      }

      document.getElementById('runOwn').onclick = async () => {
        const io = document.getElementById('customIo');
        if (io.hidden) { io.hidden = false; return; }
        if (busy) return;
        setBusy(true);
        try {
          await warm();
          status.innerHTML = '<span class="muted">Выполняю…</span>';
          const r = await Judge.run(ta.value, document.getElementById('ownIn').value);
          const out = document.getElementById('ownOut');
          if (r.tl) { out.value = ''; status.innerHTML = '<span class="vd TL">Превышено время (10 с)</span>'; }
          else { out.value = r.out + (r.err ? '\n--- ошибка ---\n' + r.err : ''); status.innerHTML = `<span class="muted">Готово за ${r.time.toFixed(2)} с</span>`; }
        } catch (e) { status.innerHTML = `<span class="vd RE">Ошибка: ${esc(e.message)}</span>`; }
        setBusy(false);
      };

      async function submit() {
        if (busy) return;
        setBusy(true);
        try {
          const tests = await loadTests(p.id);
          await warm();
          const results = tests.map((t) => ({ sub: t.sub, v: 'wait', t: 0 }));
          const draw = (done) => {
            const sc = scoreOf(p, results.filter((r) => r.v !== 'wait'));
            const cnt = results.filter((r) => r.v === 'OK').length;
            resBox.innerHTML = `
              ${done ? `<p class="total">Баллы: ${sc.score} из ${mx} <span class="muted small">(${cnt} из ${results.length} тестов)</span></p>` : ''}
              <div class="tbl-wrap"><table class="tbl tests-tbl"><tr><th>Тест</th><th>Подзадача</th><th>Вердикт</th><th>Время</th></tr>
              ${results.map((r, i) => `<tr data-i="${i}"><td class="num">${i + 1}</td><td>${tests[i].sample ? 'пример' : subNum(p, r.sub)}</td>
                <td><span class="vd ${r.v === 'wait' ? 'wait' : r.v}">${r.v === 'wait' ? '…' : r.v}</span>${r.msg ? ' <span class="small muted">' + esc(r.msg) + '</span>' : ''}</td>
                <td class="num">${r.t ? r.t.toFixed(2) + ' с' : ''}</td></tr>`).join('')}</table></div>
              <div id="detail"></div>
              <p class="small muted">OK — верно, WA — неверный ответ, RE — ошибка выполнения, TL — дольше 10 секунд. Нажмите на тест, чтобы увидеть данные.</p>`;
            resBox.querySelectorAll('tr[data-i]').forEach((tr) => tr.onclick = () => showDetail(+tr.dataset.i));
          };
          const showDetail = (i) => {
            const t = tests[i], r = results[i];
            const cut = (s) => (s && s.length > 3000 ? s.slice(0, 3000) + '\n… (обрезано)' : s || '');
            document.getElementById('detail').innerHTML = `<h3>Тест ${i + 1}</h3><div class="diff">
              <div><div class="small muted">Ввод</div><pre>${esc(cut(t.in))}</pre></div>
              <div><div class="small muted">Ожидалось</div><pre>${esc(cut(t.out))}</pre></div>
              <div><div class="small muted">Ваш вывод</div><pre>${esc(cut(r.out))}${r.err ? '\n\n' + esc(r.err) : ''}</pre></div></div>`;
          };
          draw(false);
          for (let i = 0; i < tests.length; i++) {
            status.innerHTML = `<span class="muted">Тест ${i + 1} из ${tests.length}…</span>`;
            const t = tests[i];
            let r;
            try { r = await Judge.run(ta.value, t.in); } catch (e) { r = { err: e.message, out: '' }; }
            const res = results[i];
            if (r.tl) { res.v = 'TL'; await Judge.start(); }
            else {
              res.t = r.time || 0; res.out = r.out; res.err = r.err;
              if (r.err) res.v = 'RE';
              else if (p.checker) {
                const c = await Judge.check(p.checker, t.in, r.out, t.out);
                res.v = c.good ? 'OK' : 'WA'; if (!c.good) res.msg = c.msg;
              } else res.v = sameTokens(r.out, t.out, p.id === 'hanabi') ? 'OK' : 'WA';
            }
            draw(false);
          }
          const sc = scoreOf(p, results).score;
          const prev = S.best[p.id];
          if (prev == null || sc > prev) S.best[p.id] = sc;
          if (S.contest && S.contest.cid === p.contest && Date.now() < S.contest.end) {
            S.contest.scores[p.id] = Math.max(S.contest.scores[p.id] || 0, sc);
          }
          save();
          draw(true);
          status.innerHTML = sc >= mx && mx ? '<div class="note ok">Все автотесты пройдены! 🎉</div>' : '';
        } catch (e) {
          status.innerHTML = `<span class="vd RE">Не удалось проверить: ${esc(e.message)}. Нужен интернет для загрузки Python.</span>`;
        }
        setBusy(false);
      }
      document.getElementById('submit').onclick = submit;
    }

    document.querySelectorAll('#tabs .tab').forEach((b) => b.onclick = () => show(b.dataset.t));
    if (inContest && (tab === 'hints' || tab === 'sol')) tab = 'st';
    show(tab);
    void shown;
  });

  // ---------- тесты (викторина) ----------
  route(/^\/quiz$/, () => {
    const topics = Object.keys(D.topics).filter((t) => D.quiz.some((q) => q.t === t));
    app.innerHTML = `<h1>Тесты по темам</h1>
      <p class="muted">После каждого ответа — объяснение. Вопросы «что выведет код» проверены запуском кода.</p>
      <div class="grid" style="margin-bottom:22px">
        <a class="tile" href="#/quiz/run?mode=daily"><h3>Тренировка дня</h3><p>10 вопросов, чаще — по слабым темам.</p></a>
        <a class="tile" href="#/quiz/run?mode=mix"><h3>Микс</h3><p>15 случайных вопросов из всех тем.</p></a>
        <a class="tile" href="#/quiz/run?mode=exam"><h3>Экзамен на время</h3><p>20 вопросов за 15 минут, ответы — в конце.</p></a>
        <a class="tile" href="#/quiz/run?mode=wrong"><h3>Работа над ошибками</h3><p>${S.wrong.length ? plural(S.wrong.length, 'вопрос', 'вопроса', 'вопросов') + ' с ошибками' : 'Пока ошибок нет'}</p></a>
      </div>
      <h2>По темам</h2>
      <div class="topic-grid">${topics.map((t) => {
        const n = D.quiz.filter((q) => q.t === t).length;
        const a = topicAcc(t);
        return `<a class="topic-pick" href="#/quiz/run?mode=topic&t=${t}"><span>${esc(D.topics[t])}<br><span class="small muted">${n} вопр.${a.acc != null ? ' · ' + Math.round(a.acc * 100) + '%' : ''}</span></span>
          <span class="bar"><div style="width:${a.acc != null ? Math.round(a.acc * 100) : 0}%"></div></span></a>`;
      }).join('')}</div>`;
  });

  function pickQuestions(mode, t) {
    if (mode === 'topic') return shuffle(D.quiz.filter((q) => q.t === t));
    if (mode === 'wrong') return shuffle(D.quiz.filter((q) => S.wrong.includes(q.id))).slice(0, 15);
    if (mode === 'exam') return shuffle(D.quiz).slice(0, 20);
    if (mode === 'daily') {
      // вес вопроса: невиданные и ошибочные — чаще
      const w = D.quiz.map((q) => {
        const s = S.quiz[q.id];
        const acc = topicAcc(q.t).acc;
        let x = s ? 1 + 3 * s.w / (s.r + s.w) : 2.5;
        if (acc != null) x *= 1.5 - acc;
        return [q, x * Math.random()];
      });
      return w.sort((a, b) => b[1] - a[1]).slice(0, 10).map((x) => x[0]);
    }
    return shuffle(D.quiz).slice(0, 15);
  }

  route(/^\/quiz\/run$/, (m, params) => {
    const mode = params.get('mode') || 'mix';
    const t = params.get('t');
    const qs = pickQuestions(mode, t);
    if (!qs.length) { app.innerHTML = '<div class="empty">Здесь пока нет вопросов. <a href="#/quiz">К тестам</a></div>'; return; }
    const exam = mode === 'exam';
    const title = { topic: 'Тема: ' + (D.topics[t] || ''), wrong: 'Работа над ошибками', exam: 'Экзамен на время', daily: 'Тренировка дня', mix: 'Микс' }[mode];
    let i = 0;
    const answers = [];
    const deadline = exam ? Date.now() + 15 * 60 * 1000 : 0;
    let timerId = null;
    if (exam) { timerId = setInterval(tick, 500); onLeave(() => clearInterval(timerId)); }
    function tick() {
      const el = document.getElementById('qtimer');
      const left = (deadline - Date.now()) / 1000;
      if (el) { el.textContent = fmtTime(left); el.classList.toggle('low', left < 60); }
      if (left <= 0) { clearInterval(timerId); finish(); }
    }
    function record(q, ok) {
      const s = S.quiz[q.id] || { r: 0, w: 0 };
      if (ok) s.r++; else s.w++;
      S.quiz[q.id] = s;
      const k = S.wrong.indexOf(q.id);
      if (!ok && k < 0) S.wrong.push(q.id);
      if (ok && k >= 0 && mode === 'wrong') S.wrong.splice(k, 1);
      save();
    }
    function drawQ() {
      const q = qs[i];
      const order = shuffle(q.o.map((_, k) => k));
      app.innerHTML = `<div class="row"><h1 style="margin:0">${esc(title)}</h1><span class="spacer"></span>${exam ? '<span class="timer" id="qtimer"></span>' : ''}</div>
        <div class="progress"><div style="width:${100 * i / qs.length}%"></div></div>
        <div class="card"><div class="small muted">Вопрос ${i + 1} из ${qs.length} · ${esc(D.topics[q.t])}</div>
          <div class="quiz-q">${q.q}</div>
          ${q.code ? `<pre><code>${esc(q.code)}</code></pre>` : ''}
          <div class="opts">${order.map((k, j) => `<button class="opt" data-k="${k}"><span class="key">${j + 1}</span><span>${q.o[k]}</span></button>`).join('')}</div>
          <div id="fb"></div></div>
        <p class="small muted">Клавиши <span class="kbd">1</span>–<span class="kbd">4</span> — ответ, <span class="kbd">Enter</span> — дальше.</p>`;
      if (exam) tick();
      const btns = [...app.querySelectorAll('.opt')];
      let answered = false;
      const choose = (b) => {
        if (answered) return;
        answered = true;
        const k = +b.dataset.k, ok = k === q.a;
        answers.push({ q, k, ok });
        record(q, ok);
        if (exam) { next(); return; }
        btns.forEach((x) => { x.disabled = true; if (+x.dataset.k === q.a) x.classList.add('right'); });
        if (!ok) b.classList.add('wrong');
        document.getElementById('fb').innerHTML = `<div class="note ${ok ? 'ok' : 'warn'}"><b>${ok ? 'Верно!' : 'Неверно.'}</b> ${q.w}</div>
          <button class="btn primary" id="nextQ">${i + 1 < qs.length ? 'Дальше' : 'Результат'}</button>`;
        document.getElementById('nextQ').onclick = next;
        document.getElementById('nextQ').focus();
      };
      btns.forEach((b) => b.onclick = () => choose(b));
      const onKey = (e) => {
        if (e.target.tagName === 'TEXTAREA' || e.target.tagName === 'INPUT') return;
        const n = parseInt(e.key, 10);
        if (!answered && n >= 1 && n <= btns.length) choose(btns[n - 1]);
        else if (answered && e.key === 'Enter' && document.activeElement.id !== 'nextQ') next();
      };
      document.addEventListener('keydown', onKey);
      const prevNext = next;
      void prevNext;
      cleanupKey = () => document.removeEventListener('keydown', onKey);
    }
    let cleanupKey = null;
    onLeave(() => cleanupKey && cleanupKey());
    function next() {
      if (cleanupKey) { cleanupKey(); cleanupKey = null; }
      i++;
      if (i < qs.length) drawQ(); else finish();
    }
    let finished = false;
    function finish() {
      if (finished) return;
      finished = true;
      if (cleanupKey) { cleanupKey(); cleanupKey = null; }
      if (timerId) clearInterval(timerId);
      const r = answers.filter((a) => a.ok).length;
      S.history.unshift({ kind: 'quiz', title, date: Date.now(), score: r, total: qs.length });
      S.history = S.history.slice(0, 50);
      save();
      const wrong = answers.filter((a) => !a.ok);
      const skipped = qs.length - answers.length;
      app.innerHTML = `<h1>${esc(title)}: результат</h1>
        <div class="card"><p class="total">${r} из ${qs.length} (${Math.round(100 * r / qs.length)}%)</p>
          ${skipped ? `<p class="muted">Без ответа (время вышло): ${skipped}</p>` : ''}
          <div class="row"><a class="btn primary" href="#/quiz/run?mode=${mode}${t ? '&t=' + t : ''}&r=${Date.now()}">Ещё раз</a>
          ${S.wrong.length ? '<a class="btn" href="#/quiz/run?mode=wrong">Работа над ошибками</a>' : ''}<a class="btn" href="#/quiz">Все тесты</a></div></div>
        ${wrong.length ? '<h2>Ошибки</h2>' + wrong.map((a) => `<div class="card"><div class="quiz-q">${a.q.q}</div>
          ${a.q.code ? `<pre><code>${esc(a.q.code)}</code></pre>` : ''}
          <p>Ваш ответ: <span class="vd WA">${a.q.o[a.k]}</span> · Верно: <span class="vd OK">${a.q.o[a.q.a]}</span></p>
          <p class="muted">${a.q.w}</p></div>`).join('') : '<div class="note ok">Без ошибок!</div>'}`;
    }
    drawQ();
  });

  // ---------- теория ----------
  route(/^\/theory$/, () => {
    app.innerHTML = `<h1>Теория</h1><p class="muted">Шпаргалки по темам, которые встречаются в задачах этих туров.</p>
      <div class="grid">${D.theory.map((t) => `<a class="tile" href="#/theory/${t.id}"><h3>${esc(t.title)}</h3>
        <p>${D.quiz.filter((q) => q.t === t.id).length} вопросов · ${D.problems.filter((p) => p.topics.includes(t.id)).length} задач</p></a>`).join('')}</div>`;
  });
  route(/^\/theory\/([\w-]+)$/, (m) => {
    const t = D.theory.find((x) => x.id === m[1]);
    if (!t) { app.innerHTML = '<div class="empty">Нет такой темы.</div>'; return; }
    const ps = D.problems.filter((p) => p.topics.includes(t.id));
    const nq = D.quiz.filter((q) => q.t === t.id).length;
    app.innerHTML = `<div class="crumbs"><a href="#/theory">Теория</a></div><h1>${esc(t.title)}</h1>
      <div class="card">${t.body}<h3>Шаблон</h3><pre><code>${esc(t.code)}</code></pre></div>
      <div class="row" style="margin-top:14px">${nq ? `<a class="btn primary" href="#/quiz/run?mode=topic&t=${t.id}">Тест по теме (${nq})</a>` : ''}</div>
      ${ps.length ? `<h2>Задачи по теме</h2><div class="plist">${ps.map((p) => `<a class="prow" href="#/problem/${p.id}"><span class="letter">${p.letter}</span>
        <span><b>${esc(p.title)}</b><br><span class="small muted">${esc(CONTEST[p.contest].title)}</span></span>
        <span class="meta"><span class="lvl">${levelStr(p.level)}</span></span></a>`).join('')}</div>` : ''}`;
  });

  // ---------- пробный тур ----------
  route(/^\/contest$/, () => {
    const hist = S.history.filter((h) => h.kind === 'contest');
    app.innerHTML = `<h1>Пробный тур</h1>
      <p class="muted">Три задачи настоящего тура и таймер. Во время тура подсказки и разборы скрыты, баллы считаются по автотестам.
      Можно взять продолжительность как на олимпиаде или короче.</p>
      ${S.contest ? `<div class="note info">Уже идёт тур «${esc(CONTEST[S.contest.cid].title)}». <a href="#/contest/${S.contest.cid}">Продолжить →</a></div>` : ''}
      <div class="grid">${D.contests.map((c) => {
        const ps = D.problems.filter((p) => p.contest === c.id);
        const auto = ps.reduce((s, p) => s + maxAuto(p), 0);
        return `<a class="tile" href="#/contest/${c.id}"><h3>${esc(c.title)}</h3><p>${esc(c.date)}</p>
          <p>${ps.map((p) => p.letter + '. ' + esc(p.title)).join('<br>')}</p><p>Автопроверка: до ${auto} из ${ps.length * 100} баллов</p></a>`;
      }).join('')}</div>
      ${hist.length ? `<h2>История туров</h2><div class="tbl-wrap"><table class="tbl"><tr><th>Дата</th><th>Тур</th><th>Баллы</th></tr>
        ${hist.map((h) => `<tr><td>${new Date(h.date).toLocaleString('ru-RU')}</td><td>${esc(h.title)}</td><td class="num">${h.score} / ${h.total}</td></tr>`).join('')}</table></div>` : ''}`;
  });

  route(/^\/contest\/([\w-]+)$/, (m) => {
    const c = CONTEST[m[1]];
    if (!c) { app.innerHTML = '<div class="empty">Нет такого тура.</div>'; return; }
    const ps = D.problems.filter((p) => p.contest === c.id);
    const auto = ps.reduce((s, p) => s + maxAuto(p), 0);
    const cur = S.contest && S.contest.cid === c.id ? S.contest : null;
    if (!cur) {
      app.innerHTML = `<div class="crumbs"><a href="#/contest">Пробный тур</a></div><h1>${esc(c.title)}</h1>
        <div class="card"><p>${ps.map((p) => `<b>${p.letter}.</b> ${esc(p.title)} <span class="lvl">${levelStr(p.level)}</span>`).join('<br>')}</p>
        ${c.note ? `<p class="muted">${esc(c.note)}</p>` : ''}
        <p class="muted small">Автопроверка доступна для части подзадач: максимум ${auto} из ${ps.length * 100}. Остальное оцените сами по ограничениям подзадач.</p>
        ${S.contest ? `<div class="note warn">Сейчас идёт другой тур — новый его завершит.</div>` : ''}
        <div class="row"><span>Длительность:</span>
          ${[60, 120, 180, c.duration].filter((v, i, a) => a.indexOf(v) === i).sort((a, b) => a - b).map((v) => `<button class="btn ${v === c.duration ? 'primary' : ''}" data-dur="${v}">${v} мин${v === c.duration ? ' (как на олимпиаде)' : ''}</button>`).join('')}</div></div>`;
      app.querySelectorAll('[data-dur]').forEach((b) => b.onclick = () => {
        if (S.contest) finishContest();
        S.contest = { cid: c.id, start: Date.now(), end: Date.now() + (+b.dataset.dur) * 60000, scores: {} };
        save(); render();
      });
      return;
    }
    const drawRun = () => {
      const left = (cur.end - Date.now()) / 1000;
      const total = ps.reduce((s, p) => s + (cur.scores[p.id] || 0), 0);
      app.innerHTML = `<div class="crumbs"><a href="#/contest">Пробный тур</a></div>
        <div class="row"><h1 style="margin:0">${esc(c.title)}</h1><span class="spacer"></span>
          <span class="timer ${left < 300 ? 'low' : ''}" id="ctimer">${left > 0 ? fmtTime(left) : 'время вышло'}</span></div>
        <p class="muted">Баллы за тур: <b>${total}</b> (автопроверка до ${auto}).</p>
        <div class="plist">${ps.map((p) => `<a class="prow" href="#/problem/${p.id}?tab=judge"><span class="letter">${p.letter}</span>
          <span><b>${esc(p.title)}</b></span><span class="meta"><span class="score">${cur.scores[p.id] != null ? cur.scores[p.id] : '—'} / ${maxAuto(p)}</span></span></a>`).join('')}</div>
        <div class="row" style="margin-top:16px"><button class="btn" id="endC">Завершить тур</button></div>`;
      document.getElementById('endC').onclick = () => { if (confirm('Завершить тур?')) { finishContest(); render(); } };
      if (left <= 0) { finishContest(); render(); }
    };
    drawRun();
    const id = setInterval(() => {
      const el = document.getElementById('ctimer');
      const left = (cur.end - Date.now()) / 1000;
      if (left <= 0) { clearInterval(id); finishContest(); render(); return; }
      if (el) { el.textContent = fmtTime(left); el.classList.toggle('low', left < 300); }
    }, 1000);
    onLeave(() => clearInterval(id));
  });

  function finishContest() {
    const cur = S.contest;
    if (!cur) return;
    const c = CONTEST[cur.cid];
    const ps = D.problems.filter((p) => p.contest === cur.cid);
    S.history.unshift({ kind: 'contest', title: c.title, date: Date.now(), score: ps.reduce((s, p) => s + (cur.scores[p.id] || 0), 0), total: ps.length * 100 });
    S.history = S.history.slice(0, 50);
    S.contest = null;
    save();
  }

  // ---------- прогресс ----------
  route(/^\/progress$/, () => {
    const topics = Object.keys(D.topics).filter((t) => D.quiz.some((q) => q.t === t));
    app.innerHTML = `<h1>Прогресс</h1>
      <div class="card"><h3>Задачи</h3><div class="tbl-wrap"><table class="tbl"><tr><th>Задача</th><th>Тур</th><th>Баллы</th></tr>
        ${D.problems.map((p) => `<tr><td><a href="#/problem/${p.id}">${p.letter}. ${esc(p.title)}</a></td><td class="small">${esc(CONTEST[p.contest].title)}</td>
          <td class="num">${S.best[p.id] != null ? S.best[p.id] : '—'} / ${maxAuto(p)}</td></tr>`).join('')}</table></div></div>
      <div class="card"><h3>Тесты по темам</h3><div class="tbl-wrap"><table class="tbl"><tr><th>Тема</th><th>Пройдено</th><th>Точность</th></tr>
        ${topics.map((t) => { const a = topicAcc(t); const all = D.quiz.filter((q) => q.t === t); const seen = all.filter((q) => S.quiz[q.id]).length;
          return `<tr><td><a href="#/quiz/run?mode=topic&t=${t}">${esc(D.topics[t])}</a></td><td class="num">${seen} / ${all.length}</td><td class="num">${a.acc != null ? Math.round(a.acc * 100) + '%' : '—'}</td></tr>`; }).join('')}</table></div></div>
      ${S.history.length ? `<div class="card"><h3>История</h3><div class="tbl-wrap"><table class="tbl"><tr><th>Дата</th><th>Что</th><th>Результат</th></tr>
        ${S.history.map((h) => `<tr><td class="small">${new Date(h.date).toLocaleString('ru-RU')}</td><td>${h.kind === 'contest' ? 'Тур: ' : ''}${esc(h.title)}</td><td class="num">${h.score} / ${h.total}</td></tr>`).join('')}</table></div></div>` : ''}
      <div class="card"><h3>Перенос и сброс</h3><p class="small muted">Прогресс хранится только в этом браузере. Чтобы перенести на другое устройство — скопируйте код и вставьте там.</p>
        <div class="row"><button class="btn" id="exp">Скопировать прогресс</button><button class="btn" id="imp">Вставить прогресс</button><span class="spacer"></span><button class="btn" id="rst">Сбросить всё</button></div>
        <textarea class="editor" id="dump" style="min-height:90px;margin-top:10px" hidden></textarea></div>`;
    const dump = document.getElementById('dump');
    document.getElementById('exp').onclick = () => { dump.hidden = false; dump.value = btoa(unescape(encodeURIComponent(JSON.stringify(S)))); dump.select(); try { document.execCommand('copy'); } catch (e) { /* ignore */ } };
    document.getElementById('imp').onclick = () => {
      if (dump.hidden) { dump.hidden = false; dump.value = ''; dump.placeholder = 'Вставьте сюда код прогресса и нажмите «Вставить прогресс» ещё раз'; return; }
      try { const s = JSON.parse(decodeURIComponent(escape(atob(dump.value.trim())))); S = Object.assign({ best: {}, quiz: {}, wrong: [], hints: {}, contest: null, history: [] }, s); save(); render(); }
      catch (e) { alert('Не получилось прочитать код прогресса.'); }
    };
    document.getElementById('rst').onclick = () => { if (confirm('Удалить весь прогресс в этом браузере?')) { try { localStorage.removeItem(KEY); } catch (e) { /* ignore */ } loadStore(); render(); } };
  });

  // ---------- тема оформления ----------
  document.getElementById('themeBtn').onclick = () => {
    const cur = document.documentElement.dataset.theme || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    const next = cur === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem('oly-theme', next); } catch (e) { /* ignore */ }
  };

  render();
})();
