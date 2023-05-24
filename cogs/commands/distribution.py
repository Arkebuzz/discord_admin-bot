import disnake
import emoji

from disnake.ext import commands

from main import db
from utils.logger import logger


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

        emb = disnake.Embed(title='Выберите роли',
                            description='Поставь реакцию для получения соответствующей роли.',
                            colour=disnake.Colour.gold())

        roles = db.get_reaction4role(inter.guild_id)[:10]
        for role, reaction in roles:
            emb.add_field(name='', value=f'{reaction} - <@&{role}>', inline=False)

        mes = await inter.channel.send(embed=emb)

        for _, reaction in roles:
            await mes.add_reaction(reaction)

        db.update_guild_settings(inter.guild_id, distribution=(inter.channel_id, mes.id))
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

            logger.info(f'[CALL] <@{inter.author.id}> /distribution_add_role role`s append')

            info = db.get_guilds(inter.guild_id)[0][4:]
            if not all(info):
                await inter.response.send_message(
                    'Связка роль - реакция добавлена, используйте /distribution_new_message, '
                    'чтобы создать сообщение выдачи ролей.', ephemeral=True)
                return

            emb = disnake.Embed(title='Выберите роли',
                                description='Поставь реакцию для получения соответствующей роли',
                                colour=disnake.Colour.gold())

            roles = db.get_reaction4role(inter.guild_id)[:10]
            for role, react in roles:
                emb.add_field(name='', value=f'{react} - <@&{role}>', inline=False)

            mes = self.bot.get_channel(info[0]).get_partial_message(info[1])

            await mes.edit(embed=emb)
            await mes.add_reaction(reaction)

            await inter.response.send_message(
                'Связка роль - реакция добавлена, сообщение с выдачей реакций обновлено.', ephemeral=True
            )

            logger.info(f'[CALL] <@{inter.author.id}> /distribution_add_role distribution`s update')

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

        reaction = db.delete_reaction4role(inter.guild_id, role.id)

        if reaction:
            reaction = reaction[0][0]
        else:
            await inter.response.send_message(
                'Данной роли нет в раздаче, используйте /distribution_add_role, '
                'чтобы добавить роль к раздаче.', ephemeral=True)
            return

        logger.info(f'[CALL] <@{inter.author.id}> /distribution_add_role')

        info = db.get_guilds(inter.guild_id)[0][4:]
        if not all(info):
            await inter.response.send_message(
                'Связка роль - реакция удалена, используйте /distribution_new_message, '
                'чтобы создать сообщение выдачи ролей.', ephemeral=True)
            return

        emb = disnake.Embed(title='Выберите роли',
                            description='Поставьте реакцию для получения соответствующей роли',
                            colour=disnake.Colour.gold())

        roles = db.get_reaction4role(inter.guild_id)[:10]
        for role, react in roles:
            emb.add_field(name='', value=f'{react} - <@&{role}>', inline=False)

        mes = self.bot.get_channel(info[0]).get_partial_message(info[1])

        await mes.edit(embed=emb)
        await mes.remove_reaction(reaction, self.bot.user)

        await inter.response.send_message(
            'Связка роль - реакция удалена, сообщение с выдачей реакций обновлено.', ephemeral=True
        )

        logger.info(f'[CALL] <@{inter.author.id}> /distribution_add_role distribution`s update')


def setup(bot: commands.Bot):
    """Регистрация команд бота."""

    bot.add_cog(DistributionCommands(bot))
