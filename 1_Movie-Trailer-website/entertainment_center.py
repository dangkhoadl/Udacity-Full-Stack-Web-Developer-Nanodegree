#!/usr/bin/python3
import media


# Add instances
ggCodeJam = media.Movie(
    "Google Code Jam",
    "A Google annual contest",
    "https://code.google.com/codejam/contest/static/gcj-2009-shirt-back.jpg",
    "https://www.youtube.com/watch?v=oJ_IzFsXcMo")

dota = media.Movie(
    "Dota 2",
    "an ARTS game",
    "https://pbs.twimg.com/profile_images/808475349671493632/nvi7WJf4.jpg",
    "https://www.youtube.com/watch?v=Ii_EjA7bqYw")

eg = media.Movie(
    "Evil Geniuses",
    "A story of a Dota 2 professional team",
    "http://emblemsbattlefield.com/uploads/posts/2014/10/evil-geniuses_1.jpg",
    "https://www.youtube.com/watch?v=DPhIwx6E4Wo")

navi = media.Movie(
    "Natus Vincere",
    "A story of a Dota 2 professional team",
    "http://5mid.com/wp-content/uploads/2015/10/navi.jpg",
    "https://www.youtube.com/watch?v=w8DbZoR-NM0")

cgdthw = media.Movie(
    "Co gai den tu hom qua",
    "A vietnamese movie",
    "http://hiphim.net/images/co%20gai%20den%20tu%20hom%20qua.jpg",
    "https://www.youtube.com/watch?v=hT9C_-PIgm4")

akmbcve = media.Movie(
    "Anh khong muon bat cong voi em",
    "A vietnamese music video",
    "https://i.ytimg.com/vi/ILnTPD1s7vY/maxresdefault.jpg",
    "https://www.youtube.com/watch?v=ILnTPD1s7vY")

movies = [ggCodeJam, dota, eg, navi, cgdthw, akmbcve]

# Execute
media.fresh_tomatoes.open_movies_page(movies)
