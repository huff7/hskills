#!/usr/bin/env python3
# 本地 AI 工作台 — 本地仪表盘服务（零依赖，标准库实现）
# 运行：python3 server.py  →  http://127.0.0.1:8788
import json, os, sqlite3, urllib.request, urllib.parse, datetime, time, threading, re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "data", "workbench.db")
CONFIG = os.path.join(BASE, "config.json")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"

# 本服务是本地仪表盘，所有外网抓取（抖音/HN/Open-Meteo/新浪）应直连；
# 清除环境代理变量，避免继承到宿主 Agent 的本地代理（如 127.0.0.1:58113）导致时通时断。
for _k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy", "no_proxy"):
    os.environ.pop(_k, None)


DEFAULT_CONFIG = {
    "brand": "AI 工作台",
    "short_name": "工作台",
    "tagline": "Local AI Workstation",
    "theme_color": "#0D1117",
    "background_color": "#0D1117",
    "city": "北京",
    "stocks": {
        "markets": {"A股": ["sh000001", "sz399001", "sz399006"],
                     "美股": ["gb_dji", "gb_ixic", "gb_inx"]},
        "watchlist_seed": []
    },
    "ai_tools": {}
}

def load_config():
    try:
        with open(CONFIG, encoding="utf-8") as f:
            user = json.load(f)
    except Exception:
        return dict(DEFAULT_CONFIG)
    merged = dict(DEFAULT_CONFIG)
    merged.update(user)
    return merged

def manifest_for(cfg):
    """PWA manifest，全部取自 config（代码零硬编码品牌/颜色/图标）。

    图标策略：若 static/ 下存在 PNG（icon-192.png / icon-512.png /
    icon-maskable-512.png）则优先使用，满足 iOS/Android 安装要求；
    SVG 始终保留作兜底（矢量任意尺寸）。放 PNG 即刻生效，无需改代码。
    """
    brand = cfg.get("brand") or "AI 工作台"
    icons = []
    _static = os.path.join(BASE, "static")
    _png_specs = [
        ("icon-192.png", "192x192", "image/png", "any"),
        ("icon-512.png", "512x512", "image/png", "any"),
        ("icon-maskable-512.png", "512x512", "image/png", "maskable"),
    ]
    for fn, sizes, ctype, purpose in _png_specs:
        if os.path.exists(os.path.join(_static, fn)):
            icons.append({"src": "/" + fn, "sizes": sizes, "type": ctype, "purpose": purpose})
    # SVG 兜底（始终有至少一个图标，矢量任意尺寸）
    icons.append({"src": "/icon.svg", "sizes": "any", "type": "image/svg+xml", "purpose": "any maskable"})
    return {
        "name": brand,
        "short_name": cfg.get("short_name") or brand[:4],
        "description": cfg.get("tagline") or "个人本地 AI 工作台",
        "lang": "zh-CN",
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "background_color": cfg.get("background_color") or "#0D1117",
        "theme_color": cfg.get("theme_color") or "#0D1117",
        "icons": icons,
    }

def get_db():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE IF NOT EXISTS todos (id INTEGER PRIMARY KEY AUTOINCREMENT, text TEXT, done INTEGER DEFAULT 0, created TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS materials (id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT, tags TEXT, created TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS reviews (date TEXT PRIMARY KEY, content TEXT, updated TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS watchlist (id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT, created TEXT)")
    # 待办新增 category / completed_at，支持「分类完成情况」与「每日完成趋势」图表
    try:
        conn.execute("ALTER TABLE todos ADD COLUMN category TEXT DEFAULT '通用'")
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE todos ADD COLUMN completed_at TEXT")
    except Exception:
        pass
    conn.execute("""CREATE TABLE IF NOT EXISTS tool_usage (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, hits INTEGER DEFAULT 0, last_used TEXT)""")
    # ── 每日日常新增表：打卡 / 日程 / 记账 / 股市复盘 ──
    conn.execute("""CREATE TABLE IF NOT EXISTS checkin_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, category TEXT, created TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS checkin_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, item_id INTEGER, date TEXT, created TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, datetime TEXT, note TEXT, created TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS ledger (
        id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, category TEXT, amount REAL, note TEXT, date TEXT, created TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS stock_reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, market TEXT, content TEXT, created TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS stock_strategy (
        id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT, updated TEXT)""")
    # 首次运行：用 config 中的 watchlist_seed 播种自选股
    if conn.execute("SELECT COUNT(*) FROM watchlist").fetchone()[0] == 0:
        for c in load_config().get("stocks", {}).get("watchlist_seed", []):
            conn.execute("INSERT INTO watchlist(code, created) VALUES(?,?)", (c, now()))
    # 已完成的旧数据回填 completed_at（用创建时间近似）
    try:
        conn.execute("UPDATE todos SET completed_at=created WHERE done=1 AND completed_at IS NULL")
    except Exception:
        pass
    # 用本机已安装的工具为 tool_usage 播种基线（点击会累加）
    if conn.execute("SELECT COUNT(*) FROM tool_usage").fetchone()[0] == 0:
        _seed = set()
        try:
            for t in _scan_mcp(): _seed.add(t.get("name"))
            for t in _scan_skills(): _seed.add(t.get("name"))
            for t in _scan_agents(): _seed.add(t.get("name"))
        except Exception:
            pass
        for nm in _seed:
            if nm:
                conn.execute("INSERT OR IGNORE INTO tool_usage(name, hits, last_used) VALUES(?,0,?)", (nm, now()))
    # 打卡项种子（默认：早起作息 + 运动健身）
    if conn.execute("SELECT COUNT(*) FROM checkin_items").fetchone()[0] == 0:
        for nm, cat in (("早起作息", "作息"), ("运动健身", "健身")):
            conn.execute("INSERT INTO checkin_items(name, category, created) VALUES(?,?,?)", (nm, cat, now()))
    # 迁移（仅一次）：旧版播种值全为 1 且无更高值 → 归零
    _total = conn.execute("SELECT COUNT(*) FROM tool_usage").fetchone()[0]
    _ones = conn.execute("SELECT COUNT(*) FROM tool_usage WHERE hits = 1").fetchone()[0]
    if _total > 0 and _ones == _total:
        conn.execute("UPDATE tool_usage SET hits = 0 WHERE hits = 1")
    conn.commit()
    return conn


def fetch_json(url, referer=None, timeout=10):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    if referer:
        req.add_header("Referer", referer)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", errors="ignore"))


def fetch_text(url, referer=None, timeout=10):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    if referer:
        req.add_header("Referer", referer)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
    try:
        return raw.decode("utf-8")
    except Exception:
        return raw.decode("gbk", errors="ignore")


def fnum(s):
    try:
        return float(s)
    except Exception:
        return 0.0


def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


def today():
    return datetime.date.today().strftime("%Y-%m-%d")


def safe(fn):
    try:
        return {"ok": True, **fn()}
    except Exception as e:
        return {"ok": False, "error": str(e), "items": []}


# ---------- 服务端缓存（外部抓取结果，带 TTL） ----------
# 资讯/天气等外网抓取较慢，加内存缓存 + 启动预热，避免每次打开页面都现抓。
_CACHE = {}
_CACHE_LOCK = threading.Lock()
_TTL = {"news": 300, "topics": 300, "aihot": 300, "weather": 900,
        "stock": 60}

def cached(key, fn, ok=lambda r: isinstance(r, dict) and r.get("ok")):
    t = time.time()
    with _CACHE_LOCK:
        hit = _CACHE.get(key)
        if hit and (t - hit[0]) < _TTL.get(key, 300):
            v = dict(hit[1]); v["cached"] = True
            return v
    val = fn()
    if ok(val):
        val = dict(val)
        val["cached"] = False
        val["fetched_at"] = time.strftime("%H:%M")
        with _CACHE_LOCK:
            _CACHE[key] = (t, val)
    return val


# ---------- 外部数据 ----------
def _news_fetch():
    items = []
    seen = set()
    # 1) 微博热搜（约 50 条）
    try:
        wb = fetch_json("https://weibo.com/ajax/side/hotSearch", referer="https://weibo.com/")
        for i in wb.get("data", {}).get("realtime", []):
            t = i.get("word", "")
            if t and t not in seen:
                seen.add(t)
                items.append({"title": t, "hot": i.get("num"),
                              "url": "https://s.weibo.com/weibo?q=" + urllib.parse.quote("#" + t + "#"),
                              "src": "微博"})
    except Exception:
        pass
    # 2) 头条热榜
    try:
        tt = fetch_json("https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc")
        for i in tt.get("data", []):
            t = i.get("Title") or i.get("title", "")
            if t and t not in seen:
                seen.add(t)
                items.append({"title": t, "hot": i.get("HotValue"),
                              "url": i.get("Url") or ("https://www.toutiao.com/" + (i.get("ClusterId_str") or "")),
                              "src": "头条"})
    except Exception:
        pass
    # 3) 抖音热点（约 50 条），合并补足到 120
    try:
        dy = _douyin_hot()
        for w in dy:
            t = w.get("word", "")
            if t and t not in seen:
                seen.add(t)
                items.append({"title": t, "hot": w.get("hot_value"),
                              "url": "https://www.douyin.com/search/" + urllib.parse.quote(t),
                              "src": "抖音"})
    except Exception:
        pass
    return {"ok": True, "source": "微博热搜 + 头条热榜 + 抖音热点", "items": items[:120]}

def api_news():
    return cached("news", _news_fetch)


CITY_COORDS = {
    "上海": [31.2304, 121.4737], "北京": [39.9042, 116.4074], "深圳": [22.5431, 114.0579],
    "广州": [23.1291, 113.2644], "杭州": [30.2741, 120.1551], "成都": [30.5728, 104.0668],
    "武汉": [30.5928, 114.3055], "南京": [32.0603, 118.7969], "重庆": [29.5630, 106.5516],
    "西安": [34.3416, 108.9398], "苏州": [31.2989, 120.5853], "天津": [39.3434, 117.3616],
    "长沙": [28.2282, 112.9388], "青岛": [36.0671, 120.3826], "厦门": [24.4798, 118.0894],
}
WMO = {0: "晴", 1: "大致晴朗", 2: "局部多云", 3: "阴", 45: "雾", 48: "雾凇", 51: "毛毛雨", 53: "小雨",
       55: "中雨", 56: "冻雨", 57: "冻雨", 61: "小雨", 63: "中雨", 65: "大雨", 66: "冻雨",
       67: "强冻雨", 71: "小雪", 73: "中雪", 75: "大雪", 77: "雪粒", 80: "阵雨", 81: "阵雨",
       82: "强阵雨", 85: "阵雪", 86: "强阵雪", 95: "雷阵雨", 96: "雷阵雨伴冰雹", 99: "强雷暴冰雹"}


def _weather_fetch():
    city = load_config().get("city", "北京")
    try:
        return _weather_openmeteo(city)
    except Exception:
        try:
            return _weather_wttr(city)
        except Exception as e:
            return {"ok": False, "error": str(e), "city": city, "forecast": []}

def api_weather():
    return cached("weather", _weather_fetch)


def _weather_openmeteo(city):
    coords = CITY_COORDS.get(city)
    if not coords:
        g = fetch_json("https://geocoding-api.open-meteo.com/v1/search?name=%s&count=1&language=zh" % urllib.parse.quote(city))
        res = g.get("results", [{}])
        if not res:
            raise ValueError("城市未找到: " + city)
        coords = [res[0]["latitude"], res[0]["longitude"]]
    lat, lon = coords
    u = ("https://api.open-meteo.com/v1/forecast?latitude=%.4f&longitude=%.4f"
         "&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code"
         "&daily=weather_code,temperature_2m_max,temperature_2m_min"
         "&hourly=temperature_2m&timezone=Asia%%2FShanghai&forecast_days=3" % (lat, lon))
    d = fetch_json(u)
    cur = d.get("current", {})
    daily = d.get("daily", {})
    times = daily.get("time", [])
    fc = []
    for i in range(min(3, len(times))):
        fc.append({"date": times[i][5:], "min": daily["temperature_2m_min"][i],
                   "max": daily["temperature_2m_max"][i],
                   "desc": WMO.get(daily["weather_code"][i], "")})
    hourly = []
    h = d.get("hourly", {})
    htimes, htemps = h.get("time", []), h.get("temperature_2m", [])
    if htimes and htemps:
        ch = datetime.datetime.now().hour
        start = 0
        for i, ht in enumerate(htimes):
            if ht[11:13] == "%02d" % ch:
                start = i; break
        for i in range(start, min(start + 24, len(htimes))):
            hourly.append({"t": htimes[i][11:16], "v": htemps[i]})
    return {"ok": True, "city": city, "desc": WMO.get(cur.get("weather_code"), ""),
            "temp": cur.get("temperature_2m"), "feels": cur.get("apparent_temperature"),
            "humidity": cur.get("relative_humidity_2m"), "forecast": fc, "hourly": hourly}


def _weather_wttr(city):
    data = fetch_json("https://wttr.in/%s?format=j1" % urllib.parse.quote(city))
    cur = data.get("current_condition", [{}])[0]
    fc = [{"date": d.get("date", ""), "min": d.get("mintempC", ""), "max": d.get("maxtempC", ""),
           "desc": d.get("hourly", [{}])[0].get("weatherDesc", [{}])[0].get("value", "")} for d in data.get("weather", [])[:3]]
    return {"ok": True, "city": city, "desc": cur.get("weatherDesc", [{}])[0].get("value", ""),
            "temp": cur.get("temp_C", ""), "feels": cur.get("FeelsLikeC", ""),
            "humidity": cur.get("humidity", ""), "forecast": fc}


def parse_sina(text):
    items = []
    for line in text.split(";"):
        line = line.strip()
        if not line.startswith("var hq_str"):
            continue
        try:
            key = line[len("var hq_str_"):line.index("=")]
            payload = line.split('"')[1]
        except Exception:
            continue
        p = payload.split(",")
        if len(p) < 4:
            continue
        code = key
        name = p[0]
        if code.startswith("gb_"):  # 美股：name, 现价, 涨跌幅%
            price = fnum(p[1])
            pct = fnum(p[2])
            chg = round(price * pct / 100, 2)
        else:  # A股/指数：name, 现价, 昨收
            price = fnum(p[1])
            prev = fnum(p[2])
            chg = round(price - prev, 2) if prev else 0.0
            pct = round(chg / prev * 100, 2) if prev else 0.0
        items.append({"name": name, "code": code, "price": price, "change": chg, "pct": pct})
    return items


def normalize_code(code):
    """把用户输入的任意写法规范成 Sina 能识别的代码。无法识别返回 None。"""
    code = (code or "").strip().lower()
    if not code:
        return None
    if code[:2] in ("sh", "sz", "hk") and code[2:].isdigit():
        return code
    if code.startswith("gb_") and len(code) > 3:
        return code
    if code.isdigit() and len(code) == 6:           # A股纯数字 → 按首位判断市场
        return ("sh" + code) if code[0] in "569" else ("sz" + code)
    if code.isalpha():                               # 纯字母 → 美股
        return "gb_" + code
    return None


def _stock_fetch():
    try:
        cfg = load_config().get("stocks", {})
        markets = cfg.get("markets", {"A股": ["sh000001", "sz399001", "sz399006"],
                                     "美股": ["gb_dji", "gb_ixic", "gb_inx"]})
        c = get_db()
        watch_rows = c.execute("SELECT id,code FROM watchlist ORDER BY id").fetchall()
        c.close()
        # 规范化 + 过滤掉非法代码：一个坏代码会让 Sina 整批返回 sys_auth=FAILED
        watch = [normalize_code(r["code"]) for r in watch_rows]
        watch = [w for w in watch if w]
        all_codes = []
        for codes in markets.values():
            all_codes += list(codes)
        all_codes += watch
        text = fetch_text("https://hq.sinajs.cn/list=" + ",".join(all_codes),
                          referer="https://finance.sina.com.cn", timeout=10)
        by_code = {it["code"]: it for it in parse_sina(text)}
        watch_items = []
        for r in watch_rows:
            code = (r["code"] or "").strip()
            it = by_code.get(code)
            if it:
                it = dict(it); it["wid"] = r["id"]
                watch_items.append(it)
        # 多市场分组（顺序与 config 一致，用户可自行增减市场）
        groups = [{"name": mname, "items": [by_code[x] for x in codes if x in by_code]}
                  for mname, codes in markets.items()]
        groups.append({"name": "自选股", "items": watch_items})
        return {"ok": True, "groups": groups}
    except Exception as e:
        return {"ok": False, "error": str(e), "groups": []}


def api_stock():
    return cached("stock", _stock_fetch)


# ---------- 本地 CRUD ----------
def api_plan_list():
    c = get_db(); rows = c.execute("SELECT id,text,done,category,created FROM todos ORDER BY id DESC").fetchall(); c.close()
    return {"items": [dict(r) for r in rows]}


def api_plan_add(text, category='通用'):
    c = get_db(); c.execute("INSERT INTO todos(text,done,category,created) VALUES(?,0,?,?)", (text, category, now())); c.commit(); c.close()
    return {"ok": True}


def api_plan_toggle(id):
    c = get_db()
    row = c.execute("SELECT done FROM todos WHERE id=?", (id,)).fetchone()
    if row:
        nd = 1 - row["done"]
        if nd == 1:
            c.execute("UPDATE todos SET done=1, completed_at=? WHERE id=?", (now(), id))
        else:
            c.execute("UPDATE todos SET done=0, completed_at=NULL WHERE id=?", (id,))
    c.commit(); c.close()
    return {"ok": True}


def api_plan_stats():
    c = get_db()
    td = datetime.date.today()
    days = [(td - datetime.timedelta(days=i)).strftime("%Y-%m-%d") for i in range(13, -1, -1)]
    trend = [{"date": d[5:], "count": c.execute("SELECT COUNT(*) FROM todos WHERE completed_at LIKE ?", (d + "%",)).fetchone()[0]} for d in days]
    rows = c.execute("SELECT COALESCE(category,'通用') AS cat, COUNT(*) AS n FROM todos WHERE done=1 GROUP BY cat").fetchall()
    by_category = [{"category": r["cat"], "count": r["n"]} for r in rows]
    running = [dict(r) for r in c.execute("SELECT id,text,category,created FROM todos WHERE done=0 ORDER BY id DESC").fetchall()]
    done_today = c.execute("SELECT COUNT(*) FROM todos WHERE completed_at LIKE ?", (td.strftime("%Y-%m-%d") + "%",)).fetchone()[0]
    total = c.execute("SELECT COUNT(*) FROM todos").fetchone()[0]
    c.close()
    return {"ok": True, "trend": trend, "by_category": by_category, "running": running,
            "done_today": done_today, "total": total}


def api_plan_del(id):
    c = get_db(); c.execute("DELETE FROM todos WHERE id=?", (id,)); c.commit(); c.close()
    return {"ok": True}


def api_review_get():
    c = get_db(); r = c.execute("SELECT content,updated FROM reviews WHERE date=?", (today(),)).fetchone(); c.close()
    return {"ok": True, "date": today(), "content": r["content"] if r else ""}


def api_review_save(content):
    c = get_db(); c.execute(
        "INSERT INTO reviews(date,content,updated) VALUES(?,?,?) "
        "ON CONFLICT(date) DO UPDATE SET content=excluded.content, updated=excluded.updated",
        (today(), content, now())); c.commit(); c.close()
    return {"ok": True}


def api_watch_list():
    c = get_db(); rows = c.execute("SELECT id,code FROM watchlist ORDER BY id").fetchall(); c.close()
    return {"items": [{"id": r["id"], "code": r["code"]} for r in rows]}


def api_watch_add(code):
    code = normalize_code(code)
    if not code:
        return {"ok": False, "error": "代码无法识别（A股需 6 位数字或 sh/sz 前缀，美股用字母如 tsm）"}
    c = get_db(); c.execute("INSERT INTO watchlist(code,created) VALUES(?,?)", (code, now())); c.commit(); c.close()
    return {"ok": True, "code": code}


def api_watch_del(id):
    c = get_db(); c.execute("DELETE FROM watchlist WHERE id=?", (id,)); c.commit(); c.close()
    return {"ok": True}


def api_materials_list():
    c = get_db(); rows = c.execute("SELECT id,content,tags,created FROM materials ORDER BY id DESC").fetchall(); c.close()
    return {"items": [dict(r) for r in rows]}


def api_materials_add(content, tags):
    c = get_db(); c.execute("INSERT INTO materials(content,tags,created) VALUES(?,?,?)", (content, tags, now())); c.commit(); c.close()
    return {"ok": True}


def api_materials_del(id):
    c = get_db(); c.execute("DELETE FROM materials WHERE id=?", (id,)); c.commit(); c.close()
    return {"ok": True}


# ---------- 自媒体 / AI工具 ----------
def _topics_fetch():
    items, seen = [], set()
    try:
        dy = fetch_json("https://www.iesdouyin.com/web/api/v2/hotsearch/billboard/word/")
        for w in dy.get("word_list", []):
            t = w.get("word", "")
            if t and t not in seen:
                seen.add(t)
                items.append({"title": t, "hot": w.get("hot_value"),
                              "url": "https://s.weibo.com/weibo?q=" + urllib.parse.quote("#" + t + "#"), "src": "抖音"})
    except Exception:
        pass
    try:
        wb = fetch_json("https://weibo.com/ajax/side/hotSearch", referer="https://weibo.com/")
        for i in wb.get("data", {}).get("realtime", []):
            t = i.get("word", "")
            if t and t not in seen:
                seen.add(t)
                items.append({"title": t, "hot": i.get("num"),
                              "url": "https://s.weibo.com/weibo?q=" + urllib.parse.quote("#" + t + "#"), "src": "微博"})
    except Exception:
        pass
    return {"ok": True, "source": "抖音 + 微博 热榜", "items": items[:100]}

def api_topics():
    return cached("topics", _topics_fetch)


# ===== AI工具：扫描本机真实安装（MCP / Skills / Agents），不再读 config.json 占位 =====
_HOME = os.path.expanduser("~")
SKILLS_DIRS = [
    os.path.join(_HOME, ".workbuddy", "skills"),
    os.path.join(BASE, "..", ".workbuddy", "skills"),   # 项目级 skills
]
MCP_PATH = os.path.join(_HOME, ".workbuddy", "mcp.json")
AGENTS_DIR = os.path.join(_HOME, ".workbuddy", "agents")


def _parse_frontmatter(path):
    """极简 YAML frontmatter 解析：支持行内值与块标量（| / |- / > / >-）。"""
    try:
        with open(path, encoding="utf-8") as f:
            txt = f.read()
    except Exception:
        return None
    if not txt.startswith("---"):
        return None
    end = txt.find("\n---", 3)
    if end < 0:
        return None
    block = txt[3:end]
    data = {}
    lines = block.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if not s or s.startswith("#"):
            i += 1; continue
        m = re.match(r'^([A-Za-z_][\w-]*):\s*(.*)$', line)
        if not m:
            i += 1; continue
        key, val = m.group(1), m.group(2).strip()
        if val in ("|", "|-", ">", ">-"):          # 块标量：收集后续缩进行
            parts = []
            i += 1
            while i < len(lines) and (lines[i].startswith(" ") or lines[i].startswith("\t")):
                parts.append(lines[i].strip())
                i += 1
            data[key] = " ".join(parts)
            continue
        data[key] = val.strip('"').strip("'")
        i += 1
    name = data.get("name")
    desc = data.get("description")
    if desc and len(desc) > 64:
        desc = desc[:64] + "…"
    return (name, desc)


def _scan_mcp():
    out = []
    try:
        with open(MCP_PATH, encoding="utf-8") as f:
            cfg = json.load(f)
        for sname, scfg in cfg.get("mcpServers", {}).items():
            if not isinstance(scfg, dict):
                continue
            if "url" in scfg:
                desc = scfg["url"]
            elif scfg.get("command"):
                desc = (scfg["command"] + " " + " ".join(scfg.get("args", []))).strip()
            else:
                desc = "本地 MCP 服务"
            out.append({"name": sname, "desc": desc[:90]})
    except Exception:
        pass
    return out


def _scan_skills():
    out, seen = [], set()
    for d in SKILLS_DIRS:
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            if name in seen or name.startswith("_") or name.startswith("."):
                continue
            sp = os.path.join(d, name, "SKILL.md")
            if not os.path.isfile(sp):
                continue
            fm = _parse_frontmatter(sp)
            sname = (fm and fm[0]) or name
            desc = (fm and fm[1]) or ""
            if len(desc) > 64:
                desc = desc[:64] + "…"
            out.append({"name": sname, "desc": desc, "key": name})
            seen.add(name)
    return out


def _scan_agents():
    out = []
    if os.path.isdir(AGENTS_DIR):
        for n in sorted(os.listdir(AGENTS_DIR)):
            sp = os.path.join(AGENTS_DIR, n, "SKILL.md")
            if not os.path.isfile(sp):
                continue
            fm = _parse_frontmatter(sp)
            out.append({"name": (fm and fm[0]) or n, "desc": (fm and fm[1]) or ""})
    return out


def api_aitools():
    return {"mcp": _scan_mcp(), "skills": _scan_skills(), "agents": _scan_agents()}


def api_tool_usage_get():
    c = get_db()
    # 只返回有真实使用记录的工具（hits > 0），避免全是种子值
    rows = c.execute("SELECT name, hits FROM tool_usage WHERE hits > 0 ORDER BY hits DESC LIMIT 20").fetchall()
    c.close()
    return {"ok": True, "items": [{"name": r["name"], "hits": r["hits"]} for r in rows]}


def api_tool_usage_bump(name):
    if not name:
        return {"ok": False}
    c = get_db()
    c.execute("INSERT INTO tool_usage(name, hits, last_used) VALUES(?,1,?) "
              "ON CONFLICT(name) DO UPDATE SET hits=hits+1, last_used=excluded.last_used", (name, now()))
    c.commit(); c.close()
    return {"ok": True}


# ── 统一数据源：WorkBuddy AI 任务（按空间分组）──
#   图表（趋势+饼图）和「任务在跑」列表共用此 API
def _workspace_name(cwd):
    """从 cwd 路径提取空间显示名；不在 workspaces 表中的返回 '通用'"""
    if not cwd:
        return "通用"
    # 已知工作区 → 取最后一段
    name = cwd.rstrip("/").split("/")[-1]
    wb_db = os.path.expanduser("~/.workbuddy/workbuddy.db")
    if os.path.exists(wb_db):
        try:
            wc = sqlite3.connect(wb_db)
            found = wc.execute("SELECT 1 FROM workspaces WHERE path=?", (cwd,)).fetchone()
            wc.close()
            if found:
                return name
        except Exception:
            pass
    return "通用"


def api_ai_tasks():
    """统一 API：返回 WorkBuddy AI 任务，按空间(workspace)分组"""
    result = {"ok": True, "tasks": [], "by_workspace": {}, "trend": [], "workspaces": []}
    wb_db = os.path.expanduser("~/.workbuddy/workbuddy.db")
    if not os.path.exists(wb_db):
        return {**result, "total": 0, "error": "WorkBuddy DB 未找到"}

    now_ts = int(time.time())
    try:
        wc = sqlite3.connect(wb_db)
        wc.row_factory = sqlite3.Row

        # ── 1) 全部近期 sessions（14 天内活跃的）──
        rows = wc.execute("""
            SELECT id, title, status, mode, model, expert_id,
                   is_background_automation, cwd, created_at, updated_at,
                   last_activity_at
            FROM sessions
            WHERE deleted_at IS NULL
              AND updated_at > ?
            ORDER BY updated_at DESC
            LIMIT 60
        """, (now_ts - 86400 * 14,)).fetchall()

        # 按日期统计趋势（近 14 天）
        day_counts = {}
        for i in range(14):
            d = (datetime.date.today() - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            day_counts[d] = 0

        ws_counts = {}   # by_workspace 计数
        tasks = []
        seen_cwds = set()

        for s in rows:
            cwd = s["cwd"] or ""
            ws = _workspace_name(cwd)
            seen_cwds.add((ws, cwd))

            # 趋势计数（按 created_at 日期）
            cdate = datetime.date.fromtimestamp(
                (s["created_at"] or 0) / 1000 if (s["created_at"] or 0) > 1e12 else (s["created_at"] or 0)
            ).strftime("%Y-%m-%d") if s["created_at"] else None
            if cdate and cdate in day_counts:
                day_counts[cdate] += 1

            # 空间计数
            ws_counts[ws] = ws_counts.get(ws, 0) + 1

            # 状态判定
            st = s["status"]
            upd = s["updated_at"] or 0
            age_sec = now_ts - (upd / 1000 if upd > 1e12 else upd)

            if st == "working":
                task_status = "running"
                status_label = "执行中"
            elif age_sec < 7200:
                task_status = "recent"
                status_label = "最近活跃"
            elif st not in ("archived",):
                task_status = "done"
                status_label = "已完成"
            else:
                continue  # archived 太老的不展示

            name = (s["title"] or "未命名任务")[:60]
            detail_parts = [f"模式:{s['mode'] or 'craft'}", f"模型:{s['model'] or '默认'}"]
            if s["expert_id"]:
                detail_parts.append(f"专家:{s['expert_id'][:16]}")
            if task_status == "running":
                detail_parts.append("● 正在执行")
            else:
                detail_parts.append(f"{'最近活跃' if task_status=='recent' else '完成于'}: {_ago(age_sec)}")

            tasks.append({
                "id": f"sess-{s['id']}", "name": name,
                "type": "session", "status": task_status,
                "workspace": ws, "workspace_path": cwd,
                "detail": " · ".join(detail_parts),
                "mode": s["mode"], "model": s["model"],
                "updated_ts": upd,
            })

        # 构建趋势数组（正序：旧→新）
        trend = []
        for d in sorted(day_counts.keys()):
            trend.append({"date": d[5:], "count": day_counts[d]})

        # 构建 by_workspace + workspaces 列表
        by_workspace = [{"category": k, "count": v} for k, v in sorted(ws_counts.items(), key=lambda x: -x[1])]
        workspaces_list = []
        for (ws_name, ws_path) in sorted(seen_cwds, key=lambda x: -ws_counts.get(x[0], 0)):
            workspaces_list.append({"name": ws_name, "path": ws_path, "count": ws_counts.get(ws_name, 0)})

        wc.close()

        result.update({
            "total": len(tasks),
            "tasks": tasks,
            "by_workspace": by_workspace,
            "trend": trend,
            "workspaces": workspaces_list,
        })
        return result

    except Exception as exc:
        return {**result, "error": str(exc), "total": 0}


def api_ai_running():
    """兼容入口：委托给 api_ai_tasks"""
    return api_ai_tasks()



def _ago(seconds):
    """秒数 → 可读的 'X小时前' / 'X天前'"""
    if seconds < 0:
        return "刚刚"
    if seconds < 60:
        return f"{int(seconds)}秒前"
    if seconds < 3600:
        return f"{int(seconds // 60)}分钟前"
    if seconds < 86400:
        return f"{int(seconds // 3600)}小时前"
    days = int(seconds // 86400)
    return f"{days}天前" if days < 30 else f"{days // 30}个月前"




def api_daily_summary():
    plan = api_plan_stats()
    tools = api_aitools()
    aihot = api_aihot()
    aitems = (aihot.get("items") if isinstance(aihot, dict) else []) or []
    mcp, sk, ag = tools.get("mcp", []), tools.get("skills", []), tools.get("agents", [])
    L = []
    L.append(f"今天本地共有 {len(mcp)+len(sk)+len(ag)} 个 AI 工具在线（MCP {len(mcp)} · Skills {len(sk)} · Agents {len(ag)}）。")
    L.append(f"待办共 {plan['total']} 条，今日已完成 {plan['done_today']} 条，还有 {len(plan['running'])} 条在跑。")
    if plan["running"]:
        L.append("在跑的任务：" + "、".join(t["text"] for t in plan["running"][:5]) + ("…" if len(plan["running"]) > 5 else ""))
    if aitems:
        L.append("AI 圈今日焦点：" + "；".join(i["title"] for i in aitems[:3]) + "。")
    if plan["by_category"]:
        L.append("已完成任务按类目：" + "、".join(f"{c['category']} {c['count']}" for c in plan["by_category"]) + "。")
    return {"ok": True, "date": today(), "summary": "\n".join(L)}


# ---------- 每日日常：打卡 / 日程 / 记账 / 股市复盘 ----------
def api_checkin_items():
    c = get_db()
    rows = c.execute("SELECT id,name,category,created FROM checkin_items ORDER BY id").fetchall()
    c.close()
    return {"ok": True, "items": [dict(r) for r in rows]}


def api_checkin_add(name, category='打卡'):
    name = (name or "").strip()
    if not name:
        return {"ok": False, "error": "名称不能为空"}
    c = get_db()
    c.execute("INSERT INTO checkin_items(name,category,created) VALUES(?,?,?)", (name, category, now()))
    c.commit(); c.close()
    return {"ok": True}


def api_checkin_del(id):
    c = get_db()
    c.execute("DELETE FROM checkin_items WHERE id=?", (id,))
    c.execute("DELETE FROM checkin_logs WHERE item_id=?", (id,))
    c.commit(); c.close()
    return {"ok": True}


def api_checkin_logs(item_id=None):
    c = get_db()
    if item_id:
        rows = c.execute("SELECT id,item_id,date,created FROM checkin_logs WHERE item_id=? ORDER BY date", (item_id,)).fetchall()
    else:
        rows = c.execute("SELECT id,item_id,date,created FROM checkin_logs ORDER BY date").fetchall()
    c.close()
    return {"ok": True, "logs": [dict(r) for r in rows]}


def api_checkin_toggle(item_id, date=None):
    """一键打卡：今天已打卡则取消（toggle）。返回最新状态。"""
    date = date or today()
    c = get_db()
    row = c.execute("SELECT id FROM checkin_logs WHERE item_id=? AND date=?", (item_id, date)).fetchone()
    if row:
        c.execute("DELETE FROM checkin_logs WHERE id=?", (row["id"],))
        state = False
    else:
        c.execute("INSERT INTO checkin_logs(item_id,date,created) VALUES(?,?,?)", (item_id, date, now()))
        state = True
    c.commit(); c.close()
    return {"ok": True, "checked": state, "date": date}


def api_checkin_stats():
    """返回每个打卡项的连续天数（streak）、累计次数、今日是否已打卡。"""
    c = get_db()
    items = c.execute("SELECT id,name,category FROM checkin_items ORDER BY id").fetchall()
    td = today()
    out = []
    for it in items:
        rows = c.execute("SELECT date FROM checkin_logs WHERE item_id=? ORDER BY date", (it["id"],)).fetchall()
        dates = sorted(set(r[0] for r in rows))
        total = len(dates)
        streak = 0
        if dates:
            dset = set(dates)
            from datetime import date as _date
            cur = _date.today()
            if dates[-1] != td:                       # 今天没打卡，则从昨天起算连续
                cur = cur - datetime.timedelta(days=1)
            while cur.strftime("%Y-%m-%d") in dset:
                streak += 1
                cur = cur - datetime.timedelta(days=1)
        out.append({"id": it["id"], "name": it["name"], "category": it["category"],
                    "total": total, "streak": streak,
                    "checked_today": (dates[-1] == td) if dates else False,
                    "last": dates[-1] if dates else None})
    c.close()
    return {"ok": True, "items": out}


def api_events_list():
    c = get_db()
    rows = c.execute("SELECT id,title,datetime,note,created FROM events ORDER BY datetime").fetchall()
    c.close()
    return {"ok": True, "events": [dict(r) for r in rows]}


def api_events_add(title, datetime_, note=''):
    title = (title or "").strip()
    if not title:
        return {"ok": False, "error": "标题不能为空"}
    c = get_db()
    c.execute("INSERT INTO events(title,datetime,note,created) VALUES(?,?,?,?)", (title, datetime_, note, now()))
    c.commit(); c.close()
    return {"ok": True}


def api_events_del(id):
    c = get_db(); c.execute("DELETE FROM events WHERE id=?", (id,)); c.commit(); c.close()
    return {"ok": True}


def api_ledger_list():
    c = get_db()
    rows = c.execute("SELECT id,type,category,amount,note,date,created FROM ledger ORDER BY date DESC, id DESC").fetchall()
    c.close()
    return {"ok": True, "items": [dict(r) for r in rows]}


def api_ledger_add(type_, category, amount, note='', date=None):
    if type_ not in ("income", "expense"):
        return {"ok": False, "error": "type 必须是 income / expense"}
    try:
        amount = float(amount)
    except Exception:
        return {"ok": False, "error": "金额非法"}
    date = date or today()
    c = get_db()
    c.execute("INSERT INTO ledger(type,category,amount,note,date,created) VALUES(?,?,?,?,?,?)",
              (type_, category, amount, note, date, now()))
    c.commit(); c.close()
    return {"ok": True}


def api_ledger_del(id):
    c = get_db(); c.execute("DELETE FROM ledger WHERE id=?", (id,)); c.commit(); c.close()
    return {"ok": True}


def api_ledger_stats(range_='month', period=None):
    """range: day | month | year；返回收支汇总 + 类目饼 + 余额趋势。"""
    from collections import defaultdict
    c = get_db()
    td = datetime.date.today()
    out = {"ok": True, "range": range_, "cat_data": [], "trend": []}
    if range_ == 'day':
        base = period or td.strftime("%Y-%m-%d")
        rows = c.execute("SELECT type,category,amount FROM ledger WHERE date=?", (base,)).fetchall()
        inc = sum(r["amount"] for r in rows if r["type"] == 'income')
        exp = sum(r["amount"] for r in rows if r["type"] == 'expense')
        cats = {}
        for r in rows:
            k = (r["type"], r["category"] or "未分类")
            cats[k] = cats.get(k, 0) + r["amount"]
        out.update({"period": base, "income": round(inc, 2), "expense": round(exp, 2),
                    "balance": round(inc - exp, 2),
                    "cat_data": [{"name": k[1], "type": k[0], "value": round(v, 2)} for k, v in cats.items()]})
    elif range_ == 'year':
        base = period or td.strftime("%Y")
        rows = c.execute("SELECT type,category,amount,date FROM ledger WHERE date LIKE ?", (base + "%",)).fetchall()
        inc = sum(r["amount"] for r in rows if r["type"] == 'income')
        exp = sum(r["amount"] for r in rows if r["type"] == 'expense')
        by_m = defaultdict(lambda: [0.0, 0.0])   # [exp, inc]
        cats = {}
        for r in rows:
            m = r["date"][:7]                      # YYYY-MM
            if r["type"] == 'income': by_m[m][1] += r["amount"]
            else: by_m[m][0] += r["amount"]
            k = (r["type"], r["category"] or "未分类")
            cats[k] = cats.get(k, 0) + r["amount"]
        run = 0.0
        for m in sorted(by_m.keys()):
            run += by_m[m][1] - by_m[m][0]
            out["trend"].append({"date": m[2:], "balance": round(run, 2)})   # MM
        out.update({"period": base, "income": round(inc, 2), "expense": round(exp, 2),
                    "balance": round(inc - exp, 2),
                    "cat_data": [{"name": k[1], "type": k[0], "value": round(v, 2)} for k, v in cats.items()]})
    else:  # month（默认）
        base = period or td.strftime("%Y-%m")
        rows = c.execute("SELECT type,category,amount,date FROM ledger WHERE date LIKE ?", (base + "%",)).fetchall()
        inc = sum(r["amount"] for r in rows if r["type"] == 'income')
        exp = sum(r["amount"] for r in rows if r["type"] == 'expense')
        by_d = defaultdict(lambda: [0.0, 0.0])   # [exp, inc]
        cats = {}
        for r in rows:
            d = r["date"][5:]                      # MM-DD
            if r["type"] == 'income': by_d[d][1] += r["amount"]
            else: by_d[d][0] += r["amount"]
            k = (r["type"], r["category"] or "未分类")
            cats[k] = cats.get(k, 0) + r["amount"]
        run = 0.0
        for d in sorted(by_d.keys()):
            run += by_d[d][1] - by_d[d][0]
            out["trend"].append({"date": d, "balance": round(run, 2)})
        out.update({"period": base, "income": round(inc, 2), "expense": round(exp, 2),
                    "balance": round(inc - exp, 2),
                    "cat_data": [{"name": k[1], "type": k[0], "value": round(v, 2)} for k, v in cats.items()]})
    c.close()
    return out


def api_stock_reviews_get(market=None, date=None):
    c = get_db()
    if date:
        rows = c.execute("SELECT id,date,market,content,created FROM stock_reviews WHERE date=? ORDER BY id DESC", (date,)).fetchall()
    elif market:
        rows = c.execute("SELECT id,date,market,content,created FROM stock_reviews WHERE market=? ORDER BY date DESC", (market,)).fetchall()
    else:
        rows = c.execute("SELECT id,date,market,content,created FROM stock_reviews ORDER BY date DESC").fetchall()
    c.close()
    return {"ok": True, "items": [dict(r) for r in rows]}


def api_stock_reviews_save(date, market, content):
    date = date or today()
    c = get_db()
    c.execute("INSERT INTO stock_reviews(date,market,content,created) VALUES(?,?,?,?)", (date, market, content, now()))
    c.commit(); c.close()
    return {"ok": True}


def api_stock_strategy_get():
    c = get_db()
    r = c.execute("SELECT content,updated FROM stock_strategy ORDER BY id DESC LIMIT 1").fetchone()
    c.close()
    return {"ok": True, "content": r["content"] if r else "", "updated": r["updated"] if r else ""}


def api_stock_strategy_save(content):
    c = get_db()
    c.execute("INSERT INTO stock_strategy(content,updated) VALUES(?,?)", (content, now()))
    c.execute("DELETE FROM stock_strategy WHERE id NOT IN (SELECT id FROM stock_strategy ORDER BY id DESC LIMIT 5)")
    c.commit(); c.close()
    return {"ok": True}


AI_KW = ["AI", "人工智能", "大模型", "ChatGPT", "GPT", "OpenAI", "算力", "芯片", "机器人",
         "机器学习", "深度学习", "神经网络", "LLM", "Sora", "Midjourney", "Stable Diffusion",
         "Agent", "智能体", "自动驾驶", "Claude", "Gemini", "DeepSeek", "豆包", "文心",
         "通义", "AIGC", "AI绘画", "大模型"]


def _aihot_fetch():
    items, seen = [], set()
    try:
        hn = fetch_json("https://hn.algolia.com/api/v1/search?query=AI&tags=story&hitsPerPage=100")
        for h in hn.get("hits", []):
            title = h.get("title") or h.get("story_title")
            if not title or title in seen:
                continue
            seen.add(title)
            url = h.get("url") or ("https://news.ycombinator.com/item?id=" + str(h.get("objectID", "")))
            items.append({"title": title, "url": url, "hot": h.get("points", 0), "src": "HN"})
    except Exception:
        pass
    try:
        douyin = fetch_json("https://www.iesdouyin.com/web/api/v2/hotsearch/billboard/word/")
        for w in douyin.get("word_list", []):
            word = w.get("word", "")
            if word and word not in seen and any(k.lower() in word.lower() for k in AI_KW):
                seen.add(word)
                items.append({"title": word,
                               "url": "https://s.weibo.com/weibo?q=" + urllib.parse.quote("#" + word + "#"),
                               "hot": w.get("hot_value"), "src": "抖音"})
    except Exception:
        pass
    return {"ok": True, "items": items[:100]}

def api_aihot():
    return cached("aihot", _aihot_fetch)


def _douyin_hot():
    d = fetch_json("https://www.iesdouyin.com/web/api/v2/hotsearch/billboard/word/")
    return d.get("word_list", [])


# ---------- HTTP ----------
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def json(self, obj, code=200):
        self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"))

    def static(self, rel, ctype):
        path = os.path.join(BASE, rel)
        if not os.path.isfile(path):
            self._send(404, b"not found", "text/plain; charset=utf-8"); return
        with open(path, "rb") as f:
            self._send(200, f.read(), ctype)

    def _ctype(self, fn):
        if fn.endswith(".js"): return "application/javascript; charset=utf-8"
        if fn.endswith(".css"): return "text/css; charset=utf-8"
        if fn.endswith(".json"): return "application/json; charset=utf-8"
        if fn.endswith(".png"): return "image/png"
        if fn.endswith(".svg"): return "image/svg+xml"
        if fn.endswith(".ico"): return "image/x-icon"
        if fn.endswith(".map"): return "application/json; charset=utf-8"
        return "application/octet-stream"

    def do_GET(self):
        _up = urllib.parse.urlparse(self.path)
        p = _up.path
        qs = urllib.parse.parse_qs(_up.query)
        if p in ("/", "/index.html"):
            self.static("static/index.html", "text/html; charset=utf-8")
        elif p == "/manifest.json":
            self._send(200, json.dumps(manifest_for(load_config()), ensure_ascii=False).encode("utf-8"),
                       "application/manifest+json; charset=utf-8")
        elif p == "/sw.js":
            self.static("static/sw.js", "application/javascript; charset=utf-8")
        elif p == "/icon.svg":
            self.static("static/icon.svg", "image/svg+xml")
        elif p == "/favicon.ico":
            self._send(204, b"")
        elif p == "/api/daily/news": self.json(safe(api_news))
        elif p == "/api/daily/weather": self.json(safe(api_weather))
        elif p == "/api/daily/stock": self.json(safe(api_stock))
        elif p == "/api/daily/plan": self.json(safe(api_plan_list))
        elif p == "/api/daily/plan/stats": self.json(safe(api_plan_stats))
        elif p == "/api/daily/summary": self.json(safe(api_daily_summary))
        elif p == "/api/daily/review": self.json(api_review_get())
        elif p == "/api/daily/checkin/items": self.json(safe(api_checkin_items))
        elif p == "/api/daily/checkin/stats": self.json(safe(api_checkin_stats))
        elif p == "/api/daily/checkin/logs": self.json(safe(lambda: api_checkin_logs(int(qs["item_id"][0]) if qs.get("item_id") else None)))
        elif p == "/api/daily/events": self.json(safe(api_events_list))
        elif p == "/api/daily/ledger": self.json(safe(api_ledger_list))
        elif p == "/api/daily/ledger/stats": self.json(safe(lambda: api_ledger_stats(qs.get("range", ["month"])[0], qs.get("period", [None])[0])))
        elif p.startswith("/api/daily/stock/reviews"):
            if qs.get("market"): self.json(safe(lambda: api_stock_reviews_get(market=qs["market"][0])))
            elif qs.get("date"): self.json(safe(lambda: api_stock_reviews_get(date=qs["date"][0])))
            else: self.json(safe(api_stock_reviews_get))
        elif p == "/api/daily/stock/strategy": self.json(safe(api_stock_strategy_get))
        elif p == "/api/daily/watchlist": self.json(safe(api_watch_list))
        elif p == "/api/media/materials": self.json(safe(api_materials_list))
        elif p == "/api/media/topics": self.json(api_topics())
        elif p == "/api/aitools": self.json(safe(api_aitools))
        elif p == "/api/aitools/usage": self.json(safe(api_tool_usage_get))
        elif p == "/api/ai/running": self.json(safe(api_ai_running))
        elif p == "/api/ai/tasks": self.json(safe(api_ai_tasks))
        elif p == "/api/aihot": self.json(safe(api_aihot))
        elif p.startswith("/static/"):
            fn = p[len("/static/"):]
            self.static("static/" + fn, self._ctype(fn))
        else: self._send(404, b"not found", "text/plain; charset=utf-8")

    def do_POST(self):
        p = urllib.parse.urlparse(self.path).path
        n = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(n) if n else b"{}"
        try:
            data = json.loads(raw.decode("utf-8") or "{}")
        except Exception:
            data = {}
        if p == "/api/daily/plan":
            self.json(api_plan_add(data.get("text", ""), data.get("category", "通用")))
        elif p == "/api/aitools/usage":
            self.json(api_tool_usage_bump(data.get("name", "")))
        elif p.startswith("/api/daily/plan/") and p.endswith("/toggle"):
            self.json(api_plan_toggle(int(p.split("/")[-2])))
        elif p == "/api/daily/review":
            self.json(api_review_save(data.get("content", "")))
        elif p == "/api/daily/checkin/items":
            self.json(api_checkin_add(data.get("name", ""), data.get("category", "打卡")))
        elif p == "/api/daily/checkin/logs":
            self.json(api_checkin_toggle(int(data.get("item_id", 0)), data.get("date")))
        elif p == "/api/daily/events":
            self.json(api_events_add(data.get("title", ""), data.get("datetime", ""), data.get("note", "")))
        elif p == "/api/daily/ledger":
            self.json(api_ledger_add(data.get("type", ""), data.get("category", ""), data.get("amount", 0), data.get("note", ""), data.get("date")))
        elif p == "/api/daily/stock/reviews":
            self.json(api_stock_reviews_save(data.get("date"), data.get("market", ""), data.get("content", "")))
        elif p == "/api/daily/stock/strategy":
            self.json(api_stock_strategy_save(data.get("content", "")))
        elif p == "/api/daily/watchlist":
            self.json(api_watch_add(data.get("code", "").strip()))
        elif p == "/api/media/materials":
            self.json(api_materials_add(data.get("content", ""), data.get("tags", "")))
        else:
            self._send(404, b"not found")

    def do_DELETE(self):
        p = urllib.parse.urlparse(self.path).path
        if p.startswith("/api/daily/plan/"):
            self.json(api_plan_del(int(p.rsplit("/", 1)[-1])))
        elif p.startswith("/api/daily/checkin/items/"):
            self.json(api_checkin_del(int(p.rsplit("/", 1)[-1])))
        elif p.startswith("/api/daily/events/"):
            self.json(api_events_del(int(p.rsplit("/", 1)[-1])))
        elif p.startswith("/api/daily/ledger/"):
            self.json(api_ledger_del(int(p.rsplit("/", 1)[-1])))
        elif p.startswith("/api/daily/watchlist/"):
            self.json(api_watch_del(int(p.rsplit("/", 1)[-1])))
        elif p.startswith("/api/media/materials/"):
            self.json(api_materials_del(int(p.rsplit("/", 1)[-1])))
        else:
            self._send(404, b"not found")


def _warmup():
    """后台预热外部数据缓存，使首次打开页面即时出数。"""
    for fn in (api_news, api_topics, api_aihot, api_weather, api_stock):
        try:
            fn()
        except Exception:
            pass


def main():
    port = int(os.environ.get("PORT", "8788"))
    threading.Thread(target=_warmup, daemon=True).start()
    srv = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print("本地 AI 工作台 → 容器端口 %d（对外访问用部署平台分配的稳定公网 URL，数据持久化于挂载卷）" % port)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.shutdown()


if __name__ == "__main__":
    main()
