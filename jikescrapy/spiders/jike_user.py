# -*- coding: utf-8 -*-
import scrapy
import redis
from ..settings import REDIS_KEYS, REDIS_CONFIG
import json


class JikeUserSpider(scrapy.Spider):
    name = 'jike_user'
    rds = redis.Redis(**REDIS_CONFIG)
    follower_api = 'https://app.jike.ruguoapp.com/1.0/userRelation/getFollowerList'
    following_api = 'https://app.jike.ruguoapp.com/1.0/userRelation/getFollowingList'

    def start_requests(self):
        user_info_key = REDIS_KEYS.get('user_info_key')
        username = '82D23B32-CF36-4C59-AD6F-D05E3552CBF3'# self.rds.hget(user_info_key, 'username')
        self.logger.info('username {}'.format(username))
        data = {
            "loadMoreKey": None,
            "username": username,
            "limit": 20
        }
        yield scrapy.Request(
            self.follower_api,
            method='POST',
            body=json.dumps(data),
            headers={'Content-Type': 'application/json'},
            callback=self.get_relation_person,
            meta={'type': 'follower_key', 'api': self.follower_api, 'username': username, 'd': 0}
        )

    def get_relation_person(self, response):
        meta = response.meta
        data = json.loads(response.text)
        follow_key = REDIS_KEYS.get(meta.get('type')).format(meta.get('username'))
        if not data.get('data'):
            self.logger.info(str(data.get('data')))
            self.logger.info('no follower for user {}'.format(meta.get('username')))
        for d in data.get('data'):
            f_username = d.get('username')
            self.logger.info('get {} for {}'.format(f_username, meta.get('username')))
            self.rds.hset(follow_key, f_username, str(d))
            if meta.get('d') < 1:
                post_data = {
                    "loadMoreKey": None,
                    "username": f_username,
                    "limit": 20
                }
                yield scrapy.Request(
                    self.follower_api,
                    method='POST',
                    body=json.dumps(post_data),
                    headers={'Content-Type': 'application/json'},
                    callback=self.get_relation_person,
                    meta={'type': 'follower_key', 'api': self.follower_api, 'username': f_username, 'd': 1}
                )
        if data.get('loadMoreKey'):
            self.logger.info('more key for {}'.format(meta.get('username')))
            post_data = {
                "loadMoreKey": data.get('loadMoreKey'),
                "username": meta.get('username'),
                "limit": 20
            }
            yield scrapy.Request(
                self.follower_api,
                method='POST',
                body=json.dumps(post_data),
                headers={'Content-Type': 'application/json'},
                callback=self.get_relation_person,
                meta=meta
            )
        else:
            self.logger.info('finish user {}'.format(meta.get('username')))


