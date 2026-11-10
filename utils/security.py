# 密码哈希的使用步骤
# 1. pip install "pwdlib[argon2]"
# 2. 创建 PasswordHash 实例（它决定用哪些算法、按什么顺序尝试）
# 3. 注册时 hash，登录时 verify
#
# 为什么从 passlib 换成 pwdlib：
# passlib 最后一版 1.7.4 停在 2020-10-08，已长期不维护；
# 且它与新版 bcrypt（>=4.1，你现在装的是 5.0.0）不兼容——
# 加载 bcrypt 后端时会用一个超长假密码做探测，bcrypt 新版直接抛
# ValueError: password cannot be longer than 72 bytes，
# 结果 CryptContext.hash() 一次都调不通，注册接口直接 500。


from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from pwdlib.hashers.bcrypt import BcryptHasher

# 2. 哈希器链，顺序有意义：
#    第一个 Argon2Hasher 是"写入端"，新注册的密码都用 Argon2id 算哈希；
#    第二个 BcryptHasher 是"兼容端"，库里历史数据是 $2b$ 开头的 bcrypt
#    哈希（比如 admin 那条），用它才能校验，不需要重置老账号。
#    以后老账号登录成功时可以顺手用 hash_and_update 升级成 Argon2。
password_hash = PasswordHash((
    Argon2Hasher(),
    BcryptHasher(),
))


# 对密码进行哈希加密
# 3. 注册：明文密码 -> 哈希串（存进数据库 password 字段的就是这个）
def get_hash_password(password: str) -> str:
    return password_hash.hash(password)


# 验证密码
# 3. 登录：用户输入的明文 vs 数据库里存的哈希，返回 True/False
def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


