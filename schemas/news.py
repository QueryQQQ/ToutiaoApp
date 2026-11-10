# schemas存储数据验证模型（pydantic）

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CategoryOut(BaseModel):
    """出参模型：只暴露要返回给前端的字段"""

    # from_attributes=True 允许直接从 ORM 对象（Category 实例）读取属性
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    sort_order: int
    created_at: datetime
    updated_at: datetime

class CategoryListResponse(BaseModel):
    """统一响应结构：code / message / data"""

    code: int = 200
    message: str = "获取分类成功"
    data: list[CategoryOut]
