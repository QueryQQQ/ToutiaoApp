#　根据用户名来查询用户

from operator import add
import uuid
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from websockets.version import commit

from models.users import User, UserToken, UserUpdateRequest
from schemas.users import UserRequest
from utils import security


# 根据用户名查询数据库
async def get_user_by_username(db: AsyncSession, username: str):
    query = select(User).where(User.username == username)
    result = await db.execute(query)
    return result.scalar_one_or_none()


# 创建用户
async def create_user(db: AsyncSession, user_data: UserRequest):
    # 先密码加密处理 -> add
    hashed_password = security.get_hash_password(user_data.password)
    user = User(username=user_data.username, password=hashed_password)
    db.add(user)
    # flush 只把 INSERT 发给数据库、拿到自增 id，但不提交事务；
    # 交给 get_db 在请求结束时统一 commit，这样"建用户 + 建token"要么都成功、要么都回滚
    await db.flush()
    await db.refresh(user) # 从数据读取最新的user
    # 字段从无值变有值，需要更新确保正确添加了
    return user


# 生成token
async def create_token(db: AsyncSession, user_id: int):
    #生成token -> 设置过期时间 -> 查询数据库当前用户是否有token -> 有：更新，没有：添加
    # uuid4返回uuid.UUID 对象，数据库无法识别，只能转换为字符串存储
    token = str(uuid.uuid4()) # 生成token并转换为字符串
    # timedelta(days=7, hours=2, minutes=30, second=10)
    expires_at = datetime.now() + timedelta(days=7)
    query = select(UserToken).where(UserToken.user_id == user_id)
    result = await db.execute(query)
    user_token = result.scalar_one_or_none()

    if user_token: # 如果token存在（值为True）
        user_token.token = token # 更新token
        user_token.expires_at = expires_at
    else:
        # 没有token就创建一个新的对象将token存进去
        user_token = UserToken(user_id=user_id, token=token, expires_at=expires_at)
        db.add(user_token)

    # commit 放在 if/else 外面：更新和新增两条路径都要提交
    await db.commit()
    return token


# 用户登录
async def authenticate_user(db: AsyncSession, username: str, password: str):
    user = await get_user_by_username(db, username)
    if not user:
        return None
    if not security.verify_password(password, user.password):# user类里面的password
        return None
    
    return user


# 获取用户信息
# 根据token查询用户: 验证token
async def get_user_by_token(db: AsyncSession, token: str):
    query = select(UserToken).where(UserToken.token == token)# 数据库里面的token是否符合
    result = await db.execute(query) # 获取结果并存在容器里
    db_token = result.scalar_one_or_none() # 从容器中提取结果

    if not db_token or db_token.expires_at < datetime.now():
        return None

    # 查询用户：必须 select ORM 实体 User
    # 不能写成 select(UserInfoBase)——UserInfoBase 是 Pydantic 模型，
    # SQLAlchemy 不认识，会抛 ArgumentError: Column expression ... expected
    query = select(User).where(User.id == db_token.user_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


# 更新用户信息: update更新 -> 检查是否命中 -> 返回更新后的用户
async def update_by_user(db: AsyncSession, username: str, user_data: UserUpdateRequest):
    #update(User).where(User.username == username).value(字段=值, 字段=值)
    # 此时的user_data是pydantic类型,需要解包
    # 没有设置值的不更新,避免顶掉默认值
    query = update(User).where(User.username == username).values(**user_data.model_dump(
        # **拆掉两边大括号,model.dump将pydantic转化为字典
        exclude_unset=True,# 没有设置值的不更新
        exclude_none=True,# 将返回值为none的排除在外
    ))
    result = await db.execute(query)
    await db.commit()   

    # # 检查更新是否命中
    # if result.rowcount == 0: 
    #     # 匹配行数,有则+1
    #     raise HTTPException(status_code=404, detail="用户不存在")

    # 获取更新后的用户
    update_user = await get_user_by_username(db, username)
    return update_user


# 修改密码: 验证旧密码 -> 加密新密码 -> 赋值修改密码
async def change_password(db: AsyncSession, user: User, old_password, new_password):
    if not security.verify_password(old_password, user.password):
        return False
    hashed_new_pwd = security.get_hash_password(new_password)
    user.password = hashed_new_pwd
    db.add(user)
    await db.commit()
    await db.refresh(user)  
    return True