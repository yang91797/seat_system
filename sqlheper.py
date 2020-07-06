import pymysql
from mysql_pool import POOL


class SqlHelper(object):
    def __init__(self):
        # 读取配置文件
        self.connect()

    def connect(self):
        self.conn = POOL.connection()
        self.cursor = self.conn.cursor(cursor=pymysql.cursors.DictCursor)

    def get_list(self, sql, args):
        """
        查询所有内容
        :param sql:
        :param args:
        :return:
        """
        self.cursor.execute(sql, args)
        result = self.cursor.fetchall()

        return result

    def get_one(self, sql, args):
        """
        查询一个内容
        :param sql:
        :param args:
        :return:
        """
        self.cursor.execute(sql, args)
        result = self.cursor.fetchone()

        return result

    def modify(self, sql, args):
        """
        增，删，改
        :param sql:
        :param args:
        :return:
        """
        self.cursor.execute(sql, args)
        self.conn.commit()

    def multiple_modify(self, sql, args):
        """
        批量增加
        :param sql:
        :param args:
        :return:
        """
        self.cursor.executemany(sql, args)
        self.conn.commit()

    def create(self, sql, args):
        """
        获取最后一个id
        :param sql:
        :param args:
        :return:
        """
        self.cursor.execute(sql, args)
        self.conn.commit()
        return self.cursor.lastrowid

    def close(self):
        self.cursor.close()
        self.conn.close()

