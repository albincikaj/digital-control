"""Floating course calculator docked on the right edge of the app.

A tiny same-origin iframe injects the panel + its script into the parent Streamlit document once; it then lives in the
parent page (survives page switches and reruns). Math: mathjs served locally from /app/static (offline-capable).
Tabs: Calc (complex numbers with j, DEG/RAD, Ans, variables, history) · Roots (+ stability) · Matrix (det, inv, eig, Mv, Mⁿ) · Jury.
"""
from __future__ import annotations

import streamlit as st

CALC_JS = r"""
(function(){
if (document.getElementById('dcc-root')) return;
const LS = {get(k,d){try{const v=localStorage.getItem('dcc_'+k);return v===null?d:JSON.parse(v);}catch(e){return d;}},
            set(k,v){try{localStorage.setItem('dcc_'+k,JSON.stringify(v));}catch(e){}}};
const css = `
#dcc-tab{position:fixed;right:0;top:42%;z-index:999990;background:#ff4b4b;color:#fff;border:none;border-radius:10px 0 0 10px;
  padding:12px 8px;cursor:pointer;font:600 15px system-ui;writing-mode:vertical-rl;box-shadow:0 2px 10px rgba(0,0,0,.35)}
#dcc-root{position:fixed;right:0;top:0;height:100vh;width:360px;z-index:999991;background:#111827;color:#e5e7eb;
  border-left:1px solid #374151;box-shadow:-4px 0 18px rgba(0,0,0,.4);display:none;flex-direction:column;font:13px system-ui}
#dcc-root.open{display:flex}
#dcc-root .hd{display:flex;align-items:center;gap:6px;padding:8px 10px;border-bottom:1px solid #374151;background:#0b1220}
#dcc-root .hd b{flex:1;font-size:14px}
#dcc-root button{background:#1f2937;color:#e5e7eb;border:1px solid #374151;border-radius:6px;padding:6px 4px;cursor:pointer;font:13px system-ui}
#dcc-root button:hover{background:#374151}
#dcc-root button.pri{background:#ff4b4b;border-color:#ff4b4b;color:#fff}
#dcc-root button.on{background:#2563eb;border-color:#2563eb;color:#fff}
#dcc-root .tabs{display:flex;gap:4px;padding:6px 8px}
#dcc-root .tabs button{flex:1}
#dcc-root .body{flex:1;overflow:auto;padding:8px 10px}
#dcc-root textarea,#dcc-root input{width:100%;box-sizing:border-box;background:#0b1220;color:#f9fafb;border:1px solid #374151;
  border-radius:6px;padding:6px;font:14px ui-monospace,monospace}
#dcc-root .res{font:600 17px ui-monospace,monospace;color:#86efac;min-height:22px;margin:6px 0;word-break:break-all}
#dcc-root .err{color:#fca5a5;font-size:12px;min-height:16px}
#dcc-root .keys{display:grid;grid-template-columns:repeat(6,1fr);gap:4px;margin-top:6px}
#dcc-root .row{display:flex;gap:4px;margin-top:6px}
#dcc-root .row>*{flex:1}
#dcc-root .hist div{padding:3px 4px;border-bottom:1px solid #1f2937;cursor:pointer;font:12px ui-monospace,monospace}
#dcc-root .hist div:hover{background:#1f2937}
#dcc-root .hint{color:#9ca3af;font-size:11.5px;line-height:1.35;margin-top:6px}
#dcc-root table{border-collapse:collapse;width:100%;font:12px ui-monospace,monospace;margin-top:6px}
#dcc-root td{border:1px solid #374151;padding:3px;text-align:right}
#dcc-root .grid{display:grid;gap:4px;margin-top:6px}
#dcc-root .ok{color:#86efac}#dcc-root .bad{color:#fca5a5}
`;
const st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);
const tab = document.createElement('button'); tab.id='dcc-tab'; tab.textContent='🧮 Calculator'; document.body.appendChild(tab);
const root = document.createElement('div'); root.id='dcc-root'; document.body.appendChild(root);
root.innerHTML = `
<div class="hd"><b>🧮 Course calculator</b><button id="dcc-mode" title="Angle unit for sin/cos/tan/atan2/arg">DEG</button><button id="dcc-close" title="Close">✕</button></div>
<div class="tabs"><button data-t="calc" class="on">Calc</button><button data-t="roots">Roots</button><button data-t="mat">Matrix</button><button data-t="jury">Jury</button></div>
<div class="body">
 <div data-p="calc">
  <textarea id="dcc-in" rows="2" placeholder="e.g. exp(-0.25)   abs(0.5+4j)   atan2(4,0.5)   T=0.25"></textarea>
  <div class="res" id="dcc-out"></div><div class="err" id="dcc-err"></div>
  <div class="row"><button class="pri" id="dcc-eq">= (Enter)</button><button id="dcc-ins" title="Put the result into the answer box you clicked last">↳ Insert</button><button id="dcc-copy">Copy</button><button id="dcc-clr">C</button></div>
  <div class="keys" id="dcc-keys"></div>
  <div class="hint">Complex: <code>3+4j</code>, <code>abs</code>, <code>arg</code> (in DEG/RAD mode), <code>re</code>, <code>im</code>, <code>rect(r,θ)</code>.
   <code>^</code> power, <code>sqrt</code>, <code>exp</code>, <code>ln</code>, <code>log10</code>, <code>atan2(y,x)</code>. Variables: <code>a=0.8</code>, last result: <code>Ans</code>.
   Lists: <code>[1, 2.8, 2.08]</code>. Enter = evaluate, Shift+Enter = new line.</div>
  <div class="hint"><b>History</b> (click to reuse)</div><div class="hist" id="dcc-hist"></div>
 </div>
 <div data-p="roots" style="display:none">
  <div class="hint">Coefficients, highest power first (as in MATLAB <code>roots</code>): e.g. <code>1, 0.2, -0.5, 0.1</code> for z³+0.2z²−0.5z+0.1</div>
  <input id="dcc-pc" value="1, -1.3, 0.4">
  <div class="row"><button class="pri" id="dcc-pr">Roots</button></div>
  <div id="dcc-pout"></div>
 </div>
 <div data-p="mat" style="display:none">
  <div class="row"><button id="dcc-m2" class="on">2×2</button><button id="dcc-m3">3×3</button></div>
  <div class="hint">Matrix M (row by row)</div><div class="grid" id="dcc-mg"></div>
  <div class="hint">Vector v (for M·v)</div><div class="grid" id="dcc-vg"></div>
  <div class="row"><button id="dcc-det">det</button><button id="dcc-inv">inverse</button><button id="dcc-eig">eigenvalues</button></div>
  <div class="row"><button id="dcc-mv">M·v</button><button id="dcc-vm">vᵀ·M</button><button id="dcc-pow">M^n</button><input id="dcc-n" value="2" style="max-width:50px"></div>
  <div id="dcc-mout"></div>
  <div class="hint">Q_C = [h, Gh, …]: use M·v repeatedly. Q_O = [cᵀ; cᵀG; …]: use vᵀ·M repeatedly.</div>
 </div>
 <div data-p="jury" style="display:none">
  <div class="hint">Coefficients a_n … a_0 (highest power first), e.g. <code>1, 0.2, -0.5, 0.1</code>. Use this to CHECK your hand-made table.</div>
  <input id="dcc-jc" value="1, 0.2, -0.5, 0.1">
  <div class="row"><button class="pri" id="dcc-jr">Jury test</button></div>
  <div id="dcc-jout"></div>
 </div>
</div>`;
const $ = id => document.getElementById(id);
let deg = LS.get('deg', true), open = LS.get('open', false), lastAns = 0, hist = LS.get('hist', []), scope = {};
let lastInput = null;
document.addEventListener('focusin', e => { const t = e.target;
  if ((t.tagName === 'INPUT' || t.tagName === 'TEXTAREA') && !root.contains(t)) lastInput = t; }, true);
function layout(){ root.classList.toggle('open', open); tab.style.display = open ? 'none' : 'block';
  pad(); LS.set('open', open); }
function pad(){ const a = document.querySelector('[data-testid="stAppViewContainer"]');
  if (a) { const want = open ? '360px' : ''; if (a.style.paddingRight !== want) { a.style.paddingRight = want; a.style.boxSizing = 'border-box'; } } }
tab.onclick = () => { open = true; layout(); setTimeout(() => $('dcc-in').focus(), 250); };
$('dcc-close').onclick = () => { open = false; layout(); };
function setMode(){ $('dcc-mode').textContent = deg ? 'DEG' : 'RAD'; $('dcc-mode').classList.toggle('on', deg); LS.set('deg', deg); }
$('dcc-mode').onclick = () => { deg = !deg; setMode(); };
root.querySelectorAll('.tabs button').forEach(b => b.onclick = () => {
  root.querySelectorAll('.tabs button').forEach(x => x.classList.toggle('on', x === b));
  root.querySelectorAll('[data-p]').forEach(p => p.style.display = p.dataset.p === b.dataset.t ? '' : 'none'); });

// ---------------------------------------------------------------- number formatting
function fmtR(x){ if (!isFinite(x)) return String(x); if (Math.abs(x) < 1e-12) return '0';
  const a = Math.abs(x); if (a >= 1e6 || a < 1e-4) return x.toExponential(5).replace(/\.?0+e/, 'e');
  return String(parseFloat(x.toPrecision(10))); }
function fmtC(re, im){ if (Math.abs(im) < 1e-12) return fmtR(re); if (Math.abs(re) < 1e-12) return fmtR(im) + 'j';
  return fmtR(re) + (im < 0 ? ' - ' : ' + ') + fmtR(Math.abs(im)) + 'j'; }
function fmt(v){ const M = window.math;
  if (v === undefined || v === null) return '';
  if (typeof v === 'number') return fmtR(v);
  if (typeof v === 'boolean') return String(v);
  if (M && M.isComplex(v)) return fmtC(v.re, v.im);
  if (M && (M.isMatrix(v) || Array.isArray(v))) { const a = M.isMatrix(v) ? v.toArray() : v;
    if (a.length && Array.isArray(a[0])) return a.map(r => r.map(fmt).join(', ')).join(' ; ');
    return a.map(fmt).join(', '); }
  if (M && M.isUnit && M.isUnit(v)) return v.toString();
  return String(v); }
function plain(v){ // text for inserting into answer boxes
  const M = window.math; if (M && M.isComplex(v) && Math.abs(v.im) > 1e-12) return fmt(v); return fmt(v).replace(/ ; /g, ', '); }

// ---------------------------------------------------------------- expression evaluation
function prep(s){ // j-notation → i ; ln → log ; ×÷ ; implicit '2j'
  return s.replace(/×/g, '*').replace(/÷/g, '/').replace(/π/g, 'pi').replace(/√/g, 'sqrt')
          .replace(/(\d(?:\.\d*)?|\.\d+)\s*j\b/g, '$1i').replace(/\bj\b/g, 'i').replace(/\bln\s*\(/g, 'log(').replace(/,(?=\s*\d)/g, ', '); }
function makeScope(){ const M = window.math, r = x => deg ? x * Math.PI / 180 : x, d = x => deg ? x * 180 / Math.PI : x;
  return Object.assign(scope, {
    sin: x => M.sin(typeof x === 'number' ? r(x) : x), cos: x => M.cos(typeof x === 'number' ? r(x) : x), tan: x => M.tan(typeof x === 'number' ? r(x) : x),
    asin: x => d(M.asin(x)), acos: x => d(M.acos(x)), atan: x => d(M.atan(x)), atan2: (y, x) => d(Math.atan2(y, x)),
    arg: z => d(M.arg(z)), angle: z => d(M.arg(z)), rect: (rr, th) => M.complex({abs: rr, arg: r(th)}),
    Ans: lastAns, ans: lastAns }); }
function evaluate(){ const M = window.math, s = $('dcc-in').value.trim(); $('dcc-err').textContent = '';
  if (!s) return; if (!M) { $('dcc-err').textContent = 'Math library not loaded yet — try again in a second.'; return; }
  try { makeScope(); let res; const lines = s.split('\n').filter(l => l.trim());
    for (const l of lines) res = M.evaluate(prep(l), scope);
    if (res && res.entries) res = res.entries[res.entries.length - 1];
    lastAns = res; $('dcc-out').textContent = '= ' + fmt(res); $('dcc-out').dataset.v = plain(res);
    hist.unshift(s + '  →  ' + fmt(res)); hist = hist.slice(0, 40); LS.set('hist', hist); drawHist();
  } catch (e) { $('dcc-err').textContent = e.message; } }
function drawHist(){ $('dcc-hist').innerHTML = ''; hist.forEach(h => { const d = document.createElement('div'); d.textContent = h;
  d.onclick = () => { $('dcc-in').value = h.split('  →  ')[0]; $('dcc-in').focus(); }; $('dcc-hist').appendChild(d); }); }
$('dcc-eq').onclick = evaluate;
$('dcc-in').addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); evaluate(); } e.stopPropagation(); });
$('dcc-clr').onclick = () => { $('dcc-in').value = ''; $('dcc-out').textContent = ''; $('dcc-err').textContent = ''; };
$('dcc-copy').onclick = () => { const v = $('dcc-out').dataset.v || ''; try { navigator.clipboard.writeText(v); } catch (e) {} };
function insertInto(el, val){ const proto = el.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
  const setter = Object.getOwnPropertyDescriptor(proto, 'value').set; setter.call(el, val);
  el.dispatchEvent(new Event('input', {bubbles: true})); el.focus(); }
$('dcc-ins').onclick = () => { const v = $('dcc-out').dataset.v; if (!v) return;
  if (!lastInput || !document.body.contains(lastInput)) { $('dcc-err').textContent = 'Click into an answer box first, then press ↳ Insert.'; return; }
  insertInto(lastInput, v); $('dcc-err').textContent = ''; };
const KEYS = ['7','8','9','/','(',')','4','5','6','*','^','sqrt(','1','2','3','-','exp(','ln(','0','.','j','+','abs(','arg(',
              'sin(','cos(','tan(','atan2(','pi','Ans',',','e','[',']','re(','im('];
KEYS.forEach(k => { const b = document.createElement('button'); b.textContent = k.replace('sqrt(', '√').replace('*', '×').replace('/', '÷');
  b.onclick = () => { const t = $('dcc-in'), p = t.selectionStart ?? t.value.length; t.value = t.value.slice(0, p) + k + t.value.slice(t.selectionEnd ?? p);
    t.focus(); t.selectionStart = t.selectionEnd = p + k.length; }; $('dcc-keys').appendChild(b); });
['dcc-pc','dcc-jc','dcc-n'].forEach(id => $(id).addEventListener('keydown', e => e.stopPropagation()));

// ---------------------------------------------------------------- polynomial roots (Durand–Kerner)
const C = {add:(a,b)=>[a[0]+b[0],a[1]+b[1]], sub:(a,b)=>[a[0]-b[0],a[1]-b[1]], mul:(a,b)=>[a[0]*b[0]-a[1]*b[1],a[0]*b[1]+a[1]*b[0]],
  div:(a,b)=>{const d=b[0]*b[0]+b[1]*b[1];return [(a[0]*b[0]+a[1]*b[1])/d,(a[1]*b[0]-a[0]*b[1])/d];}, abs:a=>Math.hypot(a[0],a[1])};
function parseList(s){ const v = s.replace(/[\[\]]/g, '').split(/[,;\s]+/).filter(x => x).map(x => window.math ? window.math.evaluate(prep(x), {}) : parseFloat(x));
  return v.map(x => typeof x === 'number' ? x : x.re); }
function roots(c){ while (c.length > 1 && Math.abs(c[0]) < 1e-14) c = c.slice(1); const n = c.length - 1; if (n < 1) return [];
  const a = c.map(x => x / c[0]); let z = []; for (let i = 0; i < n; i++) z.push([Math.cos(2*Math.PI*i/n + 0.4) * 0.9, Math.sin(2*Math.PI*i/n + 0.4) * 0.9]);
  const P = x => { let r = [1, 0]; for (let i = 1; i <= n; i++) r = C.add(C.mul(r, x), [a[i], 0]); return r; };
  for (let it = 0; it < 500; it++) { let mx = 0; for (let i = 0; i < n; i++) { let den = [1, 0];
      for (let j = 0; j < n; j++) if (j !== i) den = C.mul(den, C.sub(z[i], z[j]));
      const dz = C.div(P(z[i]), den); z[i] = C.sub(z[i], dz); mx = Math.max(mx, C.abs(dz)); } if (mx < 1e-14) break; }
  return z.map(r => [Math.abs(r[0]) < 1e-10 ? 0 : r[0], Math.abs(r[1]) < 1e-10 ? 0 : r[1]]).sort((p, q) => C.abs(q) - C.abs(p)); }
$('dcc-pr').onclick = () => { try { const c = parseList($('dcc-pc').value), r = roots(c);
  let h = '<table><tr><td>root</td><td>|root|</td><td>Re</td></tr>';
  r.forEach(x => h += `<tr><td>${fmtC(x[0], x[1])}</td><td>${fmtR(C.abs(x))}</td><td>${fmtR(x[0])}</td></tr>`);
  const zs = r.every(x => C.abs(x) < 1 - 1e-12), ss = r.every(x => x[0] < -1e-12);
  h += `</table><div class="hint">z-polynomial: <b class="${zs ? 'ok' : 'bad'}">${zs ? 'stable (all |root| < 1)' : 'NOT stable (some |root| ≥ 1)'}</b><br>
        s-polynomial: <b class="${ss ? 'ok' : 'bad'}">${ss ? 'stable (all Re < 0)' : 'NOT stable (some Re ≥ 0)'}</b></div>`;
  $('dcc-pout').innerHTML = h; } catch (e) { $('dcc-pout').innerHTML = '<div class="err">' + e.message + '</div>'; } };

// ---------------------------------------------------------------- matrices
let N = 2; const mdef = {2: [[0, 1], [-0.16, -1]], 3: [[0, 1, 0], [0, 0, 1], [0.315, -1.43, 2.1]]};
function drawGrid(){ const g = $('dcc-mg'), v = $('dcc-vg'); g.style.gridTemplateColumns = v.style.gridTemplateColumns = `repeat(${N},1fr)`;
  g.innerHTML = ''; v.innerHTML = ''; for (let i = 0; i < N; i++) for (let j = 0; j < N; j++) { const e = document.createElement('input');
    e.value = mdef[N][i][j]; e.id = `dcc-m${i}${j}`; e.addEventListener('keydown', ev => ev.stopPropagation()); g.appendChild(e); }
  for (let i = 0; i < N; i++) { const e = document.createElement('input'); e.value = i === N - 1 ? 1 : 0; e.id = `dcc-v${i}`;
    e.addEventListener('keydown', ev => ev.stopPropagation()); v.appendChild(e); } }
$('dcc-m2').onclick = () => { N = 2; $('dcc-m2').classList.add('on'); $('dcc-m3').classList.remove('on'); drawGrid(); };
$('dcc-m3').onclick = () => { N = 3; $('dcc-m3').classList.add('on'); $('dcc-m2').classList.remove('on'); drawGrid(); };
const num = s => { const M = window.math; const v = M ? M.evaluate(prep(String(s) || '0')) : parseFloat(s); return typeof v === 'number' ? v : v.re; };
const getM = () => { const m = []; for (let i = 0; i < N; i++) { m.push([]); for (let j = 0; j < N; j++) m[i].push(num($(`dcc-m${i}${j}`).value)); } return m; };
const getV = () => { const v = []; for (let i = 0; i < N; i++) v.push(num($(`dcc-v${i}`).value)); return v; };
const showM = (title, A) => { const rows = Array.isArray(A[0]) ? A : [A];
  $('dcc-mout').innerHTML = `<div class="hint"><b>${title}</b></div><table>` + rows.map(r => '<tr>' + r.map(x => `<td>${typeof x === 'string' ? x : fmtR(x)}</td>`).join('') + '</tr>').join('') + '</table>'; };
function wrap(f){ return () => { try { f(); } catch (e) { $('dcc-mout').innerHTML = '<div class="err">' + e.message + '</div>'; } }; }
$('dcc-det').onclick = wrap(() => showM('det(M)', [[window.math.det(getM())]]));
$('dcc-inv').onclick = wrap(() => showM('M⁻¹', window.math.inv(getM())));
$('dcc-mv').onclick = wrap(() => showM('M·v (column)', window.math.multiply(getM(), getV()).map(x => [x])));
$('dcc-vm').onclick = wrap(() => showM('vᵀ·M (row)', [window.math.multiply(getV(), getM())]));
$('dcc-pow').onclick = wrap(() => showM('M^' + $('dcc-n').value, window.math.pow(getM(), parseInt($('dcc-n').value))));
$('dcc-eig').onclick = wrap(() => { const A = getM(); let c; // characteristic polynomial
  if (N === 2) c = [1, -(A[0][0] + A[1][1]), A[0][0] * A[1][1] - A[0][1] * A[1][0]];
  else { const tr = A[0][0] + A[1][1] + A[2][2]; const m2 = A[0][0]*A[1][1]-A[0][1]*A[1][0] + A[0][0]*A[2][2]-A[0][2]*A[2][0] + A[1][1]*A[2][2]-A[1][2]*A[2][1];
    c = [1, -tr, m2, -window.math.det(A)]; }
  const r = roots(c); showM('eigenvalues (char. poly ' + c.map(fmtR).join(', ') + ')', r.map(x => [fmtC(x[0], x[1]), '|λ| = ' + fmtR(C.abs(x))])); });
drawGrid();

// ---------------------------------------------------------------- Jury
$('dcc-jr').onclick = () => { try { const desc = parseList($('dcc-jc').value), n = desc.length - 1; let a = desc.slice().reverse();
  const P = z => desc.reduce((s, c) => s * z + c, 0); const rows = [a]; const conds = [];
  conds.push(['P(1) > 0', fmtR(P(1)), P(1) > 0]); const pm = Math.pow(-1, n) * P(-1);
  conds.push([`(−1)^${n}·P(−1) > 0`, fmtR(pm), pm > 0]); conds.push([`|a₀| < |a${n}|`, fmtR(Math.abs(a[0])) + ' vs ' + fmtR(Math.abs(a[n])), Math.abs(a[0]) < Math.abs(a[n])]);
  let cur = a, L = 'bcdefg', li = 0; while (cur.length > 3) { const m = cur.length - 1, nx = []; for (let k = 0; k < m; k++) nx.push(cur[0] * cur[k] - cur[m] * cur[m - k]);
    rows.push(nx); conds.push([`|${L[li]}₀| > |${L[li]}${m - 1}|`, fmtR(Math.abs(nx[0])) + ' vs ' + fmtR(Math.abs(nx[m - 1])), Math.abs(nx[0]) > Math.abs(nx[m - 1])]); cur = nx; li++; }
  let h = '<table>'; rows.forEach((r, i) => { const nm = i === 0 ? 'a' : L[i - 1];
    h += `<tr><td>${nm}</td>` + r.map(fmtR).map(x => `<td>${x}</td>`).join('') + '</tr>';
    h += `<tr><td>${nm} rev</td>` + r.slice().reverse().map(fmtR).map(x => `<td>${x}</td>`).join('') + '</tr>'; });
  h += '</table><table>' + conds.map(c => `<tr><td style="text-align:left">${c[0]}</td><td>${c[1]}</td><td class="${c[2] ? 'ok' : 'bad'}">${c[2] ? '✓' : '✗'}</td></tr>`).join('') + '</table>';
  const okAll = conds.every(c => c[2]); h += `<div class="hint"><b class="${okAll ? 'ok' : 'bad'}">${okAll ? 'asymptotically stable' : 'NOT asymptotically stable'}</b> (b_k = a₀a_k − a_n a_{n−k}, rows start with a₀)</div>`;
  $('dcc-jout').innerHTML = h; } catch (e) { $('dcc-jout').innerHTML = '<div class="err">' + e.message + '</div>'; } };

setMode(); drawHist(); layout();
if (!window.math) { const s = document.createElement('script'); s.src = '/app/static/math.min.js'; document.head.appendChild(s); }
// Streamlit re-renders the main container; keep the margin when the panel is open
new MutationObserver(pad).observe(document.body, {childList: true, subtree: true});
})();
"""


def mount():
    """Inject the calculator into the parent page once (idempotent; cheap on reruns)."""
    js = CALC_JS.replace("</script>", "<\\/script>")
    html = ("<script>(function(){try{var d=window.parent.document;if(d.getElementById('dcc-root'))return;"
            "var s=d.createElement('script');s.textContent=" + _js_string(js) + ";d.body.appendChild(s);}catch(e){console.error('calc',e);}})();</script>")
    st.iframe(html, height=1)


def _js_string(s: str) -> str:
    import json
    return json.dumps(s)
