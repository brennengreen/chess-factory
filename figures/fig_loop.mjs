import { Sketch, INK } from './sketch.mjs';
import { writeFileSync } from 'node:fs';

const s = new Sketch(680, 500, 23);
const box = (x, y, w, h, c, o = {}) => s.rect(x, y, w, h, { stroke: c, width: 1.8, roughness: 1.3, ...o });

// Human library
for (const [i, c] of [INK.coral, INK.gold, INK.teal].entries()) {
  s.rect(40 + i * 3, 104 - i * 24, 104 - i * 8, 22, { stroke: c, width: 1.5, roughness: 1.2, fill: c, fillStyle: 'hachure', hachureGap: 6, fillWeight: 0.6 });
}
s.line(58, 108, 58, 120, { stroke: INK.coral, width: 1.2, single: true });
s.text('human chess books', 34, 150, { size: 16, color: INK.chalk });
s.lines(['Capablanca 1921, Lasker,', 'Wikipedia tactics pages'], 34, 170, { size: 12.5, color: INK.faint, lineHeight: 16 });

// Teacher
box(232, 52, 196, 92, INK.violet);
s.text('the teacher', 330, 84, { size: 21, weight: 'bold', color: INK.violet, anchor: 'middle' });
s.lines(['reads the books, studies', 'the failures, writes advice'], 330, 107, { size: 13, color: INK.dim, lineHeight: 17, anchor: 'middle' });
s.arrow(154, 96, 226, 96, { stroke: INK.dim, width: 1.6, bend: -6, head: 9 });
s.text('10 passages', 160, 84, { size: 11.5, color: INK.faint });

// Candidates
for (const [i, lbl] of ['SKILL.md', '+ tools'].entries()) {
  s.rect(494 + i * 22, 46 + i * 30, 118, 62, { stroke: INK.chalk, width: 1.4, roughness: 1.1, fill: INK.paper, fillStyle: 'solid' });
  s.text(lbl, 553 + i * 22, 66 + i * 30 + (i ? 22 : 0), { size: 14.5, color: INK.chalk, anchor: 'middle' });
}
s.text('2 candidates / round', 560, 156, { size: 13, color: INK.dim, anchor: 'middle' });
s.arrow(432, 92, 492, 86, { stroke: INK.violet, width: 1.8, bend: -8, head: 9 });

// Leak check funnel
s.poly([[508, 196], [624, 196], [584, 236], [584, 252], [548, 252], [548, 236]], { stroke: INK.coral, width: 1.6, roughness: 1.2 });
s.text('leak check', 566, 220, { size: 15, color: INK.coral, anchor: 'middle' });
s.lines(['no FENs, no IDs,', 'no solution lines'], 500, 222, { size: 12, color: INK.faint, lineHeight: 15, anchor: 'end' });
s.arrow(566, 164, 566, 190, { stroke: INK.dim, width: 1.6, head: 8 });

// Grader + gate
box(470, 290, 202, 104, INK.mint);
s.text('the grader', 571, 322, { size: 21, weight: 'bold', color: INK.mint, anchor: 'middle' });
s.lines(['120 dev puzzles, rules + a', 'rubric judge (other family)'], 571, 344, { size: 12.5, color: INK.dim, lineHeight: 16, anchor: 'middle' });
s.text('keep only if 95% lower bound > 0', 571, 384, { size: 12, color: INK.gold, anchor: 'middle' });
s.arrow(566, 258, 566, 284, { stroke: INK.dim, width: 1.6, head: 8 });

// Rejected
s.arrow(628, 398, 640, 446, { stroke: INK.pink, width: 1.5, bend: 6, head: 8 });
s.text('rejected', 614, 468, { size: 14, color: INK.pink });
s.line(606, 474, 668, 456, { stroke: INK.pink, width: 1.2, single: true, roughness: 0.6, opacity: 0.6 });

// Incumbent
box(256, 306, 156, 72, INK.gold, { width: 2.2 });
s.poly([[262, 314], [264, 298], [274, 306], [280, 292], [287, 304], [297, 296], [296, 312]], { stroke: INK.gold, width: 1.5, roughness: 0.9 });
s.text('incumbent', 334, 338, { size: 20, weight: 'bold', color: INK.gold, anchor: 'middle' });
s.text('best config so far', 334, 360, { size: 12.5, color: INK.dim, anchor: 'middle' });
s.arrow(464, 346, 418, 346, { stroke: INK.gold, width: 2, head: 9, bend: 4 });
s.text('accepted', 441, 334, { size: 12, color: INK.gold, anchor: 'middle' });

// Failures on train back to teacher
box(266, 194, 136, 56, INK.blue, { width: 1.4, roughness: 1.6 });
s.text('its failures', 334, 216, { size: 15.5, color: INK.blue, anchor: 'middle' });
s.text('on train puzzles only', 334, 236, { size: 12, color: INK.faint, anchor: 'middle' });
s.arrow(334, 300, 334, 256, { stroke: INK.blue, width: 1.8, head: 9, bend: -5 });
s.arrow(334, 190, 334, 150, { stroke: INK.blue, width: 1.8, head: 9, bend: 5 });

// Sealed test vault
const vx = 46, vy = 330;
s.rect(vx, vy, 120, 96, { stroke: INK.chalk, width: 2, roughness: 1.2, fill: INK.faint, fillStyle: 'cross-hatch', hachureGap: 9, fillWeight: 0.5 });
s.circle(vx + 60, vy + 48, 40, { stroke: INK.chalk, width: 2, fill: INK.paper, fillStyle: 'solid' });
s.line(vx + 60, vy + 48, vx + 72, vy + 38, { stroke: INK.chalk, width: 2, single: true });
s.text('the test vault', vx + 60, vy + 120, { size: 16, color: INK.chalk, anchor: 'middle' });
s.lines(['240 puzzles + 240 mirrored,', 'opened once, at the end'], vx + 60, vy + 140, { size: 12, color: INK.faint, lineHeight: 15, anchor: 'middle' });
s.arrow(252, 366, 172, 386, { stroke: INK.chalk, width: 1.4, bend: 8, head: 8, dash: '5 6' });
s.text('final round only', 186, 412, { size: 12, color: INK.faint, rotate: -10 });

// Loop annotation
s.text('one turn = one round', 34, 262, { size: 15, color: INK.gold, rotate: -4 });
s.underline(34, 176, 270, { stroke: INK.gold, width: 1.2 });
s.arrow(184, 250, 258, 228, { stroke: INK.gold, width: 1.2, bend: -10, head: 7 });

writeFileSync('out/loop.svg', s.svg(
  'The teacher/grader loop',
  'Human chess books feed a teacher model, which studies the incumbent configuration\'s failures on training puzzles and proposes two candidate skill and tool configurations per round. Candidates pass a leak check that bans positions, puzzle IDs and solution lines, then the grader scores them on 120 development puzzles. A candidate replaces the incumbent only if the one-sided 95% lower bound of its paired improvement is above zero; otherwise it is rejected. A sealed test vault of 240 puzzles plus 240 color-mirrored copies is opened once, after the final round.'));
console.log('out/loop.svg');
