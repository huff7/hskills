# Data Sources & Gotchas (references)

**Scope note.** Everything below documents the *reference implementation* in `assets/` —
it is a catalogue of working endpoints and their gotchas, **not a list of things to
build**. Which of these (if any) apply depends entirely on the modules derived from the
user's pain points in SKILL.md Step 2. A user who never mentioned stocks gets no stock
endpoint. Pull from this file the way you'd pull from a parts bin.

Copy the endpoint + its gotcha when adding a source that a derived module actually needs.
Keep each TTL in sync with how often that data really changes. Nothing here is personal —
scan root, city, and sources all come from the user's `config.json`.

## External APIs (a parts bin — use only what a derived module needs)

| Purpose | Endpoint | Notes / Gotchas |
|---|---|---|
| 微博热搜 | `https://weibo.com/ajax/side/hotSearch` (referer `https://weibo.com/`) | `data.realtime[].word` / `.num`. Needs Referer or 403. |
| 抖音热点 | `https://www.iesdouyin.com/web/api/v2/hotsearch/billboard/word/` | `word_list[].word` / `.hot_value`. No referer needed. |
| Hacker News (AI) | `https://hn.algolia.com/api/v1/search?query=AI&tags=story&hitsPerPage=100` | `hits[].title` / `.points`. Merge with a keyword filter for "AI" topics. |
| 天气 | `https://api.open-meteo.com/v1/forecast?latitude=..&longitude=..&current=..&daily=..` | Free, no key. WMO code → 中文描述见 server.py `WMO` dict. Fallback: `https://wttr.in/<city>?format=j1`. |
| 股票/大盘 | `https://hq.sinajs.cn/list=sh000001,sz399001,...` (referer `https://finance.sina.com.cn`) | **GBK encoded** → use `fetch_text` with gbk fallback. One bad code makes Sina return `sys_auth=FAILED` for the WHOLE batch → always `normalize_code()` first. |

To add a source: write `_fetch_xxx()` returning
`[{"title":..,"hot":..,"src":..}]` and register it in the `NEWS_FETCHERS` list in
`server.py`. Ship only the sources the user's own modules call for.

## Local scan paths (configurable root — default `~/.workbuddy`)

Set `scan_root` in `config.json` to wherever the user's tooling lives (and `agent_db` for
the running-tasks panel). Relative layout inside that root:

- **MCP**: `<root>/mcp.json` → `mcpServers{}`. desc = `url` (if http) else `command + args`.
- **Skills**: `<root>/skills/*/SKILL.md` and `<project>/.workbuddy/skills/*/SKILL.md`.
  Parse the YAML **frontmatter**. Skills frequently use block scalar `|-` for
  `description` — a naive `split(":")` parser breaks; use the `_parse_frontmatter`
  in assets/server.py which collects indented lines after `|`/`|-`/`>`/`>-`.
- **Agents**: `<root>/agents/*/SKILL.md` (may be empty → show friendly "未配置").

## Verification (headless browser — Chrome required)

The dashboard is visual — verify with screenshots, not just curl. Install
`puppeteer` (bundled Chromium) or `puppeteer-core` + a Chrome/Chromium binary.

```bash
# 1) launch the server (background) with the user's python, then confirm reachable
#    without proxy:
NO_PROXY=127.0.0.1 no_proxy=127.0.0.1 curl -s http://127.0.0.1:PORT/api/aitools

# 2) screenshot (Chrome path auto-detected; override via CHROME_PATH if needed):
CHROME_PATH="$(command -v google-chrome || command -v chromium || \
              command -v google-chrome-stable || echo /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome)" \
node -e '
const pptr = (() => { try { return require("puppeteer"); } catch { return require("puppeteer-core"); } })();
(async () => {
  const b = await pptr.launch({executablePath:process.env.CHROME_PATH, headless:"new", args:["--no-sandbox","--disable-gpu"]});
  const p = await b.newPage();
  await p.setViewport({width:1440,height:900});
  await p.goto("http://127.0.0.1:PORT",{waitUntil:"networkidle0",timeout:15000});
  await p.screenshot({path:"_verify.png"});
  await b.close();
})();'
```

Replace `PORT` with the user's configured port. If `require("puppeteer")` fails and
`puppeteer-core` has no Chromium, set `CHROME_PATH` to the installed browser binary.

## Common pitfalls
- **Server dies between turns** → launch via background shell with the user's python
  (`run_in_background`). Don't rely on a previous foreground process.
- **`fetched_at` is null on cache hit** → `cached()` must store an *enriched copy*
  (with `fetched_at`) on the original fetch, and return a fresh `dict` copy on hit.
- **Flex card text overflow** → long URLs break mid-word in a horizontal flex card.
  Use `flex-direction:column` (stacked) + `min-width:0` + `overflow:hidden` +
  `word-break:break-all` on the text. See `.tool` in assets/index.html.
- **Grid whitespace** → `align-items:start` on the grid so short widgets don't
  stretch; give scrollable lists a `max-height` + `overflow-y:auto` instead of
  growing the page.

## Public deployment + PWA (stable URL, phone access without tethering)

The dashboard is reached from the phone over a **stable public URL**, not same-Wi-Fi LAN.
Package the whole workbench in Docker (Step 6) and deploy to a hosted endpoint whose URL
stays valid across sandbox sleep / container recreation.

### Why not LAN / weak tunnels
- **LAN** ties the phone to the same Wi-Fi and breaks the moment you leave home; the OS
  firewall also silently blocks the first LAN hit (must "Allow incoming connections").
- **Weak tunnels** (cloudflared *quick* tunnel / localtunnel / pinggy) keep the backend local
  but the URL often rotates or the relay resets, and they do **not** outlive sandbox sleep.
  Avoid them.
- **Stable tunnels are fine.** A *named* Cloudflare Tunnel on **your own domain**
  (`workbench.yourdomain`) gives a permanent HTTPS URL and bypasses CGNAT / blocked ports via
  outbound connection — it is the recommended zero-cost path for "data stays local". Full
  steps: `references/deploy.md` (路线 B). The deciding test is only one: **is the public URL
  stable + HTTPS?** Stable → usable; rotating → drop.

### Docker sandbox + stable public URL
- Build a single image: `server.py` + `static/` + vendored `echarts.min.js` + `config.json`.
- Persist data via a **mounted volume** (`-v <host>:/app/data` or a named volume) — SQLite
  lives there, never in the image layer. Recreating the container keeps the data.
- Deploy so the platform maps the container port to a **stable public URL** that does not
  change when the sandbox idles. Tell the user the bookmarked link is permanent.

### PWA (manifest.json + service worker)
- `manifest.json` (same origin): `name` / `short_name`, `icons` (192/512 + maskable),
  `theme_color` / `background_color`, `display: "standalone"` (fullscreen, no address bar),
  `start_url`, `scope`. Custom icon + splash derive from `icons` / `background_color`.
- `sw.js`: precache the app shell (`index.html`, `echarts.min.js`, `manifest.json`) so the
  app opens offline; runtime cache for `/api/*` with stale-while-revalidate.
- Register the SW from `index.html`; link the manifest with `<link rel="manifest">`.

**Bundled reference files** (in `assets/`): `static/sw.js` (precache shell + SWR for
`/api/*`), `static/icon.svg` (neutral maskable icon — swap for your branded PNG for best iOS
support), and a dynamic `/manifest.json` route in `server.py` that fills `name` /
`short_name` / `theme_color` / `background_color` from `config.json` (no hardcoded brand).
`index.html` already links the manifest and registers the SW on load.

### Phone "Add to Home Screen" tutorial (delivery)
- **iOS (Safari):** open the public URL → Share (□↑) → *Add to Home Screen* → name it → Add.
  Launches standalone.
- **Android (Chrome):** open the URL → ⋮ menu → *Install app* / *Add to Home screen* → confirm.
- Confirm the installed icon opens with no browser chrome (standalone). Offline reload should
  still show the shell.
