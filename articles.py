import feedparser
import re
import random
from models import Article

from sqlalchemy.sql.expression import false, true

# uses http://www.wmutils.com/fulltextrss/ for processing full text rss

RSS_NEWS_SOURCES = {
    'de': {
        # 'url': 'http://rss.focus.de/fol/XML/rss_folnews.xml',
        'url': 'http://www.wmutils.com/fulltextrss/makefulltextfeed.php?url=http%3A%2F%2Frss.focus.de%2Ffol%2FXML%2Frss_folnews.xml&max=25&links=preserve&exc=',
        'source': 'Focus'
    },
    'es': {
        # 'url': 'https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada',
        'url': 'http://www.wmutils.com/fulltextrss/makefulltextfeed.php?url=https%3A%2F%2Ffeeds.elpais.com%2Fmrss-s%2Fpages%2Fep%2Fsite%2Felpais.com%2Fportada&max=25&links=preserve&exc=',
        'source': 'El País'
    },
    'fr': {
        # 'url': 'https://www.lemonde.fr/rss/en_continu.xml',
        'url': 'http://www.wmutils.com/fulltextrss/makefulltextfeed.php?url=https%3A%2F%2Fwww.lemonde.fr%2Frss%2Fen_continu.xml&max=25&links=preserve&exc=',
        'source': 'Le Monde'
    },
    'it': {
        # 'url': 'https://www.ansa.it/sito/ansait_rss.xml',
        'url': 'http://www.wmutils.com/fulltextrss/makefulltextfeed.php?url=https%3A%2F%2Fwww.ansa.it%2Fsito%2Fansait_rss.xml&max=25&links=preserve&exc=',
        'source': 'ANSA.it'
    },
    'sv': {
        'url': 'https://api.sr.se/api/rss/program/4916',
        # 'source': 'Radio Sweden på lätt svenska'
        'source': 'Radio Sweden'
    }
}


def cleanhtml(raw_html):
    cleanr = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext


def getArticleFromRSS(source_code):

    url = RSS_NEWS_SOURCES[source_code]['url']
    NewsFeed = feedparser.parse(url)

    # print('NewsFeed', NewsFeed)

    entriesCount = len(NewsFeed.entries)
    entryNum = random.randint(0, entriesCount-1)
    # print(entriesCount)
    # print(entryNum)
    entry = NewsFeed.entries[entryNum]

    # print(f"{entryNum} / {entriesCount}")

    if "author" in entry.keys():
        author = entry['author']
    else:
        author = RSS_NEWS_SOURCES[source_code]['source']

    if source_code == 'de':
        article = {
            'author': author,
            'url': entry['link'],
            'publication_date': entry['published'],
            'text': cleanhtml(entry['summary']),
            'title': entry['title'],
            'full_text': True,
            'publication': 'Focus',
            'language': 'de'
        }
        if Article.get_by_url(article['url']) == None:
            new_article = Article.add_article(article)
            print(new_article)

        return(article)

    if source_code == 'es':
        article = {
            'author': author,
            'url': entry['link'],
            'publication_date': entry['published'],
            'text': cleanhtml(entry['summary']),
            'title': entry['title'],
            'full_text': True,
            'publication': 'El País',
            'language': 'es'
        }
        if Article.get_by_url(article['url']) == None:
            new_article = Article.add_article(article)
            print(new_article)

        return(article)

    if source_code == 'fr':
        article = {
            'author': author,
            'url': entry['link'],
            'publication_date': entry['published'],
            'text': cleanhtml(entry['summary']),
            'title': entry['title'],
            'full_text': False,
            'publication': 'Le Monde',
            'language': 'fr'
        }
        if Article.get_by_url(article['url']) == None:
            new_article = Article.add_article(article)
            print(new_article)

        return(article)

    if source_code == 'it':
        article = {
            'author': author,
            'url': entry['link'],
            'publication_date': entry['published'],
            'text': cleanhtml(entry['summary']),
            'title': entry['title'],
            'full_text': True,
            'publication': 'ANSA.it',
            'language': 'it'
        }
        if Article.get_by_url(article['url']) == None:
            new_article = Article.add_article(article)
            print(new_article)

        return(article)

    if source_code == 'sv':
        article = {
            'author': author,
            'url': entry['link'],
            'publication_date': entry['published'],
            'text': cleanhtml(entry['content'][0]['value']),
            'title': entry['title'],
            'full_text': True,
            'publication': 'Radio Sweden på lätt svenska',
            'language': 'sv'
        }
        if Article.get_by_url(article['url']) == None:
            new_article = Article.add_article(article)
            print(new_article)

        return(article)

    else:
        return False
