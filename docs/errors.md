# 错误日志 · ToutiaoApp

> 规则：一个错一条；只记"会让你再犯"的错；当场写，单条不超过 10 分钟。

| # | 日期 | 一句话 | 标签 |
|---|---|---|---|
| 001 | 2026-11-04 | ORM 字段名拼错，与真实表列名不一致导致接口 500 | sqlalchemy / schema |
| 002 | 2026-11-04 | 同一个模型类在两个文件重复定义（潜伏） | 架构 / 隐患 |
| 003 | 2026-11-04 | `News` 类写进了 `models/new.py`，import 报 unknown symbol | import / 文件组织 |
| 004 | 2026-11-04 | count 的 where 加错了对象；自动导入选错模块混入 tkinter | sqlalchemy / 自动导入 |
| 005 | 2026-11-04 | `is not awaitable` 报警但接口正常，是编辑器缓存 + 同名 import 占位 | 静态检查 / import |
| 006 | 2026-11-06 | passlib 与 bcrypt 5.0 不兼容，注册接口 500 且一条都不入库 | 依赖 / 密码哈希 |
| 007 | 2026-11-06 | 前端提示注册失败，但用户已入库：模型继承多一列 + 提交过早 | sqlalchemy / 事务 |

---

## 模板（复制这一段用）

```
### NNN · 一句话标题

- **日期**：
- **标签**：
- **现象**：1-3 行，只留可搜索的报错关键片段
- **复现**：哪条命令 / 哪个请求 / 哪次点击
- **根因**：具体到 文件:行号，一句话讲清机制
- **修复**：改了什么，diff 级别
- **为什么没被提前发现**：编译器 / 类型检查 / 启动 / 首次运行，卡在哪一层
- **同类风险**：还有哪里可能犯同样的错
- **下次怎么防**：可执行的具体动作，不是"要细心"
```

---

### 001 · ORM 字段名拼错，SQL 查了一个不存在的列

- **日期**：2026-11-04
- **标签**：sqlalchemy / schema
- **现象**：`GET /api/news/categories` 返回 500，日志里
  `(1054, "Unknown column 'news_category.createed_at' in 'field list'")`
- **复现**：启动 `uvicorn main:app`，请求该接口即必现
- **根因**：`models/news.py` 第 8 行属性名写成了 `createed_at`（多一个 e），
  而 MySQL 里 `news_category` 表的列是 `created_at`。SQLAlchemy 按属性名生成列名，
  于是 SQL 直接查了一个不存在的列。
- **修复**：第 8 行改为 `created_at`；顺带把 `updated_at` 注释改成"更新时间"、
  `sort_order` 注释改成"排序"。
- **为什么没被提前发现**：语法合法 → 类型合法（`Mapped[datetime]` 对任何属性名都成立）
  → 启动不连库 → 只有第一条 SQL 才会撞上。属于"代码与外部系统契约不一致"，
  静态检查天然看不见。
- **同类风险**：以后 `news`、`user` 等表的模型同样靠手敲对齐，随时可能再分叉；
  特别是 `sort_order` / `updated_at` 这种长名字。
- **下次怎么防**：
  1. VSCode 装 Code Spell Checker，`createed` 会当场标红；
  2. 新模型写完先跑一次真实查询（哪怕 `select(Model).limit(1)`），别等接口写完才测；
  3. 接 Alembic，`alembic revision --autogenerate` 专门比对"模型 vs 真实库"。

---

### 002 · 同名模型类在两个文件重复定义（潜伏未爆）

- **日期**：2026-11-04
- **标签**：架构 / 隐患
- **现象**：暂未报错，但一旦被 import 就会抛
  `InvalidRequestError: Table 'news_category' is already defined for this MetaData instance`
- **复现**：`python -c "import models.new"`
- **根因**：`models/new.py` 与 `models/news.py` 各写了一份 `Base(DeclarativeBase)`
  和 `Category(Base)`，`__tablename__` 都是 `news_category`。
  而 `crud/news.py` 只 import 了 `models.news`，所以一直没触发。
- **修复**：`models/new.py` 重命名为 `models/new.py.bak`，原件已备份到 `_backup_20261104/`。
- **为什么没被提前发现**：死代码无人 import，Python 不会检查没被导入的模块；
  两个文件内容看起来"都一样"，肉眼看不出问题。
- **同类风险**：
  - 复制文件改名后忘了删旧文件；
  - 出现多个 `DeclarativeBase` 实例会导致 metadata 分裂，
    新表 `create_all()` 建不出来（这个坑更难查）。
- **下次怎么防**：
  1. 全项目只保留**一个** `Base`，放 `models/base.py` 或 `models/__init__.py`；
  2. 模型文件严格按表名命名（`news.py` 对应 `news` 表），杜绝 `new.py` 这种；
  3. 想留旧版本用 git，不要在目录里堆 `xxx_copy.py`。

---

### 003 · 模型类写进了另一个文件，import 时找不到符号

- **日期**：2026-11-04
- **标签**：import / 文件组织
- **现象**：VSCode 在 `crud/news.py:3` 标黄
  `"News" is unknown import symbol`；真跑起来是
  `ImportError: cannot import name 'News' from 'models.news'`
- **复现**：`python -c "from models.news import Category, News"`
- **根因**：`class News(Base)` 被写进了 `models/new.py`（漏一个 s 的旧文件），
  而 `models/news.py` 里只有 `Base` 和 `Category`，`crud/news.py` 又只从 `models.news` 导入
  → **定义在 A 文件，引用在 B 文件**。
  顺带 `models/new.py` 本身还是语法错误文件：
  `Index(name='fk_news_category_idx', *expressions: 'category_id')` 不是合法 Python
  （`*expressions: 'category_id'` 是类型注解的写法，不能出现在函数调用里），而且 `Index` 根本没导入。
- **修复**：
  1. 把 `News` 类整体迁到 `models/news.py`，补 `ForeignKey` / `Text` / `Index` / `Optional` 导入；
  2. 索引改成合法写法 `Index("fk_news_category_idx", "category_id")`、`Index("idx_publish_time", "publish_time")`；
  3. `models/new.py` 移到 `_backup_20261104/`，`models/` 下只剩 `news.py`。
- **为什么没被提前发现**：`new.py` 和 `news.py` 只差一个 s，编辑器标签页上几乎看不出；
  002 那条本来已经把它改成 `.bak` 了，后来新建模型时又顺手建了 `new.py`。
- **同类风险**：
  - `models/` / `crud/` / `schemas/` / `routers/` 四层同名文件全靠手敲，`news` / `new` / `News` 三种写法极易错位；
  - 模型类型和真库不完全一致：库里 `id`、`category_id`、`views` 是 `int unsigned`，
    `publish_time` 是 `timestamp`，模型写的是 `Integer` / `DateTime`。
    只读查询不受影响，但一旦跑 `create_all()` 会造出与设计文档不同的表。
- **下次怎么防**：
  1. 看到 unknown import symbol，先 **Ctrl+点击跳到导入源文件** 看有没有这个类，别在原文件里猜着改；
  2. 加完一个模型立刻 `python -c "from models.news import News"`，5 秒验证，别等接口写完；
  3. 目录里不堆 `xxx.bak` / `xxx_copy`，旧版本交给 git。

---

### 004 · count 的 where 加错对象 + 自动导入选错模块

- **日期**：2026-11-04
- **标签**：sqlalchemy / 自动导入
- **现象**：`AttributeError: Neither 'count' object nor 'Comparator' object has an attribute 'where'`；
  另外终端被 sqlalchemy 的 SQL 日志刷屏（echo=True + 前端每次请求打印十几行）
- **复现**：请求 `GET /api/news/list?categoryId=1`
- **根因**：
  1. `crud/news.py:29` 写成 `select(func.count(News.id).where(...))` —— `.where` 链在了
     `func.count()` 上。`func.count(...)` 只是计数表达式，没有 where 方法；
     `select(...)` 才是查询语句。正确：`select(func.count(News.id)).where(...)`
  2. 文件顶部混入了 `from tkinter import N, NE` 和 `from unicodedata import category` ——
     用 Ctrl+. 自动导入时选错了候选模块（Pylance 扫全工作区，同名的会列出多个）
  3. `config/db_conf.py` 的 `echo=True` 在前端联调时就是刷屏机
- **修复**：括号移到 count 外面；删掉两条错误 import；echo 改 False（要看 SQL 再临时开）
- **为什么没被提前发现**：AttributeError 是运行时错误，语法检查和类型检查都不报；
  错误 import 只要用不到 `N`/`category` 就不报错，属于潜伏垃圾
- **同类风险**：自动导入同名候选（news.py 有 3 个同名模块）；链式调用时括号位置写错
- **下次怎么防**：
  1. Ctrl+. 出现候选时，看清完整模块路径再回车；
  2. 提交前扫一眼文件顶部 import 区，不认识的模块名（tkinter/unicodedata 这种标准库）
     出现在业务代码里就是红灯；
  3. 记住链式调用规则：`.where()/.offset()/.limit()` 都是 select 的方法，
     `func.count()` 里只放要计数的列。

---

### 005 · `is not awaitable` 报警但接口正常：编辑器缓存 + 同名 import 占位

- **日期**：2026-11-04
- **标签**：静态检查 / import
- **现象**：Pylance 在 `routers/news.py` 的 `await news.get_categories(...)` 上报三条：

  ```
  "Sequence[Category]" is not awaitable
  "Sequence[Category]" is incompatible with protocol "Awaitable[_T_co]"
  "__await__" is not present
  ```

  但 `GET /api/news/categories` 实测 **HTTP 200**，数据正常；
  `inspect.iscoroutinefunction(crud.news.get_categories)` 返回 **True**。

- **复现**：改完 `routers/news.py` 的详情接口后突然出现，重启服务仍然只报警不影响运行
- **根因**：**分两层，必须分开看**
  1. **真正能修的那层**：`crud/news.py:3` 有一句多余的 `from models import news`。
     它在本模块内把 `news` 这个名字绑定成了 `models.news` 模块（跟下层自己的模块名同名）。
     本模块第 4 行已经 `from models.news import Category, News` 拿到需要的符号，
     这句完全没用，却给静态分析留了一个**同名不同物**的占位，
     让 Pylance 解析 `news.get_categories` 时认错了对象、把返回类型推成 `Sequence[Category]`。
  2. **假的那层**：Pylance 手里的代码快照比磁盘旧（之前还发生过一次
     编辑器用未保存内容把我改的 `alias="id"` 覆盖回去）。症状是"重启服务没用、改代码也不消"。

- **修复**：
  1. 删除 `crud/news.py:3` 的 `from models import news`（保留第 4 行的 `Category, News`）；
  2. `Ctrl+Shift+P` → `Python: Restart Language Server`（还不行就 `Developer: Reload Window`）；
  3. 回归测试三个接口，全绿：

     ```
     /api/news/categories                          → 200
     /api/news/list?categoryId=1&page=1&pageSize=3 → 200
     /api/news/detail?id=1                         → 200
     ```

- **为什么没被提前发现**：
  - 这句错 import **运行时完全无害**（名字没被用到），只有静态分析受影响；
  - 报错信息（`is not awaitable`）指向的是**调用方**（routers），而病根在**被调方文件顶部**（crud），
    顺着报错行改永远改不对；
  - 编辑器缓存不同步这件事本身没有任何提示，只能靠"报警但实测正常"这个矛盾识别出来。

- **同类风险**：
  - `from models import news` / `from crud import news` / `import news` 三种写法混用，
    `news` 这个名字在项目里同时是"模块名"和"业务对象名"；
  - 任何 `from X import Y` 里 `Y` 与本模块名同名的写法，都会制造这种歧义；
  - 详情接口里把查询结果取名 `news`，会覆盖 `from crud import news` 的模块名，
    后面整个函数都调不到 crud 了（这次没踩，但离得很近）。

- **下次怎么防**：
  1. **遇到"报警但接口 200"先信实测**：`curl -o /dev/null -w "%{http_code}"` 跑一次，
     确认是运行时问题还是静态分析问题，别顺着假报警改代码；
  2. import 语句只写**需要的符号**：`from models.news import Category, News`，
     不要 `from models import news` 这种"整包导入"，尤其当模块名和业务名撞车时；
  3. 业务变量别用模块名：`news_detail` / `news_item`，不要 `news`；
  4. 改完文件先 `Ctrl+S`，再让工具改；工具改完你在编辑器里 `Revert File` 重载，
     避免"未保存缓冲区覆盖磁盘"（这条已经踩过两次了）。

---

### 006 · passlib 与 bcrypt 5.0 不兼容，注册接口 500 且一条都不入库

- **日期**：2026-11-06
- **标签**：依赖 / 密码哈希
- **现象**：Swagger 里填用户名密码调 `POST /api/user/register`，返回
  **500 Internal Server Error**，耗时仅 0.056s（说明连数据库都没摸到），
  `user` 表里没有任何新记录。堆栈最内层：

  ```
  File "...\passlib\handlers\bcrypt.py", line 655, in _calc_checksum
      hash = _bcrypt.hashpw(secret, config)
  ValueError: password cannot be longer than 72 bytes, truncate manually if necessary
  ```

  调用链：`_load_backend_mixin` → `_finalize_backend_mixin` → `detect_wrap_bug`
  → `verify` → `_calc_checksum`。

- **复现**：

  ```bash
  curl -X POST http://127.0.0.1:8000/api/user/register \
    -H "Content-Type: application/json" \
    -d '{"username":"test","password":"abc123"}'
  ```

  必现，且**与输入的密码长短无关**——6 个字符照样崩。

- **根因**：`passlib 1.7.4` + `bcrypt 5.0.0` 的版本不兼容，不是业务代码写错。
  passlib 第一次初始化 bcrypt 后端时会做一次能力探测：`bcrypt.py:380` 的
  `detect_wrap_bug()` 拿一个**超过 72 字节的假密码**去调 `bcrypt.hashpw()`，
  用来验证老版本 bcrypt 会不会静默截断。而 bcrypt ≥4.1 改成了直接
  `raise ValueError`，探测这一步就炸 → 后端初始化失败 → 之后
  `CryptContext.hash()` **一次都调不通**。
  异常在 `crud/users.py:20` 的 `get_hash_password()` 里抛出，而 `db.add(user)`
  在第 22 行，**SQL 根本没发出去**。所以症状是"输不进数据库"，而不是"写进去的内容不对"。

- **修复**：按官方文档现在的方向迁到 pwdlib（Argon2）：
  1. `pip install "pwdlib[argon2]"`，再 `pip uninstall passlib`；
  2. 重写 `utils/security.py`：`PasswordHash((Argon2Hasher(), BcryptHasher()))` ——
     第一个负责给新密码算 Argon2id，第二个负责兼容库里 `admin` 那条 `$2b$12$...`
     老 bcrypt 哈希，**不用重置已有账号**；同时补上 `verify_password()`
     （原来只有加密没有校验，写登录接口时必然缺这个）；
  3. `crud/users.py` 一行没动（`get_hash_password` 签名不变）。

- **修复后验证**：注册返回 200；落库哈希 `$argon2id$v=19$m=65536,t=3,p=4$...`（97 字节，
  `varchar(255)` 够用）；中文密码正常（Argon2 没有 72 字节上限）；
  `admin` 老哈希仍被识别（喂错密码返回 False 而不是抛异常）。
  诊断用的临时行已删除，`user` 表自增 id 因此跳号（1 → 4），无影响。

- **为什么没被提前发现**：
  - 两个库各自都能装、都能 import，`pip list` 看不出任何冲突；
  - 项目没有 `requirements.txt`，`pyproject.toml` 也只有 ruff 配置、没有 `dependencies` 段，
    **没人知道当前装的是 passlib 1.7.4 + bcrypt 5.0.0 这个组合**；
  - 报错文本 "password cannot be longer than 72 bytes" 指的是**探测用的假密码**，
    不是用户输入的密码，极具误导性，很容易跑去改密码长度校验；
  - 启动、import、类型检查全部通过，只在**第一次真正加密**时才炸。

- **同类风险**：
  - 所有"停更老库 + 新依赖"的组合：passlib 最后一版 1.7.4 停在 2020-10-08；
    下一步写 JWT 时，教程里常用的 `python-jose` 同样长期不维护，FastAPI 官方示例已换成 `PyJWT`；
  - 没有依赖锁 → 换机器、重建 venv、`pip install --upgrade` 都会原地复发；
  - 任何"库内部自检/探测"失败的异常，堆栈里都会出现业务代码完全不认识的文件名。

- **下次怎么防**：
  1. `pip freeze > requirements.txt` 把版本钉死，别靠记忆；✅ 2026-11-06 已生成，70 个包全锁
  2. 看堆栈先看**最内层**：如果出错行在 `site-packages/xxx/` 里、函数名
     （`detect_wrap_bug`、`_calc_checksum`）自己从没调用过，那就是依赖兼容问题，
     **别去改业务代码**；
  3. `utils/security.py` 底部留了 `if __name__ == "__main__"` 自测，
     装完/换完依赖先跑 `python -m utils.security`，5 秒出结果；
  4. 判断一个库还活不活：查 PyPI 的上传时间（passlib 停在 2020），比看教程推荐靠谱。

---

### 007 · 前端提示"注册失败"，但用户已经写进库了

- **日期**：2026-11-06
- **标签**：sqlalchemy / 事务
- **现象**：在页面上填用户名密码点注册，前端提示注册失败；但 `user` 表里能查到刚填的
  用户名，`user_token` 表里一条都没有。同样的操作走 Swagger 返回 500，堆栈：

  ```
  sqlalchemy.exc.OperationalError: (1054, "Unknown column 'user_token.updated_at' in 'field list'")
  [SQL: SELECT user_token.id, user_token.user_id, user_token.token,
               user_token.expires_at, user_token.created_at, user_token.updated_at
        FROM user_token WHERE user_token.user_id = %s]
  ```

  顺带排除过 CORS：`allow_origins=["*"]` + `allow_credentials=True` 时 Starlette 会回显
  请求 Origin，预检 `OPTIONS` 也返回 200，不是跨域导致前端拿不到响应。
- **复现**：`POST /api/user/register` 传任意新用户名即必现；之后查库就是"只有 user、
  没有 token"的半成品（当时留下的 `wenhao`、`wenhao1` 都是这样，0 条 token）。
- **根因**：两层，缺一不可
  - **A · 直接原因（造成 500）**：`models/news.py:11-24` 的 `Base` 声明了 `created_at` 和
    `updated_at`，本意是"所有表都带这两个时间列"。`User` 把两列都重写了一遍
    （`models/users.py:42-43`），和 `user` 表对得上；`UserToken` **只重写了 `created_at`**
    （`models/users.py:62`），`updated_at` 就从 `Base` 继承下来 → 模型比真实 `user_token`
    表多一列。`crud/users.py:40` 的 `select(UserToken)` 生成 SQL 时带上
    `user_token.updated_at` → 1054。失败点不在 INSERT，而在第一句 SELECT。
  - **B · 放大原因（造成"失败但已入库"）**：`crud/users.py:26` 的 `create_user` 在只建完
    用户时就 `await db.commit()` 了，事务被提前切断。后面 token 失败时，`get_db` 的
    `rollback()` 只能回滚尚未提交的部分，已经 commit 的用户行回不去 → 留下半成品。
- **修复**：
  1. 补列（不去改 `Base`——声明式继承里没法"删掉"父类的列，改了等于所有模型都要各自声明）：
     ```sql
     ALTER TABLE news_app.user_token
       ADD COLUMN updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
         ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间' AFTER created_at;
     ```
  2. `crud/users.py:26` `await db.commit()` → `await db.flush()`：flush 会拿到自增 id
     但不提交，交给 `get_db` 在请求结束时统一 commit。
  3. `create_token` 里的 `await db.commit()` 从 `else` 分支挪到 `if/else` 外面——
     原来"更新 token"那条路径从不提交，全靠 `get_db` 兜底才侥幸能跑。
  4. 半成品账号（`wenhao`、`wenhao1`、`shaowenhao`）尚未清理：只要还占着名字，重注册就会撞
     400"用户已存在"，而这个报错和真实原因毫无关系，极易把人带偏。清掉时注意先删
     `user_token` 再删 `user`（有外键）。

  验证：改完后注册返回 200，`user` 与 `user_token` 两表都有数据，token 与 `expires_at`
  正确；另写脚本故意让 token 步骤抛异常，确认用户行被一起回滚，不再留半成品。
- **为什么没被提前发现**：
  - `updated_at` 这一列**在模型文件里根本搜不到**，是继承来的；肉眼看 `UserToken` 的字段
    列表是"齐全"的，`User` 又刚好把两列都写了，形成对照错觉；
  - 语法、类型、启动、import 全部通过，只有真跑一条 SELECT 才炸；
  - 报错发生在"注册"这个动作里，病根却在 `user_token` 表的列上，两处相距很远；
  - 提前 commit 是"看起来更稳妥"的写法（直觉上 commit 越早越安全），实际把可回滚性丢了。
- **同类风险**：
  - 任何新表只要**没把 `Base` 的两个时间列都重写一遍**，A 就会重演；`news`、`news_category`
    现在是对的，是因为当时照抄了 `User` 的写法，不是因为有机制保证；
  - 任何"多步写入"的接口（注册、下单、发文章 + 附件、扣库存 + 记流水）只要中途 commit，
    就会重演 B；
  - 前端只收到 500，会以为"没成功"而重复提交 → 产生重复数据或撞"已存在"，把问题越盖越深。
- **下次怎么防**：
  1. 新模型写完先跑一次真实查询（`select(Model).limit(1)`），把"模型 vs 真实表"的差异逼出来，
     别等接口写完才测；
  2. 记住规则：**一个请求 = 一个事务**。CRUD 层只在"整件事做完"时 commit 一次，中途需要
     自增 id 用 `flush()`；commit 交给 `get_db` 这类请求级依赖；
  3. 加列走 Alembic，`alembic revision --autogenerate` 会直接列出"模型比库多/少了哪些列"，
     手写 `ALTER TABLE` 容易只改一半；
  4. 前端别只提示"注册失败"，把后端返回的 `detail` 打出来；看到 500 先查库确认到底写没写进去。

---

## 每周复盘（3 个问题，5 分钟）

1. 这周记的几条，**根因**能不能归成 2 类以内？归不进去说明还没想透。
2. 有没有哪条"下次怎么防"写了但没做？做了就打个 ✅。
3. 有没有哪条已经能删了（不会再犯）？删掉，日志要保持在能一眼看完的长度。
