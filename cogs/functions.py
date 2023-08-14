import asyncio
import time

import disnake
from disnake.ext import commands

from main import db
from cogs.buttons import Voting
from utils.logger import logger
from utils.free_games import search_games


async def send_warning_message(guild: disnake.guild.Guild, message: str):
    for ch in guild.text_channels:
        try:
            await ch.send(message)
            break
        except disnake.errors.Forbidden:
            continue


async def add_guild2db(bot, guild_id):
    """
    Добавление сервера в БД, с анализом сообщений.
    """

    logger.info(f'[IN PROGRESS] guilds refresh : {guild_id} not in DB -> starting messages analyze')

    db.update_guild_settings(guild_id)

    for ch in bot.get_guild(guild_id).text_channels:
        try:
            async for mes in ch.history(limit=10000):
                if not mes.author.bot and mes.author.name != 'Deleted User':
                    name = mes.author.name.encode('windows-1251', 'replace').decode('windows-1251')
                    db.update_user(mes.guild.id, mes.author.id, name, len(mes.content), len(mes.attachments))

        except disnake.errors.Forbidden:
            continue

    db.update_guild_settings(guild_id, analyze=1)

    logger.info(f'[IN PROGRESS] guilds refresh : {guild_id} not in DB -> messages are analyzed')


async def refresh(bot: commands.InteractionBot):
    """
    Синхронизация серверов, на которых присутствует бот, и серверов в БД, а также обновление кнопок голосований.
    """

    logger.debug('[START] guilds refresh')

    cur_guilds = [g.id for g in bot.guilds]
    db_guilds = [g[0] for g in db.get_data('guilds')]

    if db_guilds != cur_guilds:
        for guild_id in set(db_guilds) - set(cur_guilds):
            db.delete_date('guilds', id=guild_id)
            logger.warning(f'[IN PROGRESS] guilds refresh : bot not in {guild_id} but it`s in DB')

        for guild_id in set(cur_guilds) - set(db_guilds):
            await add_guild2db(bot, guild_id)

    logger.debug('[IN PROGRESS] all guilds refresh')

    for voting in db.get_data('voting'):
        author = bot.get_user(voting[3])

        emb = disnake.Embed(title=voting[5], color=disnake.Color.gold())
        emb.add_field('Завершится', f'<t:{int(voting[4])}:R>')
        emb.add_field('Вариантов', 'от ' + str(voting[6]) + ' до ' + str(voting[7]))
        emb.add_field('Варианты:', ', '.join(voting[8].split('!|?')), inline=False)
        emb.set_footer(text=author.name, icon_url=author.avatar)

        view = Voting(voting[0], voting[5], voting[8].split('!|?'), voting[4] - time.time(), *voting[6:8])

        try:
            await bot.get_channel(voting[2]).get_partial_message(voting[0]).edit(embed=emb, view=view)
        except (disnake.errors.NotFound, disnake.errors.Forbidden):
            db.delete_date('voting', id=voting[0])
            logger.warning(f'[IN PROGRESS] updating voting - question: {voting[5]} message was deleted')

        logger.info(f'[IN PROGRESS] updating voting - question: {voting[5]}')

    logger.debug('[FINISHED] all voting is update')


class UpdateDB:
    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot

    async def check_voting_timeout(self):
        """
        Завершение голосований, время которых истекло.
        """

        logger.debug('[START] check voting timeout')

        cur_time = time.time()

        for voting in db.get_data('voting'):
            if voting[4] < cur_time:
                author = self.bot.get_user(voting[3])

                emb = disnake.Embed(title=f'Голосование: {voting[5]}', color=disnake.Color.gold())
                emb.add_field('Завершилось', f'<t:{int(voting[4])}:R>')
                emb.add_field('Вариантов', 'от ' + str(voting[6]) + ' до ' + str(voting[7]))
                emb.add_field('Варианты:', ', '.join(voting[8].split('!|?')), inline=False)
                emb.set_footer(text=author.name, icon_url=author.avatar)

                res = [info[2] for info in db.get_data('votes', voting_id=voting[0])]
                stat = []

                for key in set(res):
                    d = res.count(key) / len(res)
                    stat.append((key[:18],
                                 '🔳' * int(d * 10) + '⬜' * (10 - int(d * 10)),
                                 f'{round(100 * d, 2):.2f} % - {res.count(key)} голос'))

                emb.add_field('', '**Результаты:**')

                for key, progress, info in stat:
                    emb.add_field(key + ' ' + info, progress, inline=False)

                try:
                    await self.bot.get_channel(voting[2]).get_partial_message(voting[0]).edit(
                        embed=emb, view=None
                    )
                except (disnake.errors.NotFound, disnake.errors.Forbidden):
                    logger.info(f'[IN PROGRESS] deleting voting - question: {voting[5]} message was deleted')

                db.delete_date('voting', id=voting[0])

                logger.info(f'[IN PROGRESS] deleted voting - question: {voting[5]}')

        logger.debug('[FINISHED] check voting timeout')

    async def check_new_games(self):
        """
        Проверка на наличие новых игр и уведомление о них.
        """

        logger.debug('[START] check new games')

        games = await search_games()
        games_dict = {name: info for name, *info in games}

        cur_games = set((g[0], g[2]) for g in games)
        bd_games = set(db.get_data('games', 'name, url'))

        if cur_games != bd_games:
            for game in bd_games - cur_games:
                db.delete_date('games', url=game[1])

                title = game[0].encode('windows-1251', 'replace').decode('windows-1251')
                logger.info(f'[IN PROGRESS] game is no longer free - {title}')

            for game in cur_games - bd_games:
                game = [game[0]] + games_dict[game[0]]

                db.add_game(game)

                dlc = ' (DLC)' if game[1] else ''
                emb = disnake.Embed(title=f'{game[0]}{dlc} сейчас бесплатна!', colour=disnake.Colour.gold())
                emb.add_field('Описание:', game[3] if game[3] is not None else '-', inline=False)
                emb.add_field('Отзывы:', game[4] if game[4] is not None else '-', inline=False)
                emb.add_field(game[5], game[2])
                emb.set_image(game[-2])

                for guild in db.get_data('guilds'):
                    if guild[6] is not None:
                        try:
                            await self.bot.get_channel(guild[6]).send(embed=emb)
                        except disnake.errors.Forbidden:
                            logger.info(f'[IN PROGRESS] forbidden channel {guild[6]}')
                            db.update_guild_settings(guild[0], game_id=None)

                            await send_warning_message(self.bot.get_guild(guild[0]),
                                                       'Бот не может писать в канале с игровыми оповещениями, '
                                                       'установка канала с игровыми оповещениями сброшена!')

                title = game[0].encode('windows-1251', 'replace').decode('windows-1251')
                logger.info(f'[IN PROGRESS] new free game - {title}')

        logger.debug('[FINISHED] check new games')

    async def update(self):
        while True:
            try:
                await self.check_new_games()
            except Exception as e:
                logger.exception('[IN PROGRESS] check_new_games', e)

            for _ in range(60):
                try:
                    await self.check_voting_timeout()
                except Exception as e:
                    logger.exception('[IN PROGRESS] check_voting_timeout', e)

                await asyncio.sleep(60)
