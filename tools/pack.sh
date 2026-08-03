#!/usr/bin/env bash
# pack.sh — 打包单个 Skill 为 zip 分发包
# 用法: ./tools/pack.sh <skill-dir-name>
# 示例: ./tools/pack.sh 个人AI工作台搭建流程
#
# 输出: skills/<skill-dir-name>.zip（仓库根的 skills/ 下）

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILLS_DIR="$REPO_ROOT/skills"

if [ $# -lt 1 ]; then
  echo "用法: $0 <skill-dir-name>"
  echo "可用 Skill:"
  ls -1 "$SKILLS_DIR" | grep -v '\.zip$'
  exit 1
fi

NAME="$1"
SRC="$SKILLS_DIR/$NAME"

if [ ! -d "$SRC" ]; then
  echo "❌ 找不到 skill 目录: $SRC" >&2
  exit 1
fi

OUT="$SKILLS_DIR/$NAME.zip"

# 清理旧 zip
[ -f "$OUT" ] && rm -f "$OUT"

# 打包：排除 .DS_Store、__pycache__、node_modules、.git
(cd "$SRC" && zip -r "$OUT" . \
  -x '*.DS_Store' \
  -x '*__pycache__/*' \
  -x '*node_modules/*' \
  -x '*.git/*')

echo "✅ 已打包: $OUT ($(du -h "$OUT" | cut -f1))"
