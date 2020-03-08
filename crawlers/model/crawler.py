from abc import ABCMeta, abstractmethod
from crawlers.util.connection import Connection
from bs4 import BeautifulSoup
class CrawlerBase(metaclass=ABCMeta):
    def __init__(self,url):
        self.url = url
        self.rs = Connection(self.url).rs
    @property
    def get(self):
        return self.rs.get(self.url)
    @abstractmethod
    def get_post(self):
        self.soup = BeautifulSoup(self.get.text)
        return self
    @abstractmethod
    def get_content(self):
        pass

