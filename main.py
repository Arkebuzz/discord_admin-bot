import os

import disnake
from disnake.ext import commands

from config import TOKEN, PATH_DATA
from utils.db import DB

os.chdir(os.path.dirname(os.path.realpath(__file__)))

if not os.path.isdir(PATH_DATA):
    os.mkdir(PATH_DATA)

db = DB()

intents = disnake.Intents.all()
bot = commands.InteractionBot(intents=intents)

bot.load_extensions('cogs/commands')
bot.load_extension('cogs.events')

bot.run(TOKEN)
