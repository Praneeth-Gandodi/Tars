from datetime import datetime

def get_datetime():
    """
    Get current date and time - NO PARAMETERS NEEDED
    The function will always returns the current time.
    """
    now = datetime.now()
    return {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "timezone": now.strftime("%Z") or "Local",
        "day": now.strftime("%A")
    }
