import time

import disnake
from disnake.ext import commands

from cogs.buttons import Voting
from utils.db import DB
from utils.logger import logger


class VotingCommands(commands.Cog):
    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot
        self.db = DB()

    @commands.slash_command(
        name='voting_new',
        description='Создать голосование.',
    )
    async def voting_new(self, inter: disnake.ApplicationCommandInteraction,
                         question: str = commands.Param(description='Вопрос голосования'),
                         timer: str = commands.Param(
                             description='Время на голосование (1m/1h/1d)',
                             default='1d', min_length=2
                         ),
                         min_choices: int = commands.Param(
                             description='Минимальное число вариантов, которые может выбрать голосующий',
                             default=1, min_value=1, max_value=10
                         ),
                         max_choices: int = commands.Param(
                             description='Максимальное число вариантов, которые может выбрать голосующий',
                             default=1, min_value=1, max_value=10
                         ),
                         answer0: str | None = commands.Param(description='Вариант ответа', default=None),
                         answer1: str | None = commands.Param(description='Вариант ответа', default=None),
                         answer2: str | None = commands.Param(description='Вариант ответа', default=None),
                         answer3: str | None = commands.Param(description='Вариант ответа', default=None),
                         answer4: str | None = commands.Param(description='Вариант ответа', default=None),
                         answer5: str | None = commands.Param(description='Вариант ответа', default=None),
                         answer6: str | None = commands.Param(description='Вариант ответа', default=None),
                         answer7: str | None = commands.Param(description='Вариант ответа', default=None),
                         answer8: str | None = commands.Param(description='Вариант ответа', default=None),
                         answer9: str | None = commands.Param(description='Вариант ответа', default=None),
                         ):
        """Слэш-команда, создаёт новое голосование."""

        sl = {'m': 60, 'h': 3600, 'd': 86400}

        try:
            timer = time.time() + int(timer[:-1]) * sl[timer[-1]]

            if min_choices > max_choices:
                raise NameError
        except (ValueError, TypeError, KeyError):
            emb = disnake.Embed(title='Неправильно указано время голосования!', color=disnake.Color.red())
            await inter.response.send_message(embed=emb, ephemeral=True)
            return
        except NameError:
            emb = disnake.Embed(
                title='Неправильно указаны минимальное и максимальное числа вариантов, которые может выбрать голосующий!',
                color=disnake.Color.red()
            )
            await inter.response.send_message(embed=emb, ephemeral=True)
            return

        await inter.response.defer()

        answers = {
            a for a in (answer0, answer1, answer2, answer3, answer4, answer5, answer6, answer7, answer8, answer9) if
            a is not None
        }

        if not answers:
            answers = {'Да', 'Нет'}

        emb = disnake.Embed(title=question, color=disnake.Color.gold())
        emb.add_field('Завершится', f'<t:{int(timer)}:R>')
        emb.add_field('Вариантов', 'от ' + str(min_choices) + ' до ' + str(max_choices))
        emb.add_field('Варианты:', '\n'.join(answers), inline=False)
        emb.set_footer(text=inter.author, icon_url=inter.author.avatar)

        msg = await inter.original_message()

        self.db.add_voting(
            msg.id, inter.channel_id, (inter.guild_id, inter.author.id, inter.author.name),
            question, timer, min_choices, max_choices, answers
        )

        view = Voting(msg.id, question, answers, timer - time.time(), min_choices, max_choices)
        await inter.edit_original_response(embed=emb, view=view)

        logger.info(f'[CALL] <@{inter.author.id}> /voting_new : question {question}')


def setup(bot: commands.InteractionBot):
    """Регистрация команд бота."""

    bot.add_cog(VotingCommands(bot))
