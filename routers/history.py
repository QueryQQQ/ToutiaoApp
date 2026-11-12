from fastapi import APIRouter, Depends, HTTPException, Query

from rich.status import Status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status


from config.db_conf import get_db
from crud import history
from crud.favorite import remove_news_favorite
from models.news import News
from models.users import User
from schemas.favorite import FavoriteListResponse
from schemas.history import HistoryAddRequest, HistoryCheckResponse, HistoryListResponse, HistoryNewsItemResponse
from utils.auth import get_current_user
from utils.response import success_response


router = APIRouter(prefix="/api/history", tags=["history"])


# 检查历史收藏状态
# 定义newsid, 数据库, 当前用户
@router.get("/check")
async def check_history(
    news_id: int = Query(..., alias = "newsId"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    is_in_history = await history.check_news_history(db, user.id, news_id)
    return success_response(message="检查收藏状态成功", data=HistoryCheckResponse(isHistory=is_in_history))


# 添加浏览历史
@router.post("/add")
async def  add_history(
    data: HistoryAddRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await history.add_historys(db, user.id, data.news_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="浏览记录不存在")
    return success_response(message="添加成功", data=result)


# 获取浏览历史列表
@router.get("/list")
async def get_history_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100, alias="pageSize"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows, total = await history.get_history_list(db, user.id, page, page_size)
    # rows 是 list[Row]，每行 3 项：(News 实体, favorite_time, favorite_id),list[row]就是每个元素
    # Row 不能直接进响应：① 前端要驼峰别名 ② __dict__ 里有 _sa_instance_state
    history_list = [
        HistoryNewsItemResponse.model_validate({
        **news.__dict__,# **解包, __dict__转字典
        "view_time": view_time.strftime("%Y-%m-%d %H:%M:%S"),
        "history_id": history_id  
    }) for news, view_time, history_id in rows]
    has_more = total > page * page_size # has_more存bool值
    # 不能直接返回data,原因没有类型,不符合通用返回格式
    # 创建模型类来返回
    # model_validate 只接受一个位置参数 obj（要校验的原始数据），其余都是关键字参数
    # 所以这里必须传一个"字典"，不能把 list / total / hasMore 直接当关键字传进去
    data = HistoryListResponse.model_validate({
        "list": history_list,
        "total": total,
        "hasMore": has_more,
    })
    return success_response(message="成功获取浏览历史", data=data)


@router.delete("/delete/{history_id}")
async def delete_history(
    news_id: int = Query(..., alias = "newsId"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await history.remove_news_history(db, user.id, news_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="收藏记录不存在")
    return success_response(message="历史删除成功") # 删除成功data直接返回None即可


# 清空收藏列表
@router.delete("/clear")
async def clear_favorite_list(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    count= await history.remove_all_historys(db, user.id)
    return success_response(message=f"清空了{count}条新闻")
            