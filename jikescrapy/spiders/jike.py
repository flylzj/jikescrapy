# -*- coding: utf-8 -*-
import scrapy
from jike import JIKE
from ..settings import REDIS_CONFIG, REDIS_KEYS
import redis
import json
from ..items import JikescrapyItem


class JikeSpider(scrapy.Spider):
    name = 'jike'
    rds = redis.Redis(**REDIS_CONFIG)
    start_username = "82D23B32-CF36-4C59-AD6F-D05E3552CBF3"
    follower_api = 'https://app.jike.ruguoapp.com/1.0/userRelation/getFollowerList'
    following_api = 'https://app.jike.ruguoapp.com/1.0/userRelation/getFollowingList'

    def start_requests(self):
        jike = JIKE()
        if not jike.token:
            self.logger.error('登录失败')
            self.close(self, 'logging error')
        else:
            self.rds.set(REDIS_KEYS.get("token_key"), str(jike.token))
        data = {
            "loadMoreKey": None,
            "username": self.start_username,
            "limit": 20
        }
        yield scrapy.Request(
            self.follower_api,
            method='POST',
            body=json.dumps(data),
            headers={'Content-Type': 'application/json'},
            callback=self.get_relation_person,
            meta={'type': 'follower_key', 'api': self.follower_api, 'username': self.start_username}
        )
        yield scrapy.Request(
            self.following_api,
            method='POST',
            body=json.dumps(data),
            headers={'Content-Type': 'application/json'},
            callback=self.get_relation_person,
            meta={'type': 'following_key', 'api': self.following_api, 'username': self.start_username}
        )

    def get_relation_person(self, response):
        meta = response.meta
        data = json.loads(response.text)
        for d in data.get('data'):
            jike_item = JikescrapyItem()
            for key in jike_item.fields:
                jike_item[key] = d.get(key)
            if not self.rds.sismember(REDIS_KEYS.get('jike_users_key'), d.get('username')) \
                    and not self.rds.sismember(REDIS_KEYS.get("crawling_user_key"), d.get("username")):

                self.rds.sadd(REDIS_KEYS.get('crawling_user_key'), d.get('username'))
                # function self.get_personal_relation
                self.logger.info('start crawl user: {}'.format(d.get('username')))
                data = {
                    "loadMoreKey": None,
                    "username": d.get('username'),
                    "limit": 20
                }
                yield scrapy.Request(
                    self.follower_api,
                    method='POST',
                    body=json.dumps(data),
                    headers={'Content-Type': 'application/json'},
                    callback=self.get_relation_person,
                    meta={'type': 'follower_key', 'api': self.follower_api, 'username': d.get('username')}
                )
                yield scrapy.Request(
                    self.following_api,
                    method='POST',
                    body=json.dumps(data),
                    headers={'Content-Type': 'application/json'},
                    callback=self.get_relation_person,
                    meta={'type': 'following_key', 'api': self.following_api, 'username': d.get('username')}
                )

            self.rds.lpush(REDIS_KEYS.get(meta.get('type')).format(meta.get('username')), str(jike_item))
        more_key = data.get('loadMoreKey')
        if more_key:
            body = {
                "loadMoreKey": more_key,
                "username": meta.get('username'),
                "limit": 20
            }
            yield scrapy.Request(
                url=meta.get('api'),
                method='POST',
                body=json.dumps(body),
                headers={'Content-Type': 'application/json'},
                callback=self.get_relation_person,
                meta=meta
            )
        else:
            self.logger.info('finish username: {}'.format(meta.get('username')))
            self.rds.srem(REDIS_KEYS.get('crawling_user_key'), meta.get("username"))
            self.rds.sadd(REDIS_KEYS.get('jike_users_key'), meta.get('username'))
