#%%
from __future__ import absolute_import
from crawlers.model.crawler import CrawlerBase
from crawlers.model.table import (
    Chart, Artist, Song)
from crawlers.util import db
import requests
import pandas as pd
from io import StringIO
from datetime import datetime as dt, timedelta as td
from sqlalchemy.exc import IntegrityError
#%%
from collections import UserList
# ORMBaseClass.metadata.drop_all(bind=engine)
db.ORMBaseClass.metadata.create_all(bind=db.engine)
#%%

class SpotifyCrawler(CrawlerBase):
    def __init__(self,date='latest'):
        self.date = date
        self.session = db.db_session()
        super().__init__(self.spotify_url)
        self.result = SpotifyResult(self.session,self.date)
        # https://spotifycharts.com/regional/global/daily/2020-03-18/download
    
    @property
    def spotify_url(self):
        time_start_string = None
        if self.date == 'latest':
            date = self.session.query(Chart.date).order_by(Chart.date.desc()).first()
            if date is None :
                new_date = dt(year=2017,month=1,day=1)
            else:
                new_date = date.date
                new_date += td(days=1)
            time_start_string = dt.strftime(new_date,format="%Y-%m-%d")
        else:
            time_start_string = self.date
        self.date = new_date
        url = f"https://spotifycharts.com/regional/global/daily/{time_start_string}/download"
        print(f"crawling {time_start_string}")
        return url
        
    def run(self):
        html = self.get()
        # session=db_session()
        if html.status_code != 200:
            self.result.append(None)
            return self.result
        for row in html.text.split("\n")[2:]:
            attribute = row.split(',')
            if len(attribute)==5:
                this_song = {
                    'rank': int(attribute[0]),
                    'title': attribute[1].strip().replace('"',''),
                    'artist': attribute[2].strip().replace('"',''),
                    'stream': int(attribute[3]),
                    'spotify_uid': attribute[4][31:]
                }
                self.result.append(this_song)

        return self.result
#%%
class SpotifyResult(UserList):
    def __init__(self,session,date):
        self.session = session
        self.date = date
        super().__init__()
    def to_db(self):
        to_save =  []
        for song in self.data:
            if song is None:
                new_chart = Chart()
                new_chart.rank = 0
                new_chart.date = self.date
                new_chart.song_id = None
                new_chart.stream = 0
                self.session.merge(new_chart)
                self.session.commit()
                return True
            # new_artist = self.merge(Artist(song['artist']),name = song['artist'])
            new_artist = self.get_create(Artist,name = song['artist'])

            # new_song = Song(song['spotify_uid'])
            new_song = self.get_create(Song,spotify_uid = song['spotify_uid'])
            new_song.artist_id = new_artist.id
            new_song.title = song['title']
            # self.merge(new_song,spotify_uid = song['spotify_uid'])
            new_chart = Chart()
            new_chart.rank = song['rank']
            new_chart.date = self.date
            new_chart.song_id = new_song.id
            new_chart.stream = song['stream']
            self.session.merge(new_chart)
        self.session.commit()
        return True
    def get_create(self,model,**kwargs):
        return db.get_or_create_object(self.session, model,**kwargs)
#%%


if __name__ == "__main__":
    SpotifyCrawler().run().to_db()
    print('success!')