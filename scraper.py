import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging

def scrape_prices(url):
    """
    Scrape price information from a given URL
    Returns a list of dictionaries containing price and context information
    """
    try:
        # Set headers to mimic a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Make the request
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse the HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Price patterns for different currencies
        price_patterns = [
            # Korean Won
            r'₩\s*[\d,]+(?:\.\d{2})?',
            r'[₩]\s*[\d,]+',
            r'[\d,]+\s*원',
            # US Dollar
            r'\$\s*[\d,]+(?:\.\d{2})?',
            r'USD\s*[\d,]+(?:\.\d{2})?',
            # Euro
            r'€\s*[\d,]+(?:\.\d{2})?',
            r'EUR\s*[\d,]+(?:\.\d{2})?',
            # British Pound
            r'£\s*[\d,]+(?:\.\d{2})?',
            r'GBP\s*[\d,]+(?:\.\d{2})?',
            # Japanese Yen
            r'¥\s*[\d,]+',
            r'JPY\s*[\d,]+',
            # General patterns
            r'[\d,]+(?:\.\d{2})?\s*(?:USD|EUR|GBP|KRW|JPY|won|dollars?|euros?|pounds?)',
            # Numbers with currency symbols or words nearby
            r'(?:price|cost|price:|cost:)\s*[₩$€£¥]?\s*[\d,]+(?:\.\d{2})?',
            r'[₩$€£¥]\s*[\d,]+(?:\.\d{2})?(?:\s*(?:USD|EUR|GBP|KRW|JPY|won|dollars?|euros?|pounds?))?'
        ]
        
        prices_found = []
        seen_prices = set()
        
        # Search for prices in the text
        text_content = soup.get_text()
        
        for pattern in price_patterns:
            matches = re.finditer(pattern, text_content, re.IGNORECASE)
            for match in matches:
                price_text = match.group().strip()
                
                # Skip if we've already found this exact price
                if price_text in seen_prices:
                    continue
                
                seen_prices.add(price_text)
                
                # Get context around the price
                start_pos = max(0, match.start() - 50)
                end_pos = min(len(text_content), match.end() + 50)
                context = text_content[start_pos:end_pos].strip()
                
                # Clean up context
                context = re.sub(r'\s+', ' ', context)
                context = context.replace('\n', ' ').replace('\t', ' ')
                
                prices_found.append({
                    'price': price_text,
                    'context': context,
                    'position': match.start()
                })
        
        # Also search in specific HTML elements that commonly contain prices
        price_selectors = [
            '[class*="price"]',
            '[class*="cost"]',
            '[class*="amount"]',
            '[id*="price"]',
            '[id*="cost"]',
            '.price',
            '.cost',
            '.amount',
            'span[class*="price"]',
            'div[class*="price"]',
            'p[class*="price"]'
        ]
        
        for selector in price_selectors:
            elements = soup.select(selector)
            for element in elements:
                element_text = element.get_text().strip()
                
                for pattern in price_patterns:
                    matches = re.finditer(pattern, element_text, re.IGNORECASE)
                    for match in matches:
                        price_text = match.group().strip()
                        
                        if price_text in seen_prices:
                            continue
                        
                        seen_prices.add(price_text)
                        
                        # Use the entire element text as context
                        context = element_text
                        context = re.sub(r'\s+', ' ', context)
                        
                        prices_found.append({
                            'price': price_text,
                            'context': context,
                            'position': 0  # HTML element based, no specific position
                        })
        
        # Sort by position to maintain order from the page
        prices_found.sort(key=lambda x: x['position'])
        
        # Remove duplicates while preserving order
        unique_prices = []
        seen_contexts = set()
        
        for price_info in prices_found:
            # Create a key based on price and simplified context
            key = (price_info['price'], price_info['context'][:100])
            if key not in seen_contexts:
                seen_contexts.add(key)
                unique_prices.append(price_info)
        
        logging.info(f"Found {len(unique_prices)} unique prices")
        return unique_prices
        
    except requests.RequestException as e:
        logging.error(f"Request error: {e}")
        raise Exception(f"Failed to fetch the webpage: {str(e)}")
    except Exception as e:
        logging.error(f"Scraping error: {e}")
        raise Exception(f"Error parsing the webpage: {str(e)}")
