from ddgs import DDGS
from ddgs.exceptions import RatelimitException, TimeoutException




def web_search(
    topic, 
    region="wt-wt",
    safesearch="moderate",
    timelimit=None,
    backend="auto",
    max_results=None
):
    """DuckDuckGo text search generator. Query params: https://duckduckgo.com/params.

    Args:
        keywords: keywords for query.
        region: us-en, uk-en, ru-ru, etc. Defaults to None.
        safesearch: on, moderate, off. Defaults to "moderate".
        timelimit: d, w, m, y. Defaults to None.
        backend: auto, html, lite. Defaults to auto.
            auto - try all backends in random order,
            html - collect data from https://html.duckduckgo.com,
            lite - collect data from https://lite.duckduckgo.com,
            bing - collect data from https://www.bing.com.
        max_results: max number of results. If None, returns results only from the first response. Defaults to None.

    Returns:
        List of dictionaries with search results.
    """
    try:
        return DDGS().text(
            query=topic,
            region=region,
            safesearch=safesearch,
            timelimit=timelimit,
            backend=backend,
            max_results=max_results
        )
    except RatelimitException:
        return ["Rate limit hit"]
    except TimeoutException:
        return ["Timeout"]
    except Exception as e:
        return ["Unexpected Exception"]
    
def image_search(
    topic, 
    region="wt-wt",
    safesearch="moderate",
    timelimit=None,
    size=None,
    color=None,
    type_image=None,
    layout=None,
    license_image = None,
    max_results=30
):
    """DuckDuckGo images search. Query params: https://duckduckgo.com/params.

    Args:
        keywords: keywords for query.
        region: us-en, uk-en, ru-ru, etc. Defaults to "us-en".
        safesearch: on, moderate, off. Defaults to "moderate".
        timelimit: Day, Week, Month, Year. Defaults to None.
        size: Small, Medium, Large, Wallpaper. Defaults to None.
        color: color, Monochrome, Red, Orange, Yellow, Green, Blue,
            Purple, Pink, Brown, Black, Gray, Teal, White. Defaults to None.
        type_image: photo, clipart, gif, transparent, line.
            Defaults to None.
        layout: Square, Tall, Wide. Defaults to None.
        license_image: any (All Creative Commons), Public (PublicDomain),
            Share (Free to Share and Use), ShareCommercially (Free to Share and Use Commercially),
            Modify (Free to Modify, Share, and Use), ModifyCommercially (Free to Modify, Share, and
            Use Commercially). Defaults to None.
        max_results: max number of results. If None, returns results only from the first response. Defaults to None.

    Returns:
        List of dictionaries with images search results.
    """
    try:
        return DDGS().images(
            query=topic,
            region=region,
            safesearch=safesearch,
            timelimit=timelimit,
            size=size,
            color = color,
            type_image=type_image,
            layout=layout,
            license_image=license_image,
            max_results=max_results
        )
    except RatelimitException:
        return ["Rate limit hit"]
    except TimeoutException:
        return ["Timeout"]
    except Exception as e:
        return [f"Unexpected Exception {e}"]

def video_search(
    topic, 
    region="wt-wt",
    safesearch="moderate",
    timelimit=None,
    resolution=None,
    duration=None,
    license_videos=None,
    max_results=None    
):
    """DuckDuckGo videos search. Query params: https://duckduckgo.com/params.

    Args:
        keywords: keywords for query.
        region: us-en, uk-en, ru-ru, etc. Defaults to "us-en".
        safesearch: on, moderate, off. Defaults to "moderate".
        timelimit: d, w, m. Defaults to None.
        resolution: high, standart. Defaults to None.
        duration: short, medium, long. Defaults to None.
        license_videos: creativeCommon, youtube. Defaults to None.
        max_results: max number of results. If None, returns results only from the first response. Defaults to None.

    Returns:
        List of dictionaries with videos search results.
    """
    try:
        return DDGS().videos(
            query=topic, 
            region=region,
            safesearch=safesearch,
            timelimit=timelimit,
            resolution=resolution,
            duration=duration,
            license_videos=license_videos,
            max_results=max_results  
        )
    except RatelimitException:
        return ["Rate limit hit"]
    except TimeoutException:
        return ["Timeout"]
    except Exception as e:
        return ["Unexpected Exception"]
    
    
def news_search(
    query,
    region = "us-en",
    safesearch = "off",
    timelimit = None,
    max_results = None,
):
    """DuckDuckGo news search. Query params: https://duckduckgo.com/params.

    Args:
        keywords: keywords for query.
        region: us-en, uk-en, ru-ru, etc. Defaults to "us-en".
        safesearch: on, moderate, off. Defaults to "moderate".
        timelimit: d, w, m. Defaults to None.
        max_results: max number of results. If None, returns results only from the first response. Defaults to None.

    Returns:
        List of dictionaries with news search results.
    """    
    try:
        return DDGS().news(
        query=query,
        region = region,
        safesearch = safesearch,
        timelimit = timelimit,
        max_results = max_results,    
        ) 
    except RatelimitException:
        return ["Rate limit hit"]
    except TimeoutException:
        return ["Timeout"]
    except Exception as e:
        return ["Unexpected Exception"]