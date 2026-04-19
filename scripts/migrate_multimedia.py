"""
migrate_multimedia.py — Add multimedia columns to KillerBee DB.
Idempotent: checks PRAGMA table_info before adding any column.
Run from the KillerBee root directory (or any directory — uses absolute path).
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       'instance', 'killerbee.db')


def existing_columns(cursor, table):
    cursor.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cursor.fetchall()}


def add_column_if_missing(cursor, table, column, col_type):
    cols = existing_columns(cursor, table)
    if column in cols:
        print(f"  [skip] {table}.{column} already exists")
    else:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
        print(f"  [added] {table}.{column} {col_type}")


def main():
    print(f"Connecting to {DB_PATH}")
    if not os.path.exists(DB_PATH):
        print("ERROR: database not found — run app.py at least once first to create it.")
        raise SystemExit(1)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    print("\nMigrating swarm_jobs ...")
    add_column_if_missing(cur, 'swarm_jobs', 'media_type', 'TEXT')
    add_column_if_missing(cur, 'swarm_jobs', 'media_url',  'TEXT')

    print("\nMigrating job_components ...")
    add_column_if_missing(cur, 'job_components', 'piece_path',       'TEXT')
    add_column_if_missing(cur, 'job_components', 'audio_piece_path', 'TEXT')

    conn.commit()
    conn.close()
    print("\nDone — migration complete.")


if __name__ == '__main__':
    main()
