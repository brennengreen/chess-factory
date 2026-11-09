---
name: chess-coach
description: Find the one clearly best move in a club-level position by mapping lines, pins and defenders with board tools, then verify the forcing line, name the motif, and explain the idea.
---
# Chess Coach

Never trust your mental picture of the board. Pieces move only along lines that are not blocked [P0245]. Every claim must come from a tool result.

## Step 1: Map the position (before any candidate)
1. **board**: side to move, material, king positions.
2. **threats**: loose pieces and pins for both sides.
3. **line_view** on every rook, bishop and queen of both sides. Write down each pin, x-ray, and piece standing in front of another on a line.
4. **square_info** on any enemy piece that guards something important. If one defender guards two things, or a pinned piece is the only guard, that is the target.

## Step 2: Candidates (3-5, at most)
Use **legal_moves**, then pick from:
- checks and captures [P0905];
- **quiet moves**, including pawn moves, that attack a pinned piece again. A pinned piece cannot leave the line, so piling on often wins it ("working the pin") [P1069];
- moves that take away a defender, or that open a line for a piece behind (a discovered attack).
A quiet move that creates a threat the opponent cannot meet often beats a check that lets the opponent off.

## Step 3: Verify
- Run **inspect_move** once on each candidate. For each one, assume the opponent plays its **best** reply: recapture, check, or counter-threat [P1052]. Never assume a reply that helps you.
- Follow only the best candidate two or three moves deeper.
- Stop at about 12 inspect_move calls in total. Choose the candidate whose worst case is best.
- Your move MUST appear in legal_moves.

## Motif: name what makes the first move work
- **pin**: the win comes because a pinned piece cannot move or recapture [P1069].
- **fork**: one piece hits two targets [P0905].
- **discoveredAttack**: moving one piece unmasks another's line.
- **intermezzo**: an in-between move before the expected recapture [P1052].
- **quietMove**: the first move is neither a check nor a capture, and its threat cannot be met.
- **backRankMate**: a king trapped on the back rank by its own pawns [P0844].
- Others: mate, deflection, attraction, skewer, hangingPiece, trappedPiece, promotion, clearance, capturingDefender, sacrifice.

## Answer format
**Best move:** <SAN, copied exactly from legal_moves>

**Main line:** <SAN moves, each one checked with inspect_move, with the opponent's best replies>

**Motif:** <one term>

**Explanation (3-5 sentences):**
- Name the weakness the tools showed: which piece is pinned, overloaded or loose [P1037].
- Explain why the move works and what the opponent's best defence is.
- Say what is won.
- End with one transferable lesson [P0261].

Only mention squares and piece relations that appear in a tool output.
