from typing import Any, cast

from sqlalchemy import CursorResult, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.favorite import Favorite
from models.news import News


# 检查收藏状态：当前用户收费收藏了这一条新闻
async def is_news_favorite(
        db: AsyncSession,
        user_id: int,
        news_id: int,
)-> bool:
    query = select(Favorite).where(Favorite.user_id == user_id, Favorite.news_id == news_id)
    result = await db.execute(query)
    # 我们要的就是布尔值，is not None调整输出为bool，无对象->返回None->变为False，有对象->返回Favorite对象->变为True
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
        user_id: int,
        page: int = 1,
        page_size: int = 10,
):
        # 总量 + 收藏的新闻列表
        count_query = (
            select(func.count())
            .where(Favorite.user_id == user_id)
        )
        count_result = await db.execute(count_query)
        total = count_result.scalar_one()

        # 获取收藏列表 - 联表查询 join()+ 收藏时间排序 + 分页

        # 联表查询
        # 原因:收藏表里面没有新闻标题,放在news表里
        # select(查询主体模型类,字段别名).join(联合查询的模型类,联合查询的条件).where().order_by().offset().limit()

        # 别名
        # 原因: 联表后列名会重复
        # favorite.id 和 news.id 都叫 id，favorite.created_at 和 news.created_at 都叫 created_at
        # 别名命名规则:目标表.created_at.label("别名")
        offset = (page - 1) * page_size
        query = (select(News, Favorite.created_at.label("favorite_time"), Favorite.id.label("favorite_id"))# 漏写News表导致后面报错excepted 3 but received 2
                .join(Favorite, Favorite.news_id == News.id)
                .where(Favorite.user_id == user_id)
                .order_by(Favorite.created_at.desc())
                .offset(offset).limit(page_size)
                 )
        result = await db.execute(query)
        rows = result.all()
        return rows, total
        # 得到结果: 列表里面包着元组
        # [
        #   (新闻对象, 收藏时间, 收藏id)
        # ]
        

# 清空收藏列表
async def remove_all_favorites(
        db: AsyncSession,
        user_id: int,
):
    stmt = delete(Favorite).where(Favorite.user_id == user_id)
    result = await db.execute(stmt)
    await db.commit()

    # cast就是类型标签修改器，把变量 result 的类型标签从 Result 改为 CursorResult，因为Result类没有定义Rowcount而CursorResult有，所以静态检查其会对Result类报错但CursorResult类不会
    return cast(CursorResult[Any], result).rowcount or 0 # 有具体数量就返回数量，否则返回0 cursor光标，游标
   