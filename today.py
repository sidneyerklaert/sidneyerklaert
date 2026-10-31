#!/usr/bin/env python3
"""
Baut dark_mode.svg und light_mode.svg für das GitHub-Profil von sidneyerklaert
im neofetch-Stil (ASCII-Porträt links, Systeminfo-Liste rechts).

Design-Idee inspiriert von Andrew Grant (https://github.com/Andrew6rant/Andrew6rant).
Sein Repo hat keine Lizenz, deshalb ist dieser Code eine eigenständige
Neuimplementierung und übernimmt keinen Code von dort.

Nutzung:
    ACCESS_TOKEN=... USER_NAME=sidneyerklaert python today.py   # Stats live holen
    python today.py --offline                                  # nur aus cache/stats.json rendern

Benötigt nur die Python-Standardbibliothek.
"""
import datetime as dt
import hashlib
import html
import json
import os
import sys
import urllib.request

# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------

USER_NAME = os.environ.get("USER_NAME", "sidneyerklaert")

# Solange PLACEHOLDER_BIRTHDATE=True ist, wird nur das Alter in Jahren angezeigt.
BIRTHDATE = dt.date(1986, 10, 29)
PLACEHOLDER_BIRTHDATE = False

TITLE = "sidney@erklaert.ki"
WIDTH = 60           # Zeichen pro Zeile in der rechten Spalte
X_ASCII = 15
PORTRAIT_COLS = 44   # Breite des ASCII-Porträts (muss zu ascii.txt passen)
CHAR_W = 9.6
X_INFO = round(X_ASCII + PORTRAIT_COLS * CHAR_W + 15)
Y_START, LINE_H = 30, 20
SVG_W = round(X_INFO + WIDTH * CHAR_W + 25)

# Zeilen der rechten Spalte. None = Leerzeile mit Punkt, ("rule", titel) = Abschnitt,
# ("blank",) = komplett leer, ("stats",) = GitHub-Stats-Block.
# Schlüssel mit "." werden als Key.Subkey eingefärbt.
ROWS = [
    ("rule", TITLE),
    ("OS", "macOS, Windows, iOS"),
    ("Uptime", "{uptime}"),
    ("Host", "Head of AI @ Nothelle"),
    ("Kernel", "KOSMOS"),
    ("Toolchain", "Claude Code, Codex, Cursor, Ollama"),
    None,
    ("Expertise.AI", "Machine Learning, Deep Learning"),
    ("Expertise.GenAI", "LLMs, Generative AI, RAG, Voice Agents"),
    ("Expertise.Agentic", "Agentic Coding, Agentic Marketing"),
    ("Expertise.Agents", "Multi-Agent-Systeme, Agentic Workflows"),
    ("Expertise.Automation", "Prozessautomatisierung, Chatbots"),
    ("Leadership", "AI Strategy, AI Governance, Enablement"),
    ("Models.Benchmarks", "Artificial Analysis"),
    None,
    ("Languages.Programming", "TypeScript, Python, Swift, SQL"),
    ("Languages.Web", "JavaScript, HTML, CSS, Next.js"),
    ("Languages.Automation", "n8n, Webhooks, APIs, MCP, Docker"),
    ("Languages.Real", "Deutsch, English, Turkish"),
    None,
    ("Hobbies.Software", "Lokale LLMs, MCP-Server, Motion Design"),
    ("Hobbies.Content", "KI verständlich erklären"),
    ("blank",),
    ("rule", "- Contact"),
    ("YouTube", "@sidneyerklaertki"),
    ("Instagram", "@sidneyerklaert.ki"),
    ("TikTok", "@sidneyerklaert.ki"),
    ("X", "@sidneyerklaert"),
    ("Threads", "@sidneyerklaert.ki"),
    ("LinkedIn", "Sidney Bora Neudeck"),
    ("GitHub", "sidneyerklaert"),
    ("blank",),
    ("rule", "- GitHub Stats"),
    ("stats",),
]

THEMES = {
    "dark_mode.svg": dict(bg="#161b22", text="#c9d1d9", key="#ffa657", value="#a5d6ff",
                          cc="#616e7f", add="#3fb950", dele="#f85149"),
    "light_mode.svg": dict(bg="#f6f8fa", text="#24292f", key="#953800", value="#0a3069",
                           cc="#c2cfde", add="#1a7f37", dele="#cf222e"),
}

HERE = os.path.dirname(os.path.abspath(__file__))
STATS_FILE = os.path.join(HERE, "cache", "stats.json")
LOC_CACHE = os.path.join(HERE, "cache", "loc.json")

# ---------------------------------------------------------------------------
# Uptime
# ---------------------------------------------------------------------------


def uptime(today=None):
    today = today or dt.date.today()
    b = BIRTHDATE
    years = today.year - b.year - ((today.month, today.day) < (b.month, b.day))
    if PLACEHOLDER_BIRTHDATE:
        return f"{years} Jahre"
    months = (today.year - b.year) * 12 + today.month - b.month
    if today.day < b.day:
        months -= 1
    months %= 12
    anchor_m = today.month if today.day >= b.day else today.month - 1
    anchor_y = today.year
    if anchor_m == 0:
        anchor_m, anchor_y = 12, anchor_y - 1
    try:
        anchor = dt.date(anchor_y, anchor_m, b.day)
    except ValueError:  # z.B. 31. in kurzem Monat
        anchor = dt.date(anchor_y, anchor_m, 28)
    days = (today - anchor).days

    def p(n, one, many):
        return f"{n} {one if n == 1 else many}"
    s = f"{p(years, 'Jahr', 'Jahre')}, {p(months, 'Monat', 'Monate')}, {p(days, 'Tag', 'Tage')}"
    return s + (" 🎂" if months == 0 and days == 0 else "")

# ---------------------------------------------------------------------------
# GitHub API (nur lesend)
# ---------------------------------------------------------------------------


def gql(query, variables=None):
    token = os.environ["ACCESS_TOKEN"]
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables or {}}).encode(),
        headers={"Authorization": f"bearer {token}", "User-Agent": "profile-readme"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        out = json.load(r)
    if "errors" in out:
        raise RuntimeError(out["errors"])
    return out["data"]


def owned_repos():
    repos, cursor = [], None
    while True:
        d = gql("""query($login:String!,$c:String){user(login:$login){
            repositories(first:100, after:$c, ownerAffiliations:OWNER){
              pageInfo{hasNextPage endCursor}
              nodes{nameWithOwner stargazerCount isFork
                    defaultBranchRef{target{oid}}}}}}""", {"login": USER_NAME, "c": cursor})
        page = d["user"]["repositories"]
        repos += page["nodes"]
        if not page["pageInfo"]["hasNextPage"]:
            return repos
        cursor = page["pageInfo"]["endCursor"]


def repo_loc(name_with_owner, author_id):
    owner, name = name_with_owner.split("/")
    commits = add = dele = 0
    cursor = None
    while True:
        d = gql("""query($o:String!,$n:String!,$id:ID!,$c:String){repository(owner:$o,name:$n){
            defaultBranchRef{target{... on Commit{
              history(first:100, after:$c, author:{id:$id}){
                pageInfo{hasNextPage endCursor} nodes{additions deletions}}}}}}}""",
                {"o": owner, "n": name, "id": author_id, "c": cursor})
        ref = d["repository"]["defaultBranchRef"]
        if not ref:
            return 0, 0, 0
        h = ref["target"]["history"]
        for n in h["nodes"]:
            commits += 1
            add += n["additions"]
            dele += n["deletions"]
        if not h["pageInfo"]["hasNextPage"]:
            return commits, add, dele
        cursor = h["pageInfo"]["endCursor"]


def fetch_stats():
    d = gql("""query($login:String!){user(login:$login){id
        followers{totalCount}
        contributed: repositories(ownerAffiliations:[OWNER,COLLABORATOR,ORGANIZATION_MEMBER]){totalCount}}}""",
            {"login": USER_NAME})["user"]
    repos = owned_repos()
    cache = json.load(open(LOC_CACHE)) if os.path.exists(LOC_CACHE) else {}
    commits = add = dele = 0
    new_cache = {}
    for r in repos:
        head = (r["defaultBranchRef"] or {}).get("target", {}).get("oid")
        key = hashlib.sha256(r["nameWithOwner"].encode()).hexdigest()[:16]
        if key in cache and cache[key]["head"] == head:
            c = cache[key]
        else:  # nur Repos neu zählen, deren Branch sich geändert hat
            n, a, x = repo_loc(r["nameWithOwner"], d["id"]) if head else (0, 0, 0)
            c = {"head": head, "commits": n, "add": a, "del": x}
        new_cache[key] = c
        commits += c["commits"]
        add += c["add"]
        dele += c["del"]
    # Cache-Schlüssel sind Hashes, damit private Repo-Namen nicht im öffentlichen Repo landen
    json.dump(new_cache, open(LOC_CACHE, "w"), indent=1)
    return {
        "repos": len(repos),
        "contributed": d["contributed"]["totalCount"],
        "stars": sum(r["stargazerCount"] for r in repos),
        "followers": d["followers"]["totalCount"],
        "commits": commits,
        "loc_add": add,
        "loc_del": dele,
        "updated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
    }

# ---------------------------------------------------------------------------
# SVG
# ---------------------------------------------------------------------------


def esc(s):
    return html.escape(s, quote=False)


def key_spans(key):
    return ".".join(f'<tspan class="key">{esc(k)}</tspan>' for k in key.split("."))


def kv(key, value, width):
    """'. Key: ....... value' auf exakt `width` Zeichen. Gibt (svg, länge) zurück."""
    head = len(key) + 1  # "Key:"
    dots = width - head - len(value) - 2
    dots = max(dots, 1)
    svg = (f'{key_spans(key)}:<tspan class="cc"> {"." * dots} </tspan>'
           f'<tspan class="value">{esc(value)}</tspan>')
    return svg, head + dots + 2 + len(value)


def rule(title):
    n = WIDTH - len(title) - 1
    return f'{esc(title)} -{"—" * (n - 4)}-—-'


def fmt(n):
    return f"{n:,}"


def stats_lines(s):
    left_w = 32  # Breite der linken Hälfte inkl. ". "
    right_w = WIDTH - left_w - 3
    lines = []
    # Repos ... N {Contributed: M} | Stars ... K
    val = fmt(s["repos"])
    extra = f' {{<tspan class="key">Contributed</tspan>: <tspan class="value">{fmt(s["contributed"])}</tspan>}}'
    extra_len = len(f' {{Contributed: {fmt(s["contributed"])}}}')
    a, al = kv("Repos", val, left_w - 2 - extra_len)
    b, _ = kv("Stars", fmt(s["stars"]), right_w)
    lines.append(f'{a}{extra}<tspan class="cc"> | </tspan>{b}')
    a, _ = kv("Commits", fmt(s["commits"]), left_w - 2)
    b, _ = kv("Followers", fmt(s["followers"]), right_w)
    lines.append(f'{a}<tspan class="cc"> | </tspan>{b}')
    net = s["loc_add"] - s["loc_del"]
    tail_txt = f' ( {fmt(s["loc_add"])}++, {fmt(s["loc_del"])}-- )'
    tail = (f' ( <tspan class="addColor">{fmt(s["loc_add"])}++</tspan>, '
            f'<tspan class="delColor">{fmt(s["loc_del"])}--</tspan> )')
    a, _ = kv("Lines of Code", fmt(net), WIDTH - 2 - len(tail_txt))
    lines.append(a + tail)
    return lines


def build_svg(theme, ascii_lines, stats):
    info = []
    for row in ROWS:
        if row is None:
            info.append('<tspan class="cc">. </tspan>')
        elif row[0] == "blank":
            info.append("")
        elif row[0] == "rule":
            info.append(rule(row[1]))
        elif row[0] == "stats":
            info += ['<tspan class="cc">. </tspan>' + l for l in stats_lines(stats)]
        else:
            key, value = row
            value = value.replace("{uptime}", uptime())
            svg, _ = kv(key, value, WIDTH - 2)
            info.append('<tspan class="cc">. </tspan>' + svg)

    n_rows = max(len(info), len(ascii_lines))
    height = Y_START + (n_rows - 1) * LINE_H + 20
    t = THEMES[theme]
    out = [
        "<?xml version='1.0' encoding='UTF-8'?>",
        f'<svg xmlns="http://www.w3.org/2000/svg" font-family="ConsolasFallback,Consolas,Menlo,\'DejaVu Sans Mono\',monospace" '
        f'width="{SVG_W}px" height="{height}px" font-size="16px">',
        "<style>",
        "@font-face { src: local('Consolas'), local('Consolas Bold'); font-family: 'ConsolasFallback';"
        " font-display: swap; -webkit-size-adjust: 109%; size-adjust: 109%; }",
        f".key {{fill: {t['key']};}} .value {{fill: {t['value']};}} .cc {{fill: {t['cc']};}}",
        f".addColor {{fill: {t['add']};}} .delColor {{fill: {t['dele']};}}",
        "text, tspan {white-space: pre;}",
        "</style>",
        f'<rect width="{SVG_W}px" height="{height}px" fill="{t["bg"]}" rx="15"/>',
        f'<text x="{X_ASCII}" y="{Y_START}" fill="{t["text"]}" class="ascii">',
    ]
    for i, l in enumerate(ascii_lines):
        out.append(f'<tspan x="{X_ASCII}" y="{Y_START + i * LINE_H}">{esc(l)}</tspan>')
    out.append("</text>")
    out.append(f'<text x="{X_INFO}" y="{Y_START}" fill="{t["text"]}">')
    for i, l in enumerate(info):
        if l:
            out.append(f'<tspan x="{X_INFO}" y="{Y_START + i * LINE_H}">{l}</tspan>')
    out.append("</text>")
    out.append("</svg>")
    return "\n".join(out) + "\n"


def main():
    offline = "--offline" in sys.argv or not os.environ.get("ACCESS_TOKEN")
    if offline:
        stats = json.load(open(STATS_FILE))
    else:
        stats = fetch_stats()
        json.dump(stats, open(STATS_FILE, "w"), indent=1)
    for name in THEMES:
        art = "ascii_dark.txt" if name.startswith("dark") else "ascii.txt"
        if not os.path.exists(os.path.join(HERE, art)):
            art = "ascii.txt"
        ascii_lines = open(os.path.join(HERE, art), encoding="utf-8").read().splitlines()
        with open(os.path.join(HERE, name), "w", encoding="utf-8") as f:
            f.write(build_svg(name, ascii_lines, stats))
    print(("offline" if offline else "live"), stats)


if __name__ == "__main__":
    main()
