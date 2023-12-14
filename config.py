TOKEN = 'YOUR TOKEN'

PATH_FFMPEG = 'utils/ffmpeg.exe'    # Путь к ffmpeg.exe

PATH_DATA = 'data'                  # Папка для хранения БД и лога
PATH_DB = PATH_DATA + '/guilds.db'  # Путь к БД
PATH_LOG = PATH_DATA + '/log.log'   # Путь к файлу лога

__version__ = 'v0.10.2'
__version_info__ = (f'```diff\n{__version__}\n'
                    '+Добавлена поддержка воспроизведения музыки из плейлистов.\n'
                    '~Повышение стабильности (или наоборот) музыкального плеера.\n'
                    '~Исправление ошибок.\n'
                    '```')
