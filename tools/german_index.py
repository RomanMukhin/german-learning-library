"""Rebuild the German grammar overviews from the section pages themselves.

Updates, from what exists under grammar/:
  - the "In this section" tiles and the sections table in grammar/index.html
  - the German grammar cards on the main page (index.html, section id="topics")
  - the pager links between neighbouring section index pages
Run after adding or removing a German grammar page: python3 tools/german_index.py
"""
import html, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, "grammar")
# reading order of the sections: (path under grammar/, emoji, short name, what it covers, why it matters)
SECTIONS = [
    ("tenses/index.html", "⏳", "Tenses", "Present, Perfekt, Präteritum, Plusquamperfekt, Futur I and II", "Telling what happens, happened, will happen"),
    ("moods/index.html", "🎭", "Moods", "Imperative, Konjunktiv II, Konjunktiv I", "Requests, politeness, \"would\", wishes"),
    ("passive.html", "🔄", "Passive", "<em>werden</em> + Partizip II", "Rules, news, instructions: \"it is done\""),
    ("verbs/index.html", "⚙️", "Verbs", "<em>sein/haben/werden</em>, modals, separable, reflexive, participles, verbs with prepositions", "The engine of every sentence"),
    ("nouns/index.html", "🏷️", "Nouns", "Gender, plural, articles", "Every noun comes with der, die or das"),
    ("cases/index.html", "🧱", "Cases", "Nominative, accusative, dative, genitive", "Who does what to whom"),
    ("adjectives/index.html", "🎨", "Adjectives", "Endings, comparison, formation, participles as adjectives", "Describing people and things correctly"),
    ("pronouns/index.html", "👤", "Pronouns", "Personal, possessive, reflexive, relative, interrogative and more", "Not repeating nouns, asking questions"),
    ("sentences/index.html", "🧵", "Sentences", "Word order, questions, negation, all kinds of clauses", "Putting it all in the right order"),
    ("prepositions/index.html", "📍", "Prepositions", "Place, time, two-way, causal, manner", "Where, when, why and how"),
    ("adverbs/index.html", "🧭", "Adverbs", "Types, position, comparison", "Adding where, when and how to a sentence"),
]
NUM = {9: "nine", 10: "ten", 11: "eleven", 12: "twelve"}


def read(p):
    return open(p, encoding="utf-8").read()


def info(rel):
    """Title, description, level, page-id, topic pages and quiz count of one section."""
    path = os.path.join(G, rel)
    h = read(path)
    pid = re.search(r'<meta name="page-id" content="([0-9a-f]+)">', h).group(1)
    title = html.unescape(re.search(r"<h1>(.*?)</h1>", h).group(1))
    sub = html.unescape(re.search(r'<p class="sub">(.*?)</p>', h).group(1))
    level = re.search(r'<span class="badge"><span class="dot"></span>(?:Grammar · )?(.*?)</span>', h).group(1)
    folder = os.path.dirname(rel)
    pages, total = [], 0

    def quiz_len(doc):
        m = re.search(r'id="quiz-data">\s*(.*?)\s*</script>', doc, re.S)
        return len(json.loads(m.group(1))["questions"]) if m else 0

    total += quiz_len(h)
    if folder:
        grid = re.search(r'<div class="home-grid">(.*?)</div></section>', h, re.S).group(1)
        for m in re.finditer(r'<a data-quiz="([0-9a-f]+)" class="home-card card" href="([^"]+)"><span class="t">(.*?)</span>', grid):
            pages.append((m.group(1), f"{folder}/{m.group(2)}", re.sub("<[^>]+>", "", m.group(3))))
            total += quiz_len(read(os.path.join(G, folder, m.group(2))))
    return dict(rel=rel, pid=pid, title=title, sub=sub, level=level, pages=pages, quiz=total)


def esc(s):
    return html.escape(s, quote=True)


def main():
    secs = [dict(info(rel), emoji=e, short=n, covers=c, why=w) for rel, e, n, c, w in SECTIONS
            if os.path.exists(os.path.join(G, rel))]
    count = NUM.get(len(secs), str(len(secs)))

    # 1. pager links between neighbouring section index pages
    for i, s in enumerate(secs):
        path = os.path.join(G, s["rel"])
        up = "../" if os.path.dirname(s["rel"]) else ""
        link = lambda t, arrow: (f'<a data-quiz="{t["pid"]}" class="btn" href="{up}{t["rel"]}">'
                                 + (f'← {esc(t["short"])}' if arrow == "prev" else f'{esc(t["short"])} →') + "</a>")
        nav = '<nav class="pager">' + (link(secs[i - 1], "prev") if i else "") + (link(secs[i + 1], "next") if i + 1 < len(secs) else "") + "</nav>"
        h = read(path)
        h = re.sub(r'<nav class="pager">.*?</nav>', lambda m: nav, h, count=1, flags=re.S)
        open(path, "w", encoding="utf-8").write(h)

    # 2. grammar/index.html: tiles, sections table, counts
    p = os.path.join(G, "index.html")
    h = read(p)
    tiles = "".join(f'<a data-quiz="{s["pid"]}" class="home-card card" href="{s["rel"]}"><span class="t">{esc(s["title"])}</span>'
                    f'<span class="d">{esc(s["sub"])}</span><span class="k">{esc(s["level"])}</span></a>' for s in secs)
    h = re.sub(r'(<section><div class="sec-head"><h2>In this section</h2></div><div class="home-grid">).*?(</div></section>)',
               lambda m: m.group(1) + tiles + m.group(2), h, count=1, flags=re.S)
    rows = "".join(f'<tr>\n<td><a data-quiz="{s["pid"]}" href="../grammar/{s["rel"]}">{esc(s["short"])}</a></td>\n<td>{s["covers"]}</td>\n<td>{esc(s["why"])}</td>\n</tr>\n' for s in secs)
    h = re.sub(r"(<h2>The )\w+( sections</h2>\s*<div class=\"table-wrap\"><table>\s*<thead>.*?</thead>\s*<tbody>\n).*?(</tbody>)",
               lambda m: m.group(1) + count + m.group(2) + rows + m.group(3), h, count=1, flags=re.S)
    h = re.sub(r"German grammar in \w+ sections", f"German grammar in {count} sections", h)
    open(p, "w", encoding="utf-8").write(h)

    # 3. main page cards
    p = os.path.join(ROOT, "index.html")
    h = read(p)
    cards = ""
    for s in secs:
        links = " · ".join(f'<a data-quiz="{pid}" href="grammar/{href}">{esc(t)}</a>' for pid, href, t in s["pages"])
        cards += (f'<div class="home-card card"><a data-quiz="{s["pid"]}" class="t" href="grammar/{s["rel"]}">{s["emoji"]} {esc(s["title"])}</a>'
                  f'<span class="d">{esc(s["sub"])}</span>' + (f'<span class="k">{links}</span>' if links else "")
                  + f'<span class="k">{esc(s["level"])} · {s["quiz"]} quiz questions</span></div>')
    h = re.sub(r'(<section id="topics">.*?<div class="home-grid">).*?(</div></section>)', lambda m: m.group(1) + cards + m.group(2), h, count=1, flags=re.S)
    h = re.sub(r"German grammar in \w+ sections", f"German grammar in {count} sections", h)
    open(p, "w", encoding="utf-8").write(h)
    print(f"{len(secs)} sections, {sum(len(s['pages']) for s in secs)} topic pages, {sum(s['quiz'] for s in secs)} quiz questions")


if __name__ == "__main__":
    main()
