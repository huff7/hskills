# Deploy — 部署参考（Docker 沙箱 + 稳定公网 + PWA）

本文件是 `SKILL.md` Step 6 的落地手册。它给出两条互相排斥的部署大路，差别只在
**「数据落在哪」**。两条都满足 Step 6 的前三条（稳定公网地址 / HTTPS / Docker 沙箱），
只有第四条「数据始终本地」把两者分开。

> **方法论提醒**：本 skill 的原则是「绝不替用户默认技术栈」。所以这里只有候选 + 推荐，
> 真正拍板在对话里（Step 3 / Step 6）。本文件的「推荐默认」仅针对「用户明确要数据留本机」
> 的场景。

---

## 0. 两条大路：先定数据落点

| | 路线 A · 托管 PaaS（数据上云） | 路线 B · 零成本国内（数据留本机，推荐默认） |
|---|---|---|
| 后端/数据库跑在哪 | 平台云里的容器 + 持久卷 | **你自己的电脑**（Docker 容器 + 挂载卷） |
| 公网地址 | 平台分配子域 `*.onrender.com` 等 | 你自己的子域（免费或 ¥10–30/年） |
| HTTPS 来源 | 平台通配符证书 | Cloudflare Universal SSL（免费） |
| 稳定不随休眠失效 | ✅ | ✅（隧道主机名绑定，家 IP 怎么变都不变） |
| 数据本地（Step 6 第 4 条） | ❌ 数据在平台云 | ✅ 数据在你本机磁盘 |
|  recurring 费用 | 容器常驻要付费（按规格） | 仅域名费（可 ¥0）+ 本机电费 |
| 运维 | 平台全包，最低 | 本机容器保活 + 隧道客户端保活 |

**选路标准**：用户愿不愿意把数据放别人云？
- 愿意 → 路线 A（最省心，国内快，但数据在平台）。
- 不愿意，要数据留本机 → **路线 B**（本文件重点，下面详写）。

---

## 1. 路线 A · 托管 PaaS（数据在平台云）

形态 = `gz3.agentos-app.net` / `*.onrender.com` / `*.railway.app` 这一类：平台跑你的
Docker、挂卷、给固定 HTTPS 子域。它**完美满足 Step 6 前三条件**，代价是持久卷在平台云
（非本地），违反 Step 6 第 4 条「数据始终本地」。

**候选平台：**
- **Render** — `Dockerfile` 即部署，持久磁盘挂卷存 SQLite，免费版 15min 不活跃休眠但
  URL 不变、访问即唤醒；`*.onrender.com` 自带 HTTPS。
- **CloudBase 云托管（腾讯云）** — 原生 Docker + 卷，国内快、稳定；但容器常驻按
  vCPU/内存/流量计费，无真免费常驻档。
- **Railway / Fly.io / Koyeb** — 同类，按额度/规格计费。

**步骤（以 Render 为例）：**
1. 把 `assets/` 推到 GitHub 仓库（已含 `Dockerfile` + `config.json` 挂载约定）。
2. Render 控制台 → New → Web Service → 连仓库 → Runtime 选 Docker → 选 `Dockerfile`。
3. 建一个 **Persistent Disk**（挂载到 `/app/data`），`config.json` 另挂或置于镜像。
4. 部署完成即得 `https://xxx.onrender.com`（HTTPS，URL 稳定）。
5. 手机打开 → 加到主屏幕（见 §3）。

> 这条路不展开更多——平台 UI 年年变，步骤以平台当期文档为准。重点记住：
> **选它 = 接受数据上云；要数据本地请走路线 B。**

---

## 2. 路线 B · 零成本国内方案（数据留本机，推荐默认）

**原理一句话**：你注册/申请一个子域 → 把它交给 Cloudflare（免费，自动发 Universal SSL，
等于「通配符证书一次性签发」）→ 在你电脑上跑 `cloudflared`（隧道客户端，主动出站）→
把子域反向代理到你本机的 Docker 容器。数据 100% 留本机，HTTPS 由 Cloudflare 免费提供，
地址稳定不变，且**完全无视家宽封 80/443、CGNAT 无公网 IP** 这些老坑。

```
手机 ──HTTPS──► Cloudflare 边缘(Universal SSL)
                    │  隧道(本机主动出站，不被入站拦截)
                    ▼
              你电脑的 Docker 容器(server.py + SQLite 卷)
```

### 2.0 一键脚本：`assets/deploy.sh`

上面的 Docker 构建 + 容器运行 + Cloudflare Tunnel 三步，已封装成 `assets/deploy.sh`
（申请子域这一步仍须手工，见 §2.1）。它做：前置检查（docker / cloudflared 登录）→
`docker build` → 跑容器（`--restart always` + 端口 + 数据卷，幂等重跑）→ 建/复用命名隧道
→ 路由子域（幂等）→ 后台起隧道 → 验证公网 200 → 打印交付信息。

```bash
chmod +x assets/deploy.sh
# 手工前置（脚本不代劳）：§2.1 申请子域 + §2.2 接入 Cloudflare + 跑过一次 cloudflared tunnel login
./deploy.sh -d workbench.你的名.eu.org          # 全自动：Docker + 隧道
./deploy.sh -d workbench.你的名.eu.org --no-tunnel   # 只跑 Docker，不起隧道
```

停止：`docker rm -f workbench`；停隧道：`pkill -f "cloudflared tunnel run"`
（生产建议把两者交给 launchd/mac 或 systemd/linux 设为开机自启常驻）。

### 2.1 拿一个稳定子域（域名费可 ¥0）

> 不能用别人平台的子域（如 `*.agentos-app.net`）：那个通配符证书和容器都在平台云，
> 到不了你本机。必须用自己的（或免费申请的）子域。

**选项 1 · 免费子域（¥0，推荐先试）**
- **`eu.org`**（最贴本方案）：永久免费、支持把 NS 整体迁到你自己的 Cloudflare zone。
  人工审核，几天~数周；名字 ≥4 字符、中性不涉商标。
- **`is-a.dev`**（最简）：免费 `.dev` 子域，GitHub 登录即办，自带 HTTPS，审核几小时~1 天；
  DNS 在它家 Cloudflare 上，但你照样能设任意记录指向隧道。

**选项 2 · 付费真域名（¥10–30/年）**：想更「正经」就去任何注册商买 `.top`/`.cyou`/`.fun`
等促销档，流程同下、最省心。

> 别碰 `.tk/.ml/.ga/.cf/.gq`（Freenom）等「免费顶级域」——已基本灭绝、随时被收回。

**申请步骤：**
- *eu.org*：先去 Cloudflare 建 zone（Add a Site → 填 `你的名.eu.org` → Free，拿到两个
  NS 如 `ella.ns.cloudflare.com`）；再去 `nic.eu.org` 注册账号 → New Domain → 填
  `你的名.eu.org`、Nameserver 填那两个 Cloudflare NS、验证方式选 "Check for correctness
  of server names" → 提交等审核。过审后回 Cloudflare 接隧道。
- *is-a.dev*：打开其 manage 网站用 GitHub 登录 → Register → 填名字+邮箱（或官方 Discord
  打 `/register`）→ 合并后 DNS 生效。把记录设成指向你的 Cloudflare Tunnel（CNAME/代理）。

### 2.2 把子域接入 Cloudflare（免费，拿 HTTPS）

1. Cloudflare 控制台 → Add a Site → 填你的子域（如 `你的名.eu.org`）→ 选 Free。
2. 按提示把该子域的 NS 改成 Cloudflare 给的两个 NS（eu.org 过审后改；is-a.dev 在它平台
   里设 NS 指向 Cloudflare；付费域名在注册商处改）。
3. 生效后 Cloudflare 自动签发 **Universal SSL**——你任何子级
  （`workbench.你的名.eu.org`）都是 HTTPS。这就是「通配符证书一次性申请」的复刻版，
   只是证书签在你**自己的域**上。

### 2.3 本机装 cloudflared + 建 Tunnel + 路由到子域

```bash
# 1) 安装（mac）
brew install cloudflared
#   其他系统见 Cloudflare 文档

# 2) 登录（浏览器授权，把本机绑定到你的 Cloudflare 账号）
cloudflared tunnel login

# 3) 建一条命名隧道（名字随便）
cloudflared tunnel create workbench

# 4) 把子域路由到这条隧道（DNS 一条 CNAME 自动建好，URL 永久稳定）
cloudflared tunnel route dns workbench workbench.你的名.eu.org
```

> **为什么稳定**：隧道主机名 `workbench.你的名.eu.org` 永久绑定，不随家 IP 变化、
> 电脑重启而变。这正是它和「弱隧道」的本质区别（见 §2.6 注）。

### 2.4 本机跑 Docker 容器

```bash
# 构建镜像（assets/ 下已有 Dockerfile，容器绑 0.0.0.0、端口 8788）
cd assets
docker build -t workbench .

# 跑容器：端口映射 + 数据卷持久化（SQLite 在宿主机，不在镜像层）
docker run -d --name workbench \
  --restart always \
  -p 8788:8788 \
  -v "$(pwd)/data:/app/data" \
  -v "$(pwd)/config.json:/app/config.json" \
  workbench
```

### 2.5 起隧道、接上容器、验证

```bash
# 把隧道指到本机容器（http://localhost:8788）
cloudflared tunnel run --url http://localhost:8788 workbench
```

打开 `https://workbench.你的名.eu.org`：
- 应看到工作台（200）；查看页面源码含 `<link rel="manifest">` 与 SW 注册。
- `/manifest.json` → `display:"standalone"`；`/sw.js`、`/icon.svg` → 200。
- **手机加主屏幕**（§3）→ 离线重开应能看到壳（SW 预缓存生效）。

> **保活**：`cloudflared` 用 launchd（mac）/ systemd（linux）设为开机自启常驻；
> Docker 已加 `--restart always`。两者都挂 = 断电恢复后自动回到在线。

### 2.6 备选分支：不依赖 Cloudflare（DDNS + Caddy + 端口映射）

若不想用 Cloudflare，等价链路是：自己的域名 + **DDNS 客户端**（家 IP 一变自动更新解析）
+ **Caddy**（反向代理 + 自动 Let's Encrypt 证书）+ 路由器**端口映射**。

| 对比 | Cloudflare Tunnel（推荐） | DDNS + Caddy + 端口映射 |
|---|---|---|
| 额外费用 | 仅域名（可 ¥0） | 仅域名（可 ¥0） |
| CGNAT / 封 80·443 | **无感**（出站连接，全绕过） | 若 CGNAT 无公网 IP → 需加中继 VPS（¥60–150/年）；封端口 → 用 DNS-01 验证 |
| URL 稳定性 | 完全无感，永不中断 | 家 IP 变更瞬间有几十秒~几分钟解析抖动 |
| 配置量 | 低 | 中（DDNS + Caddy + 路由器三项） |

> **关于「隧道」的口径纠正**：`SKILL.md`/`sources.md` 此前「Avoid tunnels」针对的是
> **弱隧道**（cloudflared 临时隧道 / localtunnel / pinggy）——它们地址随机转、中继易断、
> 不随休眠存活。**Cloudflare Tunnel（命名隧道 + 你自己的域）不属于这一类**：公网地址
> 稳定、HTTPS 由 Cloudflare 提供、本机出站绕过所有入站限制。它是路线 B 的推荐实现。
> 判断标准只有一条：**公网 URL 是否稳定且 HTTPS**。稳 → 可用；转 → 弃。

---

## 3. PWA 注意点（两条路线通用）

PWA 是前端能力（manifest + service worker），只要求运行在 **HTTPS 安全上下文**。两条路线
都给 HTTPS，所以 PWA 在两者都能注册：离线打开 / 全屏无地址栏 / 加到主屏幕 全部生效。

- `manifest.json` 由 `server.py` 动态生成（取自 `config.json` 的 `brand` / `short_name` /
  `theme_color` / `background_color`），`display:"standalone"`。
- **图标**：默认只挂 `static/icon.svg`（矢量兜底，现代浏览器可装）。要满足 **iOS/Android 全平台**
  安装要求，把 `icon-192.png` / `icon-512.png` / `icon-maskable-512.png` 放进 `static/`，
  `server.py` 会自动探测并加入 manifest（无需改代码）。SVG 始终保留作兜底。
- `sw.js` 预缓存应用壳（`/`、`index.html`、`manifest.json`、`echarts`、`icon.svg`），
  `/api/*` 走 stale-while-revalidate。
- **隐藏好处**：数据在本地 + SW 缓存壳 → 家网络短暂抖动 / 电脑重启几秒里，手机打开 app
  仍能看到壳和上次缓存数据，不会直接白屏。这正好缓冲「数据本地 = 可用性绑家网络」。
- **iOS 启动屏**：iOS 不读 manifest 的 `background_color` 当 splash，需额外 `apple-touch-startup-image`
  或接受默认。Android 用 manifest `icons`+`background_color` 即出 splash。

**手机加主屏幕教学（交付项）：**
- **iOS (Safari)**：打开公网 URL → 分享（□↑）→ *添加到主屏幕* → 命名 → 添加。启动即 standalone。
- **Android (Chrome)**：打开 URL → ⋮ → *安装应用* / *添加到主屏幕* → 确认。
- 确认安装后的图标启动无浏览器框（standalone）；离线重开应仍显示壳。

---

## 4. 决策速查

- 要数据留本机、零成本、国内快 → **路线 B（推荐）**：子域 + Cloudflare + Tunnel + 本机 Docker。
- 要数据留本机、但不想碰 Cloudflare → 路线 B 备选：DDNS + Caddy + 端口映射（家宽受限时可能冒出 VPS 费用）。
- 能接受数据上云、最省心 → **路线 A**：Render / CloudBase 云托管（URL 稳定、HTTPS、平台全包，但数据在平台云）。
- EdgeOne / Cloudflare Workers 这类 serverless → **不在本题解内**：无持久卷，用它们就得把
  SQLite 换成托管数据库（数据上云，违反 Step 6 第 4 条），属路线 A 的「改架构版」，不推荐。

**唯一不可去掉的代价（路线 B）**：数据真在本地，可用性就绑你家网络/供电。断电/断网/重启 =
全挂，无 SLA。这是「数据本地」与「永远在线」的根本矛盾，谁都绕不开——用 PWA 壳 + 隧道保活
只能缓解，不能消除。
