# -*- coding: utf-8 -*-
import redis
import requests
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
        self.rds.sadd(item.get('follow_key'), item.get('username'))
        spider.logger.info('get {} for {} '.format(item.get("username"), item.get('follow_key')))
        if item.get("isVerified"):
            self.rds.sadd(item.get("verify_follow_key"), item.get("username"))
            self.rds.zadd(REDIS_KEYS.get('robot_following_key'), {item.get('username'): 1})
        session = self.Session()
        user = session.query(JikeUser).filter_by(
            username=item.get("username")
        ).first()
        if user:
            user.screenName = item.get('screenName')
            user.briefIntro = item.get("briefIntro")
            user.city = item.get('city') if item.get("briefIntro") else ''
            user.country = item.get('country') if item.get('country') else ''
            user.gender = item.get('gender') if item.get('gender') else ''
            user.isVerified = 1 if item.get('isVerified') else 0
            user.profileImageUrl = item.get('profileImageUrl') if item.get('profileImageUrl') else ''
            user.province = item.get('province') if item.get('province') else ''
            user.updatedAt = item.get('updatedAt') if item.get('updatedAt') else ''
            user.update_at_int = self.convert_time(item.get('update_at_int'))
            user.verifyMessage = item.get('verifyMessage') if item.get('verifyMessage') else ''
            try:
                session.commit()
                spider.logger.debug("{} already in db, update success".format(item.get("username")))
            except Exception as e:
                spider.logger.error("update {} error".format(item.get("username")))
            finally:
                session.close()
            return item
        jike_user = JikeUser(
            username=item.get("username"),
            briefIntro=item.get("briefIntro"),
            city=item.get('city') if item.get("briefIntro") else '',
            country=item.get('country') if item.get('country') else '',
            createdAt=item.get('createdAt') if item.get('createdAt') else '',
            create_at_int=self.convert_time(item.get('createdAt')),
            gender=item.get('gender') if item.get('gender') else '',
            isVerified=1 if item.get('isVerified') else 0,
            profileImageUrl=item.get('profileImageUrl') if item.get('profileImageUrl') else '',
            province=item.get('province') if item.get('province') else '',
            ref=item.get('ref') if item.get('ref') else '',
            screenName=item.get('screenName') if item.get('screenName') else '',
            updatedAt=item.get('updatedAt') if item.get('updatedAt') else '',
            update_at_int=self.convert_time(item.get('update_at_int')),
            verifyMessage=item.get('verifyMessage') if item.get('verifyMessage') else ''
        )
        try:
            session.add(jike_user)
            session.commit()
            spider.logger.debug("add {} success".format(item.get("username")))
        except Exception as e:
            spider.logger.error("add {} error {}".format(item.get("username"), e))
        finally:
            session.close()
        return item

    def close_spider(self, spider):
        pass
