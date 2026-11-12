

from datetime import datetime
from typing import Any, cast
from sqlalchemy import CursorResult, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.history import History
from models.news import News
from utils.response import success_response



# 检查浏览新闻状态：当前用户是否浏览了这一条新闻
async def check_news_history(
        db: AsyncSession,
        user_id: int,
        news_id: int,
)-> bool:
    query = select(History).where(History.user_id == user_id, History.news_id == news_id)
    result = await db.execute(query)
    # 我们要的就是布尔值，is not None调整输出为bool，无对象->返回None->变为False，有对象->返回Favorite对象->变为True
    return result.scalar_one_or_none() is not None


# 添加浏览历史
async def add_historys(
        db: AsyncSession,
        user_id: int,
        news_id: int,
):
    # 去重的判断必须放在这个函数里，不能靠 /check 那个接口：
    # 那是两次独立请求，双击/多标签页照样各插一行
    query = select(History).where(History.user_id == user_id, History.news_id == news_id)
    result = await db.execute(query)
    record = result.scalars().first()

    # 相较Favorite前端代码允许多次浏览,所以会出现重复新闻的情况,需要判断
    if record is not None:
        # 浏览过 -> 只刷新浏览时间，不新增行；列表按 view_time 倒序，它自然顶到第一条
        record.view_time = datetime.now()
    else:
        # 没浏览过 -> 才插入新行
        record = History(user_id=user_id, news_id=news_id, view_time=datetime.now())
        db.add(record)

    await db.commit()
    await db.refresh(record)
    return record



# 获取浏览历史列表 + 分页功能
async def get_history_list(
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 10,
):
        # 总量 + 收藏的新闻列表
        count_query = (
            select(func.count())
            .where(History.user_id == user_id)
        )
        count_result = await db.execute(count_query)
        total = count_result.scalar_one()

        # 获取收藏列表 - 联表查询 join()+ 收藏时间排序 + 分页

        # 联表查询
        # select(查询主体模型类,字段别名).join(联合查询的模型类,联合查询的条件).where().order_by().offset().limit()

        # 别名
        # 别名命名规则:目标表.目标列.label("别名")
        offset = (page - 1) * page_size
        query = (select(News, History.view_time.label("history_view_time"), History.id.label("history_id"))
                .join(History, History.news_id == News.id)
                .where(History.user_id == user_id)
                .order_by(History.view_time.desc())
                .offset(offset).limit(page_size)
                 )
        result = await db.execute(query)
        rows = result.all()
        return rows, total
        # 得到结果: 列表里面包着元组
        # [
        #   (新闻对象, 浏览时间, 浏览id)
        # ]


# 移除新闻收藏
async def remove_news_history(
        db: AsyncSession,
        user_id: int,
        news_id: int,
):
    stmt = delete(History).where(
        History.user_id == user_id,
        History.news_id == news_id,
    )
    result = await db.execute(stmt)
    await db.commit()
    # execute 的标注是 Result，rowcount 只在子类 CursorResult 上，用 cast 让类型检查器认可；
    # MySQL 不支持 DELETE ... RETURNING，所以删除条数只能靠 rowcount
    return cast(CursorResult[Any], result).rowcount > 0


# 清空浏览列表
async def remove_all_historys(
        db: AsyncSession,
        user_id: int,
):
    stmt = delete(History).where(History.user_id == user_id)
    result = await db.execute(stmt)
    await db.commit()

    return cast(CursorResult[Any], result).rowcount or 0 # 有具体数量就返回数量，否则返回0 cursor光标，游标
   