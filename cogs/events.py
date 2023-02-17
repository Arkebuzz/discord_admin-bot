import disnake
from disnake.ext import commands

from config import IDS
from utils.db import DB
from utils.logger import logger

db = DB()


async def refresh(bot):
    """
    Обновление БД и config.py бота.

    :param bot:
    :return:
    """

    logger.info('[START] guilds refresh')

    cur_guilds = [g.id for g in bot.guilds]
    db_guilds = [g[0] for g in db.get_guilds()]

    if IDS != cur_guilds:
        ids = [str(g.id) for g in bot.guilds]

        with open('config.py', 'r') as f:
            text = ''
            for line in f:
                if 'IDS' in line:
                    text += 'IDS = [' + ', '.join(ids) + ']\n'
                else:
                    text += line

        with open('config.py', 'w') as f:
            f.write(text)

        import os
        import sys

        logger.warning(f'[FINISHED] guilds refresh in config : BOT RESTARTING')
        os.execv(sys.executable, [sys.executable, sys.argv[0]])

    if db_guilds != cur_guilds:
        for guild_id in set(db_guilds) - set(cur_guilds):
            db.delete_guild(guild_id)
            logger.warning(f'[IN PROGRESS] guilds refresh : bot not in {id} but it`s in DB')

        for guild_id in set(cur_guilds) - set(db_guilds):
            logger.info(f'[IN PROGRESS] guilds refresh : {guild_id} not in DB -> starting messages analyze')

            db.update_guild_settings(guild_id)

            for ch in bot.get_guild(guild_id).text_channels:
                try:
                    async for mes in ch.history(limit=10000):
                        db.update_user(guild_id, mes.author.id, len(mes.content))
                except disnake.errors.Forbidden:
                    continue

            logger.info(f'[IN PROGRESS] guilds refresh : {guild_id} not in DB -> messages are analyzed')

    logger.info('[FINISHED] all guilds refresh')


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

        emb = disnake.Embed(title=f'Информация о боте "{self.bot.user.name}"', color=disnake.Colour.blue())
        emb.set_thumbnail(self.bot.user.avatar)
        emb.add_field(name='Версия:', value='beta v0.4.1', inline=False)
        emb.add_field(name='Описание:', value='Бот создан для упрощения работы админов.', inline=False)
        emb.add_field(name='Что нового:',
                      value='```diff\nv0.4\n'
                            '+Добавлена статистика участников сервера.\n'
                            '+Добавлена статистика сервера.\n'
                            '```', inline=False)
        emb.set_footer(text='@Arkebuzz#7717',
                       icon_url='https://cdn.discordapp.com/avatars/542244057947308063/'
                                '4b8f2972eb7475f44723ac9f84d9c7ec.png?size=1024')

        # await self.bot.get_channel(1075105989818339359).send(embed=emb)

        logger.info('Bot started')
        await refresh(self.bot)

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
                                   'Сейчас я проведу анализ текущих сообщений на сервере, это может занять несколько '
                                   'минут, пожалуйста подождите.')

                await channel.send('Если вам нужны оповещения о присоединении/уходе участников выберите для них '
                                   'канал командой /set_log_channel')

                break
            except disnake.errors.Forbidden:
                continue

        await refresh(self.bot)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: disnake.Intents.guilds):
        """
        Выполняется, когда бот покидает сервер.

        :param guild:
        :return:
        """

        logger.info(f'[DEL GUILD] <{guild.id}>')

        await refresh(self.bot)


class ReactionEvents(commands.Cog):
    """Класс, задающий активности с реакциями на серверах."""

    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: disnake.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return

        emoji = str(payload.emoji)

        roles = db.get_reaction4role(payload.guild_id)
        active_emoji = [react[1] for react in roles]

        if emoji in active_emoji:
            ind = active_emoji.index(emoji)

            await payload.member.add_roles(self.bot.get_guild(payload.guild_id).get_role(roles[ind][0]))

            logger.info(f'[NEW REACT] <{payload.user_id}>')

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: disnake.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return

        emoji = str(payload.emoji)

        roles = db.get_reaction4role(payload.guild_id)
        active_emoji = [react[1] for react in roles]

        if emoji in active_emoji:
            ind = active_emoji.index(emoji)
            member = self.bot.get_guild(payload.guild_id).get_member(payload.user_id)

            await member.remove_roles(self.bot.get_guild(payload.guild_id).get_role(roles[ind][0]))

            logger.info(f'[DEL REACT] <{payload.user_id}>')


class MemberEvents(commands.Cog):
    """Класс, задающий активности пользователей."""

    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: disnake.Member):
        guild = db.get_guilds(member.guild.id)

        if guild:
            guild = guild[0]

            if guild[1]:
                ch = self.bot.get_channel(guild[1])
                await ch.send(f'<@{member.id}> присоединился к серверу.')

            if guild[2]:
                await member.add_roles(guild[2])

            logger.info(f'[NEW USER] <{member.id}>')

    @commands.Cog.listener()
    async def on_raw_member_remove(self, payload: disnake.RawGuildMemberRemoveEvent):
        guild = db.get_guilds(payload.guild_id)

        if guild and guild[0][1]:
            ch = self.bot.get_channel(guild[0][1])
            await ch.send(f'<@{payload.user.id}> покинул сервер.')

            logger.info(f'[DEL USER] <{payload.user.id}>')


class MessageEvents(commands.Cog):
    """Класс, задающий активности пользователей."""

    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, mes: disnake.Message):
        if mes.author.id == self.bot.user.id:
            return

        db.update_guild_settings(mes.guild.id)
        db.update_user(mes.guild.id, mes.author.id, len(mes.content))


def setup(bot: commands.InteractionBot):
    """Регистрация активностей бота."""

    bot.add_cog(MainEvents(bot))
    bot.add_cog(ReactionEvents(bot))
    bot.add_cog(MemberEvents(bot))
    bot.add_cog(MessageEvents(bot))
