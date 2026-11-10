from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from config.db_conf import get_db
from crud import users
from models.users import User, UserUpdateRequest
from schemas.users import UserAuthResponse, UserChangePasswordRequest, UserInfoResponse, UserRequest
from utils.auth import get_current_user
from utils.response import success_response

router = APIRouter(prefix="/api/user", tags=["users"])


# 进行注册
@router.post("/register")
async def register(user_data: UserRequest, db: AsyncSession = Depends(get_db)): # 用户信息和db
    #　注册逻辑：验证用户是否存在 -> 创建用户 -> 生成token -> 响应结果
    existing_user = await users.get_user_by_username(db, user_data.username)# 查看用户名字
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户已存在")
    user = await users.create_user(db, user_data) # ORM类型
    token = await users.create_token(db, user.id)
    # return{
    #     "code": 200,
    #     "message": "注册成功",
    #     "data": {
    #         "token": token,
    #         "userInfo": {
    #             "id": user.id,
    #             "username": user.username,
    #             "bio":user.bio,
    #             "avatar": user.avatar,
    #         }
    #     }
    # }

    # 封装通用格式响应结果
    # 3.调用函数响应结果
    # 参数token = 用户token值
    resposnse_data = UserAuthResponse(token = token, userInfo = UserInfoResponse.model_validate(user))# model_validate(user)从user中取值
    return(success_response(message = "注册成功", data = resposnse_data))


# 进行登录
@router.post("/login")
async def login(user_data: UserRequest, db: AsyncSession = Depends(get_db)): # 登录输入用户名和密码,在之前定义的UserRequest里作为基本信息
    # 登录逻辑: 验证用户是否存在 -> 验证密码 -> 生成token -> 响应结果
    user = await users.authenticate_user(db, user_data.username, user_data.password) # UserRequest赋值给user_data,后续可以直接调用
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail = "用户名或密码输入错误")
    token = await users.create_token(db, user.id)
    response_data = UserAuthResponse(token=token, userInfo=UserInfoResponse.model_validate(user)) # orm对象user,UserAuthResponse定义data类所以用
    return success_response(message= "响应成功啦", data = response_data)    


# 获取用户信息
@router.get("/info")
# 这里不直接调用函数而是依赖注入
# 两种方法等价,都可以获得参数,逻辑,返回值,唯一区别是直接调用由你执行且需要重新写明函数所需参数,而依赖注入交给FastAPI执行,直接用函数名,参数调用全在函数里写完
async def get_user_info(user: User = Depends(get_current_user)):# 形参user
    # 查询用户登录状态(用户已登陆且token未过期) -> 封装crud方法 -> 功能整合成函数 -> 路由导入使用: 依赖注入
    return success_response(
        message="获取用户信息成功",
        data=UserInfoResponse.model_validate(user),
    )


# 修改用户信息：验证Token -> 更新(用户输入数据put提交) ->请求体参数 ->定义Pydantic模型类 -> 响应结果
# 参数: 用户输入的+验证token的+db
@router.put("/update")
async def update_user_info(
    user_data: UserUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
    ):# 形参user
    user1 = await users.update_by_user(db, user.username, user_data)
    return success_response(
        message="修改用户信息成功",
        data = UserInfoResponse.model_validate(user1),
        )


# 修改密码
@router.put("/password")
async def update_password(
    password_data: UserChangePasswordRequest,# 要求在第一位 否则报错Non-default argument follows default argument
    db: AsyncSession = Depends(get_db),      # 无默认值参数一定要在有默认值参数之前,像是Depends / Query / Body
    user:User = Depends(get_current_user),   # 否则出现无法跳过有默认值参数去传值给无默认值参数的情况
    ):
    res_change_pwd = await users.change_password(
        db,
        user,
        password_data.old_password,
        password_data.new_password,
        )
    if not res_change_pwd:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="修改密码失败")
    return success_response(message="修改密码成功")