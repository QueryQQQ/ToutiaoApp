# 整合 根据 token 查询用户,返回用户
from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from config.db_conf import get_db
from crud import users
from models.users import User


async def get_current_user(
    # Header() 是 FastAPI 的参数来源声明器，明确指定这个参数从 HTTP 请求头里取
    # alias 让 Swagger 文档显示规范的大小写（HTTP 头名本身大小写不敏感）
    authorization: str = Header(..., alias="Authorization"),
    db: AsyncSession = Depends(get_db),
) -> User:
    # token 有两种可能：带 "Bearer " 前缀的，或者前端直接塞的裸 token
    # removeprefix 在没有前缀时原样返回，两种都能兼容；
    token = authorization.removeprefix("Bearer ").strip()
    user = await users.get_user_by_token(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的令牌或已经过期的令牌",
        )

    return user
