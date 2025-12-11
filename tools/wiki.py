import wikipedia 
from rich.console import Console 
console = Console()

def wiki_search(word):
    """
    Search Wikipedia for pages matching the given query.
    
    Args:
        word (str): The search term or query to look up on Wikipedia.
    
    Returns:
        list: A list of Wikipedia page titles that match the search query.
              Returns an empty list if no matches are found.
    
    Example:
        >>> wiki_search("Python programming")
        ['Python (programming language)', 'Programming language', ...]
    """
    return wikipedia.search(
        word,
        suggestion=False)
    
def wiki_content(word):
    """
    Retrieve the full content and title of a Wikipedia page.
    
    Args:
        word (str): The exact title of the Wikipedia page to retrieve.
    
    Returns:
        dict: A dictionary containing:
            - 'title' (str): The page title
            - 'content' (str): The full text content of the page
    
    Raises:
        wikipedia.exceptions.PageError: If the page does not exist.
        wikipedia.exceptions.DisambiguationError: If the title is ambiguous.
    
    Example:
        >>> content = wiki_content("Python (programming language)")
        >>> print(content['title'])
        'Python (programming language)'
    """
    text = wikipedia.page(word)
    content = {
        'title': text.title,
        'content': text.content
    }
    return content

def wiki_summary(word):
    """
    Get a brief summary of a Wikipedia page.
    
    Args:
        word (str): The title or topic to get a summary for.
    
    Returns:
        str: A plain text summary of the Wikipedia page, typically
             consisting of the first few sentences or paragraphs.
    
    Raises:
        wikipedia.exceptions.PageError: If the page does not exist.
        wikipedia.exceptions.DisambiguationError: If the title is ambiguous.
    
    Example:
        >>> summary = wiki_summary("Artificial Intelligence")
        >>> print(summary[:50])
        'Artificial intelligence (AI) is intelligence...'
    """
    return wikipedia.summary(word)

