# 封装通用响应结果，响应成功全是返回规定好的字典，封装规范化
# 1.抽取响应结果
from typing import Any

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


# 任何的FastAPI, pydantic, ORM类型都需求正常响应 -> code, message, data
# 只有声明类型才用: 赋值都用=
# data 后续可能返回多种类型，暂定为 Any
def success_response(message: str = "success", data: Any = None) -> JSONResponse:
    # 字典字面量声明
    content = {
        "code": 200,
        "message": message,
        "data": data,
    }
    # 使用jsonable_encoder来确保所有类型都能被正确转换
    return JSONResponse(jsonable_encoder(content))
