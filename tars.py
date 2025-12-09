from main import get_ai, console, ccount, summarize
import logging
logging.getLogger().setLevel(logging.CRITICAL)
logging.getLogger("RealtimeSTT").setLevel(logging.CRITICAL)
logging.getLogger("faster_whisper").setLevel(logging.CRITICAL)
logging.getLogger("httpx").setLevel(logging.CRITICAL)
logging.getLogger("httpcore").setLevel(logging.CRITICAL)

def tars():
    global ccount
    while True:
        status = get_ai()
        if status in ["q", "quit", "exit", "stop"]:
            return 
        console.print(status)
        ccount += 1
        print(ccount)
        if ccount >= 10:
            console.print(summarize()) 
            ccount = 0
        
if __name__ == "__main__":
    try:
        tars()
    except KeyboardInterrupt:
        console.print("Quitting....")