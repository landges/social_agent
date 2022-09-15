import discord
from discord.ext import commands
from config import settings
from difflib import get_close_matches
import requests
from io import BytesIO
import base64
import re
from urllib.parse import urlparse

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


@bot.event
async def on_ready():
    print(f'Bot connected as {bot.user}')


async def on_member_join(member):
    channel = member.channel
    if text_is_swear(member.nick):
        await channel.send(f'We don\'t like such nicknames. Think about it')
        await member.ban(reason="Swear nickname")
    else:
        await channel.send(f'{member} has arrived')


@bot.event
async def on_message(message):
    if message.content == 'test':
        await message.channel.send('Testing 1 2 3')
    # TODO database interaction
    if text_is_swear(message.content.lower()):
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


@bot.command()
async def hello(ctx, arg=None):
    author = ctx.message.author
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
