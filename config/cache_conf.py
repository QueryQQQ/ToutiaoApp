# 安装和配置客户端redis

from typing import Any
import json

import redis.asyncio as redis

# 规范定义，避免后续改变导致需要大量修改
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0

# 创建redis的连接对象
redis_client = redis.Redis(
    host=REDIS_HOST,        # Redis 服务器主机地址
    port=REDIS_PORT,        # Redis 端口号
    db=REDIS_DB,            # Redis 数据库编号， 0~15
    decode_responses=True,  # 是否将字节数据解码为字符串
)

# 原理: 前端先读取缓存,缓存没有对应数据再读取后端,速度更快
# 读取：字符串
async def get_cache(key: str):
    try: # 不一定能获取数据,使用try
        return await redis_client.get(key)
    except Exception as e:
        print(f"获取缓存失败: {e}")



# 读取: 列表或者字典
async def get_json_cache(key: str):
    try:
        data =  await redis_client.get(key) 
        # cache里面存的是字符串,要先序列化才能能转为列表或字典
        if data:
            return json.loads(data) # 序列化
        else:
            return None
    except Exception as e:
        print(f"获取缓存失败: {e}")
        return None


# 设置缓存setex(key, expire, value)
async def set_cache(key: str, value: Any, expire: int = 3600):
    try:
        # 如果是字典和列表,要转字符串再存到缓存里面
        if isinstance(value, (dict, list)):
            # json.dump将python对象转为json字符串
            value = json.dumps(value, ensure_ascii=False) # 中文保持正常,不转译
        await redis_client.setex(key, expire, value) # 字符串直接存
    except Exception as e:
        print(f"设置缓存失败:{e}")
        return False