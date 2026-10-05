#!/usr/bin/env python3
"""Builds all static pages for The Signature Cookbook from templates + data."""
import json, os, datetime
STAMP = datetime.date.today().isoformat()

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BASE = "https://justinahiggins614-cmyk.github.io/signature-cookbook"
ORIGIN = "https://justinahiggins614-cmyk.github.io"

NAV = [
 (1, "Signature Math", "signature-math/"),
 (2, "Signature Universal Paradox Immune Calculator", "jah-calculator/"),
 (3, "The Signature Dictionary", "jah-dictionary/"),
 (4, "JAH Wiki", "jah-wiki/"),
 (5, "JAH-N Wiki Leaks", "jah-n-wiki-leaks/"),
 (6, "Signature Llama: The Fully Cyber Utilizable AI", "signature-llama/"),
 (7, "The Signature AI Phone Book", "jah-ai-models/"),
 (8, "Globally Rejustered Patent Catalog", "cyber-patent-catalog/"),
 (9, "Signature Spec Catalog Pending Patents", "signature-one-archive/specs.html"),
 (10, "The Signature PC System Depository", "jah-computer-systems/"),
 (11, "The Signature Book Depository", "signature-books/"),
 (12, "The Signature Comic Store", "signature-comics/"),
 (13, "The Signature Global Newspaper Archive", "signature-newspapers/"),
 (14, "The Signature AI Mix and Match Generator", "signature-backend/"),
 (15, "The Signature Boundless Generator Archive", "signature-boundless-generators/"),
 (16, "The Signature AI Mix Lab", "signature-ai-mixlab/"),
 (17, "AI Olympics", "signature-ai-olypics/"),
 (18, "The Signature Computer Chip Maker and Archive", "signature-chip-maker/"),
 (19, "The Signature App Archive", "signature-app-archive/"),
 (20, "The Signature AI to Robot Matcher", "signature-ai-robot-matcher/"),
 (21, "The Signature Experiment Solver", "signature-experiment-solver/"),
 (22, "Signature AI Pixel", "signature-ai-image-video-maker/"),
 (23, "Signature Music Studio", "signature-ai-song-maker/"),
 (24, "The Signature Mr Fix-It", "signature-fixit/"),
 (25, "The Signature University", "signature-university/"),
 (26, "The Signature Cyber Mega-Mall", "signature-cyber-mega-mall/"),
 (27, "The Signature 3D Print Mega Mall", "signature-3d-print/"),
 (28, "Signature Earth", "signature-earth/"),
 (29, "The Signature Flight School", "signature-flight-school/"),
 (30, "The Signature Game Store", "signature-game-store/"),
 (31, "Signature Website Creator", "signature-website-creator/"),
 (32, "The Signature Antivirus", "signature-antivirus/"),
 (33, "The Signature OS Updater", "signature-os-updater/"),
 (34, "Signature Space Mapping", "signature-space-mapping/"),
 (35, "The Signature Cookbook", "signature-cookbook/"),
]

CHAPTERS = [
 ("appetizers", "🥗", "Appetizers", "Little bites that start the party."),
 ("soups", "🍲", "Soups & Salads", "Warm bowls and crisp greens."),
 ("mains", "🍽️", "Mains", "The center of the table."),
 ("sides", "🥔", "Sides", "The supporting cast that steals the show."),
 ("breads", "🍞", "Breads", "Warm from the oven."),
 ("desserts", "🍰", "Desserts", "Save room."),
 ("drinks", "🥤", "Drinks", "Sip something good."),
 ("breakfast", "🍳", "Breakfast", "Start the day right."),
 ("snacks", "🍿", "Snacks", "For the in-between hours."),
]

def nav_html():
    parts = ['<div class="jahnet"><span class="jahnet-t">THE JAH NETWORK</span>']
    for n, name, url in NAV:
        if n == 35:
            parts.append('<br><span class="here">35 The Signature Cookbook — YOU ARE HERE</span>')
        else:
            parts.append('<a href="https://justinahiggins614-cmyk.github.io/' + url + '">' + str(n) + ' ' + name + '</a>')
    parts.append('</div>')
    return "".join(parts)

def tabs_html(active):
    tabs = [("index.html", "🏠 Main", "index")]
    for slug, emoji, name, _ in CHAPTERS:
        tabs.append((slug + ".html", emoji + " " + name, slug))
    tabs.append(("archive.html", "🗂️ 1M Archive", "archive"))
    out = ['<nav class="tabs" aria-label="Site sections">']
    for href, label, key in tabs:
        cls = ' class="active"' if key == active else ""
        out.append('<a href="%s"%s>%s</a>' % (href, cls, label))
    out.append("</nav>")
    return "".join(out)

CSS = """<style>
:root{--tom:#e8833a;--tom2:#f5b06e;--bg:#241610;--panel:#3a2417;--line:#6b4426;--txt:#f7ecd9;--dim:#c9a87f}
*{box-sizing:border-box}
body{margin:0;font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;color:var(--txt);background:var(--bg);min-height:100vh}
.wrap{max-width:1060px;margin:0 auto;padding:14px 12px 40px}
.kicker{letter-spacing:.25em;font-size:.72rem;color:var(--tom);margin:10px 0 4px}
h1{font-size:1.7rem;margin:.1em 0}
h2{color:var(--tom2);font-size:1.3rem;margin:1.2em 0 .4em}
h3{color:var(--tom2)}
p{line-height:1.6}
.tabs{display:flex;gap:10px;flex-wrap:wrap;margin:12px 0}
.tabs a{flex:1 1 130px;text-align:center;text-decoration:none;color:var(--txt);background:var(--panel);border:2px solid var(--line);border-radius:999px;padding:11px 8px;font-weight:700;font-size:.92rem}
.tabs a.active{background:var(--tom);color:#241610;border-color:var(--tom)}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px;margin:12px 0}
.card h3{margin:.2em 0}
.btn{display:inline-block;background:var(--tom);color:#241610;border:0;border-radius:999px;padding:12px 24px;font-weight:800;font-size:1rem;cursor:pointer;text-decoration:none;margin:6px 6px 6px 0;font-family:inherit}
.btn.ghost{background:transparent;color:var(--tom2);border:2px solid var(--tom)}
.btn.sm{padding:9px 16px;font-size:.9rem}
.btn.big{font-size:1.2rem;padding:15px 36px}
.hint{color:var(--dim);font-size:.85rem}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px}
.jahnet{margin:26px 0 10px;padding:14px;border:1px solid var(--line);border-radius:14px;background:#2c1c11;font-size:.82rem;line-height:2.1}
.jahnet-t{color:var(--tom);font-weight:800;letter-spacing:.2em;margin-right:10px}
.jahnet a{color:var(--dim);text-decoration:none;margin:0 8px 0 0;white-space:nowrap}
.jahnet .here{display:inline-block;background:#4a2c12;color:var(--tom2);border:1px solid var(--tom);border-radius:999px;padding:2px 12px;font-weight:800;margin:4px 0}
footer{color:#8a6a4a;font-size:.78rem;text-align:center;margin:20px 0}
.recipe{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:18px;margin:14px 0}
.recipe h2{margin:.1em 0}
.rmeta{color:var(--dim)}
.ings li,.steps li{margin:7px 0;line-height:1.55}
.steps li::marker{color:var(--tom);font-weight:800}
.rtools{margin:10px 0}
.az{margin:8px 0}
.az summary{cursor:pointer;font-weight:800;color:var(--tom2);padding:10px;background:#2c1c11;border:1px solid var(--line);border-radius:10px;margin:4px 0}
.az .row{padding:8px 4px;border-bottom:1px dashed #4a2f1a;font-size:.92rem}
.az .row a{color:var(--txt);text-decoration:none}
.az .row a:hover{color:var(--tom2)}
.best{border:2px solid var(--tom);background:#3d2a14}
input[type=text]{background:#1c100a;color:var(--txt);border:2px solid var(--line);border-radius:10px;padding:11px 13px;font-size:.95rem;width:100%}
.rlink{color:var(--txt);text-decoration:none}
.rlink:hover{color:var(--tom2)}
.hits li{margin:6px 0}
.hits a{color:var(--tom2)}
#cookMode .btn.big{min-height:64px;font-size:1.25rem}
#cookMode .btn.big:disabled{opacity:.35}
.azbody{min-height:8px}
.counter{font-size:1.15rem;font-weight:800;color:var(--tom2)}
</style>"""

WELCOME_CSS = """<style>
#jahWelcome,#jahGuide,#jahGuideBtn{--amber:#e8833a;--amber2:#f5b06e}
#jahGuideBtn{position:fixed;top:14px;right:14px;z-index:99900;min-width:48px;min-height:48px;border-radius:24px;border:1px solid var(--amber);background:#2c1c11;color:var(--amber2);font-weight:700;font-size:18px;padding:10px 16px;cursor:pointer}
#jahGuideBtn:hover{background:var(--amber);color:#241610}
#jahWelcome{position:fixed;inset:0;z-index:100000;display:none;align-items:center;justify-content:center;padding:16px;background:rgba(0,0,0,.75)}
#jahWelcome.show{display:flex}
#jahWelcomeCard{background:#2c1c11;border:2px solid var(--amber);border-radius:14px;padding:22px 20px;max-width:540px;width:100%;max-height:88vh;overflow-y:auto;color:var(--txt)}
#jahWelcomeCard h2{margin:0 0 4px;color:var(--amber2);font-size:20px}
#jahWelcomeCard .wsub{margin:4px 0 0;color:var(--dim);font-size:14px}
#jahWelcomeCard ol{margin:10px 0 0;padding-left:22px;font-size:14px;line-height:1.55}
#jahWelcomeCard ol li{margin:8px 0}
#jahWelcomeCard ol li b{color:var(--amber2)}
#jahWelcomeCard .wbtnrow{display:flex;gap:10px;margin-top:16px;flex-wrap:wrap}
#jahGuide .btn,#jahWelcome .btn{min-height:48px;min-width:48px;font-size:15px;padding:12px 22px;border-radius:10px;border:1px solid var(--amber);background:transparent;color:var(--amber2);cursor:pointer;font-family:inherit}
#jahWelcomeOk{font-weight:700;background:var(--amber)!important;color:#241610!important;border:none!important}
#jahGuide{position:fixed;inset:0;z-index:99900;display:none;align-items:center;justify-content:center;padding:16px;background:rgba(0,0,0,.7)}
#jahGuide.show{display:flex}
#jahGuideCard{background:#2c1c11;border:1px solid var(--amber);border-radius:14px;max-width:680px;width:100%;max-height:86vh;overflow:auto;padding:20px 22px;color:var(--txt)}
#jahGuideCard h2{margin-top:0;color:var(--amber2)}
#jahGuideCard .gfeat{margin:0 0 14px;padding:10px 12px;background:#241610;border:1px solid var(--line);border-radius:10px}
#jahGuideCard .gfeat b{color:var(--amber2)}
#jahGuideCard .gfeat p{margin:4px 0 0;font-size:14px;line-height:1.5}
#jahGuideCloseRow{display:flex;gap:10px;margin-bottom:12px;flex-wrap:wrap;align-items:center;justify-content:space-between}
</style>"""

WELCOME_HTML = """<button id="jahGuideBtn" aria-label="Open the site guide" title="How to use this site">?</button>
<div id="jahWelcome" aria-hidden="true">
<div id="jahWelcomeCard" role="dialog" aria-modal="true" aria-label="Welcome to The Signature Cookbook">
<h2>Welcome to The Signature Cookbook</h2>
<p class="wsub">A million recipes, organized like a real cookbook &mdash; free forever. Here&rsquo;s how to use it:</p>
<ol>
<li><b>Pick a chapter.</b> The tabs up top are the cookbook chapters &mdash; Appetizers through Snacks.</li>
<li><b>Open any recipe.</b> Every recipe has real quantities, ordered steps, time, and servings. Tap <b>🍳 Cook mode</b> for one-step-at-a-time guidance with timers.</li>
<li><b>Cook hands-free.</b> Tap &ldquo;Read aloud&rdquo; and the recipe reads itself to you, step by step.</li>
<li><b>Keep it.</b> Copy any recipe or download it as a text file &mdash; yours to keep, free.</li>
<li><b>The Archive.</b> The last tab holds everything: chapters, sections, A&ndash;Z, marching to a million.</li>
</ol>
<div class="wbtnrow">
<button class="btn" id="jahWelcomeOk" type="button">OK &mdash; Got it ✓</button>
<button class="btn" id="jahWelcomeFull" type="button">Full how-to guide</button>
</div></div></div>
<div id="jahGuide" aria-hidden="true">
<div id="jahGuideCard" role="dialog" aria-modal="true" aria-label="How to use The Signature Cookbook">
<div id="jahGuideCloseRow"><h2 style="margin:0">How to use this site</h2>
<button class="btn" id="jahGuideClose" type="button">✕ Close</button></div>
<div class="gfeat"><b>📖 Chapters</b><p><b>What:</b> the tab bar. <b>Does:</b> each tab is a cookbook chapter with its sections and recipes. <b>How:</b> tap a tab.</p></div>
<div class="gfeat"><b>🍳 Recipes</b><p><b>What:</b> every recipe page. <b>Does:</b> ingredients with quantities, ordered steps, time, servings, difficulty. <b>How:</b> open any recipe from a chapter or the archive.</p></div>
<div class="gfeat"><b>🍳 Cook mode</b><p><b>What:</b> hands-on guidance. <b>Does:</b> walks you through one step at a time with big buttons, built-in timers for every timed step, and a read-aloud option. <b>How:</b> tap “🍳 Cook mode” on any recipe.</p></div>
<div class="gfeat"><b>🤖 Cooking AI</b><p><b>What:</b> the recipe helper. <b>Does:</b> answers substitutions, timing, servings, and ingredient questions from the recipe. <b>How:</b> the “Ask the cooking AI” box on every recipe.</p></div>
<div class="gfeat"><b>🔊 Read aloud</b><p><b>What:</b> hands-free cooking. <b>Does:</b> reads the whole recipe to you, step by step. <b>How:</b> tap &ldquo;Read aloud&rdquo; on any recipe.</p></div>
<div class="gfeat"><b>📋 Copy &amp; ⬇ Download</b><p><b>What:</b> keepers. <b>Does:</b> copy a recipe to your clipboard or download it as a text file. <b>How:</b> the buttons on every recipe.</p></div>
<div class="gfeat"><b>🗂️ The 1M Archive</b><p><b>What:</b> everything. <b>Does:</b> all recipes organized chapters → sections → A&ndash;Z, with the AI&rsquo;s Best of the Best on top and an Ask-the-AI box. <b>How:</b> the last tab.</p></div>
<div class="gfeat"><b>🤖 Ask the AI</b><p><b>What:</b> the recipe finder. <b>Does:</b> type a dish or ingredient and it finds matching recipes. <b>How:</b> the box on the archive page.</p></div>
<div class="btnrow" style="display:flex;gap:10px;flex-wrap:wrap;margin-top:6px">
<button class="btn" id="jahGuideTour" type="button">▶ Show the welcome guide</button>
<button class="btn" id="jahGuideClose2" type="button">✕ Close guide</button>
</div></div></div>
<script>(function(){try{
var FLAG="jah-tour-seen-cookbook";
var JAHPS=(function(){try{return (typeof JAHProfile!=="undefined")&&JAHProfile.store?JAHProfile.store:localStorage;}catch(e){return localStorage;}})();
function ls(k,v){try{if(v===undefined)return JAHPS.get(k);JAHPS.set(k,v)}catch(e){return null}}
var w=document.getElementById("jahWelcome"),guide=document.getElementById("jahGuide"),
    guideCard=document.getElementById("jahGuideCard"),guideBtn=document.getElementById("jahGuideBtn");
function openWelcome(){if(!w)return;w.classList.add("show");w.setAttribute("aria-hidden","false");
  try{document.getElementById("jahWelcomeOk").focus({preventScroll:true})}catch(e){}}
function closeWelcome(){if(!w)return;w.classList.remove("show");w.setAttribute("aria-hidden","true");ls(FLAG,"1")}
document.getElementById("jahWelcomeOk").onclick=closeWelcome;
document.getElementById("jahWelcomeFull").onclick=function(){closeWelcome();openGuide()};
w.addEventListener("click",function(e){if(e.target===w)closeWelcome()});
document.addEventListener("keydown",function(e){if(w.classList.contains("show")&&e.key==="Escape"){closeWelcome();e.preventDefault()}});
function openGuide(){if(!guide)return;guide.classList.add("show");guide.setAttribute("aria-hidden","false");
  try{guideCard.scrollTop=0;document.getElementById("jahGuideClose").focus({preventScroll:true})}catch(e){}}
function closeGuide(){if(!guide)return;guide.classList.remove("show");guide.setAttribute("aria-hidden","true");
  try{guideBtn.focus({preventScroll:true})}catch(e){}}
guideBtn.onclick=openWelcome;
document.getElementById("jahGuideClose").onclick=closeGuide;
document.getElementById("jahGuideClose2").onclick=closeGuide;
document.getElementById("jahGuideTour").onclick=function(){closeGuide();openWelcome()};
guide.addEventListener("click",function(e){if(e.target===guide)closeGuide()});
if(!ls(FLAG)){setTimeout(openWelcome,900)}
}catch(e){}})();</script>"""

SIGNIN_HTML = """<script src="js/signin.js"></script>
<script src="js/godmode.js"></script>
<script>
(function () {
  var mount = document.querySelector('header .booksearch') ||
              document.querySelector('nav.jtabbar') ||
              document.querySelector('header nav') ||
              document.querySelector('header') ||
              document.body;
  if (window.JAHProfile && JAHProfile.ui) JAHProfile.ui.renderButton(mount);
})();
</script>
<script>
(function () {
  if (window.JAHProfile && JAHProfile.ui) {
    var mount = document.querySelector('header') || document.body;
    JAHProfile.ui.renderGreeting(mount);
  }
})();
</script>"""

def shell(title, desc, active_tab, body):
    t = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<title>__TITLE__ — The Signature Cookbook</title>
<meta name="description" content="__DESC__">
<link rel="canonical" href="__BASE__/">
__CSS__
</head>
<body>
<div class="wrap">
<header>
<p class="kicker">SITE 35 OF 35 · THE JAH NETWORK</p>
<h1>📖 The Signature Cookbook</h1>
<p class="hint">A million recipes, organized like a cookbook. Free forever.</p>
</header>
__TABS__
__BODY__
__NAV__
<footer>The Signature Cookbook · original Signature recipes · every instruction written fresh · free forever — no account, no catch</footer>
</div>
__WELCOME_CSS__
__WELCOME_HTML__
<script src="js/cookbook.js"></script>
__SIGNIN__
</body>
</html>"""
    t = t.replace("__TITLE__", title).replace("__DESC__", desc).replace("__BASE__", BASE)
    t = t.replace("__CSS__", CSS).replace("__TABS__", tabs_html(active_tab))
    t = t.replace("__BODY__", body).replace("__NAV__", nav_html())
    t = t.replace("__WELCOME_CSS__", WELCOME_CSS).replace("__WELCOME_HTML__", WELCOME_HTML)
    t = t.replace("__SIGNIN__", SIGNIN_HTML)
    return t

# ---------------- page bodies ----------------
def build_index(stats):
    total = stats["total"]
    cards = []
    for slug, emoji, name, tag in CHAPTERS:
        n = stats["per_chapter"].get(name, 0)
        cards.append('<div class="card"><h3>%s %s</h3><p>%s</p><p class="hint">%d recipes</p><a class="btn sm" href="%s.html">Open chapter</a></div>'
                     % (emoji, name, tag, n, slug))
    body = """
<div class="card" style="border:2px solid var(--tom)">
<h3>🍳 Welcome to the kitchen</h3>
<p style="font-size:1.1rem"><b>Our promise:</b> a million recipes, organized like a real cookbook —
chapters, sections, A&ndash;Z &mdash; every one with real quantities, ordered steps, honest times.
<b>Free forever.</b> No account, no payments, no catch. Cook anything, keep everything.</p>
<p>Every instruction is written fresh for this cookbook. Tap <b>🔊 Read aloud</b> on any recipe
and it reads itself to you while your hands are busy.</p>
<a class="btn big" href="archive.html">🗂️ Browse the 1M Archive</a>
<a class="btn ghost" href="mains.html">See what's for dinner</a>
</div>
<div class="card">
<h3>📊 By the numbers</h3>
<p class="counter"><b id="recipeCount">%d</b> / 1,000,000 recipes</p>
<p class="hint">On the shelves and counting · grows every 2 hours (stamped %%STAMP%%).</p>
</div>
<h2>Chapters</h2>
<div class="grid">
%s
</div>""" % (total, "\n".join(cards))
    return shell("A million recipes, organized like a cookbook",
                 "The Signature Cookbook: a million original recipes in chapters, free forever.",
                 "index", body)

def build_chapter(slug, emoji, name, tag, stats):
    n = stats["per_chapter"].get(name, 0)
    body = """
<div class="card">
<h3>%s %s</h3>
<p>%s</p>
<p class="hint"><b id="chapCount">%d</b> recipes in this chapter · <span id="chapSecs"></span></p>
</div>
<div id="chapList"><p class="hint">Loading recipes…</p></div>
<script>
cbLoadIdx().then(function(rows){
  var mine = rows.filter(function(r){return r.c === %s});
  var secs = {};
  mine.forEach(function(r){ (secs[r.s] = secs[r.s] || []).push(r); });
  document.getElementById("chapCount").textContent = mine.length;
  document.getElementById("chapSecs").textContent = Object.keys(secs).length + " sections";
  var h = "";
  Object.keys(secs).sort().forEach(function(s){
    h += '<details class="az"><summary>📑 ' + cbesc(s) + ' (' + secs[s].length + ')</summary>';
    secs[s].forEach(function(r){
      h += '<div class="row"><a class="rlink" href="archive.html?recipe=' + r.id + '"><b>' + cbesc(r.n) + '</b></a>' +
           ' <span class="hint">⏱ ' + r.t + ' min · ' + cbesc(r.d) + '</span></div>';
    });
    h += '</details>';
  });
  document.getElementById("chapList").innerHTML = h || '<p class="hint">No recipes yet in this chapter.</p>';
}).catch(function(){ document.getElementById("chapList").innerHTML = '<p class="hint">Could not load recipes.</p>'; });
</script>""" % (emoji, name, tag, n, json.dumps(name))
    return shell(name + " recipes", "The Signature Cookbook chapter: " + name + ".",
                 slug, body)

BEST_ID = "JAH-RECIPE-000010"

def build_archive(stats):
    total = stats["total"]
    body = """
<div class="card best" id="bestBox"><h3>🌟 AI's Best of the Best</h3><div id="bestRecipe"><p class="hint">Plating up…</p></div></div>
<div class="card">
<h3>🤖 Ask the AI</h3>
<p class="hint">Type a dish, ingredient, or chapter — I'll find it in the archive.</p>
<input type="text" id="askq" placeholder='e.g. "chocolate", "chicken soup", "salad"…' aria-label="Ask the AI">
<div style="margin-top:8px"><button class="btn sm" onclick="cbAsk(document.getElementById('askq').value, document.getElementById('askout'))">Ask</button></div>
<div id="askout" style="margin-top:8px"></div>
</div>
<div id="recipeView" style="display:none">
<button class="btn sm ghost" onclick="cbShowArchive()">← Back to the archive</button>
<div id="recipeDetail"></div>
</div>
<div id="archiveList">
<div class="card">
<h3>🗂️ The 1M Archive</h3>
<p class="counter"><b id="archCount">%d</b> / 1,000,000 recipes</p>
<p class="hint">Chapters → sections → A&ndash;Z · tap a letter to open it · grows every 2 hours (stamped %%STAMP%%).</p>
</div>
<div id="azTree"><p class="hint">Loading the shelves…</p></div>
</div>
<script>
var CB_CHAPTERS = %s;
function cbShowArchive(){
  document.getElementById("recipeView").style.display = "none";
  document.getElementById("archiveList").style.display = "block";
  try{history.replaceState(null, "", "archive.html")}catch(e){}
}
function cbShowRecipe(id){
  cbGetRecipe(id).then(function(r){
    document.getElementById("archiveList").style.display = "none";
    var v = document.getElementById("recipeView"); v.style.display = "block";
    document.getElementById("recipeDetail").innerHTML = cbRecipeHTML(r);
    document.title = r.name + " — The Signature Cookbook";
    window.scrollTo(0, 0);
  }).catch(function(){
    document.getElementById("recipeDetail").innerHTML = '<p class="hint">Recipe not found.</p>';
    document.getElementById("recipeView").style.display = "block";
    document.getElementById("archiveList").style.display = "none";
  });
}
cbLoadIdx().then(function(rows){
  document.getElementById("archCount").textContent = rows.length.toLocaleString("en-US");
  var tree = {}, groups = {}, gid = 0;
  rows.forEach(function(r){
    tree[r.c] = tree[r.c] || {};
    tree[r.c][r.s] = tree[r.c][r.s] || {};
    var L = (r.n[0] || "#").toUpperCase();
    var g = tree[r.c][r.s][L];
    if(!g){ g = {rows: []}; tree[r.c][r.s][L] = g; }
    g.rows.push(r);
  });
  var h = "";
  CB_CHAPTERS.forEach(function(ch){
    var secs = tree[ch[2]];
    if(!secs) return;
    var count = 0;
    Object.keys(secs).forEach(function(s){ Object.keys(secs[s]).forEach(function(L){ count += secs[s][L].rows.length; }); });
    h += '<details class="az"><summary>' + ch[1] + ' ' + cbesc(ch[2]) + ' (' + count + ')</summary>';
    Object.keys(secs).sort().forEach(function(s){
      var sc = 0;
      Object.keys(secs[s]).forEach(function(L){ sc += secs[s][L].rows.length; });
      h += '<details class="az"><summary>\U0001F4D1 ' + cbesc(s) + ' (' + sc + ')</summary>';
      Object.keys(secs[s]).sort().forEach(function(L){
        gid++;
        groups[gid] = secs[s][L].rows;
        h += '<details class="az" data-gid="' + gid + '"><summary>' + cbesc(L) + ' (' + secs[s][L].rows.length + ')</summary><div class="azbody"><p class="hint">Opening\u2026</p></div></details>';
      });
      h += '</details>';
    });
    h += '</details>';
  });
  var zt = document.getElementById("azTree");
  zt.innerHTML = h;
  /* lazy: a letter's rows enter the DOM only the first time it is opened */
  zt.addEventListener("toggle", function(e){
    var d = e.target;
    if(!d || d.tagName !== "DETAILS" || !d.hasAttribute("data-gid")) return;
    if(!d.open || d.getAttribute("data-filled")) return;
    d.setAttribute("data-filled", "1");
    var grp = groups[parseInt(d.getAttribute("data-gid"), 10)] || [];
    grp.sort(function(a, b){ return a.n < b.n ? -1 : 1; });
    var hh = "";
    for(var i = 0; i < grp.length; i++){
      var r = grp[i];
      hh += '<div class="row"><a href="archive.html?recipe=' + r.id + '"><b>' + cbesc(r.n) + '</b></a>' +
            ' <span class="hint">\u23f1 ' + r.t + ' min \u00b7 ' + cbesc(r.d) + ' \u00b7 ' + r.id + '</span></div>';
    }
    var body = d.querySelector(".azbody");
    if(body) body.innerHTML = hh;
  }, true);
  var m = /[?&]recipe=(JAH-RECIPE-\\d{6})/.exec(location.search);
  if(m) cbShowRecipe(m[1]);
});
cbGetRecipe("%s").then(function(r){
  document.getElementById("bestRecipe").innerHTML = cbRecipeHTML(r);
}).catch(function(){
  document.getElementById("bestRecipe").innerHTML = '<p class="hint">Best pick coming right up.</p>';
});
document.getElementById("askq").addEventListener("keydown", function(e){
  if(e.key === "Enter") cbAsk(e.target.value, document.getElementById("askout"));
});
</script>""" % (total, json.dumps([[s, e, n] for s, e, n, _ in CHAPTERS]), BEST_ID)
    return shell("The 1M Recipe Archive", "Every Signature cookbook recipe: chapters, sections, A-Z.",
                 "archive", body)

# ---------------- sitemap / api ----------------
def build_sitemap(total):
    urls = [BASE + "/", BASE + "/archive.html"]
    for slug, _, _, _ in CHAPTERS:
        urls.append(BASE + "/" + slug + ".html")
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        sm.append("  <url><loc>%s</loc><changefreq>daily</changefreq></url>" % u)
    # per-recipe deep links
    idx_path = os.path.join(ROOT, "data", "index", "recipes.idx.json")
    if os.path.exists(idx_path):
        for row in json.load(open(idx_path)):
            sm.append("  <url><loc>%s/archive.html?recipe=%s</loc><changefreq>monthly</changefreq></url>" % (BASE, row["id"]))
    sm.append("</urlset>")
    open(os.path.join(ROOT, "sitemap.xml"), "w").write("\n".join(sm))
    open(os.path.join(ROOT, "robots.txt"), "w").write(
        "User-agent: *\nAllow: /\nSitemap: %s/sitemap.xml\n" % BASE)

def build_api(stats):
    api = {"site": "The Signature Cookbook", "url": BASE + "/",
           "recipes": stats["total"], "goal": 1000000,
           "chapters": [n for _, _, n, _ in CHAPTERS],
           "per_chapter": stats["per_chapter"], "updated": "2026-10-05",
           "free": True}
    json.dump(api, open(os.path.join(ROOT, "api.json"), "w"), indent=1)

def main():
    stats = json.load(open(os.path.join(ROOT, "data", "stats.json")))
    pages = {"index.html": build_index(stats), "archive.html": build_archive(stats)}
    for slug, emoji, name, tag in CHAPTERS:
        pages[slug + ".html"] = build_chapter(slug, emoji, name, tag, stats)
    for fn, html in pages.items():
        open(os.path.join(ROOT, fn), "w").write(html.replace("%STAMP%", STAMP))
    build_sitemap(stats["total"])
    build_api(stats)
    print("PAGES: %d built, %d recipes" % (len(pages), stats["total"]))

if __name__ == "__main__":
    main()
