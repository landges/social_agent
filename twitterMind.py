import twitter
from pytwitter import Api
from api_keys import TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET, TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET, \
    TWITTER_BEARER_TOKEN
import requests
import requests
import random
from bs4 import BeautifulSoup as bs
from tqdm import tqdm


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


if __name__ == "__main__":
    # pr='20.54.56.26:8080'
    pr = get_access_proxies()
    api = Api(consumer_key=TWITTER_CONSUMER_KEY,
              consumer_secret=TWITTER_CONSUMER_SECRET,
              access_token=TWITTER_ACCESS_TOKEN,
              access_secret=TWITTER_ACCESS_TOKEN_SECRET, proxies={'http': pr, 'https': pr})
    user = api.get_users(usernames=['justinbieber'])
    user_id = user.data[0].id
    following = api.get_following(user_id=user_id)
    followers = api.get_followers(user_id=user_id)
    liked_tweets = api.get_user_liked_tweets(user_id=user_id)
    user_tweets = api.get_timelines(user_id=user_id).data
    print(user_tweets)
    for info in user_tweets:
        print("ID: {}".format(info.id))
        # print(info.)
        print(info.text)
        print("\n")
    # tw = api.get_tweets(user_fields=user)
    # print(tw)
    print(following)
    import tweepy

