import logging
import time
from src.document_processing.loader import DocumentLoader
from src.document_processing.preprocessor import TextPreprocessor
from src.document_processing.chunker import DocumentChunker

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def test_document_processing(file_path: str):
    """Comprehensive test of the improved document processing pipeline"""

    print("🚀 Testing Improved Document Processing Pipeline")
    print("=" * 60)

    # Initialize components with optimized settings
    loader = DocumentLoader()
    preprocessor = TextPreprocessor()

    # Test different chunking strategies and sizes
    strategies = [
        ("fixed_size_400", "fixed_size", 400, 40),
        ("fixed_size_600", "fixed_size", 600, 60),
        ("sentence_500", "sentence", 500, 50),
    ]

    all_results = {}

    try:
        # 1. Load document
        print(f"📖 Loading document: {file_path}")
        start_time = time.time()
        document = loader.load_document(file_path)
        load_time = time.time() - start_time

        print(f"✅ Loaded {document['metadata']['file_type'].upper()} document")
        print(f"   - Pages: {document['metadata'].get('page_count', 'N/A')}")
        print(f"   - Meaningful pages: {document['metadata'].get('meaningful_pages', 'N/A')}")
        print(f"   - File size: {document['metadata'].get('file_size', 0) / 1024:.1f} KB")
        print(f"   - Load time: {load_time:.2f}s")

        # 2. Preprocess
        print("\n🔧 Preprocessing document...")
        start_time = time.time()
        document = preprocessor.preprocess_document(document)
        preprocess_time = time.time() - start_time

        preprocessing_info = document['metadata']['preprocessing']
        print(f"✅ Preprocessing complete:")
        print(f"   - Original length: {preprocessing_info['original_length']} chars")
        print(f"   - Cleaned length: {preprocessing_info['cleaned_length']} chars")
        print(f"   - Reduction: {preprocessing_info['reduction_percent']}%")
        print(f"   - Word count: {preprocessing_info['language_patterns']['word_count']}")
        print(f"   - Preprocess time: {preprocess_time:.2f}s")

        # Test each chunking strategy
        for strategy_name, strategy_type, chunk_size, overlap in strategies:
            print(f"\n{'=' * 50}")
            print(f"🧪 Testing {strategy_name} (size: {chunk_size}, overlap: {overlap})")

            chunker = DocumentChunker(chunk_size=chunk_size, chunk_overlap=overlap)

            start_time = time.time()
            chunks = chunker.chunk_document(document, strategy=strategy_type)
            chunk_time = time.time() - start_time

            # Analyze results
            if chunks:
                chunk_sizes = [chunk.metadata['chunk_size'] for chunk in chunks]
                quality_scores = [chunk.metadata.get('quality_score', 0) for chunk in chunks]
                content_types = [chunk.metadata.get('content_type', 'unknown') for chunk in chunks]

                avg_size = sum(chunk_sizes) / len(chunk_sizes)
                avg_quality = sum(quality_scores) / len(quality_scores)

                content_type_counts = {}
                for ct in content_types:
                    content_type_counts[ct] = content_type_counts.get(ct, 0) + 1

                print(f"✅ {strategy_name} Results:")
                print(f"   - Total chunks: {len(chunks)}")
                print(f"   - Average size: {avg_size:.0f} chars")
                print(f"   - Size range: {min(chunk_sizes)} - {max(chunk_sizes)} chars")
                print(f"   - Average quality: {avg_quality:.2f}")
                print(f"   - Content types: {content_type_counts}")
                print(f"   - Chunking time: {chunk_time:.2f}s")

                # Show sample of high-quality chunks
                high_quality_chunks = [c for c in chunks if c.metadata.get('quality_score', 0) > 0.7]
                if high_quality_chunks:
                    print(f"   - High-quality chunks (>0.7): {len(high_quality_chunks)}")
                    print(f"\n   📄 Sample high-quality chunks:")
                    for i, chunk in enumerate(high_quality_chunks[:2]):
                        preview = chunk.content[:100].replace('\n', ' ')
                        print(f"     {i + 1}. [{chunk.metadata['chunk_size']} chars, "
                              f"quality: {chunk.metadata['quality_score']:.2f}]")
                        print(f"        {preview}...")

                all_results[strategy_name] = {
                    'chunk_count': len(chunks),
                    'avg_size': avg_size,
                    'avg_quality': avg_quality,
                    'content_types': content_type_counts
                }
            else:
                print(f"❌ {strategy_name}: No chunks produced")
                all_results[strategy_name] = {'chunk_count': 0}

        # Summary
        print(f"\n{'=' * 60}")
        print("📊 SUMMARY OF ALL STRATEGIES")
        print("=" * 60)
        for strategy_name, results in all_results.items():
            print(f"  {strategy_name}:")
            print(f"    - Chunks: {results.get('chunk_count', 0)}")
            print(f"    - Avg Size: {results.get('avg_size', 0):.0f} chars")
            print(f"    - Avg Quality: {results.get('avg_quality', 0):.2f}")
            if 'content_types' in results:
                print(f"    - Content Types: {results['content_types']}")

        return all_results

    except Exception as e:
        print(f"❌ Error processing document: {e}")
        import traceback
        traceback.print_exc()
        return {}


if __name__ == "__main__":
    # Test with your PDF
    sample_file = "data/raw/sample.pdf"
    results = test_document_processing(sample_file)