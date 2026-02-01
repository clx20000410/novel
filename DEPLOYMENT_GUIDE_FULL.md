# AI-Novel 完整部署指南

## 目录

1. [环境要求](#环境要求)
2. [快速部署（推荐）](#快速部署推荐)
3. [手动部署](#手动部署)
4. [数据库迁移](#数据库迁移)
5. [配置说明](#配置说明)
6. [健康检查](#健康检查)
7. [日志查看](#日志查看)
8. [回滚操作](#回滚操作)
9. [常见问题](#常见问题)

---

## 环境要求

### 服务器配置

- **操作系统**：Ubuntu 22.04 或更高版本
- **CPU**：2 核心或以上
- **内存**：4GB 或以上
- **磁盘**：20GB 可用空间
- **网络**：公网 IP 或域名

### 软件依赖

- **Docker**：20.10 或更高版本
- **Docker Compose**：2.0 或更高版本
- **Git**：2.x
- **MySQL**：8.0（如果使用 MySQL）

---

## 快速部署（推荐）

### 方式一：本地执行一键部署脚本

适用于从本地机器部署到远程服务器。

```bash
# 1. 克隆项目（如果还没有）
git clone https://github.com/all666666all/AI-novel.git
cd AI-novel

# 2. 配置 SSH 密钥（确保可以免密登录服务器）
ssh-copy-id root@45.15.185.52

# 3. 执行一键部署
bash deploy/scripts/quick_deploy.sh
```

### 方式二：直接在服务器上部署

适用于直接登录到服务器进行部署。

```bash
# 1. SSH 登录服务器
ssh root@45.15.185.52

# 2. 克隆项目
cd /root
git clone https://github.com/all666666all/AI-novel.git
cd AI-novel

# 3. 创建 .env 文件
cp .env.example .env
nano .env  # 编辑配置

# 4. 执行部署
bash deploy/scripts/deploy_docker.sh
```

---

## 手动部署

### 1. 准备环境

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Docker
curl -fsSL https://get.docker.com | bash
sudo systemctl start docker
sudo systemctl enable docker

# 安装 Docker Compose（如果未安装）
sudo apt install docker-compose-plugin -y

# 验证安装
docker --version
docker compose version
```

### 2. 克隆项目

```bash
cd /root
git clone https://github.com/all666666all/AI-novel.git
cd AI-novel
```

### 3. 配置环境变量

```bash
# 复制示例配置
cp .env.example .env

# 编辑配置文件
nano .env
```

**必需配置项**：

```env
# 安全密钥（生成随机字符串）
SECRET_KEY=your_random_secret_key_here

# 数据库配置
DB_PROVIDER=mysql  # 或 sqlite
MYSQL_HOST=db
MYSQL_PORT=3306
MYSQL_USER=arboris
MYSQL_PASSWORD=your_strong_password_here
MYSQL_DATABASE=arboris
MYSQL_ROOT_PASSWORD=your_root_password_here

# OpenAI API
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_API_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL_NAME=gpt-4

# 管理员账号
ADMIN_DEFAULT_USERNAME=admin
ADMIN_DEFAULT_PASSWORD=your_admin_password_here
ADMIN_DEFAULT_EMAIL=admin@example.com

# 应用端口
APP_PORT=80
```

### 4. 执行数据库迁移

```bash
# 如果使用 MySQL
bash deploy/scripts/run_migrations.sh

# 验证迁移结果
bash deploy/scripts/verify_migration.sh
```

### 5. 构建并启动服务

```bash
cd deploy

# 如果使用 MySQL
docker-compose --profile mysql build --no-cache
docker-compose --profile mysql up -d

# 如果使用 SQLite
docker-compose build --no-cache
docker-compose up -d
```

### 6. 验证部署

```bash
# 检查容器状态
docker-compose ps

# 检查健康状态
curl http://localhost/api/health

# 查看日志
docker-compose logs -f app
```

---

## 数据库迁移

### 自动迁移（推荐）

```bash
bash deploy/scripts/run_migrations.sh
```

### 手动迁移

```bash
# 1. 连接到数据库
mysql -h localhost -u arboris -p arboris

# 2. 执行迁移脚本
source backend/db/migrations/add_novel_kit_features.sql
source backend/db/migrations/add_deep_optimization_features.sql

# 3. 验证表结构
SHOW TABLES;
DESCRIBE character_states;
```

### 验证迁移

```bash
bash deploy/scripts/verify_migration.sh
```

---

## 配置说明

### 核心配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `SECRET_KEY` | 应用密钥（必需） | - |
| `ENVIRONMENT` | 运行环境 | `production` |
| `DEBUG` | 调试模式 | `false` |
| `APP_PORT` | 应用端口 | `80` |

### 数据库配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `DB_PROVIDER` | 数据库类型 | `sqlite` |
| `MYSQL_HOST` | MySQL 主机 | `db` |
| `MYSQL_PORT` | MySQL 端口 | `3306` |
| `MYSQL_USER` | MySQL 用户 | `arboris` |
| `MYSQL_PASSWORD` | MySQL 密码（必需） | - |
| `MYSQL_DATABASE` | MySQL 数据库名 | `arboris` |

### AI 配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `OPENAI_API_KEY` | OpenAI API 密钥（必需） | - |
| `OPENAI_API_BASE_URL` | OpenAI API 地址 | `https://api.openai.com/v1` |
| `OPENAI_MODEL_NAME` | 使用的模型 | `gpt-3.5-turbo` |
| `WRITER_CHAPTER_VERSION_COUNT` | 章节生成版本数 | `2` |

### 写作流程配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `writer.enable_preview` | 启用预览阶段 | `true` |
| `writer.enable_critique` | 启用自我批评 | `true` |
| `writer.enable_reader_simulation` | 启用读者模拟 | `true` |
| `writer.critique_max_iterations` | 批评最大迭代次数 | `2` |
| `writer.critique_target_score` | 批评目标分数 | `75` |
| `writer.review_interval` | 周期回顾间隔（章） | `5` |
| `writer.arc_type` | 情绪曲线类型 | `standard` |

---

## 健康检查

### API 健康检查

```bash
curl http://localhost/api/health
```

**正常响应**：
```json
{
  "status": "healthy",
  "timestamp": "2026-01-13T04:00:00Z"
}
```

### 容器健康检查

```bash
docker-compose -f deploy/docker-compose.yml ps
```

### 数据库连接检查

```bash
# 进入容器
docker-compose -f deploy/docker-compose.yml exec app bash

# 测试数据库连接
python3 -c "from app.db.database import engine; print('Database connected')"
```

---

## 日志查看

### 查看应用日志

```bash
# 实时查看
docker-compose -f deploy/docker-compose.yml logs -f app

# 查看最近 100 行
docker-compose -f deploy/docker-compose.yml logs --tail=100 app

# 查看特定时间范围
docker-compose -f deploy/docker-compose.yml logs --since 1h app
```

### 查看数据库日志

```bash
docker-compose -f deploy/docker-compose.yml --profile mysql logs -f db
```

### 查看 Nginx 日志

```bash
# 进入容器
docker-compose -f deploy/docker-compose.yml exec app bash

# 查看访问日志
tail -f /var/log/nginx/access.log

# 查看错误日志
tail -f /var/log/nginx/error.log
```

---

## 回滚操作

### 自动回滚

```bash
bash deploy/scripts/rollback.sh
```

脚本会：
1. 列出所有可用的备份
2. 创建当前数据库的安全备份
3. 恢复选定的备份
4. 重启服务

### 手动回滚

```bash
# 1. 停止服务
cd deploy
docker-compose down

# 2. 恢复数据库
mysql -h localhost -u arboris -p arboris < backups/backup_20260113_120000.sql

# 3. 重启服务
docker-compose --profile mysql up -d
```

---

## 常见问题

### 1. 容器无法启动

**问题**：`docker-compose up -d` 后容器立即退出

**解决方案**：
```bash
# 查看日志
docker-compose logs app

# 常见原因：
# - .env 文件配置错误
# - 端口被占用
# - 数据库连接失败
```

### 2. 数据库连接失败

**问题**：应用日志显示 "Can't connect to MySQL server"

**解决方案**：
```bash
# 检查数据库容器状态
docker-compose --profile mysql ps

# 检查数据库日志
docker-compose --profile mysql logs db

# 验证数据库配置
cat .env | grep MYSQL
```

### 3. 健康检查失败

**问题**：`curl http://localhost/api/health` 返回错误

**解决方案**：
```bash
# 检查容器是否运行
docker ps

# 检查端口映射
docker port arboris-app

# 检查应用日志
docker-compose logs --tail=50 app
```

### 4. 迁移脚本执行失败

**问题**：数据库迁移时报错

**解决方案**：
```bash
# 检查表是否已存在
mysql -h localhost -u arboris -p arboris -e "SHOW TABLES;"

# 如果表已存在，可以跳过迁移
# 或者手动删除表后重新执行
```

### 5. 前端无法访问

**问题**：访问 `http://服务器IP` 无响应

**解决方案**：
```bash
# 检查防火墙
sudo ufw status
sudo ufw allow 80/tcp

# 检查 Nginx 配置
docker-compose exec app nginx -t

# 重启 Nginx
docker-compose exec app supervisorctl restart nginx
```

---

## 维护操作

### 更新代码

```bash
cd /root/AI-novel
git pull origin main
bash deploy/scripts/deploy_docker.sh
```

### 备份数据库

```bash
# 手动备份
mysqldump -h localhost -u arboris -p arboris > backups/manual_backup_$(date +%Y%m%d_%H%M%S).sql

# 定时备份（crontab）
0 2 * * * cd /root/AI-novel && mysqldump -h localhost -u arboris -p'your_password' arboris > backups/auto_backup_$(date +\%Y\%m\%d_\%H\%M\%S).sql
```

### 清理旧容器和镜像

```bash
# 停止并删除容器
docker-compose -f deploy/docker-compose.yml down

# 删除旧镜像
docker image prune -a

# 清理未使用的卷
docker volume prune
```

### 监控资源使用

```bash
# 查看容器资源使用
docker stats

# 查看磁盘使用
df -h

# 查看内存使用
free -h
```

---

## 生产环境建议

### 安全配置

1. **修改默认密码**：
   - 管理员密码
   - MySQL root 密码
   - MySQL 用户密码

2. **配置 HTTPS**：
   ```bash
   # 安装 Certbot
   sudo apt install certbot python3-certbot-nginx
   
   # 获取证书
   sudo certbot --nginx -d your-domain.com
   ```

3. **配置防火墙**：
   ```bash
   sudo ufw enable
   sudo ufw allow 22/tcp
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   ```

### 性能优化

1. **增加 MySQL 连接数**：
   编辑 `deploy/docker-compose.yml`，在 `db` 服务的 `command` 中添加：
   ```yaml
   - --max_connections=1000
   ```

2. **配置 Redis 缓存**（可选）：
   添加 Redis 服务到 `docker-compose.yml`

3. **启用 Gzip 压缩**：
   编辑 `deploy/nginx.conf`，添加：
   ```nginx
   gzip on;
   gzip_types text/plain text/css application/json application/javascript;
   ```

### 监控和告警

1. **配置日志收集**：
   - 使用 ELK Stack 或 Loki
   - 配置日志轮转

2. **配置监控**：
   - Prometheus + Grafana
   - 监控 CPU、内存、磁盘、网络

3. **配置告警**：
   - 服务不可用告警
   - 资源使用告警
   - 错误日志告警

---

## 联系支持

如有问题，请：
1. 查看日志：`docker-compose logs app`
2. 检查 GitHub Issues
3. 联系技术支持

---

*最后更新：2026-01-13*
