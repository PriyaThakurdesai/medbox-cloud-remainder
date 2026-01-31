# cloud_reminder.py
# This runs on cloud (Render / Railway / etc.)
# App बंद असला, laptop बंद असला तरी reminders जातील

import time
from datetime import datetime, timedelta
from twilio.rest import Client
from libs import firebase_helper as fb
import os

# =========================
# Twilio Credentials
# =========================
ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
FROM_WHATSAPP = os.getenv("TWILIO_WHATSAPP")

client = Client(ACCOUNT_SID, AUTH_TOKEN)

# =========================
# Helper: send WhatsApp
# =========================
def send_whatsapp(to_number, message):
    try:
        client.messages.create(
            body=message,
            from_=FROM_WHATSAPP,
            to=f"whatsapp:{to_number}"
        )
        print("WhatsApp sent to", to_number)
    except Exception as e:
        print("WhatsApp error:", e)

# =========================
# Check if reminder should fire
# =========================
def should_fire(schedule, now):
    start = datetime.strptime(schedule["start"], "%Y-%m-%d").date()

    # ongoing OR end date logic
    if not schedule.get("ongoing", False):
        if schedule.get("end"):
            end = datetime.strptime(schedule["end"], "%Y-%m-%d").date()
            if now.date() > end:
                return False

    if now.date() < start:
        return False

    freq = schedule.get("frequency", "Daily")

    if freq == "Daily":
        return True

    if freq == "Weekly":
        return (now.date() - start).days % 7 == 0

    if freq == "Monthly":
        return now.day == start.day

    if freq == "Alternate Days":
        return (now.date() - start).days % 2 == 0

    return False

# =========================
# Main loop (runs forever)
# =========================
def run_cloud_reminder():
    print("☁️ Cloud Reminder Service Started")

    while True:
        try:
            now = datetime.now()

            users = fb.get_all_users()   # 🔥 must exist in firebase_helper

            for phone, user_data in users.items():
                schedules = user_data.get("schedules", {})

                for sid, sch in schedules.items():
                    if not should_fire(sch, now):
                        continue

                    for t in sch.get("times", []):
                        t_obj = datetime.strptime(t, "%I:%M %p").time()

                        if now.hour == t_obj.hour and now.minute == t_obj.minute:
                            msg = f"💊 Reminder: Take {sch['name']} ({sch['dose']})"
                            send_whatsapp("+91" + phone, msg)

            time.sleep(60)  # check every minute

        except Exception as e:
            print("Main loop error:", e)
            time.sleep(60)


if __name__ == "__main__":
    run_cloud_reminder()
