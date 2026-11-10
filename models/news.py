# models存放数据库模型（sqlalchemy.orm）
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# 用处分别是设置模型类，设置属性类型，映射字段


# 通用的：所有表都有的时间字段
class Base(DeclarativeBase):
    # column 对应表里面一列的定义，把列名、数据类型、约束（主键、唯一、可空等）和默认值打包成一个 Column 对象
    # mapped_column 负责创建这个对象（这里的 created_at、updated_at）
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        comment="创建时间",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,                       # 字段类型
        default=datetime.now,
        onupdate=datetime.now,
        comment="更新时间",
    )


# 模型化类
# 新闻分类类
class Category(Base):
    __tablename__ = "news_category"     # 数据表名

    # 定义了数据库类型、主键、自增、描述
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="分类id"
    )
    # 定义了数据库类型、是否唯一、能否为空、描述
    name: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, comment="分类名称"
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="排序"
    )

    # 打印对象时好看一点，调试用
    def __repr__(self):
        return f"<Category(id={self.id}, name={self.name}, sort_order={self.sort_order})>"


# 新闻详情类
class News(Base):
    __tablename__ = "news"

    # 创建索引: 提升查询速度 → 添加目录
    # Index 的参数是（索引名, 列名...），列名直接写位置参数，不要写 name= / *expressions=
    __table_args__ = (
        Index('fk_news_category_idx', 'category_id'),    # 高频查询场景，创建后不是全表搜索，而是只通过分类id搜索
        Index('idx_publish_time', 'publish_time'),       # （索引名字，列）
    ) # fk代表foreign key外键，idx代表index普通索引

    # 定义了数据库类型，主键，自增，描述
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="新闻ID")
    # 定义了数据库类型，能否为空，描述
    title: Mapped[str] = mapped_column(String(255), nullable=False, comment="新闻标题")
    description: Mapped[str | None] = mapped_column(String(500), comment="新闻简介")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="新闻内容")
    image: Mapped[str | None] = mapped_column(String(255), comment="封面图片URL")
    author: Mapped[str | None] = mapped_column(String(50), comment="作者")
    # 外键：指向 news_category 表的主键 id
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey('news_category.id'), nullable=False)
    views: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="浏览量")
    publish_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="发布时间")

    # 打印对象，调试用
    def __repr__(self):
        return f"<News(id={self.id}, title='{self.title}', views={self.views})>"
