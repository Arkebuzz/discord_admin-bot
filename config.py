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

__version__ = 'v0.10.5'
__version_info__ = (f'```diff\n{__version__}\n'
                    '~Все бесплатные игры из EpicGames больше не обозначены как DLC, '
                    'а считаются играми (даже если они DLC);\n'
                    '~Работа с музыкой опять переработана, повышена стабильности работы с YouTube, '
                    'добавлена теоретическая возможность работы с совместимыми с yt-dlp видео-ресурсами.'
                    '```')
