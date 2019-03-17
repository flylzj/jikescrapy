# -*- coding: utf-8 -*-

import scrapy


class JikeUserItem(scrapy.Item):
    bio = scrapy.Field()
    briefIntro = scrapy.Field()
    city = scrapy.Field()
    country = scrapy.Field()
    createdAt = scrapy.Field()
    following = scrapy.Field()
    gender = scrapy.Field()
    isVerified = scrapy.Field()
    profileImageUrl = scrapy.Field()
    province = scrapy.Field()
    ref = scrapy.Field()
    screenName = scrapy.Field()
    updatedAt = scrapy.Field()
    username = scrapy.Field()
    verifyMessage = scrapy.Field()
    follow_key = scrapy.Field()
