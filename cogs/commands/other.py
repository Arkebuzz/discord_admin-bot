import random

import disnake

from disnake.ext import commands

from main import db
from utils.logger import logger
from utils.free_games import search_free_games


def key_sort(a):
    return a.name


class OtherCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(
        name='info',
        description='Информация о боте',
    )
    async def info(self, inter: disnake.ApplicationCommandInteraction):
        """
        Слэш-команда, отправляет в ответ информацию о боте.

        :param inter:
        :return:
        """

        emb = disnake.Embed(title=f'Информация о боте "{self.bot.user.name}"', color=disnake.Colour.gold())
        emb.set_thumbnail(self.bot.user.avatar)
        emb.add_field(name='Версия:', value='v0.8.3')
        emb.add_field(name='Серверов:', value=len(self.bot.guilds))
        emb.add_field(name='Описание:', value='Бот создан для упрощения работы админов.', inline=False)
        emb.add_field(name='Что нового:',
                      value='```diff\nv0.8.3\n'
                            '+Перезапуск бота не ломает голосования.\n'
                            '+Теперь можно задать параметр сортировки топа пользователей.\n'
                            '+Добавлена команда /roll\n'
                            '+Добавлена команда /free_steam_games\n'
                            '~Теперь боты и удаленные пользователи не участвуют в топах.\n'
                            '~Исправлены ошибки.\n'
                            '```', inline=False)
        emb.set_footer(text='@Arkebuzz#7717\n'
                            'https://github.com/Arkebuzz/discord_admin-bot',
                       icon_url='https://cdn.discordapp.com/avatars/542244057947308063/'
                                '4b8f2972eb7475f44723ac9f84d9c7ec.png?size=1024')

        await inter.response.send_message(embed=emb)
        logger.info(f'[CALL] <@{inter.author.id}> /info')

    @commands.slash_command(
        name='help',
        description='Описание команд бота'
    )
    async def help(self, inter: disnake.ApplicationCommandInteraction):
        """
        Слэш-команда, отправляет сообщение с описанием команд.

        :param inter:
        :return:
        """

        emb = disnake.Embed(
            title='Помощь',
            description='Я умею раздавать роли, вести статистику пользователей сервера и создавать голосования.'
                        '\n\nСписок команд (некоторые команды доступны только администраторам сервера):',
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

        :param inter:
        :return:
        """

        info = db.get_guilds(inter.guild_id)
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

        emb.add_field(name='Добавление реакций: ' +
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

            for role in db.get_reaction4role(inter.guild_id):
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
        name='set_log_channel',
        description='Выбрать канал лога для бота',
        default_member_permissions=disnake.Permissions(8)
    )
    async def settings(self, inter: disnake.ApplicationCommandInteraction, channel: disnake.TextChannel):
        """
        Слэш-команда, производит настройку канала для бота на сервере.

        :param inter:
        :param channel:
        :return:
        """

        if channel.permissions_for(inter.guild.me).send_messages:
            db.update_guild_settings(inter.guild_id, log_id=channel.id)

            await inter.response.send_message('Выполнена настройка канала-лога для бота, '
                                              f'теперь канал лога - {channel}', ephemeral=True)

            logger.info(f'[CALL] <@{inter.author.id}> /set_log_channel channel: {channel}')
        else:
            await inter.response.send_message('Невозможно выполнить настройку канала-лога для бота, '
                                              'бот не может писать в переданном канале.', ephemeral=True)

    @commands.slash_command(
        name='ping',
        description='Задержка бота',
    )
    async def ping(self, inter: disnake.ApplicationCommandInteraction):
        """
        Слэш-команда, отправляет в ответ пинг.

        :param inter:
        :return:
        """

        logger.info(f'[CALL] <@{inter.author.id}> /ping')

        await inter.response.send_message(f'Пинг: {round(self.bot.latency * 1000)}мс', ephemeral=True)

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
        name='free_steam_games',
        description='Список игр, которые раздают в Steam',
    )
    async def games(self, inter: disnake.ApplicationCommandInteraction):
        """
        Слэш-команда, отправляет в ответ список игр, ставших бесплатными.

        :param inter:
        :return:
        """

        logger.info(f'[CALL] <@{inter.author.id}> /free_steam_games')

        emb = disnake.Embed(title='Сейчас бесплатны', colour=disnake.Colour.gold())

        games = await search_free_games()
        for game in games[:25]:
            emb.add_field(game[0], '\n'.join(game[1:]), inline=False)

        await inter.response.send_message(embed=emb)


def setup(bot: commands.Bot):
    """Регистрация команд бота."""

    bot.add_cog(OtherCommands(bot))
