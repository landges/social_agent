import discord
from discord.ext import commands
from config import settings
from difflib import get_close_matches
import requests
from io import BytesIO
import base64
import re
from urllib.parse import urlparse
from sqlalchemy.orm import Session, sessionmaker
from db_sa import *

engine = create_engine("postgresql+psycopg2://postgres:postgres@localhost/social_agent")
session = sessionmaker(bind=engine)

VIDEO = ('.m1v', '.mpeg', '.mov', '.qt', '.mpa', '.mpg', '.mpe', '.avi', '.movie', '.mp4')
AUDIO = ('.ra', '.aif', '.aiff', '.aifc', '.wav', '.au', '.snd', '.mp3', '.mp2')
IMAGE = (
    '.ras', '.xwd', '.bmp', '.jpe', '.jpg', '.jpeg', '.xpm', '.ief', '.pbm', '.tif', '.gif', '.ppm', '.xbm', '.tiff',
    '.rgb', '.pgm', '.png', '.pnm')
IMAGE_FOLDER_ID = "som3f0ld3r1D"
IMAGE_SRV_URL = 'https://...'
LINK_REGEX = r"(http|ftp|https):\/\/([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])"
BLACKLIST_PATH = 'static_data/words_blacklist.txt'
WHITELIST_PATH = 'static_data/domains_whitelist.txt'
bot = commands.Bot(command_prefix=settings['prefix'], intents=discord.Intents.all())
with open('static_data/words_blacklist.txt') as file:
    blck_lst = file.read().split(', ')
with open(WHITELIST_PATH) as file:
    domains_whitelist = file.read().split('\n')
with open(BLACKLIST_PATH) as file:
    domains_blacklist = file.read().split('\n')


# client = discord.Client()
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


def insert_users(users_ids):
    session = Session(bind=engine)
    for id in users_ids:
        member = bot.get_user(id)
        new_user = User(username=member.name, user_code=member.mention, dis_id=member.id, created_on=member.created_at)
        session.add(new_user)
        session.commit()
        new_embed = UserEmbedding(user=new_user)
        session.add(new_embed)
        session.commit()


@bot.event
async def on_ready():
    session = Session(bind=engine)
    users_db = {us.dis_id for us in session.query(User).all()}
    users_bot = {us.id for us in bot.users if us.bot is False}
    users_for_bd = users_bot - users_db
    if len(users_for_bd) > 0:
        insert_users(users_for_bd)
    print(f'Bot connected as {bot.user}')


@bot.event
async def on_member_join(member):
    if text_is_swear(member.name):
        for ch in bot.get_guild(member.guild.id).channels:
            if ch.name == 'основной':
                await bot.get_channel(ch.id).send(f'We don\'t like such nicknames. Think about it')
        await member.ban(reason="Swear nickname")
    else:
        session = Session(bind=engine)
        get_user = session.query(User).filter(User.dis_id == member.id).all()
        if len(get_user) == 0:
            insert_users({member.id})
        for ch in bot.get_guild(member.guild.id).channels:
            if ch.name == 'основной':
                await bot.get_channel(ch.id).send(f'{member} has arrived')


@bot.event
async def on_message(message):
    if message.author.bot is False:
        if message.content == 'test':
            print(message.author)
            await message.channel.send('Testing 1 2 3')
        # TODO database interaction
        is_swear = text_is_swear(message.content.lower())
        if is_swear:
            await message.channel.send('Found swear message')
        for domain in detect_domains(message.content):
            # TODO database logs
            if domain in domains_whitelist:
                await message.channel.send(f'{message.author} I like this stuff. *SNIFF SNIFF*')
            elif domain in domains_blacklist:
                await message.channel.send(f'{message.author} is  breaking the community rules. Reporting.')
                message.delete()
            else:
                await message.channel.send(f'Potentially unwanted stuff detected. Reporting.')
        # TODO database interaction
        for at in message.attachments:
            if at.url.split('.')[-1] in IMAGE:
                await process_image(at.url)
        session = Session(bind=engine)
        user = session.query(User).filter(User.dis_id==message.author.id).first()
        new_message = Message(user=user,content=message.content, is_swear=is_swear)
        session.add(new_message)
        session.commit()
        session.close()


@bot.command()
async def hello(ctx, arg=None):
    author = ctx.message.author
    print(author.usernaame)
    await ctx.send(
        f'Pososi, {author}!')


@bot.command()
async def getinfo(ctx, arg=None):
    author = ctx.message.author
    await ctx.send(
        f'Sorry, no info, {author}!')


@bot.command(pass_context=True)
@commands.has_permissions(administrator=True)
async def add_blacklist(ctx, args):
    domains = detect_domains(ctx.message.content)
    with open(BLACKLIST_PATH, 'a') as file:
        file.writelines(domains)
    domains_blacklist.extend(domains)


@bot.command(pass_context=True)
@commands.has_permissions(administrator=True)
async def add_whitelist(ctx, args):
    domains = detect_domains(ctx.message.content)
    with open(WHITELIST_PATH, 'a') as file:
        file.writelines(domains)
    domains_whitelist.extend(domains)


bot.run(settings['token'])
