"""Add the German / English / Spanish switch to the app bar of every page, and the progress tracker.

Also writes progress-manifest.js (every page with a page-id, whether it has a quiz, and the area it
belongs to) and adds progress.js to every page; see progress.js for how progress is counted.

Idempotent: run it again after regenerating pages. Usage: python3 tools/site_switch.py
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import banners

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARK_CSS = "/* site switch */"
CSS = MARK_CSS + """
.siteswitch { margin-left: auto; display: flex; gap: 2px; padding: 3px; background: var(--secondary); border-radius: 9px; flex: none; }
.siteswitch a { padding: 4px 10px; border-radius: 6px; font-size: 13px; font-weight: 500; color: var(--muted); text-decoration: none; white-space: nowrap; }
.siteswitch a:hover { color: var(--fg); }
.siteswitch a[aria-current="page"] { background: var(--card); color: var(--fg); box-shadow: var(--shadow); }
@media (max-width: 520px) { .siteswitch .long { display: none; } .crumbs a, .crumbs .sep { display: none; } .crumbs .cur { white-space: nowrap; } }
"""
SW_RE = re.compile(r'<nav class="siteswitch".*?</nav>', re.S)
PROG_RE = re.compile(r'<script src="[./]*progress-manifest\.js"></script><script src="[./]*progress\.js" data-root="[./]*"></script>\n?')
PROG_CSS = """/* progress */
.score.ok { background: var(--brand-soft); color: var(--brand); }
.pscore { display: inline-flex; align-items: center; gap: 6px; }
.pscore .pbar { width: 40px; background: color-mix(in srgb, currentColor 22%, transparent); }
.pscore .pbar i { background: currentColor; }
.pbar { display: inline-block; width: 64px; height: 5px; border-radius: 999px; background: var(--secondary); overflow: hidden; vertical-align: middle; }
.pbar i { display: block; height: 100%; background: var(--ok); border-radius: 999px; }
.pstatus { display: flex; flex-wrap: wrap; align-items: center; gap: 6px 12px; font-size: 14px; color: var(--muted); }
.pstatus .pbar { width: 140px; height: 6px; }
.pcard { padding: 16px 18px; display: grid; gap: 10px; }
.pcard > .pbar { width: 100%; height: 8px; }
.phead { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 6px; }
.pnum { font-size: 13px; color: var(--muted); font-variant-numeric: tabular-nums; }
.pgroups { display: grid; gap: 4px 20px; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); }
.pgroup { display: grid; grid-template-columns: 1fr 80px 52px; align-items: center; gap: 10px; padding: 4px 0; color: var(--fg); text-decoration: none; font-size: 14px; }
.pgroup .pbar { width: 80px; } .pgroup .pnum { text-align: right; }
.pgroup:hover .pg-t { color: var(--brand); }
.pextra { border-top: 1px solid var(--border); padding-top: 10px; grid-template-columns: 1fr 120px 52px; }
.pextra .pbar { width: 120px; }
.phint { margin: 0; font-size: 12.5px; color: var(--muted); }
"""
FONTS = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700'
         '&family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Geist+Mono:wght@500;600&display=swap">')
FONT_RE = re.compile(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com/css2\?[^"]*">')
BANNER_RE = re.compile(r'<div class="banner" aria-hidden="true">.*?</svg></div>\n?', re.S)
# per-language palette: light, dark
PALETTES = {
    "german": ("--brand: #b91c1c; --brand-soft: #fdecec; --ring: #f87171; --bg: #fbf8f3; --border: #ece4d8; --input: #e6dccd; --secondary: #f4eee5; --primary: #7f1d1d; --primary-fg: #fff;",
               "--brand: #f87171; --brand-soft: #3a1515; --ring: #ef4444; --bg: #0f0d0b; --card: #171411; --border: #2e2720; --input: #2e2720; --secondary: #221c17; --primary: #fca5a5; --primary-fg: #1c0a0a;"),
    "english": ("--brand: #1d4ed8; --brand-soft: #e8eefd; --ring: #60a5fa; --bg: #f7f9fc; --border: #e1e7f1; --input: #d7dfec; --secondary: #edf1f8; --primary: #1e3a8a; --primary-fg: #fff;",
                "--brand: #7aa2ff; --brand-soft: #15213f; --ring: #3b82f6; --bg: #0a0d14; --card: #10141d; --border: #232b3b; --input: #232b3b; --secondary: #171d2a; --primary: #bfd0ff; --primary-fg: #0b1430;"),
    "spanish": ("--brand: #c2410c; --brand-soft: #fff0e4; --ring: #fb923c; --bg: #fdf9f3; --border: #efe2d2; --input: #e8d7c3; --secondary: #f8eee2; --primary: #9a3412; --primary-fg: #fff;",
                "--brand: #fb923c; --brand-soft: #3a1d0c; --ring: #f97316; --bg: #110d09; --card: #18120d; --border: #30251a; --input: #30251a; --secondary: #23190f; --primary: #fdba74; --primary-fg: #2a1205;"),
}


def theme_css(lang):
    light, dark = PALETTES[lang]
    return f"""/* theme: {lang} */
:root {{ {light} --font: "Figtree", "Segoe UI", system-ui, -apple-system, sans-serif; --serif: "Fraunces", Georgia, "Times New Roman", serif; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ {dark} }} }}
:root[data-theme="dark"] {{ {dark} }}
h1, h2, h3, .home-card .t, .result h3, .prose h2, .prose h3 {{ font-family: var(--serif); letter-spacing: -0.01em; }}
h1 {{ font-weight: 700; }}
.badge {{ border-color: color-mix(in srgb, var(--brand) 30%, var(--border)); color: var(--brand); background: var(--brand-soft); }}
.home-card:hover {{ border-color: var(--brand); box-shadow: 0 4px 14px color-mix(in srgb, var(--brand) 14%, transparent); }}
.prose h2 {{ border-top-color: color-mix(in srgb, var(--brand) 25%, var(--border)); }}
.banner {{ height: clamp(8px, 2.6vw, 40px); overflow: hidden; line-height: 0; border-bottom: 3px solid transparent; border-image: {banners.stripe_css(lang)} 1; }}
.banner svg {{ display: block; width: 100%; height: 100%; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) .banner .bn-bg {{ fill: var(--secondary); }} }}
:root[data-theme="dark"] .banner .bn-bg {{ fill: var(--secondary); }}
"""


HOMES = {"index.html", "english/index.html", "spanish/index.html"}
GERMAN_GROUPS = {"docs": ("Reference docs", "index.html#grammar"), "grammar": ("German grammar", "grammar/index.html"), "readings": ("Reading topics", "index.html#readings"),
                 "quizzes": ("Doc quizzes", "index.html#quizzes"), "everyday": ("Everyday German", "everyday/index.html"),
                 "tests": ("Tests", "index.html#quizzes")}


def manifest(paths):
    """progress-manifest.js: one entry per page with a page-id (language homes excluded)."""
    import json
    pages, groups, group_of = [], {}, {}
    for path in sorted(paths):
        rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
        if rel in HOMES:
            continue
        h = open(path, encoding="utf-8").read()
        m = re.search(r'<meta name="page-id" content="([0-9a-f]+)">', h)
        if not m:
            continue
        q = re.search(r'id="(?:quiz-data|page-data)">\s*(.*?)\s*</script>', h, re.S)
        nq = 0
        if q:
            d = json.loads(q.group(1))
            nq = len(d.get("questions") or d.get("quiz") or [])
        seg = rel.split("/")
        key = "/".join(seg[:2]) if seg[0] in ("english", "spanish") else seg[0]
        if seg[0] == "grammar":  # German grammar is broken down by its sections
            key = "grammar/" + (seg[1] if len(seg) > 2 else seg[1][:-5])
        if key not in groups:
            if seg[0] in ("english", "spanish"):
                idx = os.path.join(ROOT, key, "index.html")
                t = re.search(r"<h1>(.*?)</h1>", open(idx, encoding="utf-8").read()) if os.path.exists(idx) else None
                title = t.group(1) if t else seg[1].replace("-", " ").capitalize()
                href = key + "/index.html" if os.path.exists(idx) else seg[0] + "/index.html#" + seg[1]
            elif seg[0] == "grammar":
                src = os.path.join(ROOT, key, "index.html") if len(seg) > 2 else path
                t = re.search(r"<h1>(.*?)</h1>", open(src, encoding="utf-8").read())
                title = "Grammar overview" if rel == "grammar/index.html" else (t.group(1) if t else key)
                href = key + "/index.html" if len(seg) > 2 else rel
            else:
                title, href = GERMAN_GROUPS.get(key, (key.capitalize(), "index.html"))
            groups[key] = {"key": key, "title": title, "href": href}
        group_of[rel] = key
        pages.append({"path": rel, "id": m.group(1), "q": nq})
    # list areas in the order the language home page shows them
    german_order = ["grammar", "everyday", "docs", "readings", "quizzes", "tests"]

    def pos(g):
        k = g["key"]
        if k.startswith("grammar/"):  # German grammar sections in the order of grammar/index.html
            gi = open(os.path.join(ROOT, "grammar", "index.html"), encoding="utf-8").read()
            i = gi.find('href="' + k[8:] + ("/" if os.path.isdir(os.path.join(ROOT, k)) else ".html"))
            return (0, 0, i if i >= 0 else -1)
        if "/" not in k:
            return (0, 1 + (german_order.index(k) if k in german_order else 99), 0)
        home = open(os.path.join(ROOT, k.split("/")[0], "index.html"), encoding="utf-8").read()
        i = home.find('href="' + k.split("/")[1] + "/")
        return (1 if k.startswith("english") else 2, i if i >= 0 else 10 ** 9, 0)
    data = {"pages": pages, "groups": sorted(groups.values(), key=pos), "groupOf": group_of}
    open(os.path.join(ROOT, "progress-manifest.js"), "w", encoding="utf-8").write(
        "window.PROGRESS_MANIFEST = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n")
    return len(pages)


# (code, folder, flag, label); the German library lives at the site root
LANGS = [("de", "", "🇩🇪", "German"), ("en", "english/", "🇬🇧", "English"), ("es", "spanish/", "🇪🇸", "Spanish")]


def switch(rel_root, current):
    links = []
    for code, folder, flag, label in LANGS:
        if folder and not os.path.exists(os.path.join(ROOT, folder, "index.html")):
            continue  # section not built yet
        cur = 'aria-current="page" ' if code == current else ""
        links.append(f'<a {cur}href="{rel_root}{folder}index.html">{flag}<span class="long"> {label}</span></a>')
    return '<nav class="siteswitch" aria-label="Library">' + "".join(links) + "</nav>"


def patch(path):
    rel = os.path.relpath(path, ROOT)
    depth = rel.count(os.sep)
    rel_root = "../" * depth
    current = next((c for c, f, _, _ in LANGS if f and rel.startswith(f[:-1] + os.sep)), "de")
    html = open(path, encoding="utf-8").read()
    html = SW_RE.sub("", html)
    start = html.find('<div class="appbar">')
    end = html.find('<div class="wrap">', start)
    if start < 0 or end < 0:
        return False
    bar = html[start:end]
    i = bar.rfind("</div></div>")
    bar = bar[:i] + switch(rel_root, current) + bar[i:]
    html = html[:start] + bar + html[end:]
    html = re.sub(re.escape(MARK_CSS) + r".*?(?=</style>)", "", html, count=1, flags=re.S)
    html = html.replace("</style>", CSS + PROG_CSS + theme_css(banners.lang_of(rel.replace(os.sep, "/"))) + "</style>", 1)
    html = FONT_RE.sub(lambda m: FONTS, html, count=1)
    html = BANNER_RE.sub("", html)
    html = html.replace('<div class="wrap">', banners.banner(rel.replace(os.sep, "/")) + '\n<div class="wrap">', 1)
    html = PROG_RE.sub("", html)
    html = html.replace("</body>", f'<script src="{rel_root}progress-manifest.js"></script><script src="{rel_root}progress.js" data-root="{rel_root}"></script>\n</body>', 1)
    open(path, "w", encoding="utf-8").write(html)
    return True


if __name__ == "__main__":
    n, pages = 0, []
    for d, _, files in os.walk(ROOT):
        if "/.git" in d:
            continue
        for f in files:
            if f.endswith(".html") and patch(os.path.join(d, f)):
                n += 1
                pages.append(os.path.join(d, f))
    print(f"progress manifest: {manifest(pages)} pages", file=sys.stderr)
    print(f"patched {n} pages", file=sys.stderr)
