"""Thin thematic banner strips (inline SVG) for every page of the site.

Each strip mixes the language's colours with small line icons that hint at the page's topic: a grammar
section (clocks for tenses, gears for verbs...) or a story's subject (a cup for a coffee story...).
The layout is seeded by the page path, so every page gets its own arrangement.
Used by tools/site_switch.py.
"""
import hashlib, math, random

# 24x24 line icons (stroke only)
ICONS = {
    "clock": "M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18M12 7v5l3 2",
    "hourglass": "M6 3h12M6 21h12M7 3c0 5 10 5 10 9s-10 4-10 9M17 3c0 5-10 5-10 9s10 4 10 9",
    "bubble": "M4 5h16v11H9l-5 4z",
    "bubbles": "M3 4h12v8H7l-4 3zM9 15v2h7l4 3V10h-3",
    "loop": "M4 12a8 8 0 0 1 14-5M20 12a8 8 0 0 1-14 5M18 3v4h-4M6 21v-4h4",
    "gear": "M10 2h4l.6 2.6 2.2 1.3 2.5-.9 2 3.4-2 1.8v2.6l2 1.8-2 3.4-2.5-.9-2.2 1.3L14 22h-4l-.6-2.6-2.2-1.3-2.5.9-2-3.4 2-1.8v-2.6l-2-1.8 2-3.4 2.5.9 2.2-1.3zM12 9a3 3 0 1 0 0 6a3 3 0 1 0 0-6",
    "tag": "M3 3h8l10 10-8 8L3 11zM7 7h.01",
    "box": "M4 7l8-4 8 4v10l-8 4-8-4zM4 7l8 4 8-4M12 11v10",
    "star": "M12 3l2.6 5.6 6 .7-4.5 4.1 1.2 6L12 16.5 6.7 19.4l1.2-6L3.4 9.3l6-.7z",
    "person": "M12 4a4 4 0 1 0 0 8a4 4 0 1 0 0-8M4 21c1-4 4-6 8-6s7 2 8 6",
    "people": "M9 5a3 3 0 1 0 0 6a3 3 0 1 0 0-6M2 20c.7-3 3.2-5 7-5s6.3 2 7 5M16 6a3 3 0 0 1 0 6M18 15c2 .6 3.4 2.4 4 5",
    "link": "M10 14a4 4 0 0 0 6 0l3-3a4 4 0 0 0-6-6l-1 1M14 10a4 4 0 0 0-6 0l-3 3a4 4 0 0 0 6 6l1-1",
    "arrow": "M4 12h15M14 6l6 6-6 6",
    "arrows": "M3 8h14M13 4l4 4-4 4M21 16H7M11 12l-4 4 4 4",
    "pin": "M12 21s-7-6.5-7-12a7 7 0 0 1 14 0c0 5.5-7 12-7 12zM12 6a3 3 0 1 0 0 6a3 3 0 1 0 0-6",
    "compass": "M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18M15.5 8.5l-2 5-5 2 2-5z",
    "check": "M4 12l5 5L20 6",
    "cross": "M6 6l12 12M18 6L6 18",
    "question": "M9 9a3 3 0 1 1 4 2.8c-.7.4-1 1-1 1.7V15M12 19h.01",
    "leaf": "M5 19C5 10 10 5 20 4c-1 10-6 15-15 15zM5 19l8-8",
    "tree": "M12 22v-7M12 3l6 8h-3l4 5H5l4-5H6z",
    "sun": "M12 8a4 4 0 1 0 0 8a4 4 0 1 0 0-8M12 2v2M12 20v2M2 12h2M20 12h2M5 5l1.5 1.5M17.5 17.5L19 19M5 19l1.5-1.5M17.5 6.5L19 5",
    "house": "M3 11l9-7 9 7M5 10v10h14V10M10 20v-6h4v6",
    "briefcase": "M3 8h18v12H3zM9 8V5h6v3M3 13h18",
    "plane": "M2 13l20-8-6 16-4-6zM12 15l4-4",
    "cup": "M4 9h13v5a5 5 0 0 1-5 5H9a5 5 0 0 1-5-5zM17 10h2a2 2 0 0 1 0 4h-2M8 3c0 2 2 2 2 4M12 3c0 2 2 2 2 4",
    "plate": "M12 5a7 7 0 1 0 0 14a7 7 0 1 0 0-14M12 9a3 3 0 1 0 0 6a3 3 0 1 0 0-6M2 4v6M2 7h0M22 4v16",
    "mountain": "M2 20l7-12 4 6 3-4 6 10zM9 8l2 3",
    "note": "M9 18V5l11-2v13M9 18a3 3 0 1 1-6 0a3 3 0 1 1 6 0M20 16a3 3 0 1 1-6 0a3 3 0 1 1 6 0",
    "heart": "M12 20s-8-5-8-11a4.5 4.5 0 0 1 8-2.8A4.5 4.5 0 0 1 20 9c0 6-8 11-8 11z",
    "paw": "M12 13c-3 0-5 3-5 5 0 1.5 1.5 2 3 1.5s2.5-.5 4 0 3 0 3-1.5c0-2-2-5-5-5zM6 9a1.8 2.2 0 1 0 0 4.4A1.8 2.2 0 1 0 6 9M18 9a1.8 2.2 0 1 0 0 4.4A1.8 2.2 0 1 0 18 9M9.5 4a1.8 2.2 0 1 0 0 4.4A1.8 2.2 0 1 0 9.5 4M14.5 4a1.8 2.2 0 1 0 0 4.4A1.8 2.2 0 1 0 14.5 4",
    "flame": "M12 22c4 0 7-3 7-7 0-5-4-7-5-12-3 3-4 5-4 8-1-1-2-2-2-4-2 2-3 5-3 8 0 4 3 7 7 7z",
    "bulb": "M9 18h6M10 21h4M12 3a6 6 0 0 0-4 10.5c.8.8 1 1.5 1 2.5h6c0-1 .2-1.7 1-2.5A6 6 0 0 0 12 3z",
    "doc": "M6 3h8l4 4v14H6zM14 3v4h4M9 12h6M9 16h6",
    "book": "M4 4h7a3 3 0 0 1 3 3v14a2 2 0 0 0-2-2H4zM20 4h-6M20 4v15h-6",
    "laptop": "M5 5h14v10H5zM2 19h20",
    "rocket": "M12 3c3 2 5 6 5 10l-2 3H9l-2-3c0-4 2-8 5-10zM12 9h.01M9 16l-2 4M15 16l2 4",
    "pill": "M8.5 3.5a5 5 0 0 1 7 7l-6 6a5 5 0 0 1-7-7zM6 9l7 7",
    "basket": "M3 10h18l-2 10H5zM7 10l4-6M17 10l-4-6M9 14v3M15 14v3",
    "city": "M3 21V9h6v12M9 21V4h7v17M16 21v-9h5v9M5 12h2M5 16h2M11 7h3M11 11h3M11 15h3",
    "train": "M6 3h12a2 2 0 0 1 2 2v10a3 3 0 0 1-3 3H7a3 3 0 0 1-3-3V5a2 2 0 0 1 2-2zM4 11h16M8 21l2-3M16 21l-2-3",
    "bike": "M6 13a4 4 0 1 0 0 8a4 4 0 1 0 0-8M18 13a4 4 0 1 0 0 8a4 4 0 1 0 0-8M6 17l5-8h5l2 8M9 9h4",
    "phone": "M7 2h10v20H7zM11 18h2",
    "moon": "M20 14a8 8 0 1 1-10-10 6 6 0 0 0 10 10z",
    "coin": "M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18M9 9h5a2 2 0 0 1 0 4h-4a2 2 0 0 0 0 4h5M12 6v2M12 16v2",
    "lock": "M5 11h14v10H5zM8 11V7a4 4 0 0 1 8 0v4",
    "code": "M8 7l-5 5 5 5M16 7l5 5-5 5M14 4l-4 16",
    "chip": "M7 7h10v10H7zM10 2v5M14 2v5M10 17v5M14 17v5M2 10h5M2 14h5M17 10h5M17 14h5",
    "gamepad": "M6 8h12a4 4 0 0 1 4 4v1a4 4 0 0 1-7 2l-1-1h-4l-1 1a4 4 0 0 1-7-2v-1a4 4 0 0 1 4-4zM7 11v3M5.5 12.5h3M16 12h.01M18 13h.01",
    "dumbbell": "M3 10v4M6 7v10M18 7v10M21 10v4M6 12h12",
    "suitcase": "M4 8h16v12H4zM9 8V5h6v3M9 8v12M15 8v12",
    "tv": "M3 6h18v12H3zM8 21h8M9 2l3 4 3-4",
    "shirt": "M8 3l-5 3 2 4 3-1v12h8V9l3 1 2-4-5-3c-1 2-2 3-4 3s-3-1-4-3z",
    "cat": "M5 4l3 4h8l3-4v9a7 7 0 0 1-14 0zM9 13h.01M15 13h.01M11 16h2",
    "flower": "M12 9a3 3 0 1 0 0 6a3 3 0 1 0 0-6M12 9V3M12 15v6M9 12H3M21 12h-6M9.8 9.8L6 6M14.2 14.2L18 18M9.8 14.2L6 18M14.2 9.8L18 6",
    "scale": "M12 3v18M5 21h14M4 7h16M7 7l-3 7a3 3 0 0 0 6 0zM17 7l-3 7a3 3 0 0 0 6 0z",
    "pencil": "M4 20l1-5L16 4l4 4L9 19zM14 6l4 4",
    "letters": "M3 18l4-12 4 12M4.5 14h5M14 6h4a3 3 0 0 1 0 6h-4zM14 12h5a3 3 0 0 1 0 6h-5z",
    "wave": "M2 12c2-3 4-3 6 0s4 3 6 0 4-3 6 0",
}

LANG = {  # background gradient, motif colours, accent stripe colours
    "german": {"bg": ("#fff6e8", "#fde7e4"), "ink": ["#1f1f1f", "#c8102e", "#d9a400"], "stripe": ["#1f1f1f", "#c8102e", "#e0ac00"]},
    "english": {"bg": ("#eef3ff", "#fdeef0"), "ink": ["#1e3a8a", "#c8102e", "#2563eb"], "stripe": ["#1e3a8a", "#e5e7eb", "#c8102e"]},
    "spanish": {"bg": ("#fff4e3", "#ffe8dc"), "ink": ["#c2410c", "#d97706", "#a21caf"], "stripe": ["#c60b1e", "#ffc400", "#c60b1e"]},
}

# topic → motifs (by path prefix; the longest matching prefix wins)
TOPICS = {
    "grammar/tenses": ["clock", "hourglass", "arrow"], "grammar/moods": ["bubble", "heart", "question"],
    "grammar/passive": ["loop", "arrows", "gear"], "grammar/verbs": ["gear", "arrow", "loop"],
    "grammar/nouns": ["tag", "box", "letters"], "grammar/cases": ["box", "tag", "arrows"],
    "grammar/adjectives": ["star", "flower", "pencil"], "grammar/pronouns": ["person", "people", "bubble"],
    "grammar/sentences": ["link", "wave", "letters"], "grammar/prepositions": ["pin", "arrow", "compass"],
    "grammar/adverbs": ["compass", "clock", "arrow"], "grammar": ["letters", "book", "pencil"],
    "docs": ["book", "doc", "letters"], "quizzes": ["check", "question", "pencil"], "tests": ["check", "question", "pencil"],
    "everyday": ["bubbles", "clock", "people"], "readings": ["book", "bubble", "pencil"],
    "english/adjectives-and-adverbs": ["star", "flower", "pencil"], "english/easily-confused-words": ["arrows", "question", "cross"],
    "english/nouns-pronouns-and-determiners": ["box", "person", "tag"], "english/prepositions-and-particles": ["pin", "arrow", "compass"],
    "english/using-english": ["bubbles", "people", "letters"], "english/verbs": ["gear", "clock", "arrow"],
    "english/words-sentences-and-clauses": ["link", "letters", "wave"], "english/common-mistakes": ["cross", "check", "pencil"],
    "english": ["letters", "book", "bubble"],
    "spanish/introduction": ["bubbles", "sun", "people"], "spanish/beginner": ["leaf", "letters", "sun"],
    "spanish/intermediate": ["leaf", "tree", "clock"], "spanish/advanced": ["tree", "star", "bubble"],
    "spanish/regional-spanish": ["pin", "sun", "mountain"], "spanish/stories": ["book", "sun", "bubble"],
    "spanish": ["sun", "bubbles", "letters"],
}
# story keywords (in the file name) → motifs
KEYWORDS = [
    ("piso", "house"), ("wg-zimmer", "house"), ("perro", "paw"), ("haustier", "paw"), ("katz", "cat"), ("resfriado", "pill"),
    ("arzt", "pill"), ("papeles", "doc"), ("anmeldung", "doc"), ("mercado", "basket"), ("luz", "bulb"), ("mozo", "cup"),
    ("cafe", "cup"), ("kaffee", "cup"), ("brunch", "cup"), ("entrevista", "briefcase"), ("vorstellung", "briefcase"),
    ("semestre", "book"), ("sprachen", "bubbles"), ("startup", "rocket"), ("teletrabajo", "laptop"), ("homeoffice", "laptop"),
    ("machu", "mountain"), ("karpaten", "mountain"), ("kasbegi", "mountain"), ("camino", "pin"), ("muertos", "flower"),
    ("fallas", "flame"), ("tango", "note"), ("milonga", "note"), ("musik", "note"), ("festival", "note"), ("tapas", "plate"),
    ("tamales", "plate"), ("kueche", "plate"), ("kochen", "plate"), ("comida", "plate"), ("cita", "heart"), ("dating", "heart"),
    ("scrum", "gear"), ("cyber", "lock"), ("ki-im", "chip"), ("detox", "phone"), ("social", "phone"), ("gaming", "gamepad"),
    ("programmieren", "code"), ("kyjiw", "city"), ("lwiw", "city"), ("tiflis", "city"), ("neuanfang", "suitcase"),
    ("reise", "suitcase"), ("gastfreund", "cup"), ("freunde", "people"), ("fitness", "dumbbell"), ("ticket", "train"),
    ("serien", "tv"), ("nachhaltig", "leaf"), ("geld", "coin"), ("fahrrad", "bike"), ("secondhand", "shirt"),
    ("nachtleben", "moon"), ("work-life", "scale"), ("tinto", "cup"), ("quindio", "cup"),
]


def stripe_css(lang):
    """CSS gradient for the thin language-coloured line under the banner."""
    a, b, c = LANG[lang]["stripe"]
    return f"linear-gradient(90deg, {a} 0 33.4%, {b} 33.4% 66.7%, {c} 66.7%)"


def lang_of(rel):
    return "english" if rel.startswith("english/") else "spanish" if rel.startswith("spanish/") else "german"


def motifs(rel):
    stem = rel.rsplit("/", 1)[-1]
    found = [icon for kw, icon in KEYWORDS if kw in stem]
    best = max((k for k in TOPICS if rel == k or rel.startswith(k + "/") or rel.startswith(k + ".")), key=len, default=None)
    base = TOPICS.get(best, ["letters", "book", "bubble"])
    return (found + base)[:4] if found else base


def banner(rel):
    """Inline SVG strip for the page at site path rel."""
    lang = lang_of(rel)
    pal = LANG[lang]
    rnd = random.Random(int(hashlib.sha1(rel.encode()).hexdigest()[:12], 16))
    icons = motifs(rel)
    w, h = 1600, 48
    gid = "bg" + hashlib.sha1(rel.encode()).hexdigest()[:6]
    out = [f'<svg viewBox="0 0 {w} {h}" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg" role="presentation">',
           f'<defs><linearGradient id="{gid}" x1="0" x2="1"><stop offset="0" stop-color="{pal["bg"][0]}"/><stop offset="1" stop-color="{pal["bg"][1]}"/></linearGradient></defs>',
           f'<rect class="bn-bg" width="{w}" height="{h}" fill="url(#{gid})"/>']
    # a soft wave in the language colour
    pts = " ".join(f"{x},{h * 0.62 + math.sin(x / 90 + rnd.random()) * 6:.1f}" for x in range(0, w + 40, 40))
    out.append(f'<polyline points="{pts}" fill="none" stroke="{pal["ink"][1]}" stroke-opacity=".12" stroke-width="10"/>')
    x = rnd.uniform(-10, 30)
    while x < w:
        icon = rnd.choice(icons) if rnd.random() < .85 else icons[0]
        s = rnd.uniform(.9, 1.35)
        y = rnd.uniform(4, h - 24 * s - 4)
        rot = rnd.uniform(-14, 14)
        col = rnd.choice(pal["ink"])
        op = rnd.uniform(.35, .8)
        out.append(f'<path d="{ICONS[icon]}" transform="translate({x:.0f} {y:.0f}) rotate({rot:.0f} 12 12) scale({s:.2f})" '
                   f'fill="none" stroke="{col}" stroke-opacity="{op:.2f}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>')
        x += rnd.uniform(46, 92)
    out.append("</svg>")
    return '<div class="banner" aria-hidden="true">' + "".join(out) + "</div>"
