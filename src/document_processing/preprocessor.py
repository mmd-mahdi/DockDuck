import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class TextPreprocessor:
    """Enhanced text cleaning and normalization"""

    def __init__(self):
        # Improved patterns for cleaning
        self.patterns = {
            'multiple_newlines': re.compile(r'\n\s*\n\s*\n+'),
            'multiple_spaces': re.compile(r'[ \t]+'),
            'special_chars': re.compile(r'[^\w\s.,!?;:()\-@\']'),
            'urls': re.compile(r'https?://\S+'),
            'emails': re.compile(r'\S+@\S+'),
            'consecutive_dots': re.compile(r'\.{4,}'),
            'isolated_chars': re.compile(r'\s+[a-zA-Z]\s+'),  # Single letters
        }

    def clean_text(self, text: str) -> str:
        """Enhanced text cleaning and normalization"""
        if not text:
            return ""

        # Step 1: Remove URLs and emails
        text = self.patterns['urls'].sub(' ', text)
        text = self.patterns['emails'].sub(' ', text)

        # Step 2: Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # Step 3: Remove excessive newlines
        text = self.patterns['multiple_newlines'].sub('\n\n', text)

        # Step 4: Remove excessive spaces and tabs
        text = self.patterns['multiple_spaces'].sub(' ', text)

        # Step 5: Clean up special characters (keep basic punctuation)
        text = self.patterns['special_chars'].sub(' ', text)

        # Step 6: Fix consecutive dots
        text = self.patterns['consecutive_dots'].sub('...', text)

        # Step 7: Remove isolated single characters
        text = self.patterns['isolated_chars'].sub(' ', text)

        # Step 8: Strip leading/trailing whitespace
        text = text.strip()

        return text

    def normalize_whitespace(self, text: str) -> str:
        """Normalize all whitespace characters"""
        return ' '.join(text.split())

    def detect_language_patterns(self, text: str) -> Dict[str, Any]:
        """Detect language and content patterns"""
        # Simple pattern detection
        arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        total_chars = len(text)

        return {
            "arabic_ratio": arabic_chars / total_chars if total_chars > 0 else 0,
            "english_ratio": english_chars / total_chars if total_chars > 0 else 0,
            "sentence_count": len(re.findall(r'[.!?]+', text)),
            "paragraph_count": len(text.split('\n\n')),
            "word_count": len(re.findall(r'\b[a-zA-Z]{3,}\b', text))
        }

    def preprocess_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced document preprocessing with pattern detection"""
        original_content = document["content"]
        cleaned_content = self.clean_text(original_content)

        # Detect language patterns
        patterns = self.detect_language_patterns(cleaned_content)

        # Add enhanced preprocessing info to metadata
        document["metadata"]["preprocessing"] = {
            "original_length": len(original_content),
            "cleaned_length": len(cleaned_content),
            "reduction_percent": round((1 - len(cleaned_content) / len(original_content)) * 100, 2)
            if original_content else 0,
            "language_patterns": patterns
        }

        document["content"] = cleaned_content
        logger.info(f"Preprocessed document: {len(cleaned_content)} chars, "
                    f"word count: {patterns['word_count']}")

        return document