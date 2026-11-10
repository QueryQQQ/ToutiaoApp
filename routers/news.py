# routers路由层

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from config.db_conf import get_db
from crud import news
from schemas.news import CategoryListResponse

# 模块化路由，使得每个模块对应自己接口，易维护
# 创建 APIRouter 实例（路由前缀，分组组名）
# 路由前缀会挂载到后续路由路径前面，tags 定义分组组名，可以折叠所包含的接口
# 编写完独立路由模块，还需要在 main 中挂载路由
router = APIRouter(prefix="/api/news", tags=["news"])

# 接口实现流程
# 1.定义模块化路由 -> 参照API接口规范文档定义
# 2.定义模型类 -> 参照数据库表定义（数据库设计文档）
# 3.在 crud 文件夹里面创建文件，封装操作数据库的方法
# 4.在路由处理函数里面调用 crud 封装好的方法，响应结果


# 1.获取新闻分类
# 定义路由里的 get_categories，处理 HTTP 请求
# response_model 告诉 FastAPI：返回值必须符合 CategoryListResponse 的结构
# 它负责三件事：按模型序列化 ORM 对象、校验数据、生成 Swagger 文档
@router.get("/categories", response_model=CategoryListResponse)# 错误2 没有加response model
async def get_categories(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """
    获取新闻分类
    :param skip: 跳过数量
    :param limit: 限制数量
    """
    categories = await news.get_categories(db, skip, limit)
    return {
        "code": 200,
        "message": "获取新闻分类成功",
        "data": categories,
    }


# 2.获取新闻列表
# 请求参数 categoryId page pageSize
@router.get("/list")
async def get_news_list(
        # 使用alias别名 规避传进来的参数是大小写混杂的
        category_id: int = Query(default = ..., alias = "categoryId"),
        page: int = 1,
        page_size: int = Query(default = 10, alias="pageSize", le=100),
        db: AsyncSession = Depends(get_db)
):
    # 查询功能
    # 进入请求 -> 处理分页规则 -> 按分类id查询新闻 -> 计算并获取总量 -> 计算是否还有更多新闻
    offset = (page - 1) * page_size # 跳过数量=(页码-1)*每页数量
    news_list = await news.get_news_list(db, category_id, offset, page_size)# 调用方法,三个参数
    total = await news.get_news_count(db, category_id)
    # 获取总量后查询是否有      # (offset + 当前新闻列表条数) < 总量
    has_more = (offset + len(news_list)) < total
    return {
          "code": 200,
            "message": "获取新闻分类成功",
            "data": {
                "list": news_list,
                "total": total,
                "hasMore": has_more,
            }
    }


# 3.获取新闻详情
@router.get("/detail")
async def get_news_detail(news_id: int = Query(alias="id"), db: AsyncSession = Depends(get_db)):
    # 响应内容：当前新闻详情 + 增加1次浏览量 + 相关新闻（同分类id里的新闻）
    news_detail = await news.get_news_details(db, news_id)

    # get_news_details 的返回类型是 News | None，这里先把 None 挡掉
    # 这一行之后，Pylance 就知道 news_detail 一定是 News，8 个警告一起消失
    if not news_detail: #news_detail is None判断是否为none，not news_detail进行取反操作，判断是否为空   
        raise HTTPException(status_code=404, detail="新闻不存在")

    # 获取相关新闻信息
    views_res = await news.increase_news_views(db, news_detail.id)
    
    if not views_res:
        raise HTTPException(status_code=404, detail="没有相关新闻")

    related_news = await news.get_related_news(db, news_detail.id, news_detail.category_id)

    return {
        "code": 200,
        "message": "success",
        "data": {
            "id": news_detail.id,
            "title": news_detail.title,
            "content": news_detail.content,
            "image": news_detail.image,
            "author": news_detail.author,        
            "publishTime": news_detail.publish_time,
            "categoryId": news_detail.category_id,
            "views": news_detail.views,
            "relatedNews": related_news
        }
    }
