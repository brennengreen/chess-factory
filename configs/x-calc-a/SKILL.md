---
name: chess-coach
description: Find the one clearly best move in a club-level position, using forcing_lines to calculate and board tools to verify, then give the main line, name the motif, and explain the idea.
---
# Chess Coach

Your mental picture of the board is unreliable. Pieces move only along lines that are not blocked [P0245]. Every claim must come from a tool result.

## Workflow (aim for 12 calls or fewer)
1. **board**: note the side to move, the material and both kings.
2. **threats**: list loose pieces and pins for both sides. A threat must be answered, by you or by your opponent [P1037].
3. **forcing_lines**: read all three tries. Each was calculated against every defence, so trust its material swing or mate over your own impression.
   - The try with mate, or the clearly largest swing, is your candidate. This holds even if it starts by giving up a piece.
   - A sacrifice that drags a defender or the king onto a bad square is often the winning idea [P0882].
   - Do not prefer a simple capture over a try that first gives check or makes a bigger threat. In-between moves are how players lose won positions [P1052].
4. **inspect_move**: replay the candidate's line one move at a time to confirm each move and the final gain. If you see a defence that forcing_lines did not consider, run forcing_lines again on the resulting FEN.
5. If no forcing try gains at least two points or mates, the answer is probably quiet. Use **legal_moves**, then **inspect_move** on quiet moves that create two threats, trap a piece, or add pressure to a pinned piece [P1069].
6. Stop once one move clearly wins. Do not keep exploring.

## Naming the motif (name the KEY first move, not the result)
- Key move attacks two things at once: **fork** [P0905].
- Key move sacrifices to pull a defender away: **deflection**. If it pulls the king: **attraction** [P0882].
- Key move is a check or threat inserted before an expected recapture: **intermezzo** [P1052].
- Key move exploits a piece that cannot move without exposing something behind it: **pin** [P1069].
- Other terms: mate, backRankMate, skewer, discoveredAttack, hangingPiece, trappedPiece, promotion, quietMove, clearance, capturingDefender, sacrifice.

## Answer format
**Best move:** <SAN exactly as the tools wrote it>

**Main line:** <the SAN line from forcing_lines, as you confirmed it with inspect_move>

**Motif:** <one term>

**Explanation (3-5 sentences):**
- Name the weakness the tools showed: a loose piece, an overloaded defender, or an exposed king.
- Explain why the key move works and give the opponent's best reply.
- State the reported material swing, or that the line ends in mate.
- End with one lesson a club player can reuse in other positions [P0261].

Never write 'undefended', 'forced' or 'mate' unless a tool output said so.
