"""Build the train/dev/test splits from a slice of the Lichess puzzle database (CC0)."""
import csv, json, random
import chess

MOTIFS = {
    "fork": {"fork"}, "pin": {"pin"}, "skewer": {"skewer"},
    "discoveredAttack": {"discoveredAttack", "discoveredCheck"}, "doubleCheck": {"doubleCheck"},
    "deflection": {"deflection", "capturingDefender"}, "attraction": {"attraction"},
    "sacrifice": {"sacrifice"}, "hangingPiece": {"hangingPiece"}, "trappedPiece": {"trappedPiece"},
    "promotion": {"promotion", "advancedPawn"}, "intermezzo": {"intermezzo"}, "clearance": {"clearance"},
    "interference": {"interference"}, "xRayAttack": {"xRayAttack"}, "quietMove": {"quietMove"},
    "zugzwang": {"zugzwang"}, "backRankMate": {"backRankMate"},
    "mate": {"mate", "mateIn1", "mateIn2", "mateIn3", "mateIn4", "mateIn5", "smotheredMate", "anastasiaMate",
             "arabianMate", "bodenMate", "dovetailMate", "hookMate", "epauletteMate", "pillsburysMate",
             "operaMate", "cornerMate", "morphysMate", "vukovicMate", "triangleMate", "killBoxMate",
             "balestraMate", "swallowstailMate", "blindSwineMate", "backRankMate"},
}

def motif_hits(themes):
    return sorted(m for m, tags in MOTIFS.items() if tags & set(themes))

def to_item(r, mirror=False):
    board = chess.Board(r["FEN"])
    uci = r["Moves"].split()
    if mirror:
        board = board.mirror()
        uci = [chess.Move(chess.square_mirror(m.from_square), chess.square_mirror(m.to_square), m.promotion).uci()
               for m in map(chess.Move.from_uci, uci)]
    last = chess.Move.from_uci(uci[0])
    last_san = board.san(last)
    board.push(last)
    fen = board.fen()
    sol_san, b = [], board.copy()
    for u in uci[1:]:
        m = chess.Move.from_uci(u)
        sol_san.append(b.san(m)); b.push(m)
    themes = r["Themes"].split()
    return {"id": r["PuzzleId"] + ("m" if mirror else ""), "fen": fen, "last_move": last_san,
            "solution_uci": uci[1:], "solution_san": sol_san, "rating": int(r["Rating"]),
            "themes": themes, "motifs": motif_hits(themes), "game": r["GameUrl"]}

def main():
    rows = list(csv.DictReader(open("data/puzzles_head.csv")))
    ok, seen = [], set()
    for r in rows:
        n = len(r["Moves"].split()) - 1
        game = r["GameUrl"].split("/")[4].split("#")[0]
        if (int(r["Popularity"]) >= 85 and int(r["NbPlays"]) >= 1000 and int(r["RatingDeviation"]) <= 80
                and 1000 <= int(r["Rating"]) <= 2200 and 2 <= n <= 6 and "veryLong" not in r["Themes"]
                and motif_hits(r["Themes"].split()) and game not in seen):
            seen.add(game); ok.append(r)
    random.Random(20261108).shuffle(ok)
    splits = {"train": ok[:200], "dev": ok[200:320], "test": ok[320:560]}
    for name, rs in splits.items():
        with open(f"data/{name}.jsonl", "w") as f:
            for r in rs:
                f.write(json.dumps(to_item(r)) + "\n")
    with open("data/test_mirror.jsonl", "w") as f:
        for r in splits["test"]:
            f.write(json.dumps(to_item(r, mirror=True)) + "\n")
    print({k: len(v) for k, v in splits.items()}, "eligible", len(ok))

if __name__ == "__main__":
    main()
