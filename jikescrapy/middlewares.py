# -*- coding: utf-8 -*-
from .settings import REDIS_CONFIG, REDIS_KEYS
import redis
import requests
import json
from jike import JIKE


class JikescrapyDownloadMiddleware(object):
    def __init__(self):
        self.rds = redis.Redis(**REDIS_CONFIG)
        self.token = None
        # self.jike = JIKE()
        # if not self.jike.token:
        #     pass
        # else:
        #     self.rds.set(REDIS_KEYS.get("token_key"), str(self.jike.token))

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
        except Exception as e:
            self.token = None

    def process_request(self, request, spider):
        if not self.token:
            self.token = eval(self.rds.get(REDIS_KEYS.get("token_key")))
        request.headers.update(
            {
                "x-jike-access-token": self.token.get("x-jike-access-token")
            }
        )

    def process_response(self, request, response, spider):
        if response.status == 401:
            spider.logger.info('token过期,正在尝试刷新token')
            self.refresh_token()
            if not self.token:
                spider.logger.error('刷新token失败,请重新登录')
            return request

        if spider.name == 'jike_fan' and not json.loads(response.body).get('success'):
            return requests
        return response