import sys

# AppOpener is a Windows-only package: importing it anywhere else raises
# (and prints import-time noise), so off-Windows we don't import it at all —
# the tool is simply not registered there (see supporter.py / main.py).
if sys.platform == "win32":
    try:
        from AppOpener import open as open_app, give_appnames, close as close_app
    except BaseException:
        open_app = None
        give_appnames = None
        close_app = None
else:
    open_app = None
    give_appnames = None
    close_app = None


def software_opener(name: str, func: str = "open"):
    """
    Manages applications by opening, closing, or listing them.
    """
    if open_app is None:
        return (
            "App opening is only supported on Windows (the AppOpener package "
            "does not run on Linux / WSL2 / Docker)."
        )

    try:
        if name.lower() == "list":
            apps = give_appnames()
            return f"Available apps: {str(apps)}" 

        if func.lower() == "open":
            open_app(name, match_closest=True)
            return f"Successfully sent command to OPEN '{name}'."
            
        elif func.lower() == "close":
            close_app(name, match_closest=True)
            return f"Successfully sent command to CLOSE '{name}'."
            
        return "Invalid function requested."
    except Exception as e:
        return f"Error processing request: {str(e)}"