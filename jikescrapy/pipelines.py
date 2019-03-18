# -*- coding: utf-8 -*-
import redis
from .settings import REDIS_CONFIG, REDIS_KEYS, MYSQL_URI
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.engine import create_engine
from model import JikeUser
import time


class JikescrapyPipeline(object):
    def __init__(self):
        pool = redis.ConnectionPool(**REDIS_CONFIG)
        self.rds = redis.StrictRedis(connection_pool=pool)
        engine = create_engine(MYSQL_URI)
        session = sessionmaker(bind=engine)
        self.Session = scoped_session(session)

    @staticmethod
    def get_dict_items(d):
        for k, v in d.items():
            if not isinstance(v, dict):
                yield k, v

    @staticmethod
    def convert_time(time_str):
        try:
            return int(time.mktime(time.strptime(time_str.split('.')[0], '%Y-%m-%dT%H:%M:%S')))
        except Exception as e:
            return 0

    def process_item(self, item, spider):
        # user_info_hash_key = REDIS_KEYS.get('user_info_hash_key')
        # with self.rds.pipeline() as p:
        #     p.sadd(item.get('follow_key'), item.get('username'))
        #     for k, v in self.get_dict_items(item):
        #         p.hsetnx(user_info_hash_key.format(item.get('username')), k, str(v))
        #         p.execute()
        self.rds.sadd(item.get('follow_key'), item.get('username'))
        session = self.Session()
        if session.query(JikeUser).filter_by(
            username=item.get("username")
        ):
            spider.logger.debug("{} already in db ".format(item.get("username")))
            return item
        jike_user = JikeUser(
            username=item.get("username"),
            briefIntro=item.get("briefIntro"),
            city=item.get('city'),
            country=item.get('country'),
            createdAt=item.get('createdAt'),
            create_at_int=self.convert_time(item.get('createdAt')),
            gender=item.get('gender'),
            isVerified=1 if item.get('isVerified') else 0,
            profileImageUrl=item.get('profileImageUrl'),
            province=item.get('province'),
            ref=item.get('ref'),
            screenName=item.get('screenName'),
            updatedAt=item.get('updatedAt'),
            update_at_int=self.convert_time(item.get('update_at_int')),
            verifyMessage=item.get('verifyMessage')
        )
        try:
            session.add(jike_user)
            session.commit()
            spider.logger.debug("add {} success".format(item.get("username")))
        except Exception as e:
            spider.logger.error("add {} error {}".format(item.get("username"), e))
        return item

    def close_spider(self, spider):
        pass
