# Study Agent

基于 RAG 与 LLM Tool Calling 的个性化课程复习智能体。

## 功能

- **课程管理**：创建课程，上传 PPT / PDF 资料，自动向量化索引
- **知识点提取**：AI 自动从资料中提取知识点，按章节归类
- **AI 对话**：类 ChatGPT 多会话对话，可检索课程资料、分析薄弱点、生成学习计划
- **提纲生成**：根据知识点自动生成结构化复习提纲
- **试卷考试**：AI 现场生成中国大学期末卷格式的试卷（选择题 + 简答题 + 判断题），在线答题并自动评分
- **薄弱点分析**：统计答题记录，定位薄弱知识点

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | Next.js 16 + React 19 + Tailwind CSS v4 + @base-ui/react |
| 后端 | FastAPI + SQLAlchemy (async) + SQLite |
| 向量库 | ChromaDB |
| LLM | OpenAI 兼容 API（支持 OpenAI / MO AI / DeepSeek 等） |

## 快速开始

### 前置要求

- **Python** >= 3.12
- **Node.js** >= 18
- **npm** >= 9

### 1. 克隆项目

```bash
git clone <repo-url>
cd agent_for_study
```

### 2. 配置后端

```bash
cd backend

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 下载本地 embedding 模型（~88MB，只需一次）
bash download_model.sh

# 配置 LLM API Key
cp .env.example .env
# 编辑 .env 填入你的 API Key 和 Base URL

cd ..
```

### 3. 配置前端

```bash
cd frontend

# 安装依赖
npm install

# 配置后端地址（默认本机 8000 端口无需修改）
cp .env.local.example .env.local

cd ..
```

### 4. 启动

```bash
# 终端 1 - 启动后端（端口 8000）
cd backend
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 终端 2 - 启动前端（端口 3000）
cd frontend
npm run dev
```

打开 http://localhost:3000 即可使用。

或使用启动脚本（Linux/Mac）：

```bash
./start.sh
```

> 如果使用 conda/mamba 环境，用 `--python /path/to/env/bin/python` 指定 Python 路径。

### 5. 在浏览器中配置 LLM

启动后打开 http://localhost:3000，点击左下角设置图标，填入 API Key 和 Base URL，或直接编辑 `backend/.env` 后重启后端。

## 项目结构

```
agent_for_study/
├── backend/
│   ├── app/
│   │   ├── agent/          # Agent 控制器 + 对话记忆
│   │   ├── models/         # SQLAlchemy 数据模型
│   │   ├── routers/        # FastAPI 路由
│   │   ├── schemas/        # Pydantic schema
│   │   ├── services/       # LLM / RAG / 业务逻辑
│   │   └── tools/          # Agent 工具函数
│   ├── .env.example        # 环境变量模板
│   ├── requirements.txt    # Python 依赖
│   └── chroma_data/        # ChromaDB 持久化目录（自动创建）
├── frontend/
│   ├── src/
│   │   ├── app/            # Next.js App Router 页面
│   │   ├── components/     # UI 组件
│   │   └── lib/            # API 客户端 & 工具函数
│   └── .env.local.example  # 前端环境变量模板
├── docs/
│   └── api-design.md       # API 设计文档
├── start.sh                # 一键启动脚本
├── .gitignore
└── README.md
```

## 配置参考

### 后端 .env

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `LLM_API_KEY` | LLM API 密钥（必填） | — |
| `LLM_BASE_URL` | LLM API 地址 | `https://api.openai.com/v1` |
| `LLM_MODEL` | 模型名称 | `gpt-4o-mini` |
| `EMBEDDING_MODEL` | Embedding 模型 | `text-embedding-3-small` |
| `DATABASE_URL` | 数据库连接 | `sqlite+aiosqlite:///./study_agent.db` |

### 前端 .env.local

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `NEXT_PUBLIC_API_URL` | 后端 API 地址 | `http://localhost:8000` |

## API 文档

启动后端后访问 http://localhost:8000/docs 查看 Swagger API 文档。

详细设计见 [docs/api-design.md](docs/api-design.md)。

## License

MIT
