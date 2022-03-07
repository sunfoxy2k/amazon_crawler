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
    category = category[-1] if len(category) > 0 else ''

    total_rating = response.css(
        '.averageStarRatingNumerical .a-color-secondary::text').get().strip().replace(
        ' global ratings', '')

    total_rating = int(total_rating.replace(',', ''))
    rating = response.css('#histogramTable.a-align-center tr::attr(aria-label)').getall()
    rating = [total_rating * int(val[18:].replace('% of rating', '')) // 100 for val in
              rating]

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
    if price is not None:
        price = float(price.replace('$', ''))

    print(asin)
    return {
        'asin': asin,
        'category': category,
        'description': description,
        'title': title,
        'brand': brand,
        'feature': feature,
        'price': price,
        'comment_url': all_comments,
        'stars_5': rating[0],
        'stars_4': rating[1],
        'stars_3': rating[2],
        'stars_2': rating[3],
        'stars_1': rating[4],
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

    def __init__(self, limit, urls, **kwargs):
        self.custom_settings['DEPTH_LIMIT'] = limit
        self.start_urls = urls

        super().__init__(**kwargs)

    def parse(self, response, **kwargs):
        return parse_product(response)
