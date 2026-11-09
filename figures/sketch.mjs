// A tiny hand-drawn SVG kit: rough.js strokes, jittered handwriting outlined from Kalam (OFL),
// and a notebook-style chess diagram. Output is self-contained SVG with no fonts or scripts.
import rough from 'roughjs';
import opentype from 'opentype.js';
import { readFileSync, writeFileSync, mkdtempSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const here = dirname(fileURLToPath(import.meta.url));
const load = (f) => { const b = readFileSync(join(here, 'fonts', f)); return opentype.parse(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength)); };
export const FONTS = { regular: load('Kalam-Regular.ttf'), bold: load('Kalam-Bold.ttf'), light: load('Kalam-Light.ttf') };

export const INK = {
  chalk: '#ebe7ef', dim: '#a3a1aa', faint: '#6f6c78', paper: '#0a0b0e',
  pink: '#ff94c8', gold: '#ffd494', mint: '#a9efc0', blue: '#9dc8ff', violet: '#c7afff', coral: '#ffa888', teal: '#8ee5d8',
};

function mulberry(seed) {
  return () => { seed |= 0; seed = (seed + 0x6d2b79f5) | 0; let t = Math.imul(seed ^ (seed >>> 15), 1 | seed); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}

const r1 = (n) => Math.round(n * 10) / 10;
const FILES = { regular: 'Kalam-Regular.ttf', bold: 'Kalam-Bold.ttf', light: 'Kalam-Light.ttf' };
const PYFT = join(here, '..', '.venv', 'bin', 'pyftsubset');

function subset(weight, chars) {
  const dir = mkdtempSync(join(tmpdir(), 'kalam-'));
  const out = join(dir, 'f.woff2');
  execFileSync(PYFT, [join(here, 'fonts', FILES[weight]), `--text=${[...chars].join('')}`, '--flavor=woff2',
    `--output-file=${out}`, '--layout-features=', '--no-hinting', '--desubroutinize', '--name-IDs=']);
  return readFileSync(out).toString('base64');
}

export class Sketch {
  constructor(w, h, seed = 7) {
    this.w = w; this.h = h; this.seed = seed;
    this.rand = mulberry(seed);
    this.gen = rough.generator();
    this.parts = [];
    this.used = {};
  }

  _opts(o = {}) {
    return {
      stroke: o.stroke ?? INK.chalk, strokeWidth: o.width ?? 1.6, roughness: o.roughness ?? 1.1, bowing: o.bowing ?? 1.2,
      fill: o.fill, fillStyle: o.fillStyle ?? 'hachure', fillWeight: o.fillWeight ?? 0.9, hachureGap: o.hachureGap ?? 5.5,
      hachureAngle: o.hachureAngle ?? -41, seed: Math.floor(this.rand() * 2 ** 31), disableMultiStroke: o.single ?? false,
      preserveVertices: false,
    };
  }

  _emit(drawable, o = {}) {
    const op = o.opacity ?? 1;
    for (const p of this.gen.toPaths(drawable)) {
      p.d = p.d.replace(/(-?\d+\.\d)\d+/g, '$1');
      const fill = p.fill && p.fill !== 'none' ? p.fill : 'none';
      this.parts.push(`<path d="${p.d}" stroke="${p.stroke}" stroke-width="${p.strokeWidth}" fill="${fill}" stroke-linecap="round" stroke-linejoin="round"${o.dash ? ` stroke-dasharray="${o.dash}"` : ''}${op < 1 ? ` opacity="${op}"` : ''}/>`);
    }
    return this;
  }

  line(x1, y1, x2, y2, o) { return this._emit(this.gen.line(x1, y1, x2, y2, this._opts(o)), o); }
  rect(x, y, w, h, o) { return this._emit(this.gen.rectangle(x, y, w, h, this._opts(o)), o); }
  ellipse(cx, cy, w, h, o) { return this._emit(this.gen.ellipse(cx, cy, w, h, this._opts(o)), o); }
  circle(cx, cy, d, o) { return this._emit(this.gen.circle(cx, cy, d, this._opts(o)), o); }
  poly(pts, o) { return this._emit(this.gen.polygon(pts, this._opts(o)), o); }
  curve(pts, o) { return this._emit(this.gen.curve(pts, this._opts(o)), o); }
  linear(pts, o) { return this._emit(this.gen.linearPath(pts, this._opts(o)), o); }
  raw(svg) { this.parts.push(svg); return this; }

  // A hand-drawn arrow along a gentle curve from (x1,y1) to (x2,y2); bend is the sideways bulge in px.
  arrow(x1, y1, x2, y2, o = {}) {
    const bend = o.bend ?? 0;
    const mx = (x1 + x2) / 2, my = (y1 + y2) / 2;
    const dx = x2 - x1, dy = y2 - y1, len = Math.hypot(dx, dy) || 1;
    const nx = -dy / len, ny = dx / len;
    const cx = mx + nx * bend, cy = my + ny * bend;
    const pts = [];
    for (let i = 0; i <= 8; i++) {
      const t = i / 8, a = (1 - t) ** 2, b = 2 * (1 - t) * t, c = t * t;
      pts.push([a * x1 + b * cx + c * x2, a * y1 + b * cy + c * y2]);
    }
    this.curve(pts, { ...o, single: true, roughness: o.roughness ?? 0.8 });
    const [px, py] = pts[pts.length - 2];
    const ang = Math.atan2(y2 - py, x2 - px), head = o.head ?? 11, spread = 0.42 + (this.rand() - 0.5) * 0.12;
    for (const s of [-1, 1]) {
      const hx = x2 - head * Math.cos(ang + s * spread), hy = y2 - head * Math.sin(ang + s * spread);
      this.line(x2, y2, hx, hy, { ...o, single: true, roughness: 0.6 });
    }
    return this;
  }

  // Handwriting: per-glyph x positions, a little rotation and baseline wobble, set in an embedded Kalam subset.
  text(str, x, y, o = {}) {
    const weight = o.weight ?? 'regular', font = FONTS[weight];
    const size = o.size ?? 18, color = o.color ?? INK.chalk, wob = o.wobble ?? 1;
    const width = this.measure(str, o);
    let cx = o.anchor === 'middle' ? x - width / 2 : o.anchor === 'end' ? x - width : x;
    const glyphs = [...str].map((ch) => font.charToGlyph(ch));
    const xs = [], dys = [], rots = [];
    let prevDy = 0;
    glyphs.forEach((g, i) => {
      xs.push(r1(cx));
      const dy = (this.rand() - 0.5) * 1.6 * wob * (size / 18);
      dys.push(r1(dy - prevDy)); prevDy = dy;
      rots.push(r1((this.rand() - 0.5) * 5 * wob));
      const next = glyphs[i + 1];
      cx += (g.advanceWidth / font.unitsPerEm) * size * (o.tracking ?? 1) + (next ? (font.getKerningValue(g, next) / font.unitsPerEm) * size : 0);
    });
    (this.used[weight] ??= new Set());
    for (const ch of str) this.used[weight].add(ch);
    const esc = str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    const tr = o.rotate ? ` transform="rotate(${o.rotate} ${r1(x)} ${r1(y)})"` : '';
    this.parts.push(`<text class="${weight[0]}" x="${xs.join(' ')}" y="${r1(y)}" dy="${dys.join(' ')}" rotate="${rots.join(' ')}" font-size="${r1(size)}" fill="${color}"${o.opacity ? ` opacity="${o.opacity}"` : ''}${tr}>${esc}</text>`);
    return this;
  }

  measure(str, o = {}) {
    const font = FONTS[o.weight ?? 'regular'];
    const g = [...str].map((ch) => font.charToGlyph(ch));
    return g.reduce((w, gl, i) => w + (gl.advanceWidth / font.unitsPerEm) * (o.size ?? 18) * (o.tracking ?? 1)
      + (g[i + 1] ? (font.getKerningValue(gl, g[i + 1]) / font.unitsPerEm) * (o.size ?? 18) : 0), 0);
  }

  // Multi-line handwriting; returns the y after the last line.
  lines(arr, x, y, o = {}) {
    const lh = o.lineHeight ?? (o.size ?? 18) * 1.25;
    arr.forEach((s, i) => this.text(s, x, y + i * lh, o));
    return y + arr.length * lh;
  }

  // A wobbly underline or highlight swash under text.
  underline(x1, x2, y, o = {}) {
    const pts = [];
    for (let i = 0; i <= 6; i++) pts.push([x1 + ((x2 - x1) * i) / 6, y + (this.rand() - 0.5) * 2.4]);
    return this.curve(pts, { roughness: 0.6, single: true, ...o });
  }

  // Notebook chess diagram. White pieces: inked letters. Black pieces: letters cut out of a filled blob.
  board(x, y, size, fen, o = {}) {
    const sq = size / 8, flip = o.flip ?? false;
    const rows = fen.split(' ')[0].split('/');
    this.rect(x, y, size, size, { width: 1.8, roughness: 0.9 });
    for (let r = 0; r < 8; r++) for (let f = 0; f < 8; f++) {
      if ((r + f) % 2 === 1) {
        this.rect(x + f * sq + 1.5, y + r * sq + 1.5, sq - 3, sq - 3, { stroke: 'none', fill: INK.faint, fillStyle: 'hachure', hachureGap: 4.2, fillWeight: 0.7, roughness: 1.4, opacity: 0.55 });
      }
    }
    const pos = (sqName) => {
      const f = sqName.charCodeAt(0) - 97, r = 8 - Number(sqName[1]);
      return flip ? [x + (7 - f) * sq + sq / 2, y + (7 - r) * sq + sq / 2] : [x + f * sq + sq / 2, y + r * sq + sq / 2];
    };
    for (const h of o.highlight ?? []) {
      const [cx, cy] = pos(h.sq);
      this.circle(cx, cy, sq * 0.98, { stroke: h.color ?? INK.gold, width: 2, roughness: 1.3 });
    }
    rows.forEach((row, r) => {
      let f = 0;
      for (const ch of row) {
        if (/\d/.test(ch)) { f += Number(ch); continue; }
        const name = String.fromCharCode(97 + f) + (8 - r);
        const [cx, cy] = pos(name);
        const white = ch === ch.toUpperCase();
        const letter = ch.toUpperCase();
        if (white) {
          this.circle(cx, cy, sq * 0.74, { stroke: INK.chalk, width: 1.2, roughness: 1.2, fill: INK.chalk, fillStyle: 'solid' });
          this.text(letter, cx, cy + sq * 0.2, { size: sq * 0.56, anchor: 'middle', weight: 'bold', color: INK.paper });
        } else {
          this.circle(cx, cy, sq * 0.74, { stroke: INK.chalk, width: 1.4, roughness: 1.2, fill: INK.paper, fillStyle: 'solid' });
          this.text(letter, cx, cy + sq * 0.2, { size: sq * 0.56, anchor: 'middle', weight: 'bold', color: INK.chalk });
        }
        f++;
      }
    });
    if (o.coords !== false) {
      for (let i = 0; i < 8; i++) {
        const file = String.fromCharCode(97 + (flip ? 7 - i : i)), rank = String(flip ? i + 1 : 8 - i);
        this.text(file, x + i * sq + sq / 2, y + size + 15, { size: 12, anchor: 'middle', color: INK.faint });
        this.text(rank, x - 9, y + i * sq + sq / 2 + 4, { size: 12, anchor: 'middle', color: INK.faint });
      }
    }
    for (const a of o.arrows ?? []) {
      let [x1, y1] = pos(a.from), [x2, y2] = pos(a.to);
      const L = Math.hypot(x2 - x1, y2 - y1), ux = (x2 - x1) / L, uy = (y2 - y1) / L;
      x1 += ux * sq * 0.42; y1 += uy * sq * 0.42; x2 -= ux * sq * (a.trimEnd ?? 0.12); y2 -= uy * sq * (a.trimEnd ?? 0.12);
      this.arrow(x1, y1, x2, y2, { stroke: a.color ?? INK.pink, width: 2.6, bend: a.bend ?? 0, head: 10 });
    }
    return { sq, pos };
  }

  // A hand-drawn interval: a whisker with end ticks and a dot at the estimate.
  interval(x1, x2, y, est, o = {}) {
    const c = o.color ?? INK.chalk;
    this.line(x1, y, x2, y, { stroke: c, width: o.width ?? 2, roughness: 0.7, single: true });
    this.line(x1, y - 6, x1, y + 6, { stroke: c, width: 1.6, roughness: 0.5, single: true });
    this.line(x2, y - 6, x2, y + 6, { stroke: c, width: 1.6, roughness: 0.5, single: true });
    this.circle(est, y, o.dot ?? 10, { stroke: c, fill: c, fillStyle: 'solid', roughness: 0.8 });
    return this;
  }

  svg(title, desc) {
    const id = `s${this.seed}`;
    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${this.w} ${this.h}" width="${this.w}" height="${this.h}" role="img" aria-labelledby="${id}t ${id}d">
<title id="${id}t">${title}</title>
<desc id="${id}d">${desc}</desc>
<defs><style>${Object.entries(this.used).map(([w, set]) => `@font-face{font-family:k${w[0]};src:url(data:font/woff2;base64,${subset(w, set)}) format("woff2")}text.${w[0]}{font-family:k${w[0]};font-kerning:none;font-variant-ligatures:none;white-space:pre}`).join('')}</style><filter id="${id}ink" x="-2%" y="-2%" width="104%" height="104%"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="${this.seed}" result="n"/><feDisplacementMap in="SourceGraphic" in2="n" scale="1.6"/></filter></defs>
<g filter="url(#${id}ink)">
${this.parts.join('\n')}
</g>
</svg>
`;
  }
}
