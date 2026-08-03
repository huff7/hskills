# Skills 仓库 · 我的 AI 能力合集（monorepo）

> 这是一个**单一仓库（monorepo）**，集中存放我将要制作 / 维护的多个 WorkBuddy Skills。
> 本文件是**仓库级**说明，不是某一个 Skill 的文档——新增 Skill 时直接套用下面的约定。
>
> 本仓库**独立维护**，与其它任何 Skills 仓库（例如 `dev/skills/`）**没有对应 / 同步关系**，各自独立提交、独立分发。

**License**: [Apache 2.0](LICENSE)

---

## 项目结构

```
hskills/                              # 仓库根
├── README.md                         # 本文件（仓库级说明）
├── LICENSE                           # Apache 2.0
├── .gitignore
│
├── skills/                           # 📦 正式发布的 Skills（每个一个目录）
│   ├── 个人AI工作台搭建流程/          # 需求驱动的个人本地工作台搭建方法论
│   └── <其它 skill 目录>/            # 后续新增
│
├── docs/                             # 📖 仓库级文档、参考资料、独立提示词
│   └── 个人AI工作台搭建流程-通用提示词.md
│
├── tools/                            # 🔧 构建 & 维护脚本
│   └── pack.sh                       # 单 Skill 打包为 zip
│
└── z/                                # 🗑️ 暂存 / 参考素材（不纳入版本管理）
```

---

## `skills/` — 正式 Skills

### 目录约定

一个 Skill = `skills/` 下的一个子目录，目录名即该 Skill 的显示名（slug）。

```
skills/<skill-显示名>/
├── SKILL.md                      # 【必须】Skill 主文件，含 frontmatter
├── references/                   # 【可选】长文档：指南 / 范例 / 速查表
├── assets/                       # 【可选】模板 / 脚本 / 静态资源
└── scripts/                      # 【可选】校验 / 构建脚本
```

### 铁律

1. **目录名 = 显示名**（与 `SKILL.md` 的 `name` 字段一致；中文也可）。
2. 每个 Skill 目录**必须**含 `SKILL.md`，且 frontmatter 含 `name` / `description` / `agent_created: true`。
3. 仓库只存**源文件**。zip 包是派生产物（由 `tools/pack.sh` 生成），不提交进仓库。

### SKILL.md 规范

```yaml
---
name: <显示名>                    # = 目录名，唯一标识（中文也可）
description: "一句话说清这个 Skill 解决什么、何时用、何时不用"
agent_created: true               # 由 AI 创建的 Skill 固定为 true
---
# <显示名>（一句话副标题）

...正文...
```

- `description` 写清：**用途 + 触发场景 + 反例（NOT for …）**。
- 正文遵循「推导方法而非产品规格」原则：从用户痛点出发，不硬编码作者专属标签、路径、品牌色等。

### 当前收录

| 目录 | 说明 |
|------|------|
| `个人AI工作台搭建流程/` | 需求驱动的个人本地工作台搭建方法论（含零依赖参考实现 + 独立提示词文档）|

> 后续每新增一个 Skill，在此表追加一行即可。

---

## 如何新增一个 Skill

1. 在 `skills/` 下新建目录 `<显示名>/`。
2. 放入 `SKILL.md`（用上面模板），按既有 Skill 的写法成文。
3. 附属文档放 `references/`，模板 / 脚本放 `assets/`、`scripts/`；若需独立提示词文档，放 `docs/`。
4. 本地自测：把目录复制到 `~/.workbuddy/skills/<显示名>/`，在 WorkBuddy 里调用验证。
5. 在本文档「当前收录」表格追加一行。
6. 提交（commit）；需要分发时运行 `./tools/pack.sh <显示名>` 打包。

---

## 安装到 WorkBuddy

```bash
# 方式一：复制整个 Skill 目录
cp -R skills/<显示名> ~/.workbuddy/skills/

# 方式二：解压 zip 分发包
unzip skills/<显示名>.zip -d ~/.workbuddy/skills/
```

安装后重启会话，在对话中输入 `/` 或描述需求即可触发。

---

## 分发（zip 包）

```bash
# 打包单个 Skill
./tools/pack.sh 个人AI工作台搭建流程
# → 输出: skills/个人AI工作台搭建流程.zip
```

---

## `docs/` — 文档与参考资料

存放仓库级别的文档、入门指南、参考资料，以及可作为一次性 prompt 直接发给 AI 的独立提示词文档（如 `个人AI工作台搭建流程-通用提示词.md`）。

---

## `tools/` — 构建与维护脚本

| 脚本 | 用法 | 说明 |
|------|------|------|
| `pack.sh` | `./tools/pack.sh <skill名>` | 将指定 Skill 打包为 zip 分发包 |

---

## `z/` — 暂存素材

`z/` 是**暂存 / 参考素材目录**（收集来的第三方 skill 样例、草稿），**不属于正式收录的 Skill，不纳入版本管理**（已在 `.gitignore` 排除）。
需要沉淀为正式 Skill 时，按「如何新增」流程迁到 `skills/` 下并在上表登记。

---

## Skill 质量自检清单

- [ ] `name` 与目录名一致
- [ ] `description` 含「触发场景 + 反例」
- [ ] 全程痛点驱动，无作者专属硬编码标签
- [ ] 有 `references/` 长文档则已拆分，不在 `SKILL.md` 内堆长文
- [ ] 前端 / 脚本类 Skill 含「截图实测」验证步骤（禁止只 curl）
- [ ] 需求访谈 / 关键决策有快照或 CHANGELOG 留存，便于增量迭代

---

## License

本仓库整体采用 **Apache License 2.0**（见 `LICENSE` 文件）。

- 你**可以自由使用、修改、二次分发**本仓库中的 Skill（含其代码与文档），包括闭源或商用。
- 若你**修改后分发**，需在修改后的文件显著位置注明改动，并保留原始版权 / 署名声明。
- 本仓库自带**专利授权**：贡献者授予你使用其专利的许可；若你主动提起专利诉讼主张本仓库构成侵权，该专利许可自动终止。
- 本仓库**不提供担保**（"AS IS"），使用风险由使用者自行承担。

如需为某个具体 Skill 设置与其他 Skill 不同的许可，请在该 Skill 目录内单独放置 `LICENSE` 文件，并在 `SKILL.md` 顶部注明。
