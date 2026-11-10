from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.functions import user

from crud import news
from models.favorite import Favorite


# 检查收藏状态：当前用户收费收藏了这一条新闻
async def is_news_favorite(
        db: AsyncSession,
        user_id: int,
        news_id: int,
):
    query = select(Favorite).where(Favorite.user_id == user_id, Favorite.news_id == news_id)
    result = await db.execute(query)
    # 我们要的就是布尔值，is not None调整bool，使得在if处有收藏记录就返回None，没收藏记录就返回True执行
    return result.scalar_one_or_none() is not None


# 添加新闻收藏
async def add_news_favorite(
        db: AsyncSession,
        user_id: int,
        news_id: int,
):
    favorite = Favorite(user_id = user_id, news_id = news_id) # 创建ORM对象赋值，原因是换成ORM对象才能添加到数据库中
    db.add(favorite)
    await db.commit()
    await db.refresh(favorite)
    return favorite