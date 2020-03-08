from crawlers.model.crawler import CrawlerBase
class CrawlerDetik(CrawlerBase):
    def __init__(self,url):
        super().__init__(url)
    def get_post(self):
        return True
    def get_content(self):
        pass
if __name__ == "__main__":
    crawler= CrawlerDetik('http://www.detik.com').get_post()
    soup = crawler.soup
    print(html)