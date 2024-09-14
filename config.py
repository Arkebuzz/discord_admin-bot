from sys import platform

TOKEN = 'YOUR TOKEN'

# Путь к ffmpeg.exe
if platform in ('win32', 'cygwin'):
    PATH_FFMPEG = 'utils/ffmpeg.exe'
else:
    PATH_FFMPEG = 'ffmpeg'

PATH_DATA = 'data'  # Папка для хранения БД и лога
PATH_DB = PATH_DATA + '/guilds.db'  # Путь к БД
PATH_LOG = PATH_DATA + '/log.log'  # Путь к файлу лога

__version__ = 'v0.11'
__version_info__ = (f'```diff\n{__version__}\n'
                    '+Добавлена возможность использовать модели ИИ доступные на DuckAI '
                    '(gpt-4o-mini, claude-3-haiku, llama-3.1-70b, mixtral-8x7b).\n'
                    '~Другие мелкие измененения.'
                    '```')
