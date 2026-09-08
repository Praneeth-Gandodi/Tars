"""System information tool (uses psutil — already in requirements.txt)."""
import platform
import time


def system_info():
    """Return OS / CPU / memory / disk / battery details for the machine."""
    try:
        import psutil
    except ImportError:
        return {"error": "psutil is not installed. Add it with: pip install psutil"}

    try:
        vm = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        info = {
            "os": platform.system(),
            "os_release": platform.release(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "cpu_count": psutil.cpu_count(logical=True),
            "cpu_percent": psutil.cpu_percent(interval=0.5),
            "memory": {
                "total_gb": round(vm.total / (1024 ** 3), 2),
                "used_gb": round(vm.used / (1024 ** 3), 2),
                "percent": vm.percent,
            },
            "disk": {
                "total_gb": round(disk.total / (1024 ** 3), 2),
                "used_gb": round(disk.used / (1024 ** 3), 2),
                "percent": disk.percent,
            },
            "uptime_hours": round((time.time() - psutil.boot_time()) / 3600, 2),
        }
        battery = psutil.sensors_battery()
        if battery:
            info["battery"] = {"percent": battery.percent, "plugged_in": battery.power_plugged}
        return info
    except Exception as e:
        return {"error": f"Could not read system info: {e}"}