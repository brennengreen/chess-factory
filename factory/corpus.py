"""The teacher's library: human-written chess instruction, chunked for BM25 retrieval.

Sources: Capablanca, Chess Fundamentals (1921); Edward Lasker, Chess Strategy (1915) and
Chess and Checkers: The Way to Mastership (1918), all public domain via Project Gutenberg;
and Wikipedia's articles on chess tactics (CC BY-SA 4.0).
"""
import json, re
from pathlib import Path
from rank_bm25 import BM25Okapi

RAW = Path(__file__).resolve().parent.parent / "corpus/raw"
BOOKS = {"pg33870.txt": "Capablanca, Chess Fundamentals (1921)",
         "pg5614.txt": "E. Lasker, Chess Strategy (1915)",
         "pg4913.txt": "E. Lasker, Chess and Checkers: The Way to Mastership (1918)"}
TOK = re.compile(r"[a-z]+")


def _gutenberg_body(text):
    s = re.search(r"\*\*\* ?START OF.*?\*\*\*", text)
    e = re.search(r"\*\*\* ?END OF", text)
    body = text[s.end() if s else 0:e.start() if e else len(text)]
    cut = re.search(r"\n\s*PART II\s*\n\s*THE GAME OF CHECKERS", body)
    return body[:cut.start()] if cut else body


def chunks(words_per=170):
    out = []
    docs = [(BOOKS[f], _gutenberg_body((RAW / f).read_text(errors="ignore"))) for f in BOOKS]
    for p in sorted(RAW.glob("wiki_*.json")):
        page = list(json.loads(p.read_text())["query"]["pages"].values())[0]
        docs.append((f"Wikipedia, \"{page['title']}\" (CC BY-SA 4.0)", page.get("extract", "")))
    for src, text in docs:
        paras = [re.sub(r"\s+", " ", x).strip() for x in re.split(r"\n\s*\n", text)]
        buf = []
        for para in paras:
            if "checker" in para.lower() or "king row" in para.lower():
                continue
            if len(para) < 40 or sum(c.isalpha() for c in para) < 0.6 * len(para):
                continue  # skip headings and move-list-only paragraphs
            buf += para.split()
            while len(buf) >= words_per:
                out.append({"source": src, "text": " ".join(buf[:words_per])})
                buf = buf[words_per - 30:]
        if len(buf) > 60:
            out.append({"source": src, "text": " ".join(buf)})
    for i, c in enumerate(out):
        c["id"] = f"P{i:04d}"
    return out


class Library:
    def __init__(self):
        self.docs = chunks()
        self.bm25 = BM25Okapi([TOK.findall(d["text"].lower()) for d in self.docs])

    def search(self, query, k=4):
        scores = self.bm25.get_scores(TOK.findall(query.lower()))
        top = sorted(range(len(scores)), key=lambda i: -scores[i])[:k]
        return [self.docs[i] for i in top]


if __name__ == "__main__":
    lib = Library()
    print(len(lib.docs), "passages")
    for d in lib.search("look at every check and capture before deciding on a move forcing", 3):
        print(d["id"], d["source"], "::", d["text"][:300], "\n")
