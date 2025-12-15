"""
Itinerary Scraping Engine
The "Collector Robot" - visits tour operator websites and extracts itinerary data.
"""

import time
import re
import logging
from datetime import datetime
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from django.utils import timezone

logger = logging.getLogger(__name__)


class RateLimiter:
    """Ensures we don't overwhelm target websites."""
    
    def __init__(self):
        self._last_request_times = {}
    
    def wait_if_needed(self, domain: str, min_seconds: int = 5):
        """Wait if we've recently made a request to this domain."""
        now = time.time()
        last_time = self._last_request_times.get(domain, 0)
        elapsed = now - last_time
        
        if elapsed < min_seconds:
            wait_time = min_seconds - elapsed
            logger.info(f"Rate limiting: waiting {wait_time:.1f}s for {domain}")
            time.sleep(wait_time)
        
        self._last_request_times[domain] = time.time()


class ItineraryScraper:
    """Scrapes itinerary content from tour operator websites."""
    
    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
    
    def scrape_url(self, url: str, rate_limit_seconds: int = 5) -> dict:
        """
        Fetch and parse a single URL.
        
        Returns dict with:
        - success: bool
        - raw_html: str
        - raw_text: str
        - page_title: str
        - meta_description: str
        - meta_keywords: str
        - error: str (if failed)
        """
        result = {
            'success': False,
            'raw_html': '',
            'raw_text': '',
            'page_title': '',
            'meta_description': '',
            'meta_keywords': '',
            'error': '',
        }
        
        try:
            # Apply rate limiting
            domain = urlparse(url).netloc
            self.rate_limiter.wait_if_needed(domain, rate_limit_seconds)
            
            # Fetch the page
            logger.info(f"Scraping: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            result['raw_html'] = response.text
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title_tag = soup.find('title')
            result['page_title'] = title_tag.get_text(strip=True) if title_tag else ''
            
            # Extract meta tags
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            result['meta_description'] = meta_desc.get('content', '') if meta_desc else ''
            
            meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
            result['meta_keywords'] = meta_keywords.get('content', '') if meta_keywords else ''
            
            # Extract main content text
            result['raw_text'] = self._extract_itinerary_text(soup)
            
            result['success'] = True
            logger.info(f"Successfully scraped: {url}")
            
        except requests.exceptions.RequestException as e:
            result['error'] = f"Request failed: {str(e)}"
            logger.error(f"Failed to scrape {url}: {e}")
        except Exception as e:
            result['error'] = f"Parsing failed: {str(e)}"
            logger.error(f"Failed to parse {url}: {e}")
        
        return result
    
    def _extract_itinerary_text(self, soup: BeautifulSoup) -> str:
        """Extract relevant itinerary text, ignoring ads/navigation."""
        
        # First, extract price information before removing elements
        price_info = self._extract_price_info(soup)
        
        # Remove unwanted elements
        for element in soup.find_all(['script', 'style', 'nav', 'iframe', 'noscript']):
            element.decompose()
        
        # Get full text first
        full_text = soup.get_text(separator=' ', strip=True)
        
        # Try to find where actual content starts (common patterns for tour sites)
        content_markers = [
            'OVERVIEW', 'Overview', 'Itinerary', 'Day 1', 'Day One',
            'Trip Overview', 'Tour Overview', 'About This Trip',
            'Detailed Itinerary', 'Trip Details'
        ]
        
        start_idx = 0
        for marker in content_markers:
            idx = full_text.find(marker)
            if idx > 0 and idx < 5000:  # Should be early in the page
                start_idx = idx
                break
        
        # Find where content likely ends
        end_markers = [
            'Related Tours', 'You may also like', 'Similar Trips',
            'Book Now Reserve', 'Contact Form', '© 20', 'Footer',
            'Share this', 'Leave a comment'
        ]
        
        end_idx = len(full_text)
        for marker in end_markers:
            idx = full_text.find(marker, start_idx + 500)
            if idx > 0:
                end_idx = min(end_idx, idx)
        
        # Extract content section
        text = full_text[start_idx:end_idx]
        
        # If extraction seems too short, fall back to full body
        if len(text) < 500:
            text = full_text[:15000]
        
        # Prepend price info if found
        if price_info:
            text = f"PRICING INFORMATION: {price_info}\n\n{text}"
        
        # Clean up the text
        text = self._clean_text(text)
        
        # Limit size for GPT processing
        return text[:12000]
    
    def _extract_price_info(self, soup: BeautifulSoup) -> str:
        """Extract price information from various page elements."""
        price_texts = []
        
        # Common price-related class/id patterns
        price_selectors = [
            '[class*="price"]', '[class*="Price"]', '[class*="cost"]', '[class*="Cost"]',
            '[class*="rate"]', '[class*="Rate"]', '[class*="amount"]', '[class*="Amount"]',
            '[id*="price"]', '[id*="Price"]', '[id*="cost"]', '[id*="rate"]',
            '.booking-price', '.tour-price', '.package-price', '.trip-cost',
            '[class*="booking"]', '[class*="sidebar"]',
        ]
        
        for selector in price_selectors:
            try:
                elements = soup.select(selector)
                for el in elements[:5]:  # Limit to first 5 matches per selector
                    text = el.get_text(strip=True)
                    # Check if it contains price-like patterns
                    if re.search(r'[\$€£]\s*[\d,]+|\d+\s*(?:USD|EUR|GBP|usd)|per person|pp|pax', text, re.I):
                        if len(text) < 500:  # Avoid huge blocks
                            price_texts.append(text)
            except Exception:
                continue
        
        # Also search for price patterns in the full text
        full_text = soup.get_text()
        price_patterns = [
            r'(?:Price|Cost|Rate|From|Starting)[\s:]*[\$€£]?\s*[\d,]+(?:\.\d{2})?(?:\s*(?:USD|EUR|per person|pp|pax))?',
            r'[\$€£]\s*[\d,]+(?:\.\d{2})?\s*(?:USD|EUR|per person|pp|pax)?',
            r'(?:USD|EUR|GBP)\s*[\d,]+(?:\.\d{2})?',
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, full_text, re.I)
            price_texts.extend(matches[:5])
        
        # Remove duplicates and join
        unique_prices = list(set(price_texts))
        return ' | '.join(unique_prices[:10]) if unique_prices else ''
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text."""
        
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        
        # Remove common noise patterns
        noise_patterns = [
            r'Cookie.*?accept',
            r'Subscribe.*?newsletter',
            r'Follow us on.*',
            r'Share this.*',
            r'©.*?\d{4}',
        ]
        for pattern in noise_patterns:
            text = re.sub(pattern, '', text, flags=re.I | re.S)
        
        return text.strip()
    
    def process_queue_item(self, queue_item) -> bool:
        """
        Process a single ScrapeQueue item.
        
        Returns True if successful, False otherwise.
        """
        from tour.models import RawItinerary, ScrapeQueue
        
        # Mark as in progress
        queue_item.status = 'in_progress'
        queue_item.save()
        
        try:
            # Scrape the URL
            rate_limit = queue_item.source.rate_limit_seconds if queue_item.source else 5
            result = self.scrape_url(queue_item.url, rate_limit)
            
            if result['success']:
                # Create RawItinerary record
                RawItinerary.objects.create(
                    source_type='scraped',
                    source=queue_item.source,
                    source_url=queue_item.url,
                    raw_html=result['raw_html'],
                    raw_text=result['raw_text'],
                    page_title=result['page_title'],
                    meta_description=result['meta_description'],
                    meta_keywords=result['meta_keywords'],
                )
                
                # Update queue item
                queue_item.status = 'completed'
                queue_item.processed_at = timezone.now()
                queue_item.save()
                
                # Update source stats
                if queue_item.source:
                    queue_item.source.total_scraped += 1
                    queue_item.source.last_scraped_at = timezone.now()
                    queue_item.source.save()
                
                return True
            else:
                raise Exception(result['error'])
                
        except Exception as e:
            queue_item.retry_count += 1
            queue_item.error_message = str(e)
            
            if queue_item.retry_count >= queue_item.max_retries:
                queue_item.status = 'failed'
            else:
                queue_item.status = 'pending'  # Will retry
            
            queue_item.save()
            return False
    
    def process_pending_queue(self, max_items: int = 10) -> dict:
        """
        Process pending items in the scrape queue.
        
        Returns stats dict with counts.
        """
        from tour.models import ScrapeQueue
        
        pending = ScrapeQueue.objects.filter(status='pending')[:max_items]
        
        stats = {
            'processed': 0,
            'succeeded': 0,
            'failed': 0,
        }
        
        for item in pending:
            stats['processed'] += 1
            if self.process_queue_item(item):
                stats['succeeded'] += 1
            else:
                stats['failed'] += 1
        
        return stats


def create_raw_from_uploaded_package(package) -> 'RawItinerary':
    """
    Create a RawItinerary from an UploadedPackage's extracted text.
    Used to feed uploaded PDFs into the AI processing pipeline.
    """
    from tour.models import RawItinerary
    
    if not package.extracted_text:
        return None
    
    raw = RawItinerary.objects.create(
        source_type='uploaded',
        uploaded_package=package,
        raw_text=package.extracted_text,
        page_title=package.title,
    )
    
    return raw
