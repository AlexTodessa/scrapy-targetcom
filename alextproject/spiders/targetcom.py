import scrapy
import jmespath
import json
import re

class TargetcomSpider(scrapy.Spider):
    name = 'targetcom'
    allowed_domains = ['target.com']
    start_urls = None
    product_url = ''

    def __init__(self, *args, **kwargs):
        self.product_url = kwargs.get('url')
        super().__init__(**kwargs)
        
    def start_requests(self):
        yield scrapy.Request(self.product_url, callback=self.parse_product)

    def parse_product(self, response):        
        
        
        jsonld = json.loads(response.selector.css('script[type="application/ld+json"]::text').get())
        
        tcin = jmespath.search('"@graph"[0].sku', jsonld)
        
        api_key = re.search(r'\"apiKey\"\:\"(.*?)\"', response.text).group(1)
        pricing_store_id = re.search(r'\"pricing_store_id\"\:\"(\d+)\"', response.text).group(1)
        

        pdp_url = (
            f'https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1?key={api_key}&tcin={tcin}'
            f'&store_id=none&has_store_id=false&pricing_store_id={pricing_store_id}'
            '&scheduled_delivery_store_id=none&has_scheduled_delivery_store_id=false'
            '&has_financing_options=false'
            )
        
        return [scrapy.Request(pdp_url, callback=self.parse_pricing, cb_kwargs=dict(
            main_url = response.url, product_response = response, jsonld = jsonld
        ))]
    
    def parse_pricing(self, response, main_url, jsonld, product_response):
        
        data = json.loads(response.text);
        
        bullets = jmespath.search('data.product.item.product_description.bullet_descriptions', data)
        bulletsList = {}
        
        for bullet in bullets:
            b = re.match(r'<B>(.*?)\:</B> (.*)', bullet)
            bulletsList[b.group(1)] = b.group(2)
            
        return {
                'url': main_url,
                'tcin': jmespath.search('"@graph"[0].sku', jsonld),
                'upc': jmespath.search('"@graph"[0].gtin13', jsonld),
                'price': jmespath.search('data.product.price.current_retail_min', data),
                'currency': jmespath.search('"@graph"[0].offers.priceCurrency', jsonld),
                'title': product_response.selector.css('h1[itemprop="name"] span::text').get(),
                'description': jmespath.search('"@graph"[0].description', jsonld),
                'specs': bulletsList
            }