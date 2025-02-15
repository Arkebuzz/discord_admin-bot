import disnake
import emoji
from disnake.ext import commands

from utils.db import DB
from utils.logger import logger


class DistributionCommands(commands.Cog):
    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot
        self.db = DB()

    @commands.slash_command(
        name='set_default_role',
        description='Изменить стандартную роль для новых участников.',
        default_member_permissions=disnake.Permissions(8)
    )
    async def set_default_role(self, inter: disnake.ApplicationCommandInteraction, role: disnake.Role):
        """Обновляет связку роль - реакция на сервере."""

        if role.is_default():
            self.db.update_guild_settings(inter.guild_id, role_id='NULL')
            await inter.response.send_message('Роль по умолчанию сброшена.', ephemeral=True)

            logger.info(f'[CALL] <@{inter.author.id}> /set_default_role role`s del')

        elif not role.is_assignable():
            await inter.response.send_message(
                'Невозможно настроить роль по умолчанию, данная роль превосходит роль бота.', ephemeral=True
            )

            logger.info(f'[CALL] <@{inter.author.id}> /set_default_role incorrect role')

        else:
            self.db.update_guild_settings(inter.guild_id, role_id=role.id)
            await inter.response.send_message('Роль по умолчанию настроена.', ephemeral=True)

            logger.info(f'[CALL] <@{inter.author.id}> /set_default_role role`s append')

    @commands.slash_command(
        name='distribution_new_message',
        description='Отправить сообщение автовыдачи ролей по эмодзи.',
        default_member_permissions=disnake.Permissions(8)
    )
    async def distribution_new_message(self, inter: disnake.ApplicationCommandInteraction):
        """Отправляет новое сообщение с автовыдачей ролей по эмодзи."""

        if not inter.channel.permissions_for(inter.guild.me).add_reactions:
            await inter.response.send_message('Я не могу ставить реакции в данном канале.', ephemeral=True)

            logger.info(f'[CALL] <@{inter.author.id}> /distribution_new_message forbidden add_reactions')
            return

        emb = disnake.Embed(
            title='Выбери роли',
            description='Поставь реакцию для получения соответствующей роли.',
            colour=disnake.Colour.gold()
        )

        roles = self.db.get_data('reaction4role', 'role, reaction', guild_id=inter.guild_id)[:10]
        for role, reaction in roles:
            emb.add_field(name='', value=f'{reaction} - <@&{role}>', inline=False)

        await inter.response.send_message(embed=emb)
        mes = await inter.original_message()

        for _, reaction in roles:
            await mes.add_reaction(reaction)

        self.db.update_guild_settings(inter.guild_id, distribution=(inter.channel_id, mes.id))

        logger.info(f'[CALL] <@{inter.author.id}> /distribution_new_message')

    @commands.slash_command(
        name='distribution_add_role',
        description='Добавить роль к автовыдаче по эмодзи.',
        default_member_permissions=disnake.Permissions(8)
    )
    async def distribution_add_role(
            self, inter: disnake.ApplicationCommandInteraction, role: disnake.Role,
            reaction: str = commands.Param(description='Смайлик, который будет связан с этой ролью')
    ):
        """Обновляет связку роль - реакция на сервере."""

        if not inter.channel.permissions_for(inter.guild.me).add_reactions:
            await inter.response.send_message('Я не могу ставить реакции в данном канале.')

            logger.info(f'[CALL] <@{inter.author.id}> /distribution_add_role forbidden add_reactions')

        elif role.is_default() or not role.is_assignable():
            await inter.response.send_message(
                'Невозможно добавить связку роль - реакция, данная роль превосходит роль '
                'бота или является ролью по умолчанию.', ephemeral=True
            )

            logger.info(f'[CALL] <@{inter.author.id}> /distribution_add_role incorrect role')

        elif emoji.is_emoji(reaction):
            if self.db.update_reaction4role(inter.guild_id, role.id, reaction) == -1:
                await inter.response.send_message(
                    'Невозможно добавить связку роль - реакция, данная реакция или роль уже участвует в раздаче, '
                    'вы можете удалить лишние связки роль-реакция командой /distribution_del_role', ephemeral=True
                )

                logger.info(f'[CALL] <@{inter.author.id}> /distribution_add_role role or reaction is used')
                return

            logger.info(f'[CALL] <@{inter.author.id}> /distribution_add_role role`s append')

            info = self.db.get_data('guilds', id=inter.guild_id)[0][4:6]
            if not all(info):
                await inter.response.send_message(
                    'Связка роль - реакция добавлена, используй /distribution_new_message, '
                    'чтобы создать сообщение выдачи ролей.', ephemeral=True
                )
                return

            emb = disnake.Embed(
                title='Выбери роли',
                description='Поставь реакцию для получения соответствующей роли',
                colour=disnake.Colour.gold()
            )

            roles = self.db.get_data('reaction4role', 'role, reaction', guild_id=inter.guild_id)[:10]
            for role, react in roles:
                emb.add_field(name='', value=f'{react} - <@&{role}>', inline=False)

            try:
                mes = await self.bot.get_channel(info[0]).get_partial_message(info[1]).edit(embed=emb)
            except (disnake.errors.NotFound, disnake.errors.Forbidden):
                await inter.response.send_message(
                    'Связка роль - реакция добавлена, старое сообщение с раздачей недоступно, '
                    'используй /distribution_new_message, чтобы создать сообщение выдачи ролей.', ephemeral=True
                )
            else:
                await mes.add_reaction(reaction)

                await inter.response.send_message(
                    'Связка роль - реакция добавлена, сообщение с выдачей реакций обновлено.', ephemeral=True
                )

            logger.info(f'[CALL] <@{inter.author.id}> /distribution_add_role distribution`s update')

        else:
            await inter.response.send_message(
                'Невозможно добавить связку роль - реакция, переданная реакция не является смайликом.', ephemeral=True
            )

            logger.info(f'[CALL] <@{inter.author.id}> /distribution_add_role reaction isn`t emoji')

    @commands.slash_command(
        name='distribution_del_role',
        description='Удалить роль из автовыдачи по эмодзи.',
        default_member_permissions=disnake.Permissions(8)
    )
    async def distribution_del_role(self, inter: disnake.ApplicationCommandInteraction, role: disnake.Role):
        """Удаляет связку роль - реакция на сервере."""

        if not inter.channel.permissions_for(inter.guild.me).add_reactions:
            await inter.response.send_message('Я не могу ставить реакции в данном канале.')

            logger.info(f'[CALL] <@{inter.author.id}> /distribution_del_role forbidden add_reactions')
            return

        reaction = self.db.get_data('reaction4role', 'reaction', guild_id=inter.guild_id, role=role.id)
        self.db.delete_date('reaction4role', guild_id=inter.guild_id, role=role.id)

        if reaction:
            reaction = reaction[0][0]
        else:
            await inter.response.send_message(
                'Данной роли нет в раздаче, используй /distribution_add_role, '
                'чтобы добавить роль к раздаче.', ephemeral=True
            )

            logger.info(f'[CALL] <@{inter.author.id}> /distribution_del_role this role isn`t used')
            return

        logger.info(f'[CALL] <@{inter.author.id}> /distribution_del_role role is deleted')

        info = self.db.get_data('guilds', id=inter.guild_id)[0][4:6]
        if not all(info):
            await inter.response.send_message(
                'Связка роль - реакция удалена, используй /distribution_new_message, '
                'чтобы создать сообщение выдачи ролей.', ephemeral=True
            )
            return

        emb = disnake.Embed(
            title='Выбери роли',
            description='Поставь реакцию для получения соответствующей роли',
            colour=disnake.Colour.gold()
        )

        roles = self.db.get_data('reaction4role', 'role, reaction', guild_id=inter.guild_id)[:10]
        for role, react in roles:
            emb.add_field(name='', value=f'{react} - <@&{role}>', inline=False)

        try:
            mes = await self.bot.get_channel(info[0]).get_partial_message(info[1]).edit(embed=emb)
        except (disnake.errors.NotFound, disnake.errors.Forbidden):
            await inter.response.send_message(
                'Связка роль - реакция удалена, старое сообщение с раздачей недоступно, '
                'используй /distribution_new_message, чтобы создать сообщение выдачи ролей.', ephemeral=True
            )
        else:
            await mes.remove_reaction(reaction, self.bot.user)

            await inter.response.send_message(
                'Связка роль - реакция удалена, сообщение с выдачей реакций обновлено.', ephemeral=True
            )

        logger.info(f'[CALL] <@{inter.author.id}> /distribution_add_role distribution`s update')


def setup(bot: commands.InteractionBot):
    """Регистрация команд бота."""

    bot.add_cog(DistributionCommands(bot))
