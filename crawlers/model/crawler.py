from abc import ABCMeta, abstractmethod
from crawlers.util.connection import Connection
from bs4 import BeautifulSoup

class CrawlerBase(metaclass=ABCMeta):
    def __init__(self,url):
        self.url = url
        self.rs = Connection(self.url).rs
        self.results =[]

    def get(self):
        html = self.rs.get(self.url)
        self.soup = BeautifulSoup(html.text,features='html.parser')
        return html

    def get_post(self):
        
        return self

    def get_content(self):
        pass

    def _commit(self,session):
        try:
            session.commit()
            print('commit success!')
        except:
            session.rollback()
            print('rollbacked!')