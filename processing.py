import re
from urllib.parse import urlparse
import requests
import base64
from difflib import get_close_matches
from io import BytesIO
from sqlalchemy.orm import Session
from db_sa import *

IMAGE_FOLDER_ID = "som3f0ld3r1D"
IMAGE_SRV_URL = 'https://...'
LINK_REGEX = r"(http|ftp|https):\/\/([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])"
BLACKLIST_PATH = 'static_data/domains_blacklist.txt'
WHITELIST_PATH = 'static_data/domains_whitelist.txt'
with open(WHITELIST_PATH) as file:
    domains_whitelist = file.read().split('\n')
with open(BLACKLIST_PATH) as file:
    domains_blacklist = file.read().split('\n')
with open('static_data/words_blacklist.txt') as file:
    blck_lst = file.read().split(', ')


# message processing
def get_message_batch(engine, message):
    session = Session(bind=engine)
    batch = []
    base_msg = session.query(Message).filter(Message.dis_id == message.id).first()


def detect_domains(text):
    return [urlparse(link.string).netloc for link in re.finditer(LINK_REGEX, text)]


def text_is_swear(text):
    for n_word in blck_lst:
        if n_word in text:
            print(n_word)
    if any(n_word in text for n_word in blck_lst):
        return True
    for word in re.split(r'\W', text):
        if len(get_close_matches(word, blck_lst, n=1, cutoff=0.9)):
            return True
    return False


# API work
def process_image(url):
    response = requests.get(url)
    try:
        # Not even looking inside. No need for local processing
        content = base64.b64encode(BytesIO(response.content).getvalue())
        body = {
            "folderId": IMAGE_FOLDER_ID,
            "analyze_specs": [{
                "content": content,
                "features": [{
                    "type": "CLASSIFICATION",
                    "classificationConfig": {
                        "model": "moderation"
                    }
                }]
            }]
        }
        r = requests.post(IMAGE_SRV_URL, data=body)
        ans = process_json(r.json())
        print(f'Sucessfully processed {url}')
        return ans
    except:
        print(f'Failed to process {url}')
        return None


def process_json(content):
    return True


# job functions
def domain_blacklisted(domain):
    return domain in domains_blacklist


def domain_whitelisted(domain):
    return domain in domains_blacklist


def expand_blacklist(domains):
    with open(BLACKLIST_PATH, 'a') as file:
        file.writelines(domains)
    domains_blacklist.extend(domains)


def expand_whitelist(domains):
    with open(WHITELIST_PATH, 'a') as file:
        file.writelines(domains)
    domains_whitelist.extend(domains)
