"""
Advanced Spam Filtering Module
"""

import re
import urllib.parse
from typing import List, Dict, Tuple
from config import MAX_LINKS_PER_MESSAGE, ALLOWED_DOMAINS


class SpamFilter:
    """Advanced spam detection and filtering system."""
    
    def __init__(self):
        # Simple URL patterns for link detection only
        self.url_patterns = [
            r'https?://[^\s]+',  # http:// or https:// links
            r't\.me/[^\s]+',     # t.me links
            r'telegram\.me/[^\s]+',  # telegram.me links
            r'@[a-zA-Z0-9_]+',   # @username
            r'bit\.ly/[^\s]+',   # bit.ly links
            r'tinyurl\.com/[^\s]+',  # tinyurl links
            r'goo\.gl/[^\s]+',   # goo.gl links
            r'is\.gd/[^\s]+',    # is.gd links
            r'v\.gd/[^\s]+',     # v.gd links
            r'ow\.ly/[^\s]+',    # ow.ly links
        ]
        
        self.allowed_domains = ALLOWED_DOMAINS
        self.max_links = MAX_LINKS_PER_MESSAGE
        
        # Compile regex patterns for better performance
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) 
                                for pattern in self.url_patterns]
    
    def extract_urls(self, text: str) -> List[str]:
        """Extract all URLs from text."""
        # Simple URL patterns to catch all types of links
        url_patterns = [
            r'https?://[^\s]+',  # http:// or https:// links
            r't\.me/[^\s]+',     # t.me links
            r'telegram\.me/[^\s]+',  # telegram.me links
            r'@[a-zA-Z0-9_]+',   # @username
            r'bit\.ly/[^\s]+',   # bit.ly links
            r'tinyurl\.com/[^\s]+',  # tinyurl links
            r'goo\.gl/[^\s]+',   # goo.gl links
            r'is\.gd/[^\s]+',    # is.gd links
            r'v\.gd/[^\s]+',     # v.gd links
            r'ow\.ly/[^\s]+',    # ow.ly links
        ]
        
        urls = []
        for pattern in url_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            urls.extend(matches)
        
        return urls
    
    def get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            parsed = urllib.parse.urlparse(url)
            return parsed.netloc.lower()
        except:
            return ""
    
    def is_allowed_domain(self, url: str) -> bool:
        """Check if URL domain is in allowed list."""
        domain = self.get_domain(url)
        return domain in self.allowed_domains
    
    def check_spam_patterns(self, text: str) -> Tuple[bool, List[str]]:
        """Check text against spam patterns."""
        if not text:
            return False, []
        
        text_lower = text.lower()
        matched_patterns = []
        
        for pattern in self.compiled_patterns:
            if pattern.search(text_lower):
                matched_patterns.append(pattern.pattern)
        
        return len(matched_patterns) > 0, matched_patterns
    
    def check_link_spam(self, text: str) -> Tuple[bool, str]:
        """Check for link spam."""
        urls = self.extract_urls(text)
        
        if len(urls) > self.max_links:
            return True, f"Too many links ({len(urls)} > {self.max_links})"
        
        # Check for suspicious domains
        suspicious_domains = []
        for url in urls:
            if not self.is_allowed_domain(url):
                domain = self.get_domain(url)
                if domain and domain not in suspicious_domains:
                    suspicious_domains.append(domain)
        
        if suspicious_domains:
            return True, f"Suspicious domains: {', '.join(suspicious_domains)}"
        
        return False, ""
    
    def check_content_spam(self, text: str) -> Tuple[bool, List[str]]:
        """Check for content-based spam."""
        is_spam, patterns = self.check_spam_patterns(text)
        
        # Additional checks
        words = text.lower().split()
        
        # Check for repetitive words
        word_count = {}
        for word in words:
            if len(word) > 3:  # Skip short words
                word_count[word] = word_count.get(word, 0) + 1
        
        repetitive_words = [word for word, count in word_count.items() 
                          if count > 3]
        
        if repetitive_words:
            patterns.append(f"Repetitive words: {', '.join(repetitive_words)}")
            is_spam = True
        
        # Check for excessive caps
        caps_ratio = sum(1 for c in text if c.isupper()) / len(text) if text else 0
        if caps_ratio > 0.7:
            patterns.append("Excessive capitalization")
            is_spam = True
        
        return is_spam, patterns
    
    def analyze_message(self, text: str) -> Dict:
        """Complete spam analysis of a message."""
        if not text:
            return {
                'is_spam': False,
                'reasons': [],
                'confidence': 0.0
            }
        
        results = {
            'is_spam': False,
            'reasons': [],
            'confidence': 0.0
        }
        
        # Check link spam
        link_spam, link_reason = self.check_link_spam(text)
        if link_spam:
            results['reasons'].append(link_reason)
            results['confidence'] += 0.4
        
        # Check content spam
        content_spam, content_reasons = self.check_content_spam(text)
        if content_spam:
            results['reasons'].extend(content_reasons)
            results['confidence'] += 0.3
        
        # Check for suspicious keywords
        suspicious_keywords = [
            'earn money', 'make money', 'quick money', 'investment',
            'bitcoin', 'crypto', 'forex', 'trading', 'casino',
            'lottery', 'prize', 'winner', 'free iphone', 'gift card'
        ]
        
        text_lower = text.lower()
        found_keywords = [kw for kw in suspicious_keywords if kw in text_lower]
        
        if found_keywords:
            results['reasons'].append(f"Suspicious keywords: {', '.join(found_keywords)}")
            results['confidence'] += 0.2
        
        # Determine if message is spam
        results['is_spam'] = results['confidence'] > 0.3
        
        return results
    
    def get_warning_message(self, user_mention: str, reasons: List[str]) -> str:
        """Generate warning message for spam detection."""
        if not reasons:
            reasons = ["spam content"]
        
        warning = f"⚠️ <b>Warning!</b>\n\n{user_mention}, your message was removed for:\n"
        
        for i, reason in enumerate(reasons[:3], 1):  # Show first 3 reasons
            warning += f"• {reason}\n"
        
        warning += "\nPlease follow group rules and avoid sharing ads or spam links."
        
        return warning


# Global spam filter instance
spam_filter = SpamFilter() 