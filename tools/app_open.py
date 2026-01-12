from AppOpener import open as open_app, give_appnames, close as close_app

def software_opener(name: str, func: str = "open"):
    """
    Manages applications by opening, closing, or listing them.
    """
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