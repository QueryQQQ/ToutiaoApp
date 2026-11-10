from typing import Any, cast

from fastapi import Depends
from sqlalchemy import CursorResult, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.favorite import Favorite
from models.news import News
from models.users import User
from utils.auth import get_current_user


# 检查收藏状态：当前用户收费收藏了这一条新闻
async def is_news_favorite(
        db: AsyncSession,
        user_id: int,
        news_id: int,
)-> bool:
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


# 移除新闻收藏
async def remove_news_favorite(
        db: AsyncSession,
        user_id: int,
        news_id: int,
):
    stmt = delete(Favorite).where(
        Favorite.user_id == user_id,
        Favorite.news_id == news_id,
    )
    result = await db.execute(stmt)
    await db.commit()
    # execute 的标注是 Result，rowcount 只在子类 CursorResult 上，用 cast 让类型检查器认可；
    # MySQL 不支持 DELETE ... RETURNING，所以删除条数只能靠 rowcount
    return cast(CursorResult[Any], result).rowcount > 0


# 获取收藏列表: 获取的是某个用户的收藏列表 + 分页功能
async def get_favorite_list(
        db: AsyncSession,
        current_user: User = Depends(get_current_user),
        page: int = 1,
        page_size: int = 10,
):
        # 总量 + 收藏的新闻列表
        count_query = (
            select(func.count())
            .select_from(Favorite)
            .where(Favorite.user_id == current_user.id)
        )
        count_result = await db.execute(count_query)
        total = count_result.scalar_one()

       
        # 获取收藏列表 - 联表查询 join()+ 收藏时间排序 + 分页
        # select(查询主体模型类,字段别名).join(联合查询的模型类,联合查询的条件).where().order_by().offset().limit()
        # 别名命名规则:目标表.created_at.label("别名")
        offset = (page - 1) * page_size
        query = (
            select(
                Favorite.created_at.label("favorite_time"),
                Favorite.id.label("favorite_id"),
                News.id.label("news_id"),
                News.title.label("title"),
                News.description.label("description"),
                News.image.label("image"),
                News.author.label("author"),
                News.publish_time.label("publish_time"),
            )
            .join(News, Favorite.news_id == News.id)
            .where(Favorite.user_id == current_user.id)
            .order_by(Favorite.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        # 得到结果: 列表里面包着元组
        [
             
        ]
        