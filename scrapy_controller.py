from scrapy.utils.project import get_project_settings
from amazon.spiders.amazon_comment import AmazonCommentSpider
from amazon.spiders.amazon_product import AmazonProductSpider
from amazon.spiders.product_list import ProductSpider
from scrapyscript import Job, Processor


def crawl(name, limit, urls):
    if name == 'Comment':
        spider = AmazonCommentSpider
    elif name == 'Product':
        spider = AmazonProductSpider
    else:  # 'Category'
        spider = ProductSpider

    job = Job(spider, limit, urls)
    settings = get_project_settings()
    settings['DEPTH_LIMIT']=limit
    processor = Processor(settings=settings)
    return processor.run([job])

if __name__ == '__main__':
    print(crawl('amazon_comment', 1, ['https://www.amazon.com/Seagate-Portable-External-Hard-Drive/product-reviews/B07CRG94G3/ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews']))