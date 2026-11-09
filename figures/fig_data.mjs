// Data figures, drawn from runs/results.json: node fig_data.mjs [results.json] [outdir]
import { Sketch, INK } from './sketch.mjs';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';

const R = JSON.parse(readFileSync(process.argv[2] ?? '../runs/results.json', 'utf8'));
const OUT = process.argv[3] ?? 'out';
const E = JSON.parse(readFileSync(process.argv[4] ?? '../runs/explore.json', 'utf8'));
const CF = process.argv[5] ?? '../runs/confirm.json';
const C = existsSync(CF) ? JSON.parse(readFileSync(CF, 'utf8')) : null;
const EXTRA = [
  { label: ['one-rule', 'edits'], names: ['x-minimal-a', 'x-minimal-b'] },
  { label: ['+ calc', 'tool'], names: ['x-calc-a', 'x-calc-b'] },
].map((c) => ({ ...c, names: c.names.filter((n) => E.dev_mean[n]) }));
const f1 = (x) => (Math.round(x * 10) / 10).toFixed(1);
const sgn = (x) => (x >= 0 ? '+' : '') + f1(x);
const scale = (d0, d1, r0, r1) => (v) => r0 + ((v - d0) / (d1 - d0)) * (r1 - r0);
const vint = (s, x, y1, y2, yEst, c, o = {}) => {
  s.line(x, y1, x, y2, { stroke: c, width: o.width ?? 1.8, roughness: 0.6, single: true });
  s.line(x - 5, y1, x + 5, y1, { stroke: c, width: 1.4, roughness: 0.5, single: true });
  s.line(x - 5, y2, x + 5, y2, { stroke: c, width: 1.4, roughness: 0.5, single: true });
  s.circle(x, yEst, o.dot ?? 10, o.hollow ? { stroke: c, width: 1.6, fill: INK.paper, fillStyle: 'solid' } : { stroke: c, fill: c, fillStyle: 'solid' });
};
const wilson = (k, n, z = 1.96) => {
  const p = k / n, d = 1 + z * z / n, c = (p + z * z / (2 * n)) / d, h = (z * Math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / d;
  return [p, c - h, c + h];
};

// ---------- 1. The ladder: dev score per round, every candidate, accepted or not ----------
{
  const s = new Sketch(680, 420, 41);
  const H = R.climb, n = H.length;
  const vals = H.flatMap((h) => [h.incumbent_dev_mean, ...h.candidates.filter((c) => c.dev_mean).map((c) => c.dev_mean)]).flat()
    .concat(EXTRA.flatMap((c) => c.names.flatMap((m) => E.dev_mean[m])));
  const lo = Math.floor((Math.min(...vals) - 6) / 10) * 10, hi = Math.ceil((Math.max(...vals) + 6) / 10) * 10;
  const X = scale(0, n + EXTRA.length + 0.7, 92, 650), Y = scale(lo, hi, 330, 46);
  s.line(80, 336, 80, 40, { stroke: INK.faint, width: 1.3 });
  s.line(80, 336, 660, 336, { stroke: INK.faint, width: 1.3 });
  for (let v = lo; v <= hi; v += 10) { s.text(String(v), 70, Y(v) + 4, { size: 12, color: INK.faint, anchor: 'end' }); s.line(76, Y(v), 84, Y(v), { stroke: INK.faint, width: 1, single: true }); }
  s.text('dev score', 20, 30, { size: 14, color: INK.dim });
  for (let r = 0; r <= n; r++) s.text(r ? `round ${r}` : 'start', X(r), 358, { size: 13, color: INK.dim, anchor: 'middle' });
  const xd = (X(n) + X(n + 1)) / 2 + 6;
  s.line(xd, 40, xd, 340, { stroke: INK.faint, width: 1.1, dash: '3 6' });
  s.lines(['after the climb', '(exploratory)'], xd + 8, 34, { size: 12, color: INK.faint, lineHeight: 15 });
  EXTRA.forEach((c, k) => s.lines(c.label, X(n + 1 + k), 356, { size: 12.5, color: INK.dim, anchor: 'middle', lineHeight: 15 }));
  // incumbent staircase
  const steps = [[X(0), Y(H[0].incumbent_dev_mean[0])]];
  H.forEach((h, i) => {
    const next = h.accepted ? h.candidates.find((c) => c.name === h.new_incumbent).dev_mean[0] : h.incumbent_dev_mean[0];
    steps.push([X(i + 1) - 18, Y(h.incumbent_dev_mean[0])], [X(i + 1) - 18, Y(next)]);
    if (i === n - 1) steps.push([xd - 6, Y(next)]);
  });
  s.linear(steps, { stroke: INK.gold, width: 2.4, roughness: 0.8 });
  vint(s, X(0), Y(H[0].incumbent_dev_mean[1]), Y(H[0].incumbent_dev_mean[2]), Y(H[0].incumbent_dev_mean[0]), INK.gold);
  s.text('bare model', X(0) + 10, Y(H[0].incumbent_dev_mean[0]) + 24, { size: 13, color: INK.gold });
  H.forEach((h, i) => h.candidates.forEach((c, j) => {
    const x = X(i + 1) + (j - (h.candidates.length - 1) / 2) * 26;
    if (c.leaks?.length) { s.text('leak', x, Y(lo) - 6, { size: 12, color: INK.coral, anchor: 'middle' }); return; }
    if (!c.dev_mean) return;
    const won = h.accepted && c.name === h.new_incumbent;
    vint(s, x, Y(c.dev_mean[1]), Y(c.dev_mean[2]), Y(c.dev_mean[0]), won ? INK.gold : INK.pink, { hollow: !won, width: won ? 2 : 1.4 });
  }));
  const incEnd = H.at(-1).accepted ? H.at(-1).candidates.find((c) => c.name === H.at(-1).new_incumbent).dev_mean[0] : H.at(-1).incumbent_dev_mean[0];
  EXTRA.forEach((c, k) => c.names.forEach((m, j) => {
    const x = X(n + 1 + k) + (j - (c.names.length - 1) / 2) * 26, [mu, l, h] = E.dev_mean[m];
    const pass = E.vs_r1a[m].lo_one_sided > 0;
    if (pass) s.linear([[xd - 6, Y(incEnd)], [x - 16, Y(incEnd)], [x - 16, Y(mu)]], { stroke: INK.mint, width: 2, roughness: 0.8, dash: '5 6' });
    vint(s, x, Y(l), Y(h), Y(mu), pass ? INK.mint : INK.pink, { hollow: !pass, width: pass ? 2 : 1.4 });
  }));
  s.circle(330, 400, 10, { stroke: INK.gold, fill: INK.gold, fillStyle: 'solid' }); s.text('accepted', 342, 405, { size: 13, color: INK.dim });
  s.circle(420, 400, 10, { stroke: INK.pink, width: 1.6, fill: INK.paper, fillStyle: 'solid' }); s.text('rejected', 432, 405, { size: 13, color: INK.dim });
  s.circle(510, 400, 10, { stroke: INK.mint, fill: INK.mint, fillStyle: 'solid' }); s.text('would pass the gate', 522, 405, { size: 13, color: INK.dim });
  s.text('whiskers: 95% CI, 120 dev puzzles', 20, 405, { size: 12, color: INK.faint });
  writeFileSync(`${OUT}/ladder.svg`, s.svg('Hill climb on the dev set',
    `Dev score by round. The bare model starts at ${f1(H[0].incumbent_dev_mean[0])}. ` + H.map((h) => `Round ${h.round}: ${h.candidates.map((c) => c.leaks?.length ? `${c.name} failed the leak check` : c.dev_mean ? `${c.name} scored ${f1(c.dev_mean[0])} (paired lower bound ${f1(c.dev.lo_one_sided)})` : `${c.name} did not run`).join(', ')}; ${h.accepted ? `accepted ${h.new_incumbent}` : 'nothing accepted'}.`).join(' ')
    + ' After the climb, exploratory: ' + EXTRA.map((c) => `${c.label.join(' ')}: ${c.names.map((m) => `${m} scored ${f1(E.dev_mean[m][0])} (paired lower bound ${f1(E.vs_r1a[m].lo_one_sided)})`).join(', ')}`).join('; ') + '.'));
}

// ---------- 2. The noise floor: per-puzzle differences vs the average ----------
{
  const s = new Sketch(680, 380, 43);
  const X = scale(-100, 100, 60, 640);
  const rows = [
    { y: 92, d: R.aa.item_diffs, c: R.aa, col: INK.teal, t: 'same config, run twice on dev (A/A)' },
    { y: 252, d: R.primary_item_diffs, c: R.primary, col: INK.gold, t: 'bare vs final, the 240 test puzzles' },
  ];
  for (const r of rows) {
    s.text(r.t, 40, r.y - 50, { size: 15, color: r.col });
    r.d.forEach((v, i) => {
      const jit = (((i * 7919) % 97) / 97 - 0.5) * 52;
      s.raw(`<circle cx="${X(Math.max(-100, Math.min(100, v))).toFixed(1)}" cy="${(r.y + jit).toFixed(1)}" r="${(2 + ((i * 31) % 7) / 20).toFixed(2)}" fill="${r.col}" opacity="0.6"/>`);
    });
    s.line(X(0), r.y - 34, X(0), r.y + 58, { stroke: INK.faint, width: 1, dash: '3 5' });
    const z = r.d.filter((v) => v === 0).length;
    if (z) s.text(`${z} unchanged`, X(0) + 6, r.y - 30, { size: 12, color: INK.faint });
    s.interval(X(r.c.lo), X(r.c.hi), r.y + 50, X(r.c.diff), { color: INK.chalk, width: 2.6 });
    s.text(`mean ${sgn(r.c.diff)}  [${f1(r.c.lo)}, ${f1(r.c.hi)}]`, X(r.c.hi) + 12, r.y + 55, { size: 13, color: INK.chalk });
  }
  for (const v of [-100, -50, 0, 50, 100]) s.text(String(v), X(v), 352, { size: 12, color: INK.faint, anchor: 'middle' });
  s.text('score difference on one puzzle (points)', 340, 372, { size: 13, color: INK.dim, anchor: 'middle' });
  writeFileSync(`${OUT}/noise.svg`, s.svg('Noise on one puzzle versus the average',
    `Each dot is one puzzle. Running the same configuration twice on dev gives per-puzzle differences spread across the scale, but the mean difference is ${sgn(R.aa.diff)} points (95% CI ${f1(R.aa.lo)} to ${f1(R.aa.hi)}). Bare versus final on test gives a mean difference of ${sgn(R.primary.diff)} (95% CI ${f1(R.primary.lo)} to ${f1(R.primary.hi)}).`));
}

// ---------- 3. Forest plot of the final test ----------
{
  const rows = [
    ['score, test (primary)', R.primary, INK.gold, true],
    ['score, mirrored test', R.primary_mirror, INK.chalk],
    ['rules only, no judge', R.deterministic_only, INK.chalk],
    ['first move right (% points)', R.move_acc_diff, INK.chalk],
    [`second judge (${R.judge.primary_under_second.n} puzzles)`, R.judge.primary_under_second, INK.chalk],
    ['A/A: same config twice', R.aa, INK.teal],
    ['mirror minus original, final', R.memorisation.final, INK.teal],
    ['mirror minus original, bare', R.memorisation.bare, INK.teal],
  ];
  if (C) rows.push(['calc tool vs final, test', C.test, INK.mint, true]);
  const gap = C ? 24 : 0;
  const s = new Sketch(680, 60 + rows.length * 40 + 50 + gap, 47);
  const all = rows.flatMap((r) => [r[1].lo, r[1].hi]);
  const lo = Math.min(-5, Math.floor(Math.min(...all) / 5) * 5), hi = Math.ceil(Math.max(...all) / 5) * 5 + 5;
  const X = scale(lo, hi, 250, 610);
  const yEnd = 50 + rows.length * 40 + gap;
  s.line(X(0), 34, X(0), yEnd, { stroke: INK.faint, width: 1.2, dash: '4 6' });
  rows.forEach(([lbl, c, col, bold], i) => {
    const y = 60 + i * 40 + (i >= 8 ? gap : 0);
    if (i === 5) s.line(20, y - 20, 660, y - 20, { stroke: INK.faint, width: 0.8, opacity: 0.5, single: true });
    if (i === 8) { s.line(20, y - 34, 660, y - 34, { stroke: INK.faint, width: 0.8, opacity: 0.5, single: true }); s.text('after the climb, one look at test (exploratory)', 660, y - 14, { size: 12, color: INK.mint, anchor: 'end' }); }
    s.text(lbl, 236, y + 5, { size: 14, color: bold ? col : INK.dim, anchor: 'end', weight: bold ? 'bold' : 'regular' });
    s.interval(X(c.lo), X(c.hi), y, X(c.diff), { color: col, width: bold ? 3 : 2 });
    s.text(sgn(c.diff), X(c.hi) + 10, y + 5, { size: 13, color: col });
  });
  for (let v = lo; v <= hi; v += 5) if (v % 10 === 0) s.text(String(v), X(v), yEnd + 22, { size: 12, color: INK.faint, anchor: 'middle' });
  s.text('improvement (points), 95% CI', X((lo + hi) / 2), yEnd + 42, { size: 13, color: INK.dim, anchor: 'middle' });
  s.text('controls: should sit on zero', 660, 60 + 5 * 40 + 5, { size: 13, color: INK.teal, anchor: 'end' });
  writeFileSync(`${OUT}/forest.svg`, s.svg('Final results on the sealed test set',
    'Mean improvement with 95% confidence intervals. ' + rows.map(([l, c]) => `${l}: ${sgn(c.diff)} (${f1(c.lo)} to ${f1(c.hi)})`).join('; ') + '.'));
}

// ---------- 4. Puzzle rating curve ----------
{
  const s = new Sketch(680, 400, 53);
  const X = scale(1000, 2200, 80, 640), Y = scale(0, 1, 330, 50);
  s.line(70, 336, 70, 44, { stroke: INK.faint, width: 1.3 }); s.line(70, 336, 650, 336, { stroke: INK.faint, width: 1.3 });
  for (const v of [0, 0.25, 0.5, 0.75, 1]) s.text(`${v * 100}%`, 60, Y(v) + 4, { size: 12, color: INK.faint, anchor: 'end' });
  for (let r = 1000; r <= 2200; r += 200) s.text(String(r), X(r), 356, { size: 12, color: INK.faint, anchor: 'middle' });
  s.text('Lichess puzzle rating', 360, 382, { size: 13, color: INK.dim, anchor: 'middle' });
  s.text('first move right', 20, 30, { size: 14, color: INK.dim });
  const series = [['bare', R.rating_points.bare, R.summary.bare_test, INK.blue, -9], ['final', R.rating_points.final, R.summary.final_test, INK.gold, 9]];
  const fin = R.summary.final_test.rating;
  const human = [];
  for (let r = 1000; r <= 2200; r += 50) human.push([X(r), Y(1 / (1 + 10 ** ((r - fin[0]) / 400)))]);
  s.curve(human, { stroke: INK.chalk, width: 1.6, roughness: 0.6, single: true, opacity: 0.7, dash: '5 7' });
  s.lines([`a human solver`, `rated ~${Math.round(fin[0] / 10) * 10}`], X(1150), Y(0.97), { size: 13, color: INK.dim, lineHeight: 16 });
  for (const [name, pts, sum, col, off] of series) {
    for (let b = 1000; b < 2200; b += 200) {
      const inb = pts.filter(([r]) => r >= b && r < b + 200);
      if (inb.length < 5) continue;
      const [p, l, h] = wilson(inb.reduce((a, [, c]) => a + c, 0), inb.length);
      vint(s, X(b + 100) + off, Y(l), Y(h), Y(p), col, { dot: 9 });
    }
    const ly = name === 'final' ? 74 : 122;
    s.circle(452, ly - 5, 10, { stroke: col, fill: col, fillStyle: 'solid' });
    s.text(`${name === 'final' ? 'final (r1a)' : 'bare model'}: ${sum.move_k} / ${sum.n} right`, 466, ly, { size: 15, color: col, weight: 'bold' });
    s.text(`rating fit ~${Math.round(sum.rating[0] / 10) * 10} (95% CI ${Math.round(sum.rating[1])} to ${Math.round(sum.rating[2])})`, 466, ly + 18, { size: 12, color: INK.faint });
  }
  writeFileSync(`${OUT}/rating.svg`, s.svg('First-move accuracy by puzzle rating',
    `Share of the 240 test puzzles where the first move was right, in 200-point rating bands, with 95% intervals. Bare model: ${R.summary.bare_test.move_k} of 240 overall, fairly flat across bands. Final configuration r1a: ${R.summary.final_test.move_k} of 240, falling only slowly as puzzles get harder. A dashed curve shows what a human solver rated about ${Math.round(fin[0] / 10) * 10} would be expected to score, falling steeply with rating. Elo-style rating fits: bare about ${Math.round(R.summary.bare_test.rating[0])} (95% CI ${Math.round(R.summary.bare_test.rating[1])} to ${Math.round(R.summary.bare_test.rating[2])}), final about ${Math.round(fin[0])} (95% CI ${Math.round(fin[1])} to ${Math.round(fin[2])}).`));
}
console.log('ok');
