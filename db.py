import sqlite3

conn = sqlite3.connect('alarms.db')
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS alarms (
                id INTEGER PRIMARY KEY,
                alarm_time TEXT NOT NULL,
                alarm_days TEXT NOT NULL,
                snooze_count INTEGER DEFAULT 0,
                next_alarm_time TEXT NOT NULL,
                is_active INTEGER DEFAULT 1
            )''')

conn.commit()
conn.close()