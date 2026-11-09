# chess-factory

A worked example of what I call *statistical software*: a **grader** (a benchmark), a **teacher** (an LLM that
turns human-written chess books into advice, never answers), and a **gate** (a paired statistical test) that
together adapt a small model, Claude Haiku 4.5 running in the GitHub Copilot CLI, to coach chess tactics.
The only things that change are a skill file and a set of MCP tools.

Companion repo to the blog post
[The Teacher and the Grader](https://brennengreen.dev/blog/the-teacher-and-the-grader/).

## Results

Primary, preregistered (sealed test, 240 puzzles, paired, 95% bootstrap CI):

| comparison | gain (points of 100) | 95% CI |
|---|---|---|
| final config (`r1a`) vs bare model | **+22.1** | 17.5 to 26.5 |
| same, on the mirrored test set | +24.6 | 19.8 to 29.6 |
| same, rules only (no LLM judge) | +17.1 | 13.6 to 20.5 |
| same, second judge (80 puzzles) | +19.4 | 11.8 to 27.1 |
| controls: A/A rerun on dev; mirror minus original (final, bare) | +0.4; +2.3; -0.2 | all span zero |

The hill climb accepted one step (round 1, +30.7 on dev) and rejected all eight candidates in rounds 2-5
(mean step -4.5). Exploratory work after the climb (labeled as such in `DECISIONS.md`) found why:

| probe on dev (vs `r1a`) | gain | 95% CI |
|---|---|---|
| `r1a` run again (A/A) | +0.4 | -4.9 to 5.8 |
| one-rule edits instead of rewrites (2 candidates) | +0.2, -2.7 | both span zero |
| oracle: model told the first move | +21.7 | 16.2 to 27.2 |
| widen the surface: `forcing_lines` calculation tool (`x-calc-a`) | +17.0 | 10.8 to 23.2 |

`x-calc-a` then got one look at the sealed test (Preregistration Amendment 2): **+25.1 over `r1a`
(95% CI 20.7 to 29.6)**, first move right on 206 of 240 puzzles against 123.

The design lesson: a gated climb guarantees that what it accepts is real, not that there is anything to accept.
Whether it keeps climbing depends on whether the editable surface can reach the remaining headroom, which you
can measure first with A/A runs, re-judging and oracle probes.

All numbers come from `runs/results.json` (preregistered analysis), `runs/explore.json` (exploratory) and
`runs/confirm.json` (Amendment 2).

## What's here

| path | what |
|---|---|
| `PREREGISTRATION.md` | the plan, committed before results, plus Amendments 1 and 2 |
| `DECISIONS.md` | every human-in-the-loop tool decision, and the exploratory interventions |
| `data/` | train (200), dev (120), test (240) and mirrored test splits, built by `factory/data.py` |
| `corpus/raw/` | the teacher's library: Capablanca and Edward Lasker (Project Gutenberg), Wikipedia tactics articles |
| `server/chess_eyes.py` | the MCP server: perception tools, plus the exploratory `forcing_lines` calculation tool |
| `factory/cli.py` | headless Copilot CLI runner with a strict tool allowlist |
| `factory/subject.py`, `grade.py`, `teacher.py`, `corpus.py` | the subject, the grader (rules + LLM judge), the teacher (BM25 RAG + leak check) |
| `factory/climb.py`, `stats.py` | the hill climb and the gate (one-sided 95% paired bootstrap lower bound > 0) |
| `factory/final.py` | the preregistered final analysis |
| `factory/probe.py`, `intervene.py`, `explore.py`, `sim.py` | exploratory: A/A, re-judge, oracle and capacity probes; interventions; climbability simulation |
| `factory/confirm.py` | Amendment 2: one sealed-test look at the calculation candidate |
| `configs/` | every skill file and tool set the teacher proposed |
| `runs/` | every subject answer, every grade, teacher prompts and replies, and the result JSON files |
| `figures/` | the hand-drawn figures (rough.js, Kalam), generated from the JSON |

## Reproduce

You need Python 3.12+, Node 20+, and the [GitHub Copilot CLI](https://github.com/github/copilot-cli) signed in
with access to the models in the preregistration. Results are cached in `runs/`, so every command below resumes
where it left off and reruns nothing that already exists; delete a run's folder to redo it.

```sh
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cd factory
../.venv/bin/python climb.py 5                                   # the hill climb
../.venv/bin/python final.py run && ../.venv/bin/python final.py analyze
../.venv/bin/python probe.py aa && ../.venv/bin/python probe.py rejudge && ../.venv/bin/python probe.py oracle
../.venv/bin/python intervene.py minimal && ../.venv/bin/python intervene.py calc
../.venv/bin/python confirm.py run && ../.venv/bin/python confirm.py analyze
../.venv/bin/python explore.py
cd ../figures && npm install && node fig_data.mjs && node fig_explore.mjs
```

The whole experiment cost about 19,000 Copilot AI credits, nearly all of it the subject model playing puzzles.

The splits in `data/` are the reference. To rebuild them, download `lichess_db_puzzle.csv.zst` from the
[Lichess database](https://database.lichess.org/#puzzles), take the header and first 400,000 rows
(`zstdcat lichess_db_puzzle.csv.zst | head -n 400001 > data/puzzles_head.csv`), and run `factory/data.py`. The
Lichess file is updated over time, so a later download may not reproduce the same splits exactly.

## Licenses

Code: Apache-2.0 (`LICENSE`). Data and assets keep their own licenses: Lichess puzzles are CC0; the Project
Gutenberg texts are public domain in the US and carry their Gutenberg headers; the Wikipedia extracts in
`corpus/raw/wiki_*.json` are CC BY-SA 4.0 (Wikipedia contributors, article titles in the file names); the Kalam
font is under the SIL Open Font License (`figures/fonts/OFL.txt`).
