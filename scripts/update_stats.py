#!/usr/bin/env python3
"""Fills the GitHub-stats window of assets/banner.template.svg with LIVE data
from the GitHub API and writes g4zwr-banner.svg. Standard library only."""
import json, os, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
USER = os.environ.get("GH_USER", "g4zwr")
TOKEN = os.environ.get("GH_TOKEN", "")
T, CY = 1.4, 14          # box-landing offset / seconds per window-switch cycle
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"

# ------------------------------------------------------------------ svg helpers
def A(attr, keys, vals, calc="linear"):
    return (f'<animate attributeName="{attr}" calcMode="{calc}" keyTimes="{";".join(map(str, keys))}" '
            f'values="{";".join(map(str, vals))}" dur="{CY}s" begin="{T}s" repeatCount="indefinite"/>')

def AT(keys, vals):
    return (f'<animateTransform attributeName="transform" type="translate" calcMode="discrete" '
            f'keyTimes="{";".join(map(str, keys))}" values="{";".join(vals)}" dur="{CY}s" begin="{T}s" repeatCount="indefinite"/>')

def bar(label, tl):
    cx = 78 + tl + 8
    return (f'<g><rect x="64" y="36" width="832" height="32" fill="#fff" fill-opacity="0.08" stroke="#fff" stroke-opacity="0.6"/>'
            f'<text x="78" y="57" font-size="15" textLength="{tl}" fill="#fff" opacity="0.9">{label}</text>'
            f'<rect x="{cx}" y="46" width="9" height="13" fill="#fff"><animate attributeName="opacity" calcMode="discrete" values="1;0" dur="1s" begin="{T}s" repeatCount="indefinite"/></rect>'
            f'<g fill="none" stroke="#fff" stroke-opacity="0.8" stroke-width="1.5"><rect x="836" y="45" width="14" height="14"/><rect x="856" y="45" width="14" height="14"/><rect x="876" y="45" width="14" height="14"/>'
            f'<path d="M839 55H847M859 48H867V56H859ZM879 48L887 56M887 48L879 56"/></g></g>')

def stats_window(d):
    tx = [64, 278, 492, 706]
    w = [bar(f'stats.dll — github.com/{USER}', 252)]
    w.append(f'<text x="64" y="448" font-size="14" fill="#fff" opacity="0.5">@{USER} · roblox gameplay dev</text>')
    w.append(f'<text x="896" y="448" font-size="14" text-anchor="end" fill="#fff" opacity="0.5">streak {d["streak"]}d</text>')
    vals = []
    for (lab, val), x in zip(d["tiles"], tx):
        fs = 46 if len(val) <= 6 else 36
        w.append(f'<g><rect x="{x}" y="90" width="198" height="100" fill="none" stroke="#fff" stroke-opacity="0.5"/>'
                 f'<path d="M{x} 100V90H{x+10}" stroke="#fff" stroke-width="3" fill="none"/>'
                 f'<text x="{x+14}" y="118" font-size="14" fill="#fff" opacity="0.6">{lab}</text></g>')
        vals.append(f'<text x="{x+14}" y="170" font-size="{fs}" font-weight="bold">{val}</text>')
    fk = [0, 0.50, 0.51, 0.52, 0.53, 0.54]
    w.append(f'<g fill="#fff" opacity="0">{A("opacity", fk, [0,1,0,1,0,1], "discrete")}{"".join(vals)}</g>')
    gk = [0, 0.50, 0.52, 0.70, 0.71, 0.72, 0.73, 0.74]
    for xs, fill in [([0,-6,0,0,5,0,-7,0], '#ff2d55'), ([0,6,0,0,-5,0,7,0], '#00e5ff')]:
        w.append(f'<g fill="{fill}" opacity="0" style="mix-blend-mode:screen">{A("opacity", gk, [0,1,0,0,1,0,1,0], "discrete")}'
                 f'{AT(gk, [f"{x} 0" for x in xs])}{"".join(vals)}</g>')
    w.append('<text x="64" y="236" font-size="15" fill="#fff" opacity="0.7">TOP LANGUAGES</text>')
    if not d["langs"]:
        w.append('<text x="64" y="290" font-size="15" fill="#fff" opacity="0.5">waiting for first stats update…</text>')
    top = max([p for _, p in d["langs"]] or [1])
    for i, (n, p) in enumerate(d["langs"][:4]):
        y = 270 + i * 40; W = max(2, round(246 * p / top)); st = round(0.51 + 0.015 * i, 3)
        w.append(f'<text x="64" y="{y}" font-size="16" fill="#fff">{n}</text>'
                 f'<rect x="190" y="{y-13}" width="250" height="16" fill="none" stroke="#fff" stroke-opacity="0.35"/>'
                 f'<rect x="192" y="{y-11}" width="0" height="12" fill="#fff" opacity="0.9">{A("width", [0, st, round(st+0.08,3), 1], [0, 0, W-4, W-4])}</rect>'
                 f'<text x="452" y="{y}" font-size="16" fill="#fff" opacity="0.8">{p}%</text>')
    w.append('<text x="520" y="236" font-size="15" fill="#fff" opacity="0.7">CONTRIBUTIONS</text>')
    for c, col in enumerate(d["cols"]):
        cells = ''.join(f'<rect x="{520+24*c}" y="{254+24*r}" width="20" height="20" fill="#fff" fill-opacity="{lv}"/>'
                        for r, lv in enumerate(col) if lv is not None)
        st = round(0.50 + 0.004 * c, 3)
        w.append(f'<g opacity="0">{A("opacity", [0, st, round(st+0.012,3), 1], [0,0,1,1])}{cells}</g>')
    w.append(f'<rect x="64" y="70" width="832" height="3" fill="#fff" opacity="0">{A("y",[0,0.5,0.58,1],[70,70,436,436])}{A("opacity",[0,0.5,0.501,0.58,0.581,1],[0,0,0.5,0.5,0,0])}</rect>')
    return ''.join(w)

# ------------------------------------------------------------------ github data
QUERY = """query($login:String!,$after:String){user(login:$login){
followers{totalCount}
repositories(ownerAffiliations:OWNER,privacy:PUBLIC,isFork:false,first:100,after:$after){
totalCount pageInfo{hasNextPage endCursor}
nodes{stargazerCount languages(first:10,orderBy:{field:SIZE,direction:DESC}){edges{size node{name}}}}}
contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{contributionCount}}}}}}"""

def gql(after=None):
    req = urllib.request.Request("https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER, "after": after}}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json", "User-Agent": "banner-stats"})
    with urllib.request.urlopen(req, timeout=30) as r:
        out = json.load(r)
    if "errors" in out:
        sys.exit(f"GitHub API error: {out['errors']}")
    return out["data"]["user"]

def fetch():
    u = gql(); first = u; stars = 0; langs = {}; after = None
    while True:
        repos = u["repositories"]
        for n in repos["nodes"]:
            stars += n["stargazerCount"]
            for e in n["languages"]["edges"]:
                langs[e["node"]["name"]] = langs.get(e["node"]["name"], 0) + e["size"]
        if not repos["pageInfo"]["hasNextPage"]:
            break
        u = gql(repos["pageInfo"]["endCursor"])
    return first, stars, langs

def build_data(first, stars, langs):
    cal = first["contributionsCollection"]["contributionCalendar"]
    weeks = cal["weeks"]
    counts = [d["contributionCount"] for w in weeks for d in w["contributionDays"]]
    i = len(counts) - 1
    if i >= 0 and counts[i] == 0: i -= 1          # today may not have commits yet
    streak = 0
    while i >= 0 and counts[i] > 0: streak += 1; i -= 1
    grid = [[d["contributionCount"] for d in w["contributionDays"]] for w in weeks[-15:]]
    mx = max([n for col in grid for n in col] or [1]) or 1
    def lv(n):
        if n == 0: return 0.07
        r = n / mx
        return 0.22 if r <= .25 else 0.45 if r <= .5 else 0.75 if r <= .75 else 1
    cols = [[lv(n) for n in col] + [None] * (7 - len(col)) for col in grid]
    total = sum(langs.values()) or 1
    top = sorted(langs.items(), key=lambda kv: -kv[1])[:4]
    return {"tiles": [("STARS", f"{stars:,}"), ("REPOS", f"{first['repositories']['totalCount']:,}"),
                      ("FOLLOWERS", f"{first['followers']['totalCount']:,}"),
                      ("CONTRIBS / YR", f"{cal['totalContributions']:,}")],
            "langs": [(n, round(100 * s / total)) for n, s in top], "cols": cols, "streak": streak}

def main():
    if not TOKEN: sys.exit("Set GH_TOKEN")
    data = build_data(*fetch())
    tpl = (ROOT / "assets" / "banner.template.svg").read_text(encoding="utf-8")
    (ROOT / "g4zwr-banner.svg").write_text(tpl.replace("<!--WIN2-->", stats_window(data)), encoding="utf-8")
    print("updated", data["tiles"], data["langs"], "streak", data["streak"])

if __name__ == "__main__":
    main()
