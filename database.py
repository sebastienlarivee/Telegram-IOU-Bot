import sqlite3
from datetime import date


def connect_db():
  conn = sqlite3.connect('iou.db')
  create_tables(conn)
  return conn


def create_tables(conn):
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id TEXT NOT NULL,
            debtor TEXT NOT NULL,
            creditor TEXT NOT NULL,
            amount REAL NOT NULL,
            reason TEXT,
            date TEXT NOT NULL
        );
    """)
  conn.commit()


def add_transaction(conn, group_id, debtor, creditor, amount, reason=None):
  cursor = conn.cursor()
  cursor.execute(
    """
        INSERT INTO transactions (group_id, debtor, creditor, amount, reason, date)
        VALUES (?, ?, ?, ?, ?, ?);
    """, (group_id, debtor, creditor, amount, reason, date.today()))
  conn.commit()


def get_transactions(conn, group_id):
  cursor = conn.cursor()
  cursor.execute(
    """
        SELECT debtor, creditor, amount
        FROM transactions
        WHERE group_id = ?;
    """, (group_id, ))
  return cursor.fetchall()


def get_history(conn, group_id):
  cursor = conn.cursor()
  cursor.execute(
    """
        SELECT debtor, creditor, amount, reason, date
        FROM transactions
        WHERE group_id = ?
        ORDER BY date DESC;
    """, (group_id, ))
  return cursor.fetchall()
