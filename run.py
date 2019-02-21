# coding: utf-8
from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerProcess
from jikescrapy.spiders.jike import JikeSpider
from jikescrapy.spiders.jike_fan import JikeFanSpider


if __name__ == '__main__':
    process = CrawlerProcess(settings=get_project_settings())
    process.crawl(JikeSpider)

    process.crawl(JikeFanSpider)
    process.start()