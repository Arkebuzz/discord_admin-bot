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

        :return:
        """

        self.cur.execute('''CREATE TABLE IF NOT EXISTS guilds(
                       id INTEGER PRIMARY KEY,
                       analyze INTEGER,
                       log_channel INTEGER,
                       default_role INTEGER,
                       message_rules INTEGER);
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
                       PRIMARY KEY(guild_id, user_id),
                       FOREIGN KEY(guild_id) REFERENCES guilds(id) ON DELETE CASCADE);
                       ''')

        self.conn.commit()

    def update_guild_settings(self, guild_id, analyze=None, log_id=None, role_id=None, message_id=None):
        """
        Обновляет лог-канал и сообщение с автораздачей на сервере.

        :param guild_id: ID сервера.
        :param analyze: Сервер проанализирован?
        :param log_id: ID лог-канала.
        :param role_id: ID роли по умолчанию.
        :param message_id: ID сообщения с автораздачей ролей.
        :return:
        """

        if log_id is None and role_id is None and message_id is None and analyze is None:
            self.cur.execute('INSERT INTO guilds VALUES(?, 0, NULL, NULL, NULL) '
                             'ON CONFLICT (id) DO NOTHING',
                             (guild_id,))

        if analyze is not None:
            self.cur.execute('INSERT INTO guilds VALUES(?, ?, NULL, NULL, NULL) '
                             'ON CONFLICT (id) DO UPDATE SET analyze = ?',
                             (guild_id, analyze, analyze))

        if log_id is not None:
            self.cur.execute('INSERT INTO guilds VALUES(?, 0, ?, NULL, NULL) '
                             'ON CONFLICT (id) DO UPDATE SET log_channel = ?',
                             (guild_id, log_id, log_id))

        if role_id is not None:
            self.cur.execute('INSERT INTO guilds VALUES(?, 0, NULL, ?, NULL) '
                             'ON CONFLICT (id) DO UPDATE SET default_role = ?',
                             (guild_id, role_id, role_id))

        if message_id is not None:
            self.cur.execute('INSERT INTO guilds VALUES(?, 0, NULL, NULL, ?) '
                             'ON CONFLICT (id) DO UPDATE SET message_rules = ?',
                             (guild_id, message_id, message_id))

        self.conn.commit()

    def get_guilds(self, guild_id=None):
        """
        Возвращает сервера бота c введенным ID, если ID не передан, то возвращает все сервера.

        :param guild_id: ID сервера.
        :return:
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
        :return:
        """

        self.cur.execute('DELETE FROM guilds WHERE id = ?;', (guild_id,))
        self.conn.commit()

    def update_reaction4role(self, guild_id, role_id, reaction):
        """
        Обновляет связку роль - реакция на сервере.

        :param guild_id:
        :param role_id:
        :param reaction:
        :return:
        """

        self.update_guild_settings(guild_id)

        self.cur.execute('INSERT INTO reaction4role VALUES(?, ?, ?) '
                         'ON CONFLICT DO UPDATE SET role = ?, reaction = ?',
                         (guild_id, role_id, reaction, role_id, reaction))

        self.conn.commit()

    def get_reaction4role(self, guild_id):
        """
        Возвращает все связки роль - реакция на сервере.

        :param guild_id:
        :return:
        """

        self.cur.execute('SELECT role, reaction FROM reaction4role WHERE guild_id = ?', (guild_id,))
        return self.cur.fetchall()

    def delete_reaction4role(self, guild_id, role_id):
        """
        Удаляет связку роль - реакция с id роли на сервере.

        :param guild_id:
        :param role_id:
        :return:
        """

        self.cur.execute('DELETE FROM reaction4role WHERE guild_id = ? AND role = ?', (guild_id, role_id))

        self.conn.commit()

    def update_user(self, guild_id, user_id, user_name, len_message=0, num_attach=0):
        """
        Обновляет статистику пользователя на сервере.

        :param guild_id:
        :param user_id:
        :param user_name:
        :param len_message:
        :param num_attach:
        :return:
        """

        e = 2.718281828459045
        l_m = len_message / 100
        exp = int(30 * (e ** l_m - e ** -l_m) / (e ** l_m + e ** -l_m))

        exp += num_attach * 7

        self.cur.execute('INSERT INTO users VALUES(?, ?, ?, ?, 1, ?) ON CONFLICT DO UPDATE '
                         'SET experience = experience + ?, messages = messages + 1, num_charact = num_charact + ?',
                         (guild_id, user_id, user_name, exp, len_message, exp, len_message))

        self.conn.commit()

    def get_users(self, guild_id, user_id=None):
        """
        Возвращает информацию о пользователе на сервере.

        :param guild_id:
        :param user_id:
        :return:
        """

        if user_id is not None:
            self.cur.execute('SELECT * FROM users WHERE guild_id = ? AND user_id = ? ', (guild_id, user_id))
        else:
            self.cur.execute('SELECT * FROM users WHERE guild_id = ? '
                             'ORDER BY experience DESC ', (guild_id,))

        return self.cur.fetchall()

    def delete_user(self, guild_id, user_id):
        """
        Удаляет пользователя с сервера.

        :param guild_id:
        :param user_id:
        :return:
        """

        self.cur.execute('DELETE FROM users WHERE guild_id = ? AND user_id = ?', (guild_id, user_id))

        self.conn.commit()
