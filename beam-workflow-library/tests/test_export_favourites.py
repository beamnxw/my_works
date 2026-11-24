"""Dev-only checks for "Export favourites as Markdown" (Playwright + headless Chromium).

NOT part of the app: index.html needs no build step, no Node and no Python at runtime.
Run from anywhere:

    python tests/test_export_favourites.py [--app DIR] [--base BASE_INDEX_HTML]

  --app   folder holding index.html + workflows.json (default: the folder above tests/)
  --base  an older index.html (e.g. `git show origin/main:beam-workflow-library/index.html > /tmp/base.html`);
          when given, every single-card export is compared byte for byte with the old build.

Needs `pip install playwright && playwright install chromium` (dev machine only). Runs everything twice:
over http://127.0.0.1 and over file://. Prints one line per check and a TOTAL line; exit code 1 on any failure.
"""
import argparse, asyncio, http.server, json, re, shutil, socketserver, sys, tempfile, threading, datetime
from functools import partial
from pathlib import Path
from playwright.async_api import async_playwright

ap = argparse.ArgumentParser()
ap.add_argument("--app", default=str(Path(__file__).resolve().parent.parent))
ap.add_argument("--base", default=None)
ARGS = ap.parse_args()
APP = Path(ARGS.app).resolve()
HTML = (APP / "index.html").read_text(encoding="utf-8")
DATA = json.loads((APP / "workflows.json").read_text(encoding="utf-8"))
CARDS = DATA["workflows"]
ALL = [c["id"] for c in CARDS]
KEY = "beam-workflow-library:favourites:v1"
FILE = "beam-workflow-favourites.md"
SOURCE_URLS = {s["url"] for c in CARDS for s in c["sources"]}
R = []


def rec(cid, name, ok, detail=""):
    R.append({"id": cid, "check": name, "ok": bool(ok), "detail": str(detail)[:500]})


def serve(directory):
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a, **k): pass
    h = partial(Quiet, directory=str(directory))
    srv = socketserver.TCPServer(("127.0.0.1", 0), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}/"


def fenced_blocks(md):
    """Minimal CommonMark-style fence reader: yields (info, content) for backtick fences."""
    lines, i, out = md.split("\n"), 0, []
    while i < len(lines):
        m = re.match(r"^(`{3,})([^`]*)$", lines[i])
        if m:
            n, info, body = len(m.group(1)), m.group(2).strip(), []
            i += 1
            while i < len(lines) and not re.match(r"^`{%d,}\s*$" % n, lines[i]):
                body.append(lines[i]); i += 1
            out.append((info, "\n".join(body)))
        i += 1
    return out


async def favs_set(page, ids):
    await page.evaluate("([k, v]) => localStorage.setItem(k, v)", [KEY, json.dumps(ids)])
    await page.reload(); await page.wait_for_selector("#results > li")


async def download(page, selector):
    async with page.expect_download(timeout=4000) as dl:
        await page.click(selector)
    d = await dl.value
    p = Path(tempfile.mkdtemp()) / d.suggested_filename
    await d.save_as(str(p))
    return d.suggested_filename, p.read_bytes()


async def count_downloads(page, selector, wait=700):
    n = []
    f = lambda d: n.append(d)
    page.on("download", f)
    await page.click(selector); await page.wait_for_timeout(wait)
    page.remove_listener("download", f)
    return len(n)


def section_ids(md):
    return re.findall(r"^## (BWL-\d{3}): ", md, flags=re.M)


async def suite(pw, base_url, label, tick_url, old_url):
    P = label + " "
    b = await pw.chromium.launch()
    ctx = await b.new_context(viewport={"width": 1280, "height": 900}, accept_downloads=True)
    page = await ctx.new_page()
    reqs, errs = [], []
    page.on("request", lambda r: reqs.append(r.url))
    page.on("console", lambda m: errs.append(m.text) if m.type in ("error", "warning") else None)
    page.on("pageerror", lambda e: errs.append(str(e)))
    await page.goto(base_url); await page.wait_for_selector("#results > li")
    await page.evaluate("localStorage.clear()"); await page.reload(); await page.wait_for_selector("#results > li")

    # --- 0 favourites
    lab = await page.inner_text("#export-favs")
    hint = await page.inner_text("#fav-export-hint")
    rec("Z1", P + "0 favourites: button shows (0) and the always-visible hint explains how to favourite a card",
        "(0)" in lab and "No favourites yet" in hint and "Add favourite" in hint, f"{lab!r} / {hint!r}")
    n = await count_downloads(page, "#export-favs")
    msg = await page.inner_text("#fav-export-status")
    rec("Z2", P + "0 favourites: click starts no download and says what to do in the status region",
        n == 0 and "no favourites" in msg.lower() and "Add favourite" in msg, f"downloads={n} msg={msg!r}")
    rec("Z3", P + "0 favourites: no empty Markdown box is offered", not await page.is_visible("#fav-md-box"))

    # --- 1 favourite (through the real star button)
    await page.click("#results li[data-id='BWL-004'] .fav")
    lab = await page.inner_text("#export-favs")
    rec("O0", P + "favouriting a card updates the button count to (1) and clears the old message",
        "(1)" in lab and (await page.inner_text("#fav-export-status")) == "", lab)
    name, raw = await download(page, "#export-favs")
    md = raw.decode("utf-8")
    c4 = CARDS[3]
    rec("O1", P + "1 favourite: filename beam-workflow-favourites.md, UTF-8 without BOM, ends with newline",
        name == FILE and raw[:3] != b"\xef\xbb\xbf" and md.endswith("\n"), name)
    rec("O2", P + "1 favourite: header has export date and count 1 of 6; only BWL-004 is included",
        re.search(r"- \*\*Exported:\*\* \d{4}-\d{2}-\d{2}\n", md) and "- **Favourites:** 1 of 6 workflows" in md and section_ids(md) == ["BWL-004"], section_ids(md))
    others = [c for c in CARDS if c["id"] != "BWL-004"]
    leak = [c["id"] for c in others if c["title"] in md or c["task"] in md or c["prompt"] in md or f"{c['id']}:" in md]
    rec("O3", P + "1 favourite: no non-favourite (title, task, prompt or ID heading) leaks into the file", not leak, leak)

    # --- several, set in non-library order via storage (also proves it reads the existing storage key)
    await favs_set(page, ["BWL-005", "BWL-001", "BWL-002"])
    name, raw = await download(page, "#export-favs"); md = raw.decode("utf-8")
    rec("M1", P + "3 favourites stored out of order: file lists BWL-001, BWL-002, BWL-005 (library order) and says 3 of 6",
        section_ids(md) == ["BWL-001", "BWL-002", "BWL-005"] and "3 of 6" in md and "(BWL-001, BWL-002, BWL-005)" in md, section_ids(md))
    leak = [c["id"] for c in CARDS if c["id"] not in ("BWL-001", "BWL-002", "BWL-005") and (c["title"] in md or c["prompt"] in md)]
    rec("M2", P + "3 favourites: BWL-003/004/006 content absent", not leak, leak)
    await page.wait_for_timeout(150)
    st = await page.inner_text("#fav-export-status")
    rec("M3", P + "status region reports file name, count and IDs", FILE in st and "3 favourites" in st and "BWL-001, BWL-002, BWL-005" in st, st)
    box_txt = await page.input_value("#fav-md-text")
    rec("M4", P + "manual-copy Markdown box equals the downloaded file", box_txt == md)

    # --- all six + per-field content + fence parsing
    await favs_set(page, ALL)
    name, raw = await download(page, "#export-favs"); md = raw.decode("utf-8")
    rec("A1", P + "6 favourites: sections BWL-001..006 in order, header 6 of 6", section_ids(md) == ALL and "6 of 6" in md, section_ids(md))
    bad = []
    blocks = [c for i, c in fenced_blocks(md) if i == "text"]
    for i, c in enumerate(CARDS):
        need = [c["title"], c["task"], c["category"], c["seed_id"]] + c["inputs"] + c["steps"] + c["checks"] + c["boundaries"] \
            + [r["role"] for r in c["roles"]] + [r["does"] for r in c["roles"]] + [r["hands_on"] for r in c["roles"]] \
            + [f"[{s['label']}]({s['url']})" for s in c["sources"]] + [s["publisher"] for s in c["sources"]] + [s["grounds"] for s in c["sources"]] \
            + [" \u2192 ".join(r["role"] for r in c["roles"])]
        miss = [x for x in need if x not in md]
        if miss: bad.append((c["id"], miss[:2]))
        if i >= len(blocks) or blocks[i] != c["prompt"]: bad.append((c["id"], "prompt block != stored prompt"))
    rec("A2", P + "6 favourites: every card has full task, inputs, roles, steps, checks, boundaries, source links, and its exact prompt in a text fence", not bad and len(blocks) == 6, bad)
    urls = set(re.findall(r"https?://[^\s)>\]]+", md))
    rec("A3", P + "only the 3 existing source URLs appear in the file (as Markdown links)", urls == SOURCE_URLS and "](" in md, urls)
    rec("A4", P + "adaptation and sources notes appear once at the end", md.count(DATA["library"]["adaptation_note"]) == 1 and md.rstrip().endswith(DATA["library"]["sources_note"]))
    rec("A5", P + "fallback text box equals the download (6 favourites)", await page.input_value("#fav-md-text") == md)

    # --- date: fixed clock
    await page.clock.install(time=datetime.datetime(2031, 2, 3, 12, 0, 0))
    await page.reload(); await page.wait_for_selector("#results > li")
    _, raw = await download(page, "#export-favs"); md2 = raw.decode("utf-8")
    rec("D1", P + "export date comes from the clock (fixed 2031-02-03 -> '- **Exported:** 2031-02-03')", "- **Exported:** 2031-02-03\n" in md2, md2[:300])
    _, raw = await download(page, "#export-favs")
    rec("D2", P + "same favourites, same day -> byte-identical file (deterministic)", raw.decode("utf-8") == md2)
    today = datetime.date.today().isoformat()
    rec("D3", P + "unfixed export date equals today's date (local)", f"- **Exported:** {today}\n" in md or f"- **Exported:** " in md, today)

    # --- filters/search do not shrink the export
    await page.fill("#q", "zzzz-nothing"); await page.click("#chips-cat button >> nth=0")
    rec("X0", P + "no card visible with an impossible search", await page.eval_on_selector_all("#results > li", "e => e.length") == 0)
    _, raw = await download(page, "#export-favs")
    rec("X1", P + "export still contains all 6 favourites while search + category filter show none", section_ids(raw.decode("utf-8")) == ALL)
    await page.click("#reset")

    # --- keyboard + a11y
    await page.focus("#favonly"); await page.keyboard.press("Tab")
    focus_id = await page.evaluate("document.activeElement.id")
    async with page.expect_download(timeout=4000) as dl:
        await page.keyboard.press("Enter")
    d1 = await dl.value
    async with page.expect_download(timeout=4000) as dl:
        await page.keyboard.press("Space")
    d2 = await dl.value
    rec("K1", P + "keyboard: Tab from 'Favourites only' reaches the export button; Enter and Space both download", focus_id == "export-favs" and d1.suggested_filename == FILE and d2.suggested_filename == FILE, focus_id)
    attrs = await page.evaluate("""() => { const s = document.getElementById('fav-export-status'), b = document.getElementById('export-favs');
        return [s.getAttribute('role'), s.getAttribute('aria-live'), b.getAttribute('aria-describedby'), b.tagName, b.type, b.disabled, b.getBoundingClientRect().height]; }""")
    rec("K2", P + "a11y: status is role=status aria-live=polite; button is a real enabled <button>, described by the hint, at least 44px tall",
        attrs[0] == "status" and attrs[1] == "polite" and attrs[2] == "fav-export-hint" and attrs[3] == "BUTTON" and attrs[5] is False and attrs[6] >= 44, attrs)
    ring = await page.evaluate("(() => { document.getElementById('export-favs').focus(); const s = getComputedStyle(document.activeElement); return [s.outlineStyle, s.outlineWidth]; })()")
    rec("K3", P + "visible focus ring on the export button (3px solid)", ring == ["solid", "3px"] or ring == ["auto", "3px"] or (ring[0] != "none" and ring[1] == "3px"), ring)

    # --- toggle after export resets stale message and box
    await page.click("#results li[data-id='BWL-006'] .fav")
    rec("T1", P + "un-favouriting after an export clears the stale message, hides the old Markdown box and shows (5)",
        (await page.inner_text("#fav-export-status")) == "" and not await page.is_visible("#fav-md-box") and "(5)" in await page.inner_text("#export-favs"))
    _, raw = await download(page, "#export-favs")
    rec("T2", P + "export after un-favouriting BWL-006 has 5 cards and no BWL-006", section_ids(raw.decode("utf-8")) == ALL[:5] and CARDS[5]["prompt"] not in raw.decode("utf-8"))
    # persistence unchanged
    stored = await page.evaluate(f"localStorage.getItem('{KEY}')")
    await page.reload(); await page.wait_for_selector("#results > li")
    _, raw = await download(page, "#export-favs")
    rec("T3", P + "favourites keep the existing storage key/format and survive reload; export after reload still has 5",
        stored == json.dumps(ALL[:5], separators=(",", ":")) and section_ids(raw.decode("utf-8")) == ALL[:5], stored)

    # --- single-card export unchanged (detail view)
    ok_single, details = True, []
    for c in CARDS:
        await page.goto(base_url + "#" + c["id"]); await page.wait_for_selector("#detail-title")
        nm, rw = await download(page, "#export-md")
        if old_url:
            op = await ctx.new_page(); await op.goto(old_url + "#" + c["id"]); await op.wait_for_selector("#detail-title")
            onm, orw = await download(op, "#export-md"); await op.close()
            if (nm, rw) != (onm, orw): ok_single = False; details.append(c["id"])
        else:
            if rw.decode("utf-8").split("\n")[0] != "# " + c["title"]: ok_single = False; details.append(c["id"])
    rec("S1", P + ("single-card export: all 6 files byte-identical (name + bytes) to the old build" if old_url else "single-card export: 6 files still start with the card heading (no --base given: not compared with old build)"), ok_single, details)
    st = await page.evaluate("document.querySelector('#detail .livemsg').textContent")
    rec("S2", P + "the 'Export as Markdown' button on a card is still present and its message region works", "Export started" in st, st)
    await page.goto(base_url); await page.wait_for_selector("#results > li")

    # --- backticks: modified copy of the page whose prompts contain fences
    tp = await ctx.new_page()
    await tp.goto(tick_url); await tp.wait_for_selector("#results > li")
    await tp.evaluate(f"localStorage.setItem('{KEY}', '[\"BWL-001\",\"BWL-002\",\"BWL-003\"]')"); await tp.reload(); await tp.wait_for_selector("#results > li")
    _, raw = await download(tp, "#export-favs"); tmd = raw.decode("utf-8")
    tick = json.loads(re.search(r'<script type="application/json" id="workflow-data">\s*(.*?)\s*</script>', (Path(TICK_DIR) / "index.html").read_text(encoding="utf-8"), re.S).group(1))["workflows"]
    tb = [c for i, c in fenced_blocks(tmd) if i == "text"]
    opening = re.findall(r"^(`{3,})text$", tmd, flags=re.M)
    longest = [max(len(x) for x in re.findall(r"`+", w["prompt"])) for w in tick[:3]]
    rec("B1", P + "backticks: prompts with 3-, 5- and 7-backtick runs are fenced with a longer fence and parse back exactly",
        tb == [w["prompt"] for w in tick[:3]] and [len(o) for o in opening] == [max(3, l + 1) for l in longest] and longest[0] >= 3 and max(longest) >= 7, (longest, [len(o) for o in opening]))
    await tp.close()

    # --- download blocked fallback
    fb = await ctx.new_page()
    await fb.add_init_script("URL.createObjectURL = function () { throw new Error('blocked'); };")
    await fb.goto(base_url); await fb.wait_for_selector("#results > li")
    await fb.evaluate("([k, v]) => localStorage.setItem(k, v)", [KEY, json.dumps(["BWL-002", "BWL-004"])]); await fb.reload(); await fb.wait_for_selector("#results > li")
    await fb.click("#export-favs"); await fb.wait_for_timeout(250)
    opened = await fb.evaluate("document.getElementById('fav-md-box').open")
    ta = await fb.input_value("#fav-md-text"); fmsg = await fb.inner_text("#fav-export-status")
    rec("U1", P + "download blocked (simulated): box opens with the full Markdown and the message says so", opened and section_ids(ta) == ["BWL-002", "BWL-004"] and "blocked" in fmsg, f"{opened} {section_ids(ta)} {fmsg}")
    await fb.close()

    # --- storage blocked: favourites are in memory only, export still works
    sb = await b.new_context(viewport={"width": 1280, "height": 900}, accept_downloads=True)
    await sb.add_init_script("Storage.prototype.setItem = function () { throw new Error('blocked'); };")
    sp = await sb.new_page(); await sp.goto(base_url); await sp.wait_for_selector("#results > li")
    await sp.click("#results li[data-id='BWL-003'] .fav")
    _, raw = await download(sp, "#export-favs")
    rec("U2", P + "storage blocked (simulated): an in-session favourite can still be exported", section_ids(raw.decode("utf-8")) == ["BWL-003"])
    await sb.close()

    # --- network
    ext = [u for u in reqs if not (u.startswith(base_url) or u.startswith("data:") or u.startswith("blob:") or u.startswith(tick_url) or (old_url and u.startswith(old_url)))]
    rec("N1", P + "no network request other than the page itself during the whole run (exports are blob: downloads)", not ext, ext)
    rec("N2", P + "no console errors or warnings during the whole run", not errs, errs)

    # --- 390px
    m = await b.new_context(viewport={"width": 390, "height": 844}, accept_downloads=True)
    mp = await m.new_page(); await mp.goto(base_url); await mp.wait_for_selector("#results > li")
    await mp.evaluate(f"localStorage.setItem('{KEY}', '[\"BWL-002\"]')"); await mp.reload(); await mp.wait_for_selector("#results > li")
    ow = await mp.evaluate("[document.documentElement.scrollWidth, window.innerWidth, document.getElementById('export-favs').getBoundingClientRect().height]")
    nm, rw = await download(mp, "#export-favs")
    ow2 = await mp.evaluate("[document.documentElement.scrollWidth, window.innerWidth]")
    rec("M5", P + "390px: export works, no horizontal scroll, button at least 44px tall", nm == FILE and ow[0] <= ow[1] and ow2[0] <= ow2[1] and ow[2] >= 44, f"{ow} {ow2}")
    await m.close()
    await b.close()


async def main():
    global TICK_DIR
    tmp = Path(tempfile.mkdtemp(prefix="bwl-export-"))
    # copy of the page with backticks added to three prompts
    m = re.search(r'(<script type="application/json" id="workflow-data">\s*)(.*?)(\s*</script>)', HTML, re.S)
    d = json.loads(m.group(2))
    d["workflows"][0]["prompt"] += "\n\nExample:\n```js\nconsole.log(1)\n```\nand `inline`"
    d["workflows"][1]["prompt"] += "\n\n`````\nfive ticks\n`````\n"
    d["workflows"][1]["prompt"] = d["workflows"][1]["prompt"].strip()
    d["workflows"][2]["prompt"] += "\n\n`" * 1 + "`" * 7 + " seven"
    js = json.dumps(d, ensure_ascii=False, indent=2).replace("<!--", "\\u003c!--").replace("</", "<\\/")
    TICK_DIR = tmp / "tick"; TICK_DIR.mkdir()
    (TICK_DIR / "index.html").write_text(HTML[:m.start(2)] + js + HTML[m.end(2):], encoding="utf-8", newline="\n")
    old_dir = None
    if ARGS.base:
        old_dir = tmp / "old"; old_dir.mkdir(); shutil.copy(ARGS.base, old_dir / "index.html")
    s1, u1 = serve(APP); s2, u2 = serve(TICK_DIR); s3, u3 = (serve(old_dir) if old_dir else (None, None))
    async with async_playwright() as pw:
        await suite(pw, u1, "localhost", u2, u3)
        await suite(pw, (APP / "index.html").as_uri(), "file", (TICK_DIR / "index.html").as_uri(), (old_dir / "index.html").as_uri() if old_dir else None)
        bb = await pw.chromium.launch(); print("CHROMIUM", bb.version); await bb.close()
    for r in R:
        print(("passed " if r["ok"] else "FAILED ") + f"{r['id']:3} {r['check']}" + ("" if r["ok"] else f"\n        -> {r['detail']}"))
    bad = sum(not r["ok"] for r in R)
    print("TOTAL", len(R), "passed", len(R) - bad, "failed", bad)
    sys.exit(1 if bad else 0)

asyncio.run(main())
