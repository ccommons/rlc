#!/usr/bin/env python

import sys
sys.path.append("/home/www/rlc")

import rlc.settings
from django.core.management import setup_environ
setup_environ(rlc.settings)

# note: not python 3 compatible (yet)
import urllib2

import xml.etree.ElementTree as ElementTree
import datetime
import re

from django.contrib.auth.models import User
from er.models import NewsItem, NewsTag
from annotation import comment

feed_url = 'http://www.cancercommons.org/feed/?tag=melanoma%20rc'

response = urllib2.urlopen(feed_url)
data = response.read().strip()

root = ElementTree.fromstring(data)

news_user = User.objects.get(username="news")

for article in root.iter('item'):
    # TODO: catch exceptions

    # url
    url = article.find('link').text
    try:
        existing_item = NewsItem.objects.get(url=url)
        # matching URL, skip to next iteration
        # TODO: look for changes and save them
        print("got existing: {0}".format(url))
        continue
    except NewsItem.DoesNotExist:
        print("new: {0}".format(url))
        pass

    # title
    title = article.find('title').text

    # tags
    tags = []
    for tag in article.iter('category'):
        tags.append(tag.text)

    # summary
    summary = article.find('description').text

    # pubdate
    pubdate = article.find('pubDate')
    # for some reason, the TZ offset isn't supported universally
    pubdate_no_offset = re.sub(r' \+0000$', '', pubdate.text)
    d = datetime.datetime.strptime(pubdate_no_offset, "%a, %d %b %Y %H:%M:%S")

    # set up comment root
    c = comment(text="all comments for " + url, user=news_user)

    # set up and save the object
    news_item = NewsItem(
        title=title,
        url=url,
        preview=summary,
        comments=c.model_object,
        pubdate=d,
        authorjournal="stand-in for author/journal info",
    )

    news_item.save()

    # set up tags
    for tag in tags:
        tag_o = None
        try:
            tag_o = NewsTag.objects.get(tag_value=tag)
        except NewsTag.DoesNotExist:
            tag_o = NewsTag(tag_value=tag)
            tag_o.save()
        except NewsTag.MultipleObjectsReturned:
            # TODO: report this error
            tag_o = None

        if tag_o != None:
            tag_o.news_items.add(news_item)
            tag_o.save()

