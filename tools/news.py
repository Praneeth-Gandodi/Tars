import requests
import json
from datetime import datetime
from rich.console import Console 
console = Console()

def get_news(category, country, save_file=False):
    """
    Fetch top news headlines by category and country.
    
    Args:
        category (str): News category (e.g., 'technology', 'business', 'sports')
        country (str): Two-letter country code (e.g., 'us', 'in', 'gb')
        save_file (bool): Whether to save the response to a JSON file
    
    Returns:
        dict: Top 5 articles with full details + remaining headlines only
    """
    
    url = f"https://saurav.tech/NewsAPI/top-headlines/category/{category}/{country}.json"
    response = requests.get(url=url)
    news_data = response.json()
    
    articles = news_data.get('articles', [])

    top_5_full = [
        {
            "title": article.get('title'),
            "description": article.get('description', 'No description'),
            "source": article.get('source', {}).get('name'),
        }
        for article in articles[:5]
    ]
    

    remaining_headlines = [
        {
            "title": article.get('title'),
            "source": article.get('source', {}).get('name')
        }
        for article in articles[5:]
    ]

    compact_data = {
        "category": category,
        "country": country.upper(),
        "top_stories": top_5_full,
        "more_headlines": remaining_headlines,
        "total_articles": len(articles)
    }
    
    if save_file == True:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{category}_{country}_{timestamp}.json"
        
        with open(filename, "w") as file:
            json.dump(news_data, file, indent=4) 
        
        return {
            "message": f"Full data saved as {filename}",
            "preview": compact_data
        }
    
    return compact_data


