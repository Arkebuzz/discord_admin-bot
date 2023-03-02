import disnake
import emoji

from disnake.ext import commands
from tabulate import tabulate

from main import db
from utils.logger import logger


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
        emb.add_field(name='Версия:', value='beta v0.5')
        emb.add_field(name='Серверов:', value=len(self.bot.guilds))
        emb.add_field(name='Описание:', value='Бот создан для упрощения работы админов.', inline=False)
        emb.add_field(name='Что нового:',
                      value='```diff\nv0.5\n'
                            '+Создана функция проверки разрешений бота.\n'
                            '+Топ игроков переделан для телефонов.\n'
                            '+Теперь опыт начисляется за вложения сообщений (фото, гифки и т.д.)\n'
                            '+Открыт исходный код.\n'
                            '~Исправлено ошибок.\n'
                            '```', inline=False)
        emb.set_footer(text='@Arkebuzz#7717\n'
                            'https://github.com/Arkebuzz/discord_admin-bot/blob/main/cogs/events.py',
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
            description='Я умею раздавать роли и вести статистику пользователей сервера.\n\n',
            color=disnake.Color.blue()
        )

        emb.add_field('Команда', '\n'.join(com.name for com in self.bot.slash_commands))
        emb.add_field('Описание', '\n'.join(com.description for com in self.bot.slash_commands))

        await inter.response.send_message(embed=emb, ephemeral=True)

        logger.info(f'[CALL] <@{inter.author.id}> /help')

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
                                              f'теперь канал лога - {channel}')

            logger.info(f'[CALL] <@{inter.author.id}> /set_log_channel channel: {channel}')
        else:
            await inter.response.send_message('Невозможно выполнить настройку канала-лога для бота, '
                                              'бот не может писать в переданном канале.', ephemeral=True)


class DistributionCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(
        name='set_default_role',
        description='Изменить стандартную роль для новых участников',
        default_member_permissions=disnake.Permissions(8)
    )
    async def set_default_role(self, inter: disnake.ApplicationCommandInteraction, role: disnake.Role):
        """
        Обновляет связку роль - реакция на сервере.

        :param inter:
        :param role:
        :return:
        """

        if role.is_default():
            db.update_guild_settings(inter.guild_id, role_id='NULL')
            await inter.response.send_message('Роль по умолчанию сброшена.', ephemeral=True)

            logger.info(f'[CALL] <@{inter.author.id}> /set_default_role role`s dell')

        elif not role.is_assignable():
            await inter.response.send_message('Невозможно настроить роль по умолчанию, данная роль превосходит роль '
                                              'бота.', ephemeral=True)

            logger.info(f'[CALL] <@{inter.author.id}> /set_default_role incorrect role')

        else:
            db.update_guild_settings(inter.guild_id, role_id=role.id)
            await inter.response.send_message('Роль по умолчанию настроена.', ephemeral=True)

            logger.info(f'[CALL] <@{inter.author.id}> /set_default_role role`s append')

    @commands.slash_command(
        name='distribution_new_message',
        description='Отправить сообщение автовыдачи ролей по эмодзи',
        default_member_permissions=disnake.Permissions(8)
    )
    async def new_distribution(self, inter: disnake.ApplicationCommandInteraction):
        """
        Отправляет новое сообщение с автовыдачей ролей по эмодзи.

        :param inter:
        :return:
        """

        await inter.response.defer(ephemeral=True)
        await inter.delete_original_response()

        emb = disnake.Embed(title='Какие роли вы хотите иметь?',
                            colour=disnake.Colour.gold())

        roles = db.get_reaction4role(inter.guild_id)[:10]
        for role, reaction in roles:
            emb.add_field(name='', value=f'{reaction} - <@&{role}>', inline=False)

        mes = await inter.channel.send(embed=emb)

        for _, reaction in roles:
            await mes.add_reaction(reaction)

        db.update_guild_settings(inter.guild_id, message_id=mes.id)
        logger.info(f'[CALL] <@{inter.author.id}> /distribution_new_message')

    @commands.slash_command(
        name='distribution_add_role',
        description='Добавить роль к автовыдаче по эмодзи',
        default_member_permissions=disnake.Permissions(8)
    )
    async def add_role(self, inter: disnake.ApplicationCommandInteraction, role: disnake.Role,
                       reaction: str):
        """
        Обновляет связку роль - реакция на сервере.

        :param inter:
        :param role:
        :param reaction:
        :return:
        """

        if role.is_default() or not role.is_assignable():
            await inter.response.send_message('Невозможно добавить связку роль - реакция, данная роль превосходит роль '
                                              'бота или является ролью по умолчанию.', ephemeral=True)

            logger.info(f'[CALL] <@{inter.author.id}> /distribution_add_role incorrect role')

        elif emoji.is_emoji(reaction):
            db.update_reaction4role(inter.guild_id, role.id, reaction)
            await inter.response.send_message('Связка роль - реакция добавлена, используйте /distribution_new_message, '
                                              'чтобы обновить сообщение выдачи ролей.', ephemeral=True)

            logger.info(f'[CALL] <@{inter.author.id}> /distribution_add_role role`s append')

        else:
            await inter.response.send_message('Невозможно добавить связку роль - реакция, переданная реакция не '
                                              'является смайликом.', ephemeral=True)

            logger.info(f'[CALL] <@{inter.author.id}> /distribution_add_role reaction isn`t emoji')

    @commands.slash_command(
        name='distribution_del_role',
        description='Удалить роль из автовыдачи по эмодзи',
        default_member_permissions=disnake.Permissions(8)
    )
    async def del_role(self, inter: disnake.ApplicationCommandInteraction, role: disnake.Role):
        """
        Удаляет связку роль - реакция на сервере.

        :param inter:
        :param role:
        :return:
        """

        db.delete_reaction4role(inter.guild_id, role.id)
        await inter.response.send_message('Связка роль - реакция удалена, используйте /distribution_new_message, '
                                          'чтобы обновить сообщение выдачи ролей.', ephemeral=True)

        logger.info(f'[CALL] <@{inter.author.id}> /distribution_add_role')


class StatisticCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(
        name='server_info',
        description='Статистика сервера',
    )
    async def server_info(self, inter: disnake.ApplicationCommandInteraction):
        guild = inter.guild
        info = db.get_users(guild.id)
        exp = sum(us[3] for us in info) // 2
        mes = sum(us[4] for us in info)

        emb = disnake.Embed(colour=disnake.Colour.gold())
        emb.set_author(name=guild.name + f'\t\t\t\tУровень {exp // 1000 + 1}', icon_url=guild.icon)

        emb.add_field('Опыт', exp)
        emb.add_field('Создатель', f'<@{guild.owner_id}>')
        emb.add_field('Создан', f'<t:{int(guild.created_at.timestamp())}:R>')
        emb.add_field('Участников', guild.member_count)
        emb.add_field('Сообщений', mes)
        emb.add_field('', '')

        emb.set_footer(text=f'ID: {guild.id}')

        await inter.response.send_message(embed=emb)
        logger.info(f'[CALL] <@{inter.author.id}> /server_info')

    @commands.slash_command(
        name='user_info',
        description='Статистика пользователя',
    )
    async def user_info(self, inter: disnake.ApplicationCommandInteraction, user: disnake.Member = None):
        if user is None:
            user = inter.author

        db_info = db.get_users(inter.guild_id, user.id)

        if user.id == self.bot.user.id:
            info = ['∞', '∞', '∞']
            s2m = '∞'
            lvl = '∞'
        elif db_info:
            info = db_info[0][3:6]
            s2m = round(info[2] / info[1], 2) if info[1] else 0
            lvl = info[0] // 1000 + 1
        else:
            info = [0, 0, 0]
            s2m = 0
            lvl = 1

        emb = disnake.Embed(colour=user.color)

        emb.add_field('Опыт', info[0])
        emb.add_field('Зарегистрирован', f'<t:{int(user.created_at.timestamp())}:R>')
        emb.add_field('Присоединился', f'<t:{int(user.joined_at.timestamp())}:R>')

        emb.add_field('Сообщений', info[1])
        emb.add_field('Символов', info[2])
        emb.add_field('Длина сообщений', s2m)

        emb.set_author(name=user.name + f'\t\t\t\t\t\t\t\tУровень {lvl}', icon_url=user.avatar)
        emb.set_footer(text=f'ID: {user.id}')

        await inter.response.send_message(embed=emb, ephemeral=True)
        logger.info(f'[CALL] <@{inter.author.id}> /user_info')

    @commands.slash_command(
        name='user_top',
        description='Топ пользователей по количеству опыта',
    )
    async def user_top(self, inter: disnake.ApplicationCommandInteraction):
        info = db.get_users(inter.guild_id)[:10]

        emb = disnake.Embed(title=f'Топ пользователей', colour=disnake.Colour.gold())

        emb.add_field(
            '',
            '```' +
            tabulate([(user[2][:18], user[3]) for user in info],
                     ['Участник', 'Опыт'], 'rounded_outline') +
            '```'
        )

        await inter.response.send_message(embed=emb)
        logger.info(f'[CALL] <@{inter.author.id}> /user_top')


def setup(bot: commands.Bot):
    """Регистрация команд бота."""

    bot.add_cog(OtherCommands(bot))
    bot.add_cog(DistributionCommands(bot))
    bot.add_cog(StatisticCommands(bot))
