import { Sketch, INK } from './sketch.mjs';
import { writeFileSync } from 'node:fs';

const s = new Sketch(680, 548, 31);

// Three piles of puzzle cards
const pile = (x, c, name, n, sub, n2) => {
  for (let i = 3; i >= 0; i--) s.rect(x + i * 5, 54 - i * 5, 150, 84, { stroke: c, width: i ? 1 : 1.8, roughness: 1.2, fill: INK.paper, fillStyle: 'solid', opacity: i ? 0.7 : 1 });
  s.text(name, x + 12, 86, { size: 24, weight: 'bold', color: c });
  s.text(n, x + 12, 112, { size: 14, color: INK.chalk });
  if (n2) s.text(n2, x + 12, 129, { size: 12, color: INK.dim });
  s.lines(sub, x + 4, 166, { size: 13, color: INK.dim, lineHeight: 17 });
};
pile(20, INK.blue, 'train', '200 puzzles', ['the teacher may look', 'at these failures']);
pile(250, INK.mint, 'dev', '120 puzzles', ['the grader scores every', 'candidate here']);
pile(480, INK.chalk, 'test', '240 puzzles', ['sealed until the', 'final config is frozen'], '+ 240 mirrored twins');

// Eye over train, ruler over dev, padlock over test
s.ellipse(150, 30, 34, 16, { stroke: INK.blue, width: 1.4 });
s.circle(150, 30, 7, { stroke: INK.blue, fill: INK.blue, fillStyle: 'solid', width: 1 });
s.rect(358, 22, 44, 14, { stroke: INK.mint, width: 1.3 });
for (let i = 1; i < 6; i++) s.line(358 + i * 7.3, 22, 358 + i * 7.3, 28 + (i % 2) * 3, { stroke: INK.mint, width: 1, single: true });
s.rect(600, 26, 26, 20, { stroke: INK.chalk, width: 1.6, fill: INK.chalk, fillStyle: 'solid' });
s.curve([[605, 26], [604, 13], [613, 9], [622, 13], [621, 26]], { stroke: INK.chalk, width: 1.8, single: true });

// Walls between piles
s.line(234, 40, 236, 150, { stroke: INK.faint, width: 1.4, dash: '4 6' });
s.line(464, 34, 462, 150, { stroke: INK.coral, width: 2.4, roughness: 1.4 });
s.text('no peeking', 472, 212, { size: 14, color: INK.coral, rotate: -5 });
s.arrow(486, 196, 466, 160, { stroke: INK.coral, width: 1.2, head: 7, bend: -6 });
s.text('one puzzle per game, so no game shows up in two piles', 340, 238, { size: 13, color: INK.faint, anchor: 'middle' });

// The mirror test
const by = 296, bs = 200;
s.text('a train puzzle...', 26, by - 14, { size: 15, color: INK.dim });
s.board(26, by, bs, '4Q3/P2R4/8/8/1P2pk2/3n1p1K/6r1/8 b - - 0 56', {
  arrows: [{ from: 'd3', to: 'f2', color: INK.mint }, { from: 'g2', to: 'h2', color: INK.mint, trimEnd: 0.3 }],
});
s.text('Black: Nf2+ Kh4 Rh2#', 26, by + bs + 40, { size: 15, color: INK.mint });

s.text('...and its mirrored twin', 454, by - 14, { size: 15, color: INK.dim });
s.board(454, by, bs, '8/6R1/3N1P1k/1p2PK2/8/8/p2r4/4q3 w - - 0 56', {
  arrows: [{ from: 'd6', to: 'f7', color: INK.mint }, { from: 'g7', to: 'h7', color: INK.mint, trimEnd: 0.3 }],
});
s.text('White: Nf7+ Kh5 Rh7#', 454, by + bs + 40, { size: 15, color: INK.mint });

s.arrow(246, by + 76, 434, by + 76, { stroke: INK.gold, width: 1.8, bend: -18, head: 10 });
s.lines(['flip the board,', 'swap the colors'], 340, by + 38, { size: 15, color: INK.gold, anchor: 'middle', lineHeight: 18 });
s.lines(['same idea, new string.', 'A model that understands', 'scores the same on both.', 'A model that memorized', 'the internet does not.'], 340, by + 122, { size: 13.5, color: INK.chalk, anchor: 'middle', lineHeight: 18 });

writeFileSync('out/splits.svg', s.svg(
  'Three piles of puzzles, and a mirror test',
  'Puzzles are split into train (200, the teacher may look at failures), dev (120, the grader scores every candidate) and test (240 plus 240 mirrored twins, sealed until the final configuration is frozen). Each puzzle comes from a different game. Below, a training puzzle where Black mates with Nf2+ Kh4 Rh2# is shown next to its mirrored twin, where the board is flipped and colors swapped so White mates with Nf7+ Kh5 Rh7#. A model that understands the idea scores the same on both; a model that memorized published puzzles does not.'));
console.log('out/splits.svg');
