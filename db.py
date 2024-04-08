from datetime import datetime, timezone
import sqlite3
from config import SYMBOLS

connection = sqlite3.connect('readings.db')
cursor = connection.cursor()
params = ", ".join(f"{symbol} INTEGER UNSIGNED" for symbol in SYMBOLS)
with connection:
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS all_submissions ("
        "user_id INTEGER NOT NULL, "
        "submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, "
        f"{params}"
        ")"
    )
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS last_submissions ("
        "user_id INTEGER PRIMARY KEY, "
        "submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, "
        f"{params}"
        ")"
    )

    # Check if database schema matches config
    cursor.execute("SELECT * FROM all_submissions LIMIT 1")
    if not SYMBOLS == tuple(attr[0] for attr in cursor.description[2:]):
        raise Exception("Database schema doesn't fit the config. Delete the database or alter it accordingly.")


def submit(user_id: int, readings: list[int, ...]) -> int:
    attributes = ", ".join(SYMBOLS)
    values = ", ".join(map(str, readings))
    with connection:
        cursor.execute(
            "SELECT * FROM last_submissions WHERE user_id = ?",
            (user_id,)
        )
        data = cursor.fetchone()
        if data:
            old_readings = data[2:]
            if all(old is None or new >= old for old, new in zip(old_readings, readings)):
                data = ", ".join(f"{SYMBOLS[i]} = {readings[i]}" for i in range(len(SYMBOLS)))
                cursor.execute(
                    "UPDATE last_submissions "
                    "SET submitted_at = CURRENT_TIMESTAMP, "
                    f"{data} "
                    "WHERE user_id = ?",
                    (user_id,)
                )
            else:
                return -1
        else:
            cursor.execute(f"INSERT INTO last_submissions VALUES ({user_id}, CURRENT_TIMESTAMP, {values})")
        cursor.execute(f"INSERT INTO all_submissions (user_id, {attributes}) VALUES ({user_id}, {values})")
        return 0


def get(user_id: int) -> tuple[datetime, list[int | None, ...]] | None:
    with connection:
        cursor.execute(
            "SELECT * FROM last_submissions WHERE user_id = ?",
            (user_id,)
        )
        data = cursor.fetchone()
        if data:
            timestamp = (datetime.strptime(data[1], '%Y-%m-%d %H:%M:%S')
                         .replace(tzinfo=timezone.utc).astimezone(tz=None).replace(tzinfo=None))
            readings = list(data[2:])
            return timestamp, readings
        else:
            return None
