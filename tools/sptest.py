import speedtest
from rich.console import Console 


console = Console()
def sptest():
    """
    Retuns internet speed 
    Returns:
        _type_: _description_
    """
    with console.status("[green dim]Checking internet speed[green dim]", spinner = "dots"):
        st = speedtest.Speedtest()
        st.get_best_server()
        dspeed = st.download()
        uspeed = st.upload()
        ping = st.results.ping
    
    download_mbps = dspeed / 1000000
    upload_mbps = uspeed / 1000000
    
    return f"Current download speed is {dspeed}, upload speed is {uspeed} and the ping is {ping} (download, upload in mbps {download_mbps}, {upload_mbps})"
    
