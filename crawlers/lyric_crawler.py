from __future__ import absolute_import
import requests
from urllib.parse import quote
import pandas as pd
from io import StringIO
from unidecode import unidecode
import re
import dateparser
import json
from crawlers.util.db import db_session
from crawlers.model.crawler import CrawlerBase
from crawlers.model.table import (
    Chart, Artist, Song, Lyric, Album, Writer, SongWriterMap, Distributor, SongDistributorMap, Label, SongLabelMap)
from crawlers.util.db import engine
#%%
from collections import UserDict
#%%
# ORMBaseClass.metadata.drop_all(bind=engine)
# ORMBaseClass.metadata.create_all(bind=engine)
class LyricCrawler(CrawlerBase):
    def __init__(self,artist_name,song_title)    :
        """Crawling Lyric from www.genius.com
        Default input from Spotify's data
        However, if the crawler couldn't find the default lyric,
        it would fetch lyric from the first search result
        in genius.
        Parameter:
        :artist_name: singer name
        :song_title: title of the song"""
        self.artist_name = artist_name
        self.song_title = song_title
        self.album = None
        self.writer = None
        self.distributor = None
        self.label = None
        self.lyric = None
        self.release_date = None
        self.session = db_session()
        self.result = LyricResult(self.session)
        super().__init__(self.lyric_url)

    @property
    def lyric_url(self):
        """generate the default form of lyric's link"""
        def combine_with_dash(text_input,first_cap=True):
            def remove_symbol(word):
                symbols = ["'",'"',"/",".",",","?","!","`","’"]
                for symbol in symbols:
                    word = word.replace(symbol,'')
                return word
            result = ""
            list_ = text_input.split()
            if first_cap:
                result += remove_symbol(list_[0].capitalize())
                list_.pop(0)
            for member in list_:
                result+="-"+ remove_symbol(member.lower())
            return result
        self.clean_artist = self.clean_text(self.artist_name)
        self.clean_title = self.clean_text(self.song_title)
        artist_coded = combine_with_dash(self.clean_artist)
        track_name_coded = combine_with_dash(self.clean_title,False)
        artist_and_track = artist_coded + track_name_coded
        return unidecode("https://genius.com/" + artist_and_track +"-"+"lyrics")
    def clean_text(self,text_input):
        def clean_with_regex(text,pattern):
            result = [text.replace(match,'') for match in re.findall(pattern,text)]
            if result == []:
                return text
            else:
                return result[0].strip()
        def replace_with_other(text):
            to_replace = {'$':'-', "&":'and', }
            for key,value in to_replace.items():
                text = text.replace(key,value)
            return text
        regex = ["\(.*\)","-.*?$"]
        for pattern in regex:
            text_input = clean_with_regex(text_input,pattern)
        text_input = replace_with_other(text_input)
        return text_input
            
    @property
    def fallback_url(self):
        """if the default url couldn't be found, it'll use search result"""
        combine = self.clean_title + " "+ self.clean_artist
        combine = combine.replace(" ","+")
        # return unidecode("https://genius.com/search?q="+quote(combine))
        return f"https://genius.com/api/search/multi?per_page=5&q={combine}"

    def get_soup(self):
        print(f"\nurl : {self.lyric_url}")
        response = self.get()
        if response.status_code != 200:
            self.url = self.fallback_url
            print(f"{self.url}")
            try:
                html = self.get()
                if html.status_code != 200:
                    print("FALLBACK NOT FOUND")
                for hits in json.loads(html.text)['response']['sections'][0]['hits']:
                    if hits['type'] == 'song':
                        self.url = hits['result']['url']
            except Exception as e:
                return False
            print(f"crawling to this link {self.url}")
            response = self.get()
            if response.status_code != 200:
                print("SEARCH NOT FOUND")
                return False
        return True

    def run(self):
        """get, and save the information in self.result
        
        Returns:
            [self] -- [LyricCrawler object]
        """        
        #do the request
        response =self.get_soup()
        if response is not True:
            raise Exception("Date not found! ")
        paragraph = self.soup.find('div',class_="lyrics").find('p')
        [ads.extract() for ads in paragraph.find_all('defer-compile')];

        # saving lyric and album
        self.lyric = paragraph.text.strip().replace('\u2005',' ')
        album_soup = self.soup.find(text="Album")
        if album_soup is not None:
            self.album = album_soup.parent.nextSibling.nextSibling.text.strip()
        else:
            pass
        content_info = self.soup.find('div',{"initial-content-for":"track_info"})
        writer_soup = content_info.find(text="Written By")

        # saving song writer
        if writer_soup is not None:
            writers = writer_soup.parent.nextSibling.nextSibling.text.strip()
            self.writer = []
            for writer in writers.replace('&',',').split(","):
                self.writer.append(writer)
        else:
            # print(f'writer not found for: {self.artist_name}-{self.song_title}')
            pass
        
        # save song's distributor
        distributor_soup = content_info.find(text="Distributor")
        if distributor_soup is not None:
            self.distributor = distributor_soup.parent.nextSibling.nextSibling.text.strip()
        else:
            # print(f'distributor not found for: {self.artist_name}-{self.song_title}')
            pass
        # save song's label
        label_soup = content_info.find(text="Label")
        if label_soup is not None:
            self.label = label_soup.parent.nextSibling.nextSibling.text.strip()
        else:
            # print(f'label not found for: {self.artist_name}-{self.song_title}')
            pass
        # save song's release date
        release_date_soup = content_info.find(text="Release Date")
        if release_date_soup is not None:
            self.release_date = dateparser.parse(release_date_soup.parent.nextSibling.nextSibling.text.strip())
        else:
            # print(f'release date not found for: {self.artist_name}-{self.song_title}')
            pass
        self.result.update({"artist_name": self.artist_name,
                "song_title": self.song_title,
                "album": self.album,
                "writer": self.writer,
                "distributor": self.distributor,
                "label": self.label,
                "lyric": self.lyric,
                "release_date": self.release_date
                })
        self.status = True
        return self.result
#%%
class LyricResult(UserDict):
    def __init__(self,session):
        self.session = session
        super().__init__()
    def to_db(self,song_obj):
        """Saving information to database
        
        Arguments:
            song_obj {[Song]} -- [needed to update the song object]
            db_session {[mysqlalchemy.session]} -- [SQL session engine connector]
        """        
        # write lyric
        new_lyric = Lyric(song_obj.id,self.data['lyric'])
        self.session.merge(new_lyric)

        # write album
        new_album = Album(self.data['album'])
        new_album.song_id = song_obj.id
        new_album.artist_id = song_obj.artist_id
        self.session.merge(new_album)

        # write writer
        if isinstance(self.data['writer'], str):
            self.data['writer'] = list(self.data['writer'])
        if isinstance(self.data['writer'], list):
            for writer in self.data['writer']:
                new_writer = Writer(writer)
                new_writer = self.session.merge(new_writer)
                self.session.commit()
                new_songwriter_map = SongWriterMap(song_obj.id,new_writer.id)
                self.session.merge(new_songwriter_map)

        # distributor
        if self.data['distributor'] is not None:
            new_distributor = Distributor(self.data['distributor'])
            new_distributor = self.session.merge(new_distributor)
            self.session.commit()

        # label
        if self.data['label'] is not None:
            new_label = Label(self.data['label'])
            new_label = self.session.merge(new_label)
            self.session.commit()

        # add attribute in song obj
        if self.data['label'] is not None:
            song_obj.label_id = new_label.id
        if self.data['distributor'] is not None:
            song_obj.distributor_id = new_distributor.id
        song_obj.release_date = self.data['release_date']
        self.session.commit()

        return True

# %%
