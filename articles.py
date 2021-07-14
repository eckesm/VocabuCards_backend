import feedparser
import re
import random

from sqlalchemy.sql.expression import false

RSS_NEWS_SOURCES = {
    'es': {
        'url': 'https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada',
        'source': 'El País'
    },
    'fr': {
        'url': 'https://www.lemonde.fr/rss/en_continu.xml',
        'source': 'Le Monde'
    },
    'ge': {
        'url': 'http://rss.focus.de/fol/XML/rss_folnews.xml',
        'source': 'Focus    '
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

    entriesCount = len(NewsFeed.entries)
    entryNum = random.randint(0, entriesCount)
    entry = NewsFeed.entries[entryNum]

    # print(entriesCount)
    # print(entryNum)

    # return (entry)

    if source_code == 'es':
        article = {
            'author': entry['author'],
            'link': entry['link'],
            'pubDate': entry['published'],
            'text': cleanhtml(entry['content'][1]['value']),
            'title': entry['title'],
            'fullText': False
        }
        return(article)

    if source_code == 'fr':
        article = {
            'author': RSS_NEWS_SOURCES[source_code]['source'],
            'link': entry['link'],
            'pubDate': entry['published'],
            'text': cleanhtml(entry['summary']),
            'title': entry['title'],
            'fullText': False
        }
        return(article)

    if source_code == 'ge':
        article = {
            'author': RSS_NEWS_SOURCES[source_code]['source'],
            'link': entry['link'],
            'pubDate': entry['published'],
            'text': cleanhtml(entry['content'][1]['value']),
            'title': entry['title'],
            'fullText': False
        }
        return(article)

    if source_code == 'sv':
        article = {
            'author': entry['author'],
            'link': entry['link'],
            'pubDate': entry['published'],
            'text': cleanhtml(entry['content'][0]['value']),
            'title': entry['title'],
            'fullText': True
        }
        return(article)

    else:
        return False
