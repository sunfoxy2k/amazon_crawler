import scrapy
from scrapy import Request


class AmazonCommentSpider(scrapy.Spider):
    name = 'amazon_comment'
    allowed_domains = ['amazon.com']
    custom_settings = {
        'DEPTH_LIMIT': 1,
        'ITEM_PIPELINES': {
            'amazon.pipelines.MongoPipeline': 900
        }
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with open('comment_url.txt', 'r') as file:
            self.start_urls = file.readlines()

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url, callback=self.parse)

    def process_review(self, review, asin):
        summary = review.css(
            '.review-title.a-color-base.review-title-content.a-text-bold span::text').get()
        content = [
            val.strip() for val in review.css(
                'span.a-size-base.review-text.review-text-content>span::text').getall()
        ]

        content = '\n'.join(content)

        reviewer = review.css('span.a-profile-name::text').get()
        rating = review.css('.a-icon-alt::text').get()[0]
        helpful = review.css('span.a-size-base.a-color-tertiary.cr-vote-text::text').get()
        if helpful:
            helpful = helpful.split(' people')[0]

        return {
            'asin': asin,
            'summary': summary,
            'content': content,
            'reviewer': reviewer,
            'rating': rating,
            'helpful': helpful,
        }

    def parse(self, response, **kwargs):
        asin = response.url.split('/product-reviews/')[1].split('/')[0]

        for review in response.css('.review-views.celwidget div.review>div.a-row'):
            yield self.process_review(review, asin)

        next_page = response.css('ul.a-pagination>li.a-last>a::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)
