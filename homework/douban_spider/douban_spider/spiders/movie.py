import scrapy
from douban_spider.items import DoubanSpiderItem

class MovieSpider(scrapy.Spider):
    name = "movie"
    allowed_domains =["movie.douban.com"]
    # 修改为具体的Top250页面链接
    start_urls =["https://movie.douban.com/top250"]

    def parse(self, response):
        # 使用 Scrapy 自带的 XPath 提取节点
        movie_items = response.xpath('//div[@class="item"]')
        
        for item in movie_items:
            # 实例化刚才定义的Item对象
            douban_item = DoubanSpiderItem()
            
            # 使用 .get() 方法获取具体的文本数据
            douban_item['title'] = item.xpath('.//span[@class="title"][1]/text()').get()
            douban_item['rating'] = item.xpath('.//span[@class="rating_num"]/text()').get()
            
            # yield 抛出给引擎处理 (类似PPT第28页的数据流向)
            yield douban_item