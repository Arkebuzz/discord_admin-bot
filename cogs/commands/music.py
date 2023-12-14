import asyncio
from typing import Any, Dict

import disnake
import yt_dlp
from disnake.ext import commands

from config import PATH_FFMPEG
from utils.logger import logger

yt_dlp.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 4096',
    'options': '-vn',
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

guilds_queue = {}
guilds_player = {}


class YTDLSource(disnake.PCMVolumeTransformer):
    def __init__(self, title, source: disnake.AudioSource, volume: float = 0.5):
        super().__init__(source, volume)

        self.title = title

    @classmethod
    async def from_url(cls, guild, url, loop: asyncio.AbstractEventLoop):
        try:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
        except yt_dlp.DownloadError as e:
            return e

        if 'entries' in data:
            for file in data['entries']:
                guilds_queue[guild] = (
                        guilds_queue.setdefault(guild, []) +
                        [cls(file['title'], disnake.FFmpegPCMAudio(file['url'], executable=PATH_FFMPEG, **ffmpeg_options))]
                )


class Music(commands.Cog):
    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot

    @staticmethod
    async def join(inter):
        """Присоединение к голосовому каналу"""

        try:
            if inter.guild.voice_client is None:
                await inter.user.voice.channel.connect()
            else:
                await inter.guild.voice_client.move_to(inter.user.voice.channel)

            await inter.edit_original_response('Подключение выполнено.')

            logger.info(f'[IN PROGRESS] is connected to {inter.user.voice.channel}')

            return 1

        except AttributeError:
            await inter.edit_original_response('Вы не присоединены ни к одному каналу.')

        except disnake.errors.Forbidden:
            await inter.edit_original_response('Я не могу присоединиться к вашему каналу.')

    def next_music(self, guild, channel):
        """Переключение на следующий трек"""

        logger.info(f'[IN PROGRESS] {guild.id} next_music')

        queue = guilds_queue.setdefault(guild.id, [])

        guilds_queue[guild.id] = queue[1:] if len(queue) > 1 else []

        if not guilds_player.setdefault(guild.id, False):
            self.bot.loop.create_task(self.play(guild, channel))

    async def play(self, guild, channel):
        """Запуск очереди музыки"""

        guilds_player[guild.id] = True
        queue = guilds_queue.setdefault(guild.id, [])

        vc: disnake.VoiceClient = guild.voice_client

        if queue:
            vc.play(queue[0], after=lambda _: self.next_music(guild, channel))
            await channel.send(f'Сейчас играет: {queue[0].title}')
            logger.info(f'[IN PROGRESS] {guild.id} music_play')
        else:
            await channel.send('Добавьте музыку в очередь командой /music_add2queue.')

        guilds_player[guild.id] = False

    @commands.slash_command(
        name='music_add2queue',
        description='Добавить музыку в очередь.'
    )
    async def music_add2queue(self, inter: disnake.ApplicationCommandInteraction,
                              name: str = commands.Param(description='Название трека или ссылка')):
        """
        Добавляет музыку по ссылке в очередь.
        """

        logger.info(f'[CALL] <@{inter.author.id}> /music_add2queue')

        await inter.response.send_message('Обрабатываю...', ephemeral=True)

        vc: disnake.VoiceClient = inter.guild.voice_client

        player = await YTDLSource.from_url(inter.guild_id, name, loop=self.bot.loop)

        if type(player) is yt_dlp.utils.DownloadError:
            await inter.edit_original_response(str(player))
            return

        if vc and not vc.is_playing() and not guilds_player.setdefault(inter.guild_id, False):
            self.bot.loop.create_task(self.play(inter.guild, inter.channel))

        await inter.edit_original_response(f'Все элементы добавлены в очередь.')

    @commands.slash_command(
        name='music_queue',
        description='Получить очередь музыки.'
    )
    async def music_queue(self, inter: disnake.ApplicationCommandInteraction):
        """
        Показать очередь музыки.
        """

        logger.info(f'[CALL] <@{inter.author.id}> /music_queue')

        await inter.response.send_message(
            'Очередь музыки:\n' +
            '\n'.join(m.title for m in guilds_queue.setdefault(inter.guild_id, []))[:1950],
            ephemeral=True
        )

    @commands.slash_command(
        name='music_play',
        description='Запустить музыку в очереди.'
    )
    async def music_play(self, inter: disnake.ApplicationCommandInteraction):
        """
        Запускает очередь.
        """

        logger.info(f'[CALL] <@{inter.author.id}> /music_play')

        await inter.response.defer(ephemeral=True)

        if await self.join(inter) is None:
            return

        vc: disnake.VoiceClient = inter.guild.voice_client

        if vc and vc.is_playing():
            await inter.send('Уже играет.', ephemeral=True)

        elif not guilds_player.setdefault(inter.guild_id, False):
            self.bot.loop.create_task(self.play(inter.guild, inter.channel))

    @commands.slash_command(
        name='music_pause',
        description='Поставить музыку на паузу.'
    )
    async def music_pause(self, inter: disnake.ApplicationCommandInteraction):
        """
        Поставить музыку на паузу.
        """

        logger.info(f'[CALL] <@{inter.author.id}> /music_pause')

        vc: disnake.VoiceClient = inter.guild.voice_client
        if vc is not None:
            vc.pause()

        await inter.response.send_message('Музыка приостановлена.')

    @commands.slash_command(
        name='music_next',
        description='Переключиться на следующую музыку.'
    )
    async def music_next(self, inter: disnake.ApplicationCommandInteraction):
        """
        Переключиться на следующий трек.
        """

        logger.info(f'[CALL] <@{inter.author.id}> /music_next')

        await inter.response.defer()
        await inter.delete_original_response()

        vc: disnake.VoiceClient = inter.guild.voice_client
        if vc is not None:
            vc.stop()

    @commands.slash_command(
        name='music_clear',
        description='Очистить очередь музыки.'
    )
    async def music_clear(self, inter: disnake.ApplicationCommandInteraction):
        """
        Очистить очередь музыки.
        """

        logger.info(f'[CALL] <@{inter.author.id}> /music_clear')

        vc: disnake.VoiceClient = inter.guild.voice_client

        try:
            vc.stop()
        except (AttributeError, TypeError):
            pass

        try:
            del guilds_queue[inter.guild_id]
            del guilds_player[inter.guild_id]
        except KeyError:
            pass

        await inter.response.send_message('Очередь музыки очищена.')

    @commands.slash_command(
        name='music_stop',
        description='Отключиться от голосового канала и очистить очередь.'
    )
    async def stop(self, inter: disnake.ApplicationCommandInteraction):
        """
        Остановить музыку и отключиться от голосового канала.
        """

        logger.info(f'[CALL] <@{inter.author.id}> /music_stop')

        try:
            await inter.guild.voice_client.disconnect()

        except (AttributeError, commands.errors.CommandInvokeError):
            pass

        try:
            del guilds_queue[inter.guild_id]
            del guilds_player[inter.guild_id]
        except KeyError:
            pass

        await inter.response.send_message('Отключение выполнено, очередь музыки очищена.')


def setup(bot: commands.InteractionBot):
    """Регистрация команд бота."""

    bot.add_cog(Music(bot))
