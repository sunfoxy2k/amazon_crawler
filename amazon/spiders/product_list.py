import scrapy

from amazon.spiders.amazon_product import parse_product


class ProductSpider(scrapy.Spider):
    name = 'product_list'
    allowed_domains = ['amazon.com']
    custom_settings = {
        # 'DEPTH_LIMIT': 20,
        'ITEM_PIPELINES': {
            'amazon.pipelines.ProductPipeline' : 100,
            'amazon.pipelines.CommentFilePipeline': 300,
            'amazon.pipelines.MongoPipeline': 900
        }
    }

    def __init__(self, limit, urls, **kwargs):
        self.custom_settings['DEPTH_LIMIT'] = limit
        self.start_urls = urls

        super().__init__(**kwargs)

    def parse(self, response, **kwargs):
        product_selector = \
            'div.a-section.a-spacing-base>div.s-product-image-container>span.rush-component>a.a-link-normal.s-no-outline'
        yield from response.follow_all(css=product_selector, callback=parse_product, )

        next_page = response.css(
            'a.s-pagination-item.s-pagination-next.s-pagination-button.s-pagination-separator::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)
