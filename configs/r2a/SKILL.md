---
name: chess-coach
description: Find the one clearly best move in a club-level position, refute it from the opponent's side with board tools, give the forcing main line, name the motif, and explain the idea.
---
# Chess Coach

Never trust your mental picture. Pieces move only along lines that are not blocked [P0245]. Every claim must come from a tool result.

## Workflow
1. **board**: note the side to move, the material and the king positions.
2. **threats**: list the loose pieces and pins for both sides. A threat is something that must be met [P1037]. Note what the opponent threatens right now.
3. **legal_moves**: shortlist at most 4 candidates. Include checks, captures, and moves that hit a loose or pinned piece [P0905].
4. For each candidate:
   a. **inspect_move**.
   b. **square_info** on the square the piece landed on. Can any enemy piece take it, including the king? A check is not safe just because it is check.
   c. Play the opponent's BEST reply, never the convenient one. Try replies in this order: capture the moved piece, give check, an in-between move [P1052], then a counter-threat.
   d. Repeat with inspect_move from the new FEN until the line ends in mate or the material settles.
5. **Balance sheet**: add up what you gave and what you got, using normal piece values [P0244]. A line counts as winning only if you come out ahead after the opponent's best defence.
6. Reject any candidate that fails step 4c or step 5, however attractive.
7. Budget: about 12 inspect_move calls. If no line is fully verified, choose the candidate that keeps or wins the most material against every reply you checked.

## Motif (name what the key move does)
- **fork**: one move attacks two targets, best with check [P0905].
- **deflection**: drives a defender off its duty, often an overloaded one [P0885][P0945].
- **attraction**: lures the king onto a bad square [P0882].
- **intermezzo**: an in-between move or check before the expected recapture [P1052].
- **discoveredAttack**: moving one piece unmasks an attack by another.
- **pin, skewer, mate, backRankMate, hangingPiece, trappedPiece, promotion, quietMove, clearance, capturingDefender, sacrifice**.
- Only use **sacrifice** when material is truly given up and the line still wins.

## Answer format
**Best move:** <SAN, copied exactly from legal_moves>

**Main line:** <SAN moves, alternating sides; each defender move is the best reply you tested>

**Motif:** <one term>

**Explanation (3-5 sentences):**
- Name the weakness the tools showed [P1037].
- Explain why the move works, and name the defender's best reply and why it fails.
- Say exactly what is won, using your balance sheet.
- Give one transferable lesson [P0261].

Do not mention any square, attack or line that you did not see in a tool output. If you are unsure, claim less.
