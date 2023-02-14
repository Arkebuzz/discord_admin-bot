import disnake
from disnake.ext import commands

from config import IDS, BOT_ID
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
        for guild in set(db_guilds) - set(cur_guilds):
            db.delete_guild(guild)
            logger.warning(f'[IN PROGRESS] guilds refresh : bot not in {id} but it`s in DB')

        for guild in set(cur_guilds) - set(db_guilds):
            g = bot.get_guild(guild)
            channels = (
                (g.system_channel,) if g.system_channel is not None else () +
                                                                         (
                                                                         g.public_updates_channel,) if g.public_updates_channel is not None else () +
                                                                                                                                                 g.text_channels
            )

            for channel in channels:
                try:
                    await channel.send('Для первоначальной настройки бота используйте функцию /set_log_channel.\n'
                                       'Бот не будет корректно работать, пока Вы этого не сделаете.')
                    break
                except disnake.errors.Forbidden:
                    continue

            logger.warning(f'[IN PROGRESS] guilds refresh : {guild} not in DB -> warning sent')

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
        if payload.user_id == BOT_ID:
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
        if payload.user_id == BOT_ID:
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

            logger.info(f'[NEW USER] <{member.user_id}>')

    @commands.Cog.listener()
    async def on_raw_member_remove(self, payload: disnake.RawGuildMemberRemoveEvent):
        guild = db.get_guilds(payload.guild_id)

        if guild and guild[0][1]:
            ch = self.bot.get_channel(guild[0][1])
            await ch.send(f'<@{payload.user.id}> покинул сервер.')

            logger.info(f'[DEL USER] <{payload.user.id}>')


def setup(bot: commands.InteractionBot):
    """Регистрация активностей бота."""

    bot.add_cog(MainEvents(bot))
    bot.add_cog(ReactionEvents(bot))
    bot.add_cog(MemberEvents(bot))
