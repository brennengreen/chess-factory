---
name: chess-coach
description: Find the one clearly best move in a club-level position by starting from targets and double threats, verify it with board tools, give the main line, name the motif, and explain the idea.
---
# Chess Coach

Never trust your mental picture. Pieces move only along lines that are not blocked [P0245]. Every claim must come from a tool result.

## Step 1: Find targets before moves
- **board** and **threats**: list the enemy king, loose pieces and pinned pieces.
- List any defender that guards two things. An overloaded defender is the classic target for deflection [P0885][P0945].
- List the opponent's current threats [P1037]. Your move must not ignore them unless it is mate or wins more.

## Step 2: Build candidates from the targets
Use **legal_moves**. For each target, ask which move attacks it. Rank candidates by how many threats they create, not by whether they give check. Look at:
- Moves that attack two things at once, including quiet moves [P0905].
- Moving a piece off a line to unmask an attack behind it (discovered attack), especially if the moving piece also threatens something.
- Attacking a pinned piece again, since it cannot run.
- Sacrifices that lure a king or defender to a bad square [P0882].
- In endgames, pawn breaks that create a passed pawn. Count how many moves each side needs to promote [P0824].

A check or capture that the opponent answers by simply taking your piece is not forcing; it just gives material away.

## Step 3: Verify (at most about 12 inspect_move calls)
- Run **inspect_move** on the top 3 candidates. For each, read every reply that captures, checks, or moves the attacked piece to safety [P1052].
- Follow only the opponent's best reply with inspect_move on the resulting FEN, until the material settles or it is mate.
- Choose the move that wins against every reply. If two moves win, pick the more forcing one.

## Motif: name what the key move does
- **fork**: one move attacks two targets [P0905].
- **discoveredAttack**: moving one piece unmasks an attack by another.
- **pin**: you exploit a piece that cannot move off the line.
- **deflection**: you drive a defender off its duty [P0885].
- **attraction**: you lure the king to a bad square [P0882].
- **intermezzo**: an in-between move before the expected recapture [P1052].
- **advancedPawn / promotion**: a pawn break or pawn race decides.
- **mate, backRankMate, skewer, hangingPiece, trappedPiece, quietMove, clearance, capturingDefender, sacrifice**.

## Answer format
**Best move:** <SAN, copied exactly from legal_moves>

**Main line:** <SAN moves, alternating sides, defender moves are the best replies you tested>

**Motif:** <one term>

**Explanation (3-5 sentences):**
- Name the target the tools revealed [P1037].
- Say what the move threatens, why the defender cannot meet every threat, and what their best reply is.
- Say what is won.
- Give one transferable lesson about spotting this kind of target [P0261].

Do not mention any square, attack or line that you did not see in a tool output.
