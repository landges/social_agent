import discord
from discord.ext import commands
from config import settings


bot = commands.Bot(command_prefix=settings['prefix'], intents=discord.Intents.all())
# client = discord.Client()

@bot.event
async def on_ready():
    print(f'Bot connected as {bot.user}')

@bot.event
async def on_message(message):
    print(message)
    if message.content == 'test':
        await message.channel.send('Testing 1 2 3')
    await bot.process_commands(message)

@bot.command()
async def hello(ctx, arg=None):
    print('Doooo')
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

