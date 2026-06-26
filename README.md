# Creative Workshop

一个围绕“生图提示词优化”的小型创意车间 Demo。项目使用 FastAPI + MySQL，本地保存提示词偏好和生成历史，生图与提示词优化都通过云端 OpenAI-compatible API 调用。

## 功能

- 专题方向与视觉风格选择，内置多组中文 Positive / Negative 默认关键词
- “生成创意”：根据专题方向和视觉风格调用 LLM 生成中文创意句
- “优化提示词”：调用 LLM 优化 Positive / Negative 关键词
- 前端 API 配置面板：可在页面里编辑生图 API 与提示词优化 LLM 配置
- 支持手动编辑提示词，并按“专题方向 + 视觉风格”持久化到 MySQL
- 支持重置为默认提示词
- 调用云端 Images API 生成图片，支持 mock 模式本地占位图
- 输出台图片预览、滚轮缩放、拖动平移、下载当前图片
- 历史夹保留所有已生成图片，支持点击预览和下载
- 单屏前端界面，装配台 / 输出台 / 历史夹可拖动调整宽度

## 技术栈

- Python 3.12
- FastAPI
- SQLAlchemy
- PyMySQL
- MySQL
- 原生 HTML / CSS / JavaScript

## 目录结构

```text
app/
  main.py              # FastAPI 路由与页面渲染
  image_service.py     # 生图 API 调用与本地图片保存
  llm_service.py       # 创意生成与提示词优化
  prompt_service.py    # 专题 / 风格 / 默认提示词
  models.py            # MySQL 数据模型
  templates/index.html # 单页前端界面
scripts/init_db.py     # 初始化数据库表
start_demo.bat         # Windows 快速启动脚本
.env.example           # 环境变量示例
```

## 启动方式

1. 创建 MySQL 数据库：

```sql
CREATE DATABASE IF NOT EXISTS creative_workshop
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

2. 复制环境变量文件：

```powershell
copy .env.example .env
```

3. 修改 `.env`：

```env
DATABASE_URL=mysql+pymysql://root:你的MySQL密码@127.0.0.1:3306/creative_workshop?charset=utf8mb4
```

4. 一键启动：

```powershell
.\start_demo.bat
```

5. 打开页面：

```text
http://127.0.0.1:8000
```

健康检查：

```text
http://127.0.0.1:8000/api/health
```

## 手动启动

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
python scripts\init_db.py
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Docker 部署

Docker 方式会同时启动 FastAPI 和 MySQL，不依赖本机 Python 虚拟环境。

### 日常用 Docker Desktop 启动

首次已经用 `docker compose up -d --build` 构建成功后，以后日常使用可以直接在 Docker Desktop 里启动：

1. 打开 Docker Desktop
2. 找到项目里的两个容器：
   - `creative-workshop-mysql`
   - `creative-workshop-web`
3. 点击启动按钮
4. 浏览器打开：

```text
http://127.0.0.1:8000
```

使用 Docker Desktop 启动时，不需要再在 VSCode 里运行 `start_demo.bat`。Docker 版和本地快速启动脚本二选一即可，不要同时启动，否则 `8000` 或 `3306` 端口可能冲突。

如果你改了 Python 依赖、`Dockerfile` 或 `docker-compose.yml`，再回到终端重新构建：

```powershell
docker compose up -d --build
```

1. 准备 `.env`：

```powershell
copy .env.example .env
```

2. 修改 `.env` 中的 Docker 配置：

```env
MYSQL_ROOT_PASSWORD=换成你的Docker数据库密码
MYSQL_DATABASE=creative_workshop
APP_PORT=8000
```

生图和 LLM Key 也继续写在 `.env` 里：

```env
IMAGE_PROVIDER=openai_compatible
IMAGE_API_KEY=你的生图APIKey
IMAGE_API_BASE_URL=https://api.unity2.ai/v1
IMAGE_MODEL=gpt-image-2

LLM_API_KEY=你的LLM_APIKey
LLM_API_BASE_URL=https://api.example.com/v1
LLM_MODEL=你的聊天模型
```

3. 构建并启动：

```powershell
docker compose up --build
```

后台启动：

```powershell
docker compose up -d --build
```

4. 打开：

```text
http://127.0.0.1:8000
```

5. 停止服务：

```powershell
docker compose down
```

清空 Docker 数据库和生成图片：

```powershell
docker compose down -v
```

Docker 持久化数据：

- `mysql_data`：MySQL 数据
- `generated_images`：云端返回 `b64_json` 时保存的本地图片

容器内应用会使用 `mysql` 作为数据库主机名，所以 Docker 模式不需要手动把 `DATABASE_URL` 改成容器地址，`docker-compose.yml` 会自动覆盖。

## 生图 API 配置

默认 `IMAGE_PROVIDER=mock`，用于不消耗额度地验证完整流程。

也可以在页面右上角点击 `API 配置` 直接编辑生图 API 和 LLM API。Key 不会明文回显，输入框留空保存时会保留当前 Key。

切换到云端 Images API：

```env
IMAGE_PROVIDER=openai_compatible
IMAGE_API_KEY=你的生图APIKey
IMAGE_API_BASE_URL=https://api.unity2.ai/v1
IMAGE_MODEL=gpt-image-2
```

程序会请求：

```text
POST {IMAGE_API_BASE_URL}/images/generations
```

当前发送的核心参数：

```json
{
  "model": "gpt-image-2",
  "prompt": "你的创意 + positive 关键词 + negative 避免项",
  "size": "1024x1536"
}
```

尺寸会根据专题方向的比例自动映射，例如 `3:4` 使用 `1024x1536`，`16:9` 使用 `1536x864`。

## LLM 配置

“生成创意”和“优化提示词”共用 OpenAI-compatible Chat Completions API：

这些配置同样可以在页面右上角的 `API 配置` 面板中修改。

```env
LLM_API_KEY=你的LLM_APIKey
LLM_API_BASE_URL=https://api.example.com/v1
LLM_MODEL=你的聊天模型
```

程序会请求：

```text
POST {LLM_API_BASE_URL}/chat/completions
```

## 数据存储

本 Demo 不做登录注册，数据都存在本地 MySQL：

- `generations`：生成历史、图片地址、提示词记录
- `prompt_preferences`：用户手动修改或 AI 优化后的提示词偏好

如果云端返回 `b64_json`，图片会保存到：

```text
app/static/generated/
```

如果云端返回 `url`，历史记录会保存远程图片地址，下载时由后端转发下载。

## GitHub 安全检查

上传前请确认：

- 不要提交 `.env`
- 不要提交真实 API Key、Bearer Token、数据库密码
- 不要提交 `.venv/`
- 不要提交 `*.log`
- 不要提交 `app/static/generated/`
- `.env.example` 只能放占位符

当前 `.gitignore` 已覆盖这些本地文件：

```text
.env
.venv/
app/static/generated/
*.log
server.log
server.err.log
__pycache__/
*.pyc
```

可以用下面命令确认将要提交的文件：

```powershell
git status --short
git status --ignored --short
```

注意：`docker compose config` 会把 `.env` 中的环境变量展开到终端输出里，可能包含 API Key。不要把这段输出发布到 GitHub Issue、README 或截图里。

## 常见问题

如果一直是 mock 图：

- 检查 `.env` 是否设置 `IMAGE_PROVIDER=openai_compatible`
- 检查 `IMAGE_API_KEY` 和 `IMAGE_API_BASE_URL`
- 修改 `.env` 后重启服务

如果生图等待很久：

- 部分中转站同步生图可能需要 1-3 分钟
- 前端会显示等待秒数，超过 8 分钟会停止等待
- 可查看本地 `image_api.log` 排查 HTTP 状态和响应格式

如果 LLM 功能报错：

- 检查 `LLM_API_BASE_URL` 是否包含 `/v1`
- 检查模型名是否支持 `/chat/completions`
- 检查 Key 是否可用
