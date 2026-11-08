# Preregistration: chess-coach teacher/grader experiment

Committed before any dev or test results beyond a 10-item dev pilot of the bare baseline.

## Task
Given a position from a real Lichess game (Lichess puzzle database, CC0), the agent must give the one
clearly best move, the main line, one or two motif tags, and a coaching note of at most 80 words.

## Data (seed 20261108, see factory/data.py)
Puzzles with popularity >= 85, >= 1000 plays, rating deviation <= 80, rating 1000-2200, 2-6 solution plies,
at least one motif tag, one puzzle per game. 200 train (teacher may see), 120 dev (hill climbing; teacher
sees aggregate scores only through accept/reject), 240 test (sealed until the end), and the same 240 test
positions colour-mirrored (test_mirror) to detect memorisation.

## Systems
Subject: claude-haiku-4.5 inside the Copilot CLI, isolated home, tools limited to the skill tool and the
enabled chess-eyes MCP tools. Judge: gpt-5.6-luna. Teacher: claude-opus-5.5.

## Score (0-100)
move 40 (first move equals the solution, or any mate in one), line 15 (legal, fraction of the solution
matched), motif 15 (any of the first two tags matches the human/auto theme tags), explanation 30 (judge
rubric: accurate, why, teach, each 0-2, reference-guided).

## Hill climbing
Up to 5 rounds. Each round the teacher sees a 60-item train slice graded on the incumbent, retrieves human
passages (BM25 over Capablanca 1921, E. Lasker 1915/1918, Wikipedia tactic articles), and proposes two
candidates. Leak check rejects any candidate containing a position, puzzle id or two-move solution
sequence from any split. A candidate is accepted only if its paired dev improvement over the incumbent has
a one-sided 95% bootstrap lower bound above zero (10,000 resamples).

## Final analysis (run once)
Bare baseline (v0-bare) vs final incumbent on test and test_mirror:
- primary: paired mean score difference on test, 95% bootstrap CI, Wilcoxon signed-rank p
- move accuracy with Wilson CIs, exact McNemar test
- memorisation: final(test_mirror) - final(test) and baseline(test_mirror) - baseline(test); expect CIs to include 0
- estimated Lichess puzzle rating (first-move) with bootstrap CI
- noise floor: final incumbent run twice on dev (A/A)
- judge reliability: re-judge a subsample with the same judge and with a second judge family
- robustness: the primary comparison repeated on the deterministic-only score (move + line + motif)
- dev-to-test gap for the final incumbent, reported as measured overfitting to dev
