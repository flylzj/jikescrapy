# -*- coding: utf-8 -*-
REDIS_KEYS = {
    "token_key": "jike_token",
    "follower_key": "{}_follower",
    "following_key": "{}_following",
    "jike_users_key": "jike_users",
    "crawling_user_key": "crawling_user",
    "robot_following_key": "robot_following",
    "user_info_key": "user_info"
}


MYSQL_URI = 'mysql+pymysql://jike:jike123@gz-cdb-h25tz5ek.sql.tencentcdb.com:62581/jike'

REDIS_CONFIG = {
    "host": "139.199.66.15",
    "port": "6379",
    'password': 'lzjlzj123',
    "db": 0,
    "decode_responses": True,
    "encoding": "utf-8"
}

BOT_NAME = 'jikescrapy'

LOG_LEVEL = 'INFO'

FEED_EXPORT_ENCODING = 'utf-8'

# DOWNLOAD_DELAY = 0.5  # 相同域名下载延时

SPIDER_MODULES = ['jikescrapy.spiders']
NEWSPIDER_MODULE = 'jikescrapy.spiders'

ROBOTSTXT_OBEY = False

DEFAULT_REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:61.0) Gecko/20100101 Firefox/61.0",
}

DOWNLOADER_MIDDLEWARES = {
   'jikescrapy.middlewares.JikescrapyDownloadMiddleware': 543,
}
