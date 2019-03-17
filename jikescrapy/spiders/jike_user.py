# -*- coding: utf-8 -*-
import scrapy
import redis
from ..settings import REDIS_KEYS, REDIS_CONFIG, START_USERNAME
import json
from ..items import JikeUserItem


class JikeUserSpider(scrapy.Spider):
    name = 'jike_user'
    pool = redis.ConnectionPool(**REDIS_CONFIG)
    rds = redis.StrictRedis(connection_pool=pool)
    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {
            'jikescrapy.middlewares.JikescrapyDownloadMiddleware': 800,
        },
        'ITEM_PIPELINES': {
            'jikescrapy.pipelines.JikescrapyPipeline': 100
        }
    }
    follower_api = 'https://app.jike.ruguoapp.com/1.0/userRelation/getFollowerList'
    following_api = 'https://app.jike.ruguoapp.com/1.0/userRelation/getFollowingList'

    def get_user_more_key(self, username):
        user_more_key = REDIS_KEYS.get("user_more_key")
        more_key = self.rds.get(user_more_key.format(username))
        return eval(more_key) if more_key else None

    def set_user_more_key(self, username, more_key_str):
        user_more_key = REDIS_KEYS.get("user_more_key")
        self.rds.set(user_more_key.format(username), more_key_str)

    @staticmethod
    def get_dict_items(d):
        for k, v in d.items():
            if not isinstance(v, dict):
                yield k, v

    def start_requests(self):
        user_info_key = REDIS_KEYS.get('user_info_key')
        username = START_USERNAME if START_USERNAME else self.rds.hget(user_info_key, 'username')
        self.logger.info('username {}'.format(username))
        data = {
            # "loadMoreKey": None,
            "loadMoreKey": self.get_user_more_key(username),
            "username": username,
            "limit": 20
        }
        yield scrapy.Request(
            self.follower_api,
            method='POST',
            body=json.dumps(data),
            headers={'Content-Type': 'application/json'},
            callback=self.get_relation_person,
            meta={'type': 'follower_key', 'api': self.follower_api, 'username': username, 'd': 0, 'page': 0}
        )
        yield scrapy.Request(
            self.following_api,
            method='POST',
            body=json.dumps(data),
            headers={'Content-Type': 'application/json'},
            callback=self.get_relation_person,
            meta={'type': 'following_key', 'api': self.following_api, 'username': username, 'd': 0, 'page': 0}
        )

    def get_relation_person(self, response):
        meta = response.meta
        data = json.loads(response.text)
        follow_key = REDIS_KEYS.get(meta.get('type')).format(meta.get('username'))
        # if not data.get('data'):
        #     self.logger.info(str(data.get('data')))
        #     self.logger.info('no follower for user {}'.format(meta.get('username')))
        for d in data.get('data'):
            f_username = d.get('username')
            jike_user_item = JikeUserItem()
            for k in jike_user_item.fields:
                jike_user_item[k] = d.get(k)
            jike_user_item['follow_key'] = follow_key
            yield jike_user_item
            # self.logger.info('get {} for {}'.format(f_username, meta.get('username')))
            if meta.get('d') < 2:
                d = meta.get('d')
                d += 1
                post_data = {
                    "loadMoreKey": self.get_user_more_key(f_username),
                    "username": f_username,
                    "limit": 20
                }
                yield scrapy.Request(
                    self.follower_api,
                    method='POST',
                    body=json.dumps(post_data),
                    headers={'Content-Type': 'application/json'},
                    callback=self.get_relation_person,
                    meta={
                        'type': 'follower_key',
                        'api': self.follower_api,
                        'username': f_username,
                        'd': d,
                        'page': 0
                    }
                )
                yield scrapy.Request(
                    self.following_api,
                    method='POST',
                    body=json.dumps(post_data),
                    headers={'Content-Type': 'application/json'},
                    callback=self.get_relation_person,
                    meta={
                        'type': 'following_key',
                        'api': self.following_api,
                        'username': f_username,
                        'd': d,
                        'page': 0
                    }
                )
        more_key = data.get('loadMoreKey')
        self.set_user_more_key(meta.get('username'), str(more_key))
        if more_key:
            meta['page'] += 1
            self.logger.info('more key for {}, now page {}'.format(meta.get('username'), meta.get('page')))
            post_data = {
                "loadMoreKey": data.get('loadMoreKey'),
                "username": meta.get('username'),
                "limit": 20
            }
            yield scrapy.Request(
                meta.get('api'),
                method='POST',
                body=json.dumps(post_data),
                headers={'Content-Type': 'application/json'},
                callback=self.get_relation_person,
                meta=meta
            )
        else:
            self.logger.info('finish user {}, type {}'.format(meta.get('username'), meta.get('type')))
            self.rds.sadd(REDIS_KEYS.get('finished_user'), meta.get('username'))





