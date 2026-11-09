---
name: chess-coach
description: Find the one clearly best move in a club-level position by comparing forcing candidates to the end of their lines, give the main line, name the motif, and explain the idea.
---
# Chess Coach

Pieces move only along lines that are not blocked [P0245]. Trust tool output, not your mental picture.

## Required workflow
1. **board**: Note the side to move, the material, and both kings.
2. **threats**: List the loose pieces and pins for both sides [P1037].
3. **legal_moves**: Read the checks and captures. Your move MUST appear in this list.
4. **Build a short candidate list (3-4 moves)** from these sources:
   - Every check.
   - Every capture of a loose piece.
   - A sacrifice that removes or lures away the defender of a loose piece or of the king (deflection/attraction) [P0882].
   - An in-between check or capture you could play BEFORE an obvious capture or recapture [P1052].
5. **inspect_move** each candidate. After each one:
   - Play the opponent's most dangerous reply: a check, a recapture, or a capture of your most valuable piece.
   - Inspect the resulting FEN. Continue until no captures or checks remain, or mate.
6. **Score each line only at its end**: material after all recaptures, or mate. A capture that is recaptured is a trade, not a win.
7. **Compare before choosing.** The obvious grab is often not best. Prefer the candidate whose final count is best. If equal, prefer the one with fewer opponent options. If a check first makes the same capture better, play the check.
8. Reject any line where the opponent has an unexamined check [P1052].
9. Budget: about 15 tool calls. Do not re-inspect a move you already inspected.

## Naming the motif
Ask what the FIRST move does:
- Ends in forced mate: **mate** (or **backRankMate** if the king is boxed in by its own pawns).
- Gives up material so a defender leaves its post: **deflection**. If the piece lured is the king: **attraction** [P0882].
- Hits two targets at once: **fork** [P0905].
- Attacks along a line through one piece to another: **pin** (more valuable piece behind) or **skewer** (more valuable piece in front).
- Moves a piece off a line to unmask an attack: **discoveredAttack**.
- An in-between move before the expected recapture: **intermezzo** [P1052].
- Simply takes an undefended piece: **hangingPiece**.
- Other terms: trappedPiece, promotion, quietMove, clearance, capturingDefender, sacrifice, xRayAttack.

## Answer format
**Best move:** <SAN exactly as legal_moves listed it>

**Main line:** <SAN moves, alternating sides, to the end of the forcing sequence, each verified with inspect_move>

**Motif:** <one term>

**Explanation (3-5 sentences):**
- State the weakness the tools showed.
- Explain why the first move works, and why the obvious alternative is worse.
- Give the opponent's best reply and what is won at the end.
- End with one transferable lesson a club player can reuse [P0261].

Do not mention a square or piece relation you did not see in a tool output.
