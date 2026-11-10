from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from config.db_conf import get_db
from crud import favorite
from crud.favorite import is_news_favorite, add_news_favorite
from models.users import User
from schemas.favorite import FavoriteAddRequest, FavoriteCheckResponse
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
    page: int,
    page_size: int = Query(default=10, alias="pageSize", le = 100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return success_response(message="成功获取收藏列表")