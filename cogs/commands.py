import disnake
import emoji

from disnake.ext import commands

from utils.db import DB
from utils.logger import logger

db = DB()


class OtherCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(
        name='set_log_channel',
        description='Выбрать канал лога для бота.',
        default_member_permissions=disnake.Permissions(8)
    )
    async def settings(self, inter: disnake.ApplicationCommandInteraction, channel: disnake.TextChannel):
        """
        Слэш-команда, производит настройку канала для бота на сервере.

        :param inter:
        :param channel:
        :return:
        """

        db.update_guild_settings(inter.guild_id, log_id=channel.id)

        await inter.response.send_message('Выполнена настройка канала-лога для бота, '
                                          f'теперь канал лога - {channel}')

        logger.info(f'[CALL] <@{inter.author.id}> /set_log_channel channel: {channel}')

    @commands.slash_command(
        name='ping',
        description='Узнать задержку бота.',
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
        name='info',
        description='Информация о боте.',
    )
    async def info(self, inter: disnake.ApplicationCommandInteraction):
        """
        Слэш-команда, отправляет в ответ информацию о боте.

        :param inter:
        :return:
        """

        emb = disnake.Embed(title='Информация о боте "КВАНт"', color=disnake.Colour.blue())
        emb.set_thumbnail(r'https://i.pinimg.com/originals/64/39/45/643945344aa7b4c3d8151ea1ec80212c.jpg')
        emb.add_field(name='Название:', value='Комитет Везопасности Академии Наук (т)', inline=False)
        emb.add_field(name='Версия:', value='alpha v0.3', inline=False)
        emb.add_field(name='Описание:', value='Бот создан для упрощения работы админов.', inline=False)
        emb.add_field(name='Что нового:',
                      value='```diff\nv0.3\n'
                            '+Бот создан.\n'
                            '+Добавлена возможность назначать заданную роль новым участникам.\n'
                            '+Добавлена возможность создать сообщение для автовыдачи ролей участникам по реакциям.\n'
                            '+Добавлено оповещение о присоединении/уходе участников.\n'
                            '```', inline=False)
        emb.set_footer(text='@Arkebuzz#7717',
                       icon_url='https://sun1-27.userapi.com/s/v1/ig1'
                                '/FEUHI48F0M7K3DXhPtF_hChVzAsFiKAvaTvSG3966WmikzGIrLrj0u7UPX7o_zQ1vMW0x4CP.jpg?size'
                                '=400x400&quality=96&crop=528,397,709,709&ava=1')

        await inter.response.send_message(embed=emb)
        logger.info(f'[CALL] <@{inter.author.id}> /info')


class DistributionRoles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(
        name='edit_default_role',
        description='Изменить стандартную роль для новых участников сервера.',
        default_member_permissions=disnake.Permissions(8)
    )
    async def edit_default_role(self, inter: disnake.ApplicationCommandInteraction, role: disnake.Role):
        """
        Обновляет связку роль - реакция на сервере.

        :param inter:
        :param role:
        :return:
        """

        roles = inter.guild.roles
        if roles.index(role) >= roles.index(inter.guild.me.roles[-1]):
            await inter.response.send_message('Невозможно настроить роль по умолчанию, данная роль превосходит роль '
                                              'бота.', ephemeral=True)

            logger.info(f'[CALL] <@{inter.author.id}> /edit_default_role incorrect role')

        elif role.is_default():
            db.update_guild_settings(inter.guild_id, role_id='NULL')
            await inter.response.send_message('Роль по умолчанию настроена.', ephemeral=True)

            logger.info(f'[CALL] <@{inter.author.id}> /edit_default_role role`s append')

        else:
            db.update_guild_settings(inter.guild_id, role_id=inter.id)
            await inter.response.send_message('Роль по умолчанию настроена.', ephemeral=True)

            logger.info(f'[CALL] <@{inter.author.id}> /edit_default_role role`s append')

    @commands.slash_command(
        name='add_role2distribution_roles',
        description='Добавить роль к автовыдачи по эмодзи.',
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

        roles = inter.guild.roles
        if role.is_default() or roles.index(role) >= roles.index(inter.guild.me.roles[-1]):
            await inter.response.send_message('Невозможно добавить связку роль - реакция, данная роль превосходит роль '
                                              'бота или является ролью по умолчанию.', ephemeral=True)

            logger.info(f'[CALL] <@{inter.author.id}> /add_role2distribution_roles incorrect role')

        elif emoji.is_emoji(reaction):
            db.update_reaction4role(inter.guild_id, role.id, reaction)
            await inter.response.send_message('Связка роль - реакция добавлена, используйте /new_distribution_roles,'
                                              'чтобы обновить сообщение выдачи ролей.', ephemeral=True)

            logger.info(f'[CALL] <@{inter.author.id}> /add_role2distribution_roles role`s append')

        else:
            await inter.response.send_message('Невозможно добавить связку роль - реакция, переданная реакция не '
                                              'является смайликом.', ephemeral=True)

            logger.info(f'[CALL] <@{inter.author.id}> /add_role2distribution_roles reaction isn`t emoji')

    @commands.slash_command(
        name='del_role2distribution_roles',
        description='Удалить роль из автовыдачи по эмодзи.',
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
        await inter.response.send_message('Связка роль - реакция удалена, используйте /new_distribution_roles, '
                                          'чтобы обновить сообщение выдачи ролей.', ephemeral=True)

        logger.info(f'[CALL] <@{inter.author.id}> /del_role2distribution_roles')

    @commands.slash_command(
        name='new_distribution_roles',
        description='Новое сообщение с автовыдачей ролей по эмодзи.',
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
        logger.info(f'[CALL] <@{inter.author.id}> /new_distribution_roles')


def setup(bot: commands.Bot):
    """Регистрация команд бота."""

    bot.add_cog(OtherCommands(bot))
    bot.add_cog(DistributionRoles(bot))
