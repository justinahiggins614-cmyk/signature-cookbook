#!/bin/bash
# The Signature Cookbook 2h drip: +300 recipes toward 1M. Silent on success.
set -e
cd "$(dirname "$0")/.."
git pull -q --ff-only origin main || true
python3 code/gen_recipes.py 300
python3 code/qa_recipes.py || { echo "QA FAILED — not committing"; exit 1; }
python3 code/build_pages.py
node --check js/cookbook.js
for f in /tmp/cb_drip_*.js; do rm -f "$f"; done
python3 - <<'EOF'
import re, glob
for fn in sorted(glob.glob("*.html")):
    s = open(fn).read()
    scripts = re.findall(r"<script>([\s\S]*?)</script>", s)
    open("/tmp/cb_drip_%s.js" % fn.replace(".html",""), "w").write("\n;\n".join(scripts))
EOF
for f in /tmp/cb_drip_*.js; do node --check "$f" || { echo "INLINE JS FAILED — not committing"; exit 1; }; done
git add -A
git commit -qm "Cookbook drip: +300 recipes" || true
git push -q origin main
echo "DRIP OK"
