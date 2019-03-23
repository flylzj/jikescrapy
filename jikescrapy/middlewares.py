# -*- coding: utf-8 -*-
from .settings import REDIS_CONFIG, REDIS_KEYS
import redis
import requests
from jike import JIKE
import logging
import time


class JikeFanDownloadMiddleware(object):
    def __init__(self):
        pool = redis.ConnectionPool(**REDIS_CONFIG)
        self.rds = redis.StrictRedis(connection_pool=pool)

    def process_request(self, request, spider):
        token = self.rds.hget(REDIS_KEYS.get('user_info_key'), 'x-jike-access-token')
        update_time = self.rds.hget(REDIS_KEYS.get('user_info_key'), 'update_time')
        spider.logger.info('token {}\nupdate_time {}'.format(token, update_time))
        request.headers.update(
            {
                "x-jike-access-token": token
            }
        )

    def process_response(self, request, response, spider):
        if response.status != 200:
            spider.logger.warning(response.text)
            return request
        return response


class JikescrapyDownloadMiddleware(object):
    def __init__(self):
        pool = redis.ConnectionPool(**REDIS_CONFIG)
        self.rds = redis.StrictRedis(connection_pool=pool)
        self.jike = JIKE()
        self.token = self.jike.token
        self.profile = self.jike.profile
        self.load_user_info()

    def load_user_info(self):
        logging.info('正在加载user info')
        keys = ['username', 'screenName', 'briefIntro', 'id']
        user_info_key = REDIS_KEYS.get('user_info_key')
        for k, v in self.profile.get('user').items():
            if k in keys:
                self.rds.hset(user_info_key, k, v)
        keys = ['x-jike-refresh-token', 'x-jike-access-token', 'token']
        for k, v in self.token.items():
            if k in keys:
                self.rds.hset(user_info_key, k, v)
        self.rds.hset(user_info_key, 'update_time', time.strftime("%Y-%m-%d %H:%M:%S"))
        logging.info('info写入redis成功')

    def refresh_token(self):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:61.0) Gecko/20100101 Firefox/61.0",
            }
            headers.update(
                {
                    "x-jike-refresh-token": self.token.get('x-jike-refresh-token')
                }
            )
            refresh_token_api = 'https://app.jike.ruguoapp.com/app_auth_tokens.refresh'
            r = requests.get(refresh_token_api, headers=headers)
            self.token = r.json()
            return True
        except Exception as e:
            self.token = None
            return False

    def process_request(self, request, spider):
        request.headers.update(
            {
                "x-jike-access-token": self.token.get("x-jike-access-token")
            }
        )

    def process_response(self, request, response, spider):
        if response.status != 200:
            spider.logger.info('token过期,正在尝试刷新token')
            self.refresh_token()
            if not self.token:
                spider.logger.error('刷新token失败,请重新登录')
                spider.close(spider, 'login error')
            else:
                spider.logger.info('刷新token成功')
                self.load_user_info()
            return request
        return response