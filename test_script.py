from crawlers.crawler_detik import CrawlerDetik
def detik_crawler_post():
    crawler = CrawlerDetik('http://www.detik.com').get_post()
    status = False
    if crawler.get == 200:
      status = True
    assert status
    
def test_placeholder():
  pass
