import os

import disnake
from disnake.ext import commands

from config import TOKEN, IDS

os.chdir(os.path.dirname(os.path.realpath(__file__)))

if not os.path.isdir('data'):
    os.mkdir('data')

intents = disnake.Intents.default()
intents.members = True
bot = commands.InteractionBot(test_guilds=IDS, intents=intents)

bot.load_extension('cogs.commands')
bot.load_extension('cogs.events')

bot.run(TOKEN)
