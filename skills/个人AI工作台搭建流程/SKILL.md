---
name: 个人AI工作台搭建流程
description: "个人AI工作台搭建流程（Personal AI Workbench Builder）：Requirement-driven methodology for building a personal local dashboard/workbench/cockpit. Starts from the user's pain points, derives the module breakdown from those pains (never a fixed module list), lets the user choose the tech stack from presented options, then derives endpoints and tables from the confirmed modules. Ships a reference implementation (zero-dependency Python stdlib server + vanilla-JS SPA, SQLite, ECharts, LAN/phone access, dark theme, local tool scanning, and a unified running-AI-tasks panel) as ONE worked example to adapt, not as the required product. Use when a user wants a self-hosted personal dashboard, wants scattered daily info on one local page, wants to see their own local AI tooling, or wants to know what their AI agent is running. NOT for hosted SaaS or multi-user apps. Branding and paths are config-driven — the skill ships NO author-specific labels."
agent_created: true
---

# 个人AI工作台搭建流程（需求驱动方法论）

## Philosophy

**This is a derivation method, not a product spec.**
**This is a conversation, not a form.** The user doesn't speak "module"; they speak life.

The bundled `assets/` are *one* worked example — the modules in them (daily / media /
aitools), the endpoint list, and the table schema all came from **one particular
user's** pain points. They exist to give you (a) inspiration and candidate options, and
(b) a demonstration of how to go from "痛点 → 模块 → 接口 → 表". They are **not** the
module set to install.

Copying the reference modules wholesale is the primary failure mode of this skill. A
dashboard where two thirds of the nav is never clicked is worse than a three-card page
the user opens daily.

**Two things ARE fixed** and should not be re-derived per user:
- the ordering of the process (pains → modules → stack → contracts → code → verify)
- the conventions in *Step 4* and *Generic conventions* (naming, return shape, empty
  state, one-board-one-endpoint, config-not-code)

Everything else — which modules exist, what stack runs them, how many tables — is an
output of the conversation, not an input.

**Seven principles from lived experience:**

1. **先聊生活，再给方案。** 用户面对"你想要哪些功能"答不上来，面对"我理解你需要这 5 个，对不对"就答得很好。先问他在忙什么、想记录什么，再归纳成模块让他删改——绝不上来就套模板。
2. **功能分三层，当场说清代价。** 〔本地〕零门槛 / 〔内容〕一次生成会过期 / 〔联网〕要 key 可能挂。用户要联网型时必须**当场**告诉他代价和替代方案，而不是做完了才说。
3. **6–9 个模块是舒适区。** 少于 5 个单薄，多于 10 个侧栏挤到看不清。超了就建议合并或砍，不要为了"看起来完整"硬凑。
4. **主动推荐最多 2 个，且必须说明为什么。** 从用户的原话里找依据（"你提到久坐→推荐喝水记录"）。不解释理由的推荐像塞私货。
5. **每道闸门都停下来等用户。** 标记只负责让你看见它们，真正决定放不放行的是各步写明的"什么算通过"。别自问自答跨过闸门。
6. **产物是用户自己的。** 个性化信息进 `config.json`，代码里零硬编码。品牌名由用户定，不替他拍板——这个名字每天出现在标题栏里。
7. **配置文件是迭代入口。** 产出一份记录模块清单/风格参数/数据结构的配置文件。以后用户说"加个喝水提醒"，读配置接着改，不用重聊。

## Step 1 — 开放式需求访谈（MANDATORY，禁止跳过）

**不要问"你想要哪些模块"。** 能说出模块名的用户不需要这个 skill。

### 第 1 轮：三个开放式问题（一次问 1-2 个，等回答完再往下）

| # | 问 | 挖的是 |
|---|---|---|
| Q1 | 你平时主要在忙什么？（工作、学习、带娃、做自媒体、备考、减肥……随便说） | 身份，决定后面推荐方向 |
| Q2 | 每天有哪些事是你必须盯着、怕忘的？ | 高频刚需，工作台的骨架 |
| Q3 | 有没有什么是你一直想记录、但没坚持下来的？为什么没坚持下来？ | 未被满足的需求；"太麻烦要专门打开一个 App"=低摩擦机会 |

**用户第一句就带了信息？** （"我是做自媒体的，想做个工作台"）— 保留问候，**删掉 Q1**，改成复述他说的再往下问。当着用户的面问他刚回答过的问题很蠢。

### 第 2 轮：两个定架构的问题（必须问，但像闲聊）

| # | 问 | 决定什么 |
|---|---|---|
| Q4 | 这个工作台主要在电脑上用，还是手机也要看？ | 响应式优先级 / 布局策略 |
| Q5 | 里面会不会有你不想被别人看到的内容？ | 隐私处理方式 |

### 用户不配合时的处理

| 表现 | 怎么办 |
|---|---|
| 答"你看着办"/"随便" | **不要追问第二次**。按身份从灵感清单挑 2 条 + 本地型补几条高频，凑 6-9 条让他删，说"我先按常见的搭一版，你看着删" |
| 连问两轮仍说不出具体场景 | 停止访谈，给最小四件套（计划+打卡+记账+设置），说明"先用起来，用两天你就知道缺什么了" |
| 描述的东西不满足三特征（给团队用的、对外展示的、一次性工具） | **就地退出**，说明这个需求更适合怎么做，不要硬套 |

### 收口：复述确认

用一句话复述你理解的"最痛的三件事"，拿到用户确认后再进入 Step 2。

> 我理解下来，你最痛的三件事是：①每天早上要开好几个页面才能看清今天的情况 ②打卡和日程散在各处老忘记 ③钱花哪了完全没概念。对吗？

**个性化信息（品牌名、城市、路径等）留到 Step 2 之后再收** —— 这时候你还不知道是否需要天气 city 或扫描 root。

### 产出：原始需求快照

访谈收口后、进入 Step 2 之前，趁记忆新鲜，把用户**全部原话**整理成一份《原始需求快照》，存入项目文档（`docs/需求快照_YYYY-MM-DD.md`，或 README 的「原始需求」一节）。内容至少包含：

- Q1–Q5 的逐条原话（按用户自己的措辞，不急着翻译成模块）
- 复述确认过的「最痛三件事」
- 用户明确说不想要的东西 / 说"随便"时被你给的最小集合

这份快照是后续复盘和增量迭代的**原始上下文基准**——几个月后你只会看到翻译后的模块表，会丢失"用户当时到底怎么说的"。增量版（C 版）改动前先读它，能避免把用户的原意改歪。

## Step 2 — 归纳功能清单（你翻译，用户确认）

**从用户的大白话翻译成模块清单。** 格式：

> 我理解下来，你的工作台应该有这些。你看看要删要加：
>
> 1. 📅 **今日计划** — 固定行程 + 勾选打卡〔本地〕
> 2. 💰 **记账** — 收支记录 + 月度统计〔本地〕
> 3. 🔥 **每日热点** — 实时资讯〔联网 · **需要你申请一个 key，约 10 分钟**〕
>
> 另外我想推荐两个你没提但可能用得上的（说明为什么）：
> - 💧 **喝水记录** — 你提到久坐，这个点一下就记一次，几乎零成本
> - 📊 **每周复盘** — 自动汇总本周打卡和记账，周日看一眼
>
> 要不要？不要就直接说删掉。

### 三层分类（每条必须标）

| 标记 | 是什么 | 怎么跟用户说 |
|---|---|---|
| **〔本地〕** | 状态存本机，零门槛 | 不用解释，直接做 |
| **〔内容〕** | AI 一次性生成后写死 | "这部分我一次性生成好放进去，大概够用 X 天，用完了跟我说" |
| **〔联网〕** | 需要实时外部数据 | "这个需要你自己去申请一个 key，约 X 分钟。不想折腾的话也可以换成 XX（替代方案）" |

判断方法：问自己"飞行模式下还能用吗"。能 → 本地或内容；不能 → 联网。

**联网型必须当场给代价和替代方案。** 别把代价藏起来。

### 拆解四问（每个候选模块都要过）

1. **数据从哪来？** 外部 API → 抓取型 / 本机文件/DB → 扫描型 / 用户录入 → 录入型 / 从其他模块算 → 派生型
2. **多久变一次？** 秒/分/时/天/仅操作时 → 决定缓存 TTL
3. **只读还是可写？** 只读 → 一个 GET；可写 → CRUD 四件套
4. **没数据时显示什么？** 每个模块必须有明确空态。想不出来 = 价值不清晰

### 合并与粒度

- **合并判据**：回答同一个问题 / 同一个数据源 / 打开 A 总顺手看 B → 合并
- **粒度**：一模块 ≈ 一屏；少于 3 张卡片考虑并进相邻；一级导航控制在 3–6 个
- **复合模块模式**：当多个痛点都回答"我今天怎么样"时，合成**一个落地页内的子模块**而不是 N 个导航入口（见 Reference implementation 的「每日日常」样例）
- **数量**：6–9 个舒适区；超了建议合并；少于 5 个不要硬凑

### 产出格式

| 模块 | 解决哪句原话 | 数据来源 | 类型 | 频率 | 读/写 | 空态 |
|---|---|---|---|---|---|---|

列完表后主动告诉用户三件事：
1. 哪两个需求你合并了，为什么
2. 哪个建议先砍（一期不做），为什么
3. 没提到但值得加的（**最多 2 个**），各是什么+为什么

> 🔴 **CHECKPOINT 1 · 功能清单**
> 用户逐条确认前不得进入下一步。
> 只回"嗯""好"不算通过——追问一句"有要删要加的吗"，拿到明确答复再走。

## Step 2.5 — 命名与品牌（不能跳过，不要替用户拍板）

**这个名字每天出现在浏览器标题栏和侧边栏顶部。** 随手起个「个人工作台」会让用户觉得这是通用模板不是他的。

问法：
> 给它起个名字吧——会显示在标题栏和侧边栏顶上。很多人用自己的昵称，比如「小鹿的工作台」。你平时喜欢别人怎么叫你？或者你心里已经有名字了？

要拿到：**品牌全名**（不限长度）+ **短名称**（≤4 字，手机桌面图标下用）+ **品牌 emoji**（可选）。

用户说"随便"时，给 2-3 个从访谈信息里取材的候选让他挑，不要真的随便起。

同时收齐个性化配置值（进 `config.json`，代码零硬编码）：
城市 / 默认天气地 / 扫描根路径 / 股票市场 / 品牌色偏好 / 标语（tagline）

## Step 2.6 — 生成闸门（最后一次确认，然后闭嘴动手）

在写任何代码之前，问**最后一次**：

> 还有别的想做进工作台的需求或痛点吗？（比如想加别的模块、别的看板、别的数据源）

- 有 → 回到 Step 2 补拆，重新过 CHECKPOINT 1
- "暂时没有 / 先把这些做扎实" → **停。只做确认过的集合，不脑补。**

> 🛑 **STOP · 这是最后一道可逆点。** 之后返工成本 10 倍。
> 发出确认单后**停止输出、等用户回复**，不得自问自答继续往下。

确认单格式：名字 / 功能清单（含类型标记）/ 技术栈选型（下一步才定）/ 数据存哪。
用户要改某条时按类型回退，改完**重发完整确认单**。

| 改什么 | 回哪一步 |
|---|---|
| 功能增删 | 回 Step 2 |
| 名字/品牌 | 回 Step 2.5 |
| 要不要部署/数据存哪 | 不用回退，Step 5 再定 |

## Step 3 — Tech stack selection (you present, user decides)

Never silently default into a stack. Present a comparison, give a clear recommendation
*with* its cost, then let the user pick.

| Option | Backend | Frontend | Fits | Cost |
|---|---|---|---|---|
| Zero-dependency single file | language stdlib HTTP server | one HTML + vanilla JS | personal use, wants to hand-edit, no toolchain, long-lived | complex interactions get painful; no component ecosystem |
| Light framework | FastAPI / Flask / Express | vanilla JS or Alpine | many endpoints, async, auto docs | dependency install; env drift |
| Modern frontend | any | Vite + React/Vue | complex interaction, heavy component reuse | build step; heavy dep tree |
| Static, no backend | scheduled script emits JSON | static page reads JSON | pure read-only board | no write operations possible |

Also offer, same rules (options + recommendation + user decides): **storage** (SQLite /
JSON file / none), **charts** (library / hand-rolled SVG / none this version), **styling**
(hand-written CSS / utility framework / component library).

When the confirmed modules include **privacy-sensitive data** (journal, weight, ledger,
credentials): also offer an optional **加密存储 (encrypted storage)** path — SQLite with at-rest
encryption (e.g. SQLCipher), or a JSON file encrypted at rest (e.g. `age` / `libsodium`) —
and state the trade-off (one extra dependency / one password to remember). Do not default it
on; let the user decide after seeing the cost, and never silently store plaintext secrets.

Weigh against what the user actually said in Step 1 — *do they edit code, will they install
a toolchain, does it run long-term, is anything real-time, where will they extend next* —
not against what is newest. If their confirmed modules include drag-reorder, rich text, or
multi-step forms, say plainly that vanilla JS will hurt and a framework is warranted.

The bundled `assets/` implement the **zero-dependency** row. If the user picks it, you can
adapt them directly; if not, they are still a valid design reference — port the conventions,
not the files. Record the decision and its rationale in the project README.

## Step 4 — Endpoint & schema derivation

Derive from the confirmed module list. **Do not copy the reference endpoint list.** Modules
the user declined get zero endpoints.

**Naming** — `/api/<domain>/<resource>`, domain = module name. Writable resources get
`GET` list · `POST` create · `DELETE /<id>` · `POST /<id>/<action>`. Derived stats hang off
`/api/<domain>/<resource>/stats`.

**Return shape** — always `{"ok": true, ...}`, failures `{"ok": false, "error": ...}`.
Fetch-type endpoints carry `fetched_at`. One dead upstream degrades its own card only —
never a 500 or a blank page.

**One board, one endpoint** — if a chart and a list in the same module show the same data,
one endpoint returns both. Split sources produce mismatched numbers and instantly destroy
trust in the whole panel. This cost far more than the extra endpoint would have.

**Tables** — fetch type: no table, use cache · entry type: table with `id` + `created_at` ·
derived stats: no table, compute live · counters: own table, seed `0`.

Present a per-module endpoint/table table for confirmation before writing code. If two
modules' endpoints overlap heavily, raise the merge *now*, not after implementation.

## Step 5 — Build, personalize, verify

1. Scaffold per the chosen stack. Personalization goes in `config.json`, exposed via
   `/api/config`, hydrated into title/brand at boot — so a user can drop in a new server
   file without losing their identity.
2. Landing page = the module they actually open daily. No welcome screen; first paint must
   already be useful. Ask if unclear.
3. Bind `0.0.0.0`, print both localhost and LAN URLs, collapse the sidebar to a drawer
   under 880px.
4. **Dropping a module means deleting five things**: nav node, view fn, loader fn, backend
   route, and its tables. Never leave a dead entry that does nothing when clicked.
5. **Generate a 《工作台配置.md》 (or config section in README)** recording: module list with
   pain-point mapping, style params, data structures, deployed URLs, tech stack rationale.
   **This file is the iteration entry point.** When the user later says "add a hydration reminder",
   read this config and continue — don't re-interview. Tell the user this explicitly on delivery.
6. **Maintain a 迭代记录 (CHANGELOG).** Every time you add a module, change a feature, or
   swap a tech choice, append one line to `CHANGELOG.md` (date + what changed + why). The
   incremental (C-version) flow reads it before touching anything, so you don't repeat work or
   regress a pitfall already fixed.

## Reference implementation (`assets/` — one example, adapt freely)

Zero-dependency row of the stack table. `server.py` (ThreadingHTTPServer, `safe()` wrapper,
`cached(key, fn)` + warm-up daemon, SQLite, local scanners) · `index.html` (no framework:
`TREE` nav / `VIEWS{}` HTML / `LOAD{}` async loaders / `renderView()`; `getJSON` + `safeSet`
are the only helpers) · vendored `echarts.min.js` with CDN fallback ·
`config.example.json`.

Its modules came from one user's pains and are **candidates, not requirements**:

- **`每日日常`** (composite landing module — see below) bundling four daily-glance
  sub-modules: `每日资讯` (news + weather), `每日日程` (check-in + schedule + review),
  `记账记录` (ledger), `每日股市` (multi-market quotes + review/strategy).
- `media` (topics, materials) — for content/creation users.
- `aitools` (local MCP/Skills/Agents scan + running AI tasks) — same root, same question.
- `aihot` (Hacker News "AI" feed) — optional inspiration strip.

The **composite module** pattern is the key takeaway: when several pains all answer "what's
my day look like", merge them into ONE landing board with sub-sections instead of four nav
entries. It is how the reference avoids a 6-item nav where 4 items would be ignored.

### Reference module: 每日日常 (composite — one worked example)

A single landing board that aggregates four sub-modules. Each sub-module is independently
derivable; together they answer "今日概览". **Use as a template shape, not a mandate** —
drop any sub-module the user's pains don't justify.

| 子模块 | 解决什么 | 数据来源 | 类型 | 接口 | 表 |
|---|---|---|---|---|---|
| **每日资讯** | 热榜/天气散在多处 | 微博+头条+抖音热榜 / Open-Meteo 天气 | 抓取型 | `GET /api/daily/news` · `GET /api/daily/weather` | 无（缓存） |
| **每日日程** | 打卡/日程/复盘记不住 | 录入 + 本机 | 录入型 | `GET/POST /api/daily/checkin/items` · `POST /api/daily/checkin/logs`(toggle) · `GET /api/daily/checkin/stats` · `GET/POST/DELETE /api/daily/events` · `GET/POST /api/daily/review` | `checkin_items` · `checkin_logs` · `events` · `reviews` |
| **记账记录** | 收支不知去向 | 录入 | 录入型 | `GET/POST/DELETE /api/daily/ledger` · `GET /api/daily/ledger/stats?range=day\|month\|year` | `ledger` |
| **每日股市** | 多市场行情看不到一处 | 新浪财经（GBK）多市场 | 抓取型 + 录入型 | `GET /api/daily/stock`(markets) · `GET/POST /api/daily/stock/reviews` · `GET/POST /api/daily/stock/strategy` · `GET/POST/DELETE /api/daily/watchlist` | `stock_reviews` · `stock_strategy` · `watchlist` |

Sub-module notes (gotchas live in `references/sources.md`):
- **打卡** uses a two-table design: `checkin_items` (what to track) + `checkin_logs`
  (one row per check-in per day). `stats` computes current **streak** (consecutive days
  ending today/yesterday) + total + `checked_today`. Seed defaults (早起作息 / 运动健身)
  come from config, not code. One-click toggle = POST a log row; toggle off = DELETE it.
- **记账** `stats` returns income/expense/balance + a category pie + a running-balance
  trend, all computed live from `ledger` rows — no stats table.
- **股市** reads a `markets` dict (`config.json`): `{"A股":[...], "美股":[...]}`; each group
  is one column. Always `normalize_code()` before batch queries or one bad symbol fails the
  whole Sina batch.

Full endpoint list, external API URLs, and scan paths: `references/sources.md`.
Worked end-to-end derivation example (4 messy quotes → 3 modules → endpoints):
`references/prompt.md` 附录 2.

**No-skill fallback.** `references/prompt.md` is a standalone, copy-pasteable prompt pack
(极简 / 完整 / 增量 tiers + module inspiration catalog + stack comparison + pitfall table)
reproducing this whole methodology in any AI coding assistant. Hand it over when the user
asks for a 提示词版 or works where skills are unavailable.

## Module inspiration catalog (candidates only — never install wholesale)

Daily-glance (todos, calendar, weather, hot lists, FX) · Local assets (installed tools,
disk, service health) · Tasks & processes (running jobs, queue depth, failures) · Records
(journal, review, quick notes) · Material & topics (inspiration, drafts) · Metrics
monitoring (watchlist, thresholds) · Rankings & intel (vertical charts, competitors) ·
Health (sleep, movement, hydration) · Finance (expenses, subscription renewals) · Learning
(review queue, progress).

Selection rules: only what they'll open *this week*; ≤3 modules in phase one; every module
must name the action it removes.

## Generic conventions (apply regardless of derived modules)

**Visual** — ask light/dark and accent first, then: never pure-black shadows (use tinted
rgba); accent via runtime CSS variables; faint noise overlay (feTurbulence, ~0.035,
`mix-blend:overlay`) kills the plastic look; grids need **`align-items:start`** or short
cards stretch; **name lists render as pills, not comma-joined text** (`.tool-tag`
border-radius 20px in a `flex-wrap` row — 20 pills scan instantly, a 20-item comma string
is unreadable; cap and show "+N"); long URLs need `flex-direction:column` + `min-width:0`
+ `overflow:hidden` + `word-break:break-all`; every data card shows its update time.

**Feature-specific pitfalls** (only when the derived modules include them):
- *Counters*: seed `0` not `1` (seeding 1 makes every row look used once — a flat bar row).
  Never run a normalizing `UPDATE` in the request path; it silently erased every real bump.
  Filter `hits > 0` at the API and render an explicit empty state.
- *Local scanning*: configurable root, graceful missing-dir, skip `_`/`.` dirs, and use a
  **block-scalar-aware** frontmatter parser (`|-` / `>-` are everywhere).
- *Reading another app's DB*: open read-only (`mode=ro`), degrade to `{ok:true,total:0}`
  when absent. **Never scan OS processes to guess what's running** — `ps` catches editors
  and Electron shells and forces keyword guessing; the app's own DB is authoritative,
  cheap, and heuristic-free.
- *External fetches*: return a fresh dict copy on cache hit and write `fetched_at` on first
  fetch (or the timestamp reads null); gbk fallback for GBK feeds; normalize every code
  before batch queries or one bad symbol fails the batch.

## Verification (screenshot-driven)

This UI is visual — verify with a headless browser, not HTTP status.

```bash
NO_PROXY=127.0.0.1 no_proxy=127.0.0.1 curl -s http://127.0.0.1:PORT/api/config
CHROME_PATH="$(command -v google-chrome || command -v chromium || echo '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')" \
node -e '
const pptr=require("puppeteer-core");
(async()=>{const b=await pptr.launch({executablePath:process.env.CHROME_PATH,headless:"new",args:["--no-sandbox","--disable-gpu"]});
const p=await b.newPage();const errs=[];p.on("console",m=>m.type()==="error"&&errs.push(m.text()));
p.on("pageerror",e=>errs.push("PAGEERROR: "+e.message));
await p.setViewport({width:1440,height:900});
await p.goto("http://127.0.0.1:PORT",{waitUntil:"networkidle0",timeout:20000});
await new Promise(r=>setTimeout(r,2500));
await p.screenshot({path:"_test_snap/verify_<module>_<YYYYMMDD>.png",fullPage:true});console.log("console errors:",errs);await b.close();})();'
```

Pass criteria: **zero console errors** · charts actually drawn (not the fallback
placeholder) · no card overflow · no huge grid gaps · update times present · **every
confirmed module has a working entry with real content**. Screenshot after ≥2s — charts
render async and an early shot catches a "生成中" intermediate state, which is not a bug.
**Mobile**: re-run at `{width:390,height:844,isMobile:true}`, click `.hamburger`, confirm
the drawer opens and closes on leaf selection.

**归档**：每次验证截图统一存进项目 `_test_snap/` 目录（如 `_test_snap/verify_landing_20260803.png`、`_test_snap/verify_mobile_20260803.png`），不要只丢在根目录的 `_verify.png` 然后删掉。这批截图是交付物的一部分——下次增量改动后重跑，能直接对比"改之前 vs 改之后"的渲染，省去重新描述 bug 的功夫。

## Gotchas (one fix = permanent)

- **Server dies between turns** → relaunch in a background shell; do *not* append `&`.
- **Proxies break local fetches** → strip `HTTP_PROXY/HTTPS_PROXY/...` at server start.
- **OS firewall** silently blocks the first LAN hit → the user must allow the binary.
- **Personal data leaking into the template** → before packaging, grep assets for the
  author's home path, brand, and persona strings. See Self-Evolution #6.

## Self-Evolution loop

1. **Derive, don't default.** Modules come from stated pains; stacks come from presented
   options the user picks. Reference lists are inspiration, never an install manifest.
2. **Conversation, not form.** Ask life scenarios first ("你在忙什么"), not categories.
   Translate messy answers into structured modules yourself — that's the skill's core value.
3. **Uncertain → verify, don't guess.** Screenshot before claiming a UI fix works.
4. **One correction = permanent defense.** Fix the shared CSS/pattern, not the one card;
   record the gotcha here so it cannot recur.
5. **Merge before you add.** If a new page would restate numbers an existing page shows,
   merge them and unify the data source instead.
6. **Progressive disclosure.** Keep SKILL.md lean; endpoints/pitfalls → `references/`,
   boilerplate → `assets/`.
7. **Template ≠ the author's instance.** When improving a live personal dashboard, port
   changes *into* the template and de-personalize the copy — never de-personalize the
   user's own running instance. Strictly one-way: `live → (copy + scrub) → assets/`.
8. **Re-package after meaningful change** so the distributed zip stays current.
9. **CHECKPOINTs are non-negotiable.** Every gate in the flow exists to prevent the #1
   failure mode: a dashboard full of dead nav entries the user never clicks. Never
   self-answer past a checkpoint.
