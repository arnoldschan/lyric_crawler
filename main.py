#%%
from __future__ import absolute_import
from crawlers.lyric_crawler import LyricCrawler
from crawlers.util.db import ORMBaseClass, engine, db_session
from sqlalchemy.exc import IntegrityError
from crawlers.model.table import (
    Chart, Artist, Song, Lyric)

from crawlers.spotify_crawler import SpotifyCrawler
from sqlalchemy.sql import exists
# ORMBaseClass.metadata.drop_all(bind=engine)
import time
ORMBaseClass.metadata.create_all(bind=engine)
#%%

def run():
    next_day_exists = True
    while next_day_exists:
        session = db_session()
        sc = SpotifyCrawler(date='latest')
        result = sc.run()
        result.to_db()
        songs_without_lyrics = session.query(
            Song,
            Artist.name.label('artist_name'),
            Artist.id.label('artist_id')
            ).filter(
                ~ exists().where(Song.id==Lyric.song_id)
                ).join(
                    Artist,
                    Song.artist_id == Artist.id
                ).all()

        with open('fail_links.txt','r+') as file:
            for query in songs_without_lyrics:
                print(query.artist_name)
                print(query.Song.title)
                lc = LyricCrawler(query.artist_name,query.Song.title)
                try:
                    result = lc.run()
                    result.to_db(query.Song)
                except Exception as e:
                    file.write(lc.lyric_url+'\n')
                    print(f"Fail crawl lyric: {query.Song.id}: {e}")
                time.sleep(3)
        
#%%

if __name__ == "__main__":
    run()
    # session = db_session()
    # artist = 'Ed Sheeran'
    # song_title = 'Thinking Out Loud'
    # song_spotify_link = "https://open.spotify.com/track/0sf12qNH5qcw8qpgymFOqD"
    # new_artist = Artist(artist)
    # new_song = Song(song_title,song_spotify_link)
    # try:
    #     new_artist = session.merge(new_artist)
    #     session.commit()
    #     new_song.artist_id = new_artist.id
    #     new_song = session.merge(new_song)
    #     session.commit()
    #     lc = LyricCrawler(artist,song_title).run().to_db(song_obj=new_song, artist_obj=new_artist, db_session=session)
    #     print('success!')
    # except IntegrityError:
    #     print('owned!')
#%%
# artist = "ZAYN"
# title = "I Don’t Wanna Live Forever (Fifty Shades Darker) - From Fifty Shades Darker (Original Motion Picture Soundtrack)"

# lc = LyricCrawler(artist,title)
# # %%
# lc.clean_artist