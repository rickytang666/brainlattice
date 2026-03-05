"""Unit tests for global seed extraction (Step 1)."""
import re
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def _extract_headers(text: str) -> str:
    """Mirrors IngestionProcessor._extract_headers logic for testing."""
    headers = []
    for line in text.split("\n"):
        if re.match(r"^#{1,3}\s+(.+)$", line):
            headers.append(line.strip())
    return "\n".join(headers)


def test_extract_headers_h1_h2_h3():
    """_extract_headers returns H1/H2/H3 lines only."""
    text = """# Calculus

Some intro text.

## Limits

Content about limits.

### Epsilon-Delta Definition

More content.

## Derivatives

### Chain Rule

## Integrals

# Linear Algebra

## Vector Spaces
"""
    headers = _extract_headers(text)
    lines = headers.split("\n")
    assert "# Calculus" in lines
    assert "## Limits" in lines
    assert "### Epsilon-Delta Definition" in lines
    assert "## Derivatives" in lines
    assert "### Chain Rule" in lines
    assert "## Integrals" in lines
    assert "# Linear Algebra" in lines
    assert "## Vector Spaces" in lines
    assert "Some intro text" not in headers
    assert "Content about limits" not in headers


def test_extract_headers_includes_h3_excludes_h4():
    """_extract_headers includes H1-H3, excludes H4+."""
    text = """# Root
## Child
### Grandchild
#### Great-grandchild (excluded)
"""
    headers = _extract_headers(text)
    assert "#### Great-grandchild" not in headers
    assert "### Grandchild" in headers


def test_global_seed_header_prompt_renders():
    """global_seed_header.jinja renders with header_text."""
    from services.llm.prompt_service import get_prompt_service

    prompts = get_prompt_service()
    out = prompts.render("global_seed_header.jinja", header_text="# Calculus\n## Limits")
    assert "convert these document headers" in out.lower()
    assert "# Calculus" in out
    assert "## Limits" in out
    assert "header_text" not in out  # variable should be rendered


def test_create_extraction_chunks():
    """create_extraction_chunks produces ~8k char chunks with overlap."""
    from services.chunking_service import create_extraction_chunks

    # 20k chars -> ~3 chunks (8k + 8k + 4k)
    text = "x" * 20000
    chunks = create_extraction_chunks(text, chunk_size=8000, overlap=200)
    assert len(chunks) >= 2
    assert all(hasattr(c, "page_content") for c in chunks)
    assert chunks[0].page_content == "x" * 8000


def test_chunk_extraction_prompt_renders():
    """chunk_extraction.jinja renders with chunk_text and seed_list."""
    from services.llm.prompt_service import get_prompt_service

    prompts = get_prompt_service()
    out = prompts.render(
        "chunk_extraction.jinja",
        chunk_text="The limit of a function...",
        seed_list=["calculus", "limit"],
    )
    assert "seed concept" in out.lower()
    assert "calculus" in out
    assert "limit" in out
    assert "The limit of a function" in out
