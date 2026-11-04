"""Add the German / English / Spanish switch to the app bar of every page.

Idempotent: run it again after regenerating pages. Usage: python3 tools/site_switch.py
"""
import os, re, sys

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
    html = html.replace("</style>", CSS + "</style>", 1)
    open(path, "w", encoding="utf-8").write(html)
    return True


if __name__ == "__main__":
    n = 0
    for d, _, files in os.walk(ROOT):
        if "/.git" in d:
            continue
        for f in files:
            if f.endswith(".html") and patch(os.path.join(d, f)):
                n += 1
    print(f"patched {n} pages", file=sys.stderr)
