# -*- coding: utf-8 -*-
import redis
from .settings import REDIS_CONFIG, REDIS_KEYS


class JikescrapyPipeline(object):
    def __init__(self):
        pool = redis.ConnectionPool(**REDIS_CONFIG)
        self.rds = redis.StrictRedis(connection_pool=pool)

    @staticmethod
    def get_dict_items(d):
        for k, v in d.items():
            if not isinstance(v, dict):
                yield k, v

    def process_item(self, item, spider):
        user_info_hash_key = REDIS_KEYS.get('user_info_hash_key')
        with self.rds.pipeline() as p:
            p.sadd(item.get('follow_key'), item.get('username'))
            for k, v in self.get_dict_items(item):
                p.hsetnx(user_info_hash_key.format(item.get('username')), k, str(v))
                p.execute()
        return item

    def close_spider(spider):
        pass
