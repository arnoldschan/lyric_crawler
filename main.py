from crawlers.lyric_crawler import LyricCrawler
from crawlers.util.db import ORMBaseClass, engine, db_session
from sqlalchemy.exc import IntegrityError
from crawlers.model.table import (
    Chart, Artist, Song)
ORMBaseClass.metadata.drop_all(bind=engine)
ORMBaseClass.metadata.create_all(bind=engine)
if __name__ == "__main__":
    session = db_session()
    new_artist = Artist('Ed Sheeran')
    new_song = Song('Thinking Out Loud',"https://open.spotify.com/track/0sf12qNH5qcw8qpgymFOqD")
    try:
        new_artist = session.merge(new_artist)
        session.commit()
        new_song.artist_id = new_artist.id
        new_song = session.merge(new_song)
        session.commit()
        LyricCrawler(new_artist,new_song).crawl()
    except IntegrityError:
        print('owned!')