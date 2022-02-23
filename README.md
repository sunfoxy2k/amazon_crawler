#Execute script
changing the depth limit will change the amount of page will be crawl
0 = all
1 = 1 page
2 = 2 pages

## to crawl product

`scrapy crawl product_list`

this will get the url from category_list_url,

__BE CAREFUL__ this will reset the value in product_url.txt and comment_url.txt

## to crawl specific product

`scrapy crawl amazon_product`

this will get the url from product_url.txt

__BE CAREFUL__ this will reset the value in comment_url.txt

## to crawl comments

`scrapy crawl amazon_comment`

this will get the url from comment_url.txt

# get ouput locally

add this after the command
`-o "outputfilename.json"`

for example 
`scrapy crawl amazon_comment -o output.json`

__BE CAREFUL__ this will append data not reset

the actual output is in ndjson format.

#