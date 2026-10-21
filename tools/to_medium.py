"""Split the article Markdown into Medium-paste segments: HTML chunks and image slots."""
import json, re, sys
import markdown

src, out = sys.argv[1], sys.argv[2]
text = open(src).read()

# Title and subtitle are typed into Medium's title fields separately.
lines = text.split("\n")
title = lines[0].lstrip("# ").strip()
subtitle = lines[2].lstrip("# ").strip()
body = "\n".join(lines[3:])
body = body.replace("*LLMs for Backend Engineers · Part 1 · 9 min read*", "*LLMs for Backend Engineers · Part 1*")
body = body.replace(
    "[COLAB LINK: upload `attention-fuzzy-lookup.ipynb` to GitHub and paste the Colab URL here]",
    "[NOTEBOOK LINK — to be added]")
body = body.replace("\n  *[In Medium, paste this link on its own line and press Enter to embed the video.]*", "")

# Image markers: "> **[FIGURE n: `file`]**\n> *caption*"  or FEATURED IMAGE
pat = re.compile(r"> \*\*\[(?:FIGURE \d+|FEATURED IMAGE): `([^`]+)`\]\*\*\n> \*(.+?)\*\n", re.S)
segments, pos = [], 0
for m in pat.finditer(body):
    segments.append({"type": "html", "md": body[pos:m.start()]})
    segments.append({"type": "image", "file": m.group(1), "caption": m.group(2).strip()})
    pos = m.end()
segments.append({"type": "html", "md": body[pos:]})

md = markdown.Markdown(extensions=["fenced_code"])
result = []
for s in segments:
    if s["type"] == "html":
        chunk = s["md"].strip()
        chunk = re.sub(r"^---\s*$", "", chunk, flags=re.M)  # Medium separators are added by hand if wanted
        if not chunk.strip():
            continue
        html = md.reset().convert(chunk)
        # Medium has two heading sizes: h3 (big) and h4 (small).
        html = html.replace("<h3>", "<h4>").replace("</h3>", "</h4>")
        html = html.replace("<h2>", "<h3>").replace("</h2>", "</h3>")
        result.append({"type": "html", "html": html})
    else:
        result.append(s)
json.dump({"title": title, "subtitle": subtitle, "segments": result}, open(out, "w"), indent=1)
print(title, "|", subtitle)
for i, s in enumerate(result):
    print(i, s["type"], s.get("file", ""), len(s.get("html", "")))
