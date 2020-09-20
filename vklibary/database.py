import sqlite3
from pathlib import Path

conn = sqlite3.connect(str(Path(__file__).resolve().parent)+'/sfds.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()


def GetInfo(table, sorting="", what="*"):
    if sorting == "":
        sql = "SELECT {0} FROM {1}".format(what, table)
    else:
        sql = "SELECT {0} FROM {1} WHERE {2}".format(what, table, sorting)
    obj = c.execute(sql)
    return obj.fetchall()


def GetAds(datestart, dateend, sorting=""):
    sql = "SELECT * FROM static WHERE date BETWEEN '{0}' and '{1}' AND {2} ".format(datestart, dateend, sorting)
    obj = c.execute(sql)
    return obj.fetchall()


def Insert(table, value):
    sql = "INSERT INTO {0} VALUES({1})".format(table, value)
    c.execute(sql)
    conn.commit()


def InsertStatic(static):
    c.executemany("INSERT INTO static VALUES (?,?,?,?,?,?,?,?,?)", static)
    conn.commit()


def InsertTempory(static):
    c.executemany("INSERT INTO temporary_data VALUES (?,?,?,?,?,?,?,?)", static)
    conn.commit()


def Clear(table):
    sql = "DELETE FROM {0}".format(table)
    c.execute(sql)
    conn.commit()
