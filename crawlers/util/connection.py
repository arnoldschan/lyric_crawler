import requests

class Connection():
    def __init__(self, url, headers={}, cookies={}):
        self.rs = requests.session()
        self.url = url
        self.headers = headers
        self.cookies = cookies
        self.status_code = None
    def get(self):
        try:
            res = self.rs.get(self.url, headers=self.headers, cookies=self.cookies, timeout=10)
            if res.status_code == 200:
                self.status_code = 200
                return res.text
            else:
                self.status_code = res.status_code
                return False
        except Exception as e:
            print(str(e))
            return False

class GeneralRequest(Connection):
    def __init__(self, url):
        headers = {"User-Agent": 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:51.0) Gecko/20100101 Firefox/51.0'}
        super().__init__(url, headers=headers)

# %%
