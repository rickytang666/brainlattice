import pytest
import sys
import os
from unittest.mock import MagicMock, patch

# fix path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.storage_service import S3StorageService

@pytest.fixture
def mock_boto3():
    with patch("boto3.client") as mock:
        yield mock

def test_upload_file(mock_boto3):
    # setup
    mock_s3 = MagicMock()
    mock_boto3.return_value = mock_s3
    
    service = S3StorageService()
    content = b"test content"
    filename = "test.pdf"
    
    # act
    result = service.upload_file(content, filename)
    
    # assert
    assert result == filename
    mock_s3.upload_fileobj.assert_called_once()
    
def test_download_file(mock_boto3):
    # setup
    mock_s3 = MagicMock()
    mock_boto3.return_value = mock_s3
    
    # mock download_fileobj writing to the buffer
    def side_effect(bucket, key, fileobj):
        fileobj.write(b"downloaded content")

    mock_s3.download_fileobj.side_effect = side_effect
    
    service = S3StorageService()
    
    # act
    content = service.download_file("test.pdf")
    
    # assert
    assert content == b"downloaded content"
    mock_s3.download_fileobj.assert_called_once()    

def test_delete_file(mock_boto3):
    # setup
    mock_s3 = MagicMock()
    mock_boto3.return_value = mock_s3
    
    service = S3StorageService()
    
    # act
    service.delete_file("test.pdf")
    
    # assert
    mock_s3.delete_object.assert_called_once_with(Bucket=service.bucket, Key="test.pdf")
