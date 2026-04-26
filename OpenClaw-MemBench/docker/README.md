# OpenClaw-MemBench Docker 配置

## 文件说明

| 文件 | 说明 |
|------|------|
| `Dockerfile` | **推荐使用** - 修复了挂载覆盖问题的最终版本 |
| `Dockerfile.openclaw-*` | 历史版本文件（已弃用） |
| `Dockerfile.standalone` | 独立构建版本（备用） |
| `Dockerfile.windows` | Windows 环境专用（备用） |

## 快速构建

```bash
cd ..
docker build -f docker/Dockerfile -t openclaw-membench:latest .
```

## 关键修复

原官方镜像的问题是：`/usr/local/bin/openclaw` 指向 `/app/openclaw.mjs`。

运行时 workspace 挂载到 `/app`，导致 openclaw 命令失效。

**本 Dockerfile 的修复**：将 openclaw 复制到 `/opt/openclaw/`，该位置不会被挂载覆盖。

```dockerfile
RUN mkdir -p /opt/openclaw && \
    cp -r /app/* /opt/openclaw/ && \
    rm -f /usr/local/bin/openclaw && \
    ln -s /opt/openclaw/openclaw.mjs /usr/local/bin/openclaw
```

## 验证镜像

```bash
docker run --rm openclaw-membench:latest openclaw --version
# 应输出: OpenClaw 2026.4.15
```

## 运行测评

详见 [docs/DOCKER_SETUP.md](../docs/DOCKER_SETUP.md)
