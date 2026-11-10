from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# 三步
# 1.创建异步引擎（数据库引擎）
# 方言+驱动://用户:密码@主机:端口/库名?参数
ASYNC_DATABASE_URL = "mysql+aiomysql://root:123456@localhost:3306/news_app?charset=utf8mb4"
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
