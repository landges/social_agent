import discord
from discord.ext import commands
from api_keys import DICSORD_TOKEN


bot = commands.Bot(command_prefix='!')
bot.run(DICSORD_TOKEN)
