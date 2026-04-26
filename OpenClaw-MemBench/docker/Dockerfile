# OpenClaw-MemBench Docker Image
# 基于官方 OpenClaw 镜像，修复了挂载覆盖问题

FROM ghcr.io/openclaw/openclaw:2026.4.15

USER root

# 将 openclaw 复制到不会被挂载覆盖的位置 (/opt/openclaw)
# 原镜像中 /usr/local/bin/openclaw 指向 /app/openclaw.mjs
# 但运行时会将 sandbox 挂载到 /app，导致 openclaw 命令失效
RUN mkdir -p /opt/openclaw /tmp_workspace /tmp_output /root/.openclaw && \
    cp -r /app/* /opt/openclaw/ && \
    chmod 777 /tmp_workspace /tmp_output && \
    rm -f /usr/local/bin/openclaw && \
    ln -s /opt/openclaw/openclaw.mjs /usr/local/bin/openclaw && \
    chmod +x /usr/local/bin/openclaw

# 设置环境变量
ENV PATH="/usr/local/bin:${PATH}"
ENV HOME=/root

# 清除基础镜像的 entrypoint，避免冲突
ENTRYPOINT []

# 验证 OpenClaw 可用
RUN openclaw --version

WORKDIR /root

# 默认保持容器运行
CMD ["tail", "-f", "/dev/null"]
