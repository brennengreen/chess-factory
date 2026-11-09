# Human-in-the-loop decisions

The teacher may request perception tools (never search or evaluation). A human decides.

## Round 1 tool_request: square_info (built)
> "A 'square_info' perception tool. Given a square, it would list every piece of each side that attacks or
> defends that square, including x-ray attackers behind a blocker."

Built as `square_info(fen, square)` in `server/chess_eyes.py`: reports the piece on the square, direct
attackers/defenders for both sides, and x-ray sliders behind exactly one blocker. It is perception only
(no search, no evaluation, no move ranking), so it is within the rules. Added to the teacher's catalog
from round 2 on. Round 1 candidates did not have it and their runs were unaffected (tools are enabled
by name per session).

## Round 2 tool_request: inspect_move capture flag (declined), line_view (built)
> "Add a capture flag to inspect_move: for the moved piece, list every enemy piece (including the king)
> that can legally capture it on its new square, and every own piece that defends it there. Also add a
> line_view tool: for a given piece, list the first piece it meets along each line and any piece directly
> behind it (x-ray)."

- Capture flag: declined. Changing inspect_move would alter the behaviour of the incumbent (r1a) after it
  was measured, so cached incumbent results would no longer describe the incumbent. The same facts are
  already one call away: inspect_move returns the resulting FEN, and square_info on the destination square
  lists every attacker and defender, kings included.
- line_view: built as a new tool (perception only), in the catalog from round 3 on.

## Round 3 tool_request: piece_mobility (declined)
> "piece_mobility: for one piece, list every square it can legally move to and mark each as safe or unsafe
> (attacked by a cheaper enemy piece, or attacked more times than defended)."

Declined. Marking a square "safe" or "unsafe" is a static exchange judgment, i.e. evaluation, which the
tool rules exclude. The underlying facts are already available (legal_moves for destinations, square_info
for attackers and defenders of any square). Evidence also argued against more perception tools: in rounds
2 and 3, candidates given square_info and line_view did not beat the incumbent (paired diffs -1.9 and
-1.6 points, both CIs spanning zero).
