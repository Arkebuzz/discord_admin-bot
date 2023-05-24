import disnake

from disnake.ext import commands
from tabulate import tabulate

from main import db
from utils.logger import logger

PARAM_SORT = {
    'Опыт': ('experience', 3),
    'Сообщений': ('messages', 4),
    'Символов': ('num_charact', 5),
    'Голосов': ('num_voting', 6),
    'Голосований': ('num_votes', 7)
}


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

        db_info = db.get_users(inter.guild_id, user_id=user.id)

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
    async def user_top(self, inter: disnake.ApplicationCommandInteraction,
                       sort_by: str = commands.Param(choices=PARAM_SORT.keys(), default='Опыт')):

        info = db.get_users(inter.guild_id, sort_by=PARAM_SORT[sort_by][0])
        number = [i[1] for i in info].index(inter.author.id)

        emb = disnake.Embed(title=f'Топ пользователей по {sort_by}', colour=disnake.Colour.gold())
        emb.add_field('', f'{inter.author.name}, вы находитесь на {number + 1} месте.', inline=False)
        emb.add_field(
            '',
            '```' +
            tabulate([(user[2], user[PARAM_SORT[sort_by][1]]) for user in info[:10]],
                     ['Участник', sort_by], 'fancy_grid', maxcolwidths=[18, None]) +
            '```'
        )

        await inter.response.send_message(embed=emb)
        logger.info(f'[CALL] <@{inter.author.id}> /user_top')


def setup(bot: commands.Bot):
    """Регистрация команд бота."""

    bot.add_cog(StatisticCommands(bot))