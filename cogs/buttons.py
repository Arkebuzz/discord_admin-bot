import disnake

from utils.db import DB
from utils.logger import logger

db = DB()


class Voting(disnake.ui.View):
    """
    Класс добавляет к сообщению 2 кнопки: продолжить и отменить.
    """

    def __init__(self, mes_id, question, choices, time, min_values=1, max_values=1):
        self.mes_id = mes_id
        self.question = question
        self.choices = choices
        self.min_values = min_values
        self.max_values = max_values

        super().__init__(timeout=time)

    @disnake.ui.button(label='Голосовать', style=disnake.ButtonStyle.green)
    async def vote(self, _, inter: disnake.ApplicationCommandInteraction):
        class SelectMenu(disnake.ui.View):
            """
            Класс добавляет к сообщению меню с выбором.

            :attribute value: Выбор пользователя.
            """

            def __init__(self):
                super().__init__(timeout=60)
                self.value = None

            @disnake.ui.string_select(placeholder=self.question,
                                      min_values=self.min_values,
                                      max_values=self.max_values,
                                      options=[disnake.SelectOption(label=lab) for lab in self.choices])
            async def select(self, string_select: disnake.ui.StringSelect,
                             select_inter: disnake.ApplicationCommandInteraction):
                if string_select.values:
                    self.value = string_select.values

                await select_inter.response.defer()
                self.stop()

        view = SelectMenu()
        await inter.response.send_message(view=view, ephemeral=True)
        await view.wait()

        if view.value is not None:
            db.add_vote(self.mes_id, (inter.guild_id, inter.author.id, inter.author.id), view.value)

            await inter.edit_original_response('Ваш голос принят.', view=None)
            logger.info(f'[NEW VOTE] <@{inter.author.id}> question {self.question}')
        else:
            await inter.delete_original_response()

    @disnake.ui.button(label='Результаты', style=disnake.ButtonStyle.green)
    async def results(self, _, inter: disnake.ApplicationCommandInteraction):
        res = [info[2] for info in db.get_data('votes', voting_id=self.mes_id)]
        stat = []

        for key in set(res):
            d = res.count(key) / len(res)
            stat.append((key[:18],
                         '🔳' * int(d * 10) + '⬜' * (10 - int(d * 10)),
                         f'{round(100 * d, 2):.2f} % - {res.count(key)} голос'))

        emb = disnake.Embed(title=f'Результаты голосования {self.question}', color=disnake.Color.gold())

        for key, progress, info in stat:
            emb.add_field(key + ' ' + info, progress, inline=False)

        await inter.response.send_message(embed=emb, ephemeral=True)
        logger.info(f'[CALL] <@{inter.author.id}> results voting - question {self.question}')
