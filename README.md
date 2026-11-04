# German library

A static website with reference docs, 40 B1 reading texts and quizzes for learning German (A2–B1+), explained in English with Ukrainian comparisons. A second half, **English grammar** (`english/`), covers British English grammar in eight areas, each ending with a quiz. A switch in the top bar moves between the two halves.

Plain HTML, no build step: open `index.html`, or host the folder as-is (GitHub Pages serves `main` directly; Cloudflare Pages: framework preset "None", build command empty, output directory `/`).

The pages are generated. Edit the sources and rebuild instead of editing the HTML by hand.

## English grammar

Sources are Markdown files in `english-src/` (one folder per area: `_index.md`, one `.md` per page, `quiz.json`). Rebuild with:

```
pip install markdown
python3 tools/build_section.py
```

This regenerates `english/` and then runs `tools/site_switch.py`, which adds the German / English switch to the app bar of every page (safe to run again on its own after regenerating the German pages).
