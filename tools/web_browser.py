import webbrowser
import tomllib

def open_browser(link:str) -> bool:
    with open("settings.toml", "rb") as settings:
        data = tomllib.load(settings)
    
    if data["tool_settings"]["web_browser_exe_path"]:
        path = data["tool_settings"]["web_browser_exe_path"] + " %s"
        browser = webbrowser.get(path)
        link_opened = browser.open(link)
        return link_opened
    else:
        link_opened = webbrowser.open(link)
        return link_opened
    
    
