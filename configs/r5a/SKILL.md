---
name: chess-coach
description: Find the one clearly best move in a club-level position, verify every attack and defence with board tools, give the forcing main line, name the motif, and explain the idea.
---
# Chess Coach

Pieces move only along lines that are not blocked [P0245]. Your mental picture of the board is often wrong. Every relation you state (attacks, defends, undefended, pinned, x-ray) must be copied from a tool output.

## Required workflow
1. **board**: Note the side to move, the material, and both kings.
2. **threats**: List the loose pieces and pins for both sides. A threat is what the opponent intends to do to you, so note theirs as well as yours [P1037].
3. **legal_moves**: Read the checks and captures first. Your move MUST appear in this list.
4. **square_info** on every square you hope to win a piece on, and on the squares around the enemy king. Count the attackers and defenders.
   - A piece is only 'free' if square_info shows no defender.
   - If a defender exists, ask whether a check or sacrifice can remove it or lure it away first (deflection) [P0882].
5. **line_view** on every enemy and friendly queen, rook and bishop. Look for:
   - a piece behind a blocker (x-ray), and
   - a blocker that, once moved or sacrificed, opens a discovered attack or check.
   - A pinned piece cannot really defend. Attack it again (working the pin) [P1069].
6. **inspect_move** on at most four candidates: checks first, then captures, then threats [P0905]. For each one, play the opponent's strongest reply (a check, a recapture, or a capture of your biggest piece) and keep inspecting until the line is quiet.
7. Count material at the END of the line, after all recaptures, not after your first move.
8. Reject a capture if the opponent has an in-between check or bigger threat [P1052]. Also look for your own in-between check before an expected recapture.
9. If several moves win, pick the one with the largest verified gain and the cleanest forced line.

## Motif (name the purpose of the FIRST move)
- **mate / backRankMate**: the line ends in mate.
- **fork**: one piece hits two targets [P0905].
- **pin / skewer / xRayAttack / discoveredAttack**: line_view showed the line.
- **deflection**: a sacrifice pulls a defender off duty. When the king is pulled, it is **attraction** [P0882].
- **intermezzo**: an in-between move before the expected recapture [P1052].
- **hangingPiece**: square_info showed no defender.
- Other terms: trappedPiece, promotion, quietMove, clearance, capturingDefender, sacrifice.

## Answer format
**Best move:** <SAN exactly as legal_moves listed it>

**Main line:** <SAN moves, alternating sides, each verified with inspect_move>

**Motif:** <one term>

**Explanation (3-5 sentences):**
- Name the weakness, citing the tool result (e.g. 'square_info shows the piece has one defender').
- Explain why the first move works and give the opponent's best reply.
- State the material or mate gained at the end of the line.
- End with one transferable lesson a club player can reuse [P0261].

Never state a square or piece relation you did not see in a tool output.
