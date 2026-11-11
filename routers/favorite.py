from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from config.db_conf import get_db
from crud import favorite
from crud.favorite import is_news_favorite
from models.users import User
from schemas.favorite import FavoriteAddRequest, FavoriteCheckResponse, FavoriteListResponse, FavoriteNewsItemResponse
from utils.auth import get_current_user
from utils.response import success_response



router = APIRouter(prefix="/api/favorite", tags=["favorite"])


# 检查新闻收藏状态
# 定义newsid, 数据库, 当前用户
@router.get("/check")
async def check_favorite(
    news_id: int = Query(..., alias = "newsId"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    is_favorited = await is_news_favorite(db, user.id, news_id)
    return success_response(message="检查收藏状态成功", data=FavoriteCheckResponse(isFavorite=is_favorited))


# 收藏新闻
@router.post("/add")
async def add_favorite(
    data: FavoriteAddRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):

    result = await favorite.add_news_favorite(db, user.id, data.news_id)
    return success_response(message="添加收藏成功", data=result)


# 取消收藏新闻
@router.delete("/remove")
async def remove_favorite(
    news_id: int = Query(..., alias = "newsId"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):

    result = await favorite.remove_news_favorite(db, user.id, news_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="收藏记录不存在")
    return success_response(message="取消收藏成功")


# 获取收藏列表
# 需要分页查询,page,page_size,db,user
@router.get("/list")
async def get_favorite_list(
    page: int = Query(default=1,ge=1),
    page_size: int = Query(default=10, alias="pageSize", le = 100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rows, total = await favorite.get_favorite_list(db, user.id, page, page_size)
    # rows 是 list[Row]，每行 3 项：(News 实体, favorite_time, favorite_id),list[row]就是每个元素
    # Row 不能直接进响应：① 前端要驼峰别名 ② __dict__ 里有 _sa_instance_state
    # 所以逐条构造成 FavoriteNewsItemResponse
    favorite_list = [
        FavoriteNewsItemResponse.model_validate({
        **news.__dict__,# **解包, __dict__转字典
        "favorite_time": favorite_time,
        "favorite_id": favorite_id  
    }) for news, favorite_time, favorite_id in rows]
    has_more = total > page * page_size # has_more存bool值
    # 不能直接返回data,原因没有类型,不符合通用返回格式
    # 创建模型类来返回
    # model_validate 只接受一个位置参数 obj（要校验的原始数据），其余都是关键字参数
    # 所以这里必须传一个"字典"，不能把 list / total / hasMore 直接当关键字传进去
    data = FavoriteListResponse.model_validate({
        "list": favorite_list,
        "total": total,
        "hasMore": has_more,
    })
    return success_response(message="成功获取收藏列表", data=data)