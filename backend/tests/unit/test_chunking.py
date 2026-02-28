import pytest
import sys
import os

# fix path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.chunking_service import RecursiveMarkdownSplitter

@pytest.fixture
def splitter():
    return RecursiveMarkdownSplitter(chunk_size=50, chunk_overlap=0)

def test_split_by_headers(splitter):
    """test header parsing and metadata"""
    text = """# Header 1
Some content.

## Header 2
More content.

# Header 3
Final content.
"""
    chunks = splitter.split_text(text)
    
    # header 1 context
    assert "Header 1" in chunks[0].text
    assert chunks[0].metadata['headers'] == ['Header 1']
    
    # header 2 nested under header 1
    assert "Header 2" in chunks[1].text
    assert chunks[1].metadata['headers'] == ['Header 1', 'Header 2']
    
    # header 3 resets context
    assert "Header 3" in chunks[2].text
    assert chunks[2].metadata['headers'] == ['Header 3']

def test_recursive_split_blocks():
    """test splitting of large text blocks"""
    splitter = RecursiveMarkdownSplitter(chunk_size=20, chunk_overlap=0)
    text = "# Title\n\nThis is a very long paragraph that should definitely get split because it exceeds twenty chars."
    
    chunks = splitter.split_text(text)
    
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk.text) > 0
        assert chunk.metadata['headers'] == ['Title']

def test_hierarchy_preservation():
    """test deep hierarchy tracking"""
    text = """
# Root
## Child A
Content A.
### Grandchild A1
Content A1.
## Child B
Content B.
    """
    splitter = RecursiveMarkdownSplitter(chunk_size=1000)
    chunks = splitter.split_text(text)
    
    # verify grandchild context
    a1_chunk = next(c for c in chunks if "Content A1" in c.text)
    assert a1_chunk.metadata['headers'] == ['Root', 'Child A', 'Grandchild A1']
    
    # verify sibling context resets previous child
    b_chunk = next(c for c in chunks if "Content B" in c.text)
    assert b_chunk.metadata['headers'] == ['Root', 'Child B']
