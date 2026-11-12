from fastapi import FastAPI

# cors是一种浏览器安全机制，用于允许在同一个源的运行的web应用向另一个源的web应用提起HTTP请求
# middleware中间件用于调和前端和后端的跨域（地址不同）问题，告诉后端这个前端可以访问
# 同源指的是协议、域名、端口都要相同
from fastapi.middleware.cors import CORSMiddleware

from routers import favorite, history, news, users
from utils.exception_handlers import register_excetion_handlers  # 引入路由模块

# 颜色对应的语言元素
# 黄=函数/方法，青=类/类型，浅蓝=变量，绿=注释，蓝=关键字

app = FastAPI()

# 注册异常处理器
register_excetion_handlers(app)

# 添加中间件
app.add_middleware(
    CORSMiddleware,         # 添加的中间件的类型
    allow_origins=["*"],    # 允许的源 *号代表所有源，实际开发要规定指定源
    allow_credentials=True, # 允许携带cookie
    allow_methods=["*"],    # 允许的请求方法
    allow_headers=["*"],    # 允许的请求头
)
# 实际允许源
"""
allow_origins=[
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    ],
"""


@app.get("/")
def root():
    return {"message": "Hello World"}


# 挂载路由/注册路由
app.include_router(news.router)
app.include_router(users.router)
app.include_router(favorite.router)
app.include_router(history.router)