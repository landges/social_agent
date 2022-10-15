import json

import twitter
from pytwitter import Api
from api_keys import TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET, TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET, \
    TWITTER_BEARER_TOKEN
import requests
import requests
import random
from bs4 import BeautifulSoup as bs
from tqdm import tqdm
import tweepy
import sys
import re


def get_free_proxies():
    url = "https://free-proxy-list.net/"
    # получаем ответ HTTP и создаем объект soup
    soup = bs(requests.get(url).content, "html5lib")
    proxies = []
    for row in soup.find("table").find_all("tr")[1:]:
        tds = row.find_all("td")
        try:
            ip = tds[0].text.strip()
            port = tds[1].text.strip()
            host = f"{ip}:{port}"
            proxies.append(host)
        except IndexError:
            continue
    return proxies


def get_access_proxies():
    free_proxies = get_free_proxies()
    success_proxy=[]
    for index, pr in tqdm(enumerate(free_proxies), total=len(free_proxies)):
        try:
            api = Api(consumer_key=TWITTER_CONSUMER_KEY,
                      consumer_secret=TWITTER_CONSUMER_SECRET,
                      access_token=TWITTER_ACCESS_TOKEN,
                      access_secret=TWITTER_ACCESS_TOKEN_SECRET, proxies={'http': pr, 'https': pr})
            res = api.get_users(usernames="Twitter,TwitterDev")
            success_proxy.append(pr)
            with open('proxies', 'a') as fout:
                fout.write(pr + '\n')
        except:
            continue
    return success_proxy

def parse_tweet(tweet):
    retweet_user=re.findall(r'RT @[\w]*',tweet)
    hashtags = re.findall(r'#[\w]*',tweet)
    print(hashtags)
    print(retweet_user)

def get_user_tweets_url(user_id):
    # Replace with user ID below
    return "https://api.twitter.com/2/users/{}/tweets".format(user_id)

def get_user_url(usernames):
    # Specify the usernames that you want to lookup below
    # You can enter up to 100 comma-separated values.
    user_fields = "user.fields=description,created_at,public_metrics,location"
    # User fields are adjustable, options include:
    # created_at, description, entities, id, location, name,
    # pinned_tweet_id, profile_image_url, protected,
    # public_metrics, url, username, verified, and withheld
    url = "https://api.twitter.com/2/users/by?{}&{}".format(usernames, user_fields)
    return url


def get_params():
    # Tweet fields are adjustable.
    # Options include:
    # attachments, author_id, context_annotations,
    # conversation_id, created_at, entities, geo, id,
    # in_reply_to_user_id, lang, non_public_metrics, organic_metrics,
    # possibly_sensitive, promoted_metrics, public_metrics, referenced_tweets,
    # source, text, and withheld
    return {"tweet.fields": "entities,created_at,text,public_metrics"}


def bearer_oauth(r):
    """
    Method required by bearer token authentication.
    """

    r.headers["Authorization"] = f"Bearer {TWITTER_BEARER_TOKEN}"
    r.headers["User-Agent"] = "v2UserTweetsPython"
    return r


def connect_to_endpoint(url, params):
    if params is not None:
        response = requests.request("GET", url, auth=bearer_oauth, params=params)
    else:
        response = requests.request("GET", url, auth=bearer_oauth)
    print(response.status_code)
    if response.status_code != 200:
        raise Exception(
            "Request returned an error: {} {}".format(
                response.status_code, response.text
            )
        )
    return response.json()


if __name__ == "__main__":
    usernames = "usernames=TwitterDev,TwitterAPI"
    users_url = get_user_url(usernames)
    users_response = connect_to_endpoint(users_url, params=None)
    # users_response = json.dumps(users_response, indent=4, sort_keys=True)
    for user in users_response["data"]:
        user_id = int(user["id"])
        params = get_params()
        twewts_response = connect_to_endpoint(get_user_tweets_url(user_id), params=params)
        print(json.dumps(twewts_response, indent=4, sort_keys=True))
    # json_response = connect_to_endpoint(url, params=None)
    # print(json.dumps(json_response, indent=4, sort_keys=True))