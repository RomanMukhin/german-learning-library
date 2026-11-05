"""Build a language section of the site (english/, spanish/) from Markdown sources in <dir>-src/.

Layout of <dir>-src/:
  _home.md                      intro text for <dir>/index.html
  <section>/_index.md           first-level topic page (front matter + body)
  <section>/quiz.json           quiz shown at the end of the first-level topic page
  <section>/<page>.md           child pages (front matter + body)

Front matter is a block of "key: value" lines between two "---" lines.
Keys: title, sub, order, emoji (sections), level (optional).
Callouts: a blockquote whose first line is "[!hack] Title", "[!trap] Title" or "[!fact] Title".
Links between pages: write [text](section/page) and it becomes a relative link.

Styles and the quiz script are taken from an existing German page, so both halves of the
site look and behave the same. Run: python3 tools/build_section.py [english|spanish ...]
(no argument builds every section that has a source folder)
"""
import hashlib, html, json, os, re, shutil, sys
import markdown

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECTIONS = {"english": "English grammar", "spanish": "Spanish grammar"}
DIR, NAME = "english", SECTIONS["english"]
SRC = os.path.join(ROOT, DIR + "-src")
OUT = os.path.join(ROOT, DIR)


def configure(d):
    global DIR, NAME, SRC, OUT
    DIR, NAME = d, SECTIONS[d]
    SRC, OUT = os.path.join(ROOT, d + "-src"), os.path.join(ROOT, d)
TEMPLATE = os.path.join(ROOT, "grammar", "cases", "index.html")

tpl = open(TEMPLATE, encoding="utf-8").read()
STYLE = tpl[tpl.index("<style>"):tpl.index("</style>") + len("</style>")]
scripts = re.findall(r"<script>\n.*?\n</script>", tpl, re.S)
QUIZ_JS, TILES_JS = scripts[0], scripts[1]
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@500;600&display=swap">')
EXTRA_CSS = """<style>
.prose .ex { margin: 6px 0 12px; padding: 0; list-style: none; display: grid; gap: 4px; }
.prose .ex li { padding: 6px 12px; border-left: 2px solid var(--border); background: var(--secondary); border-radius: 0 8px 8px 0; }
.prose del { color: var(--bad); text-decoration-thickness: 1.5px; }
.wrap { grid-template-columns: minmax(0, 1fr); }
.prose > h2:first-child { border-top: 0; padding-top: 0; }
.toc-list { columns: 2 260px; column-gap: 28px; margin: 0; padding-left: 18px; }
.toc-list li { break-inside: avoid; margin: 0 0 4px; }
</style>"""


def pid(path):
    return hashlib.sha1((DIR + "/" + path).encode()).hexdigest()[:12]


def read(path):
    text = open(path, encoding="utf-8").read()
    meta = {}
    if text.startswith("---\n"):
        head, text = text[4:].split("\n---\n", 1)
        for line in head.splitlines():
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip()
    return meta, text


def md(text, depth):
    """Markdown to HTML with callouts, example lists and site-relative links."""
    # callouts
    def callout(m):
        kind, title, body = m.group(1), m.group(2).strip(), m.group(3)
        body = re.sub(r"^> ?", "", body, flags=re.M)
        inner = markdown.markdown(body, extensions=["tables"])
        return (f'\n<aside class="callout {kind}"><p class="callout-title">{html.escape(title)}</p>'
                f'{inner}</aside>\n')
    # a run of lines starting with "» " is an example block
    text = re.sub(r"(?:^» .*\n?)+", lambda m: "\n{.ex}\n\n" + re.sub(r"^» ", "- ", m.group(0), flags=re.M) + "\n", text, flags=re.M)
    text = re.sub(r"^\{\.ex\}\n(?!\n)", "{.ex}\n\n", text, flags=re.M)
    # links like (section/page) or (section/) to relative paths
    up = "../" * (depth - 1)  # links are relative to the section folder

    def link(m):
        target = m.group(2)
        if re.match(r"^(https?:|#|\.\.?/)", target):
            return m.group(0)
        anchor = ""
        if "#" in target:
            target, anchor = target.split("#", 1)
            anchor = "#" + anchor
        target = target.rstrip("/")
        path = target + ("/index.html" if "/" not in target else ".html")
        return f"[{m.group(1)}]({up}{path}{anchor})"
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, text)
    text = re.sub(r"^> \[!(hack|trap|fact)\] ?(.*)\n((?:>.*\n?)*)", callout, text, flags=re.M)
    out = markdown.markdown(text, extensions=["tables", "md_in_html", "sane_lists", "toc"])
    out = out.replace("<table>", '<div class="table-wrap"><table>').replace("</table>", "</table></div>")
    # a list directly after a paragraph ending in ":" whose items are example sentences keeps the default style;
    # lists marked with {.ex} on the line before become example blocks
    out = out.replace("<p>{.ex}</p>\n<ul>", '<ul class="ex">')
    out = re.sub(r"~~(.+?)~~", r"<del>\1</del>", out)
    return out


def shuffled(q):
    """Same order on every build, but the right answer lands in a different slot per question."""
    import random
    idx = list(range(len(q["options"])))
    random.Random(hashlib.sha1(q["q"].encode()).hexdigest()).shuffle(idx)
    return {"q": q["q"], "options": [q["options"][i] for i in idx], "answer": idx.index(q["answer"]), "explain": q["explain"]}


def quiz_block(quiz):
    data = {"questions": [shuffled(q) for q in quiz["questions"]], "title": quiz["title"], "level": quiz.get("level", "")}
    js = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    section = """<section id="quiz" data-embedded>
  <div class="sec-head"><h2>Quiz</h2><p class="hint">Answer every question, then check. Each answer comes with a short explanation. Reloading the page starts over.</p></div>
  <div class="qbar card">
    <div class="progress"><span id="progress"></span><span class="meter"><i id="meter"></i></span></div>
    <div class="actions">
      <button class="btn primary" id="check" type="button">Check answers</button>
      <button class="btn" id="copy" type="button" hidden>Copy results</button>
      <button class="btn" id="reset" type="button">Start over</button>
    </div>
  </div>
  <p class="note-copy" id="copynote" hidden></p>
  <div class="result card" id="result" hidden aria-live="polite"></div>
  <div id="questions" style="display:grid;gap:12px"></div>
</section>"""
    scripts = f'<script type="application/json" id="quiz-data">\n{js}\n</script>\n{QUIZ_JS}'
    return section, scripts


def page(*, path, title, crumbs, badge, h1, sub, body, depth, quiz=None, pager=""):
    up = "../" * depth
    crumb_html = "".join(f'<span class="sep">/</span><a href="{h}">{html.escape(t)}</a>' for t, h in crumbs)
    crumb_html += f'<span class="sep">/</span><span class="cur">{html.escape(title)}</span>'
    qsec, qjs = quiz_block(quiz) if quiz else ("", "")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta name="page-id" content="{pid(path)}">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="robots" content="noindex, nofollow">
<title>{html.escape(title)} · {NAME}</title>
{FONTS}
{STYLE}
{EXTRA_CSS}
</head>
<body>
<div class="appbar"><div class="appbar-inner">
  <a class="btn ghost" href="{up}{DIR}/index.html">← {NAME}</a>
  <div class="crumbs">{crumb_html}</div>
</div></div>
<div class="wrap">
<header class="hero"><span class="badge"><span class="dot"></span>{html.escape(badge)}</span><h1>{html.escape(h1)}</h1><p class="sub">{html.escape(sub)}</p></header>
{body}
{pager}
{qsec}
<footer><span>Part of the {NAME} library</span><a class="btn" href="{up}{DIR}/index.html">← Back to {NAME}</a></footer>
</div>
{qjs}
{TILES_JS}
<script>
(function () {{
  // area headings on the home page: show the last saved quiz result of that area
  function get(id) {{ try {{ return JSON.parse(localStorage.getItem('quiz:' + id) || 'null'); }} catch (e) {{ return null; }} }}
  document.querySelectorAll('h2 > a[data-quiz]').forEach(function (a) {{
    var r = get(a.getAttribute('data-quiz')); if (!r || !r.total) return;
    var pct = r.score / r.total, b = document.createElement('span');
    b.className = 'score' + (pct >= 0.9 ? ' hi' : '');
    b.textContent = (pct >= 0.9 ? '✓ ' : '') + r.score + '/' + r.total; b.title = 'Last quiz result';
    a.parentNode.appendChild(b);
  }});
}})();
</script>
</body>
</html>
"""


def esc(s):
    return html.escape(s, quote=True)


def build():
    sections = []
    for name in sorted(os.listdir(SRC)):
        d = os.path.join(SRC, name)
        if not os.path.isdir(d) or not os.path.exists(os.path.join(d, "_index.md")):
            continue
        meta, body = read(os.path.join(d, "_index.md"))
        children = []
        for f in sorted(os.listdir(d)):
            if f.endswith(".md") and f != "_index.md":
                cm, cb = read(os.path.join(d, f))
                children.append({"slug": f[:-3], "meta": cm, "body": cb})
        children.sort(key=lambda c: (float(c["meta"].get("order", 999)), c["meta"]["title"].lower()))
        qpath = os.path.join(d, "quiz.json")
        quiz = json.load(open(qpath, encoding="utf-8")) if os.path.exists(qpath) else None
        sections.append({"slug": name, "meta": meta, "body": body, "children": children, "quiz": quiz})
    sections.sort(key=lambda s: float(s["meta"].get("order", 999)))

    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    total_pages = 0
    for si, s in enumerate(sections):
        os.makedirs(os.path.join(OUT, s["slug"]))
        m = s["meta"]
        # child pages
        for ci, c in enumerate(s["children"]):
            cm = c["meta"]
            prev_ = s["children"][ci - 1] if ci > 0 else None
            next_ = s["children"][ci + 1] if ci + 1 < len(s["children"]) else None
            pager = '<nav class="pager">'
            pager += (f'<a class="btn" href="{prev_["slug"]}.html">← {esc(prev_["meta"]["title"])}</a>' if prev_
                      else f'<a class="btn" href="index.html">← {esc(m["title"])}</a>')
            pager += (f'<a class="btn" href="{next_["slug"]}.html">{esc(next_["meta"]["title"])} →</a>' if next_
                      else f'<a class="btn" href="index.html#quiz">{esc(m["title"])} quiz →</a>')
            pager += "</nav>"
            content = md(c["body"], 2)
            heads = re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', content)
            toc = ""
            if len(heads) >= 3:
                toc = ('<nav class="card prose" style="padding:16px 20px" aria-label="On this page"><p style="margin:0 0 6px;font-weight:600">On this page</p><ol class="toc-list">'
                       + "".join(f'<li><a href="#{i}">{t}</a></li>' for i, t in heads) + '</ol></nav>\n')
            body = f'{toc}<article class="prose card">\n{content}\n</article>'
            out = page(path=f'{s["slug"]}/{c["slug"]}', title=cm["title"],
                       crumbs=[(m["title"], "index.html")], badge=f'{m["title"]}',
                       h1=cm["title"], sub=cm.get("sub", ""), body=body, depth=2, pager=pager)
            open(os.path.join(OUT, s["slug"], c["slug"] + ".html"), "w", encoding="utf-8").write(out)
            total_pages += 1
        # section page: tiles of children, overview text, quiz
        tiles = "".join(
            f'<a class="home-card card" href="{c["slug"]}.html"><span class="t">{esc(c["meta"]["title"])}</span>'
            f'<span class="d">{esc(c["meta"].get("sub", ""))}</span></a>' for c in s["children"])
        body = (f'<section><div class="sec-head"><h2>In this section</h2><p class="hint">{len(s["children"])} topics. '
                f'Read them in order, then take the quiz at the bottom of this page.</p></div>'
                f'<div class="home-grid">{tiles}</div></section>\n')
        if s["body"].strip():
            body += f'<article class="prose card">\n{md(s["body"], 2)}\n</article>'
        prev_ = sections[si - 1] if si > 0 else None
        next_ = sections[si + 1] if si + 1 < len(sections) else None
        pager = '<nav class="pager">'
        pager += f'<a class="btn" href="../{prev_["slug"]}/index.html">← {esc(prev_["meta"]["title"])}</a>' if prev_ else "<span></span>"
        pager += f'<a class="btn" href="../{next_["slug"]}/index.html">{esc(next_["meta"]["title"])} →</a>' if next_ else ""
        pager += "</nav>"
        out = page(path=f'{s["slug"]}/index', title=m["title"], crumbs=[], badge=NAME,
                   h1=m["title"], sub=m.get("sub", ""), body=body, depth=2, quiz=s["quiz"], pager=pager)
        open(os.path.join(OUT, s["slug"], "index.html"), "w", encoding="utf-8").write(out)
        total_pages += 1

    # home
    hm, hb = read(os.path.join(SRC, "_home.md"))
    parts = []
    for s in sections:
        m = s["meta"]
        sp = pid(f'{s["slug"]}/index')
        items = "".join(f'<li><a href="{s["slug"]}/{c["slug"]}.html">{esc(c["meta"]["title"])}</a></li>' for c in s["children"])
        nq = len(s["quiz"]["questions"]) if s["quiz"] else 0
        parts.append(
            f'<section id="{s["slug"]}"><div class="sec-head"><h2><a data-quiz="{sp}" href="{s["slug"]}/index.html" '
            f'style="color:inherit;text-decoration:none">{m.get("emoji", "")} {esc(m["title"])}</a></h2>'
            f'<p class="hint">{esc(m.get("sub", ""))} · {len(s["children"])} topics · quiz of {nq} questions</p></div>'
            f'<div class="card prose" style="padding:16px 20px"><ol class="toc-list">{items}</ol></div></section>')
    tabs = "".join(f'<a href="#{s["slug"]}">{esc(s["meta"]["title"])}</a>' for s in sections)
    stories = ""
    if DIR == "spanish":  # reading stories, built by tools/build_stories.py
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import build_stories
        stories = build_stories.home_section()
        if stories:
            tabs += '<a href="#stories">Stories</a>'
    body = (f'<nav class="tabs" aria-label="Sections">{tabs}</nav>\n'
            + (f'<article class="prose card">\n{md(hb, 1)}\n</article>\n' if hb.strip() else "")
            + "\n".join(parts) + stories)
    out = page(path="index", title=hm.get("title", NAME), crumbs=[], badge=hm.get("badge", "British English"),
               h1=hm.get("title", NAME), sub=hm.get("sub", ""), body=body, depth=1)
    # the home page has no back button and no crumbs
    out = re.sub(r'  <a class="btn ghost" href="[^"]*">← ' + re.escape(NAME) + r'</a>\n', "", out, count=1)
    out = out.replace('<div class="crumbs"><span class="sep">/</span><span class="cur">',
                      '<div class="crumbs"><span class="cur">', 1)
    out = out.replace(f'<footer><span>Part of the {NAME} library</span><a class="btn" href="../{DIR}/index.html">← Back to {NAME}</a></footer>',
                      f'<footer><span>{NAME} library</span><a class="btn" href="../index.html">🇩🇪 German library</a></footer>')
    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(out)
    total_pages += 1
    print(f"built {total_pages} pages in {DIR}/")
    if DIR == "spanish":
        build_stories.build()


if __name__ == "__main__":
    import sys
    for d in (sys.argv[1:] or [d for d in SECTIONS if os.path.isdir(os.path.join(ROOT, d + "-src"))]):
        configure(d)
        build()
    import subprocess, sys
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "site_switch.py")], check=True)
