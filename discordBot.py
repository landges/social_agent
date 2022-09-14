import discord
from discord.ext import commands
from config import settings
from difflib import SequenceMatcher, get_close_matches
import re
import string

bot = commands.Bot(command_prefix=settings['prefix'], intents=discord.Intents.all())
with open('blacklist.txt') as file:
    blck_lst = file.read().split(', ')


# client = discord.Client()


def text_is_swear(text):
    if any(n_word in text for n_word in blck_lst):
        return True
    for word in re.split(r'\W', text):
        if len(get_close_matches(word, blck_lst, n=1, cutoff=0.9)):
            return True


@bot.event
async def on_ready():
    print(f'Bot connected as {bot.user}')


@bot.event
async def on_message(message):
    if message.content == 'test':
        await message.channel.send('Testing 1 2 3')
    # elif message.conent.contains('Anton'):
    #     await message.edit()
    elif text_is_swear(message.content):
        await message.channel.send('Found swear message')


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


# @client.event
# async def on_ready():
#     print(f'{client.user} welcome to the club, buddy!')

bot.run(settings['token'])
