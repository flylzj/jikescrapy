# -*- coding: utf-8 -*-
REDIS_KEYS = {
    "token_key": "jike_token",
    "follower_key": ("{}_follower", "{}_verify_follower"),
    "following_key": ("{}_following", "{}_verify_following"),
    "jike_users_key": "jike_users",
    "crawling_user_key": "crawling_user",
    "robot_following_key": "robot_following",
    "user_info_key": "user_info",
    "user_info_hash_key": "{}_user_info",
    "more_key_key": "jike_more_key",
    "user_more_key": "{}_more_key",
    "finished_user": "finished_user",
}

mysql_config = {
    "username": "jike",
    "password": "jike123123",
    "host": "gz-cdb-h25tz5ek.sql.tencentcdb.com",
    "port": "62581",
    "database": "jike"
}

MYSQL_URI = 'mysql+pymysql://{username}:{password}@{host}:{port}/{database}'.format(**mysql_config)


# REDIS_CONFIG = {
#     "host": "120.24.66.220",
#     "port": "6379",
#     'password': 'lzjlzj123',
#     "db": 0,
#     "decode_responses": True,
#     "encoding": "utf-8"
# }

REDIS_CONFIG = {
    "host": "redis",
    "db": 0,
    "decode_responses": True,
    "encoding": "utf-8"
}

BOT_NAME = 'jikescrapy'

# LOG_LEVEL = 'DEBUG'
LOG_LEVEL = 'INFO'

FEED_EXPORT_ENCODING = 'utf-8'

DOWNLOAD_DELAY = 3  # 相同域名下载延时

SPIDER_MODULES = ['jikescrapy.spiders']
NEWSPIDER_MODULE = 'jikescrapy.spiders'

ROBOTSTXT_OBEY = False

DEFAULT_REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:61.0) Gecko/20100101 Firefox/61.0",
}


START_USERNAME = 'dianying'  # '82D23B32-CF36-4C59-AD6F-D05E3552CBF3'
JIKE_DEPTH = 100
