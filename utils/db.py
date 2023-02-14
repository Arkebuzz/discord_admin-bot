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
                       log_channel INTEGER,
                       default_role INTEGER,
                       message_rules INTEGER);
                       ''')

        self.cur.execute('''CREATE TABLE IF NOT EXISTS reaction4role(
                       guild_id,
                       role INTEGER,
                       reaction INTEGER,
                       PRIMARY KEY(role, reaction),
                       FOREIGN KEY(guild_id) REFERENCES guilds(id) ON DELETE CASCADE);
                       ''')

        self.conn.commit()

    def update_guild_settings(self, guild_id, log_id=None, role_id=None, message_id=None):
        """
        Обновляет лог-канал и сообщение с автораздачей на сервере.

        :param guild_id: ID сервера.
        :param log_id: ID лог-канала.
        :param role_id: ID роли по умолчанию.
        :param message_id: ID сообщения с автораздачей ролей.
        :return:
        """

        if log_id is not None:
            self.cur.execute('INSERT INTO guilds VALUES(?, ?, NULL, NULL) '
                             'ON CONFLICT (id) DO UPDATE SET log_channel = ?',
                             (guild_id, log_id, log_id))

        if role_id is not None:
            self.cur.execute('INSERT INTO guilds VALUES(?, NULL, ?, NULL) '
                             'ON CONFLICT (id) DO UPDATE SET default_role = ?',
                             (guild_id, role_id, role_id))

        if message_id is not None:
            self.cur.execute('INSERT INTO guilds VALUES(?, NULL, NULL, ?) '
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
