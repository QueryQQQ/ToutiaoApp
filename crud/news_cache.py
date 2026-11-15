# cruds数据库增删改查逻辑（封装数据库操作）
from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from cache.news_cache import get_cache_news_list, get_cached_categories, set_cache_categories, set_cache_news_list
from models.news import Category, News
from schemas.base import NewsItemBase


# get_categories查询数据库
async def get_categories(db: AsyncSession, skip: int = 0, limit: int = 100):
    # 先从缓存中获取数据
    cached_categories = await get_cached_categories()
    if cached_categories:
        return cached_categories

    stmt = select(Category).offset(skip).limit(limit)
    result = await db.execute(stmt)
    categories =  result.scalars().all()

    # 写入缓存
    if categories:# 如果缓存有数据
        categories = jsonable_encoder(categories) # 转换为json可接受格式
        await set_cache_categories(categories)

    return categories


# 查询功能
# 按分类id查询新闻
async def get_news_list(db: AsyncSession, category_id: int = 0, skip: int = 0, limit: int = 100):
    # 先尝试从缓存获取数据
    # get_cache_news_list需要页码，直接用skip反推回去
    # skip = (page - 1) * size -> page = skip // limit + 1  //是整除
    page = skip // limit + 1 
    cache_list = await get_cache_news_list(category_id, page, limit) # 缓存的是json格式, 键是列名(category_id/publish_time)
    if cache_list:
        # 命中缓存时直接返回 dict，未命中时返回 ORM 对象，两者都只是"原始数据"
        # 真正决定响应结构的只有一处：路由层用 NewsItemBase 统一序列化
        # 不要再用 News(**item) 伪造 ORM 对象——造出来的对象没有 content/created_at/updated_at，
        # 会让"命中"和"未命中"两条路径的响应字段对不上
        return cache_list


    # 查询指定分类下的所有新闻
    stmt = select(News).where(News.category_id == category_id).offset(skip).limit(limit)
    result = await db.execute(stmt) # db数据库执行上一句
    news_list = result.scalars().all()# 提取结果并返回

    # 写入缓存
    if news_list:
        # 先把ORM数据转换为json才能写入缓存
        # 把ORM转换为pydnatic，再转化为字典
        # by_alias = False表示不使用别名，因为这个Redis数据不走前端，单纯后端用
        news_data = [NewsItemBase.model_validate(item).model_dump(mode="json", by_alias=False) for item in news_list]
        await set_cache_news_list(category_id, page, limit, news_data)

    return news_list

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

