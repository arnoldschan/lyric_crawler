from crawlers.lyric_crawler import LyricCrawler
def lyric_crawler():
    artist = 'Ed Sheeran'
    song_title = 'Thinking Out Loud'
    song_spotify_link = "https://open.spotify.com/track/0sf12qNH5qcw8qpgymFOqD"
    lc = LyricCrawler(artist,song_title).run()
    assert lc.status
    
def test_placeholder():
  pass
