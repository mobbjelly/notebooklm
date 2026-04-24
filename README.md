# KnowBase

中文个人知识管理助手，类 NotebookLM 的开源替代方案。上传文档，AI 帮你读懂、总结、关联。

## 功能特性

- **文档上传**：支持 PDF、Word、TXT、Markdown 及网页 URL
- **AI 问答**：基于 RAG 的对话式问答，回答附带原文引用溯源
- **自动摘要**：文档解析完成后自动生成结构化摘要与笔记
- **多文档关联分析**：跨文档发现共同主题、差异与知识盲点
- **匿名使用**：无需注册，浏览器本地生成 client_id 即可使用
- **笔记本分享**：生成只读分享链接
- **国产模型**：对接通义千问，数据不出境

## 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Python · FastAPI · SQLAlchemy · SQLite |
| AI | LangChain-core 1.x · ChromaDB · 通义千问 · DashScope Embeddings |
| 前端 | React 18 · TypeScript · Vite · Zustand |

## 目录结构

```
notebooklm/
├── backend/
│   ├── main.py              # FastAPI 应用入口
│   ├── core/                # 配置、数据库、依赖注入
│   ├── models/              # SQLAlchemy 数据模型
│   ├── schemas/             # Pydantic 请求/响应体
│   ├── api/routes/          # API 路由层
│   ├── services/            # 核心业务逻辑
│   │   ├── ingestion.py     # 文档摄入流水线
│   │   ├── rag.py           # RAG 检索问答
│   │   ├── summary.py       # 摘要与笔记生成
│   │   └── analysis.py      # 多文档关联分析
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/client.ts    # API 封装 + SSE 流式聊天
│   │   ├── store/           # clientId 生成 + Zustand 状态
│   │   ├── pages/           # HomePage · NotebookPage
│   │   └── components/      # DocumentPanel · ChatPanel · AnalysisPanel
│   ├── package.json
│   └── vite.config.ts
└── docs/
    └── PRD.md               # 产品需求文档
```

## 快速开始

### 前提条件

- Python 3.11+
- Node.js 18+
- [通义千问 API Key](https://dashscope.aliyun.com/)（免费额度可用）

### 后端启动

```bash
cd backend

# 1. 创建并激活虚拟环境
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 DASHSCOPE_API_KEY

# 4. 启动服务
uvicorn main:app --reload
# API 文档：http://localhost:8000/docs
```

### 前端启动

```bash
cd frontend

# 1. 安装依赖
npm install

# 2. 启动开发服务器
npm run dev
# 访问：http://localhost:3000
```

## 环境变量

在 `backend/.env` 中配置：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DASHSCOPE_API_KEY` | 通义千问 API Key（必填） | — |
| `LLM_MODEL` | LLM 模型名称 | `qwen-long` |
| `EMBEDDING_MODEL` | Embedding 模型 | `text-embedding-v3` |
| `DEBUG` | 开启调试模式 | `false` |
| `CHUNK_SIZE` | 文本分块大小（tokens） | `512` |
| `RAG_TOP_K` | 检索返回的最大文档块数 | `8` |
| `CHAT_DAILY_LIMIT` | 每用户每日问答次数限制 | `50` |

## API 文档

启动后端后访问 `http://localhost:8000/docs` 查看完整的 Swagger 文档。

核心端点：

```
GET    /api/notebooks                        # 笔记本列表
POST   /api/notebooks                        # 创建笔记本
POST   /api/notebooks/{id}/documents/upload  # 上传文件
POST   /api/notebooks/{id}/documents/url     # 添加 URL
POST   /api/notebooks/{id}/chat              # AI 对话（SSE 流式）
POST   /api/notebooks/{id}/analysis          # 触发关联分析
POST   /api/notebooks/{id}/share             # 生成分享链接
```

所有写操作需在请求头中携带 `X-Client-ID`（前端自动生成并存入 localStorage）。

## 数据存储

| 内容 | 位置 |
|------|------|
| 数据库 | `backend/data/knowbase.db` |
| 上传文件 | `backend/data/uploads/` |
| 向量索引 | `backend/data/chroma/` |

## 开发路线图

- [ ] 扫描版 PDF OCR 支持（PaddleOCR）
- [ ] 文档摘要页面（查看/编辑 AI 生成的笔记）
- [ ] 知识图谱可视化
- [ ] 音频播客生成
- [ ] 团队协作与权限管理
- [ ] 移动端适配
