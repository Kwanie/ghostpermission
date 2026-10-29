import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from typing import Optional

def find_privacy_policy_url(app_name: str, developer: str = "") -> Optional[str]:
    """Searches DuckDuckGo for an external Privacy Policy URL."""
    query = f"{app_name} {developer} privacy policy".strip()
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            for res in results:
                url = res.get("href", "")
                if "privacy" in url.lower() or "policy" in url.lower():
                    return url
    except Exception:
        pass
    return None

def scrape_policy_text(url: str, max_chars: int = 8000) -> str:
    """Scrapes and cleans plain text from a privacy policy web page."""
    if not url:
        return ""
        
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        response = requests.get(url, headers=headers, timeout=8)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove non-content elements
        for element in soup(["script", "style", "nav", "footer", "header", "form"]):
            element.decompose()
            
        clean_text = soup.get_text(separator=" ", strip=True)
        return clean_text[:max_chars]
    except Exception as e:
        return f"Unable to fetch text from privacy policy URL: {str(e)}"