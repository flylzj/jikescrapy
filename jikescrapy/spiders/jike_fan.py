# -*- coding: utf-8 -*-
import scrapy
import redis
from ..settings import REDIS_KEYS, REDIS_CONFIG
import json
from random import choice
from jike import JIKE


class JikeFanSpider(scrapy.Spider):
    custom_settings = {
        "DOWNLOAD_DELAY": 3600,
    }
    name = 'jike_fan'
    pool = redis.ConnectionPool(**REDIS_CONFIG)
    rds = redis.StrictRedis(connection_pool=pool)
    follow_api = 'https://app.jike.ruguoapp.com/1.0/userRelation/follow'
    unfollow_api = 'https://app.jike.ruguoapp.com/1.0/userRelation/unfollow'
    father_username = '6ef2cacc-f140-4e75-a60c-686808ef7c2b'

    def start_requests(self):
        user_info_key = REDIS_KEYS.get('user_info_key')
        userinfo = self.rds.hgetall(user_info_key)
        self.logger.info('username: {}\nscreenName: {}'.format(userinfo.get('username'), userinfo.get('screenName')))
        users = self.rds.zrangebyscore(REDIS_KEYS.get('robot_following_key'), 1, 1, start=0, num=1)
        if not users:
            self.logger.info('no data now')
            username = self.father_username
        else:
            username = users[0]

        data = {
            "username": username
        }
        yield scrapy.Request(
            self.follow_api,
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps(data),
            callback=self.follow,
            dont_filter=True,
            meta={'username': username}
        )

    def follow(self, response):
        result = json.loads(response.text)
        meta = response.meta
        if result.get('success'):
            self.logger.info('follow user {} success'.format(meta.get('username')))
            self.rds.zincrby(REDIS_KEYS.get('robot_following_key'), -1, meta.get('username'))
        users = self.rds.zrangebyscore(REDIS_KEYS.get('robot_following_key'), 1, 1, start=0, num=1)

        if not users:
            self.logger.info('no data now')
            username = self.father_username
        else:
            username = users[0]

        data = {
            "username": username
        }
        yield scrapy.Request(
            self.follow_api,
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps(data),
            callback=self.follow,
            dont_filter=True,
            meta={'username': username}
        )

