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

## LAN & phone access

The reliable path to put the dashboard on a phone is **same-Wi-Fi LAN access**. The
scaffold binds `0.0.0.0` and prints `http://<LAN-IP>:PORT` via `_lan_ip()`. On the
phone, open that URL — the sidebar auto-collapses into a hamburger drawer (CSS in
assets/index.html, `max-width:880px` + `.sidebar.open` + `.scrim`).

- **OS firewall** is the #1 LAN gotcha. The python binary running `server.py` needs an
  "Allow incoming connections" rule. If the user gets a silent timeout, have them allow
  that python binary in the OS firewall settings. A localhost `127.0.0.1` fetch still
  works regardless; only LAN/phone clients are filtered.
- A momentary timeout right after a server restart is *not* the firewall — the warm-up
  thread may still be fetching. Re-test after ~2s before assuming it's blocked.

### Tunnel options (off-network / public access)

Tunnels keep the backend local (so the local scan survives). Reliability varies by
network. On a *restricted* network (GitHub throttled, broker WebSockets hang), expect:

| Tool | Command | Pros | Failure mode |
|---|---|---|---|
| **cloudflared** | `cloudflared tunnel --url http://localhost:PORT` | Stable, no password, HTTP→HTTPS | Binary download from GitHub blocked → can't install |
| **localtunnel** | `npx localtunnel --port PORT --password x` | Pure Node, no binary | Broker WebSocket handshake hangs forever on throttled net |
| **pinggy** | `ssh -4 -p 443 -R 0:localhost:PORT a.pinggy.io` | No binary; SSH egress often open | Free relay resets frequently; needs `-4` (IPv6 times out); real URL only printed under a pty |

If every tunnel fails, the only public option is a tiny VPS running `server.py` — but
then the local scan panels are empty (no tooling on the cloud box). Live
news/weather/stock still work. State this trade-off explicitly; never silently drop the
local panels.
