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
│   ├── 个人AI工作台搭建流程/                # 📦 原创 Skill 源（规范目录）
│   │   ├── SKILL.md                       # 主文件
│   │   ├── references/                    # 长文档（prompt.md / sources.md）
│   │   └── assets/                        # 模板 / 脚本 / 静态资源
│   ├── openclaw-video-toolkit/            # 📦 第三方（MIT，Digital Samba）视频剪辑工具箱
│   ├── claude-shorts/                     # 📦 第三方（MIT，Daniel Agrici）长转短一键切片
│   ├── ffmpeg-usage/                      # 📦 原创（Apache 2.0，huff7）ffmpeg 命令速查与实战配方
│   ├── 个人AI工作台搭建流程.zip            # 📦 打包产物（用 tools/pack.sh 生成）
│   ├── openclaw-video-toolkit.zip
│   ├── claude-shorts.zip
│   └── ffmpeg-usage.zip
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

## 已打包的 Skill 清单（含第三方）

本仓库除原创 Skill 外，还打包了「时序 · AI 提效与搞钱」系列视频中提到的**视频剪辑类 Skill**（详见 `ATTRIBUTION.md` 的许可与署名）：

| Skill 文件夹 | 来源 / 上游 | 许可 | 对应视频能力（Day4 资料包） |
|-------------|------------|------|--------------------------|
| `个人AI工作台搭建流程` | 本仓库原创 | Apache 2.0 | —（个人 AI 工作台搭建） |
| `openclaw-video-toolkit` | [digitalsamba/claude-code-video-toolkit](https://github.com/digitalsamba/claude-code-video-toolkit)（原 `khushil` 旧 owner，仍可 clone） | MIT（Digital Samba） | 1 智能粗剪 · 2 口播精修 · 3 批量处理 · 4 自动字幕 · 5 转码助手 · 6 品牌包装 · 7 动态片头（含 ffmpeg skill） |
| `claude-shorts` | [AgriciDaniel/claude-shorts](https://github.com/AgriciDaniel/claude-shorts) | MIT（Daniel Agrici） | 8 一键切片 ⭐ |
| `ffmpeg-usage` | 本仓库原创 | Apache 2.0（huff7） | 转码助手（5 号）底层命令层 · 截图/抽帧/封装/格式转换等通用音视频处理 |

> 每个 Skill 目录都提供完整源码；`tools/pack.sh <目录名>` 可重新生成对应的 `.zip` 一键安装包（已在 `skills/` 下生成）。
> 第三方 Skill 的版权与许可归原作者所有，使用前请阅读对应上游仓库的 `README` 与 `LICENSE`。

---

## License

本仓库采用 **Apache License 2.0**（见 `LICENSE` 文件）。

- 可自由使用、修改、二次分发（含闭源 / 商用）。
- 修改后分发需注明改动并保留原始署名。
- 不提供担保（"AS IS"），使用风险自负。
