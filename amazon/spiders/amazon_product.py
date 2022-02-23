import scrapy
from urllib.parse import urljoin


def parse_product(response):
    all_comments = response.css(
        '#reviews-medley-footer .a-link-emphasis.a-text-bold::attr(href)').get()

    if all_comments:
        all_comments = urljoin('https://www.amazon.com/', all_comments)

    asin = response.url.split('/dp/')[1].split('/')[0]
    category = response.css(
        '.a-unordered-list.a-horizontal.a-size-small li>span>a::text').getall()
    category = [val.strip() for val in category]
    description = response.css('.aplus-v2.desktop.celwidget').xpath('//p//text()') \
        .getall()
    description = response.css('#productDescription span::text').getall() \
        if len(description) == 0 else description

    description = [
        val.strip() for val in description if
        len(val) < 10 and val != ' Click to play video '
    ]

    description = ''.join(description)

    title = response.css('#productTitle::text').get()
    title = title.strip() if title else None

    brand = response.css(
        'tr.a-spacing-small.po-brand > td:nth-child(2) > span:nth-child(1)::text').get()
    feature = response.css(
        'ul.a-unordered-list.a-vertical.a-spacing-mini li>span::text').getall()
    price = response.css('.apexPriceToPay > span:nth-child(2)::text').get()
    return {
        'asin': asin,
        'category': category,
        'description': description,
        'title': title,
        'brand': brand,
        'feature': feature,
        'price': price,
        'comment_url': all_comments,
    }


class AmazonProductSpider(scrapy.Spider):
    name = 'amazon_product'
    allowed_domains = ['amazon.com']
    custom_settings = {
        'ITEM_PIPELINES': {
            'amazon.pipelines.CommentFilePipeline': 300,
            'amazon.pipelines.MongoPipeline': 900
        }
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with open('product_url.txt', 'r') as file:
            self.start_urls = file.readlines()

    def parse(self, response, **kwargs):
        return parse_product(response)
