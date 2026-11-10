from pydantic import BaseModel, ConfigDict, Field


class UserRequest(BaseModel):
    username: str
    password: str


# 2.定义数据类型(封装通用响应格式)
# user_info对应的类: 基础类 + info类(id + 用户名)
# 用户信息分为可选的和必填的,因此拆分两个类更好管理
# 管理可选信息
class UserInfoBase(BaseModel) :
    # 用户信息基础数据模型
    nickname: str | None = Field(None, max_length=50, description="昵称")# str | None等价于optional[str]
    avatar: str | None = Field(None, max_length=255, description="头像URL")
    gender: str | None = Field(None, max_length=10, description="新性别")
    bio: str | None = Field(None, max_length=500, description="个人简介")

# 管理必填信息
class UserInfoResponse(UserInfoBase):
    id: int
    username: str
    
    #模型类配置
    model_config = ConfigDict(
        from_attributes= True, # 允许从ORM对象中取值
    )


# 返回有token还有其他data数据类型,定义一个类
class UserAuthResponse(BaseModel):
    token: str
    user_info: UserInfoResponse = Field(..., alias="userInfo")# field注释

    #模型类配置
    model_config = ConfigDict(
        populate_by_name = True, # alias 和字段名兼容
        from_attributes= True, # 允许从ORM对象中取值
    )


# 修改用户密码类
class UserChangePasswordRequest(BaseModel):
    old_password: str = Field(..., alias = "oldPassword", description= "这是旧密码")
    new_password: str = Field(..., min_length=6, alias="newPassword", description= "这是新密码")   