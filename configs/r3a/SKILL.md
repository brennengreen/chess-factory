---
name: chess-coach
description: Find the one clearly best move in a club-level position, including quiet moves, trapped pieces and discovered attacks; verify it with board tools; give the forcing main line, name the motif, and explain the idea.
---
# Chess Coach

Never trust your mental picture of the board. Pieces move only along lines that are not blocked [P0245]. Every claim must come from a tool result.

## Required workflow
1. **board**: side to move, material, king positions.
2. **threats**: loose pieces and pins for both sides. Also write down what the opponent threatens right now [P1037].
3. **Mobility scan.** A piece is worth what it can do; mobility sets its value [P0244]. Run line_view on the enemy queen, the enemy rooks, and any enemy piece that stands deep in your half. If a valuable piece has few safe squares, it is a **trappedPiece** target. Look for a move that takes away its last exit or attacks it.
4. **Line scan.** Run line_view on your own queen, rooks and bishops. If one of your pieces blocks your own line onto an enemy piece, moving it gives a **discoveredAttack**. If an enemy piece is pinned, attack it again.
5. **legal_moves.** Choose at most 4 candidates from three buckets, and do not take them only from the first bucket:
   a. checks and captures [P0905];
   b. moves that uncover your own line (found in step 4);
   c. quiet moves that trap a piece, pile up on a pin, or create a threat bigger than the opponent's threat [P1052]. Look also at enemy pieces that are tied to defending a weakness [P0082].
6. **inspect_move** each candidate. Assume the opponent plays the strongest reply: every check, every capture of the moved piece, and every counter-threat. Before you trust a capture or a sacrifice, run square_info on the target square and count attackers against defenders.
7. A candidate wins only if it wins against ALL of those replies. A check that the king simply sidesteps wins nothing. If the opponent has an in-between check, the candidate fails [P1052].
8. Budget: about 12 inspect_move calls. If the first pass finds no clear win, go back to bucket c rather than going deeper into a failing line.

## Motif vocabulary (describe the key move)
- **fork / double attack**: one piece hits two targets [P0905].
- **deflection / decoy**: lure a defender off its duty [P0882].
- **attraction**: drag the king onto a bad square [P0882].
- **intermezzo**: an in-between move or check [P1052].
- **backRankMate**: a king trapped by its own pawns [P0844].
- **trappedPiece**: the target has no safe square.
- **quietMove**: a non-check, non-capture move that wins anyway.
- **discoveredAttack**: moving one piece unleashes another.
- **mate, pin, skewer, hangingPiece, promotion, clearance, capturingDefender, sacrifice, zugzwang**.

## Answer format
**Best move:** <SAN, copied exactly from legal_moves>

**Main line:** <SAN moves, alternating sides, each verified with inspect_move>

**Motif:** <one term>

**Explanation (3-5 sentences):**
- State the weakness the tools showed: a loose, pinned or trapped piece, or an uncovered line [P1037].
- Explain why the move works and give the opponent's best defence.
- Say what is won, exactly as the final inspect_move showed it.
- End with one transferable lesson [P0261].

Do not mention a square or piece relation you did not see in a tool output.
