# 个人AI工作台搭建流程 · 分发仓库

> 这是 **「个人AI工作台搭建流程」** 这个 WorkBuddy Skill 的**自包含分发仓库**。
> 仓库结构遵循统一的 Skills 仓库约定（参考 `skills/` 分层布局），可直接上传、安装或二次打包。

**License**: [Apache 2.0](LICENSE)

---

## 项目结构

```
hskills/
├── README.md                              # 本文件
├── LICENSE                                # Apache 2.0
├── .gitignore
│
├── skills/
│   ├── 个人AI工作台搭建流程/                # 📦 Skill 源（规范目录）
│   │   ├── SKILL.md                       # 主文件
│   │   ├── references/                    # 长文档（prompt.md / sources.md）
│   │   └── assets/                        # 模板 / 脚本 / 静态资源
│   └── 个人AI工作台搭建流程.zip            # 📦 打包产物（git 忽略，用 tools/pack.sh 生成）
│
├── docs/
│   └── 个人AI工作台搭建流程-通用提示词.md   # 独立提示词文档（可直接复制给 AI 使用）
│
└── tools/
    └── pack.sh                            # 重新打包 skill 为 zip
```

---

## 安装到 WorkBuddy

```bash
# 方式一：复制 skill 目录
cp -R skills/个人AI工作台搭建流程 ~/.workbuddy/skills/

# 方式二：解压 zip 分发包
unzip skills/个人AI工作台搭建流程.zip -d ~/.workbuddy/skills/
```

安装后重启会话，在对话中输入 `/` 或描述需求即可触发。

---

## 重新打包

```bash
./tools/pack.sh 个人AI工作台搭建流程
# → 输出: skills/个人AI工作台搭建流程.zip
```

---

## 内容说明

- **`skills/个人AI工作台搭建流程/`** — Skill 完整源（SKILL.md + references + assets）。
- **`docs/个人AI工作台搭建流程-通用提示词.md`** — 独立版提示词，可单独发给 AI 当一次性 prompt 使用，无需安装 skill。
- **`assets/`** 内含零依赖参考实现（`server.py` + `index.html`），是方法论的示范代码。

---

## License

本仓库采用 **Apache License 2.0**（见 `LICENSE` 文件）。

- 可自由使用、修改、二次分发（含闭源 / 商用）。
- 修改后分发需注明改动并保留原始署名。
- 不提供担保（"AS IS"），使用风险自负。
