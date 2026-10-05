#!/usr/bin/env python3
"""QA harness for The Signature Cookbook dataset.
Validates every recipe: structure, quantities, coherence, uniqueness.
Exit 0 = PASS, 1 = FAIL with details."""
import gzip, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CHUNKS = os.path.join(ROOT, "data", "recipes", "chunks")

def load_all():
    recs = []
    for fn in sorted(os.listdir(CHUNKS)):
        if not fn.endswith(".jsonl.gz"):
            continue
        with gzip.open(os.path.join(CHUNKS, fn), "rt", encoding="utf-8") as f:
            for line in f:
                recs.append(json.loads(line))
    return recs

def check(recs):
    fails = []
    seen_ids, seen_names = set(), set()
    for r in recs:
        rid = r.get("id", "?")
        # id format + sequence sanity
        if not re.fullmatch(r"JAH-RECIPE-\d{6}", rid or ""):
            fails.append((rid, "bad id format"))
        if rid in seen_ids:
            fails.append((rid, "duplicate id"))
        seen_ids.add(rid)
        if r.get("name") in seen_names:
            fails.append((rid, "duplicate name %r" % r.get("name")))
        seen_names.add(r.get("name"))
        ings = r.get("ingredients", [])
        if len(ings) < 3:
            fails.append((rid, "ingredients < 3"))
        for i in ings:
            if not str(i.get("qty", "")).strip() or not str(i.get("item", "")).strip():
                fails.append((rid, "ingredient missing qty/item")); break
            if re.search(r"\d\s{2,}\w", i["qty"] + " " + i.get("unit", "")):
                fails.append((rid, "double space in qty: %r" % i)); break
        steps = r.get("steps", [])
        if len(steps) < 3:
            fails.append((rid, "steps < 3"))
        for st in steps:
            if len(st) < 25:
                fails.append((rid, "short step")); break
            if "{" in st or "}" in st:
                fails.append((rid, "template placeholder left")); break
        if r.get("prep_min", 0) + r.get("cook_min", 0) <= 0:
            fails.append((rid, "no time"))
        if not (1 <= r.get("servings", 0) <= 12):
            fails.append((rid, "bad servings"))
        if r.get("difficulty") not in ("Easy", "Medium", "Hard"):
            fails.append((rid, "bad difficulty"))
        if r.get("total_min") != r.get("prep_min", 0) + r.get("cook_min", 0):
            fails.append((rid, "total_min mismatch"))
        blob = " ".join(steps).lower()
        hits = sum(1 for i in ings
                   if len(i["item"].split()[0]) > 3 and i["item"].split()[0].lower().strip(",") in blob)
        if hits < 2:
            fails.append((rid, "ingredient coherence %d/2" % hits))
        # named-dish coherence: a dish naming a specific item should contain it
        nm = (r.get("name") or "").lower()
        for key, need in [("lasagna", "lasagna"), ("hummus", "chickpea"),
                          ("guacamole", "avocado"), ("pancake", "flour")]:
            if key in nm and need not in blob and need not in " ".join(i["item"] for i in ings).lower():
                fails.append((rid, "dish %r missing %r" % (key, need)))
    # id contiguity
    nums = sorted(int(i.split("-")[-1]) for i in seen_ids)
    if nums and nums != list(range(1, len(nums) + 1)):
        fails.append(("DATASET", "ids not contiguous 1..%d" % len(nums)))
    return fails

def main():
    recs = load_all()
    print("recipes checked: %d" % len(recs))
    fails = check(recs)
    by = {}
    for rid, msg in fails:
        by[msg.split(":")[0] if ":" in msg else msg] = by.get(msg.split(":")[0] if ":" in msg else msg, 0) + 1
    if fails:
        print("FAILURES: %d" % len(fails))
        for k in sorted(by):
            print("  %-40s %d" % (k, by[k]))
        for rid, msg in fails[:15]:
            print("  e.g. %s: %s" % (rid, msg))
        return 1
    print("QA: ALL PASS")
    return 0

if __name__ == "__main__":
    sys.exit(main())
