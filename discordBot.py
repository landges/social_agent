from datetime import timedelta

import discord
import asyncio
from discord.ext import commands, tasks
from scipy.spatial import distance

from config import settings

from processing import detect_domains, text_is_swear, process_image, \
    domain_blacklisted, domain_whitelisted, expand_blacklist, expand_whitelist, get_message_batch, get_message_batch2
from sqlalchemy.orm import Session, sessionmaker
from sentence_transformers import SentenceTransformer, util
from db_sa import *
import nltk

nltk.download('omw-1.4')
from nltk.stem import WordNetLemmatizer

engine = create_engine("postgresql+psycopg2://postgres:postgres@localhost/social_agent")
session = sessionmaker(bind=engine)
wnl = WordNetLemmatizer()
VIDEO = ('.m1v', '.mpeg', '.mov', '.qt', '.mpa', '.mpg', '.mpe', '.avi', '.movie', '.mp4')
AUDIO = ('.ra', '.aif', '.aiff', '.aifc', '.wav', '.au', '.snd', '.mp3', '.mp2')
IMAGE = (
    '.ras', '.xwd', '.bmp', '.jpe', '.jpg', '.jpeg', '.xpm', '.ief', '.pbm', '.tif', '.gif', '.ppm', '.xbm', '.tiff',
    '.rgb', '.pgm', '.png', '.pnm')

bot = commands.Bot(command_prefix=settings['prefix'], intents=discord.Intents.all())


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
    global model_sb
    model_sb = SentenceTransformer('distiluse-base-multilingual-cased')
    users_db = {us.dis_id for us in session.query(User).all()}
    users_bot = {us.id for us in bot.users if us.bot is False}
    users_for_bd = users_bot - users_db
    if len(users_for_bd) > 0:
        insert_users(users_for_bd)
    print(f'Bot connected as {bot.user}')
    # msg1.start()


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
        session = Session(bind=engine)
        user = session.query(User).filter(User.dis_id == message.author.id).first()
        new_message = Message(user=user, content=message.content, dis_id=message.id,
                              channel=message.channel.id)
        if message.content == 'test':
            print(message.author)
            await message.channel.send('Testing 1 2 3')
        # TODO database interaction
        is_swear = text_is_swear(message.content.lower())
        if is_swear:
            new_message.is_swear = True
            await message.channel.send('Found swear message')
        for domain in detect_domains(message.content):
            print(domain)
            # TODO database logs
            if domain_whitelisted(domain):
                await message.channel.send(f'{message.author} I like this stuff. *SNIFF SNIFF*')
            elif domain_blacklisted(domain):
                new_message.is_ads = True
                await message.channel.send(f'{message.author} is  breaking the community rules. Reporting.')
                await message.delete()
            else:
                await message.channel.send(f'Potentially unwanted stuff detected. Reporting.')
        # TODO database interaction
        for at in message.attachments:
            if at.url.split('.')[-1] in IMAGE:
                process_image(at.url)
        if message.reference is not None:
            ans_msg = session.query(Message).filter(Message.dis_id == message.reference.message_id).first()
            if ans_msg:
                new_message.parent_id = ans_msg.id
        session.add(new_message)
        session.commit()
        print('bath1', get_message_batch(engine, session.query(Message).filter(Message.dis_id == message.id).first()))
        print('batch2', get_message_batch2(engine, session.query(Message).filter(Message.dis_id == message.id).first()))
        session.close()
        await bot.process_commands(message)


@bot.command()
async def getinfo(ctx, arg=None):
    author = ctx.message.author
    await ctx.send(
        f'Sorry, no info, {author}!')


@bot.command()
async def get_brahch(ctx, arg=None):
    author = ctx.message.author
    await ctx.send(
        f'Sorry, no info, {author}!')


# TODO nn processing
def get_sense_score(batch, msg, model_sb=None, threshold=0.7):
    message_embed = model_sb.encode(msg)
    embeds = [model_sb.encode(' '.join(chain)) for chain in batch]
    corr = max([distance.cosine(embed, message_embed) for embed in embeds])
    if corr >= threshold:
        return 0.5
    else:
        return -0.2


@tasks.loop(seconds=300)
async def process_messages():
    session = Session(bind=engine)
    interval = datetime.now() - timedelta(minutes=4)
    for user in session.query(User).all():
        usremb = session.query(UserEmbedding).filter(UserEmbedding.user_id == user.id).first()
        user_msgs = session.query(Message).filter(Message.created_on.between(interval, datetime.now()),
                                                  Message.user_id == user.id)
        for msg in user_msgs:
            usremb.score += get_sense_score(get_message_batch(engine, msg), msg.content, model_sb)
            if msg.is_swear:
                usremb.score -= 0.2
            if msg.is_ads:
                usremb.score -= 0.5
    session.commit()


@bot.command(pass_context=True)
@commands.has_role('BotAdmin')
async def add_blacklist(ctx, args):
    domains = detect_domains(args)
    print(f'Adding domains {domains} to blacklist')
    expand_blacklist(domains)


@bot.command(pass_context=True)
@commands.has_role('BotAdmin')
async def add_whitelist(ctx, args):
    domains = detect_domains(args)
    print(f'Adding domains {domains} to whitelist')
    expand_whitelist(domains)


bot.run(settings['token'])
