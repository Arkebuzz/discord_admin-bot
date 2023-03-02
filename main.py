import os

import disnake
from disnake.ext import commands

from config import TOKEN
from utils.db import DB

os.chdir(os.path.dirname(os.path.realpath(__file__)))

if not os.path.isdir('data'):
    os.mkdir('data')

db = DB()

intents = disnake.Intents.all()
bot = commands.InteractionBot(intents=intents)

bot.load_extension('cogs.commands')
bot.load_extension('cogs.events')

bot.run(TOKEN)
