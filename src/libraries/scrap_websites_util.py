import time
import requests
from datetime import datetime, timedelta

from twython import TwythonError
from pprint import pprint
from dataclasses import dataclass

how_many_tweets = 5


# scraps /biz/ and returns a list of tuple (threadId, body, title) of threads matching the regex ^rot |rot$| rot |rotten|rotting
def get_biz_threads(re_4chan):
    url = 'https://a.4cdn.org/biz/catalog.json'
    response_json = requests.get(url).json()
    threads_ids = []
    for page in response_json:
        for thread in page['threads']:
            try:
                if 'com' in thread:
                    com = thread['com']
                else:
                    com = ""
                if 'sub' in thread:
                    sub = thread['sub']
                else:
                    sub = ""
            except KeyError:
                print("ERROR")
                pass
            else:
                if re_4chan.search(com) or re_4chan.search(sub):
                    thread_id = thread['no']
                    threads_ids.append((thread_id, com, sub))
    return threads_ids


@dataclass(frozen=True)
class TweetReceived:
    message: str
    creation_date: datetime
    user: str
    tweet_id: str

    def minutes_since(self, current_time=datetime.utcnow()):
        diff_time = current_time - self.creation_date
        return int(diff_time.total_seconds() / 60)

    def tweet_url(self):
        return "twitter.com/anyuser/status/" + self.tweet_id

    def to_string(self):
        return "<a href=\"" + self.tweet_url() + "\"><b>" + str(self.minutes_since()) + \
        " mins ago</b> | " + self.user + "</a> -- " + self.message + "\n"


def parse_tweet(tweet_raw):
    tweet_id = tweet_raw['id_str']
    message = tweet_raw['text'].replace("\n", "").split('https')[0].replace('#', '').replace('@', '')

    time_tweet_creation = tweet_raw['created_at']
    user = tweet_raw['user']['screen_name']
    tweet_raw = TweetReceived(message=message,
                              creation_date=time_tweet_creation,
                              user=user,
                              tweet_id=tweet_id)
    return tweet_raw


def get_last_tweets(twitter, ticker, minutes_since=10000000):
    if ticker[0] == "@":
        message = '<b>Last tweets by <a href="twitter.com/' + ticker + '">' + ticker[1:] + "</a>:</b>\n"
        try:
            results = query_tweets(twitter, ticker[1:], True)
        except TwythonError:
            time.sleep(0.5)
            results = query_tweets(twitter, ticker[1:], True)
        parsed_tweets = []
        for tweet in results:
            parsed_tweets.append(parse_tweet(tweet))
        tweets_to_keep = [x.to_string() for x in parsed_tweets if x.minutes_since() < minutes_since]
        return message + ''.join(tweets_to_keep)
    else:
        try:
            results = query_tweets(twitter, ticker)
        except TwythonError:
            time.sleep(0.5)
            results = query_tweets(twitter, ticker)
        message = "<b>Last tweets for " + ticker.upper() + ":</b>\n"
        parsed_tweets = []
        for tweet in results:
            parsed_tweets.append(parse_tweet(tweet))
        tweets_to_keep = [x.to_string() for x in parsed_tweets if x.minutes_since() < minutes_since]
        rest_message = ''.join(tweets_to_keep)
        if rest_message == "":
            print("empty tweets, fallback")
            rest_message = "Unable to find tweets right now."
        return message + rest_message


def filter_tweets(all_tweets):
    message = ""
    if all_tweets.get('statuses'):
        count = 0
        tweets = all_tweets['statuses']
        for tweet in tweets:
            if "RT " not in tweet['text']:
                if count < how_many_tweets:
                    message = message + parse_tweet(tweet)
                    count = count + 1
    return message


def query_tweets(twitter, token, is_user: bool = False):
    if is_user:  # actually searching for a user
        print("showing user tweets: " + token)
        tweets = twitter.get_user_timeline(screen_name=token, count=how_many_tweets)
        return tweets
        # return twitter.show_user(screen_name=token[1:])
    else:
        return twitter.search(q='$' + token)

