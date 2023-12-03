import asyncio

import disnake
from disnake.ext import commands

from cogs.functions import send_warning_message, add_guild2db, refresh, UpdateDB, key_sort
from main import db
from utils.logger import logger


class MainEvents(commands.Cog):
    """Класс, задающий основные активности на серверах."""

    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Выполняется, когда бот запустился.
        """

        logger.info('Bot started')

        await refresh(self.bot)

        asyncio.ensure_future(UpdateDB(self.bot).update())

    @commands.Cog.listener()
    async def on_guild_join(self, guild: disnake.Intents.guilds):
        """
        Выполняется, когда бот присоединяется к новому серверу.
        """

        logger.info(f'[NEW GUILD] <{guild.id}>')

        for channel in guild.text_channels:
            try:
                await channel.send('Здравствуйте, я очень рад, что вы добавили меня на сервер.\n'
                                   'Сейчас я проведу анализ текущих сообщений на сервере, это займёт несколько минут.\n'
                                   'Вы можете пользоваться ботом в течении этого времени, '
                                   'однако статистика пользователей и сервера будет выводиться некорректно.')

                emb = disnake.Embed(
                    description='Я умею раздавать роли, вести статистику пользователей сервера, устраивать голосования,'
                                ' сообщать о новых раздачах игр и транслировать музыку.\n\n'
                                'Список команд (некоторые команды доступны только администраторам сервера):',
                    color=disnake.Color.blue()
                )

                for com in sorted(list(self.bot.slash_commands), key=key_sort):
                    emb.add_field('/' + com.name, com.description, inline=False)

                emb.add_field('Для просмотра помощи по использованию голосований смотри /voting_help.', '',
                              inline=False)

                await channel.send(embed=emb)

            except disnake.errors.Forbidden:
                continue

        await add_guild2db(self.bot, guild.id)

        await send_warning_message(guild, 'Анализ сообщений завершён.')
        await send_warning_message(
            guild,
            'Если вам нужны оповещения о присоединении/уходе участников, то выберите для этого '
            'канал командой /log_channel_set.\n'
            'Если вам нужны оповещения о новых раздачах игр, то выберите для этого '
            'канал командой /games_channel_set.\n'
            'Рекомендуется вызвать команду /check_permissions, чтобы удостовериться, '
            'что бот имеет необходимые права.\n'
        )

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: disnake.Intents.guilds):
        """
        Выполняется, когда бот покидает сервер.
        """

        db.delete_date('guilds', id=guild.id)

        logger.info(f'[DEL GUILD] <{guild.id}>')


class ReactionEvents(commands.Cog):
    """Класс, задающий активности с реакциями."""

    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: disnake.RawReactionActionEvent):
        """
        Выполняется, когда поставлена новая реакция.
        """

        mes = db.get_data('guilds', id=payload.guild_id)[0][4:]

        if payload.user_id == self.bot.user.id or payload.channel_id != mes[0] or payload.message_id != mes[1]:
            return

        emoji = str(payload.emoji)

        roles = db.get_data('reaction4role', 'role, reaction', guild_id=payload.guild_id)
        active_emoji = [react[1] for react in roles]

        if emoji in active_emoji:
            ind = active_emoji.index(emoji)

            try:
                await payload.member.add_roles(self.bot.get_guild(payload.guild_id).get_role(roles[ind][0]))
            except disnake.errors.Forbidden:
                logger.info(f'[NEW REACT] <{payload.user_id}> forbidden role')

                await send_warning_message(self.bot.get_guild(payload.guild_id),
                                           f'Бот не может назначить роль по следующей реакции - {emoji} '
                                           f'на <@{payload.user_id}>!')

            logger.info(f'[NEW REACT] <{payload.user_id}>')

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: disnake.RawReactionActionEvent):
        """
        Выполняется, когда реакция удалена.
        """

        mes = db.get_data('guilds', id=payload.guild_id)[0][4:]

        if payload.user_id == self.bot.user.id or payload.channel_id != mes[0] or payload.message_id != mes[1]:
            return

        emoji = str(payload.emoji)

        roles = db.get_data('reaction4role', 'role, reaction', guild_id=payload.guild_id)
        active_emoji = [react[1] for react in roles]

        if emoji in active_emoji:
            ind = active_emoji.index(emoji)
            member = self.bot.get_guild(payload.guild_id).get_member(payload.user_id)

            try:
                await member.remove_roles(self.bot.get_guild(payload.guild_id).get_role(roles[ind][0]))
            except disnake.errors.Forbidden:
                logger.info(f'[DEL REACT] <{payload.user_id}> forbidden role')

                await send_warning_message(self.bot.get_guild(payload.guild_id),
                                           f'Бот не может убрать роль по следующей реакции - {emoji} '
                                           f'с <@{payload.user_id}>!')

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
                try:
                    await self.bot.get_channel(guild[2]).send(f'<@{member.id}> присоединился к серверу.')
                except disnake.errors.Forbidden:
                    logger.info(f'[NEW USER] forbidden log-channel {guild[2]} from {guild[0]}')
                    db.update_guild_settings(guild[0], log_id=None)

                    await send_warning_message(
                        member.guild,
                        'Бот не может писать в канале лога, установка канала-лога сброшена!'
                    )

            if guild[3]:
                try:
                    await member.add_roles(member.guild.get_role(guild[3]))
                except disnake.errors.Forbidden:
                    logger.info(f'[NEW USER] forbidden role')
                    db.update_guild_settings(guild[0], role_id=None)

                    await send_warning_message(
                        member.guild,
                        f'Бот не может назначить роль по умолчанию на <@{member.id}>.\n'
                        'Роль по умолчанию сброшена!'
                    )

            logger.info(f'[NEW USER] <{member.id}>')

    @commands.Cog.listener()
    async def on_raw_member_remove(self, payload: disnake.RawGuildMemberRemoveEvent):
        guild = db.get_data('guilds', id=payload.guild_id)

        if guild and guild[0][2]:
            try:
                await self.bot.get_channel(guild[0][2]).send(f'<@{payload.user.id}> покинул сервер.')
            except disnake.errors.Forbidden:
                logger.info(f'[DEL USER] forbidden log-channel {guild[0][2]} from {guild[0][0]}')
                db.update_guild_settings(guild[0][0], log_id=None)

                await send_warning_message(
                    self.bot.get_guild(payload.guild_id),
                    'Бот не может писать в канале лога, установка канала-лога сброшена!'
                )

            logger.info(f'[DEL USER] <{payload.user.id}>')


class MessageEvents(commands.Cog):
    """Класс, обновляющий статистику пользователей."""

    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, mes: disnake.Message):
        guild = db.get_data('guilds', id=mes.guild.id)

        if not guild or not guild[0][1] or mes.author.bot or mes.author.name == 'Deleted User':
            return

        name = mes.author.name.encode('windows-1251', 'replace').decode('windows-1251')
        db.update_user(mes.guild.id, mes.author.id, name, len(mes.content), len(mes.attachments))


def setup(bot: commands.InteractionBot):
    """Регистрация активностей бота."""

    bot.add_cog(MainEvents(bot))
    bot.add_cog(ReactionEvents(bot))
    bot.add_cog(MemberEvents(bot))
    bot.add_cog(MessageEvents(bot))
