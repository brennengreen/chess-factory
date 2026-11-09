"""chess-eyes: an MCP server that gives a model eyes on the board, never an engine.

Every tool reports facts about the current position (legality, attacks, defenders).
None of them searches, scores, or ranks moves.
"""
import os
import chess
from mcp.server.fastmcp import FastMCP

VAL = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}
NAME = {chess.PAWN: "pawn", chess.KNIGHT: "knight", chess.BISHOP: "bishop", chess.ROOK: "rook",
        chess.QUEEN: "queen", chess.KING: "king"}
SIDE = {chess.WHITE: "White", chess.BLACK: "Black"}
mcp = FastMCP("chess-eyes")


def _board(fen):
    try:
        return chess.Board(fen)
    except ValueError as e:
        raise ValueError(f"bad FEN: {e}")


def _desc(b, sq):
    p = b.piece_at(sq)
    return f"{SIDE[p.color]} {NAME[p.piece_type]} on {chess.square_name(sq)}"


def _material(b):
    return {SIDE[c]: sum(VAL[p.piece_type] for p in b.piece_map().values() if p.color == c) for c in chess.COLORS}


def _loose(b, color):
    """Pieces of `color` that are attacked and either undefended or attacked by something cheaper."""
    out = []
    for sq, p in b.piece_map().items():
        if p.color != color or p.piece_type == chess.KING:
            continue
        attackers = b.attackers(not color, sq)
        if not attackers:
            continue
        cheapest = min(VAL[b.piece_at(a).piece_type] for a in attackers)
        defended = bool(b.attackers(color, sq))
        if not defended or cheapest < VAL[p.piece_type]:
            out.append(f"{_desc(b, sq)} (attacked by {', '.join(_desc(b, a) for a in attackers)}; "
                       f"{'defended' if defended else 'UNDEFENDED'})")
    return out


def _pins(b, color):
    return [f"{_desc(b, sq)} is pinned to its king" for sq, p in b.piece_map().items()
            if p.color == color and p.piece_type != chess.KING and b.is_pinned(color, sq)]


@mcp.tool()
def board(fen: str) -> str:
    """Draw the position: diagram, piece list for each side, side to move, check status, material."""
    b = _board(fen)
    lines = [str(b), "", f"{SIDE[b.turn]} to move." + (" (in check)" if b.is_check() else "")]
    for c in chess.COLORS:
        ps = sorted(b.piece_map().items(), key=lambda kv: -VAL[kv[1].piece_type] if kv[1].piece_type != chess.KING else -100)
        lines.append(f"{SIDE[c]}: " + ", ".join(f"{NAME[p.piece_type]} {chess.square_name(s)}" for s, p in ps if p.color == c))
    lines.append(f"Material (P=1,N=B=3,R=5,Q=9): {_material(b)}")
    return "\n".join(lines)


@mcp.tool()
def legal_moves(fen: str) -> str:
    """List every legal move for the side to move, grouped into checks, captures and quiet moves."""
    b = _board(fen)
    checks, caps, quiet = [], [], []
    for m in b.legal_moves:
        san = b.san(m)
        if b.gives_check(m):
            checks.append(san)
        if b.is_capture(m):
            tgt = m.to_square if not b.is_en_passant(m) else chess.square(chess.square_file(m.to_square), chess.square_rank(m.from_square))
            d = "defended" if b.attackers(not b.turn, m.to_square) else "undefended"
            caps.append(f"{san} (takes {NAME[b.piece_at(tgt).piece_type]}, {d})")
        elif not b.gives_check(m):
            quiet.append(san)
    return (f"{SIDE[b.turn]} to move, {b.legal_moves.count()} legal moves.\n"
            f"Checks: {', '.join(checks) or 'none'}\nCaptures: {'; '.join(caps) or 'none'}\nOther: {', '.join(quiet) or 'none'}")


@mcp.tool()
def threats(fen: str) -> str:
    """Report loose pieces (attacked and undefended, or attacked by a cheaper piece) and pins, for both sides."""
    b = _board(fen)
    out = []
    for c in (b.turn, not b.turn):
        who = "side to move" if c == b.turn else "opponent"
        out.append(f"{SIDE[c]} ({who}) loose pieces: " + ("; ".join(_loose(b, c)) or "none"))
        out.append(f"{SIDE[c]} ({who}) pins: " + ("; ".join(_pins(b, c)) or "none"))
    return "\n".join(out)


@mcp.tool()
def inspect_move(fen: str, move: str) -> str:
    """Play one move (SAN like Nxe5 or UCI like g1f3) and describe the resulting position:
    check or mate, what the moved piece now attacks, newly loose pieces, the opponent's checks and
    captures in reply, and the resulting FEN so you can keep exploring."""
    b = _board(fen)
    try:
        m = b.parse_san(move)
    except ValueError:
        try:
            m = chess.Move.from_uci(move)
            if m not in b.legal_moves:
                raise ValueError
        except ValueError:
            return f"{move} is not legal here. Use legal_moves to see the options."
    mover = b.turn
    san = b.san(m)
    before = _material(b)
    b.push(m)
    out = [f"After {san}: FEN {b.fen()}"]
    if b.is_checkmate():
        out.append("CHECKMATE.")
        return "\n".join(out)
    if b.is_stalemate():
        out.append("Stalemate (draw).")
    if b.is_check():
        out.append(f"Check. {SIDE[b.turn]} has {b.legal_moves.count()} legal replies: "
                   + ", ".join(b.san(r) for r in b.legal_moves))
    hit = [_desc(b, s) for s in b.attacks(m.to_square) if b.piece_at(s) and b.piece_at(s).color != mover]
    out.append(f"The {NAME[b.piece_at(m.to_square).piece_type]} on {chess.square_name(m.to_square)} attacks: {', '.join(hit) or 'nothing'}")
    out.append("Opponent loose pieces now: " + ("; ".join(_loose(b, not mover)) or "none"))
    out.append("Your loose pieces now: " + ("; ".join(_loose(b, mover)) or "none"))
    after = _material(b)
    out.append(f"Material change for {SIDE[mover]}: {after[SIDE[mover]] - before[SIDE[mover]] - (after[SIDE[not mover]] - before[SIDE[not mover]]):+d}")
    if not b.is_check():
        rc = [b.san(r) for r in b.legal_moves if b.gives_check(r)]
        rx = [b.san(r) for r in b.legal_moves if b.is_capture(r)]
        out.append(f"Opponent replies: checks {', '.join(rc) or 'none'}; captures {', '.join(rx) or 'none'}")
    return "\n".join(out)



def _aligned(piece_type, a, sq):
    same_line = chess.square_file(a) == chess.square_file(sq) or chess.square_rank(a) == chess.square_rank(sq)
    diag = abs(chess.square_file(a) - chess.square_file(sq)) == abs(chess.square_rank(a) - chess.square_rank(sq))
    return (piece_type in (chess.ROOK, chess.QUEEN) and same_line) or (piece_type in (chess.BISHOP, chess.QUEEN) and diag)


@mcp.tool()
def square_info(fen: str, square: str) -> str:
    """Who controls one square: the piece on it, every piece of each side that attacks or defends it,
    and x-ray attackers lined up behind exactly one blocking piece. Facts only, no evaluation."""
    b = _board(fen)
    try:
        sq = chess.parse_square(square.strip().lower())
    except ValueError:
        return f"{square} is not a square. Use names like e4."
    p = b.piece_at(sq)
    out = [f"{chess.square_name(sq)}: " + (_desc(b, sq) if p else "empty")]
    for c in (b.turn, not b.turn):
        direct = [_desc(b, a) for a in b.attackers(c, sq)]
        xray = []
        for a, q in b.piece_map().items():
            if q.color != c or a == sq or a in b.attackers(c, sq) or not _aligned(q.piece_type, a, sq):
                continue
            blockers = list(chess.SquareSet(chess.between(a, sq)) & chess.SquareSet(b.occupied))
            if len(blockers) == 1:
                xray.append(f"{_desc(b, a)} through {_desc(b, blockers[0])}")
        verb = "defend" if p and p.color == c else "attack"
        who = "side to move" if c == b.turn else "opponent"
        out.append(f"{SIDE[c]} ({who}) pieces that {verb} it ({len(direct)}): {', '.join(direct) or 'none'}")
        out.append(f"{SIDE[c]} x-rays: {'; '.join(xray) or 'none'}")
    return "\n".join(out)

if __name__ == "__main__":
    enabled = set(filter(None, os.environ.get("CHESS_EYES_TOOLS", "").split(",")))
    if enabled:
        for name in list(mcp._tool_manager._tools):
            if name not in enabled:
                mcp._tool_manager._tools.pop(name)
    mcp.run()
