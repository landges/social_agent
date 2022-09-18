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
    for index, pr in tqdm(enumerate(free_proxies), total=len(free_proxies)):
        try:
            api = Api(consumer_key=TWITTER_CONSUMER_KEY,
                      consumer_secret=TWITTER_CONSUMER_SECRET,
                      access_token=TWITTER_ACCESS_TOKEN,
                      access_secret=TWITTER_ACCESS_TOKEN_SECRET, proxies={'http': pr, 'https': pr})
            res = api.get_users(usernames="Twitter,TwitterDev")
            with open('proxies', 'a') as fout:
                fout.write(pr + '\n')
        except:
            continue


if __name__ == "__main__":
    pr = '45.42.177.17:3128'
    api = Api(consumer_key=TWITTER_CONSUMER_KEY,
              consumer_secret=TWITTER_CONSUMER_SECRET,
              access_token=TWITTER_ACCESS_TOKEN,
              access_secret=TWITTER_ACCESS_TOKEN_SECRET, proxies={'http': pr, 'https': pr})
    user = api.get_users(usernames=['arimelonari'])
    user_id = user.data[0].id
    folowing = api.get_following(user_id=user_id)
    print(folowing)