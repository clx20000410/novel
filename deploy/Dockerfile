# ============================================
# 第一阶段：构建前端静态资源
# ============================================
FROM node:20-slim AS frontend-builder

WORKDIR /frontend

# 配置 npm 使用中国镜像源
RUN npm config set registry https://registry.npmmirror.com

# 复制前端依赖文件
COPY frontend/package*.json ./

RUN npm install

# 安装前端依赖
RUN npm ci --prefer-offline --no-audit

# 复制前端源码
COPY frontend/ ./

# 构建前端
RUN npm run build

# ============================================
# 第二阶段：构建最终镜像（后端 + nginx）
# ============================================
FROM python:3.11-slim

# 配置 apt 使用中国镜像源
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's|security.debian.org/debian-security|mirrors.tuna.tsinghua.edu.cn/debian-security|g' /etc/apt/sources.list.d/debian.sources

WORKDIR /app

# 安装系统依赖：nginx、supervisor、curl、mysql客户端等
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    nginx \
    supervisor \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 配置 pip 使用中国镜像源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 复制后端依赖文件
COPY backend/requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端应用代码
COPY backend/ ./

# 清理可能被带入的 SQLite 数据文件，确保首次启动时根据环境变量初始化管理员密码
RUN rm -rf /app/storage && mkdir -p /app/storage

# 从前端构建阶段复制静态资源到 nginx 默认目录
COPY --from=frontend-builder /frontend/dist /usr/share/nginx/html

# 复制部署配置
COPY deploy/nginx.conf /etc/nginx/sites-available/default
COPY deploy/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY deploy/docker-entrypoint.sh /app/docker-entrypoint.sh

# 允许入口脚本在启动时修正宿主机挂载目录权限
RUN chmod +x /app/docker-entrypoint.sh

# 创建非 root 用户（供 supervisor 使用）
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# 暴露端口（nginx 80端口）
EXPOSE 80

# 使用 supervisor 启动 nginx 和 uvicorn
# 注意：容器以 root 启动，supervisor 会根据配置降权运行各个进程
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
