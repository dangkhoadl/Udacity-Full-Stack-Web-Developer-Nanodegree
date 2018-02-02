import fresh_tomatoes


class Movie():
    """ Documentations:
        This is the class to store movie attributes:
        movie titles, box art, poster images, and movie trailer URLs"""

    # Constructor
    def __init__(self,
                 movie_title,
                 movie_storyline,
                 poster_image,
                 trailer_youtube):
        self.title = movie_title
        self.storyline = movie_storyline
        self.poster_image_url = poster_image
        self.trailer_youtube_url = trailer_youtube

    # show the trailer of the movie on youtube
    def showTrailer(self):
        webbrowser.open(self.trailer_youtube_url)
