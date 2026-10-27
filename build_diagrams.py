#!/usr/bin/env python3
"""Draw the 3 Bank AI Platform diagrams as PNGs (Pillow, no network)."""
from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
W, H = 1400, 900
BG = (255, 255, 255)
INK = (20, 20, 20)
BLUE = (27, 94, 168)
GREEN = (27, 140, 80)
ORANGE = (196, 110, 0)
GREY = (90, 90, 90)


def font(size, bold=False):
    return ImageFont.truetype(BOLD if bold else FONT, size)


def wrap(draw, text, fnt, max_w):
    words, lines, cur = text.split(), [], ""
    for word in words:
        trial = f"{cur} {word}".strip()
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def box(draw, x, y, w, h, title, body="", fill=(235, 242, 252), outline=BLUE):
    draw.rounded_rectangle([x, y, x + w, y + h], radius=14,
                           fill=fill, outline=outline, width=3)
    tf, bf = font(26, True), font(21)
    for i, line in enumerate(wrap(draw, title, tf, w - 30)):
        draw.text((x + 15, y + 12 + i * 30), line, font=tf, fill=INK)
    ty = y + 12 + len(wrap(draw, title, tf, w - 30)) * 30 + 6
    for i, line in enumerate(wrap(draw, body, bf, w - 30)):
        draw.text((x + 15, ty + i * 26), line, font=bf, fill=(60, 60, 60))


def arrow(draw, x1, y1, x2, y2, label=""):
    draw.line([x1, y1, x2, y2], fill=INK, width=4)
    # Arrow head pointing toward (x2, y2): assume axis-aligned.
    if x2 > x1:
        draw.polygon([(x2, y2), (x2 - 16, y2 - 9), (x2 - 16, y2 + 9)], fill=INK)
    elif x2 < x1:
        draw.polygon([(x2, y2), (x2 + 16, y2 - 9), (x2 + 16, y2 + 9)], fill=INK)
    elif y2 > y1:
        draw.polygon([(x2, y2), (x2 - 9, y2 - 16), (x2 + 9, y2 - 16)], fill=INK)
    else:
        draw.polygon([(x2, y2), (x2 - 9, y2 + 16), (x2 + 9, y2 + 16)], fill=INK)
    if label:
        mx, my = (x1 + x2) // 2, (y1 + y2) // 2
        draw.text((mx + 8, my - 26), label, font=font(20, True), fill=GREY)


def title_bar(draw, text):
    draw.text((40, 24), text, font=font(36, True), fill=INK)


def save(img, path):
    img.save(path)
    print("saved", path)


# ---------------- 1. Architecture ----------------
img = Image.new("RGB", (W, 1000), BG)
d = ImageDraw.Draw(img)
title_bar(d, "Bank AI Platform - System Architecture")
box(d, 40, 110, 380, 200, "React Frontend (:5173)",
    "Vite + React: account list, detail, deposit / withdraw / transfer forms, AI assistant panel. Logs in with the demo user.",
    fill=(255, 243, 224), outline=ORANGE)
box(d, 500, 110, 420, 200, "AI Service (Python, :8081)",
    "Agent loop, tool registry, TF-IDF RAG index, Vertex AI provider interface.",
    fill=(232, 245, 233), outline=GREEN)
box(d, 1000, 110, 360, 200, "Banking Service (Java, :8080)",
    "Spring Boot REST APIs, Spring Security (HTTP Basic), JPA entities, audit trail.",
    fill=(235, 242, 252), outline=BLUE)
box(d, 40, 420, 380, 180, "Event Publishers",
    "Local publisher by default (in-memory + log). Pub/Sub REST publisher when configured.",
    fill=(235, 242, 252), outline=BLUE)
box(d, 500, 420, 420, 180, "Bank Documents",
    "Fee schedule, account policies, FAQs, loan basics. Ingested into the TF-IDF index.",
    fill=(232, 245, 233), outline=GREEN)
box(d, 1000, 420, 360, 180, "MySQL Database",
    "accounts + transactions tables via Spring Data JPA. H2 is used in tests only.",
    fill=(235, 242, 252), outline=BLUE)
box(d, 40, 650, 380, 180, "Docker + GitHub Actions",
    "Dockerfile per service, docker-compose (incl. MySQL), CI workflow: Maven tests + Python tests.",
    fill=(255, 243, 224), outline=ORANGE)
box(d, 500, 650, 860, 180, "Security + testing",
    "Banking API: HTTP Basic auth (local demo user, BCrypt-hashed). AI service calls it with Basic auth from env vars. "
    "Tests: JPA repository tests, MockMvc security tests (401 / 200), Python auth-header tests.",
    fill=(255, 243, 224), outline=ORANGE)
arrow(d, 420, 210, 500, 210)
arrow(d, 920, 210, 1000, 210)
arrow(d, 710, 310, 710, 420, "retrieve")
arrow(d, 1180, 310, 1180, 420, "JPA")
save(img, "docs/architecture.png")

# ---------------- 2. RAG pipeline ----------------
img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)
title_bar(d, "Bank AI Platform - RAG Pipeline (offline, pure Python)")
steps = [
    ("1. Bank documents", "Fee schedule, policies, FAQs, loan basics (plain text)."),
    ("2. Parse + chunk", "Split on sentence boundaries, max 800 chars per chunk."),
    ("3. TF-IDF index", "Each chunk becomes a term vector (IDF-weighted). No model download."),
    ("4. Question", "User asks, e.g. 'What is the overdraft fee?'"),
    ("5. Retrieve top-3", "Cosine similarity ranks chunks; weak matches are dropped."),
    ("6. Agent + tools", "Live data via banking tools; docs for policies and fees."),
    ("7. Answer", "Composed by the local provider, or Vertex AI when configured."),
]
y = 110
for i, (t, b) in enumerate(steps):
    x = 120 if i % 2 == 0 else 720
    if i > 0:
        px = 120 if (i - 1) % 2 == 0 else 720
        arrow(d, px + 300, y - 40 + 0, x + 300, y, "")
    box(d, x, y, 560, 150, t, b, fill=(232, 245, 233) if i < 3 else (235, 242, 252),
        outline=GREEN if i < 3 else BLUE)
    y += 0  # layout is two columns; advance rows every two steps
    if i % 2 == 1:
        y += 0
# Simpler vertical flow: redraw as a clean vertical chain instead.
img = Image.new("RGB", (W, 1000), BG)
d = ImageDraw.Draw(img)
title_bar(d, "Bank AI Platform - RAG Pipeline (offline, pure Python)")
y = 100
for t, b in steps:
    box(d, 320, y, 760, 108, t, b, fill=(232, 245, 233), outline=GREEN)
    if t != steps[-1][0]:
        arrow(d, 700, y + 108, 700, y + 134, "")
    y += 134
save(img, "docs/rag-pipeline.png")

# ---------------- 3. Transaction / event flow ----------------
img = Image.new("RGB", (W, 1000), BG)
d = ImageDraw.Draw(img)
title_bar(d, "Bank AI Platform - Transaction & Event Flow")
flow = [
    ("Client request", "POST /api/accounts/{id}/deposit (or withdraw / transfer)."),
    ("Validation", "Amount must be positive; account must exist; no overdraft allowed."),
    ("Balance update", "Balance changes inside a lock; transfers lock both accounts in order."),
    ("Audit trail", "An immutable Transaction row is written: type, amount, balance after."),
    ("Event publish", "A TransactionEvent goes to the local publisher (or Pub/Sub if configured)."),
    ("Response", "The updated account is returned with the new balance."),
]
y = 100
for i, (t, b) in enumerate(flow):
    fill = (255, 243, 224) if i in (1, 3) else (235, 242, 252)
    outline = ORANGE if i in (1, 3) else BLUE
    box(d, 320, y, 760, 108, f"{i + 1}. {t}", b, fill=fill, outline=outline)
    if i < len(flow) - 1:
        arrow(d, 700, y + 108, 700, y + 134, "")
    y += 134
save(img, "docs/transaction-flow.png")
print("done")
