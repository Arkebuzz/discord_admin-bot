import asyncio

import disnake
import yt_dlp
from disnake.ext import commands

from config import PATH_FFMPEG
from utils.logger import logger

ytdl_params = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,  # Принудительно использовать в названиях файлов только ASCII
    'extract_flat': 'in_playlist',
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

ytdl = yt_dlp.YoutubeDL(ytdl_params)

guilds_queue = {}


class YTDLSource(disnake.PCMVolumeTransformer):
    def __init__(self, title, source: disnake.AudioSource, volume: float = 0.5):
        super().__init__(source, volume)

        self.title = title

    @staticmethod
    async def download(loop, url):
        try:
            return await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
        except yt_dlp.DownloadError as e:
            return e

    @classmethod
    def adder(cls, file, guild_id):
        if guild_id not in guilds_queue:
            return KeyError

        guilds_queue[guild_id] = (
                guilds_queue[guild_id] +
                [cls(file['title'],
                     disnake.FFmpegPCMAudio(file['url'], executable=PATH_FFMPEG, **ffmpeg_options))]
        )

    @classmethod
    async def from_url(cls, guild_id, url, loop: asyncio.AbstractEventLoop):
        data = await cls.download(loop, url)

        if type(data) is yt_dlp.DownloadError:
            return data

        if guild_id not in guilds_queue:
            guilds_queue[guild_id] = []

        if 'entries' in data:
            for file in data['entries']:
                file = await cls.download(loop, file['url'])

                if cls.adder(file, guild_id) is not None:
                    return
        else:
            cls.adder(data, guild_id)


class Music(commands.Cog):
    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot

    def next_music(self, guild, channel):
        """Переключение на следующий трек"""

        logger.info(f'[IN PROGRESS] {guild.id} next_music')

        queue = guilds_queue.setdefault(guild.id, [])

        guilds_queue[guild.id] = queue[1:] if len(queue) > 1 else []

        self.bot.loop.create_task(self.play(guild, channel))

    async def play(self, guild, channel):
        """Запуск очереди музыки"""

        queue = guilds_queue.setdefault(guild.id, [])

        vc: disnake.VoiceClient = guild.voice_client

        if queue and vc:
            vc.play(queue[0], after=lambda _: self.next_music(guild, channel))
            await channel.send(f'Сейчас играет: {queue[0].title}')
            logger.info(f'[IN PROGRESS] {guild.id} music_play')
        elif vc:
            await channel.send('Добавьте музыку в очередь командой /music_add2queue.')

    @commands.slash_command(
        name='music_add2queue',
        description='Добавить музыку в очередь.'
    )
    async def music_add2queue(self, inter: disnake.ApplicationCommandInteraction,
                              name: str = commands.Param(description='Название трека или ссылка')):
        """Добавляет музыку по ссылке в очередь."""

        logger.info(f'[CALL] <@{inter.author.id}> /music_add2queue')

        await inter.response.send_message('Обрабатываю...', ephemeral=True)

        vc: disnake.VoiceClient = inter.guild.voice_client

        player = await YTDLSource.from_url(inter.guild_id, name, loop=self.bot.loop)

        if type(player) is yt_dlp.utils.DownloadError:
            await inter.edit_original_response(str(player))
            return

        if vc and not vc.is_playing():
            await self.bot.loop.create_task(self.play(inter.guild, inter.channel))

        await inter.edit_original_response('Все элементы добавлены в очередь.')

    @commands.slash_command(
        name='music_connect',
        description='Присоединиться к голосовому каналу.'
    )
    async def music_connect(self, inter: disnake.ApplicationCommandInteraction, channel: disnake.VoiceChannel = None):
        """Присоединяет бота к голосовому каналу."""

        try:
            if channel is None:
                channel = inter.user.voice.channel

            if inter.guild.voice_client is None:
                await channel.connect()
            else:
                await inter.guild.voice_client.move_to(channel)

            await inter.response.send_message('Подключение выполнено.', ephemeral=True)

            logger.info(f'[IN PROGRESS] is connected to {channel}')

            return 1

        except AttributeError:
            await inter.response.send_message('Вы не присоединены ни к одному каналу.', ephemeral=True)

        except disnake.errors.Forbidden:
            await inter.response.send_message('Я не могу присоединиться к вашему каналу.', ephemeral=True)

    @commands.slash_command(
        name='music_play',
        description='Начать воспроизведение/снять с паузы.'
    )
    async def music_play(self, inter: disnake.ApplicationCommandInteraction):
        """Запускает очередь."""

        logger.info(f'[CALL] <@{inter.author.id}> /music_play')

        vc: disnake.VoiceClient = inter.guild.voice_client

        await inter.response.defer(ephemeral=True)

        if not vc:
            await inter.edit_original_response(
                'Я не подключен ни к одному каналу, выполните подключение с помощью /music_connect.',
            )
        elif vc and vc.is_playing():
            await inter.edit_original_response('Уже играет.')
        else:
            await inter.delete_original_response()
            await self.bot.loop.create_task(self.play(inter.guild, inter.channel))

    @commands.slash_command(
        name='music_queue',
        description='Получить очередь музыки.'
    )
    async def music_queue(self, inter: disnake.ApplicationCommandInteraction):
        """Показать очередь музыки."""

        logger.info(f'[CALL] <@{inter.author.id}> /music_queue')

        await inter.response.send_message(
            'Очередь музыки:\n' +
            '\n'.join(m.title for m in guilds_queue.setdefault(inter.guild_id, []))[:1950],
            ephemeral=True
        )

    @commands.slash_command(
        name='music_pause',
        description='Поставить музыку на паузу.'
    )
    async def music_pause(self, inter: disnake.ApplicationCommandInteraction):
        """Поставить музыку на паузу."""

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
        """Переключиться на следующий трек."""

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
        """Очистить очередь музыки."""

        logger.info(f'[CALL] <@{inter.author.id}> /music_clear')

        vc: disnake.VoiceClient = inter.guild.voice_client

        try:
            vc.stop()
        except (AttributeError, TypeError):
            pass

        try:
            del guilds_queue[inter.guild_id]
        except KeyError:
            pass

        await inter.response.send_message('Очередь музыки очищена.')

    @commands.slash_command(
        name='music_stop',
        description='Отключиться от голосового канала и очистить очередь.'
    )
    async def stop(self, inter: disnake.ApplicationCommandInteraction):
        """Остановить музыку и отключиться от голосового канала."""

        logger.info(f'[CALL] <@{inter.author.id}> /music_stop')

        try:
            await inter.guild.voice_client.disconnect(force=False)
        except (AttributeError, commands.errors.CommandInvokeError):
            pass

        try:
            del guilds_queue[inter.guild_id]
        except KeyError:
            pass

        await inter.response.send_message('Отключение выполнено, очередь музыки очищена.')


def setup(bot: commands.InteractionBot):
    """Регистрация команд бота."""

    bot.add_cog(Music(bot))
