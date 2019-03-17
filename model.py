# coding: utf-8
from sqlalchemy import Column, String, Text, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from jikescrapy.settings import MYSQL_URI

base = declarative_base()


class JikeUser(base):
    __tablename__ = 'jike_user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    jike_id = Column(String(64), nullable=False, default="")
    username = Column(String(64), nullable=False, default="", unique=True)  # username eg. c66c0403-5ae5-4fc6-adfb-1be70f138d59
    briefIntro = Column(String(128), nullable=False, default="")  # 自我介绍  eg. 喜欢萝莉哈哈哈哈哈嗝
    city = Column(String(12), nullable=False, default="")  # 城市 eg. 001051006
    country = Column(String(12), nullable=False, default="")  # 国家 eg. 001
    createdAt = Column(String(30), nullable=False, default="")  # 账号创建时间 eg. "2018-09-22T16:00:00.000Z"
    create_at_int = Column(Integer, nullable=False, default=0)  # 时间戳
    gender = Column(String(30), nullable=False)  # 性别 eg. MALE
    isVerified = Column(Integer, nullable=False)  # 是否认证  eg. 1
    profileImageUrl = Column(String(256), nullable=False, default="")  # 头像
    province = Column(String(12), nullable=False, default="")  # 省
    ref = Column(String(64), nullable=False, default="")  # 未知  eg. MY_FOLLOWERS
    screenName = Column(String(64), nullable=False, default="")  # 昵称
    updatedAt = Column(String(30), nullable=False, default="")  # 账号更新时间？
    update_at_int = Column(Integer, nullable=False, default=0)
    verifyMessage = Column(String(256), nullable=False, default="")  # 认证信息


if __name__ == '__main__':
    engine = create_engine(MYSQL_URI)
    base.metadata.bind = engine
    base.metadata.drop_all()
    base.metadata.create_all()