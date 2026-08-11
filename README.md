# 个人AI工作台搭建流程 · 分发仓库（召唤命令 /hs-personal-ai-workbench-builder）

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
│   ├── hs-personal-ai-workbench-builder/   # 📦 原创 Skill 源（召唤：/hs-personal-ai-workbench-builder）
│   │   ├── SKILL.md                       # 主文件
│   │   ├── references/                    # 长文档（prompt.md / sources.md）
│   │   └── assets/                        # 模板 / 脚本 / 静态资源
│   │
│   ├── hs-ffmpeg-usage/               # 📦 原创（Apache 2.0，huff7）ffmpeg 命令速查与实战配方
│   ├── hs-ai-video-skills-collection/ # 📦 原创（Apache 2.0，huff7）一键安装编排：装好 8 个视频 Skill
│   │
│   ├── hs-personal-ai-workbench-builder.zip
│   ├── hs-ffmpeg-usage.zip
│   └── hs-ai-video-skills-collection.zip
│
├── docs/
│   └── hs-personal-ai-workbench-builder-通用提示词.md   # 独立提示词文档（可直接复制给 AI 使用）
│
└── tools/
    └── pack.sh                            # 重新打包 skill 为 zip
```

> **关于「用 AI 做视频的 8 个 Skill」**：本仓库**不捆绑**它们的源码。
> 它们由用户各自的 Agent 从原作者仓库通过 `npx skills add` 安装，由一个原创编排 Skill
> **`hs-ai-video-skills-collection`** 统一驱动一键安装（详见下方清单与 `ATTRIBUTION.md`）。

---

## 已打包的 Skill 清单（均为本仓库原创）

| Skill 文件夹（召唤命令） | 来源 | 许可 | 说明 |
|--------------------------|------|------|------|
| `hs-personal-ai-workbench-builder`（`/hs-personal-ai-workbench-builder`）| 本仓库原创 | Apache 2.0 | 个人 AI 工作台搭建方法论 |
| `hs-ffmpeg-usage`（`/hs-ffmpeg-usage`）| 本仓库原创（huff7） | Apache 2.0 | ffmpeg / ffprobe 命令速查与实战配方（转码助手底层命令层）|
| `hs-ai-video-skills-collection`（`/hs-ai-video-skills-collection`）| 本仓库原创（huff7） | Apache 2.0 | **安装编排器**：触发后逐个安装「用 AI 做视频」所需的 8 个开源 Skill 并汇报状态（不捆绑源码）|

---

## 引用的外部视频 Skill（不随本仓库分发，由用户各自安装）

`hs-ai-video-skills-collection` 会指引 Agent 从上游安装以下 8 个开源 Skill（许可以各自上游仓库为准）：

| # | 能力 | 来源仓库 | 安装命令 | 许可 |
|---|------|---------|----------|------|
| 1 | 智能粗剪 | [browser-use/video-use](https://github.com/browser-use/video-use) | `npx skills add browser-use/video-use` | MIT |
| 2 | 口播精修 | [Vibetool/talking-head-video](https://github.com/Vibetool/talking-head-video) | `npx skills add Vibetool/talking-head-video` | MIT |
| 3 | 批量处理 | [amywork777/video-editing-pipeline](https://github.com/amywork777/video-editing-pipeline) | `npx skills add amywork777/video-editing-pipeline` | 未声明（需授权）|
| 4 | 自动字幕 | [kwindla/skill-caption-clip](https://github.com/kwindla/skill-caption-clip) | `npx skills add kwindla/skill-caption-clip` | MIT |
| 5 | 转码助手（ffmpeg）| [huff7/hskills · ffmpeg-usage](https://github.com/huff7/hskills)（**本仓库原创**）| `git clone` 后复制 `skills/hs-ffmpeg-usage/` | Apache 2.0 |
| 6 | 品牌包装 | [op7418/Video-Wrapper-Skills](https://github.com/op7418/Video-Wrapper-Skills) | `npx skills add op7418/Video-Wrapper-Skills` | MIT |
| 7 | 动态片头 | [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) + [remotion-dev/skills](https://github.com/remotion-dev/skills) | `npx skills add heygen-com/hyperframes --full-depth` / `npx skills add remotion-dev/skills` | 见上游 |
| 8 | 一键切片 ⭐ | [AgriciDaniel/claude-shorts](https://github.com/AgriciDaniel/claude-shorts) | `npx skills add AgriciDaniel/claude-shorts` | MIT |

> 完整对照表（含「跟 Agent 说这句话」话术与兜底路径）见 `hs-ai-video-skills-collection/references/skills-catalog.md`。

---

## 安装到 WorkBuddy

```bash
# 原创 Skill：复制目录 或 解压 zip
cp -R skills/hs-ffmpeg-usage              ~/.workbuddy/skills/
cp -R skills/hs-ai-video-skills-collection ~/.workbuddy/skills/
unzip skills/hs-ffmpeg-usage.zip -d ~/.workbuddy/skills/

# 装好 hs-ai-video-skills-collection 后，把下面这段话发给你的 Agent，它自动装好上面 8 个视频 Skill：
# （完整 Prompt 见 skills/hs-ai-video-skills-collection/references/install-prompt.txt）
```

安装后重启会话，在对话中输入 `/` 或描述需求即可触发。

---

## 重新打包

```bash
./tools/pack.sh hs-personal-ai-workbench-builder
./tools/pack.sh hs-ffmpeg-usage
./tools/pack.sh hs-ai-video-skills-collection
# → 各自输出对应 .zip
```

---

## 内容说明

- **`skills/hs-personal-ai-workbench-builder/`** — Skill 完整源（SKILL.md + references + assets）。
- **`skills/hs-ffmpeg-usage/`** — 原创 ffmpeg 命令配方库（SKILL.md + references/ffmpeg-cheatsheet.md）。
- **`skills/hs-ai-video-skills-collection/`** — 原创安装编排 Skill（SKILL.md + references/ 速查表与一键安装 Prompt）。
- **`docs/hs-personal-ai-workbench-builder-通用提示词.md`** — 独立版提示词，可单独发给 AI 当一次性 prompt 使用，无需安装 skill。

---

## License

本仓库采用 **Apache License 2.0**（见 `LICENSE` 文件）。

- 可自由使用、修改、二次分发（含闭源 / 商用）。
- 修改后分发需注明改动并保留原始署名。
- 不提供担保（"AS IS"），使用风险自负。
- 引用的外部 Skill 各自遵循其上游许可，使用前请阅读对应仓库的 `README` 与 `LICENSE`。
