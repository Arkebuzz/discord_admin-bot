import sqlite3

from config import PATH_DB


class DB:
    def __init__(self, path=PATH_DB) -> None:
        self.path = path
        self.conn = sqlite3.connect(path)
        self.conn.execute('PRAGMA foreign_keys = ON;')
        self.cur = self.conn.cursor()

        self.create_db()

    def create_db(self) -> None:
        """
        Создаёт БД.

        :return: None
        """

        self.cur.execute('''CREATE TABLE IF NOT EXISTS guilds(
                       id INTEGER PRIMARY KEY,
                       analyze INTEGER,
                       log_channel INTEGER,
                       default_role INTEGER,
                       distrib_channel INTEGER,
                       distrib_message INTEGER,
                       game_channel INTEGER);
                       ''')

        self.cur.execute('''CREATE TABLE IF NOT EXISTS reaction4role(
                       guild_id INTEGER,
                       role INTEGER PRIMARY KEY,
                       reaction INTEGER UNIQUE,
                       FOREIGN KEY(guild_id) REFERENCES guilds(id) ON DELETE CASCADE);
                       ''')

        self.cur.execute('''CREATE TABLE IF NOT EXISTS users(
                       guild_id INTEGER,
                       user_id INTEGER,
                       user_name TEXT,
                       experience INTEGER,
                       messages INTEGER,
                       num_charact INTEGER,
                       num_voting INTEGER,
                       num_votes INTEGER,
                       PRIMARY KEY(guild_id, user_id),
                       FOREIGN KEY(guild_id) REFERENCES guilds(id) ON DELETE CASCADE);
                       ''')

        self.cur.execute('''CREATE TABLE IF NOT EXISTS voting(
                       id INTEGER PRIMARY KEY,
                       guild_id INTEGER,
                       channel_id INTEGER,
                       user_id INTEGER,
                       time INTEGER,
                       question TEXT,
                       min_choice INTEGER,
                       max_choice INTEGER,
                       choices TEXT,
                       FOREIGN KEY(guild_id) REFERENCES guilds(id) ON DELETE CASCADE);
                       ''')

        self.cur.execute('''CREATE TABLE IF NOT EXISTS votes(
                       voting_id INTEGER,
                       user_id INTEGER,
                       choice TEXT,
                       PRIMARY KEY(voting_id, user_id, choice),
                       FOREIGN KEY(voting_id) REFERENCES voting(id) ON DELETE CASCADE);
                       ''')

        self.cur.execute('''CREATE TABLE IF NOT EXISTS games(
                       name TEXT,
                       dlc INTEGER,
                       url TEXT PRIMARY KEY,
                       description TEXT,
                       rating TEXT,
                       date TEXT,
                       image TEXT,
                       store INTEGER);
                       ''')

        self.conn.commit()

    def get_data(self, table, columns='*', orders=None, **filters) -> list:
        """
        Получение строк из БД по введенным параметрам.

        :param table: название таблицы
        :param columns: названия нужных столбцов
        :param orders: ['column DESC/ASC']
        :param filters: столбец = значение
        :return: [[строка1], [строка2], ...]
        """

        if filters and orders:
            self.cur.execute(f'SELECT {columns} FROM {table} WHERE ' +
                             ' AND '.join(f'"{key}" = "{value}"' for key, value in filters.items()) +
                             f' ORDER BY {", ".join(orders)}')

        elif filters:
            self.cur.execute(f'SELECT {columns} FROM {table} WHERE ' +
                             ' AND '.join(f'"{key}" = "{value}"' for key, value in filters.items()))

        elif orders:
            self.cur.execute(f'SELECT {columns} FROM {table} ORDER BY {", ".join(orders)}')

        else:
            self.cur.execute(f'SELECT {columns} FROM {table}')

        return self.cur.fetchall()

    def delete_date(self, table, **filters) -> None:
        """
        Удаление строк из БД.

        :param table: название таблицы
        :param filters: столбец = значение
        :return: None
        """

        if filters:
            self.cur.execute(f'DELETE FROM {table} WHERE ' +
                             ' AND '.join(f'"{key}" = "{value}"' for key, value in filters.items()))
        else:
            self.cur.execute(f'DELETE FROM {table}')

        self.conn.commit()

    def update_guild_settings(self, guild_id, analyze=-1, log_id=-1, role_id=-1, distribution=-1, game_id=-1):
        """
        Обновляет лог и игровой каналы, роль по умолчанию и сообщение с автораздачей на сервере.

        :param guild_id: ID сервера.
        :param analyze: Сервер проанализирован?
        :param log_id: ID лог-канала.
        :param role_id: ID роли по умолчанию.
        :param distribution: (ID, ID) ID канала и ID сообщения с автораздачей ролей.
        :param game_id: ID канала для оповещений об играх.
        :return: None
        """

        if log_id == -1 and role_id == -1 and distribution == -1 and analyze == -1 and game_id == -1:
            self.cur.execute('INSERT INTO guilds VALUES(?, 0, NULL, NULL, NULL, NULL, NULL) '
                             'ON CONFLICT (id) DO NOTHING',
                             (guild_id,))

        if analyze != -1:
            self.cur.execute('INSERT INTO guilds VALUES(?, ?, NULL, NULL, NULL, NULL, NULL) '
                             'ON CONFLICT (id) DO UPDATE SET analyze = ?',
                             (guild_id, analyze, analyze))

        if log_id != -1:
            self.cur.execute('INSERT INTO guilds VALUES(?, 0, ?, NULL, NULL, NULL, NULL) '
                             'ON CONFLICT (id) DO UPDATE SET log_channel = ?',
                             (guild_id, log_id, log_id))

        if role_id != -1:
            self.cur.execute('INSERT INTO guilds VALUES(?, 0, NULL, ?, NULL, NULL, NULL) '
                             'ON CONFLICT (id) DO UPDATE SET default_role = ?',
                             (guild_id, role_id, role_id))

        if distribution != -1:
            self.cur.execute('INSERT INTO guilds VALUES(?, 0, NULL, NULL, ?, ?, NULL) '
                             'ON CONFLICT (id) DO UPDATE SET distrib_channel = ?, distrib_message = ?',
                             (guild_id, *distribution, *distribution))

        if game_id != -1:
            self.cur.execute('INSERT INTO guilds VALUES(?, 0, NULL, NULL, NULL, NULL, ?) '
                             'ON CONFLICT (id) DO UPDATE SET game_channel = ?',
                             (guild_id, game_id, game_id))

        self.conn.commit()

    def update_reaction4role(self, guild_id, role_id, reaction):
        """
        Обновляет связку роль - реакция на сервере.

        :param guild_id: ID сервера.
        :param role_id: ID роли.
        :param reaction: Эмодзи.
        :return: None | -1
        """

        self.update_guild_settings(guild_id)

        try:
            self.cur.execute('INSERT INTO reaction4role VALUES(?, ?, ?)',
                             (guild_id, role_id, reaction))
            self.conn.commit()

        except sqlite3.Error:
            return -1

    def update_user(self, guild_id, user_id, user_name, len_message=0, num_attach=0, voting=(0, 0)):
        """
        Обновляет статистику пользователя на сервере.

        :param guild_id: ID сервера.
        :param user_id: ID пользователя.
        :param user_name: Имя пользователя.
        :param len_message: Длина сообщения.
        :param num_attach: Количество вложений.
        :param voting: (int(bool), int(bool)) [0] - новое голосование, [1] - новый голос.
        :return: None
        """

        self.update_guild_settings(guild_id)

        e = 2.718281828459045
        l_m = len_message / 100
        exp = int(30 * (e ** l_m - e ** -l_m) / (e ** l_m + e ** -l_m))

        exp += num_attach * 7
        exp += voting[0] * 30
        exp += voting[1] * 5

        self.cur.execute('INSERT INTO users VALUES(?, ?, ?, ?, 1, ?, ?, ?) ON CONFLICT DO UPDATE '
                         'SET experience = experience + ?, messages = messages + 1, num_charact = num_charact + ?,'
                         'num_voting = num_voting + ?, num_votes = num_votes + ?',
                         (guild_id, user_id, user_name, exp, len_message, *voting, exp, len_message, *voting))

        self.conn.commit()

    def add_voting(self, mes_id, channel_id, user_info, question, time, min_choices, max_choices, answers):
        """
        Создаёт новое голосование.

        :param mes_id: ID сообщения с голосованием.
        :param channel_id: ID канала.
        :param user_info: (guild_id, user_id, user_name)
        :param question: Название голосования.
        :param time: Время, когда вопрос завершится (секунды).
        :param min_choices: Минимум выборов.
        :param max_choices: Максимум выборов.
        :param answers: Варианты ответов.
        :return: None
        """

        self.update_guild_settings(user_info[0])
        self.update_user(*user_info, voting=(1, 0))

        self.cur.execute('INSERT INTO voting VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)',
                         (mes_id, user_info[0], channel_id, user_info[1], time, question, min_choices, max_choices,
                          '!|?'.join(answers)))

        self.conn.commit()

    def add_vote(self, mes_id, user_info, choice):
        """
        Принимает новый голос.

        :param mes_id: ID сообщения с голосованием (ID голосования).
        :param user_info: (guild_id, user_id, user_name) проголосовавшего.
        :param choice: [str] массив с вариантами ответов.
        :return: None
        """

        self.cur.execute('SELECT * FROM votes WHERE voting_id = ? AND user_id = ?', (mes_id, user_info[1]))

        if self.cur.fetchall():
            self.cur.execute('DELETE FROM votes WHERE voting_id = ? AND user_id = ?', (mes_id, user_info[1]))
        else:
            self.update_user(*user_info, voting=(0, 1))

        self.cur.executemany('INSERT INTO votes VALUES(?, ?, ?)',
                             ((mes_id, user_info[1], ch) for ch in choice))

        self.conn.commit()

    def add_game(self, game):
        """
        Добавляет новую игры в БД.

        :param game
        :return: None
        """
        self.cur.execute('INSERT INTO games VALUES(?, ?, ?, ?, ?, ?, ?, ?)',
                         (*game,))

        self.conn.commit()
