# cruds数据库增删改查逻辑（封装数据库操作）
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.news import Category, News


# get_categories查询数据库
async def get_categories(db: AsyncSession, skip: int = 0, limit: int = 100):
    # 进行分页操作，select获得模型类，off
    stmt = select(Category).offset(skip).limit(limit)
    result = await db.execute(stmt) # db数据库执行上一句
    # scalars() 取出 ORM 对象列表；scalar() 只取第一行第一列
    return result.scalars().all()# 提取结果并返回


# 查询功能
# 按分类id查询新闻
async def get_news_list(db: AsyncSession, category_id: int = 0, skip: int = 0, limit: int = 100):
    # 查询的是指定分类下的所有新闻, news里面有符合用户指定的category_id
    stmt = select(News).where(News.category_id == category_id).offset(skip).limit(limit)
    result = await db.execute(stmt) # db数据库执行上一句
    return result.scalars().all()# 提取结果并返回

# 计算总量
async def get_news_count(db: AsyncSession,category_id: int):
    # 查询的是指定分类下的新闻数量
    # 注意括号位置：.where 是加在 select() 上的，不是加在 func.count() 上
    # func.count(News.id) 只是一个"计数表达式"，没有 where 方法；
    # select(...) 才是查询语句，where 是它的条件
    stmt = select(func.count(News.id)).where(News.category_id == category_id)
    result = await db.execute(stmt)
    return result.scalar_one() # scalar_one只能有一个结果, 否则就报错


# 获取新闻详情id
async def get_news_details(db: AsyncSession, news_id: int):
    stmt = select(News).where(News.id == news_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none() 


# 浏览量+1 修改字段
 
async def increase_news_views(db: AsyncSession, news_id: int):# 变量名是db，类型为AsyncSession，实际是个会话
    stmt = update(News).where(News.id == news_id).values(views=News.views + 1) # value语句给这些列赋值
    result = await db.execute(stmt)
    await db.commit() # 依赖项get_db是全部完成后再提交，而我们需要立即提交
    # rowcount统计命中的行数，命中就返回True
    return result.rowcount > 0 # type: ignore[attr-defined]


# 获取相关新闻
# 同分类id下 + 不同详情id
async def get_related_news(db: AsyncSession, news_id: int, category_id: int, limit: int = 5):
    # order_by 排序 -> 浏览量和发布时间
    stmt = select(# 返回全部信息只用限定News范围即可
         News.id,
         News.title,
         News.content,
         News.image,
         News.author,
         News.publish_time,
         News.category_id,
         News.views,
         ).where(
        News.category_id == category_id,
        News.id != news_id
    ).order_by( # 排序语句
        News.views.desc(),# 默认升序，desc表示降序
        News.publish_time.desc()
    ).limit(limit)
    result = await db.execute(stmt)
    # return result.scalars().all() 返回全部信息
    # 返回指定信息
    return result.mappings().all() 

