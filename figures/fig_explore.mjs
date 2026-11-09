// Exploratory figures, drawn from runs/explore.json: node fig_explore.mjs [explore.json] [outdir]
import { Sketch, INK } from './sketch.mjs';
import { readFileSync, writeFileSync } from 'node:fs';

const E = JSON.parse(readFileSync(process.argv[2] ?? '../runs/explore.json', 'utf8'));
const OUT = process.argv[3] ?? 'out';
const f1 = (x) => (Math.round(x * 10) / 10).toFixed(1);
const sgn = (x) => (x >= 0 ? '+' : '') + f1(x);
const scale = (d0, d1, r0, r1) => (v) => r0 + ((v - d0) / (d1 - d0)) * (r1 - r0);
const hollow = (s, x, y, c, d = 11) => s.circle(x, y, d, { stroke: c, width: 1.6, fill: INK.paper, fillStyle: 'solid', roughness: 0.8 });
const has = (t) => E.dev_mean[t] !== undefined;

// ---------- 1. Headroom: where the points were ----------
{
  const s = new Sketch(680, 452, 59);
  const X = scale(0, 100, 232, 640);
  const rewrites = E.operator.rewrites_r2_r5.names;
  const minimal = E.operator.minimal_edits.names.filter(has);
  const rows = [
    { t: 'bare model, no tools', k: 'v0-bare', c: INK.blue },
    { t: 'eyes only (r1a, accepted)', k: 'r1a', c: INK.gold, bold: true },
    { t: 'r1a run again', k: 'r1a-aa', c: INK.teal },
    { t: `${rewrites.length} rewrites, rounds 2-5`, dots: rewrites, c: INK.pink },
    { t: minimal.length > 1 ? `${minimal.length} one-rule edits` : 'one-rule edit', dots: minimal, c: INK.chalk },
    { t: '+ a calculation tool', k: 'x-calc-a', c: INK.mint, bold: true },
    { t: 'told the first move', k: 'r1a+oracle-move', c: INK.violet, dash: true },
  ];
  const y0 = 64, dy = 46, yEnd = y0 + (rows.length - 1) * dy;
  const r1 = E.dev_mean['r1a'][0];
  s.line(X(r1), y0 + dy - 22, X(r1), yEnd + 26, { stroke: INK.gold, width: 1.2, dash: '4 6', opacity: 0.8 });
  rows.forEach((r, i) => {
    const y = y0 + i * dy;
    s.text(r.t, 214, y + 5, { size: 14.5, color: r.bold ? r.c : INK.dim, anchor: 'end', weight: r.bold ? 'bold' : 'regular' });
    if (r.dots) {
      const v = r.dots.map((n) => E.dev_mean[n][0]);
      if (v.length > 1) s.line(X(Math.min(...v)), y, X(Math.max(...v)), y, { stroke: r.c, width: 1, roughness: 0.6, opacity: 0.6, single: true });
      v.forEach((m) => hollow(s, X(m), y, r.c, 9));
      return;
    }
    const [m, lo, hi] = E.dev_mean[r.k];
    s.interval(X(lo), X(hi), y, X(m), { color: r.c, width: r.bold ? 2.6 : 1.8, dot: r.bold ? 11 : 9 });
    s.text(f1(m), X(hi) + 10, y + 5, { size: 13, color: r.c });
  });
  // brackets: the oracle's headroom and how much of it calculation reached
  const yb = yEnd + 46, orc = E.dev_mean['r1a+oracle-move'][0], calc = E.dev_mean['x-calc-a'][0];
  const brace = (a, b, y, c, label, up) => {
    s.line(X(a), y, X(b), y, { stroke: c, width: 1.6, roughness: 0.9, single: true });
    s.line(X(a), y - 7, X(a), y + 1, { stroke: c, width: 1.4, single: true });
    s.line(X(b), y - 7, X(b), y + 1, { stroke: c, width: 1.4, single: true });
    s.text(label, X(b) + 10, y + 5 + (up ?? 0), { size: 13.5, color: c });
  };
  brace(r1, orc, yb, INK.violet, `${sgn(E.headroom.oracle_gain)} above the plateau`);
  brace(r1, calc, yb + 26, INK.mint, `${sgn(E.headroom.calc_gain)} reached, ${Math.round(E.headroom.recovered * 100)}% of it`);
  s.text('the eyes-only plateau', X(r1) - 8, yEnd + 30, { size: 12.5, color: INK.gold, anchor: 'end' });
  for (const v of [0, 20, 40, 60, 80, 100]) s.text(String(v), X(v), 26, { size: 12, color: INK.faint, anchor: 'middle' });
  s.text('dev score, 95% CI', 20, 26, { size: 12.5, color: INK.faint });
  const rw = rewrites.map((n) => f1(E.dev_mean[n][0])).join(', ');
  writeFileSync(`${OUT}/headroom.svg`, s.svg('Where the points were',
    `Dev scores on 120 puzzles with 95% confidence intervals. Bare model ${f1(E.dev_mean['v0-bare'][0])}. Eyes-only skill r1a ${f1(r1)}, and ${f1(E.dev_mean['r1a-aa'][0])} when run again. ` +
    `The ${rewrites.length} rewrites from rounds 2 to 5 scored ${rw}. One-rule edits scored ${minimal.map((n) => f1(E.dev_mean[n][0])).join(' and ')}. ` +
    `Adding a calculation tool scored ${f1(calc)}. Telling the model the first move scored ${f1(orc)}, so ${f1(E.headroom.oracle_gain)} points sat above the plateau, and the calculation tool reached ${Math.round(E.headroom.recovered * 100)}% of them.`));
}

// ---------- 2. Climbability: what the teacher's average step does to a gated climb ----------
{
  const s = new Sketch(680, 480, 61);
  const X = scale(-10, 8, 92, 600), Y = scale(0, 45, 330, 46);
  s.line(80, 336, 80, 40, { stroke: INK.faint, width: 1.3 });
  s.line(80, 336, 616, 336, { stroke: INK.faint, width: 1.3 });
  for (let v = 0; v <= 40; v += 10) { s.text(String(v), 70, Y(v) + 4, { size: 12, color: INK.faint, anchor: 'end' }); s.line(76, Y(v), 84, Y(v), { stroke: INK.faint, width: 1, single: true }); }
  for (let m = -10; m <= 8; m += 2) s.text(m ? sgn(m).replace('.0', '') : '0', X(m), 368, { size: 12, color: INK.faint, anchor: 'middle' });
  s.text('real gain after 5 rounds (points)', 20, 30, { size: 14, color: INK.dim });
  s.text('n = dev puzzles', 640, 30, { size: 12, color: INK.faint, anchor: 'end' });
  s.text("how much better the teacher's average proposal really is (points)", 346, 392, { size: 13, color: INK.dim, anchor: 'middle' });
  s.line(X(0), 336, X(0), 44, { stroke: INK.faint, width: 1, dash: '3 6', opacity: 0.7 });
  const curves = [['120', INK.gold, ['n = 120', '(ours)']], ['480', INK.teal, ['n = 480']]];
  for (const [n, c, lbl] of curves) {
    const pts = E.sim.curves[n].map((r) => [X(r.M), Y(Math.max(0, r.true_gain))]);
    s.curve(pts, { stroke: c, width: 2.4, roughness: 0.7, single: true });
    const last = E.sim.curves[n].at(-1);
    s.lines(lbl, X(8) + 8, Y(last.true_gain) + 5, { size: 13, color: c, lineHeight: 16 });
  }
  // measured operators, as a rug under the axis
  const rw = E.operator.rewrites_r2_r5, mi = E.operator.minimal_edits;
  const yr = 420;
  s.line(X(rw.mean - rw.tau), yr, X(rw.mean + rw.tau), yr, { stroke: INK.pink, width: 5, roughness: 0.5, opacity: 0.45, single: true });
  rw.diffs.forEach((d) => s.line(X(d), 340, X(d), 350, { stroke: INK.pink, width: 1.6, single: true }));
  hollow(s, X(rw.mean), yr, INK.pink, 12);
  s.text(`full rewrites ${sgn(rw.mean)}`, X(rw.mean) + 16, yr + 26, { size: 13.5, color: INK.pink, anchor: 'end' });
  if (mi.mean !== null) {
    mi.diffs.forEach((d) => s.line(X(d), 340, X(d), 350, { stroke: INK.chalk, width: 1.6, single: true }));
    hollow(s, X(mi.mean), yr, INK.chalk, 12);
    s.text(`one-rule edits ${sgn(mi.mean)}`, X(mi.mean) - 10, yr + 26, { size: 13.5, color: INK.chalk });
  }
  s.arrow(X(5.6), yr, X(8) + 28, yr, { stroke: INK.mint, width: 2, head: 10 });
  s.text(`calc tool ${sgn(E.operator.calc_surface.diffs[0])}`, X(8) + 26, yr + 26, { size: 13.5, color: INK.mint, anchor: 'end' });
  s.lines(['left of zero, nothing climbs,', 'whatever the size of the dev set'], X(-4.5), Y(16), { size: 13.5, color: INK.dim, anchor: 'middle', lineHeight: 18 });
  s.lines(['right of zero,', 'a bigger dev set lets', 'smaller steps through'], X(0.5), Y(41), { size: 13.5, color: INK.dim, lineHeight: 18 });
  const fa = Math.max(...E.sim.curves['120'].filter((r) => r.M < 0).map((r) => r.false_accepts));
  writeFileSync(`${OUT}/climbability.svg`, s.svg('What decides whether a gated climb climbs',
    `Simulated 5-round climbs using the measured noise (run-to-run sd ${f1(E.sim.SE)}, item-by-config sd ${f1(E.sim.SB)}) and the measured spread of the teacher's proposals (${f1(E.sim.tau)}). ` +
    `When the average proposal is worse than the incumbent, the real gain stays near zero for both 120 and 480 dev puzzles, and fewer than ${Math.ceil(fa * 100)} in 100 climbs accept a step that is really a loss. ` +
    `Measured average steps: full rewrites ${sgn(rw.mean)}${mi.mean !== null ? `, one-rule edits ${sgn(mi.mean)}` : ''}, adding a calculation tool ${sgn(E.operator.calc_surface.diffs[0])}.`));
}
console.log('ok');
