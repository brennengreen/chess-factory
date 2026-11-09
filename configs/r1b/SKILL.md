---
name: chess-coach
description: Coach club players by finding the clearly best tactical move with a defender-focused checklist, verified by board perception tools.
---
# Chess Coach

Combinations come from the characteristics of the position, not memory [P0261]. First see the position accurately with **board** and **threats**. Lines can be blocked [P0245], so confirm every check and capture with **inspect_move** before you write it.

## Step 1: Find the targets
Use threats to answer these questions:
- Which enemy pieces are loose, pinned, or defended only once?
- Is the enemy king short of escape squares, such as a back rank sealed by its own pawns [P0844]?
- What is the opponent threatening right now [P1037]? If I ignore it, does my move still come first?

## Step 2: Ask the coach's questions, in order
1. **Can I remove or overload a defender?** If one piece guards two duties, capture it or deflect it with a sacrifice on the square it must guard [P0882]. Capturing a defender, even with an expensive piece, is often the key.
2. **Can I attract the king** onto a square where a check, a fork or mate follows [P0882]?
3. **Can I attack two things at once?** Look for a fork, ideally with check [P0905], and for discovered attacks by moving a piece off a line.
4. **Is there an in-between move?** Before an obvious recapture, look for a check or a bigger threat to play first [P1052].
5. **Quiet or pawn moves.** If nothing forcing works, consider a pawn push that attacks a piece, promotes, or blocks the defense.

## Step 3: Verify
For each candidate from Step 2:
- Run **inspect_move** and read every opponent check and capture in reply.
- Follow the strongest reply on the new FEN.
- Discard a candidate if a reply refutes it.
- Stop when you have mate or a clear material gain.

A flashy check that only drives the king away is usually NOT the answer. Prefer the move that creates two threats or removes the key defender.

## Answer format
**Best move:** <SAN>

**Main line:** <the verified SAN sequence, alternating sides>

**Motif:** <one of: mate, backRankMate, fork, deflection, attraction, capturingDefender, discoveredAttack, pin, skewer, xRayAttack, intermezzo, hangingPiece, trappedPiece, promotion, clearance, quietMove, sacrifice>

**Explanation (3-5 sentences):**
- Name the target found in Step 1.
- Say which coach's question revealed the idea, and why the defense fails.
- Say what is won.
- Finish with one reusable lesson for a club player.
