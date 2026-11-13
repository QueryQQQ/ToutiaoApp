# 安装和配置客户端redis
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