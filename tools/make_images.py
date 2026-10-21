"""Generate the article images as SVG-in-HTML and render them with headless Chrome."""
import math, os, subprocess, sys

OUT = sys.argv[1]
WORK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frames")
os.makedirs(OUT, exist_ok=True)
os.makedirs(WORK, exist_ok=True)
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

SURF = "#fcfcfb"; INK = "#0b0b0b"; INK2 = "#52514e"; MUTED = "#8a8983"; LINE = "#e4e2dc"
BLUE = "#2a78d6"; ORANGE = "#eb6834"; AQUA = "#1baf7a"
BLUE_T = "#eaf2fc"; ORANGE_T = "#fdeee7"; AQUA_T = "#e6f6f0"
SANS = "-apple-system, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif"
MONO = "'SF Mono', Menlo, Monaco, monospace"
SEQ = ["#f4f3ef", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
FOOT = "LLMs for Backend Engineers · Part 1"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def t(x, y, s, size=24, fill=INK, weight=400, anchor="start", font=SANS, extra=""):
    return (f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}" fill="{fill}" '
            f'font-weight="{weight}" text-anchor="{anchor}" {extra}>{esc(s)}</text>')


def box(x, y, w, h, fill="#fff", stroke=LINE, sw=2, r=14):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'


def header(title, sub, W):
    return t(80, 100, title, 52, weight=700) + t(80, 148, sub, 26, INK2)


def footer(W, H):
    return t(80, H - 40, FOOT, 20, MUTED)


def render(name, svg, W, H, folder=OUT):
    html = (f'<!doctype html><html><head><meta charset="utf-8"><style>html,body{{margin:0;padding:0;'
            f'background:{SURF}}}svg{{display:block}}</style></head><body>'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
            f'<rect width="{W}" height="{H}" fill="{SURF}"/>{svg}</svg></body></html>')
    hp = os.path.join(WORK, name + ".html")
    with open(hp, "w") as f:
        f.write(html)
    png = os.path.join(folder, name + ".png")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    f"--user-data-dir={os.path.join(WORK, 'chrome-profile')}",
                    f"--window-size={W},{H}", "--force-device-scale-factor=1",
                    f"--screenshot={png}", "file://" + hp],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return png


def seq_color(v):
    v = max(0.0, min(1.0, v))
    pos = v * (len(SEQ) - 1)
    i = min(int(pos), len(SEQ) - 2)
    f = pos - i
    a = [int(SEQ[i][k:k + 2], 16) for k in (1, 3, 5)]
    b = [int(SEQ[i + 1][k:k + 2], 16) for k in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(round(a[j] + (b[j] - a[j]) * f) for j in range(3))


# ---------------------------------------------------------------- 1. hero
def fan_panel(cx, weights, labels, colors, query, out_main, out_sub, show_pct=True, lw_scale=30):
    """Query box on top, three rows, merged output below. Line widths follow weights."""
    s = ""
    qy, ry, oy = 210, 400, 650
    xs = [cx - 230, cx, cx + 230]
    for i, x in enumerate(xs):
        w = weights[i]
        width = max(1.5, w * lw_scale)
        col = colors[i] if w > 0 else "#cfcdc6"
        dash = '' if w > 0 else 'stroke-dasharray="6 8"'
        s += f'<path d="M{cx},{qy + 70} C{cx},{qy + 140} {x},{ry - 70} {x},{ry}" stroke="{col}" stroke-width="{width}" fill="none" stroke-linecap="round" {dash}/>'
        if w > 0:
            s += f'<path d="M{x},{ry + 110} C{x},{ry + 180} {cx},{oy - 70} {cx},{oy}" stroke="{col}" stroke-width="{width}" fill="none" stroke-linecap="round"/>'
    for i, x in enumerate(xs):
        w = weights[i]
        active = w > 0
        s += box(x - 100, ry, 200, 110, "#fff", colors[i] if active else "#d6d4cd", 3 if active else 2)
        s += t(x, ry + 48, labels[i][0], 28, INK if active else MUTED, 700, "middle")
        s += t(x, ry + 84, labels[i][1], 20, INK2 if active else MUTED, 400, "middle", MONO)
        if show_pct:
            mx, my = (cx + x) / 2, qy + 125
            txt = f"{w * 100:.0f}%" if active else "no match"
            pw = 96 if active else 120
            s += box(mx - pw / 2, my - 22, pw, 44, SURF, LINE, 2, 22)
            s += t(mx, my + 9, txt, 22 if active else 18, INK if active else MUTED, 700 if active else 400, "middle")
    s += box(cx - 170, qy, 340, 70, BLUE_T, BLUE, 3, 35)
    s += t(cx, qy + 45, query, 26, INK, 600, "middle", MONO)
    s += box(cx - 330, oy, 660, 100, INK, INK, 0, 16)
    s += t(cx, oy + 46, out_main, 25, "#fff", 700, "middle")
    s += t(cx, oy + 80, out_sub, 19, "#c3c2b7", 400, "middle")
    return s


def hero():
    W, H = 1600, 900
    s = header("A SELECT vs. Attention", "A database returns the row that matches. Attention blends every row by how well it matches.", W)
    s += f'<line x1="800" y1="200" x2="800" y2="800" stroke="{LINE}" stroke-width="2"/>'
    s += t(400, 196, "EXACT LOOKUP", 18, INK2, 700, "middle", extra='letter-spacing="3"')
    s += t(1200, 196, "ATTENTION  (FUZZY LOOKUP)", 18, INK2, 700, "middle", extra='letter-spacing="3"')
    grey = "#d6d4cd"
    s += fan_panel(400, [0, 1, 0], [("france", "Paris"), ("japan", "Tokyo"), ("india", "New Delhi")],
                   [grey, BLUE, grey], "key = 'japan'", "Tokyo", "exactly one row — or a KeyError", lw_scale=10)
    s += fan_panel(1200, [0.80, 0.08, 0.13], [("order", "key → value"), ("customer", "key → value"), ("returned", "key → value")],
                   [ORANGE, ORANGE, ORANGE], 'query: "it"', "80% order · 8% customer · 13% returned",
                   "a weighted blend of every row", lw_scale=30)
    s += footer(W, H)
    return render("01-hero-select-vs-attention", s, W, H)


# ---------------------------------------------------------------- 2. QKV mapping
def qkv():
    W, H = 1600, 900
    s = header("Q, K and V are exactly what they sound like", "Every token produces all three. Map them to a query you have written a thousand times.", W)
    rows = [("Q", "Query", "“What am I looking for?”", "WHERE …", "the filter you search with", BLUE, BLUE_T),
            ("K", "Key", "“Here's how to find me.”", "INDEX ON …", "the column you search on", AQUA, AQUA_T),
            ("V", "Value", "“If you pick me, here's what I hand over.”", "SELECT name, email …", "the payload you get back", ORANGE, ORANGE_T)]
    for i, (L, name, quote, sql, sqlsub, col, tint) in enumerate(rows):
        y = 220 + i * 190
        s += box(120, y, 600, 150, "#fff", col, 3)
        s += f'<circle cx="195" cy="{y + 75}" r="44" fill="{tint}" stroke="{col}" stroke-width="3"/>'
        s += t(195, y + 90, L, 42, INK, 800, "middle")
        s += t(270, y + 64, name, 32, INK, 700)
        s += t(270, y + 106, quote, 22, INK2)
        s += t(800, y + 88, "=", 48, MUTED, 700, "middle")
        s += box(880, y, 600, 150, tint, tint, 0)
        s += t(920, y + 70, sql, 32, INK, 600, font=MONO)
        s += t(920, y + 110, sqlsub, 22, INK2)
    s += footer(W, H)
    return render("02-qkv-equals-sql", s, W, H)


# ---------------------------------------------------------------- 3. score -> softmax
def softmax_img():
    W, H = 1600, 900
    raw = [4.0, 0.0, 0.8]
    scaled = [r / math.sqrt(3) for r in raw]
    ex = [math.exp(v) for v in scaled]
    w = [e / sum(ex) for e in ex]
    names = ["order", "customer", "returned"]
    cols = [BLUE, ORANGE, AQUA]
    s = header("From similarity scores to a traffic split", "How the query “it” decides how much of each word to pull in.", W)
    heads = [(120, "TOKEN"), (420, "① DOT PRODUCT"), (690, "② SCALE ÷ √3"), (960, "③ SOFTMAX → WEIGHT")]
    for x, h in heads:
        s += t(x, 240, h, 18, INK2, 700, extra='letter-spacing="2"')
    s += f'<line x1="120" y1="262" x2="1480" y2="262" stroke="{LINE}" stroke-width="2"/>'
    barmax = 440
    for i in range(3):
        y = 330 + i * 110
        s += f'<circle cx="134" cy="{y - 9}" r="9" fill="{cols[i]}"/>'
        s += t(156, y, names[i], 32, INK, 700)
        s += t(420, y, f"{raw[i]:.1f}", 34, INK, 600, font=MONO)
        s += t(690, y, f"{scaled[i]:.2f}", 34, INK, 600, font=MONO)
        bw = max(6, w[i] * barmax)
        s += f'<rect x="960" y="{y - 32}" width="{bw}" height="40" rx="4" fill="{cols[i]}"/>'
        s += t(960 + bw + 16, y, f"{w[i] * 100:.1f}%", 30, INK, 700)
    for x in (600, 870):
        s += t(x - 40, 440, "→", 40, MUTED, 400, "middle")
    # stacked traffic split
    y0 = 680
    s += t(120, y0 - 24, "Same weights as a 100% traffic split — like a weighted load balancer", 22, INK2, 600)
    x = 120
    total = 1360
    for i in range(3):
        seg = w[i] * total - (2 if i < 2 else 0)
        s += f'<rect x="{x}" y="{y0}" width="{seg}" height="64" rx="4" fill="{cols[i]}"/>'
        if seg > 260:
            s += t(x + 20, y0 + 42, f"{names[i]} {w[i] * 100:.0f}%", 26, "#fff", 700)
        else:
            s += t(x + seg / 2, y0 + 100, f"{names[i]} {w[i] * 100:.0f}%", 20, INK, 600, "middle")
        x += seg + 2
    s += footer(W, H)
    return render("03-scores-to-softmax", s, W, H)


# ---------------------------------------------------------------- 4. animated fan-out
def gif():
    from PIL import Image
    W, H = 1200, 820
    final = [0.7956, 0.0790, 0.1254]
    frames = []
    steps = 22
    for k in range(steps + 1):
        p = k / steps
        p = 1 - (1 - p) ** 3  # ease out
        w = [1 / 3 + (f - 1 / 3) * p for f in final]
        s = t(600, 70, "The query “it” scores every word, then blends them", 34, INK, 700, "middle")
        s += t(600, 112, "weights start equal, then attention shifts to the best match", 22, INK2, 400, "middle")
        blend = " + ".join(f"{w[i] * 100:.0f}% {n}" for i, n in enumerate(["order", "customer", "returned"]))
        g = fan_panel(600, w, [("order", "key → value"), ("customer", "key → value"), ("returned", "key → value")],
                      [ORANGE] * 3, 'query: "it"', blend, "the token “it” now carries the order's information", lw_scale=30)
        s += f'<g transform="translate(0,-60)">{g}</g>'
        s += t(600, H - 28, FOOT, 18, MUTED, 400, "middle")
        frames.append(render(f"gif-{k:02d}", s, W, H, folder=WORK))
    imgs = [Image.open(f).convert("RGB").quantize(colors=128, method=Image.Quantize.MEDIANCUT) for f in frames]
    durs = [900] + [70] * (steps - 1) + [2600]
    gp = os.path.join(OUT, "04-attention-fan-out.gif")
    imgs[0].save(gp, save_all=True, append_images=imgs[1:], duration=durs, loop=0, optimize=True)
    return gp


# ---------------------------------------------------------------- 5. causal self-attention heatmap
TOK = ["The", "customer", "returned", "the", "order", "because", "it", "arrived", "damaged"]


def causal_matrix():
    n = len(TOK)
    M = []
    for i in range(n):
        row = [0.0] * n
        for j in range(i + 1):
            row[j] = 0.15
        row[i] += 0.35
        if i > 0:
            row[i - 1] += 0.2
        if i == 2: row[1] += 0.6           # returned -> customer
        if i == 4: row[2] += 0.3           # order -> returned
        if i == 6: row = [0.02, 0.10, 0.08, 0.02, 1.6, 0.05, 0.12, 0, 0]  # it -> order
        if i == 7: row[6] += 0.5; row[4] += 0.5
        if i == 8: row[4] += 0.6; row[7] += 0.3
        s = sum(row)
        M.append([v / s for v in row])
    return M


def heatmap(x0, y0, M, cell, rowlabels=True, collabels=True, font=20, highlight_row=None, mask_label=False):
    n = len(M)
    s = '<defs><pattern id="hatch" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">' \
        f'<rect width="10" height="10" fill="#f0efec"/><line x1="0" y1="0" x2="0" y2="10" stroke="#dcdad3" stroke-width="3"/></pattern></defs>'
    for i in range(n):
        for j in range(n):
            x, y = x0 + j * cell, y0 + i * cell
            if j > i:
                s += f'<rect x="{x + 1}" y="{y + 1}" width="{cell - 2}" height="{cell - 2}" rx="3" fill="url(#hatch)"/>'
            else:
                v = M[i][j]
                s += f'<rect x="{x + 1}" y="{y + 1}" width="{cell - 2}" height="{cell - 2}" rx="3" fill="{seq_color(min(1, v / 0.75))}"/>'
                if cell >= 56 and v >= 0.2:
                    s += t(x + cell / 2, y + cell / 2 + 7, f"{v * 100:.0f}", 18, "#fff" if v > 0.3 else INK, 700, "middle")
        if rowlabels:
            hl = (i == highlight_row)
            s += t(x0 - 14, y0 + i * cell + cell / 2 + 7, TOK[i], font, INK if hl else INK2, 700 if hl else 400, "end")
    if collabels:
        for j in range(n):
            cx, cy = x0 + j * cell + cell / 2 + 6, y0 - 12
            s += t(cx, cy, TOK[j], font - 2, INK2, 400, "start", extra=f'transform="rotate(-55 {cx} {cy})"')
    if highlight_row is not None:
        y = y0 + highlight_row * cell
        s += f'<rect x="{x0 - 2}" y="{y - 1}" width="{cell * n + 4}" height="{cell + 2}" rx="5" fill="none" stroke="{ORANGE}" stroke-width="4"/>'
    return s


def selfattn():
    W, H = 1600, 1000
    M = causal_matrix()
    s = header("Self-attention is a self-join — with a causal mask",
               "Each row is one token's query. Each cell is how much it pulls from that column. Every row sums to 100%.", W)
    cell = 62
    x0, y0 = 300, 300
    s += heatmap(x0, y0, M, cell, font=21, highlight_row=6)
    s += t(x0 + cell * 9 / 2, y0 + cell * 9 + 50, "← the keys it looks at (columns) →", 20, INK2, 400, "middle")
    # notes
    nx = 980
    s += t(nx, 360, "Row “it”", 30, INK, 700)
    s += t(nx, 400, "80% of its attention goes to “order”.", 24, INK2)
    s += t(nx, 434, "That's how the model resolves the pronoun.", 24, INK2)
    s += f'<rect x="{nx}" y="490" width="40" height="40" rx="3" fill="url(#hatch)"/>'
    s += t(nx + 60, 520, "Masked: the future", 28, INK, 700)
    s += t(nx, 568, "A token can't attend to words after it.", 24, INK2)
    s += t(nx, 606, "WHERE b.position <= a.position", 24, INK, 600, font=MONO)
    # legend ramp
    ly = 690
    s += t(nx, ly, "Attention weight", 22, INK2, 600)
    for k in range(10):
        s += f'<rect x="{nx + k * 40}" y="{ly + 16}" width="38" height="22" rx="2" fill="{seq_color(k / 9)}"/>'
    s += t(nx, ly + 66, "0%", 18, INK2)
    s += t(nx + 398, ly + 66, "75%+", 18, INK2, 400, "end")
    s += t(nx, 830, "Illustrative weights for a toy example —", 20, MUTED)
    s += t(nx, 858, "real models learn these during training.", 20, MUTED)
    s += footer(W, H)
    return render("05-self-attention-causal-mask", s, W, H)


# ---------------------------------------------------------------- 6. multi-head
def head_matrix(kind):
    n = len(TOK)
    M = []
    for i in range(n):
        row = [0.04] * (i + 1) + [0] * (n - i - 1)
        if kind == "prev":
            row[max(0, i - 1)] += 1.0
        elif kind == "coref":
            row[i] += 0.5
            if i == 6: row[4] += 2.0
            if i == 7: row[4] += 1.0
            if i == 8: row[4] += 1.0
        elif kind == "verb":
            row[i] += 0.5
            if i == 2: row[1] += 1.5
            if i == 7: row[4] += 1.2
            if i == 8: row[4] += 0.8
            if i == 4: row[2] += 0.8
        elif kind == "start":
            row[0] += 1.0
            row[i] += 0.3
        s = sum(row)
        M.append([v / s for v in row])
    return M


def multihead():
    W, H = 1600, 900
    s = header("Multi-head attention = many indexes on one table",
               "Each head learns its own way to look things up. Same sentence, different access paths.", W)
    heads = [("prev", "INDEX prev_word", "looks at the word before"),
             ("coref", "INDEX coreference", "“it” → “order”"),
             ("verb", "INDEX verb_subject", "verbs → who did it"),
             ("start", "INDEX sentence_start", "anchors on the first word")]
    cell = 30
    for k, (kind, name, desc) in enumerate(heads):
        x0 = 210 + k * 350
        y0 = 360
        s += t(x0 - 90, 250, f"Head {k + 1}", 20, INK2, 700, extra='letter-spacing="2"')
        s += t(x0 - 90, 284, name, 22, INK, 700, font=MONO)
        s += heatmap(x0, y0, head_matrix(kind), cell, rowlabels=(k == 0), collabels=True, font=15)
        s += t(x0 - 90, y0 + cell * 9 + 44, desc, 21, INK2)
    s += t(80, 780, "Outputs from every head are concatenated and mixed back together — then the whole block repeats, layer after layer.", 22, INK2)
    s += t(80, 808, "Illustrative patterns; real heads are learned and messier.", 18, MUTED)
    s += footer(W, H)
    return render("06-multi-head-indexes", s, W, H)


# ---------------------------------------------------------------- 7. O(n^2) cost
def cost():
    W, H = 1600, 900
    data = [("1K", 1e3), ("8K", 8e3), ("32K", 32e3), ("128K", 128e3), ("1M", 1e6)]
    labels = ["1 million", "64 million", "1 billion", "16.4 billion", "1 trillion"]
    s = header("Double the context, quadruple the work",
               "Attention scores computed for one head in one layer: every token × every token (n²).", W)
    x0, x1, y0, y1 = 220, 1480, 250, 720  # plot area; y1 is baseline
    lo, hi = 5, 12.5  # log10 range
    def ypos(v): return y1 - (math.log10(v) - lo) / (hi - lo) * (y1 - y0)
    for e in range(6, 13, 2):
        y = ypos(10 ** e)
        s += f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="{LINE}" stroke-width="1.5"/>'
        s += t(x0 - 16, y + 7, {6: "1M", 8: "100M", 10: "10B", 12: "1T"}[e], 20, MUTED, 400, "end")
    s += f'<line x1="{x0}" y1="{y1}" x2="{x1}" y2="{y1}" stroke="{INK2}" stroke-width="2"/>'
    s += t(x0 - 16, y0 - 30, "scores (log scale)", 18, MUTED, 400, "start")
    slot = (x1 - x0) / len(data)
    bw = 120
    for i, (name, n) in enumerate(data):
        v = n * n
        cx = x0 + slot * i + slot / 2
        y = ypos(v)
        s += f'<path d="M{cx - bw / 2},{y1} V{y + 4} a4,4 0 0 1 4,-4 H{cx + bw / 2 - 4} a4,4 0 0 1 4,4 V{y1} Z" fill="{BLUE}"/>'
        s += t(cx, y - 16, labels[i], 26, INK, 700, "middle")
        s += t(cx, y1 + 40, name + " tokens", 22, INK2, 600, "middle")
    s += t(80, 805, "Multiply by every head and every layer. Your worst self-join report query — on every single request.", 22, INK2)
    s += footer(W, H + 0)
    return render("07-attention-cost-n-squared", s, W, H)


# ---------------------------------------------------------------- 8. cheat sheet
def cheatsheet():
    W, H = 1600, 1260
    rows = [("Query (Q)", "your WHERE clause"), ("Key (K)", "the index"), ("Value (V)", "the row you get back"),
            ("Dot product", "the similarity score"), ("Softmax", "a traffic split that sums to 100%"),
            ("Self-attention", "a self-join on the sentence"), ("Causal mask", "WHERE b.position <= a.position"),
            ("Multi-head", "multiple indexes on the same table"), ("The cost", "a cross join — O(n²)")]
    s = header("Attention, translated for backend engineers", "Save this. Every concept maps to something you already know.", W)
    s += t(120, 240, "IN THE PAPER", 18, INK2, 700, extra='letter-spacing="3"')
    s += t(700, 240, "IN YOUR DATABASE", 18, INK2, 700, extra='letter-spacing="3"')
    for i, (a, b) in enumerate(rows):
        y = 270 + i * 92
        fill = "#fff" if i % 2 == 0 else "#f6f5f1"
        s += box(100, y, 1400, 80, fill, fill, 0, 10)
        s += t(130, y + 52, a, 30, INK, 700)
        mono = b.startswith("WHERE")
        s += t(700, y + 52, b, 28 if not mono else 26, INK, 500, font=MONO if mono else SANS)
    s += t(800, 1170, "A database asks “which row is exactly this?”  Attention asks “how much is each row like this?”", 24, INK2, 600, "middle")
    s += t(80, H - 30, FOOT, 20, MUTED)
    return render("08-cheat-sheet", s, W, H)


if __name__ == "__main__":
    which = sys.argv[2:] or ["hero", "qkv", "softmax_img", "selfattn", "multihead", "cost", "cheatsheet", "gif"]
    for name in which:
        print(globals()[name]())
