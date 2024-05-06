from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)

def create_connection():
    # connect to the db
    return sqlite3.connect('alarms.db')

class AlarmClock:
    def __init__(self):
        pass

    def display_current_time(self):
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def display_alarms(self):
        conn = create_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM alarms")
        alarms = c.fetchall()
        conn.close()
        alarms_info = []
        for alarm in alarms:
            alarms_info.append({
                "id": alarm[0],
                "time": alarm[1],
                "days": alarm[2],
                "snooze_count": alarm[3],
                "next_alarm_time": alarm[4],
                "is_active": bool(alarm[5])
            })
        return alarms_info

    def get_alarm_by_id(self, id):
        conn = create_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM alarms WHERE id = ?", (id,))
        alarm = c.fetchone()
        conn.close()
        if alarm:
            return {
                "id": alarm[0],
                "alarm_time": alarm[1],
                "alarm_days": alarm[2],
                "snooze_count": alarm[3],
                "next_alarm_time": alarm[4],
                "is_active": bool(alarm[5])
            }
        return None

    def create_alarm(self, alarm_time, alarm_days, next_alarm_time):
        conn = create_connection()
        c = conn.cursor()
        c.execute("INSERT INTO alarms (alarm_time, alarm_days, next_alarm_time) VALUES (?, ?, ?)", (alarm_time, alarm_days, next_alarm_time))
        conn.commit()
        conn.close()

    def delete_alarm(self, alarm_id):
        conn = create_connection()
        c = conn.cursor()
        c.execute("DELETE FROM alarms WHERE id=?", (alarm_id,))
        conn.commit()
        conn.close()
    
    def calculate_next_alarm_time(self, alarm_time, alarm_days):
        # time when the alarm should alert
        current_time = datetime.now()
        alarm_hour, alarm_minute = map(int, alarm_time.split(':'))

        # Check for current day alarm
        if current_time.strftime('%A') in alarm_days:
            if current_time.hour > alarm_hour or (current_time.hour == alarm_hour and current_time.minute >= alarm_minute):
                current_time += timedelta(days=1)

        if current_time.strftime('%A') in alarm_days:
            next_alarm_time = current_time.replace(hour=alarm_hour, minute=alarm_minute, second=0, microsecond=0)
        else:
            while True:
                if current_time.strftime('%A') in alarm_days:
                    next_alarm_time = current_time.replace(hour=alarm_hour, minute=alarm_minute, second=0, microsecond=0)
                    break

                current_time += timedelta(days=1)

        return next_alarm_time.strftime('%Y-%m-%d %H:%M:%S')
    
    def snooze_alarm(self, id):
        alarm = self.get_alarm_by_id(id)
        if alarm:
            # snooze count check
            if alarm['snooze_count'] < 3:
                snooze_count = alarm['snooze_count'] + 1
                next_alarm_time = datetime.strptime(alarm['next_alarm_time'], '%Y-%m-%d %H:%M:%S')
                next_alarm_time += timedelta(minutes=5)
                next_alarm_time_str = next_alarm_time.strftime('%Y-%m-%d %H:%M:%S')
                # Update the DB
                conn = create_connection()
                c = conn.cursor()
                c.execute("UPDATE alarms SET snooze_count = ?, next_alarm_time = ? WHERE id = ?", (snooze_count, next_alarm_time_str, id))
                conn.commit()
                conn.close()
                return True, next_alarm_time_str
            else:
                # Maximum snooze limit reached, recalculate the next alarm time
                alarm_time = alarm['alarm_time']
                alarm_days = alarm['alarm_days'].split(',')
                next_alarm_time = self.calculate_next_alarm_time(alarm_time, alarm_days)
                # Update the DB
                conn = create_connection()
                c = conn.cursor()
                c.execute("UPDATE alarms SET snooze_count = ?, next_alarm_time = ? WHERE id = ?", (0, next_alarm_time, id))  # Reset snooze count to 0
                conn.commit()
                conn.close()
                return False, next_alarm_time
        return False, None


clock = AlarmClock()

@app.route('/')
def index():
    current_time = clock.display_current_time()
    alarms = clock.display_alarms()
    return render_template('index.html', current_time=current_time, alarms=alarms)

@app.route('/alarms')
def get_alarms():
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    alarms = clock.display_alarms()
    ringing_alarms = [alarm for alarm in alarms if alarm['next_alarm_time'] <= current_time]
    return jsonify(ringing_alarms)

@app.route('/create_alarm', methods=['POST'])
def create_alarm():
    data = request.json
    alarm_time = data.get('alarm_time')
    alarm_days = data.get('alarm_days', [])
    next_alarm_time = clock.calculate_next_alarm_time(alarm_time, alarm_days)
    clock.create_alarm(alarm_time, ','.join(alarm_days), next_alarm_time)
    return jsonify({'message': 'Alarm created successfully'})


@app.route('/delete_alarm/<int:alarm_id>', methods=['POST'])
def delete_alarm(alarm_id):
    clock.delete_alarm(alarm_id)
    return redirect(url_for('index'))

@app.route('/snooze_alarm/<int:id>', methods=['POST'])
def snooze_alarm(id):
    clock.snooze_alarm(id)
    return jsonify({'message': 'Alarm snoozed successfully'})

if __name__ == "__main__":
    app.run(debug=True)
