"""Exploratory climbability probes on dev (never test). Each probe is paired against the incumbent r1a.

aa        rerun r1a unchanged (tag r1a-aa, reused by final.py if r1a is final): run-to-run noise
rejudge   re-grade r1a's existing dev outputs with the same judge: judge noise
capacity  same skill and tools, stronger subject model: headroom from model capacity
oracle    same skill and tools, told the correct first move: headroom from calculation
"""
import sys
import grade, subject

PROBES = {
    "aa": dict(tag="r1a-aa"),
    "capacity": dict(tag="r1a@sonnet-5", model="claude-sonnet-5"),
    "oracle": dict(tag="r1a+oracle-move", oracle_move=True),
}


def main(name, limit=None):
    if name == "rejudge":
        grade.grade_run("r1a", "dev", judge_tag="judge-retest")
        return
    p = PROBES[name]
    for _ in range(2):
        subject.run_split("r1a", "dev", p["tag"], workers=4, limit=limit, model=p.get("model"),
                          oracle_move=p.get("oracle_move", False))
    grade.grade_run(p["tag"], "dev")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else None)
