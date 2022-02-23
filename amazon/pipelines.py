from itemadapter import ItemAdapter
import pymongo


class FilePipeline:
    file_name = 'default'

    def __init__(self):
        self.file = None

    def open_spider(self, spider):
        self.file = open(self.file_name, 'w')

    def process_item(self, item, spider):
        pass

    def close_spider(self, spider):
        if self.file:
            self.file.close()


class CommentFilePipeline(FilePipeline):
    file_name = 'comment_url.txt'

    def process_item(self, item, spider):
        if item['comment_url'] is not None:
            self.file.write(item['comment_url'] + '\n')

        item.pop('comment_url', None)

        return item


class ProductPipeline(FilePipeline):
    file_name = 'product_url.txt'

    def process_item(self, item, spider):
        url = 'https://www.amazon.com/dp/' + item['asin']
        self.file.write(url + '\n')

        return item


class MongoPipeline:
    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE' )
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        collection_name = 'review' if spider.name == 'amazon_comment' else 'products'

        self.db[collection_name].insert_one(ItemAdapter(item).asdict())
        return item