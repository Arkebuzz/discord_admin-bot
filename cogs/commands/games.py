import random

import disnake

from disnake.ext import commands

from main import db
from utils.logger import logger

PARAMS_STORE = {'Все': None,
                'Steam': 0,
                'EpicGames': 1,
                'GOG': 2}

PARAMS_DLC = {'Все': None,
              'Только игры': 0,
              'Только DLC': 1}


class GameCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(
        name='roll',
        description='Случайное число от 0 до 100',
    )
    async def roll(self, inter: disnake.ApplicationCommandInteraction):
        """
        Слэш-команда, отправляет в ответ случайное число от 0 до 100.

        :param inter:
        :return:
        """

        logger.info(f'[CALL] <@{inter.author.id}> /roll')

        await inter.response.send_message(random.randint(0, 100))

    @commands.slash_command(
        name='free_games',
        description='Список игр, которые раздают в Steam, GOG или EpicGames',
    )
    async def free_games(self, inter: disnake.ApplicationCommandInteraction,
                         store: str = commands.Param(choices=PARAMS_STORE.keys(), default='Все',
                                                     description='Выберите магазин'),
                         dlc: str = commands.Param(choices=PARAMS_DLC.keys(), default='Все',
                                                   description='Показывать дополнения?')
                         ):
        """
        Слэш-команда, отправляет в ответ список игр, ставших бесплатными.

        :param inter:
        :param store:
        :param dlc:
        :return:
        """

        logger.info(f'[CALL] <@{inter.author.id}> /free_steam_games')

        dlc = PARAMS_DLC[dlc]
        store = PARAMS_STORE[store]

        if store is not None and dlc is not None:
            games = db.get_data('games', dlc=dlc, store=store)[:25]
        elif store is not None:
            games = db.get_data('games', store=store)[:25]
        elif dlc is not None:
            games = db.get_data('games', dlc=dlc)[:25]
        else:
            games = db.get_data('games')

        emb = disnake.Embed(title='Сейчас бесплатны', colour=disnake.Colour.gold())
        for game in games:
            title = game[0] + (' (DLC)' if game[1] else '')
            emb.add_field(title, game[2], inline=False)

        await inter.response.send_message(embed=emb)


def setup(bot: commands.Bot):
    """Регистрация команд бота."""

    bot.add_cog(GameCommands(bot))
