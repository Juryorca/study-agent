# Study Agent — API & Design Reference

> 最后更新：2026-06-03

## API Endpoints

### 知识点 `/api/knowledge`

| Method | Path | Query Params | Body | Description |
|--------|------|-------------|------|-------------|
| GET | `/` | `course_id`, `importance`, `mastery`, `search` | — | 列表，支持按重要度/掌握度筛选，名称/描述模糊搜索 |
| POST | `/extract?course_id=` | `course_id` | `{document_id}` | SSE 流式提取知识点，分批处理，自动去重 |
| PATCH | `/{id}/mastery` | — | `{mastery: "unlearned"|"learning"|"mastered"}` | 更新掌握状态 |
| POST | `/outline?course_id=` | `course_id` | `{chapter?}` | 启动后台提纲生成，返回 `outline_id` |
| GET | `/outline?course_id=` | `course_id` | — | 列出课程所有提纲（含状态和内容） |
| DELETE | `/outline/{id}` | — | — | 删除提纲 |

### 课程 `/api/courses`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | 课程列表 |
| POST | `/` | 创建课程 |
| GET | `/{id}` | 课程详情 |
| DELETE | `/{id}` | 删除课程 |

### 资料 `/api/documents`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/?course_id=` | 资料列表 |
| POST | `/upload` (FormData) | 上传文件 |
| POST | `/{id}/reindex` | 重新向量化 |
| DELETE | `/{id}` | 删除资料 |

### 题目 `/api/questions`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/?course_id=&knowledge_point=&difficulty=&question_type=` | 题目列表 |
| POST | `/generate?course_id=` | 生成题目 |

### 答题 `/api/answers`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/submit?user_id=` | 提交单题 |
| POST | `/submit-batch?user_id=` | 批量提交 |

### 分析 `/api/analysis`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/weakness/{course_id}?user_id=` | 薄弱点分析 |

### Agent `/api/agent`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/chat` | SSE 流式 Agent 对话，支持 `session_id` 持久化 |
| POST | `/reset?user_id=` | 重置对话历史（兼容保留，建议用 sessions API） |

### 会话管理 `/api/agent` (NEW)

| Method | Path | Query Params | Body | Description |
|--------|------|-------------|------|-------------|
| GET | `/sessions` | `course_id` | — | 列出课程下所有会话（按 updated_at 倒序） |
| POST | `/sessions` | — | `{course_id, title?}` | 创建新会话 |
| DELETE | `/sessions/{id}` | — | — | 删除会话（级联删除消息） |
| GET | `/sessions/{id}/messages` | — | — | 加载会话历史消息 |

### 试卷管理 `/api/exams` (NEW)

| Method | Path | Query Params | Body | Description |
|--------|------|-------------|------|-------------|
| POST | `/generate` | `course_id` | `{title, config: {choice_count, short_answer_count, difficulty_distribution}}` | 生成试卷，从题库抽题+不足时 LLM 生成 |
| GET | `/` | `course_id`, `status` | — | 试卷列表 |
| GET | `/{id}` | — | — | 试卷详情含全部题目 |
| PUT | `/{id}/answer` | — | `{question_id, student_answer}` | 保存单题答案 |
| POST | `/{id}/save` | — | — | 保存为草稿 |
| POST | `/{id}/submit` | — | — | 提交评分（自动批改+写 answer_records） |
| DELETE | `/{id}` | — | — | 删除试卷（级联删除题目） |

### 设置 `/api/settings`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | 获取运行时配置 |
| POST | `/` | 更新运行时配置并重置 LLM client |

---

## KnowledgePoint Model

```
knowledge_points
├── id: str (UUID)
├── course_id: str (FK)
├── chapter: str        # 章节归类（LLM 提取时自动识别）
├── name: str           # 知识点名称
├── description: str    # 详细描述
├── importance: str     # high | medium | low
├── mastery: str        # unlearned | learning | mastered
├── source: str         # 来源页码/段落
├── document_id: str    # 来源文档
└── created_at: datetime
```

---

## ChatSession & ChatMessage Model

```
chat_sessions
├── id: str (UUID)
├── course_id: str (FK)
├── user_id: str       # "default"
├── title: str          # 自动从首条消息截取
├── created_at: datetime
└── updated_at: datetime

chat_messages
├── id: str (UUID)
├── session_id: str (FK → chat_sessions)
├── role: str           # user | assistant | tool
├── content: str
├── tool_name: str
├── tool_args: JSON
└── created_at: datetime
```

## ExamPaper & ExamQuestion Model

```
exam_papers
├── id: str (UUID)
├── course_id: str (FK)
├── title: str          # "新试卷" 或自定义
├── config: JSON        # {choice_count, short_answer_count, difficulty_distribution}
├── status: str         # draft | in_progress | submitted | graded
├── total_score: float
├── earned_score: float
├── created_at: datetime
└── updated_at: datetime

exam_questions
├── id: str (UUID)
├── paper_id: str (FK → exam_papers)
├── question_id: str (FK → questions)
├── question_type: str  # 反范式，防原题被删
├── stem: str           # 反范式
├── options: JSON       # 反范式
├── correct_answer: str # 反范式
├── explanation: str    # 反范式
├── max_score: float    # 选择 1.0 / 简答 10.0
├── order: int
├── student_answer: str
├── score: float
├── is_correct: bool
└── feedback: str
```

---

## Frontend Component Architecture

### 知识点页 `courses/[id]/knowledge/page.tsx`
```
KnowledgePage
├── StatsBar         — 掌握进度条 + 分类统计
├── Toolbar
│   ├── SearchInput  — 名称/描述搜索
│   ├── ImportanceFilter — 全部/重要/中等/一般（button group）
│   ├── MasteryFilter — 全部/未学习/学习中/已掌握（button group）
│   └── ViewToggle  — 列表 / 闪卡
├── ChapterFilter    — 全部章节 / 各章节快捷筛选（从数据派生）
├── GroupToggle     — 按章节分组 开关按钮
├── ListView         — 知识点卡片列表（支持分组/平铺两种模式）
│   └── Card         — 名称 + 描述 + 重要度badge + 掌握度badge + 快捷切换 + AI对话按钮
└── FlashcardView    — 闪卡复习模式 (components/knowledge/flashcard.tsx)
    └── Card         — 翻转动画：正面=名称, 背面=描述
    └── Actions      — 不熟/学习中/已掌握 + 前后翻页
```

### Agent 对话页 `agent/page.tsx` (NEW layout)
```
AgentChatPage
├── Sidebar (w-56, 仅课程上下文时显示)
│   ├── Header       — "对话历史" + 新建按钮
│   └── SessionList  — 会话条目（高亮当前、hover删除）
└── ChatArea
    ├── Header       — 标题 "AI 学习助手"
    ├── MessageList  — 消息气泡（assistant 用 ReactMarkdown 渲染）
    └── InputBar     — Textarea + 发送按钮
```
- URL 参数: `course_id` + `session_id` 可选
- 无 session_id 时发送消息自动创建会话
- 切换 session 时从 `/api/agent/sessions/{id}/messages` 加载历史

### 试卷页 `courses/[id]/exams/` (NEW)
```
ExamsPage (列表)
├── TabFilter    — 全部 / 已批改
├── PaperCard    — 标题 + 状态Badge + 分数 + 时间 + 删除
└── NewButton    — 跳转生成页

NewExamPage (配置生成)
├── TitleInput   — 试卷名称
├── ConfigForm   — 选择题/简答题数量
└── GenerateBtn  — 调用 /api/exams/generate

ExamTakePage (答题)
├── Header       — 标题 + 得分（已批改时）
├── Progress     — 答题进度条（未批改时）
├── ActionBar    — 保存草稿 + 提交评分（未批改时）
└── QuestionList
    └── QuestionCard
        ├── Stem + Badges（题型/分值/对错）
        ├── Options（单选点击） / Textarea（简答）
        └── Feedback（已批改时绿色/红色高亮）
```

### 数据流
- `mastery` 更新走乐观更新：先改 UI，再调 API，失败时回滚
- 列表筛选走服务端查询 (`importance`, `mastery`, `chapter`, `search` 均作为 query params)
- 闪卡模式从已加载的 `points` 数组读取，不额外请求
- 章节分组从已加载数据派生，纯客户端 groupBy，无需额外请求
- Agent 对话持久化：流式结束后后端自动保存消息到 DB，前端切换 session 时加载
- 试卷答案防抖自动保存：2s debounce → `PUT /api/exams/{id}/answer`

---

## Design Decisions
- **无 Select 组件**：筛选用 button group（pill 按钮组），更直观，减少依赖
- **乐观更新**：mastery 切换即时生效，失败才回滚，体验流畅
- **闪卡在同一页面**：不新建路由，`viewMode` state 切换，保持课程上下文
- **跳转 AI 对话**：通过 URL query `?course_id=&prompt=...` 传递课程上下文和预设提示
- **章节来自 LLM 但客户端分组**：LLM 返回 `chapter` 但存入 DB 后由前端按需分组，后端支持按 chapter 过滤
- **对话 DB 持久化**：不再依赖内存 `_agents` dict，消息流式结束后批量写入 DB，支持跨重启恢复
- **试卷反范式化**：ExamQuestion 保存 stem/options/answer 副本，防止原题被删后试卷内容丢失
- **@base-ui/react**：项目使用 @base-ui/react（非 Radix），用 `render` prop + `nativeButton={false}` 代替 `asChild`
- **Agent 路由**：侧边栏点击 `→ /agent` 无 course_id 时显示课程选择页；选中后 `→ /agent?course_id=xxx` 进入聊天界面；知识点跳转 `→ /agent?course_id=xxx&prompt=...` 预填提示词
- **Agent course_id 注入**：`AgentChatRequest.course_id` 传递到 `AgentController`，注入 system prompt，LLM 在调用工具时使用当前课程上下文
- **Tool 自动注册**：`app/tools/__init__.py` 必须显式导入所有工具模块，否则 `global_registry` 为空，LLM 无工具可调
- **commit 后重新查询**：包含 `onupdate=func.now()` 的列在 `commit()` 后可能触发 async greenlet 过期错误，必须在 commit 后重新 SELECT 再构建 Pydantic 响应
- **skipHistoryRef 避免清空消息**：首次发消息自动创建 session 时 `setActiveSessionId` 会触发 history-loading `useEffect` 把当前消息清掉。用 `skipHistoryRef` 在 auto-create 时跳过一次历史加载，之后切换 session 正常加载
- **courseId 稳定化**：`router.replace` 导致 Suspense 重挂载时 `searchParams` 短暂为空，`courseId` 变 `""` 导致闪现课程选择页。用 `courseIdRef` 缓存：一旦设值就不再清空
- **重复点击同一 session tab 是 no-op**：`switchToSession` 开头 `if (activeSessionId === sid) return;` 防止重复点击清空消息
- **ChatMessage.tool_args 类型**：DB 中存的是 OpenAI `tool_calls` 数组（list），Pydantic schema 需用 `Any` 而非 `dict`
- **试卷全部 LLM 现场生成**：不再从题库抽取，每张试卷通过 `generate_exam_questions()` 一次性生成所有题目，每次新鲜
- **简答题工科风格**：参考北大工科期末考卷，简答题 prompt 改为 "简述XXX的工作流程/步骤"、"说明XXX与YYY的区别和适用场景"、"分析XXX问题的原因及解决方案"，不出纯记忆性题目
- **Markdown 表格渲染**：ReactMarkdown 需配置 `remarkPlugins={[remarkGfm]}` 才能渲染 GFM 表格、删除线等
