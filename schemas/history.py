
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from schemas.base import NewsItemBase


# 定义请求体参数(继承BaseModel)
class HistoryCheckResponse(BaseModel):
    is_history: bool = Field(..., alias = "isHistory")


# 定义请求体
class HistoryAddRequest(BaseModel):
    news_id: int = Field(..., alias="newsId")


# 规划两个类: 一个是新闻模型类 + 收藏的模型类
class HistoryNewsItemResponse(NewsItemBase):
    history_id: int = Field(alias="historyId")
    view_time: str = Field(alias="viewTime") # favorite用datetime
    
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )


# 收藏列表接口响应模型类
class HistoryListResponse(BaseModel):
    list: list[HistoryNewsItemResponse]
    total: int
    has_more: bool = Field(alias="hasMore")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )