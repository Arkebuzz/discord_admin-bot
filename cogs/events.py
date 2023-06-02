import asyncio
import time

import disnake
from disnake.ext import commands

from main import db
from cogs.buttons import Voting
from utils.logger import logger
from utils.free_games import search_games


async def add_guild2db(bot, guild_id):
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
    Обновление БД и config.py бота.

    :param bot:
    :return:
    """

    logger.debug('[START] guilds refresh')

    cur_guilds = [g.id for g in bot.guilds]
    db_guilds = [g[0] for g in db.get_data('guilds') if g[1]]

    if db_guilds != cur_guilds:
        for guild_id in set(db_guilds) - set(cur_guilds):
            db.delete_date('guilds', id=guild_id)
            logger.warning(f'[IN PROGRESS] guilds refresh : bot not in {db_guilds} but it`s in DB')

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
        except disnake.errors:
            logger.warning(f'[IN PROGRESS] updating voting - question: {voting[5]} message was deleted')

        logger.info(f'[IN PROGRESS] updating voting - question: {voting[5]}')

    logger.debug('[FINISHED] all voting is update')


async def check_voting_timeout(bot: commands.InteractionBot):
    while True:
        logger.debug('[START] check voting timeout')

        cur_time = time.time()

        try:
            for voting in db.get_data('voting'):
                if voting[4] < cur_time:
                    author = bot.get_user(voting[3])

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
                        await bot.get_channel(voting[2]).get_partial_message(voting[0]).edit(embed=emb, view=None)
                    except disnake.errors:
                        logger.warning(f'[IN PROGRESS] deleting voting - question: {voting[5]} message was deleted')

                    db.delete_date('voting', id=voting[0])

                    logger.info(f'[IN PROGRESS] deleted voting - question: {voting[5]}')

        except Exception as e:
            logger.warning(f'[IN PROGRESS] {e}')

        logger.debug('[FINISHED] check voting timeout')
        await asyncio.sleep(60)


async def check_new_games(bot: commands.InteractionBot):
    while True:
        logger.debug('[START] check new games')

        try:
            games = await search_games()

            cur_games = set(games)
            bd_games = set(db.get_data('games'))

            if cur_games != bd_games:
                for game in bd_games - cur_games:
                    db.delete_date('games', url=game[2])

                    title = game[0].encode('windows-1251', 'replace').decode('windows-1251')
                    logger.info(f'[IN PROGRESS] game is no longer free - {title}')

                for game in cur_games - bd_games:
                    db.add_game(game)

                    dlc = ' (DLC)' if game[1] else ''
                    emb = disnake.Embed(title=f'{game[0]}{dlc} сейчас бесплатна!', colour=disnake.Colour.gold())
                    emb.add_field('Описание:', game[3] if game[3] is not None else '-', inline=False)
                    emb.add_field('Отзывы:', game[4] if game[4] is not None else '-', inline=False)
                    emb.add_field(game[5], game[2])
                    emb.set_image(game[-2])

                    for guild in db.get_data('guilds'):
                        if guild[6] is not None:
                            await bot.get_channel(guild[6]).send(embed=emb)

                    title = game[0].encode('windows-1251', 'replace').decode('windows-1251')
                    logger.info(f'[IN PROGRESS] new free game - {title}')

        except Exception as e:
            logger.warning(f'[IN PROGRESS] check new games {e}')

        logger.debug('[FINISHED] check new games')
        await asyncio.sleep(3600)


class MainEvents(commands.Cog):
    """Класс, задающий основные активности на серверах."""

    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Выполняется, когда бот запустился.

        :return:
        """

        logger.info('Bot started')

        await refresh(self.bot)
        await asyncio.sleep(600)
        asyncio.ensure_future(check_voting_timeout(self.bot))
        asyncio.ensure_future(check_new_games(self.bot))

    @commands.Cog.listener()
    async def on_guild_join(self, guild: disnake.Intents.guilds):
        """
        Выполняется, когда бот присоединяется к новому серверу.

        :param guild:
        :return:
        """

        logger.info(f'[NEW GUILD] <{guild.id}>')

        for channel in guild.text_channels:
            try:
                await channel.send('Здравствуйте, я очень рад, что вы добавили меня на сервер.\n'
                                   'Сейчас я проведу анализ текущих сообщений на сервере, это займёт несколько минут.\n'
                                   'Вы можете пользоваться ботом в течении этого времени, '
                                   'однако статистика пользователей и сервера будет выводиться некорректно.')

                emb = disnake.Embed(
                    description='Я умею раздавать роли, вести статистику пользователей сервера, устраивать голосования '
                                'и сообщать о новых раздачах игр.\n\n'
                                'Список команд (некоторые команды доступны только администраторам сервера):',
                    color=disnake.Color.gold()
                )

                emb.add_field('Команда', '\n'.join(com.name for com in self.bot.slash_commands))
                emb.add_field('Описание', '\n'.join(com.description for com in self.bot.slash_commands))

                await channel.send(embed=emb)

                await add_guild2db(self.bot, guild.id)

                await channel.send('Анализ сообщений завершён.')
                await channel.send('Если вам нужны оповещения о присоединении/уходе участников, то выберите для этого '
                                   'канал командой /set_log_channel')
                await channel.send('Если вам нужны оповещения о новых раздачах игр, то выберите для этого '
                                   'канал командой /set_games_channel')
                await channel.send('Рекомендуется вызвать команду /check_permissions, чтобы удостовериться, '
                                   'что бот имеет необходимые права.')
                break

            except disnake.errors.Forbidden:
                continue

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: disnake.Intents.guilds):
        """
        Выполняется, когда бот покидает сервер.

        :param guild:
        :return:
        """

        db.delete_date('guilds', id=guild.id)
        logger.warning(f'[IN PROGRESS] guilds refresh : bot not in {guild.id} but it`s in DB')

        logger.info(f'[DEL GUILD] <{guild.id}>')


class ReactionEvents(commands.Cog):
    """Класс, задающий активности с реакциями."""

    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: disnake.RawReactionActionEvent):
        mes = db.get_data('guilds', payload.guild_id)[0][4:]

        if payload.user_id == self.bot.user.id or payload.channel_id != mes[0] or payload.message_id != mes[1]:
            return

        emoji = str(payload.emoji)

        roles = db.get_data('reaction4role', 'role, reaction', guild_id=payload.guild_id)
        active_emoji = [react[1] for react in roles]

        if emoji in active_emoji:
            ind = active_emoji.index(emoji)

            await payload.member.add_roles(self.bot.get_guild(payload.guild_id).get_role(roles[ind][0]))

            logger.info(f'[NEW REACT] <{payload.user_id}>')

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: disnake.RawReactionActionEvent):
        mes = db.get_data('guilds', payload.guild_id)[0][4:]

        if payload.user_id == self.bot.user.id or payload.channel_id != mes[0] or payload.message_id != mes[1]:
            return

        emoji = str(payload.emoji)

        roles = db.get_data('reaction4role', 'role, reaction', guild_id=payload.guild_id)
        active_emoji = [react[1] for react in roles]

        if emoji in active_emoji:
            ind = active_emoji.index(emoji)
            member = self.bot.get_guild(payload.guild_id).get_member(payload.user_id)

            await member.remove_roles(self.bot.get_guild(payload.guild_id).get_role(roles[ind][0]))

            logger.info(f'[DEL REACT] <{payload.user_id}>')


class MemberEvents(commands.Cog):
    """Класс, обрабатывающий добавление/удаление пользователей."""

    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: disnake.Member):
        guild = db.get_data('guilds', id=member.guild.id)

        if guild:
            guild = guild[0]

            if guild[2]:
                ch = self.bot.get_channel(guild[2])
                await ch.send(f'<@{member.id}> присоединился к серверу.')

            if guild[3]:
                await member.add_roles(member.guild.get_role(guild[3]))

            logger.info(f'[NEW USER] <{member.id}>')

    @commands.Cog.listener()
    async def on_raw_member_remove(self, payload: disnake.RawGuildMemberRemoveEvent):
        guild = db.get_data('guilds', id=payload.guild_id)

        if guild and guild[0][2]:
            ch = self.bot.get_channel(guild[0][2])
            await ch.send(f'<@{payload.user.id}> покинул сервер.')

            logger.info(f'[DEL USER] <{payload.user.id}>')


class MessageEvents(commands.Cog):
    """Класс, обновляющий статистику пользователей."""

    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, mes: disnake.Message):
        guild = db.get_data('guilds', id=mes.guild.id)

        if not guild or not guild[0][1] or mes.author.bot or mes.author.name != 'Deleted User':
            return

        name = mes.author.name.encode('windows-1251', 'replace').decode('windows-1251')
        db.update_user(mes.guild.id, mes.author.id, name, len(mes.content), len(mes.attachments))


def setup(bot: commands.InteractionBot):
    """Регистрация активностей бота."""

    bot.add_cog(MainEvents(bot))
    bot.add_cog(ReactionEvents(bot))
    bot.add_cog(MemberEvents(bot))
    bot.add_cog(MessageEvents(bot))
