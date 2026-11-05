"""Build the Spanish reading stories (spanish/stories/) from JSON sources in spanish-src/stories/.

Each story page reuses a German reading page (readings/01-wg-zimmer.html) as its template, so both
look and behave the same: word list, grammar notes, a text with hover translations, a quiz.
Called by tools/build_section.py after it builds spanish/; can also be run on its own.

Source format, one file per story: spanish-src/stories/NN-slug.json
{
  "n": 1, "area": "Everyday", "level": "A2", "title_es": "...", "title_en": "...",
  "grammar": [{"name": "...", "explain": "*es* marks Spanish", "examples": [{"es": "...", "en": "..."}],
               "links": [{"title": "Por vs. para", "url": "../intermediate/por-vs-para.html"}]}],
  "vocab": [{"id": "piso", "es": "piso", "gender": "m|f|mpl|fpl|(empty)", "plural": "pisos",
             "en": "flat", "examples": [{"es": "...", "en": "..."}], "note": "optional"}],
  "text": "paragraphs split by blank lines; {{id|surface}} = list word, {{=surface|translation}} = extra gloss",
  "quiz": [{"q": "...", "options": ["a", "b", "c", "d", "e"], "answer": 1, "explain": "..."}]
}
"""
import hashlib, html, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "spanish-src", "stories")
OUT = os.path.join(ROOT, "spanish", "stories")
TEMPLATE = os.path.join(ROOT, "readings", "01-wg-zimmer.html")
AREA_EMOJI = {"Everyday": "🏠", "Work and study": "💼", "Travel and culture": "✈️", "Food and social life": "🍽️"}


def load():
    stories = []
    if not os.path.isdir(SRC):
        return stories
    for f in sorted(os.listdir(SRC)):
        if f.endswith(".json"):
            d = json.load(open(os.path.join(SRC, f), encoding="utf-8"))
            d["id"] = f[:-5]
            stories.append(d)
    stories.sort(key=lambda d: d["n"])
    return stories


def pid(sid):
    return hashlib.sha1(("spanish/stories/" + sid).encode()).hexdigest()[:12]


def to_template(d):
    """Map the Spanish keys onto the keys the German page script reads."""
    ex = lambda xs: [{"de": x["es"], "en": x["en"]} for x in xs or []]
    return {
        "id": d["id"], "n": d["n"], "area": d["area"], "level": d["level"],
        "title_de": d["title_es"], "title_en": d["title_en"],
        "grammar": [{"name": g["name"], "explain": g["explain"], "examples": ex(g.get("examples")),
                     "links": g.get("links", [])} for g in d["grammar"]],
        "vocab": [{"id": w["id"], "de": w["es"], "gender": w.get("gender", ""), "plural": w.get("plural", ""),
                   "en": w["en"], "examples": ex(w.get("examples")), "note": w.get("note", "")} for w in d["vocab"]],
        "text": d["text"], "quiz": d["quiz"],
    }


def page(tpl, d):
    h = tpl
    rep = [
        (r'<meta name="page-id" content="[0-9a-f]+">', f'<meta name="page-id" content="{pid(d["id"])}">'),
        (r"<title>.*?</title>", f"<title>{html.escape(d['title_es'])} · Spanish stories</title>"),
        (r'<a class="btn ghost" href="\.\./index\.html" aria-label="Back to the main page">← Main page</a>',
         '<a class="btn ghost" href="../index.html" aria-label="Back to Spanish grammar">← Spanish grammar</a>'),
        (r'<span class="hide-sm">Reading topics</span>', '<a class="hide-sm" href="../index.html#stories">Stories</a>'),
        (r'<div class="legend">.*?</div>',
         '<div class="legend"><span><span class="g g-m">m</span>el</span><span><span class="g g-f">f</span>la</span>'
         '<span><span class="g g-pl">pl</span>los / las</span><span><span class="g g-x">—</span>verb, adjective, phrase</span></div>'),
        (r"<footer>.*?</footer>",
         '<footer><span>Part of the Spanish library</span><a class="btn" href="../index.html">← Back to Spanish grammar</a></footer>'),
    ]
    for pat, new in rep:
        h, n = re.subn(pat, lambda m: new, h, count=1, flags=re.S)
        assert n == 1, pat
    # Spanish articles instead of der/die/das; plural genders share the "pl" colour
    js = [
        ("var GLAB = { m: 'm', f: 'f', n: 'n', pl: 'pl' };", "var GLAB = { m: 'm', f: 'f', mpl: 'pl', fpl: 'pl' };"),
        ("var ART = { m: 'der', f: 'die', n: 'das', pl: 'die' };", "var ART = { m: 'el', f: 'la', mpl: 'los', fpl: 'las' };"),
        ("s.appendChild(el('span', 'g g-' + g,", "s.appendChild(el('span', 'g g-' + (GLAB[g] || g),"),
        ("de.appendChild(el('span', 'art-' + g,", "de.appendChild(el('span', 'art-' + (GLAB[g] || g),"),
        ("/[\\wÄÖÜäöüß]/", "/[\\wáéíóúüñÁÉÍÓÚÜÑ]/"),
    ]
    for a, b in js:
        assert a in h, a
        h = h.replace(a, b)
    data = json.dumps(to_template(d), ensure_ascii=False).replace("</", "<\\/")
    h, n = re.subn(r'(<script type="application/json" id="page-data">\n).*?(\n</script>)',
                   lambda m: m.group(1) + data + m.group(2), h, count=1, flags=re.S)
    assert n == 1
    return h


def check(d):
    ids = {w["id"] for w in d["vocab"]}
    for m in re.finditer(r"\{\{(=?)([^|}]+)\|([^}]+)\}\}", d["text"]):
        if not m.group(1) and m.group(2) not in ids:
            raise SystemExit(f'{d["id"]}: {{{{{m.group(2)}|…}}}} is not in the word list')
    for q in d["quiz"]:
        if not 0 <= q["answer"] < len(q["options"]) <= 5:
            raise SystemExit(f'{d["id"]}: bad quiz answer in "{q["q"]}"')


def home_section(prefix="stories/"):
    """HTML for the stories block on the Spanish home page."""
    stories = load()
    if not stories:
        return ""
    cards = "".join(
        f'<a data-quiz="{pid(d["id"])}" class="home-card card" href="{prefix}{d["id"]}.html">'
        f'<span class="k">{d["n"]:02d} · {AREA_EMOJI.get(d["area"], "")} {html.escape(d["area"])} · {html.escape(d["level"])}</span>'
        f'<span class="t">{html.escape(d["title_es"])}</span><span class="d">{html.escape(d["title_en"])}</span>'
        f'<span class="d">{html.escape(" · ".join(g["name"] for g in d["grammar"]))}</span></a>'
        for d in stories)
    return (f'<section id="stories"><div class="sec-head"><h2>📖 Stories</h2><p class="hint">{len(stories)} short texts: '
            f'20 words each with examples, 2–3 grammar points, hover translations and a 10-question quiz.</p></div>'
            f'<div class="home-grid">{cards}</div></section>')


def build():
    stories = load()
    if not stories:
        return 0
    tpl = open(TEMPLATE, encoding="utf-8").read()
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        os.remove(os.path.join(OUT, f))
    for d in stories:
        check(d)
        open(os.path.join(OUT, d["id"] + ".html"), "w", encoding="utf-8").write(page(tpl, d))
    print(f"built {len(stories)} stories in spanish/stories/")
    return len(stories)


if __name__ == "__main__":
    build()
    import subprocess
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "site_switch.py")], check=True)
