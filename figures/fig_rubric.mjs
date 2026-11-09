import { Sketch, INK } from './sketch.mjs';
import { writeFileSync } from 'node:fs';

const s = new Sketch(640, 430, 11);
const tick = (x, y, c = INK.mint) => { s.line(x, y, x + 6, y + 7, { stroke: c, width: 2.4, single: true }); s.line(x + 6, y + 7, x + 18, y - 9, { stroke: c, width: 2.4, single: true }); };
const cross = (x, y, c = INK.pink) => { s.line(x, y - 8, x + 14, y + 6, { stroke: c, width: 2.4, single: true }); s.line(x + 14, y - 8, x, y + 6, { stroke: c, width: 2.4, single: true }); };

s.text('White to move', 46, 34, { size: 16, color: INK.dim });
s.circle(206, 29, 9, { stroke: INK.chalk, width: 1, fill: INK.chalk, fillStyle: 'solid' });
s.text('White', 215, 34, { size: 12, color: INK.faint });
s.circle(256, 29, 9, { stroke: INK.chalk, width: 1.2, fill: INK.paper, fillStyle: 'solid' });
s.text('Black', 265, 34, { size: 12, color: INK.faint });
s.board(46, 46, 232, '8/1p6/p2PQ2p/1n2q3/1P3k1K/8/7P/8 w - - 1 46', {
  arrows: [{ from: 'd6', to: 'd8', color: INK.mint, bend: -6 }],
  highlight: [{ sq: 'd8', color: INK.mint }, { sq: 'e5', color: INK.pink }],
});
s.text('1. Qxe5+ Kxe5 2. d7, and it queens', 46, 330, { size: 15, color: INK.mint });
s.text('(the real idea: trade queens, win the race)', 46, 350, { size: 14, color: INK.faint });

const X = 318;
s.text('the model answered...', X, 34, { size: 16, color: INK.dim });
s.rect(X, 46, 296, 134, { stroke: INK.faint, width: 1.2, roughness: 1.6 });
s.lines(['"Black\'s queen on e5 is undefended', 'and under attack. By capturing it', 'with check, White wins the queen', 'immediately..."', 'motif: hangingPiece'], X + 12, 72, { size: 15.5, color: INK.chalk, lineHeight: 23 });

let y = 212;
const row = (label, pts, ok, note) => {
  ok ? tick(X + 2, y - 6) : cross(X + 4, y - 4);
  s.text(label, X + 28, y, { size: 17, color: INK.chalk });
  s.text(pts, X + 296, y, { size: 17, anchor: 'end', color: ok ? INK.mint : INK.pink, weight: 'bold' });
  if (note) s.text(note, X + 28, y + 19, { size: 13.5, color: INK.faint });
  y += note ? 44 : 30;
};
row('move  Qxe5+', '40 / 40', true);
row('line  Qxe5+ Kxe5 d7', '15 / 15', true);
row('motif', '0 / 15', false, 'a promotion race, not a hanging piece');
row('explanation', '5 / 30', false, 'judge: the king on f4 defends the queen');
s.line(X, y - 12, X + 296, y - 10, { stroke: INK.dim, width: 1.2, single: true });
s.text('60 / 100', X + 296, y + 14, { size: 22, anchor: 'end', weight: 'bold', color: INK.gold });
s.text('a move-only benchmark says 100', X, y + 14, { size: 14.5, color: INK.dim });
s.arrow(X + 120, y + 32, 296, y + 52, { stroke: INK.gold, width: 1.6, bend: -14, head: 9 });
s.text('right move, wrong reason', 52, 404, { size: 21, weight: 'bold', color: INK.gold, rotate: -2 });
s.underline(52, 276, 412, { stroke: INK.gold, width: 1.6 });

writeFileSync(new URL('./out/rubric.svg', import.meta.url), s.svg(
  'Grading a real answer: right move, wrong reason',
  'A chess diagram, White to move. A real answer from the final configuration on a dev puzzle: it played the correct Qxe5+ and gave the correct line, earning 55 of 55 points for move and line, but said Black\'s queen on e5 was undefended and tagged the motif as a hanging piece. The black king on f4 defends the queen; the real idea is trading queens so the d-pawn promotes. Motif 0 of 15, explanation 5 of 30: 60 of 100, where a move-only benchmark would give 100.'));
