import re
from urllib.parse import urlparse
import requests
import base64
from difflib import get_close_matches
from io import BytesIO
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from datetime import datetime, timedelta
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
# ELEVEN ALL LIKE ONE JUST LOOK AT THEM SO PRETTY
def get_message_batch(engine, base_msg):
    session = Session(bind=engine)
    # base_msg = session.query(Message).filter(Message.dis_id == message.id).first()
    limit = 11
    chain = [base_msg, ]
    batch = []
    # get message branch
    while chain[-1].parent_id is not None and limit != 2:
        parent_msg = session.query(Message).filter(Message.id == chain[-1].parent_id).first()
        chain.append(parent_msg)
        limit = (12 - len(chain)) // len(chain)
    # get chain message for msg in branch
    for i, msg in enumerate(chain[1:-1]):
        # fix_date_chain = msg.created_on - timedelta(minutes=3)
        # half-interval
        chain_msg = session.query(Message).filter(
            Message.created_on.between(chain[i+1].created_on+timedelta(microseconds=1), msg.created_on), Message.channel == base_msg.channel).order_by(
            desc(Message.id)).limit(limit).all()
        print([m.content for m in chain_msg])
        batch.extend([m.content for m in chain_msg])

    batch.extend([m.content for m in session.query(Message).filter(
        Message.created_on <= chain[-1].created_on, Message.channel == base_msg.channel).order_by(
        desc(Message.id)).limit(12 - len(batch)).all()])
    return batch


def get_message_batch2(engine, message):
    session = Session(bind=engine)

    # base_msg = session.query(Message).filter(Message.dis_id == message.id).first()
    limit = 12
    chain = [message, ]
    batch = []
    while chain[-1].parent_id is not None and limit != 0:
        parent_msg = session.query(Message).filter(Message.id == chain[-1].parent_id).first()
        chain.append(parent_msg)
        batch.append(parent_msg.content)
        limit -= 1
    if limit > 0:
        batch.extend([m.content for m in session.query(Message).filter(
            Message.created_on < chain[-1].created_on, Message.channel == message.channel).order_by(
            desc(Message.id)).limit(limit)])
    return batch


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
    return domain in domains_whitelist


def expand_blacklist(domains):
    with open(BLACKLIST_PATH, 'a') as file:
        file.writelines(domains)
    domains_blacklist.extend(domains)


def expand_whitelist(domains):
    with open(WHITELIST_PATH, 'a') as file:
        file.writelines(domains)
    domains_whitelist.extend(domains)
