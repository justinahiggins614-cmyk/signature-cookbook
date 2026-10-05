#!/usr/bin/env python3
"""Deterministic recipe generator for The Signature Cookbook.
Every recipe: JAH-RECIPE-######, original instructions (never copied text),
sane quantities, logical step order. QA-gated: reject-and-regenerate.
"""
import gzip, json, math, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data", "recipes")
CHUNKS = os.path.join(DATA, "chunks")
STATE = os.path.join(DATA, "state.json")
IDX = os.path.join(ROOT, "data", "index", "recipes.idx.json")
STATS = os.path.join(ROOT, "data", "stats.json")
CHUNK_SIZE = 100

# ---------------- quantity helpers ----------------
FRACS = [(0.25, "1/4"), (1/3.0, "1/3"), (0.5, "1/2"), (2/3.0, "2/3"), (0.75, "3/4")]

def fmt_num(v):
    for f, s in FRACS:
        if abs(v - f) < 0.02:
            return s
    if abs(v - round(v)) < 0.02:
        return str(int(round(v)))
    whole = int(v)
    rem = v - whole
    for f, s in FRACS:
        if abs(rem - f) < 0.06:
            return ("%d %s" % (whole, s)) if whole else s
    return ("%.1f" % v).rstrip("0").rstrip(".")

def qty(rng, kind, lo=None, hi=None):
    if kind == "cup":
        cands = [0.25, 1/3.0, 0.5, 2/3.0, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.5, 3, 4]
        cands = [c for c in cands if (lo is None or c >= lo - 0.01) and (hi is None or c <= hi + 0.01)]
        v = rng.choice(cands)
        return fmt_num(v), "cup" if v <= 1 else "cups"
    if kind == "tbsp":
        v = rng.choice([0.5, 1, 2, 3, 4])
        return fmt_num(v), "tablespoon" if v <= 1 else "tablespoons"
    if kind == "tsp":
        v = rng.choice([0.25, 0.5, 1, 2])
        return fmt_num(v), "teaspoon" if v <= 1 else "teaspoons"
    if kind == "count":
        lo, hi = lo or 1, hi or 4
        v = rng.randint(lo, hi)
        return str(v), ""
    if kind == "lb":
        v = rng.choice([0.5, 0.75, 1, 1.5, 2])
        return fmt_num(v), "pound" if abs(v - 1) < 0.02 else "pounds"
    if kind == "oz":
        v = rng.choice([4, 6, 8, 12, 16])
        return str(v), "ounces"
    if kind == "can":
        v = rng.choice([1, 2])
        return str(v), "(15-ounce) can" if v == 1 else "(15-ounce) cans"
    if kind == "clove":
        v = rng.randint(1, 4)
        return str(v), "clove" if v == 1 else "cloves"
    return "1", ""

def ing(qty_kind, item, rng, lo=None, hi=None, prep=""):
    q, u = qty(rng, qty_kind, lo, hi)
    name = (prep + " " + item).strip() if prep else item
    return {"qty": q, "unit": u, "item": name}

def fmt_ing(i):
    parts = [i["qty"]]
    if i["unit"]:
        parts.append(i["unit"])
    parts.append(i["item"])
    return " ".join(p for p in parts if p)

# ---------------- name helpers ----------------
PREFIX = ["Classic", "Golden", "Rustic", "Creamy", "Hearty", "Zesty", "Savory",
          "Crispy", "Tender", "Smoky", "Fresh", "Homestyle", "Easy", "Garden", "Sunny"]
SUFFIX = ["", "", "", "Supreme", "Deluxe", "with Herbs", "with Garlic", "Special"]

def dish_name(rng, base, used, sweet=False):
    for _ in range(40):
        p = rng.choice(PREFIX)
        s = rng.choice(SUFFIX_SWEET if sweet else SUFFIX)
        nm = (p + " " + base + (" " + s if s else "")).strip()
        if nm not in used:
            return nm
    # fallback: numbered variant (still unique, still sane)
    k = 2
    while ("%s (Style %d)" % (base, k)) in used:
        k += 1
    return "%s (Style %d)" % (base, k)

# ---------------- method builders ----------------
# Each returns (ingredients[list of dict], steps[list of str], prep_min, cook_min)

def m_soup(rng, base=None, hearty=True):
    fat = ing("tbsp", rng.choice(["olive oil", "butter", "vegetable oil"]), rng, hi=3)
    arom = [ing("count", rng.choice(["yellow onion", "sweet onion"]), rng, 1, 1, "diced"),
            ing("clove", "garlic", rng, prep="minced")]
    if rng.random() < 0.6:
        arom.append(ing("count", rng.choice(["carrots", "celery stalks"]), rng, 1, 3, "diced"))
    mains_pool = ["white beans", "diced potatoes", "kidney beans", "barley",
                  "chopped kale", "sweet potatoes", "elbow macaroni", "rice",
                  "diced tomatoes", "chicken breast", "red lentils", "ground beef"]
    main_item = SOUP_MAIN.get(base) or rng.choice(mains_pool)
    main = ing("cup", main_item, rng, 0.75, 2)
    main2 = ing("cup", rng.choice(mains_pool), rng, 0.5, 1.5) if hearty and rng.random() < 0.7 else None
    liq = ing("cup", rng.choice(["chicken broth", "vegetable broth", "beef broth"]), rng, 4, 4)
    seas = [ing("tsp", "salt", rng), ing("tsp", "black pepper", rng)]
    extra = rng.choice(["bay leaf", "dried thyme", "ground cumin", "smoked paprika", "dried oregano", "curry powder"])
    seas.append(ing("tsp", extra, rng))
    garn = ing("tbsp", rng.choice(["chopped parsley", "sour cream", "grated Parmesan", "croutons", "cilantro"]), rng, hi=4)
    ings = [fat] + arom + [main] + ([main2] if main2 else []) + [liq] + seas + [garn]
    sim = rng.choice([20, 25, 30, 35, 40])
    steps = [
        "Heat the %s in a large pot over medium heat. Add the %s and cook, stirring often, until softened, about 5 minutes." % (fmt_ing(fat), ", ".join(i["item"] for i in arom)),
        "Pour in the %s and add the %s. Bring to a boil over high heat." % (fmt_ing(liq), fmt_ing(main) + (", " + fmt_ing(main2) if main2 else "")),
        "Reduce the heat to low, cover partially, and simmer %d minutes, until everything is tender." % sim,
        "Remove any bay leaf. Season with the %s, tasting and adjusting as you go." % (", ".join(fmt_ing(s) for s in seas)),
        "Ladle into warm bowls, top with %s, and serve hot." % fmt_ing(garn),
    ]
    return ings, steps, 15, sim + 10

def m_salad(rng, base=None, hearty=False):
    green = ing("cup", rng.choice(["chopped romaine", "baby spinach", "arugula", "mixed greens", "chopped kale"]), rng, 4, 4)
    adds = []
    for _ in range(rng.randint(2, 4)):
        adds.append(ing("cup", rng.choice(["cherry tomatoes", "diced cucumber", "sliced avocado", "shredded carrots",
            "crumbled feta", "chopped walnuts", "sliced red onion", "diced bell pepper",
            "chickpeas", "sliced strawberries", "blue cheese", "sunflower seeds"]), rng, 0.25, 1))
    if hearty:
        adds.append(ing("cup", rng.choice(["diced grilled chicken", "flaked tuna", "chopped hard-boiled egg", "cooked quinoa"]), rng, 0.75, 1.5))
    oil = ing("tbsp", "olive oil", rng, hi=4)
    acid = ing("tbsp", rng.choice(["lemon juice", "red wine vinegar", "balsamic vinegar", "apple cider vinegar"]), rng, hi=3)
    seas = [ing("tsp", "Dijon mustard", rng), ing("tsp", "honey", rng), ing("tsp", "salt", rng)]
    ings = [green] + adds + [oil, acid] + seas
    steps = [
        "Wash and dry the %s and place in a large salad bowl." % fmt_ing(green),
        "Add the %s." % (", ".join(fmt_ing(a) for a in adds)),
        "In a small jar, shake together the %s, %s, and %s until emulsified." % (fmt_ing(oil), fmt_ing(acid), ", ".join(fmt_ing(s) for s in seas)),
        "Pour the dressing over the salad and toss gently until everything is lightly coated. Serve right away.",
    ]
    return ings, steps, 15, 0

def m_dip(rng, base=None):
    base = ing("cup", DIP_BASE.get(base) or rng.choice(["sour cream", "Greek yogurt", "cream cheese, softened", "mashed chickpeas", "mashed avocado", "ricotta cheese"]), rng, 1, 2)
    mix = [ing("cup", rng.choice(["shredded cheddar", "chopped spinach", "diced tomatoes", "sliced black olives",
        "chopped artichoke hearts", "crumbled bacon", "diced jalapeños", "chopped green onions"]), rng, 0.25, 0.75) for _ in range(2)]
    seas = [ing("tsp", "garlic powder", rng), ing("tsp", "salt", rng)]
    if rng.random() < 0.5:
        seas.append(ing("tbsp", rng.choice(["lemon juice", "hot sauce"]), rng, hi=2))
    dipper = ing("count", rng.choice(["tortilla chip", "pita wedge", "cracker", "celery stick"]), rng, 8, 24, "for serving")
    ings = [base] + mix + seas + [dipper]
    steps = [
        "In a medium bowl, combine the %s with the %s." % (fmt_ing(base), ", ".join(fmt_ing(m) for m in mix)),
        "Stir in the %s until well blended. Taste and adjust seasoning." % (", ".join(fmt_ing(s) for s in seas)),
        "Cover and refrigerate at least 30 minutes so the flavors meld.",
        "Serve chilled with %s." % fmt_ing(dipper),
    ]
    return ings, steps, 10, 0

def m_fingerfood(rng, base=None):
    base = ing("count", rng.choice(["mushroom caps", "wonton wrappers", "mini bell peppers", "chicken wings", "potato halves"]), rng, 8, 24)
    fill = ing("cup", rng.choice(["cream cheese filling", "seasoned ground meat", "crab mixture", "cheese and herb mixture"]), rng, 0.75, 1.5)
    seas = [ing("tsp", "salt", rng), ing("tsp", rng.choice(["paprika", "garlic powder", "Italian seasoning"]), rng)]
    oil = ing("tbsp", "olive oil", rng, hi=2)
    ings = [base, fill, oil] + seas
    temp = rng.choice([375, 400, 425])
    t = rng.choice([12, 15, 18, 20])
    steps = [
        "Heat the oven to %d°F. Line a baking sheet with parchment." % temp,
        "Arrange the %s on the sheet and brush lightly with %s." % (fmt_ing(base), fmt_ing(oil)),
        "Spoon the %s into each, then sprinkle with %s." % (fmt_ing(fill), ", ".join(fmt_ing(s) for s in seas)),
        "Bake %d minutes, until golden and cooked through. Cool 5 minutes and serve warm." % t,
    ]
    return ings, steps, 20, t

def m_skewer(rng, base=None):
    prot = ing("lb", rng.choice(["chicken breast", "beef sirloin", "shrimp, peeled", "pork tenderloin"]), rng)
    veg = ing("cup", rng.choice(["bell pepper chunks", "zucchini rounds", "cherry tomatoes", "red onion wedges", "pineapple chunks"]), rng, 1, 2)
    marin = [ing("tbsp", "soy sauce", rng, hi=3), ing("tbsp", "olive oil", rng, hi=2), ing("tsp", "honey", rng)]
    ings = [prot, veg] + marin
    t = rng.choice([8, 10, 12])
    steps = [
        "Cut the %s into 1-inch pieces. Thread onto skewers, alternating with the %s." % (fmt_ing(prot), fmt_ing(veg)),
        "Whisk together the %s and brush over the skewers. Marinate 15 minutes." % (", ".join(fmt_ing(m) for m in marin)),
        "Grill over medium-high heat, turning, %d minutes until cooked through and lightly charred." % t,
        "Rest 5 minutes and serve hot.",
    ]
    return ings, steps, 25, t

def m_roastmain(rng, base=None):
    prot = ing("lb", rng.choice(["chicken thighs", "whole chicken", "pork chops", "beef chuck roast", "chicken breast", "pork tenderloin"]), rng)
    oil = ing("tbsp", "olive oil", rng, hi=3)
    seas = [ing("tsp", "salt", rng), ing("tsp", "black pepper", rng),
            ing("tsp", rng.choice(["garlic powder", "paprika", "dried rosemary", "Italian seasoning", "cumin"]), rng)]
    veg = ing("cup", rng.choice(["baby potatoes", "carrots", "Brussels sprouts", "green beans"]), rng, 1, 3) if rng.random() < 0.7 else None
    ings = [prot, oil] + seas + ([veg] if veg else [])
    temp = rng.choice([375, 400, 425])
    t = rng.choice([35, 45, 60, 75, 90])
    steps = [
        "Heat the oven to %d°F. Pat the %s dry with paper towels." % (temp, fmt_ing(prot)),
        "Rub all over with %s and season generously with %s." % (fmt_ing(oil), ", ".join(fmt_ing(s) for s in seas)),
        ("Scatter the %s around the pan. " % fmt_ing(veg) if veg else "") + "Roast %d minutes, until cooked through and the juices run clear." % t,
        "Rest 10 minutes before slicing so the juices settle. Serve warm.",
    ]
    return ings, steps, 15, t

def m_pasta(rng, base=None):
    asian = base in ("Pad Thai", "Lo Mein")
    shape = PASTA_SHAPE.get(base) or rng.choice(["spaghetti", "penne", "fettuccine", "rigatoni", "linguine"])
    pasta = ing("oz", shape, rng)
    prot = ing("cup", rng.choice(["ground beef", "Italian sausage", "diced chicken", "shrimp", "white beans", "mushrooms"]), rng, 0.75, 1.5) if rng.random() < 0.8 else None
    sauce = ing("cup", rng.choice(PASTA_SAUCE_ASIAN if asian else ["marinara sauce", "crushed tomatoes", "Alfredo sauce", "pesto"]), rng, 1.5, 2.5)
    arom = [ing("tbsp", "sesame oil" if asian else "olive oil", rng, hi=2), ing("clove", "garlic", rng, prep="minced")]
    cheese = None if asian else ing("cup", rng.choice(["grated Parmesan", "shredded mozzarella", "ricotta"]), rng, 0.25, 0.75)
    ings = [pasta] + ([prot] if prot else []) + [sauce] + arom + ([cheese] if cheese else [])
    steps = [
        "Bring a large pot of salted water to a boil. Cook the %s until al dente; reserve 1/2 cup pasta water, then drain." % fmt_ing(pasta),
        "Meanwhile, heat the %s in a large skillet over medium heat. Add the %s and cook 1 minute." % (fmt_ing(arom[0]), fmt_ing(arom[1])) +
        ((" Add the %s and cook until browned, breaking it up." % fmt_ing(prot)) if prot else ""),
        "Stir in the %s and simmer 8 minutes, loosening with pasta water as needed." % fmt_ing(sauce),
        ("Toss the pasta with the sauce, top with %s, and serve immediately." % fmt_ing(cheese)) if cheese else "Toss the noodles with the sauce and serve immediately.",
    ]
    return ings, steps, 10, 20

def m_stirfry(rng, base=None):
    prot = ing("lb", rng.choice(["chicken breast", "flank steak", "shrimp", "tofu", "pork loin"]), rng)
    vegs = [ing("cup", rng.choice(["broccoli florets", "sliced bell peppers", "snap peas", "sliced carrots", "baby corn", "mushrooms"]), rng, 0.75, 1.5) for _ in range(2)]
    sauce = [ing("tbsp", "soy sauce", rng, hi=3), ing("tbsp", rng.choice(["oyster sauce", "hoisin sauce", "teriyaki sauce"]), rng, hi=2),
             ing("tsp", "sesame oil", rng), ing("tsp", "cornstarch", rng)]
    oil = ing("tbsp", "vegetable oil", rng, hi=3)
    rice = ing("cup", "cooked rice", rng, 2, 4, "for serving")
    ings = [prot] + vegs + sauce + [oil, rice]
    steps = [
        "Slice the %s thinly against the grain. Have all ingredients ready by the stove — stir-fry moves fast." % fmt_ing(prot),
        "Heat the %s in a wok or large skillet over high heat until shimmering." % fmt_ing(oil),
        "Add the protein in a single layer and sear 2–3 minutes until browned; remove to a plate.",
        "Add the %s and stir-fry 3–4 minutes until crisp-tender." % (", ".join(fmt_ing(v) for v in vegs)),
        "Return the protein, pour over the %s, and toss 1–2 minutes until the sauce thickens and coats everything." % (", ".join(fmt_ing(s) for s in sauce)),
        "Serve hot over %s." % fmt_ing(rice),
    ]
    return ings, steps, 20, 10

def m_fish(rng, base=None):
    fish = ing("lb", rng.choice(["salmon fillets", "tilapia fillets", "cod fillets", "shrimp, peeled", "halibut fillets"]), rng)
    seas = [ing("tsp", "salt", rng), ing("tsp", "black pepper", rng), ing("tsp", rng.choice(["paprika", "garlic powder", "lemon pepper"]), rng)]
    fat = ing("tbsp", rng.choice(["butter", "olive oil"]), rng, hi=3)
    lemon = ing("count", "lemon", rng, 1, 1, "cut into wedges")
    herb = ing("tbsp", rng.choice(["chopped dill", "chopped parsley", "chopped cilantro"]), rng, hi=2)
    ings = [fish] + seas + [fat, lemon, herb]
    t = rng.choice([10, 12, 15])
    steps = [
        "Pat the %s dry and season both sides with %s." % (fmt_ing(fish), ", ".join(fmt_ing(s) for s in seas)),
        "Heat the %s in a large skillet over medium-high heat." % fmt_ing(fat),
        "Cook the fish %d minutes, turning once, until opaque and flakes easily." % t,
        "Squeeze %s over the top, sprinkle with %s, and serve at once." % (fmt_ing(lemon), fmt_ing(herb)),
    ]
    return ings, steps, 10, t

def m_vegside(rng, base=None):
    veg = ing("lb", rng.choice(["broccoli florets", "Brussels sprouts", "carrots", "green beans", "asparagus", "cauliflower"]), rng)
    oil = ing("tbsp", "olive oil", rng, hi=3)
    seas = [ing("tsp", "salt", rng), ing("tsp", "black pepper", rng)]
    if rng.random() < 0.5:
        seas.append(ing("tbsp", rng.choice(["balsamic vinegar", "lemon juice", "soy sauce"]), rng, hi=2))
    top = ing("tbsp", rng.choice(["grated Parmesan", "toasted almonds", "sesame seeds"]), rng, hi=3) if rng.random() < 0.6 else None
    ings = [veg, oil] + seas + ([top] if top else [])
    temp = rng.choice([400, 425])
    t = rng.choice([18, 20, 25])
    steps = [
        "Heat the oven to %d°F. Line a baking sheet with parchment." % temp,
        "Toss the %s with %s and %s until evenly coated." % (fmt_ing(veg), fmt_ing(oil), ", ".join(fmt_ing(s) for s in seas)),
        "Spread in a single layer and roast %d minutes, turning once, until tender and browned at the edges." % t,
        (("Sprinkle with %s and serve warm right away." % fmt_ing(top)) if top else "Transfer to a serving dish and serve warm right away."),
    ]
    return ings, steps, 10, t

def m_potato(rng, base=None, style=None):
    style = style or rng.choice(["mashed", "roasted"])
    if style == "mashed":
        pot = ing("lb", "russet potatoes", rng)
        dairy = [ing("tbsp", "butter", rng, hi=4), ing("cup", "warm milk", rng, 0.25, 0.75)]
        seas = [ing("tsp", "salt", rng), ing("tsp", "black pepper", rng)]
        ings = [pot] + dairy + seas
        steps = [
            "Peel and quarter the %s. Cover with cold salted water in a large pot." % fmt_ing(pot),
            "Bring to a boil, then simmer 15–18 minutes until very tender when pierced.",
            "Drain well and return to the hot pot for 1 minute to steam dry.",
            "Mash with the %s, then beat in the %s until smooth. Season with %s and serve hot." % (fmt_ing(dairy[0]), fmt_ing(dairy[1]), ", ".join(fmt_ing(s) for s in seas)),
        ]
        return ings, steps, 15, 20
    pot = ing("lb", rng.choice(["baby potatoes", "russet potatoes"]), rng)
    oil = ing("tbsp", "olive oil", rng, hi=3)
    seas = [ing("tsp", "salt", rng), ing("tsp", rng.choice(["rosemary", "garlic powder", "paprika"]), rng)]
    ings = [pot, oil] + seas
    steps = [
        "Heat the oven to 425°F. Cut the %s into even chunks." % fmt_ing(pot),
        "Toss with %s and %s on a baking sheet." % (fmt_ing(oil), ", ".join(fmt_ing(s) for s in seas)),
        "Roast 30–35 minutes, turning once, until crisp and golden. Serve hot.",
    ]
    return ings, steps, 10, 35

def m_grain(rng, base=None):
    grain = ing("cup", rng.choice(["long-grain rice", "basmati rice", "quinoa", "couscous", "wild rice blend"]), rng, 1, 2)
    liq = ing("cup", rng.choice(["water", "chicken broth", "vegetable broth"]), rng, 2, 2)
    arom = [ing("tbsp", "butter", rng, hi=2), ing("count", "shallot", rng, 1, 1, "minced")]
    seas = [ing("tsp", "salt", rng)]
    herb = ing("tbsp", rng.choice(["chopped parsley", "sliced green onions"]), rng, hi=2) if rng.random() < 0.6 else None
    ings = [grain, liq] + arom + seas + ([herb] if herb else [])
    t = rng.choice([15, 18, 20])
    steps = [
        "Melt the %s in a saucepan over medium heat. Add the %s and cook 2 minutes." % (fmt_ing(arom[0]), fmt_ing(arom[1])),
        "Stir in the %s to coat, then add the %s and %s. Bring to a boil." % (fmt_ing(grain), fmt_ing(liq), fmt_ing(seas[0])),
        "Cover, reduce to low, and cook %d minutes without lifting the lid." % t,
        "Remove from heat, rest 5 minutes, then fluff with a fork." + ((" Stir in %s." % fmt_ing(herb)) if herb else " Serve warm."),
    ]
    return ings, steps, 5, t + 5

def m_quickbread(rng, base=None):
    flour = ing("cup", "all-purpose flour", rng, 1.5, 2)
    leav = [{"qty": rng.choice(["1/2", "1"]), "unit": "teaspoon", "item": "baking soda"}, ing("tsp", "salt", rng)]
    wet = [ing("cup", "sugar", rng, 0.5, 1), ing("count", "eggs", rng, 2, 3),
           ing("cup", rng.choice(["mashed ripe bananas", "melted butter", "vegetable oil", "pumpkin puree"]), rng, 0.5, 1.5)]
    mixin = ing("cup", rng.choice(["chopped walnuts", "chocolate chips", "blueberries", "shredded zucchini"]), rng, 0.5, 1) if rng.random() < 0.7 else None
    ings = [flour] + leav + wet + ([mixin] if mixin else [])
    temp = 350
    t = rng.choice([50, 55, 60])
    steps = [
        "Heat the oven to %d°F. Grease a 9x5-inch loaf pan." % temp,
        "Whisk together the %s, %s, and %s in a large bowl." % (fmt_ing(flour), fmt_ing(leav[0]), fmt_ing(leav[1])),
        "In another bowl, whisk the %s until smooth." % (", ".join(fmt_ing(w) for w in wet)),
        "Pour wet into dry and stir just until combined — a few lumps are fine." + ((" Fold in the %s." % fmt_ing(mixin)) if mixin else ""),
        "Bake %d minutes, until a toothpick in the center comes out clean. Cool 10 minutes, then turn out." % t,
    ]
    return ings, steps, 15, t

def m_yeastbread(rng, base=None):
    flour = ing("cup", "bread flour", rng, 3, 4)
    yeast = {"qty": "2", "unit": "teaspoons", "item": "active dry yeast"}
    liq = ing("cup", "warm water", rng, 1, 1.5)
    other = [ing("tbsp", "sugar", rng, hi=2), {"qty": "1 1/2", "unit": "teaspoons", "item": "salt"}, ing("tbsp", "olive oil", rng, hi=3)]
    ings = [flour, yeast, liq] + other
    temp = rng.choice([375, 400])
    t = rng.choice([20, 25, 30])
    steps = [
        "Stir the %s and %s into the %s; let stand 5–10 minutes until foamy." % (fmt_ing(yeast), fmt_ing(other[0]), fmt_ing(liq)),
        "Add the %s, %s, and %s. Knead 8–10 minutes until smooth and elastic." % (fmt_ing(flour), fmt_ing(other[1]), fmt_ing(other[2])),
        "Cover and rise in a warm spot about 1 hour, until doubled.",
        "Punch down, shape as desired, and rise 30 minutes more.",
        "Bake at %d°F for %d minutes until deep golden and hollow-sounding when tapped. Cool on a rack." % (temp, t),
    ]
    return ings, steps, 30, t + 90

def m_flatbread(rng, base=None):
    flour = ing("cup", "all-purpose flour", rng, 1.5, 2)
    liq = ing("cup", rng.choice(["warm water", "plain yogurt"]), rng, 0.5, 0.75)
    fat = ing("tbsp", rng.choice(["olive oil", "melted butter"]), rng, hi=3)
    seas = [ing("tsp", "salt", rng)]
    top = ing("tbsp", rng.choice(["minced garlic", "chopped herbs", "sesame seeds"]), rng, hi=2) if rng.random() < 0.7 else None
    ings = [flour, liq, fat] + seas + ([top] if top else [])
    t = rng.choice([2, 3])
    steps = [
        "Mix the %s, %s, %s, and %s into a soft dough; knead 3 minutes and rest 15." % (fmt_ing(flour), fmt_ing(liq), fmt_ing(fat), fmt_ing(seas[0])),
        "Divide into 6 balls and roll each thin.",
        "Cook in a hot dry skillet %d minutes per side until puffed and spotted." % t,
        (("Brush with butter, sprinkle %s, and serve warm." % fmt_ing(top)) if top else "Wrap in a clean towel and serve warm."),
    ]
    return ings, steps, 25, 12

def m_cookie(rng, base=None):
    butter = ing("cup", "butter, softened", rng, 0.5, 1)
    sugar = [ing("cup", "brown sugar", rng, 0.5, 1), ing("cup", "granulated sugar", rng, 0.25, 0.5)]
    egg = [ing("count", "eggs", rng, 1, 2), ing("tsp", "vanilla extract", rng)]
    dry = [ing("cup", "all-purpose flour", rng, 1.5, 2.5), {"qty": "1", "unit": "teaspoon", "item": "baking soda"}, ing("tsp", "salt", rng)]
    chip = ing("cup", rng.choice(["chocolate chips", "chopped walnuts", "oats", "raisins", "white chocolate chips"]), rng, 0.75, 1.5)
    ings = [butter] + sugar + egg + dry + [chip]
    temp = 350
    t = rng.choice([10, 11, 12])
    steps = [
        "Heat the oven to %d°F. Line baking sheets with parchment." % temp,
        "Beat the %s with the %s until creamy, about 2 minutes." % (fmt_ing(butter), " and ".join(fmt_ing(s) for s in sugar)),
        "Beat in the %s." % (", ".join(fmt_ing(e) for e in egg)),
        "Stir in the %s just until combined, then fold in the %s." % (", ".join(fmt_ing(d) for d in dry), fmt_ing(chip)),
        "Scoop rounded tablespoons 2 inches apart. Bake %d minutes until edges are golden. Cool on the sheet 5 minutes." % t,
    ]
    return ings, steps, 15, t

def m_cake(rng, base=None):
    flour = ing("cup", "all-purpose flour", rng, 1.5, 2.5)
    sugar = ing("cup", "granulated sugar", rng, 1, 1.5)
    _bp = rng.choice(["1", "2"])
    leav = [{"qty": _bp, "unit": "teaspoon" if _bp == "1" else "teaspoons", "item": "baking powder"}, ing("tsp", "salt", rng)]
    wet = [ing("count", "eggs", rng, 2, 3), ing("cup", "milk", rng, 0.75, 1), ing("cup", "vegetable oil", rng, 0.5, 0.75), ing("tsp", "vanilla extract", rng)]
    flavor = ing("cup", rng.choice(["cocoa powder", "lemon zest", "shredded coconut", "mashed banana"]), rng, 0.25, 0.5) if rng.random() < 0.6 else None
    ings = [flour, sugar] + leav + wet + ([flavor] if flavor else [])
    temp = 350
    t = rng.choice([28, 30, 35])
    steps = [
        "Heat the oven to %d°F. Grease and flour two 8-inch round pans." % temp,
        "Whisk the %s, %s, %s, and %s in a large bowl." % (fmt_ing(flour), fmt_ing(sugar), fmt_ing(leav[0]), fmt_ing(leav[1])),
        "Add the %s and beat 2 minutes until smooth." % (", ".join(fmt_ing(w) for w in wet)) + ((" Fold in the %s." % fmt_ing(flavor)) if flavor else ""),
        "Divide between pans and bake %d minutes, until a toothpick comes out clean." % t,
        "Cool 10 minutes in pans, then turn out and cool completely before frosting.",
    ]
    return ings, steps, 20, t

def m_pie(rng, base=None):
    crust = ing("count", "pie crust", rng, 1, 2, "store-bought or homemade")
    fill_base = rng.choice(["sliced apples", "pumpkin puree", "pecan halves", "cherry pie filling", "lemon curd"])
    fill = ing("cup", fill_base, rng, 3, 6) if "puree" not in fill_base and "filling" not in fill_base and "curd" not in fill_base else ing("cup", fill_base, rng, 1.5, 3)
    sweet = ing("cup", "sugar", rng, 0.5, 1)
    spice = ing("tsp", rng.choice(["cinnamon", "pumpkin pie spice", "nutmeg"]), rng)
    egg = ing("count", "eggs", rng, 1, 3) if rng.random() < 0.5 else None
    ings = [crust, fill, sweet, spice] + ([egg] if egg else [])
    temp = rng.choice([375, 400])
    t = rng.choice([40, 45, 50])
    steps = [
        "Heat the oven to %d°F. Fit the %s into a 9-inch pie plate." % (temp, fmt_ing(crust)),
        "Toss the %s with the %s and %s%s." % (fmt_ing(fill), fmt_ing(sweet), fmt_ing(spice), (", then beat in the %s" % fmt_ing(egg)) if egg else ""),
        "Pour into the crust and smooth the top.",
        "Bake %d minutes until the filling is set and the crust is golden. Cool at least 2 hours before slicing." % t,
    ]
    return ings, steps, 25, t

def m_pudding(rng, base=None):
    base = ing("cup", rng.choice(["milk", "heavy cream", "coconut milk"]), rng, 1.5, 2)
    choc = ing("cup", rng.choice(["chocolate chips", "sugar", "cooked rice"]), rng, 0.5, 1)
    egg = [ing("count", "egg yolks", rng, 2, 4), ing("tsp", "vanilla extract", rng)]
    ings = [base, choc] + egg
    steps = [
        "Heat the %s in a saucepan until steaming (not boiling)." % fmt_ing(base),
        "Whisk the %s with the %s in a bowl, then slowly whisk in the hot liquid." % (fmt_ing(egg[0]), fmt_ing(choc)),
        "Return to the pan and cook over medium-low, stirring constantly, until thick enough to coat a spoon, about 8 minutes.",
        "Stir in the %s, pour into cups, and chill at least 2 hours. Serve cold." % fmt_ing(egg[1]),
    ]
    return ings, steps, 10, 10

def m_smoothie(rng, base=None):
    fruit = [ing("cup", rng.choice(["frozen berries", "banana", "mango chunks", "peaches", "pineapple"]), rng, 0.75, 1.5) for _ in range(2)]
    liq = ing("cup", rng.choice(["milk", "orange juice", "almond milk", "yogurt"]), rng, 0.75, 1.25)
    extra = ing("tbsp", rng.choice(["honey", "peanut butter", "chia seeds"]), rng, hi=2) if rng.random() < 0.6 else None
    ice = ing("cup", "ice cubes", rng, 0.5, 1)
    ings = fruit + [liq] + ([extra] if extra else []) + [ice]
    steps = [
        "Add the %s, %s%s, and %s to a blender." % (fmt_ing(fruit[0]), fmt_ing(fruit[1]), (", " + fmt_ing(extra)) if extra else "", fmt_ing(liq)),
        "Add the %s." % fmt_ing(ice),
        "Blend on high 45–60 seconds until completely smooth, tamping down as needed.",
        "Pour into glasses and serve immediately.",
    ]
    return ings, steps, 5, 0

def m_cooler(rng, base=None):
    base = ing("cup", rng.choice(["fresh lemon juice", "brewed black tea, cooled", "fruit juice", "cucumber slices"]), rng, 0.75, 2)
    sweet = ing("cup", "sugar", rng, 0.25, 0.75)
    water = ing("cup", "cold water", rng, 3, 4)
    garn = ing("count", rng.choice(["lemon slice", "mint sprig", "orange wheel"]), rng, 2, 6, "for serving")
    ings = [base, sweet, water, garn]
    steps = [
        "Stir the %s and %s in a pitcher until the sugar dissolves." % (fmt_ing(base), fmt_ing(sweet)),
        "Add the %s and stir well. Refrigerate at least 1 hour.",
        "Serve over ice, garnished with %s." % fmt_ing(garn),
    ]
    return ings, steps, 10, 0

def m_hotdrink(rng, base=None):
    liq = ing("cup", "milk", rng, 2, 2)
    flav = ing("tbsp", rng.choice(["cocoa powder", "chai spice mix", "instant coffee"]), rng, hi=3)
    sweet = ing("tbsp", "sugar", rng, hi=3)
    top = ing("tbsp", rng.choice(["whipped cream", "marshmallows", "cinnamon"]), rng, hi=2) if rng.random() < 0.7 else None
    ings = [liq, flav, sweet] + ([top] if top else [])
    steps = [
        "Heat the %s in a saucepan over medium heat until steaming." % fmt_ing(liq),
        "Whisk in the %s and %s until smooth and dissolved." % (fmt_ing(flav), fmt_ing(sweet)),
        "Pour into warm mugs." + ((" Top with %s and serve immediately." % fmt_ing(top)) if top else " Serve immediately while hot."),
    ]
    return ings, steps, 5, 5

def m_egg(rng, base=None):
    egg = ing("count", "eggs", rng, 2, 6)
    dairy = ing("tbsp", rng.choice(["butter", "milk", "cream"]), rng, hi=3)
    fill = ing("cup", rng.choice(["shredded cheddar", "diced ham", "sautéed mushrooms", "spinach", "diced bell pepper"]), rng, 0.25, 0.75) if rng.random() < 0.7 else None
    seas = [ing("tsp", "salt", rng), ing("tsp", "black pepper", rng)]
    ings = [egg, dairy] + ([fill] if fill else []) + seas
    steps = [
        "Crack the %s into a bowl, add %s, and beat until uniform." % (fmt_ing(egg), ", ".join(fmt_ing(s) for s in seas)),
        "Melt the %s in a nonstick skillet over medium-low heat." % fmt_ing(dairy),
        "Pour in the eggs and cook gently, pushing with a spatula, until just set but still creamy, 3–4 minutes." + ((" Sprinkle %s over the top." % fmt_ing(fill)) if fill else ""),
        "Serve immediately, while hot and soft.",
    ]
    return ings, steps, 5, 5

def m_pancake(rng, base=None):
    dry = [ing("cup", "all-purpose flour", rng, 1, 1.5), ing("tbsp", "sugar", rng, hi=2), ing("tsp", "baking powder", rng), ing("tsp", "salt", rng)]
    wet = [ing("cup", "milk", rng, 0.75, 1.25), ing("count", "egg", rng, 1, 1), ing("tbsp", "melted butter", rng, hi=3)]
    ings = dry + wet
    steps = [
        "Whisk the %s in a large bowl." % (", ".join(fmt_ing(d) for d in dry)),
        "Whisk the %s in another bowl, then pour into the dry mix and stir just until combined." % (", ".join(fmt_ing(w) for w in wet)),
        "Heat a buttered griddle over medium heat. Pour 1/4-cup batter per pancake.",
        "Cook until bubbles pop on the surface, about 2 minutes, then flip and cook 1–2 minutes more. Serve warm with syrup.",
    ]
    return ings, steps, 10, 15

def m_oatmeal(rng, base=None):
    oat = ing("cup", rng.choice(["rolled oats", "steel-cut oats"]), rng, 0.75, 1)
    liq = ing("cup", rng.choice(["milk", "water"]), rng, 1.5, 2)
    sweet = ing("tbsp", rng.choice(["brown sugar", "honey", "maple syrup"]), rng, hi=2)
    top = ing("cup", rng.choice(["sliced bananas", "berries", "chopped apples", "raisins"]), rng, 0.25, 0.5)
    ings = [oat, liq, sweet, top]
    steps = [
        "Bring the %s to a boil in a saucepan." % fmt_ing(liq),
        "Stir in the %s, reduce heat, and simmer 5–7 minutes, stirring, until creamy.",
        "Stir in the %s, spoon into bowls, and top with %s." % (fmt_ing(sweet), fmt_ing(top)),
    ]
    return ings, steps, 3, 7

def m_snack(rng, base=None, sweet=False):
    if sweet:
        base = ing("cup", rng.choice(["granola", "mixed dried fruit", "yogurt-covered raisins"]), rng, 1, 2)
        add = ing("cup", rng.choice(["chocolate chips", "mini marshmallows", "coconut flakes"]), rng, 0.25, 0.75)
        bind = ing("tbsp", rng.choice(["honey", "peanut butter", "maple syrup"]), rng, hi=3)
        ings = [base, add, bind]
        steps = [
            "Combine the %s, %s, and %s in a large bowl and toss until evenly mixed and lightly coated." % (fmt_ing(base), fmt_ing(add), fmt_ing(bind)),
            "For extra crunch, spread on a lined baking sheet and bake at 300°F for 12 minutes, stirring once; cool completely.",
            "Portion into small bags or a jar. Keeps 2 weeks airtight.",
        ]
        return ings, steps, 5, 12
    base = ing("cup", rng.choice(["popcorn", "mixed nuts", "pretzels", "roasted chickpeas"]), rng, 4, 8)
    seas = [ing("tbsp", "olive oil", rng, hi=2), ing("tsp", "salt", rng), ing("tsp", rng.choice(["paprika", "garlic powder", "ranch seasoning"]), rng)]
    ings = [base] + seas
    steps = [
        "Place the %s in a large bowl." % fmt_ing(base),
        "Drizzle with %s and sprinkle %s; toss well to coat." % (fmt_ing(seas[0]), ", ".join(fmt_ing(s) for s in seas[1:])),
        "Serve right away, or store airtight up to 3 days.",
    ]
    return ings, steps, 5, 0

# ---------------- chapters, sections, dish pools ----------------
# (chapter, emoji, [(section, method_key, [base dish names])])
CHAPTERS = [
 ("Appetizers", "🥗", [
   ("Dips & Spreads", "dip", ["Hummus","Guacamole","Spinach Artichoke Dip","Salsa","Bean Dip","Tzatziki","Pimento Cheese","Onion Dip","Baba Ganoush","Queso Dip","Crab Dip","White Bean Dip","Edamame Dip","Roasted Red Pepper Dip","Ranch Dip"]),
   ("Finger Foods", "fingerfood", ["Stuffed Mushrooms","Deviled Eggs","Bruschetta","Spring Rolls","Chicken Wings","Mozzarella Sticks","Pigs in a Blanket","Shrimp Cocktail","Potato Skins","Jalapeño Poppers","Meatballs","Crab Cakes","Dumplings","Samosas","Crostini"]),
   ("Skewers & Bites", "skewer", ["Caprese Skewers","Chicken Satay","Fruit Skewers","Antipasto Skewers","Teriyaki Skewers","Shrimp Skewers","Beef Skewers","Veggie Skewers"]),
 ]),
 ("Soups & Salads", "🍲", [
   ("Hearty Soups", "soup", ["Chicken Noodle Soup","Tomato Soup","Beef Stew","Clam Chowder","Lentil Soup","Minestrone","Potato Leek Soup","Chili","Corn Chowder","Split Pea Soup","Butternut Squash Soup","Chicken Tortilla Soup","Gumbo","Borscht","Ramen","Vegetable Soup"]),
   ("Light Soups", "soup_light", ["Miso Soup","Egg Drop Soup","Gazpacho","Cucumber Soup","Chicken Broth Soup","Tomato Basil Soup","Carrot Ginger Soup","Wonton Soup"]),
   ("Green Salads", "salad", ["Caesar Salad","Greek Salad","Garden Salad","Spinach Salad","Cobb Salad","Arugula Salad","Waldorf Salad","Chef Salad"]),
   ("Hearty Salads", "salad_hearty", ["Chicken Salad","Tuna Salad","Pasta Salad","Quinoa Salad","Taco Salad","Potato Salad","Coleslaw","Egg Salad"]),
 ]),
 ("Mains", "🍽️", [
   ("Chicken", "roastmain", ["Roast Chicken","Chicken Parmesan","Chicken Stir-Fry","Grilled Chicken","Chicken Tacos","Chicken Curry","Chicken Piccata","BBQ Chicken","Chicken Alfredo","Orange Chicken","Herb Roasted Chicken","Chicken Fajitas"]),
   ("Beef & Pork", "roastmain", ["Meatloaf","Beef Tacos","Pork Chops","Beef Stir-Fry","Pulled Pork","Steak","Beef Stew","Salisbury Steak","Pork Tenderloin","Beef Burritos","BBQ Pork Ribs","Swedish Meatballs"]),
   ("Fish & Seafood", "fish", ["Baked Salmon","Shrimp Scampi","Garlic Butter Tilapia","Grilled Tilapia","Blackened Salmon","Garlic Butter Shrimp","Baked Cod","Crab Cakes","Salmon Patties","Lemon Butter Fish"]),
   ("Pasta & Noodles", "pasta", ["Spaghetti Bolognese","Lasagna","Mac and Cheese","Fettuccine Alfredo","Pad Thai","Lo Mein","Baked Ziti","Pesto Pasta","Penne alla Vodka","Spaghetti Carbonara"]),
   ("Vegetarian", "vegmain", ["Rainbow Veggie Stir-Fry","Sesame Tofu Stir-Fry","Roasted Eggplant","Veggie Stir-Fry","Tofu Stir-Fry","Vegetable Lo Mein","Zucchini Stir-Fry","Chickpea Stir-Fry"]),
 ]),
 ("Sides", "🥔", [
   ("Roasted Vegetables", "vegside", ["Roasted Broccoli","Roasted Carrots","Grilled Asparagus","Sautéed Green Beans","Roasted Cauliflower","Honey Glazed Carrots","Garlic Green Beans","Roasted Brussels Sprouts"]),
   ("Potatoes", "potato", ["Mashed Potatoes","Roasted Potatoes","Baked Potatoes","Potato Salad","French Fries","Scalloped Potatoes","Sweet Potato Fries","Hash Browns"]),
   ("Grains & Rice", "grain", ["Rice Pilaf","Fried Rice","Quinoa","Couscous","Wild Rice","Spanish Rice","Risotto","Bulgur Wheat"]),
 ]),
 ("Breads", "🍞", [
   ("Quick Breads", "quickbread", ["Banana Bread","Cornbread","Zucchini Bread","Blueberry Muffins","Biscuits","Scones","Pumpkin Bread","Apple Bread"]),
   ("Yeast Breads", "yeastbread", ["Dinner Rolls","White Bread","Pizza Dough","Focaccia","Cinnamon Rolls","Whole Wheat Bread","Bagels","Pretzels"]),
   ("Flatbreads", "flatbread", ["Garlic Bread","Naan","Tortillas","Pita Bread","Flatbread Pizza","Chapati"]),
 ]),
 ("Desserts", "🍰", [
   ("Cakes", "cake", ["Vanilla Cake","Chocolate Cake","Carrot Cake","Lemon Cake","Pound Cake","Red Velvet Cake","Banana Cake","Spice Cake"]),
   ("Cookies", "cookie", ["Chocolate Chip Cookies","Oatmeal Cookies","Sugar Cookies","Peanut Butter Cookies","Brownies","Snickerdoodles","Gingerbread Cookies","Shortbread"]),
   ("Pies & Tarts", "pie", ["Apple Pie","Pumpkin Pie","Pecan Pie","Lemon Tart","Cherry Pie","Key Lime Pie","Blueberry Pie","Custard Tart"]),
   ("Puddings & Creams", "pudding", ["Chocolate Mousse","Rice Pudding","Bread Pudding","Panna Cotta","Vanilla Custard","Tapioca Pudding","Banana Pudding"]),
 ]),
 ("Drinks", "🥤", [
   ("Smoothies & Shakes", "smoothie", ["Berry Smoothie","Banana Smoothie","Mango Smoothie","Chocolate Shake","Strawberry Banana Smoothie","Green Smoothie","Peach Smoothie","Vanilla Shake"]),
   ("Coolers", "cooler", ["Lemonade","Iced Tea","Fruit Punch","Cucumber Cooler","Agua Fresca","Strawberry Lemonade","Mint Cooler","Orange Cooler"]),
   ("Hot Drinks", "hotdrink", ["Hot Chocolate","Spiced Cider","Chai Latte","Cinnamon Coffee","Warm Apple Cider","Mocha","Turmeric Latte"]),
 ]),
 ("Breakfast", "🍳", [
   ("Eggs", "egg", ["Scrambled Eggs","Cheese Omelet","Fried Eggs","Frittata","Veggie Omelet","Breakfast Burrito","Ham and Cheese Scramble","Western Omelet"]),
   ("Pancakes & More", "pancake", ["Pancakes","Waffles","Chocolate Chip Pancakes","Buttermilk Waffles","Blueberry Pancakes","Banana Pancakes","Dutch Baby"]),
   ("Warm Grains", "oatmeal", ["Oatmeal","Cream of Wheat","Grits","Granola Bowl","Overnight Oats","Cornmeal Mush"]),
 ]),
 ("Snacks", "🍿", [
   ("Savory Snacks", "snack_savory", ["Popcorn","Nachos","Trail Mix","Roasted Nuts","Roasted Chickpeas","Pretzel Mix","Cheese Straws","Potato Chips"]),
   ("Sweet Snacks", "snack_sweet", ["Granola Bars","Energy Bites","Fruit Leather","Yogurt Bark","Candied Nuts","Chocolate Trail Mix"]),
 ]),
]

METHODS = {
 "dip": lambda r, b, _m=m_dip: _m(r, b), "fingerfood": lambda r, b, _m=m_fingerfood: _m(r, b), "skewer": lambda r, b, _m=m_skewer: _m(r, b),
 "soup": lambda r, b: m_soup(r, b, True), "soup_light": lambda r, b: m_soup(r, False),
 "salad": lambda r, b: m_salad(r, b, False), "salad_hearty": lambda r, b: m_salad(r, b, True),
 "roastmain": lambda r, b, _m=m_roastmain: _m(r, b), "pasta": lambda r, b, _m=m_pasta: _m(r, b), "stirfry": lambda r, b, _m=m_stirfry: _m(r, b), "fish": lambda r, b, _m=m_fish: _m(r, b),
 "vegmain": lambda r, b: m_stirfry(r, b) if r.random() < 0.5 else m_vegside(r, b),
 "vegside": lambda r, b, _m=m_vegside: _m(r, b), "potato": lambda r, b, _m=m_potato: _m(r, b), "grain": lambda r, b, _m=m_grain: _m(r, b),
 "quickbread": lambda r, b, _m=m_quickbread: _m(r, b), "yeastbread": lambda r, b, _m=m_yeastbread: _m(r, b), "flatbread": lambda r, b, _m=m_flatbread: _m(r, b),
 "cake": lambda r, b, _m=m_cake: _m(r, b), "cookie": lambda r, b, _m=m_cookie: _m(r, b), "pie": lambda r, b, _m=m_pie: _m(r, b), "pudding": lambda r, b, _m=m_pudding: _m(r, b),
 "smoothie": lambda r, b, _m=m_smoothie: _m(r, b), "cooler": lambda r, b, _m=m_cooler: _m(r, b), "hotdrink": lambda r, b, _m=m_hotdrink: _m(r, b),
 "egg": lambda r, b, _m=m_egg: _m(r, b), "pancake": lambda r, b, _m=m_pancake: _m(r, b), "oatmeal": lambda r, b, _m=m_oatmeal: _m(r, b),
 "snack_savory": lambda r, b: m_snack(r, b, False), "snack_sweet": lambda r, b: m_snack(r, b, True),
}

# Classic dishes get the lowest IDs (original instructions, never copied text)
CLASSICS = [
 ("Appetizers","Dips & Spreads","Guacamole"),("Appetizers","Dips & Spreads","Classic Hummus"),
 ("Appetizers","Finger Foods","Deviled Eggs"),("Appetizers","Finger Foods","Bruschetta"),
 ("Soups & Salads","Hearty Soups","Chicken Noodle Soup"),("Soups & Salads","Hearty Soups","Tomato Soup"),
 ("Soups & Salads","Hearty Soups","Beef Stew"),("Soups & Salads","Green Salads","Caesar Salad"),
 ("Soups & Salads","Green Salads","Greek Salad"),("Mains","Chicken","Roast Chicken"),
 ("Mains","Chicken","Chicken Stir-Fry"),("Mains","Pasta & Noodles","Spaghetti Bolognese"),
 ("Mains","Pasta & Noodles","Lasagna"),("Mains","Fish & Seafood","Baked Salmon"),
 ("Mains","Beef & Pork","Meatloaf"),("Sides","Potatoes","Mashed Potatoes"),
 ("Sides","Roasted Vegetables","Roasted Broccoli"),("Sides","Grains & Rice","Rice Pilaf"),
 ("Breads","Quick Breads","Banana Bread"),("Breads","Flatbreads","Garlic Bread"),
 ("Breads","Yeast Breads","Dinner Rolls"),("Desserts","Cookies","Chocolate Chip Cookies"),
 ("Desserts","Cakes","Vanilla Cake"),("Desserts","Pies & Tarts","Apple Pie"),
 ("Desserts","Puddings & Creams","Chocolate Mousse"),("Drinks","Smoothies & Shakes","Berry Smoothie"),
 ("Drinks","Coolers","Lemonade"),("Drinks","Hot Drinks","Hot Chocolate"),
 ("Breakfast","Eggs","Scrambled Eggs"),("Breakfast","Pancakes & More","Pancakes"),
 ("Breakfast","Warm Grains","Oatmeal"),("Snacks","Savory Snacks","Popcorn"),
 ("Snacks","Sweet Snacks","Granola Bars"),("Mains","Vegetarian","Rainbow Veggie Stir-Fry"),
 ("Soups & Salads","Hearty Salads","Chicken Salad"),("Appetizers","Skewers & Bites","Chicken Satay"),
]

DIFFICULTY = ["Easy", "Easy", "Easy", "Medium", "Medium", "Hard"]

PASTA_SHAPE = {"Lasagna": "lasagna noodles", "Spaghetti Bolognese": "spaghetti",
 "Spaghetti Carbonara": "spaghetti", "Fettuccine Alfredo": "fettuccine",
 "Mac and Cheese": "elbow macaroni", "Pad Thai": "rice noodles", "Lo Mein": "lo mein noodles",
 "Baked Ziti": "ziti", "Pesto Pasta": "penne", "Penne alla Vodka": "penne"}
PASTA_SAUCE_ASIAN = ["pad thai sauce", "teriyaki sauce", "soy-ginger sauce"]
SOUP_MAIN = {"Clam Chowder": "chopped clams", "Chicken Noodle Soup": "diced chicken breast",
 "Chicken Tortilla Soup": "shredded chicken", "Tomato Soup": "diced tomatoes",
 "Tomato Basil Soup": "diced tomatoes", "Beef Stew": "beef stew meat",
 "Lentil Soup": "red lentils", "Minestrone": "kidney beans", "Potato Leek Soup": "diced potatoes",
 "Chili": "ground beef", "Corn Chowder": "corn kernels", "Split Pea Soup": "split peas",
 "Butternut Squash Soup": "cubed butternut squash", "Borscht": "shredded beets",
 "Ramen": "ramen noodles", "Miso Soup": "cubed tofu", "Egg Drop Soup": "beaten eggs",
 "Wonton Soup": "frozen wontons", "Carrot Ginger Soup": "sliced carrots",
 "Gazpacho": "diced tomatoes", "Cucumber Soup": "diced cucumber",
 "Chicken Broth Soup": "diced chicken breast", "Vegetable Soup": "mixed vegetables"}
SUFFIX_SWEET = ["", "", "", "", "Supreme", "Deluxe", "Special"]
SWEET_CHAPTERS = ("Desserts", "Drinks")
DIP_BASE = {"Guacamole": "mashed avocados", "Classic Hummus": "mashed chickpeas", "Hummus": "mashed chickpeas",
 "Baba Ganoush": "roasted eggplant", "Tzatziki": "Greek yogurt", "Salsa": "diced tomatoes",
 "Queso Dip": "shredded cheddar cheese", "Pimento Cheese": "shredded cheddar cheese",
 "Spinach Artichoke Dip": "cream cheese, softened", "Crab Dip": "lump crab meat",
 "Bean Dip": "refried beans", "White Bean Dip": "cannellini beans", "Edamame Dip": "shelled edamame",
 "Roasted Red Pepper Dip": "roasted red peppers", "Onion Dip": "sour cream", "Ranch Dip": "sour cream"}

# ---------------- QA ----------------
def qa_recipe(r):
    probs = []
    ings = r.get("ingredients", [])
    if len(ings) < 3:
        probs.append("fewer than 3 ingredients")
    for i in ings:
        if not i.get("qty") or not i.get("item"):
            probs.append("ingredient missing qty/item: %r" % (i,))
            break
    steps = r.get("steps", [])
    if len(steps) < 3:
        probs.append("fewer than 3 steps")
    for s in steps:
        if len(s) < 25:
            probs.append("step too short: %r" % s[:40]); break
        if "{" in s or "}" in s:
            probs.append("unfilled template placeholder"); break
    if not r.get("prep_min") and not r.get("cook_min"):
        if r.get("prep_min", 0) + r.get("cook_min", 0) <= 0:
            probs.append("no time")
    if not (1 <= r.get("servings", 0) <= 12):
        probs.append("bad servings")
    if r.get("difficulty") not in ("Easy", "Medium", "Hard"):
        probs.append("bad difficulty")
    # coherence: at least 2 ingredient keywords appear in steps
    blob = " ".join(steps).lower()
    hits = 0
    for i in ings:
        kw = i["item"].split()[0].lower().strip(",")
        if len(kw) > 3 and kw in blob:
            hits += 1
    if hits < 2:
        probs.append("steps do not reference ingredients (%d hits)" % hits)
    if not r.get("name") or len(r["name"]) < 4:
        probs.append("bad name")
    return probs

# ---------------- generation ----------------
def section_for(chapter, section):
    for ch, _, secs in CHAPTERS:
        if ch == chapter:
            for sname, mkey, dishes in secs:
                if sname == section:
                    return mkey, dishes
    raise ValueError("unknown section %s / %s" % (chapter, section))

def gen_recipe(index, used_names, classic=None):
    """Deterministic. classic=(chapter, section, name) for seeded classics."""
    for attempt in range(12):
        rng = random.Random(index * 7919 + attempt * 131 + 7)
        if classic:
            chapter, section, base = classic
            name = base
        else:
            ch = rng.choice(CHAPTERS)
            chapter, _, secs = ch
            sname, mkey, dishes = rng.choice(secs)
            section = sname
            base = rng.choice(dishes)
            name = dish_name(rng, base, used_names, sweet=(chapter in SWEET_CHAPTERS))
        mkey, _dishes = section_for(chapter, section)
        ings, steps, prep, cook = METHODS[mkey](rng, base)
        # servings + difficulty
        if mkey in ("dip", "snack_savory", "snack_sweet", "cooler", "smoothie"):
            servings = rng.choice([4, 6, 8])
        elif mkey in ("cake", "pie", "cookie", "quickbread", "yeastbread"):
            servings = rng.choice([8, 10, 12])
        else:
            servings = rng.choice([2, 4, 4, 6])
        difficulty = rng.choice(DIFFICULTY)
        r = {
            "id": "JAH-RECIPE-%06d" % index,
            "name": name, "chapter": chapter, "section": section,
            "ingredients": ings, "steps": steps,
            "prep_min": prep, "cook_min": cook,
            "total_min": prep + cook,
            "servings": servings, "difficulty": difficulty,
        }
        probs = qa_recipe(r)
        if not probs and name not in used_names:
            return r
    raise Runtimeur("could not generate coherent recipe", index)

class Runtimeur(Exception):
    pass

def load_state():
    if os.path.exists(STATE):
        return json.load(open(STATE))
    return {"next_index": 1}

def save_state(s):
    os.makedirs(DATA, exist_ok=True)
    json.dump(s, open(STATE, "w"))

def existing_names():
    names = set()
    idx_path = IDX
    if os.path.exists(idx_path):
        for row in json.load(open(idx_path)):
            names.add(row["name"])
    return names

def append_recipes(recipes):
    os.makedirs(CHUNKS, exist_ok=True)
    # group by chunk
    by_chunk = {}
    for r in recipes:
        n = int(r["id"].split("-")[-1])
        cn = (n - 1) // CHUNK_SIZE + 1
        by_chunk.setdefault(cn, []).append(r)
    for cn, rs in sorted(by_chunk.items()):
        path = os.path.join(CHUNKS, "rc-%05d.jsonl.gz" % cn)
        mode = "at" if os.path.exists(path) else "wt"
        with gzip.open(path, mode, encoding="utf-8") as f:
            for r in rs:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

def rebuild_index():
    os.makedirs(os.path.dirname(IDX), exist_ok=True)
    rows = []
    total = 0
    per_chapter = {}
    for fn in sorted(os.listdir(CHUNKS)):
        if not fn.endswith(".jsonl.gz"):
            continue
        cn = fn.split("-")[1].split(".")[0]
        with gzip.open(os.path.join(CHUNKS, fn), "rt", encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                rows.append({"id": r["id"], "n": r["name"], "c": r["chapter"],
                             "s": r["section"], "k": cn, "t": r["total_min"], "d": r["difficulty"]})
                per_chapter[r["chapter"]] = per_chapter.get(r["chapter"], 0) + 1
                total += 1
    rows.sort(key=lambda x: x["id"])
    json.dump(rows, open(IDX, "w"), ensure_ascii=False)
    json.dump({"total": total, "per_chapter": per_chapter,
               "goal": 1000000, "updated": "2026-10-05"},
              open(STATS, "w"), indent=1)
    return total

def generate_batch(n):
    st = load_state()
    used = existing_names()
    made = []
    idx = st["next_index"]
    classics = CLASSICS if idx == 1 else []
    for c in classics:
        r = gen_recipe(idx, used, classic=c)
        used.add(r["name"])
        made.append(r)
        idx += 1
    while len(made) < n:
        r = gen_recipe(idx, used)
        used.add(r["name"])
        made.append(r)
        idx += 1
    append_recipes(made)
    st["next_index"] = idx
    save_state(st)
    total = rebuild_index()
    return len(made), total

if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    made, total = generate_batch(n)
    print("RECIPES: +%d total=%d" % (made, total))
