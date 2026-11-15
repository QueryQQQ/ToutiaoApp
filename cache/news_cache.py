# 新闻相关的缓存方法: 新闻分类的读取和写入
# key -value

from typing import Any, Dict, List, Optional

from config.cache_conf import get_json_cache, set_cache


CATEGORIES_KEY = "news:categories"
NEWS_LIST_PREFIX = "news_list:"


# 获取新闻分类缓存
async def get_cached_categories():
    return await get_json_cache(CATEGORIES_KEY)


# 写入新闻分类缓存: 缓存的数据, 过期时间
# 不同的数据过期时间不同,需要单独写
# 过期时间: 分类,配置:7200; 列表: 600; 详情: 1800; 验证码: 60 ->数据越稳定, 缓存时间越久,单位秒
async def set_cache_categories(data:List[Dict[str, Any]], expire: int = 7200):
    # 新闻分类数据是一个列表,里面包含一个字典,字典key为str, value为Any 
    return await set_cache(CATEGORIES_KEY, data, expire)


# 写入缓存-新闻列表: key定义规范：key=news_list:分类id：页码：每页数量 + 列表数据 + 过期时间
async def set_cache_news_list(category_id: Optional[int], page: int,size: int, news_list:List[Dict[str, Any]], expire: int = 1800):
    # 调用封装的REDIS方法，存新闻列表到缓存
    category_part = category_id if category_id is not None else "all" # 如果有分类id就以分类id写，没有就用all
    key = f"{NEWS_LIST_PREFIX}{category_part}:{page}:{size}"
    return await set_cache(key, news_list, expire)
    

# 读取缓存-新闻列表
async def get_cache_news_list(category_id:Optional[int], page: int, size: int):
    category_part = category_id if category_id is not None else "all"
    key = f"{NEWS_LIST_PREFIX}{category_part}:{page}:{size}"
    return await get_json_cache(key)