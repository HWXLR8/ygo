import sqlite3

from include.pyinstaller_helper import rpath

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(rpath('sql/cards.db'))
        self.cursor = self.conn.cursor()

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()
