import sqlite3

from config import PATH_DB


class DB:
    def __init__(self, path=PATH_DB):
        self.path = path
        self.conn = sqlite3.connect(path)
        self.conn.execute('PRAGMA foreign_keys = ON;')
        self.cur = self.conn.cursor()

        self.create_db()

    def create_db(self):
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
                       distrib_message INTEGER);
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

        self.conn.commit()

    def update_guild_settings(self, guild_id, analyze=None, log_id=None, role_id=None, distribution=None):
        """
        Обновляет лог-канал и сообщение с автораздачей на сервере.

        :param guild_id: ID сервера.
        :param analyze: Сервер проанализирован?
        :param log_id: ID лог-канала.
        :param role_id: ID роли по умолчанию.
        :param distribution: (ID, ID) ID канала и ID сообщения с автораздачей ролей.
        :return: None
        """

        if log_id is None and role_id is None and distribution is None and analyze is None:
            self.cur.execute('INSERT INTO guilds VALUES(?, 0, NULL, NULL, NULL, NULL) '
                             'ON CONFLICT (id) DO NOTHING',
                             (guild_id,))

        if analyze is not None:
            self.cur.execute('INSERT INTO guilds VALUES(?, ?, NULL, NULL, NULL, NULL) '
                             'ON CONFLICT (id) DO UPDATE SET analyze = ?',
                             (guild_id, analyze, analyze))

        if log_id is not None:
            self.cur.execute('INSERT INTO guilds VALUES(?, 0, ?, NULL, NULL, NULL) '
                             'ON CONFLICT (id) DO UPDATE SET log_channel = ?',
                             (guild_id, log_id, log_id))

        if role_id is not None:
            self.cur.execute('INSERT INTO guilds VALUES(?, 0, NULL, ?, NULL, NULL) '
                             'ON CONFLICT (id) DO UPDATE SET default_role = ?',
                             (guild_id, role_id, role_id))

        if distribution is not None:
            self.cur.execute('INSERT INTO guilds VALUES(?, 0, NULL, NULL, ?, ?) '
                             'ON CONFLICT (id) DO UPDATE SET distrib_channel = ?, distrib_message = ?',
                             (guild_id, *distribution, *distribution))

        self.conn.commit()

    def get_guilds(self, guild_id=None):
        """
        Возвращает сервера бота c введенным ID, если ID не передан, то возвращает все сервера.

        :param guild_id: ID сервера.
        :return: [[id, analyze, log_channel, default_role, distrib_channel, distrib_message]]
        """

        if guild_id is None:
            self.cur.execute('SELECT * FROM guilds;')
        else:
            self.cur.execute('SELECT * FROM guilds WHERE id = ?;', (guild_id,))

        res = self.cur.fetchall()

        return res

    def delete_guild(self, guild_id):
        """
        Удаление сервер из БД.

        :param guild_id: ID сервера.
        :return: None
        """

        self.cur.execute('DELETE FROM guilds WHERE id = ?;', (guild_id,))
        self.conn.commit()

    def update_reaction4role(self, guild_id, role_id, reaction):
        """
        Обновляет связку роль - реакция на сервере.

        :param guild_id: ID сервера.
        :param role_id: ID роли.
        :param reaction: Эмодзи.
        :return: None
        """

        self.update_guild_settings(guild_id)

        self.cur.execute('INSERT INTO reaction4role VALUES(?, ?, ?) '
                         'ON CONFLICT DO UPDATE SET role = ?, reaction = ?',
                         (guild_id, role_id, reaction, role_id, reaction))

        self.conn.commit()

    def get_reaction4role(self, guild_id):
        """
        Возвращает все связки роль - реакция на сервере.

        :param guild_id: ID сервера.
        :return: [[role, reaction]]
        """

        self.update_guild_settings(guild_id)

        self.cur.execute('SELECT role, reaction FROM reaction4role WHERE guild_id = ?', (guild_id,))
        return self.cur.fetchall()

    def delete_reaction4role(self, guild_id, role_id):
        """
        Удаляет связку роль - реакция с id роли на сервере.

        :param guild_id: ID сервера.
        :param role_id: ID роли.
        :return: None
        """

        self.cur.execute('SELECT reaction FROM reaction4role WHERE guild_id = ? AND role = ?', (guild_id, role_id))
        react = self.cur.fetchall()
        self.cur.execute('DELETE FROM reaction4role WHERE guild_id = ? AND role = ?', (guild_id, role_id))

        self.conn.commit()
        return react

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

    def get_users(self, guild_id, user_id=None, sort_by=None):
        """
        Возвращает информацию о пользователе на сервере.

        :param guild_id: ID сервера.
        :param user_id: ID пользователя.
        :param sort_by: По чему сортировать
        :return: [[guild_id, user_id, user_name, experience, messages, num_charact, num_voting, num_votes]]
        """

        if user_id is not None:
            self.cur.execute('SELECT * FROM users WHERE guild_id = ? AND user_id = ? ', (guild_id, user_id))
        else:
            self.cur.execute('SELECT * FROM users WHERE guild_id = ? '
                             f'ORDER BY {sort_by if sort_by is not None else "experience"} DESC ', (guild_id, ))

        return self.cur.fetchall()

    def delete_user(self, guild_id, user_id):
        """
        Удаляет пользователя с сервера.

        :param guild_id: ID сервера.
        :param user_id: ID пользователя.
        :return: None
        """

        self.cur.execute('DELETE FROM users WHERE guild_id = ? AND user_id = ?', (guild_id, user_id))

        self.conn.commit()

    def new_voting(self, mes_id, channel_id, user_info, question, time, min_choices, max_choices, answers):
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

    def get_voting(self, mes_id=None):
        """
        Возвращает все голосования.

        :param mes_id: ID сообщения с голосованием (ID голосования).
        :return: [[id, guild_id, channel_id, user_id, time, question, min_choice, max_choice, choices]]
        """

        if mes_id is not None:
            self.cur.execute('SELECT * FROM voting WHERE id = ?', (mes_id,))
        else:
            self.cur.execute('SELECT * FROM voting')

        return self.cur.fetchall()

    def delete_voting(self, mes_id):
        """
        Удалить голосование по ID.

        :param mes_id: ID сообщения с голосованием (ID голосования).
        :return: None.
        """

        self.cur.execute('DELETE FROM voting WHERE id = ?', (mes_id,))

        self.conn.commit()

    def new_vote(self, mes_id, user_info, choice):
        """
        Принимает новый голос.

        :param mes_id: ID сообщения с голосованием (ID голосования).
        :param user_info: (guild_id, user_id, user_name) проголосовавшего.
        :param choice: [str] массив с вариантами ответов.
        :return:
        """

        self.cur.execute('SELECT * FROM votes WHERE voting_id = ? AND user_id = ?', (mes_id, user_info[1]))

        if self.cur.fetchall():
            self.cur.execute('DELETE FROM votes WHERE voting_id = ? AND user_id = ?', (mes_id, user_info[1]))
        else:
            self.update_user(*user_info, voting=(0, 1))

        self.cur.executemany('INSERT INTO votes VALUES(?, ?, ?)',
                             ((mes_id, user_info[1], ch) for ch in choice))

        self.conn.commit()

    def get_votes(self, mes_id):
        """
        Получить все голоса определенного голосования.

        :param mes_id: ID сообщения с голосованием (ID голосования).
        :return: [[voting_id, user_id, choice]]
        """

        self.cur.execute('SELECT * FROM votes WHERE voting_id = ?', (mes_id,))

        return self.cur.fetchall()
