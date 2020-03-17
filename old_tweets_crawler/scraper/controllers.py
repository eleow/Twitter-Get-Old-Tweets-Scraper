import logging

import csv
import re
import urllib.parse
import requests as req
from datetime import datetime
from pyquery import PyQuery as pq

from .models import Tweet
from .exceptions import ScrapperException


logger = logging.getLogger(__file__)
logging.basicConfig(level=logging.INFO)


class Exporter(object):

    def __init__(self, criteria=None, filename='tweets_gathered.csv'):
        if criteria and criteria.output_filename:
            filename = criteria.output_filename
        self.filename = filename

        self.output = open(self.filename, 'w+', encoding='utf-8', newline='\n')
        self.csv_writter = csv.writer(
            self.output, delimiter=',', quotechar='"')
        if not criteria:
            criteria = [
                'username', 'user_handle', 'date', 'retweets',
                'favorites', 'text', 'language', 'geological_location',
                'mentions', 'hashtags', 'tweet_id', 'permalink'
            ]

        # criteria_string = ','.join(criteria)
        self.csv_writter.writerow(criteria)

    def output_to_file(self, tweets):
        for tweet in tweets:
            self.csv_writter.writerow([
                tweet.user,
                tweet.user_handle,
                tweet.date_fromtimestamp.strftime('%Y-%m-%d %H:%M'),
                tweet.retweets,
                tweet.favorites,
                tweet.text,
                tweet.lang,
                tweet.geological_location,
                tweet.mentions,
                tweet.hashtags,
                tweet.id,
                tweet.permalink
            ])

        self.output.flush()
        print('%d tweets added to file' % len(tweets))

    def close(self):
        self.output.close()


class Scraper(object):

    def __init__(self):
        pass

    @staticmethod
    def set_headers(data, language, refresh_cursor):
        url = 'https://twitter.com/i/search/timeline?f=realtime&q=%s&src=typd'
        if language:
            url += f'&{language}'
        else:
            url += '&'
        url += 'max_position=%s'
        url = url % (urllib.parse.quote(data), refresh_cursor)
        headers = {
            'Host': 'twitter.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': url,
            'Connection': 'keep-alive'
        }

        return url, headers

    @staticmethod
    def get_tweets(tweet_criteria, buffer=None, buffer_length=100, verbose=False):
        active = True
        refresh_cursor = ''
        mentions = re.compile('(@\\w*)')
        hashtags = re.compile('(#\\w*)')
        results = []
        results_to_append = []

        if tweet_criteria.max_tweets <= 0:
            return

        while active:
            json = Scraper.get_json_response(
                tweet_criteria, refresh_cursor, verbose)

            if 'items_html' not in json:
                # Sorry, die Anzahl deiner Anfragen ist begrenzt
                # Sorry, the number of your requests is limited
                print(json['message'])
                break

            if not json or len(json['items_html'].strip()) == 0:
                break

            refresh_cursor = json['min_position']
            tweets = pq(json['items_html'])('div .js-stream-tweet')

            if len(tweets) == 0:
                break

            for tweetHTML in tweets:
                _ = pq(tweetHTML)

                tweet_id = _.attr('data-tweet-id')
                user_id = _.attr('data-user-id')
                user_handle = _.attr('data-screen-name')
                username = _.attr('data-name')

                # quick-fix: remove html tags manually instead of using .text() because some tags are replaced with \n
                text = re.sub('http', ' http', _('p.js-tweet-text').html())  # add spacing before an URL
                text = re.sub(r'<.*?>', '', text)
                # text = re.sub(r'<.*?>', '', _('p.js-tweet-text').html())
                # text = re.sub(r'\s+', ' ', _('p.js-tweet-text').text()
                #               .replace('# ', '#').replace('@ ', '@'))
                retweet_id = 'span.ProfileTweet-action--retweet '\
                    + 'span.ProfileTweet-actionCount'
                retweets = int(_(retweet_id).attr('data-tweet-stat-count')
                               .replace(',', ''))
                favorites_id = 'span.ProfileTweet-action--favorite '\
                    + 'span.ProfileTweet-actionCount'
                favorites = int(_(favorites_id).attr('data-tweet-stat-count')
                                .replace(',', ''))
                href = 'https://twitter.com' + _.attr('data-permalink-path')
                raw_date_ms = int(_('span.js-short-timestamp')
                                  .attr('data-time'))
                lang = _('p.js-tweet-text').attr('lang') or ''
                tweet_date = _('span._timestamp .js-short-timestamp').text()
                geological_location = _('span.Tweet-geo').attr('title')\
                    if len(_('span.Tweet-geo')) > 0 else ''

                urls = []
                for link in _('a'):
                    try:
                        urls.append(link.attrib['data-expanded-url'])
                    except Exception:
                        pass

                tweet = Tweet()
                tweet.id = tweet_id
                tweet.user_id = user_id
                tweet.user = username
                tweet.user_handle = user_handle
                tweet.text = text
                tweet.lang = lang
                tweet.date = tweet_date
                tweet.raw_date_ms = raw_date_ms
                tweet.date_fromtimestamp = datetime.fromtimestamp(raw_date_ms)
                tweet.formatted_raw_date = datetime.fromtimestamp(raw_date_ms)\
                    .strftime('%a %b %d %X +0000 %Y')
                tweet.permalink = href
                tweet.retweets = retweets
                tweet.favorites = favorites
                tweet.geological_location = geological_location
                tweet.urls = ','.join(urls)
                tweet.mentions = ' '.join(mentions.findall(tweet.text))
                tweet.hashtags = ' '.join(hashtags.findall(tweet.text))

                results.append(tweet)
                results_to_append.append(tweet)

                if buffer and len(results_to_append) >= buffer_length:
                    buffer(results_to_append)
                    results_to_append = []

                if len(results) >= tweet_criteria.max_tweets:
                    active = False
                    break

        if buffer and len(results_to_append) > 0:
            buffer(results_to_append)

        print("Total results: %s" % len(results))
        return results

    @staticmethod
    def get_json_response(tweet_criteria, refresh_cursor, verbose=False):
        data = ''

        if hasattr(tweet_criteria, 'username'):
            data += ' from:' + tweet_criteria.username

        if hasattr(tweet_criteria, 'since'):
            data += ' since:' + tweet_criteria.since

        if hasattr(tweet_criteria, 'until'):
            data += ' until:' + tweet_criteria.until

        if hasattr(tweet_criteria, 'query'):
            data += ' ' + tweet_criteria.query
        else:
            print('No query placed.')
            return

        language = None
        if hasattr(tweet_criteria, 'language'):
            language = 'lang=' + tweet_criteria.language + '&'
        # else:
        #     language = 'lang=en-US&'

        url, headers = Scraper.set_headers(data, language, refresh_cursor)

        try:
            if verbose:
                logger.info(f'get: {url} / headers: {headers}')
            res = req.get(url, headers=headers)
        except Exception as e:
            logger.exception(e)
            text = ('Twitter weird response. Try to see on browser:'
                    ' f{url}')
            logger.error(text)
            logger.error(f'stoped in {refresh_cursor}')
            raise ScrapperException(e)
        return res.json()
