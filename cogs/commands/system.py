import disnake
from disnake.ext import commands

from config import __version__, __version_info__
from main import db
from utils.logger import logger


def key_sort(a):
    return a.name


class SystemCommands(commands.Cog):
    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot

    @commands.slash_command(
        name='info',
        description='Информация о боте',
    )
    async def info(self, inter: disnake.ApplicationCommandInteraction):
        """
        Слэш-команда, отправляет в ответ информацию о боте.
        """

        emb = disnake.Embed(title=f'Информация о боте "{self.bot.user.name}"', color=disnake.Colour.gold())
        emb.set_thumbnail(self.bot.user.avatar)
        emb.add_field(name='Версия:', value=__version__)
        emb.add_field(name='Серверов:', value=len(self.bot.guilds))
        emb.add_field(name='Описание:', value='Бот создан для упрощения работы админов.', inline=False)
        emb.add_field(name='Что нового:',
                      value=__version_info__, inline=False)
        emb.set_footer(text='@Arkebuzz#7717\n'
                            'https://github.com/Arkebuzz/discord_admin-bot',
                       icon_url='https://avatars.githubusercontent.com/u/115876609?v=4')

        await inter.response.send_message(embed=emb)

        logger.info(f'[CALL] <@{inter.author.id}> /info')

    @commands.slash_command(
        name='help',
        description='Описание команд бота'
    )
    async def help(self, inter: disnake.ApplicationCommandInteraction):
        """
        Слэш-команда, отправляет сообщение с описанием команд.
        """

        emb = disnake.Embed(
            title='Помощь',
            description='Я умею раздавать роли, вести статистику пользователей сервера, устраивать голосования '
                        'и сообщать о новых раздачах игр.\n\n'
                        'Список команд (некоторые команды доступны только администраторам сервера):',
            color=disnake.Color.blue()
        )

        for com in sorted(list(self.bot.slash_commands), key=key_sort):
            emb.add_field('/' + com.name, com.description + '.', inline=False)

        emb.add_field('Для просмотра помощи по созданию голосований смотри /voting_help', '', inline=False)

        await inter.response.send_message(embed=emb, ephemeral=True)

        logger.info(f'[CALL] <@{inter.author.id}> /help')

    @commands.slash_command(
        name='check_permissions',
        description='Проверка разрешений бота',
        default_member_permissions=disnake.Permissions(8)
    )
    async def check_permissions(self, inter: disnake.ApplicationCommandInteraction):
        """
        Слэш-команда, проверяет верно ли настроены разрешения бота.
        """

        info = db.get_data('guilds', id=inter.guild_id)
        emb = disnake.Embed(title='Проверка разрешений бота', color=disnake.Color.gold())

        if info and info[0][2]:
            emb.add_field(
                name='Отправка сообщений в канале лога: ' +
                     ('✅' if self.bot.get_channel(info[0][2]).permissions_for(inter.guild.me).send_messages else '⛔'),
                value='',
                inline=False
            )
        else:
            emb.add_field(name='Отправка сообщений в канале лога: ⚠️',
                          value='',
                          inline=False)

        if info and info[0][6]:
            emb.add_field(
                name='Отправка сообщений в канале игр: ' +
                     ('✅' if self.bot.get_channel(info[0][6]).permissions_for(inter.guild.me).send_messages else '⛔'),
                value='',
                inline=False
            )
        else:
            emb.add_field(name='Отправка сообщений в канале игр: ⚠️',
                          value='',
                          inline=False)

        emb.add_field(name='Добавление реакций в данном канале: ' +
                           ('✅' if inter.channel.permissions_for(inter.guild.me).add_reactions else '⛔'),
                      value='',
                      inline=False)

        if inter.channel.permissions_for(inter.guild.me).manage_roles:
            if not info or not info[0][3]:
                emb.add_field(name='Роль по умолчанию: ⚠️', value='', inline=False)
            else:
                emb.add_field(
                    name='Роль по умолчанию: ' +
                         ('✅' if self.bot.get_guild(inter.guild_id).get_role(info[0][3]).is_assignable() else '⛔'),
                    value='',
                    inline=False
                )

            emb.add_field('Право на назначение ролей в автораздаче:', '', inline=False)

            for role in db.get_data('reaction4role', 'role, reaction', guild_id=inter.guild_id):
                emb.add_field('',
                              f'<@&{role[0]}> ' +
                              ('✅' if self.bot.get_guild(inter.guild_id).get_role(role[0]).is_assignable() else '⛔'))
        else:
            emb.add_field('Право на управление ролями: ⛔',
                          '',
                          inline=False)

        emb.set_footer(text='✅ - работает; ️️⚠️ - не настроено; ⛔ - нет прав')

        await inter.response.send_message(embed=emb)

        logger.info(f'[CALL] <@{inter.author.id}> /check_permissions')

    @commands.slash_command(
        name='log_channel_set',
        description='Выбрать канал лога для бота',
        default_member_permissions=disnake.Permissions(8)
    )
    async def set_log_channel(self, inter: disnake.ApplicationCommandInteraction, channel: disnake.TextChannel):
        """
        Слэш-команда, производит настройку канала для бота на сервере.
        """

        if channel.permissions_for(inter.guild.me).send_messages:
            db.update_guild_settings(inter.guild_id, log_id=channel.id)

            await inter.response.send_message('Выполнена настройка канала-лога для бота, '
                                              f'теперь канал лога - {channel}', ephemeral=True)

            logger.info(f'[CALL] <@{inter.author.id}> /set_log_channel channel: {channel}')
        else:
            await inter.response.send_message('Невозможно выполнить настройку канала-лога для бота, '
                                              'бот не может писать в переданном канале.', ephemeral=True)

            logger.info(f'[CALL] <@{inter.author.id}> /set_log_channel forbidden sent message')

    @commands.slash_command(
        name='log_channel_disable',
        description='Удалить канал лога для бота',
        default_member_permissions=disnake.Permissions(8)
    )
    async def disable_log_channel(self, inter: disnake.ApplicationCommandInteraction):
        """
        Слэш-команда, производит настройку канала для бота на сервере.
        """

        db.update_guild_settings(inter.guild_id, log_id=None)

        await inter.response.send_message('Канал-лог отключен.', ephemeral=True)

        logger.info(f'[CALL] <@{inter.author.id}> /disable_log_channel')

    @commands.slash_command(
        name='games_channel_set',
        description='Выбрать канал лога для бота',
        default_member_permissions=disnake.Permissions(8)
    )
    async def set_games_channel(self, inter: disnake.ApplicationCommandInteraction, channel: disnake.TextChannel):
        """
        Слэш-команда, производит настройку канала для бота на сервере.
        """

        if channel.permissions_for(inter.guild.me).send_messages:
            db.update_guild_settings(inter.guild_id, game_id=channel.id)

            await inter.response.send_message('Выполнена настройка канала оповещений для бота, '
                                              f'теперь канал с игровыми оповещениями - {channel}', ephemeral=True)

            logger.info(f'[CALL] <@{inter.author.id}> /set_games_channel channel: {channel}')
        else:
            await inter.response.send_message('Невозможно выполнить настройку канала оповещений для бота, '
                                              'бот не может писать в переданном канале.', ephemeral=True)

            logger.info(f'[CALL] <@{inter.author.id}> /set_log_channel forbidden sent message')

    @commands.slash_command(
        name='games_channel_disable',
        description='Удалить канал игр для бота',
        default_member_permissions=disnake.Permissions(8)
    )
    async def disable_games_channel(self, inter: disnake.ApplicationCommandInteraction):
        """
        Слэш-команда, производит настройку канала для бота на сервере.
        """

        db.update_guild_settings(inter.guild_id, game_id=None)

        await inter.response.send_message('Канал игр отключен.', ephemeral=True)

        logger.info(f'[CALL] <@{inter.author.id}> /disable_games_channel')

    @commands.slash_command(
        name='ping',
        description='Задержка бота',
    )
    async def ping(self, inter: disnake.ApplicationCommandInteraction):
        """
        Слэш-команда, отправляет в ответ пинг.
        """

        logger.info(f'[CALL] <@{inter.author.id}> /ping')

        await inter.response.send_message(f'Пинг: {round(self.bot.latency * 1000)}мс', ephemeral=True)


def setup(bot: commands.InteractionBot):
    """Регистрация команд бота."""

    bot.add_cog(SystemCommands(bot))
