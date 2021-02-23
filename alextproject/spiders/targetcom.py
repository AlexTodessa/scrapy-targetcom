import scrapy
import json
import urllib
from w3lib.html import remove_tags
import re

class TargetcomSpider(scrapy.Spider):
    name = 'targetcom'
    allowed_domains = ['target.com']
    start_urls = ['https://www.target.com/']

    def parse(self, response):        
        
        
        jsonld = json.loads(response.selector.css('script[type="application/ld+json"]::text').get())
        tcin = remove_tags(jsonld["@graph"][0]["sku"])
        upc = remove_tags(jsonld["@graph"][0]["gtin13"])
        
        apiKey = re.search(r'\"apiKey\"\:\"(.*?)\"', response.text).group(1)
        pricingStoreId = re.search(r'\"pricing_store_id\"\:\"(\d+)\"', response.text).group(1)
        

        pdpUrl = f'https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1?key={apiKey}&tcin={tcin}'
        pdpUrl = pdpUrl + f'&store_id=none&has_store_id=false&pricing_store_id={pricingStoreId}'
        pdpUrl = pdpUrl + '&scheduled_delivery_store_id=none&has_scheduled_delivery_store_id=false'
        pdpUrl = pdpUrl + '&has_financing_options=false'
        
        
        with urllib.request.urlopen(pdpUrl) as url:
            data = json.loads(url.read().decode())
        
        price = data["data"]["product"]["price"]["current_retail_min"]
        
        bullets = data["data"]["product"]["item"]["product_description"]["bullet_descriptions"]
        
        bulletsList = {}
        for bullet in bullets:
            b = re.match(r'<B>(.*?)\:</B> (.*)', bullet)
            bulletsList[b.group(1)] = b.group(2)
        
        #https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1
        #?key=ff457966e64d5e877fdbad070f276d18ecec4a01
        #&tcin=81204099
        #&store_id=none
        #&has_store_id=false
        #&pricing_store_id=3991
        #&scheduled_delivery_store_id=none
        #&has_scheduled_delivery_store_id=false
        #&has_financing_options=false
        
        return {
                'url': response.url,
                'title': response.selector.css('h1[itemprop="name"] span::text').get(),                
                'description': remove_tags(jsonld["@graph"][0]["description"]),
                'tcin': tcin,
                'upc': upc,
                'price': price,
                'currency': remove_tags(jsonld["@graph"][0]["offers"]["priceCurrency"]),
                'specs': bulletsList
            }
