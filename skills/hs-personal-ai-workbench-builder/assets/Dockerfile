# 个人 AI 工作台 — 零依赖 Docker 沙箱
# 数据通过挂载卷持久化到宿主机，容器可随意重建，数据不丢。
#
# 构建：  docker build -t ai-workbench .
# 运行：  docker run -d --name wb \
#           -p 8788:8788 \
#           -v $(pwd)/data:/app/data \
#           -v $(pwd)/config.json:/app/config.json \
#           ai-workbench
# 对外访问地址由部署平台分配的稳定公网 URL 提供（不随容器/沙箱休眠失效）。
# 删除容器不会删 data/ 与 config.json（它们在宿主机挂载卷里）。
FROM python:3.12-slim

WORKDIR /app

# 仅复制运行时文件。数据（SQLite）在宿主机挂载卷，不进镜像层。
COPY server.py ./
COPY config.example.json ./config.json
COPY static/ ./static/

EXPOSE 8788
ENV PORT=8788

# 容器内绑定 0.0.0.0，由平台映射端口；个性化全在 config.json，代码零硬编码。
CMD ["python3", "server.py"]
