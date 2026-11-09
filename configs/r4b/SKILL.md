---
name: chess-coach
description: Find the one clearly best move in a club-level position using disciplined breadth-first checking against the opponent's best replies, then give the main line, motif and an accurate explanation.
---
# Chess Coach

Never trust your mental picture of the board. Pieces move only along lines that are not blocked [P0245]. Every claim must come from a tool result.

## Workflow (budget: about 12 tool calls)
1. **board**, then **threats**. Write down every loose enemy piece, every pin, and every loose piece of your own.
2. **legal_moves**. Write a shortlist of 4-6 moves:
   - checks and captures [P0905];
   - at least one **quiet move**, such as a pawn push, that attacks a pinned or loose piece or traps one.
   A move that is not check or capture is often the answer.
3. **Breadth first.** Run **inspect_move** once on every shortlisted move before going deeper on any of them. For each one, write down the opponent's most dangerous reply from the tool output: a check, a capture of your best piece, or a recapture [P1052].
4. **Assume best defence.** Reject any line in which you win only if the opponent makes a poor or optional move. If they can simply recapture, they will.
5. Go deeper (at most 3 more inspect_move calls) only on the one or two survivors.
6. Choose the move whose result after the best defence is a mate or a clear material gain. If a capture-or-check line nets nothing after the best reply, look for the quiet move instead.
7. If you are near the budget, stop and answer with the best verified candidate. Do not restart.

## Motif: describe why the first move works
- **pin**: a pinned piece cannot escape or recapture [P1069].
- **fork**: one piece attacks two targets [P0905].
- **intermezzo**: an in-between move or check [P1052].
- **backRankMate**: a king trapped on the back rank by its own pawns [P0844].
- **quietMove**: the key move is neither a check nor a capture.
- Others: mate, deflection, attraction, discoveredAttack, skewer, hangingPiece, trappedPiece, promotion, clearance, capturingDefender, sacrifice.

## Answer format
**Best move:** <SAN, copied exactly from legal_moves>

**Main line:** <SAN moves, each checked with inspect_move, with the opponent's best replies>

**Motif:** <one term>

**Explanation (3-5 sentences):**
- State the threat or weakness, copying the piece and square from the tool output [P1037].
- Explain why the move works and what the opponent's best reply is.
- Say exactly what is won, counted from the tool's material report.
- End with one transferable lesson [P0261].

Do not describe any line you did not inspect. Write the answer only once your analysis is complete.
