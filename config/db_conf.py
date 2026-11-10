import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# 读取项目根目录下的 .env（文件不存在时静默跳过，不影响本地默认值启动）
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# 三步
# 1.创建异步引擎（数据库引擎）
# 方言+驱动://用户:密码@主机:端口/库名?参数
# 连接串优先从环境变量 DATABASE_URL 读取，换数据库/换机器/上线都不用改代码；
# 没配环境变量时用下面的本地开发默认值兜底（想改密码就写进 .env，不要改这里）
DEFAULT_DATABASE_URL = "mysql+aiomysql://root:123456@localhost:3306/news_app?charset=utf8mb4"
ASYNC_DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
# 创建异步引擎
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,         # 打印SQL日志：学习期可临时改 True 看SQL，平时关掉，否则前端每发一次请求终端就刷十几行
    pool_size=10,       # 设置连接池中保持的持久连接数
    max_overflow=20     # 设置连接池允许创建的额外连接数
)

# 2.创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 3.依赖项，用于获取数据库会话
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
