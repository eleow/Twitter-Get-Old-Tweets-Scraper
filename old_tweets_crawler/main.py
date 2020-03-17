import logging
import sys
import getopt

from scraper import controllers, models


logger = logging.getLogger(__file__)
logging.basicConfig(level=logging.INFO)


def run(tweet_criteria, verbose=False):
    exporter = controllers.Exporter(filename=tweet_criteria.output_filename)
    miner = controllers.Scraper()
    results = None

    try:
        results = miner.get_tweets(tweet_criteria, buffer=exporter.output_to_file, verbose=verbose)

    except Exception as e:
        logger.exception(e)
    else:
        # text = (
        #     'Finished scraping data. Output file generated'
        #     f' "{tweet_criteria.output_filename}"'
        # )
        text = "Finished scraping data. Output file generated %s with %i %s" % (tweet_criteria.output_filename, len(results), "tweets" if len(results) > 1 else "tweet")
        logger.info(text)
    finally:
        exporter.close()


def main(argv):

    if len(argv) == 0:
        print('No arguments/parameters passed. For more information on how to'\
         'use OldTweetsScraper, you may pass "-help" as a parameter.')
        return

    if len(argv) == 1 and argv[0] == '-help':
        instructions = 'You need to include parameters when running this file.'\
                    + 'At least one of the following arguments must be used:'\
                    + '\n query: query text to search for'\
                    + '\n username: twitter username'\
                    + '\n\nThe following arguments are optional and may be '\
                    + 'passed simultaneously:'\
                    + '\n since: lower bound for the date using format '\
                    + 'YYYY-MM-DD'\
                    + '\n until: upper bound for the date using format '\
                    + 'YYYY-MM-DD'\
                    + '\n max-tweets: maximum number of tweets to retrieve '\
                    + '(default: 100)\n'
        examples = '''
        #Example 1 - Get tweets by username [barackobama] and set max tweets to 1
            python main.py --username "barackobama" --max-tweets 1\n

        #Example 2 - Get tweets by query [#marcosNotAHero]
            python main.py --query "#marcosNotAHero" --max-tweets 1\n

        #example 3 - Get tweets by query and bound dates [#BenhamRise, '2016-01-01', '2017-04-01']
            python main.py --query "#BenhamRise" --since 2016-01-01 --until 2017-04-01
        '''

        print(instructions)
        print(examples)
        return

    try:
        opts, args = getopt.getopt(argv, '', ('username=', 'since=',
                    'until=', 'query=', 'max-tweets=', 'output-file='))

        tweet_criteria = models.TweetCriteria()

        for opt, arg in opts:
            if opt == '--username':
                tweet_criteria.username = arg
            elif opt == '--since':
                tweet_criteria.since = arg
            elif opt == '--until':
                tweet_criteria.until = arg
            elif opt == '--query':
                tweet_criteria.query = arg
            elif opt == '--max-tweets':
                tweet_criteria.max_tweets = int(arg)
            elif opt == '--output-file':
                tweet_criteria.output_filename = arg

        run(tweet_criteria)

    except Exception as e:
        text = 'Unexpected error. Please try again. For more information on'\
            + ' how to use this script, use the -help argument.'
        print(text)
        print(e)


if __name__ == '__main__':
    main(sys.argv[1:])
