---
name: webfetch-empty-use-agent-browser
description: >-
  When webfetch returns garbled binary from a .pdf/.docx/.xlsx URL (PDF magic bytes, mojibake), do NOT pivot to agent-browser: download with curl and extract via pdftotext or pypdf/pdfplumber (see the Binary files section). Otherwise, when webfetch yields an empty body, a TOO-LARGE response, a near-empty JS-rendered shell, or fails on a dynamic page, SWITCH to agent-browser instead of retrying — 'too large' is the same signal as 'empty'. Targets: single-page apps, job boards (Workday, Greenhouse, Lever, Ashby), dashboards, docs portals, anything client-side rendered. Covers the browser fallback recipe, DOM-eval cleanup when get-text-body returns noise, recursive docs-site extraction, search-engine cancellation and CAPTCHA handling (do not cascade to a second engine; pivot to Exa or direct fetches), the enrichment tier (one cheap sibling fetch, never invent specifics), verified Unsplash stock imagery, citation-link verification, and the HTML-format fix for stripped <head> content. Details in the body.
created_by: autolearn
created_at: "2026-07-15"
---

# Webfetch empty → use agent-browser

When `webfetch` comes back empty, near-empty, **too large** (response exceeds the size limit — the page is JS-rendered with heavy bundled content), or as a generic JS-rendered shell (nav/header chrome but no real body content), do NOT keep retrying webfetch with URL variations, and do NOT reason about or guess the page's content from its title/URL alone. Switch to `agent-browser`, which actually executes the page's JavaScript and returns the rendered content.

Script-download-blocking portals are the same signal. Some government form sites (e.g. Mass.gov, seen 2026-08-31 fetching a MassHealth SACA-2 renewal PDF) serve nothing useful to scripted downloads (curl, webfetch). One blocked attempt is enough to diagnose: pull the file through a real browser session (agent-browser) and save from there. (Exception, unchanged: garbled BINARY from a downloadable file URL is a successful download, see the Binary files section.)

This is the single most reliable fallback for any client-side-rendered page. One failed `webfetch` attempt is sufficient signal to pivot — don't burn 3–5 turns retrying.


## Pre-flight: verify agent-browser is installed BEFORE relying on the fallback

The entire fallback chain below assumes `agent-browser` is on PATH. It is NOT auto-installed with the skill — the skill documents the command surface, but the binary is a separate install. On Eric's machines as of 2026-07-18, `agent-browser` is NOT installed (`which agent-browser` returns empty, no binary in `~/.local/bin/`, no global npm package, npx itself absent). Memory #46 (2026-06-29) already flagged it as "recommended but NOT yet confirmed working by the user."

Before committing to the agent-browser pivot, run the one-command pre-flight:

```bash
command -v agent-browser >/dev/null 2>&1 && echo "available" || echo "MISSING"
```

**If MISSING, do NOT burn turns discovering this mid-fallback.** Pick one of:

1. **Tell the user agent-browser is not installed** and ask whether to install it (do NOT silently install — system changes need user consent). This is the right move when agent-browser is genuinely necessary for the task (Workday job postings, JS-rendered auth-walled content, recursive site crawl) and the alternates below won't suffice.
2. **Fall back to the documented no-browser pivots** (these are the SAME pivots recommended for CAPTCHA'd search engines — see the "Search engines" section below):
   - Direct GET fetches of known authoritative JSON/HTML endpoints: SEC EDGAR, PyPI JSON API (`pypi-package-metadata-json-api` skill), Wikipedia wikitext, official docs sites, arXiv, university press releases, government databases. See the `*-research-fallback` skill family.
   - German/EU company registry facts: the legally-mandatory Impressum on the company's own website matches the Handelsregister entry (same registered name, same HRB number, same Amtsgericht) — this is primary-source-equivalent verification without needing the Handelsregister direct URL (which is often JS-gated). Verified 2026-07-18 confirming `prefix.dev GmbH` via prefix.dev's own imprint.
   - Report the claim as UNVERIFIABLE this session rather than fabricating (per memory #75 / epistemic-honesty discipline). State what you verified, what you couldn't, and what would be needed.
3. **Do NOT cycle through webfetch URL-pattern guesses** as a substitute — that is its own wasted-turn cascade documented in the "Variant: URL-pattern guessing" section below.

The cost of skipping the pre-flight: in the 2026-07-18 EOSS session, the assistant burned multiple turns cycling `webfetch 404` → search-engine CAPTCHA → load agent-browser skill → discover binary missing → try Google via webfetch → ... before converging. The pre-flight check is one command and short-circuits all of that.

## Recognition — when to pivot

Pivot to agent-browser immediately when `webfetch` returns any of:
- an empty result / `Empty` output,
- a **TOO-LARGE response** (exceeds the size limit, e.g. >5MB) — this is just as decisive a signal as "empty"; a page whose raw HTML is 5MB+ is almost certainly JS-rendered with bundled content, and retrying webfetch will yield the same result every time,
- a homepage shell or nav menu with none of the target content (e.g. just "Skip to main content / Sign In / footer"),
- a login/redirect stub instead of content,
- a reCAPTCHA / challenge page.

Typical culprits: **Workday** job boards (`*.myworkdayjobs.com`), Greenhouse/Lever/Ashby job pages, single-page apps (React/Vue/Angular/Svelte), dashboards, analytics portals, many docs sites (material.io, **GitHub Pages sites** like schema-harness.github.io, Docusaurus, some ReadTheDashboards), and any URL whose content is built by client-side JS.


## Binary files (PDFs, Office docs, images) — do NOT pivot to agent-browser

A DISTINCT failure mode from all the JS-rendered cases above: webfetch on a **binary file URL** (a `.pdf`, `.docx`, `.xlsx`, `.pptx`, or image) returns GARBLED binary content — not empty, not a JS shell, not "too large," but raw bytes (`%PDF-1.4...` or unreadable mojibake). This is NOT a fetch failure and NOT a signal to pivot to agent-browser. The file downloaded fine; it is just not text.

**Do NOT use agent-browser here.** A real browser RENDERS a PDF visually; `agent-browser get text "body"` will not return the PDF's text layer reliably (or at all). The fix is download + text extraction.

**Fix — download with curl, then extract text:**

```bash
# 1. Download the file directly
curl -sL -o /tmp/doc.pdf "<pdf-url>"

# 2a. Fastest: pdftotext (poppler) — prints text to stdout
pdftotext /tmp/doc.pdf - | grep -i "outlier"

# 2b. If pdftotext isn't installed: pypdf via uv (no install needed)
uv run --with pypdf python -c "
import pypdf
r = pypdf.PdfReader('/tmp/doc.pdf')
text = chr(10).join(p.extract_text() for p in r.pages)
print(text[:5000])  # preview
"

# 2c. For complex layouts (tables, columns): pdfplumber via uv
uv run --with pdfplumber python -c "
import pdfplumber
with pdfplumber.open('/tmp/doc.pdf') as pdf:
    text = chr(10).join((p.extract_text() or '') for p in pdf.pages)
    print(text[:5000])
"
```

**Recognition — the signal that this is a BINARY file, not a JS-rendered page:**
- webfetch output starts with `%PDF` (PDF magic bytes) or is non-UTF8 mojibake (angle brackets / control chars with no readable prose)
- The URL ends in `.pdf`, `.docx`, `.xlsx`, `/download`, or a content-disposition header suggests an attachment
- Contrast with the JS-shell case: a JS shell is READABLE HTML (nav/header/footer text) with the body missing; binary garbage is UNREADABLE bytes throughout

**Government/regulatory PDFs** (FDA, EMA, ICH guidance documents) are the common trigger — the guidance exists as a PDF, and the "view" page links to a `/media/<id>/download` URL. Download + extract is the only reliable path. NOTE: the search/listing pages AROUND those PDFs are often JS-rendered (a separate problem — those DO warrant agent-browser); only the PDF itself needs the curl+extract path.

Discovered 2026-07-23 researching FDA Bioanalytical Method Validation (BMV) 2018 guidance: webfetch on `fda.gov/media/70858/download` returned binary garbage; `curl -o` + `pdftotext` extracted the full searchable text, including the key "QC results (including outliers)... should be included" quote at section III.C.

**VARIANT — portals that BLOCK the scripted download itself (2026-08-31, Mass.gov SACA-2 form):** everything above assumes the server will serve the file to a script. Government benefit portals (Mass.gov confirmed; expect similar state/federal benefits portals) block non-browser clients — curl/webfetch return a block page or nothing useful, and the download itself fails. That is a DIFFERENT condition from the garbled-bytes success case above: garbled bytes = the file downloaded fine (no pivot); blocked/empty = the download failed (pivot IS warranted). Fix: pull the file through a real browser session (agent-browser: navigate to the form page, trigger the download link, save to disk), then run the pdftotext/pypdf extraction pipeline on the saved file. Do not loop on curl retries first — one failed scripted fetch on this portal class, go straight to the browser. (pdf-form-filler's 'Downloading government form PDFs' section cross-references this rule.)


## The agent-browser fallback

```bash
agent-browser open "<url>"
agent-browser wait --load networkidle
agent-browser wait 2500          # short fixed wait for late-rendering content
agent-browser get text "body"    # full rendered text, including the section you need
```

Notes:
- `wait --load networkidle` + a 2–3s fixed wait catches content that renders after the load event (Workday postings, lazy-loaded sections).
- For a page that still renders thin, try `agent-browser reload` + a longer fixed wait (5–6s).
- If the body comes back as ~160 bytes saying *"The page you are looking for doesn't exist"*, the item/posting was removed (a genuine 404) — that is not a fetch failure; it means the content is gone. Report it; don't keep trying.
- The rendered body is often one long line; to extract a specific section (e.g. "Basic Qualifications"), grep/slice the saved text rather than eyeballing a truncated preview.

## When agent-browser ALSO fails: Cloudflare-protected share/export links

The agent-browser fallback above assumes the page is JS-rendered but NOT actively blocking automation. A distinct class of sites sits behind a Cloudflare (or similar) bot-challenge that blocks BOTH layers of the fallback chain: `webfetch` returns the empty JS shell (the standard pivot signal), AND `agent-browser` opens the page but lands on the Cloudflare challenge / "Just a moment..." interstitial instead of the content. ~~The Cloudflare JS/Turnstile challenge cannot be solved programmatically by a headless or even a real automated browser session.~~ (FALSIFIED 2026-09-25: HEADLESS sessions stall, but REAL system Chrome over CDP auto-clears the challenge with zero human interaction — see the golden path two sections below.)

**Known affected URL class:** `claude.ai/share/*` (Claude conversation share links) — discovered 2026-07-23. Likely siblings (same risk profile, not yet confirmed): Google Docs/Drive share links, Notion public pages, any site fronted by Cloudflare's "Under Attack" / bot-fight mode for unauthenticated traffic.

**Root cause:** Cloudflare bot management issues a JS/Turnstile challenge to non-human traffic. Headless fetch gets an empty challenge page; automated browsers get the same challenge page (the solver requires human interaction or a real trusted-browser fingerprint the automation does not have). This is NOT a "webfetch failed, try harder" situation and NOT an "agent-browser needs a longer wait" situation — no amount of waiting or reloading clears a Cloudflare challenge for automation.

**Workaround (2026-07-23 version, SUPERSEDED 2026-09-25):** ask the user to paste the content directly into the chat. ~~There is no automated path.~~ There IS one: real system Chrome over CDP (golden path below). What remains true: do NOT burn turns on a second webfetch variant, URL-pattern guesses, or waiting/reloading headless agent-browser — they all hit the same wall. The one escalation worth trying before asking the user is the real-Chrome pass.

**One-attempt rule extension:** just as one empty webfetch is enough to pivot to agent-browser, one agent-browser Cloudflare-challenge page on a SHARE/EXPORT link is enough to stop and ask the user. The diagnostic signature: `agent-browser open` succeeds (no error) but the page text is the challenge interstitial ("Just a moment...", "Checking your browser", "Verify you are human", a Turnstile checkbox) rather than the expected conversation/document content. If you see that, immediately ask the user to paste — do not retry.

Fallback chain (updated 2026-09-25): webfetch empty → agent-browser headless → (Cloudflare challenge stalls) → REAL Chrome over CDP → ask the user. The terminal case is now one step later; recognizing each rung's failure signature fast still saves 3-5 wasted turns.

### Amendment (2026-08-28): mirrorable content gets a MIRROR PIVOT before "ask the user"

The "ask the user to paste" workaround above is terminal for SHARE/EXPORT links — content that exists in exactly one place, with a human on the other end who can paste it. It is NOT terminal for MIRRORABLE content: artifacts that exist on many sites (APKs, datasets, installers, public binaries). When a Cloudflare challenge blocks one mirror, the content is usually one pivot away on a server-rendered sibling site.

Escalation for mirrorable content:

1. **Pivot to a server-rendered mirror of the same artifact BEFORE any further browser work.** For Android APKs (instance: apkpure.com download pages, 2026-08-28, VeSync reverse-engineering arc): the candidate curl-friendly mirrors are apkcombo, apkfab, and apkmonk app pages — fetch the app page with plain `curl` and grep for `.apk`/`.xapk` hrefs. Verified dead ends from that session, do NOT retry: `apkeep -d apk-pure` downloads nothing (APKPure's API returns an EMPTY version list; apkeep 1.0.0 exits 0 having produced no file — never trust exit 0 alone, verify a file landed); direct `d.apkpure.net/b/APK|XAPK/<pkg>?version=latest` URL patterns 404; the google-play source needs credentials; evozi requires a JS token.
2. **`--headed` mode** (visible window) sometimes passes challenges a headless session trips (removes the HeadlessChrome UA tell) — UNTESTED against Cloudflare "Just a moment..." pages; per the Unsplash BotStopper discipline below, do not claim it works without testing. It pops a window briefly; Eric accepted that trade-off 2026-08-28.
3. **Ask the user** only when the content is genuinely single-sourced (share links) or every mirror is blocked.

Full ladder (updated 2026-09-25): webfetch empty/too-large -> agent-browser headless -> Cloudflare challenge stalls -> server-rendered mirror pivot (mirrorable content) or REAL Chrome over CDP (single-sourced content) -> ask the user (last resort).

### GOLDEN PATH (2026-09-25): real system Chrome over CDP clears Cloudflare and extracts claude.ai/public/artifacts

Verified end-to-end on `https://claude.ai/public/artifacts/<uuid>` (Jen Brady course proposal). This supersedes the 2026-07-23 "ask the user to paste" terminal verdict for this URL class. The rungs, with exact working commands:

1. **webfetch** → 200 but empty JS-rendered app shell. **agent-browser headless** → opens fine but title stays `Just a moment...` forever (Turnstile never auto-resolves under HeadlessChrome). One poll is enough to diagnose.
2. **Launch REAL Chrome with a throwaway profile over CDP** (subshell double-fork so it survives the bash tool; throwaway dir because Chrome 136+ ignores CDP on the default profile — memory #63; headed-but-backgrounded per Eric's standing preference — memory #18):

```bash
PORT=9233
lsof -i :$PORT >/dev/null 2>&1 && PORT=9244   # dodge port collisions
( nohup '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' \
    --remote-debugging-port=$PORT --user-data-dir=/tmp/chrome-artifact-profile \
    --no-first-run --no-default-browser-check >/tmp/chrome-artifact.log 2>&1 & )
for i in $(seq 1 20); do curl -s http://localhost:$PORT/json/version >/dev/null 2>&1 && break; sleep 0.5; done
agent-browser --cdp $PORT open "https://claude.ai/public/artifacts/<uuid>"
for i in $(seq 1 24); do
  T=$(agent-browser --cdp $PORT get title 2>/dev/null)
  [ -n "$T" ] && [ "$T" != "Just a moment..." ] && break
  sleep 2
done   # real Chrome auto-clears Turnstile in seconds — no human interaction
```

3. **The artifact renders in a SANDBOXED CROSS-ORIGIN IFRAME** on `www.claudeusercontent.com`. In-page JS cannot read it (`f.contentDocument` throws). Dead ends, do NOT retry: `curl https://www.claudeusercontent.com/artifact/<uuid>` with a Chrome UA → 200 but empty app shell; navigating the tab directly to that URL → redirects to login (session-scoped).
4. **The cross-origin iframe is a separate CDP target.** List targets, find `type: "iframe"` with the claudeusercontent URL, and attach to its `webSocketDebuggerUrl` directly:

```python
# /tmp/extract_iframe.py — run: uv run --with websocket-client python /tmp/extract_iframe.py
import json, urllib.request
from websocket import create_connection
targets = json.load(urllib.request.urlopen("http://localhost:9233/json"))
iframe = next(t for t in targets if t.get("type") == "iframe" and "claudeusercontent.com" in t.get("url", ""))
ws = create_connection(iframe["webSocketDebuggerUrl"], timeout=30, suppress_origin=True)  # suppress_origin is LOAD-BEARING
ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {
    "expression": "document.documentElement.outerHTML", "returnByValue": True}}))
while True:
    msg = json.loads(ws.recv())
    if msg.get("id") == 1:
        open("/tmp/artifact-iframe.html", "w").write(msg["result"]["result"]["value"]); break
```

   Without `suppress_origin=True` the DevTools WebSocket rejects the upgrade on an Origin-header mismatch — fix the flag, do NOT restart Chrome (session 2026-09-25 burned a turn on exactly this).
5. **The artifact HTML is NOT in the iframe's visible DOM** — BeautifulSoup text comes back nearly empty. It lives in the **RSC (React Server Components) flight payload**: the full artifact HTML is embedded double-escaped inside script JSON strings. Recover it:

```python
import html as h
raw = open("/tmp/artifact-iframe.html").read()
start = raw.find('&lt;!DOCTYPE')
if start == -1: start = raw.find('&lt;html')
end = raw.rfind('&lt;/html&gt;')
chunk = h.unescape(raw[start:end + len('&lt;/html&gt;')])          # entity pass
chunk = chunk.replace('\\n','\n').replace('\\"','"').replace('\\\\','\\')  # JSON-string pass
```

   Then slice from the artifact's own `<body` onward and BeautifulSoup for text.
6. **Cleanup:** kill the throwaway Chrome (`pkill -f chrome-artifact-profile`) and remove /tmp files. Eric's daily Chrome is untouched throughout.

Generalizes beyond claude.ai: any Cloudflare-gated single-sourced page where headless stalls. The real-Chrome pass costs ~30s and one throwaway profile; try it BEFORE asking Eric to paste.

## When `get text "body"` returns base64 / image noise

On media-heavy single-page sites (research blogs with a hero collage, marketing landing pages, image grids), `agent-browser get text "body"` can SUCCEED but return hundreds of KB of base64-encoded data (inline `<svg>`/`<canvas>` payloads, data-URI images) that bury the actual prose. The output is technically "text" but dominated by image payloads, so the real content is unreadable.

Escalation ladder:

1. First try targeting the content container directly — often excludes header/footer/nav AND some of the noise:

   ```bash
   agent-browser get text "main"
   ```

2. If still noisy, clean via `agent-browser eval` — clone the container, strip noise tags from the CLONE (leaves the live DOM intact), and return `textContent`:

   ```bash
   agent-browser eval "(() => { const m = document.querySelector('main') || document.body; const c = m.cloneNode(true); c.querySelectorAll('script,style,svg,canvas,img').forEach(e => e.remove()); return c.textContent; })()"
   ```

Why it works: `cloneNode(true)` + removing from the clone never mutates the rendered page; stripping `script/style/svg/canvas/img` drops the base64/image payloads while keeping the prose text nodes. Target `<main>` when present (also drops chrome); fall back to `<body>`.

Worked example (2026-07-16, schema-harness.github.io): `get text "body"` on the landing page returned ~512 KB of base64 from the hero collage; cloning `<main>` and stripping `script/style/svg/canvas` recovered the clean article text.

## Batch fetching

Loop multiple URLs, saving each `get text "body"` to its own file, so you can read/section them individually:

```bash
for entry in "${urls[@]}"; do
  name="${entry%%||*}"; url="${entry##*||}"
  agent-browser open "$url" >/dev/null 2>&1
  agent-browser wait --load networkidle >/dev/null 2>&1
  agent-browser wait 2500 >/dev/null 2>&1
  agent-browser get text "body" 2>/dev/null > "/tmp/jobs/$name.txt"
done
```

## Recursive docs-site extraction (capture COMPLETE content, not just landing page)

When the user asks to **study** or **research** a site (not just extract one page), the goal is to capture the COMPLETE conceptual content — not just the landing page. This is a recursive crawl: extract the landing page, discover its subpage links, then visit each.

```bash
# STEP 1: Navigate to the site and render
agent-browser open "<url>"
agent-browser wait --load networkidle
agent-browser wait 2500

# STEP 2a: Extract the full visible text body
agent-browser get text "body"

# STEP 2b: Extract ALL hyperlinks on the page (href attributes)
#          — this discovers subpages on a docs/conceptual site
agent-browser eval "Array.from(document.querySelectorAll('a[href]')).map(a => a.href)"

# STEP 3: For each discovered subpage URL (filter to same-origin, deduplicate):
#   - navigate, wait networkidle + short wait
#   - extract the text body
#   - save to its own file for individual reading
for suburl in "${subpages[@]}"; do
  agent-browser open "$suburl" >/dev/null 2>&1
  agent-browser wait --load networkidle >/dev/null 2>&1
  agent-browser wait 2000 >/dev/null 2>&1
  agent-browser get text "body" > "/tmp/site-extract/$(slugify "$suburl").txt"
done
```

Key points:
- **Extract hrefs, not just text.** A docs site's conceptual content lives in its subpages (/concepts, /spec, /about, /docs/...). The landing page alone is insufficient when the user wants to "study" or "understand" a site's ideas.
- **Filter discovered URLs** to same-origin relative paths; skip mailto:, external links, anchors (#), and duplicates. Normalize relative hrefs against the base URL.
- **Load the agent-browser skill FIRST** (via the skill tool) before starting the extraction workflow — it documents the exact command surface and any gotchas for the installed version.
- **The user's standard (2026-07-16):** "The goal is to capture the complete conceptual content of the site, not just the landing page." When asked to study/research a site, ALWAYS plan the recursive crawl, not a single-page extraction.

## Search engines (DuckDuckGo, Bing, Google) — don't cascade across engines

When a **search engine** (not a content URL) returns a CAPTCHA / challenge / empty result page for your programmatic query, do NOT try a second search engine. All major search engines (DuckDuckGo, Bing, Google, Yahoo) detect automated queries the same way and will CAPTCHA-block you for the same reason in the same session — cascading from DuckDuckGo to Bing (or Bing to Google) is the wasted turn. One CAPTCHA'd search engine means the whole CLASS is blocked for this session.

Pivot immediately to one of:

1. **DIRECT URL fetches of known authoritative sources** (preferred — no CAPTCHA, structured data):
   - SEC EDGAR (`financial-research-fallback`), PyPI JSON API (`pypi-package-metadata-json-api`), Wikipedia wikitext (full text with inline citations), official docs sites, arXiv, university press releases, government databases. See the `*-research-fallback` skill family for the accessible-source map per domain.
   - These endpoints serve JSON/HTML to GET requests without challenge pages.
2. **agent-browser to perform the search itself** — a real browser session passes the CAPTCHA heuristic that headless fetches trip. Use the open → wait networkidle → get text body flow on the search-engine results page, then extract result links and fetch each.

Diagnostic signature (the wasted-turn pattern to short-circuit):
- Assistant says "DuckDuckGo is now consistently CAPTCHA-blocking me" → then "Let me try Bing" → then "Bing is also CAPTCHA-blocking" → THEN pivots. The middle sentence is the waste. After the FIRST search-engine CAPTCHA, pivot directly.

The one-attempt rule from the Recognition section ("one webfetch attempt is enough to diagnose — including the reCAPTCHA / challenge page variant") EXTENDS to search engines: one CAPTCHA'd search engine = the whole class is blocked; pivot, don't retry across engines. Discovered 2026-07-18 during EOSS grant letter-of-support research (verifying Wolf Vollprecht credentials, the OpenFold3 pixi claim, and Eric's Moderna title), where DuckDuckGo then Bing both CAPTCHA'd before the assistant pivoted to direct URL fetches of authoritative sources.

### Variant: built-in search tool gets CANCELLED (quota pressure, 2026-08-29)

A sibling signal to CAPTCHA: the web *search tool call itself* gets CANCELLED — the call is cut off before returning anything (not empty results, not a CAPTCHA page). After TWO cancellations of the same search tool in one session, read it as QUOTA PRESSURE on the search backend integration, not a broken backend; further retries of the same tool are wasted turns. Pivot immediately to: (1) DIRECT fetch of the authoritative source (the vendor's own docs page for factual questions), and (2) in parallel, the alternate search integration (Exa MCP `web_search_exa`). Verified 2026-08-29: two cancelled websearch calls while researching GLM weekend rate limits; direct Z.ai docs fetch + Exa answered on the first attempt after the pivot. The cancellation itself is the diagnosis signal — do not spend a third retry confirming it.

## Cancelled mid-call search = provider quota pressure — pivot to Exa MCP (2026-08-29)

A DISTINCT search-failure signal from CAPTCHA (challenge page returned) and empty (content unreachable): the built-in **websearch tool call itself gets CANCELLED mid-call** — no results, no challenge page, just cancellation, repeatedly in the same session.

- **TRIGGER:** websearch cancelled 2+ times in one session, especially late in a long session.
- **ROOT CAUSE (refined 2026-08-29, later same day):** Z.ai's UNPUBLISHED DYNAMIC CONCURRENCY/RESOURCE limit, NOT the credit quota — Eric is on the MAX tier (GLM-5.3-Flash; 28k credits/5h, 140k/week; Flash bills 0.4x off-peak, weekends off-peak all day) and STILL hits limits, so the huge credit quota is amply not binding. The concurrency limit fluctuates with live platform capacity (Max > Pro > Lite), making failures TRANSIENT: unilateral rapid retries are wasted turns, but a retry in a LATER turn — e.g. user-commissioned ('lets try again') — can succeed (verified 2026-08-29). Distinguish from CAPTCHA blocks (whole class session-sticky). Diagnose quota-vs-concurrency at z.ai/manage-apikey/subscription: credits depleted = quota; credits ample + still erroring = concurrency.
- **FIX:** after the FIRST cancellation, route around instead of retrying: (1) use the Exa MCP search integration (`tools.exa.web_search_exa`), and/or (2) fetch the authoritative source's docs directly by URL.
- **Verified working 2026-08-29** (Z.ai weekend-rate-limit research): websearch cancelled twice; direct docs fetch + Exa search both succeeded on the first try.

Related diagnostic: repeated tool-call failures/cancellations late in a session can be the QUOTA speaking, not the tool being broken — check the provider-plan angle before blaming the backend.

CONFIRMED later 2026-08-29: the top tier does NOT exempt — Eric is on the Z.ai coding plan MAX tier (GLM-5.3-flash) and still hits resource rate limits. REFINE the root cause above: when credits remain, the binding constraint is the separate DYNAMIC concurrency/resource limit (unpublished, no RPM number, fluctuates with Z.ai's live capacity — "Max > Pro > Lite" is the entire published spec), not the 5h/weekly credit quota. Diagnose via https://z.ai/manage-apikey/subscription: credits low = quota; credits remaining + errors/cancellations = concurrency limit. Weekend off-peak hours bill at 0.4x but attract load — cheap hours are contended hours. Failures are TRANSIENT: after routing around (Exa/direct fetch), a plain retry of the original tool next turn often just works. Under active throttle, long single-turn generations can truncate mid-stream — lead with the actionable diagnosis and keep the response compact.

## Worked example (2026-07-15, Moderna job-posting fit assessment)

Needed the full job descriptions from seven `modernatx.wd1.myworkdayjobs.com` postings to assess a candidate's fit. Three `webfetch` attempts all returned empty (Workday is fully client-side rendered). Switching to `agent-browser` returned the complete posting on the first try — including the decision-critical "Here's What You'll Need (Minimum Qualifications)" sections with exact year/experience requirements, which titles alone could not have provided. One of the seven URLs returned a 404 "page doesn't exist" (posting removed) — correctly diagnosed as gone rather than as a fetch problem.

Lesson Eric stated explicitly: *don't presume to know a page's content from its title; if webfetch can't get it, use agent-browser.* Guessing job-requirements from titles produced a wrong assessment (understated a hard "5+ years Power Platform" requirement as a "stretch"; called a junior-level role a "complete mismatch"). The real minimum qualifications are the substance, and only the rendered page has them.

## Worked example 2 (2026-07-16, schema-harness.github.io research)

Asked to study https://schema-harness.github.io/ (a GitHub Pages site) and synthesize how its ideas could evolve opencode-autolearn. Three `webfetch` attempts all returned "too large" (>5MB response). The assistant recognized it should pivot to agent-browser but burned 3+ turns *narrating* the pivot without actually loading the skill or running the commands. The user intervened with an explicit STEP 1-2-3 procedure: (1) load the agent-browser skill, (2) navigate + wait networkidle + extract text body AND all hrefs, (3) recursively visit each subpage.

Two lessons reinforced:
1. **"Too large" = "empty" for pivot decisions.** A >5MB webfetch response is the same signal as an empty one — the content is JS-rendered and webfetch cannot reach it. Switch after ONE attempt; do not retry.
2. **Recognizing a skill applies ≠ executing its procedure.** Citing "per my webfetch-empty-use-agent-browser skill, I'll switch to agent-browser" across multiple turns without actually calling `skill({name:"agent-browser"})` or running any agent-browser command is the failure mode. When you identify the applicable skill, ACT on it immediately — load it, run its commands — don't narrate the intention.


## Variant: URL-pattern guessing after search CAPTCHA (do NOT substitute for agent-browser search)

A distinct wasted-turn cascade from the same 2026-07-18 EOSS session. After DuckDuckGo and Bing both CAPTCHA'd, the assistant did NOT pivot to agent-browser search (option 2 above) — instead it started **guessing URL patterns from memory**, trying each one via webfetch:

- `eoasspec.org` (does not exist)
- `chanzuckerberg.com/news` (404)
- `chanzuckerberg.com/blog/...` (404)
- `chanzuckerberg.github.io/eoss-ar2022/` (404)
- various blog-post slug guesses

Each guessed 404 burned a turn. Five+ guesses later, the assistant finally loaded the agent-browser skill.

**The gap this names:** Option 1 above ("direct URL fetch of known authoritative sources") requires you to **already KNOW** the authoritative URL. When you DON'T know it (you're trying to discover WHERE a fact lives — e.g. "which page lists the EOSS Cycle 4 cohort?"), option 2 (agent-browser search) is **mandatory, not optional**. URL-pattern guessing from memory is a third, unlisted path that feels productive (each guess is a plausible URL) but has the same hit rate as random — institutional URL structures are not guessable (eoasspec.org doesn't exist; chanzuckerberg.com uses /blog not /news; the EOSS reports live at a github.io subdomain with an unguessable slug).

**Diagnostic signature (the wasted-turn pattern):**
- Search engines CAPTCHA → assistant says "let me try the authoritative source directly" → guesses `org-name.domain` → 404 → guesses `org-name.domain/news` → 404 → guesses `org-name.domain/blog` → 404 → THEN loads agent-browser.
- Each "let me try X" where X is a URL you are GUESSING (not one you've verified exists) is the waste.

**Rule:** When search is blocked AND you cannot name the exact URL from a verified prior fetch, go to agent-browser to **search** (navigate to a search engine in the real browser, or navigate to the parent org's site and crawl for the link). Do not substitute URL-pattern guessing — the two pivot options are (1) fetch a KNOWN URL, or (2) agent-browser search; there is no option (3) "guess URLs."

## Author/topic research: fetch the tag/category INDEX first (not individual post URLs)

A specific, high-value sub-case distinct from the institutional-URL-guessing cascade above. When researching a named AUTHOR's writing on a TOPIC (e.g. "what has Simon Willison written about cognitive debt?"), do NOT guess the author's date-based post URLs (`/YYYY/Mon/D/slug/`) — they 404 almost always, because you cannot reconstruct the exact day/month/slug from memory. Instead, fetch the author's **topic INDEX page**, which is a predictable, non-guessed URL that lists every post on that tag in one fetch.

**Simon Willison's site (the canonical example, 2026-07-24):** the URL `https://simonwillison.net/tags/<kebab-topic>/` returns a page listing every post tagged with that topic. Two guessed date-URLs both 404'd; ONE fetch of `https://simonwillison.net/tags/cognitive-debt/` surfaced six relevant posts at once (the "Understand to participate" writeup of Geoffrey Litt's talk, "Thoughts on slowing the fuck down", his own "Interactive explanations" agentic-engineering guide, plus Simon Højberg "The Programmer Identity Crisis" and Steve Yegge references) — described in-session as "a goldmine." Willison also maintains a `/guides/<section>/<page>/` tree (e.g. `/guides/agentic-engineering-patterns/interactive-explanations/`) for longer-form material.

**Why this beats both alternatives:**
- vs guessing individual post URLs: the index is ONE predictable URL; post URLs are many and unguessable.
- vs spinning up agent-browser to search: the tag index is a server-rendered STATIC page (no JS), so plain `webfetch` returns it immediately — cheaper than a browser session.

**Generalization:** many author blogs / personal sites expose a tag or category index at a predictable path (`/tags/<topic>/`, `/topics/<topic>/`, `/category/<topic>/`, `/blog/tag/<topic>/`). When the author is a recurring citation source (Willison, Matuschak, Højberg, Litt, Fowler), prefer the index fetch as the FIRST move — before any post-URL guess or browser pivot.

**Diagnostic signature (the wasted-turn pattern):**
- Assistant knows an author wrote about a topic → guesses `/author/2025/May/1/topic-slug/` → 404 → guesses a second date/slug → 404 → THEN tries the tag page.
- The two guessed 404s are the waste; the tag page should have been the first fetch.

**Rule:** When researching an author's writing on a topic, the tag/category index is the authoritative discovery URL — construct it from the author's known index pattern and fetch it directly. Reserve date-based post-URL guessing for when you already know the exact slug from a prior fetch.

**Distinct from the "Variant: URL-pattern guessing" section above:** THAT governs institutional URLs you genuinely cannot know (use agent-browser to search). THIS governs author blogs whose tag-index URL IS reliably constructible from a known pattern — so fetch the index directly rather than escalating to the browser.

## Enrichment vs load-bearing — degrade gracefully instead of pivoting (2026-08-23)

When the unfetchable content is **optional enrichment** rather than load-bearing for the deliverable, a full browser session is disproportionate. Decision rule: if a known-good summary already exists and the missing detail would merely enrich it (a talk slide outline, a nice-to-have example list), take the CHEAP LADDER instead of the browser pivot:

1. **ONE alternative static fetch** of the same information from a predictable sibling source — for a hosted reveal.js deck that is the GitHub repo README.
2. If that also fails, **degrade gracefully** — write the general-but-accurate version and move on.
3. **NEVER invent the missing specifics.**

Instance (2026-08-23, website talks spruce-up): the reveal.js deck for the Modern Principled DS Workflow talk is JS-rendered (webfetch empty), the repo README listed no outline, and the correct move — taken — was to keep the description general and NOT fabricate the five principles. A general-but-accurate description beats a specific-but-hallucinated one every time.

The standing rule from Eric ("if you can't webfetch, switch to agent-browser") governs the **load-bearing** case: when the page IS the deliverable (job-posting minimum qualifications, docs you must follow, a price you must report), pivot immediately. This section governs the **enrichment** case. Distinct from the agent-browser-MISSING pre-flight fallback (that pivots for lack of a tool; this declines for lack of need).

## Citation-link verification — curl 200 on a JS-rendered site is NOT verification (2026-08-30)

Adding or verifying a book/citation link in published content (blog post, vault note): a bare status code is not verification. Verified dead ends, do not retry: `benjaminhardy.com` book page 301s to a 404 (a redirect landing on 404 is dead — check the FINAL status with `curl -sIL`, not the first response); the Hay House publisher page is 404; `goodreads.com` returns HTTP 200 but a JS-app shell with no verifiable body text via curl — a 200 from Goodreads verifies NOTHING about page content (same JS-rendered class as the Unsplash search pages below).

Cheap-ladder procedure (enrichment case) before deferring to the user:

1. Direct fetches of the canonical sources (author site, publisher).
2. If those dead-end, run ONE search (exa `web_search_exa` or built-in websearch) for `<title> <author> goodreads` — search results surface the canonical URL without fetching the JS-rendered page. This rung was missed 2026-08-30 (Who Not How link: three dead direct fetches, then asked Eric for the URL).
3. Only if search also fails: ship the prose UNLINKED and flag the open item to Eric.

NEVER guess or fabricate a citation URL — unlinked prose is always defensible, a hallucinated link is not.

## Verified stock imagery (Unsplash): extract live photo IDs, never guess them (2026-08-23)

When a deliverable must ship REAL imagery (design brief: "When the brief implies imagery, you must ship imagery — zero images is a bug"), you need photo URLs that verifiably resolve. Two Unsplash facts combine into one trap:

1. **Guessed photo IDs 404.** `images.unsplash.com/photo-<hash>` IDs are opaque — you cannot construct them from memory or pattern (an even harder version of the URL-pattern-guessing section above).
2. **Unsplash search pages block plain HTTP.** `https://unsplash.com/s/photos/<query>` is JS-rendered with bot detection — `curl` gets blocked. This is the webfetch-empty pivot case, and the imagery IS load-bearing (part of the deliverable), so pivot immediately.

**Extraction recipe (agent-browser, dedicated session):**

    agent-browser --session unsplash open 'https://unsplash.com/s/photos/<query>'
    agent-browser --session unsplash wait --load networkidle
    agent-browser --session unsplash eval "[...document.querySelectorAll('img')].map(i => i.src).filter(s => s.includes('images.unsplash.com/photo-')).slice(0, 12).join('\n')"

Then **verify each candidate** with `curl -sI <url>` → expect 200 before embedding (append sizing params `?q=80&w=...&auto=format&fit=crop` to taste). Alternative path without a browser session: exa/web search for `unsplash.com/photos <subject>` photo pages, then fetch a photo page and extract its `og:image` (an images.unsplash.com URL) — but still HEAD-verify it.

**Diagnostic signature:** the assistant "recalls" a plausible photo ID from memory, embeds it, and it 404s at render time; or it curls the Unsplash search page, gets blocked, and starts deliberating instead of pivoting. Both wasted paths are avoided by: search page via agent-browser → extract live IDs → curl HEAD verify → embed only 200s.

Instance (2026-08-23, White Mountains family-trip itinerary page): curl on unsplash.com/s/photos/franconia-notch blocked; pivot to agent-browser eval planned per this rule.

## UPDATE (2026-08-23, later same day): Unsplash BotStopper escalation — the eval recipe above now fails; Wikimedia Commons API is the working fallback

The agent-browser eval recipe above **no longer works on Unsplash**: the search page now serves **BotStopper "Access Denied" even to a headless agent-browser session** (empty eval output, no `img` srcs to extract; the page title/body show the block). Unsplash has escalated from JS-rendering to active bot blocking. Untested fallback: `--headed` mode (removes the HeadlessChrome UA tell) — do not claim it works without testing it.

**Working alternative for real-place imagery (landmarks, parks, cities, regions): the Wikimedia Commons API** — no browser session needed, curl-friendly, free-licensed (CC/PD):

    curl -s 'https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch=<terms>&gsrnamespace=6&prop=imageinfo&iiprop=url|size|mime&iiurlwidth=1600&format=json'

Returns `imageinfo` with **stable `upload.wikimedia.org` thumbnail URLs at the requested width** (`iiurlwidth=1600`), plus width/height/mime for filtering. For well-documented areas (national forests, notable landmarks like Franconia Notch or the Kancamagus Highway) the curation is solid — and photos of the ACTUAL place beat generic stock for keepsake/trip/editorial use.

**Selection filter:** `mime=jpeg`, decent resolution, landscape; prefer modern flickr-import uploads (historic "Postcard"/archive items are often B&W); **match image season to the subject date** — an October-foliage highway photo is wrong for an August trip.

**Two gotchas:**

1. **Copy file titles EXACTLY from the search results** into any follow-up title query. A guessed/reconstructed title silently returns a page with **no `imageinfo` element** — not an error; the API page exists, the title does not. When a title query comes back imageinfo-less, the title guess is wrong: re-search and copy the exact string.
2. **Rapid `curl -I` bursts to `upload.wikimedia.org` get 429-throttled.** A 429 means rate-limited, **NOT a missing file** — do not prune 429'd URLs as broken. Chain the wait inside the command (`sleep 20; curl -sI <url>`) instead of ending the turn to "pause".

**Preference order for verifiable imagery of real places:** Commons API first (curl-verifiable, licensed, zero browser overhead); Unsplash agent-browser eval only when Unsplash specifically is required, and only headed.

Instance (2026-08-23, White Mountains trip, continuation): headless agent-browser on unsplash.com/s/photos/* → BotStopper Access Denied, empty eval; pivot to Commons API found verifiable hero/day imagery (Presidential Range, Loon Mountain, Flume Gorge, Echo Lake, Kancamagus) in one scripted query pass.

## UPDATE (2026-08-27): 403 bot-block → search-first pivot (facts), and stale search indexes for recent Substack posts

A **403 from webfetch is publisher bot-blocking — a different failure mode from the JS-shell/empty case.** Before spinning up a browser session, ask what you actually need from the page:

- **You need FACTS about the page** (names, dates, deadlines, scope, pricing): pivot to a **web search** (exa / custom_websearch) FIRST. Search results and snippets often answer fact questions completely, at a fraction of the cost of a browser session. Verified 2026-08-27: slas-discovery.org 403'd on webfetch; one exa search yielded the entire guest-editor list, submission deadline, and scope of the call-for-papers with zero browser usage.
- **You need the page CONTENT itself** (verbatim text, form filling, screenshots, tables): agent-browser remains the pivot.

Companion gotcha — **third-party search indexes lag Substack by weeks**: exa reported Jun 11 as the latest dspn.substack.com post when an Aug 21 post existed. When recency matters on a Substack publication, fetch `<publication>.substack.com/archive` directly instead of trusting search-index recency.

## Output FORMAT: markdown strips `<head>` — request HTML format for design tokens / meta tags (2026-09-01)

A DISTINCT failure mode from all the blocked/JS-rendered cases above: the fetch SUCCEEDS but the default **markdown output strips the entire `<head>`**, so anything living there — inline `<style>` blocks (brand palettes, design tokens), `<meta>` tags, JSON-LD — is invisible no matter how many times you refetch. This is a format problem, not a fetch failure: do NOT pivot to agent-browser or burn curl retries first.

Fix: request webfetch's **HTML output format**, which preserves raw markup. Verified 2026-09-01 extracting BCG's brand palette from bcg.com: markdown output omitted `<head>`; the HTML format returned the full markup including `<style id="global-colors">` with the authoritative hex codes. (Generalizes: corporate design tokens usually live in an inline `<style>` block in `<head>` — markdown mode can never see them.)

Companion heuristic from the same arc: a curl response of only a few hundred bytes (365 here) is a **block/redirect page, not real content** — before drawing conclusions, save it to a file and READ what you actually got. Same family as the ~160-byte "page doesn't exist" agent-browser case above and the Mass.gov block-page variant.
