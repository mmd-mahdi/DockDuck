import re
import logging
from typing import List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TextChunk:
    """Represents a chunk of text with metadata"""
    content: str
    metadata: Dict[str, Any]
    chunk_id: int


class DocumentChunker:
    """Enhanced document chunker with multiple strategies and strict quality filtering"""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Enhanced patterns for splitting
        self.sentence_endings = re.compile(r'[.!?]+[\s\n]+')
        self.paragraph_endings = re.compile(r'\n\s*\n')

    def classify_content_type(self, text: str) -> str:
        """Classify content type to filter out non-book content"""
        text_lower = text.lower()

        # Front matter detection
        front_matter_indicators = [
            'published by', 'copyright', 'all rights reserved',
            'isbn', 'first edition', 'printed in', 'distributed by'
        ]
        if any(indicator in text_lower for indicator in front_matter_indicators):
            return 'front_matter'

        # Table of contents detection
        toc_indicators = ['contents', 'chapters', 'page']
        if any(word in text_lower for word in toc_indicators):
            if len(text) < 800 and (text_lower.count('page') > 1 or '......' in text):
                return 'toc'

        # Header detection
        lines = text.split('\n')
        if len(lines) <= 3 and all(len(line) < 100 for line in lines):
            return 'header'

        # Repetitive content detection
        words = text.split()
        if len(words) > 10:
            unique_words = set(words)
            if len(unique_words) / len(words) < 0.3:
                return 'repetitive'

        return 'main_content'

    def is_quality_chunk(self, chunk_content: str) -> bool:
        """Strict quality filtering for meaningful content"""
        content = chunk_content.strip()

        # Length checks
        if len(content) < 80 or len(content) > self.chunk_size * 1.5:
            return False

        # Check content type
        content_type = self.classify_content_type(content)
        if content_type in ['front_matter', 'toc', 'header']:
            return False

        # Check for meaningful word density
        words = re.findall(r'\b[a-zA-Z]{3,}\b', content)
        if len(words) < 8:
            return False

        # Word diversity (avoid repetitive content)
        unique_ratio = len(set(words)) / len(words)
        if unique_ratio < 0.5 and len(words) > 15:
            return False

        # Check for reasonable sentence structure
        sentences = re.findall(r'[^.!?]+[.!?]', content)
        if len(sentences) >= 2:
            avg_sentence_length = sum(len(s) for s in sentences) / len(sentences)
            if avg_sentence_length < 25 or avg_sentence_length > 300:
                return False

        # Check for excessive special characters
        special_chars = len(re.findall(r'[\.\-\=\*]', content))
        if special_chars > len(content) * 0.2:
            return False

        # Check for meaningful text ratio (vs whitespace)
        text_ratio = len(content.replace(' ', '').replace('\n', '')) / len(content)
        if text_ratio < 0.6:
            return False

        return True

    def calculate_quality_score(self, text: str) -> float:
        """Calculate a comprehensive quality score for text chunks"""
        score = 0.0

        # Length score (ideal: 70-100% of target chunk size)
        length_ratio = len(text) / self.chunk_size
        if 0.7 <= length_ratio <= 1.0:
            score += 0.4
        elif 0.5 <= length_ratio <= 1.2:
            score += 0.2

        # Word diversity score
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text)
        if len(words) >= 8:
            unique_ratio = len(set(words)) / len(words)
            score += unique_ratio * 0.3

        # Sentence structure score
        sentences = re.findall(r'[.!?]+', text)
        if len(sentences) >= 2:
            avg_sent_len = sum(len(s) for s in sentences) / len(sentences)
            if 40 <= avg_sent_len <= 200:
                score += 0.3

        return min(1.0, score)

    def chunk_by_fixed_size(self, document: Dict[str, Any]) -> List[TextChunk]:
        """Fixed-size chunking that actually respects the target size"""
        content = document["content"]
        base_metadata = document["metadata"]

        chunks = []
        chunk_id = 0
        start = 0
        content_length = len(content)

        while start < content_length:
            # Calculate end position
            end = min(start + self.chunk_size, content_length)

            # Get initial chunk
            chunk_content = content[start:end].strip()

            if not chunk_content:
                break

            # Try to find a good break point near the end
            if end < content_length:
                # Look for sentence boundaries first
                sentence_breaks = list(re.finditer(r'[.!?]\s+', chunk_content))
                if sentence_breaks and len(sentence_breaks) > 1:
                    # Use the last sentence break
                    last_break = sentence_breaks[-1]
                    chunk_content = content[start:start + last_break.end()].strip()
                    end = start + last_break.end()
                else:
                    # Fallback to paragraph breaks
                    paragraph_breaks = list(re.finditer(r'\n\s*\n', chunk_content))
                    if paragraph_breaks:
                        last_break = paragraph_breaks[-1]
                        chunk_content = content[start:start + last_break.end()].strip()
                        end = start + last_break.end()
                    else:
                        # Fallback to word boundary
                        last_space = chunk_content.rfind(' ')
                        if last_space > self.chunk_size * 0.6:
                            chunk_content = content[start:start + last_space].strip()
                            end = start + last_space

            # Check quality and add chunk
            if chunk_content and self.is_quality_chunk(chunk_content):
                chunks.append(TextChunk(
                    content=chunk_content,
                    metadata={
                        "chunk_size": len(chunk_content),
                        "chunking_strategy": "fixed_size",
                        "quality_score": self.calculate_quality_score(chunk_content),
                        "content_type": self.classify_content_type(chunk_content),
                        "start_pos": start,
                        "end_pos": end
                    },
                    chunk_id=chunk_id
                ))
                chunk_id += 1

            # Move start position (with overlap if specified)
            if self.chunk_overlap > 0:
                start = end - self.chunk_overlap
            else:
                start = end

            # Ensure we make progress
            if start <= end - 10:  # Minimum progress check
                start = end

        return chunks

    def chunk_by_sentences_enhanced(self, document: Dict[str, Any]) -> List[TextChunk]:
        """Enhanced sentence-based chunking with strict size control"""
        content = document["content"]

        # Split into sentences
        sentences = self.sentence_endings.split(content)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 20]

        chunks = []
        current_chunk = ""
        current_sentences = []
        chunk_id = 0

        for sentence in sentences:
            # If adding this sentence would exceed chunk size
            if len(current_chunk) + len(sentence) > self.chunk_size and current_chunk:
                # Finalize current chunk if it meets quality standards
                if self.is_quality_chunk(current_chunk):
                    chunks.append(TextChunk(
                        content=current_chunk.strip(),
                        metadata={
                            "chunk_size": len(current_chunk),
                            "chunking_strategy": "sentence_based",
                            "sentence_count": len(current_sentences),
                            "quality_score": self.calculate_quality_score(current_chunk),
                            "content_type": self.classify_content_type(current_chunk)
                        },
                        chunk_id=chunk_id
                    ))
                    chunk_id += 1

                # Start new chunk with overlap
                if self.chunk_overlap > 0 and current_sentences:
                    # Keep last few sentences for overlap
                    overlap_count = max(1, min(3, len(current_sentences) // 3))
                    current_sentences = current_sentences[-overlap_count:]
                    current_chunk = ' '.join(current_sentences) + ' '
                else:
                    current_sentences = []
                    current_chunk = ""

            current_sentences.append(sentence)
            current_chunk = ' '.join(current_sentences)

        # Add final chunk if it meets quality standards
        if current_chunk.strip() and self.is_quality_chunk(current_chunk):
            chunks.append(TextChunk(
                content=current_chunk.strip(),
                metadata={
                    "chunk_size": len(current_chunk),
                    "chunking_strategy": "sentence_based",
                    "sentence_count": len(current_sentences),
                    "quality_score": self.calculate_quality_score(current_chunk),
                    "content_type": self.classify_content_type(current_chunk)
                },
                chunk_id=chunk_id
            ))

        return chunks

    def chunk_document(self, document: Dict[str, Any], strategy: str = "fixed_size") -> List[TextChunk]:
        """Main method to chunk a document with strategy selection"""
        content = document["content"]
        base_metadata = document["metadata"]

        logger.info(f"Starting chunking for {base_metadata['file_path']} with {strategy} strategy")
        logger.info(f"Target chunk size: {self.chunk_size}, overlap: {self.chunk_overlap}")

        if strategy == "fixed_size":
            chunks = self.chunk_by_fixed_size(document)
        elif strategy == "sentence":
            chunks = self.chunk_by_sentences_enhanced(document)
        else:
            raise ValueError(f"Unknown chunking strategy: {strategy}")

        # Filter chunks by quality
        initial_count = len(chunks)
        quality_chunks = [chunk for chunk in chunks if self.is_quality_chunk(chunk.content)]

        # Enhance chunk metadata with document info
        for chunk in quality_chunks:
            chunk.metadata.update({
                "source_file": base_metadata["file_path"],
                "file_type": base_metadata["file_type"],
                "original_metadata": {k: v for k, v in base_metadata.items()
                                      if k not in ['file_path', 'file_type']}
            })

        filtered_count = initial_count - len(quality_chunks)
        logger.info(f"Created {len(quality_chunks)} quality chunks "
                    f"(filtered {filtered_count} low-quality chunks)")

        # Log chunk size statistics
        if quality_chunks:
            chunk_sizes = [chunk.metadata['chunk_size'] for chunk in quality_chunks]
            avg_size = sum(chunk_sizes) / len(chunk_sizes)
            logger.info(f"Chunk size stats: avg={avg_size:.0f}, "
                        f"min={min(chunk_sizes)}, max={max(chunk_sizes)}")

        return quality_chunks

    def set_chunking_strategy(self, chunk_size: int, chunk_overlap: int):
        """Update chunking parameters"""
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        logger.info(f"Updated chunking strategy: size={chunk_size}, overlap={chunk_overlap}")