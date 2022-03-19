import scrapy
import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup


def parse_product(self,response):
    all_comments = response.css(
        '#reviews-medley-footer .a-link-emphasis.a-text-bold::attr(href)').get()

    if all_comments:
        all_comments = urljoin('https://www.amazon.com/', all_comments)

    if '/dp/' in response.url:
        asin = response.url.split('/dp/')[1].split('/')[0]
    elif '/gp/product/' in response.url:
        asin = response.url.split('/gp/product/')[1].split('/')[0]
    else:
        asin = None

    category = response.css(
        '.a-unordered-list.a-horizontal.a-size-small li>span>a::text').getall()
    category = [val.strip() for val in category]
    category = category[-1] if len(category) > 0 else ''
    from scrapy.shell import inspect_response
    inspect_response(response, self)
    total_rating = response.css(
        '.averageStarRatingNumerical .a-color-secondary::text').get().strip().replace(
        ' global ratings', '')

    total_rating = int(total_rating.replace(',', ''))
    rating = response.css('#histogramTable.a-align-center tr::attr(aria-label)').getall()
    rating = [total_rating * int(val[18:].replace('% of rating', '')) // 100 for val in
              rating]

    description = response.css('#productDescription > p::text').get()

    title = response.css('#productTitle::text').get()
    title = title.strip() if title else None

    brand = response.css(
        'tr.a-spacing-small.po-brand > td:nth-child(2) > span:nth-child(1)::text').get()
    feature = response.css(
        'ul.a-unordered-list.a-vertical.a-spacing-mini li>span::text').getall()
    price = response.css('.apexPriceToPay > span:nth-child(2)::text').get()
    if price is not None:
        price = float(price.replace('$', ''))

    overall_rating = response.css('#reviewsMedley .a-size-medium::text').extract_first()
    overall_rating = overall_rating.split()[0]

    star_rating_list = response.css('#histogramTable .a-link-normal::text').extract()
    star_rating = {}
    star_rating_list = list(map(lambda k: k.strip(), star_rating_list))
    star_rating_list = list(filter(None, star_rating_list))
    for i in range(len(star_rating_list)):
        if i % 2 == 1:
            continue
        star_rating[star_rating_list[i]] = star_rating_list[i + 1]
    for i in range(5, 0, -1):
        if star_rating.get(str(i) + " star", None) == None:
            star_rating[str(i) + " star"] = "0%"
    star_rating = dict(sorted(star_rating.items()))


    data = {
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
        'global_rating': total_rating,
        'overall_rating': overall_rating,
        'star_rating': star_rating,
    }

    if asin != None:
        url = "https://www.amazon.com/hz/reviews-render/ajax/lazy-widgets/stream?asin=" + asin + "&language=en_US&lazyWidget=cr-summarization-attributes"
        yield scrapy.Request(
        url,
        meta={'data': data},
            callback=self.parse_feature_rating
    )
    else:
        yield data

class AmazonProductSpider(scrapy.Spider):
    name = 'amazon_product'
    allowed_domains = ['amazon.com']
    custom_settings = {
        'ITEM_PIPELINES': {
            'amazon.pipelines.CommentFilePipeline': 300,
            'amazon.pipelines.MongoPipeline': 900
        }
    }

    def __init__(self, limit=1, urls=['https://www.amazon.com/gp/product/B08Y9891ZD/ref=ox_sc_saved_image_8?smid=ATVPDKIKX0DER&psc=1'], **kwargs):
        self.custom_settings['DEPTH_LIMIT'] = limit
        self.start_urls = urls

        super().__init__(**kwargs)

    def parse(self, response, **kwargs):
        return parse_product(self,response)

    def parse_feature_rating(self, response):
        data = response.meta.get('data')
        html_text = response.body.decode('utf-8').replace('"', '').replace("\\n", "").replace("\\", "").split(',')
        soup = BeautifulSoup(html_text[2], 'html.parser')
        feature_list = soup.find_all(id=re.compile("cr-summarization-attribute-attr-"))
        rating = {}
        for i in range(len(feature_list)):
            feature_set = feature_list[i].find_all("span", {"class": "a-size-base"})
            rating[feature_set[0].text] = feature_set[1].text
        data["feature_rating"] = rating
        yield data