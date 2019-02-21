# -*- coding: utf-8 -*-

import scrapy


class JikescrapyItem(scrapy.Item):
    username = scrapy.Field()
    screenName = scrapy.Field()
    createdAt = scrapy.Field()
    updatedAt = scrapy.Field()
    isVerified = scrapy.Field()
    verifyMessage = scrapy.Field()
    briefIntro = scrapy.Field()
    gender = scrapy.Field()
