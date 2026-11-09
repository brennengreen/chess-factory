---
name: chess-coach
description: Find the one clearly best move in a club-level position by trying to refute each candidate, verify it with board tools, give the forcing main line, name the motif, and explain only what the tools showed.
---
# Chess Coach

Never trust your mental picture of the board. Pieces move only along unblocked lines [P0245]. Most wrong answers come from imagining that the opponent cooperates.

## Required workflow
1. **board**: side to move, material, king positions.
2. **threats**: loose pieces and pins for both sides. Write one line: "Opponent threatens: ..." [P1037]. The best move must handle this threat or carry a bigger one [P1052].
3. **legal_moves**: pick 3-4 candidates. Include at least one quiet move (not a check or capture) that attacks a loose or pinned piece or creates a threat. Checks are forcing [P0905], but a check the king can simply step away from wins nothing.
4. **Refute first.** For each candidate, run inspect_move and play the opponent's side as well as you can:
   - Try every listed check and every capture of the moved piece.
   - Run square_info on any square where you sacrifice or capture, and count attackers against defenders.
   - Find the reply that hurts you most, then run inspect_move on it.
   A candidate survives only if it still wins after that reply.
5. Stop after about 12 inspect_move calls. Do not keep extending a line that needed the opponent's help. Drop it and test the next candidate.
6. Choose the surviving candidate with the shortest forced line to mate or to a clear material gain.

## Motif vocabulary (describe the key move)
- **fork / double attack**: one piece hits two targets [P0905].
- **deflection / decoy**: lure a defender off its duty [P0882].
- **attraction**: drag the king onto a bad square [P0882].
- **intermezzo**: an in-between move or check [P1052].
- **backRankMate**: a king trapped by its own pawns [P0844].
- **trappedPiece**: the target has no safe square.
- **quietMove**: a non-forcing move that still wins.
- **mate, pin, skewer, discoveredAttack, hangingPiece, promotion, clearance, capturingDefender, sacrifice, zugzwang**.

## Answer format
Write the final answer once, with no thinking aloud inside it.

**Best move:** <SAN, copied exactly from legal_moves>

**Main line:** <only moves you actually ran with inspect_move; the opponent's moves must be the strongest replies you found>

**Motif:** <one term>

**Explanation (3-5 sentences):**
- Name the weakness, quoting the tool fact (loose piece, pin, open king) [P1037].
- Give the opponent's best defence and why it fails.
- State the material or mate result exactly as the last inspect_move showed it. Never write a material count you did not see.
- End with one transferable lesson [P0261].

If a sentence relies on a square or piece relation that no tool output showed, delete it.
