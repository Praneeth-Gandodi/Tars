from datetime import datetime

def get_datetime(query):
    now = datetime.now()
    return {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "timezone": now.strftime("%Z") or "Local",
        "day": now.strftime("%A")
    }
