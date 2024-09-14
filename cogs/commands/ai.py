import disnake
from disnake.ext import commands
from duckduckgo_search import AsyncDDGS

from utils.logger import logger

models = ['gpt-4o-mini', 'claude-3-haiku', 'llama-3.1-70b', 'mixtral-8x7b']


class AICommands(commands.Cog):
    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot

    @commands.slash_command(
        name='ai',
        description='Спросить у ИИ.',
    )
    async def ai(
            self, inter: disnake.ApplicationCommandInteraction, query: str,
            model: str = commands.Param(choices=models, default='gpt-4o-mini', description='Модель ИИ')
    ):
        """Слэш-команда, отправляет ответ от нейронок DuckDuckGo."""

        await inter.response.defer()

        ddg = AsyncDDGS(timeout=30)
        res = await ddg.achat(query, model, 60)
        await inter.edit_original_response('```yaml\n[' + model + ' на запрос: ' + query + ']```\n' + res)

        logger.info(f'[CALL] <@{inter.author.id}> /ai query: {query[:100]}')


def setup(bot: commands.InteractionBot):
    """Регистрация команд бота."""

    bot.add_cog(AICommands(bot))
