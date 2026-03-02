import pytest
import sys
import os
from unittest.mock import MagicMock, patch

# fix path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.embedding_service import EmbeddingService

@pytest.fixture
def mock_openai():
    with patch("openai.OpenAI") as mock:
        yield mock

def test_get_embedding(mock_openai):
    # setup
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    
    # mock response structure
    mock_response = MagicMock()
    mock_data = MagicMock()
    mock_data.embedding = [0.1, 0.2, 0.3]
    mock_response.data = [mock_data]
    mock_client.embeddings.create.return_value = mock_response
    
    service = EmbeddingService(openai_key="test_key")
    
    # act
    embedding = service.get_embedding("test text")
    
    # assert
    assert embedding == [0.1, 0.2, 0.3]
    mock_client.embeddings.create.assert_called_once()
    call_args = mock_client.embeddings.create.call_args
    assert call_args.kwargs['model'] == "text-embedding-3-small"
    assert call_args.kwargs['input'] == ["test text"]

def test_get_embeddings_batch(mock_openai):
    # setup
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    
    # mock response for batch
    mock_response = MagicMock()
    d1 = MagicMock(); d1.embedding = [0.1]
    d2 = MagicMock(); d2.embedding = [0.2]
    mock_response.data = [d1, d2]
    mock_client.embeddings.create.return_value = mock_response
    
    service = EmbeddingService(openai_key="test_key")
    
    # act
    embeddings = service.get_embeddings(["text 1", "text 2"])
    
    # assert
    assert len(embeddings) == 2
    assert embeddings[0] == [0.1]
    assert embeddings[1] == [0.2]
