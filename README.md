<div align="center">

# 🌳 Arboris Novel

**AI 驱动的小说创作平台 —— 让创意生根发芽**

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/Vue-3.5-brightgreen.svg)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)

[功能特色](#-功能特色) • [快速开始](#-快速开始) • [配置说明](#-配置说明) • [开发指南](#-开发指南) • [常见问题](#-常见问题) • [参与贡献](#-参与贡献)

</div>

---

## 📖 项目简介

**Arboris** 不是一个简单的 AI 文本生成器，而是一个**能记住你的世界、理解你的角色、陪你一起推进故事的创作伙伴**。

无论你是网文作者、小说爱好者，还是世界观构建狂魔，Arboris 都能帮助你：
- 🎭 **系统化管理**你的角色、地点、派系设定
- 🧠 **AI 辅助创作**从大纲到章节的全流程
- 🔄 **多版本对比**找到最合适的表达方式
- 📚 **永不遗忘**的世界观知识库

我们选择**开源**——因为好的工具应该属于所有创作者。

---

## ✨ 功能特色

### 📖 设定管理 —— 管住那些跑偏的设定
写到第五十章突然想不起来男二号的眼睛是什么颜色？世界观里的魔法体系到底有几个等级？
Arboris 帮你把所有角色、地点、派系的设定都记下来，随时翻阅，再也不会前后矛盾。

### 🧵 大纲梳理 —— 把乱糟糟的灵感捋成故事线
脑子里有十几个场景片段，但不知道怎么串起来？
和 AI 聊聊你的想法，它会帮你梳理出一条主线，从开头到结局的大纲自然就出来了。

### ✍️ 协作写作 —— 有个不会累的写作搭档
今天状态不好，但又不想断更？让 AI 先写个草稿，你再根据自己的风格改改。
或者反过来——你写了开头，让它接着往下试试，没准能给你意想不到的灵感。

### 🔄 多版本对比 —— 找到最对味的那一版
AI 生成的内容不一定第一次就完美，但你可以让它多试几版，挑出最喜欢的部分，慢慢"训练"它懂你的笔触。

---

## 🛠️ 技术栈

| 层级 | 技术选型 |
|:---:|:---|
| **前端** | Vue 3 + TypeScript + Vite + Tailwind CSS + Naive UI + Pinia |
| **后端** | Python + FastAPI + SQLAlchemy |
| **数据库** | SQLite（默认） / MySQL |
| **AI 服务** | OpenAI API（或兼容接口） |
| **部署** | Docker + Docker Compose + Nginx |

---

## 🚀 快速开始

### 方式一：Docker 部署（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/t59688/arboris-novel.git
cd arboris-novel

# 2. 复制并编辑配置文件
cp .env.example .env

# 3. 编辑 .env 文件，填写必要配置
#    - SECRET_KEY: 随机字符串，用于 JWT 加密
#    - OPENAI_API_KEY: 你的 LLM API Key
#    - ADMIN_DEFAULT_PASSWORD: 管理员密码

# 4. 启动服务
docker compose up -d

# 🎉 完成！访问 http://localhost 即可使用
```

### 方式二：使用 MySQL 数据库

```bash
# 修改 .env 中的 DB_PROVIDER=mysql
# 然后启动（自动包含 MySQL 容器）
DB_PROVIDER=mysql docker compose --profile mysql up -d
```

### 方式三：连接已有 MySQL 服务器

```bash
# 在 .env 中配置你的数据库连接信息
# DB_PROVIDER=mysql
# MYSQL_HOST=your-mysql-host
# MYSQL_USER=your-username
# MYSQL_PASSWORD=your-password
# MYSQL_DATABASE=arboris

docker compose up -d
```

---

## ⚙️ 配置说明

### 环境变量速查表

| 配置项 | 必填 | 说明 |
|:---|:---:|:---|
| `SECRET_KEY` | ✅ | JWT 加密密钥，随机生成一串字符 |
| `OPENAI_API_KEY` | ✅ | LLM API Key（OpenAI 或兼容接口） |
| `OPENAI_API_BASE_URL` | ❌ | API 地址，默认 OpenAI 官方 |
| `OPENAI_MODEL_NAME` | ❌ | 模型名称，默认 `gpt-3.5-turbo` |
| `ADMIN_DEFAULT_PASSWORD` | ❌ | 管理员初始密码，**部署后务必修改** |
| `ALLOW_USER_REGISTRATION` | ❌ | 是否开放注册，默认 `false` |
| `SMTP_SERVER` | 📧 | 邮件服务器（开启注册时需要） |
| `SMTP_USERNAME` | 📧 | 邮件账号（开启注册时需要） |

> 💡 **数据存储**：默认使用 SQLite，数据存储在 Docker 卷中。如需映射到本地，可设置 `SQLITE_STORAGE_SOURCE=./storage`

完整配置请参考 `.env.example` 文件。

---

## 💻 开发指南

### 环境要求

- **Python** 3.10+（建议使用虚拟环境）
- **Node.js** 20+ 与 npm
- **Docker** & Docker Compose（可选，用于部署）

### 后端开发

```bash
cd backend

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Linux/macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端服务运行在 `http://127.0.0.1:8000`

### 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端开发服务器运行在 `http://127.0.0.1:5173`

### 构建部署

```bash
# 前端构建
cd frontend && npm run build

# Docker 一体化部署
docker compose -f deploy/docker-compose.yml up -d --build

# 推送镜像（可选）
cd deploy
docker build -t <registry>/arboris:<tag> .
docker push <registry>/arboris:<tag>
```

---

## ❓ 常见问题

<details>
<summary><b>🔰 基础问题</b></summary>

**Q: 我不会 Docker 怎么办？**
A: 安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/)（Windows/Mac）或 Docker Engine（Linux），然后复制粘贴上面的命令即可。

**Q: 我的 API Key 会不会泄露？**
A: 不会。密钥存储在服务器的 `.env` 文件中，不会暴露给前端或用户。

**Q: 可以用其它大模型吗？**
A: 只要提供 OpenAI 兼容接口，都可以使用。修改 `OPENAI_API_BASE_URL` 即可。

</details>

<details>
<summary><b>⚠️ 生成相关问题</b></summary>

**Q: 提示"未配置默认 LLM API Key"？**
A: 检查 `.env` 文件中的 `OPENAI_API_KEY` 是否正确配置。个人用户也可在个人设置中配置自定义 API Key。

**Q: 提示"今日请求次数已达上限"？**
A: 系统可能设置了每日请求限制。可以：
- 等到明天再试
- 在个人设置中配置自己的 API Key（不受系统配额限制）
- 联系管理员调整配额

**Q: 提示"AI 服务响应超时"？**
A: 网络或 API 服务问题。请检查：
- 网络连接是否正常
- `OPENAI_API_BASE_URL` 配置是否正确
- 稍后重试

**Q: 提示"AI 返回的内容格式不正确"？** ⭐ **常见问题**
A: AI 返回内容无法解析为有效 JSON。解决方案：
- 切换到能力更强的模型
- 使用支持 structured output 的模型
- 多试几次（有时是偶发问题）

**Q: 生成的内容质量不理想？**
A: 建议：
- 完善角色、地点、派系等设定信息
- 优化章节纲要，提供更详细的指引
- 使用多版本生成功能，挑选最佳版本
- 尝试不同的模型

</details>

<details>
<summary><b>🛠️ 配置相关问题</b></summary>

**Q: 提示"蓝图中未找到对应章节纲要"？**
A: 在生成章节内容前，需要先在蓝图（大纲）中创建对应章节的纲要。

**Q: 提示"未配置摘要提示词"？**
A: 管理员需在后台配置名为 `extraction` 的提示词模板。

</details>

---

## 🤝 参与贡献

如果你觉得这个项目有意思，欢迎参与：

- ⭐ **Star** —— 给项目点个星
- 🐛 **Issue** —— 报告 Bug 或提出建议
- 💻 **PR** —— 贡献代码（我们认真对待每一个 PR）
- 💬 **讨论** —— 加入社区交流

---

## 📄 License

本项目基于 [MIT License](LICENSE) 开源。

---

<div align="center">

**如果你用 Arboris 写出了什么有趣的东西，记得告诉我们！**

祝你写作顺利，故事精彩 ✨

[![Star History Chart](https://api.star-history.com/svg?repos=t59688/arboris-novel&type=Date)](https://star-history.com/#t59688/arboris-novel&Date)

</div>
