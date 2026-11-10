# 头条资讯 ToutiaoApp

一个前后端分离的新闻资讯 Web 应用：后端提供新闻、用户、收藏的 RESTful 接口，前端是一个移动端风格的 Vue 3 单页应用。

项目以学习全栈开发为目标，代码保留了大量中文注释，踩过的坑记录在 [`docs/errors.md`](docs/errors.md)。

## 功能

| 模块 | 状态 | 说明 |
|---|---|---|
| 新闻分类 | ✅ | 分类列表，支持 `skip` / `limit` 分页 |
| 新闻列表 | ✅ | 按分类分页查询，返回 `total` 与 `hasMore` |
| 新闻详情 | ✅ | 详情 + 浏览量自增 + 同分类相关推荐 |
| 用户注册 / 登录 | ✅ | 密码 Argon2id 哈希，登录发放 token |
| 用户信息 | ✅ | 查询、修改资料、修改密码 |
| 新闻收藏 | 🚧 | 后端只有「检查状态」「添加收藏」，列表/取消/清空待补 |
| 浏览历史 | 🚧 | 前端页面与 Pinia store 已就绪，后端接口未实现（本地 localStorage 兜底） |
| AI 问答 | 🚧 | 前端流式对话页面已就绪，后端 `/api/ai/chat` 未实现 |

> 🚧 标记的功能在界面上点得到，但请求会失败——后端对应路由还没写。

## 技术栈

**后端**

| 组件 | 选型 |
|---|---|
| Web 框架 | FastAPI 0.162 |
| ORM | SQLAlchemy 2.1（`Mapped` / `mapped_column` 声明式写法） |
| 数据库 | MySQL 8 + `aiomysql` 异步驱动 |
| 数据校验 | Pydantic v2 |
| 密码哈希 | `pwdlib`（Argon2id）+ `bcrypt`（兼容库里已有的 `$2b$` 哈希） |
| 鉴权 | 数据库 token 表 + `Authorization` 请求头 |
| 代码检查 | Ruff（规则见 `pyproject.toml`） |

**前端**

| 组件 | 选型 |
|---|---|
| 框架 | Vue 3（Composition API，`<script setup>`） |
| 构建 | Vite 7 |
| 状态管理 | Pinia + `pinia-plugin-persistedstate` |
| 路由 | Vue Router 4 |
| UI 组件 | Vant 4 |
| 国际化 | vue-i18n 9（简体中文 / English） |
| HTTP | axios |
| 富文本 | marked + DOMPurify（渲染新闻正文 HTML，防 XSS） |

## 目录结构

```
ToutiaoApp/
├── main.py                  # FastAPI 入口：注册路由、CORS、异常处理器
├── config/
│   └── db_conf.py           # 异步引擎、会话工厂、get_db 依赖
├── models/                  # SQLAlchemy ORM 模型
│   ├── news.py              # Base、Category、News
│   ├── users.py             # User、UserToken
│   └── favorite.py          # Favorite
├── schemas/                 # Pydantic 请求/响应模型
├── crud/                    # 数据库读写封装（路由层不直接写 SQL）
├── routers/                 # 路由层
│   ├── news.py              # /api/news/*
│   ├── users.py             # /api/user/*
│   └── favorite.py          # /api/favorite/*
├── utils/
│   ├── auth.py              # get_current_user 依赖（解析 token 取用户）
│   ├── security.py          # 密码哈希与校验
│   ├── response.py          # 统一响应格式
│   └── exception_handlers.py
├── docs/errors.md           # 开发错误日志（踩坑记录）
├── requirements.txt         # 依赖锁定（含传递依赖）
├── pyproject.toml           # Ruff 配置
├── 启动开发环境.bat          # Windows 一键启动前后端
└── xwzx-news/               # 前端项目
    ├── src/views/           # 11 个页面：首页/分类/详情/收藏/历史/AI 问答/我的/资料/设置/登录/注册
    ├── src/store/           # Pinia：news / user / favorite / history / theme / language
    ├── src/config/api.js    # 后端地址配置（baseURL）
    └── src/i18n/            # 中英文语言包
```

## 快速开始

### 环境要求

- Python 3.11+（开发环境为 3.14）
- Node.js 18+
- MySQL 8.0+，已启动并监听 3306

### 1. 准备数据库

```sql
CREATE DATABASE news_app DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

项目**没有接入迁移工具**，表不会自动创建。首次运行前需要按 `models/` 里的定义手动建表（用 Navicat / DataGrip / 手写 DDL 都行），共 5 张：

| 表名 | 说明 |
|---|---|
| `news_category` | 新闻分类：`name` 唯一，`sort_order` 为排序字段（当前接口未按其排序） |
| `news` | 新闻：标题、简介、正文、封面、作者、`category_id` 外键、浏览量、发布时间 |
| `user` | 用户：用户名/手机号唯一、密码哈希、昵称、头像、性别、简介 |
| `user_token` | 登录令牌：`token` 唯一、`user_id` 外键、`expires_at` 过期时间 |
| `favorite` | 收藏：`(user_id, news_id)` 联合唯一，保证同一新闻只能收藏一次 |

也可以自行接入 Alembic 管理表结构。

### 2. 启动后端

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

配置数据库连接（不配也能跑，会用代码里的本地默认值）：

```bash
# Windows
copy .env.example .env
# macOS / Linux
cp .env.example .env
```

编辑 `.env`，把用户名密码改成自己的：

```
DATABASE_URL=mysql+aiomysql://root:你的密码@localhost:3306/news_app?charset=utf8mb4
```

启动：

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

- 接口文档：http://127.0.0.1:8000/docs
- 健康检查：http://127.0.0.1:8000/ → `{"message": "Hello World"}`

### 3. 启动前端

```bash
cd xwzx-news
npm install
npm run dev
```

打开 http://localhost:5173 即可。前端默认请求 `http://127.0.0.1:8000`，如后端换了端口，改 `xwzx-news/src/config/api.js` 里的 `baseURL`。

### 4. 一键启动（Windows）

双击根目录的 `启动开发环境.bat`，脚本会依次检查 8000 / 5173 端口、启动后端、必要时 `npm install`、再拉起 Vite 并打开浏览器。

> 脚本里的 `ROOT` 是硬编码的绝对路径，换机器后需要改成自己的项目路径。

## 环境变量

| 变量 | 必填 | 说明 |
|---|---|---|
| `DATABASE_URL` | 否 | 数据库连接串。优先级：环境变量 > `.env` 文件 > `config/db_conf.py` 里的本地默认值 |

`.env` 已写入 `.gitignore`，不会被提交；`.env.example` 是供他人复制的模板。

## API 一览

除注册、登录、新闻查询外，其余接口都需要请求头鉴权：

```
Authorization: <token>          # 或 "Bearer <token>"，两种都兼容
```

| 方法 | 路径 | 参数 | 说明 |
|---|---|---|---|
| GET | `/` | — | 健康检查 |
| GET | `/api/news/categories` | `skip`, `limit` | 分类列表 |
| GET | `/api/news/list` | `categoryId`, `page`, `pageSize` | 新闻列表（分页） |
| GET | `/api/news/detail` | `id` | 新闻详情 + 浏览量 +1 + 相关新闻 |
| POST | `/api/user/register` | body: `username`, `password` | 注册，返回 token 与用户信息 |
| POST | `/api/user/login` | body: `username`, `password` | 登录，返回 token 与用户信息 |
| GET | `/api/user/info` | — | 当前用户信息 |
| PUT | `/api/user/update` | body: `nickname` / `avatar` / `gender` / `bio` / `phone` | 修改资料 |
| PUT | `/api/user/password` | body: `old_password`, `new_password` | 修改密码 |
| GET | `/api/favorite/check` | `newsID` | 检查是否已收藏 |
| POST | `/api/favorite/add` | body: `news_id` | 添加收藏 |

响应统一为 `{ "code": 200, "message": "...", "data": ... }`。

## 已知限制

这些都是有意留下的「下一步」，不是 bug，但会影响使用体验：

1. **部分前端功能没有后端支撑**：`/api/history/*`、`/api/favorite/list|remove|clear`、`/api/ai/chat` 均未实现，相关页面请求会 404 / 报错。
2. **CORS 全开**：`main.py` 里 `allow_origins=["*"]` 同时开了 `allow_credentials`，生产环境必须改成具体的源。
3. **token 明文存库**：`user_token.token` 直接存原始值，泄露数据库即可冒充用户。生产环境应存哈希，并加定期清理过期 token 的任务。
4. **无数据库迁移**：表结构靠手动建，改字段容易漏。
5. **默认连接串含开发密码**：`config/db_conf.py` 里的 `root:123456` 只是本地开发兜底值，线上务必用 `DATABASE_URL` 覆盖。

## 开发笔记

[`docs/errors.md`](docs/errors.md) 按时间记录了开发过程中遇到的真实问题，包括：

- ORM 字段名拼错导致 SQL 查不存在的列
- 同名模型类在两个文件重复定义
- `passlib` 与 `bcrypt 5.0` 不兼容，注册接口 500
- 前端提示注册失败但用户已入库（事务与响应顺序问题）

排查同类问题时值得先翻一遍。
