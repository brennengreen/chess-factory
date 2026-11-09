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
