from crawlers.lyric_crawler import LyricCrawler
from crawlers.util.db import ORMBaseClass, engine, db_session
from sqlalchemy.exc import IntegrityError
from crawlers.model.table import (
    Chart, Artist, Song)
ORMBaseClass.metadata.drop_all(bind=engine)
ORMBaseClass.metadata.create_all(bind=engine)
if __name__ == "__main__":
    session = db_session()
    artist = 'Ed Sheeran'
    song_title = 'Thinking Out Loud'
    song_spotify_link = "https://open.spotify.com/track/0sf12qNH5qcw8qpgymFOqD"
    new_artist = Artist(artist)
    new_song = Song(song_title,song_spotify_link)
    try:
        new_artist = session.merge(new_artist)
        session.commit()
        new_song.artist_id = new_artist.id
        new_song = session.merge(new_song)
        session.commit()
        lc = LyricCrawler(artist,song_title).run().to_db(song_obj=new_song, artist_obj=new_artist, db_session=session)
        print('success!')
    except IntegrityError:
        print('owned!')