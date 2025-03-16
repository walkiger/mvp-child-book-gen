"""
Tests for the image generation functionality.
"""
import pytest
import base64
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open, AsyncMock
import tempfile
import shutil
import asyncio

from app.core.image_generation import (
    generate_character_images,
    generate_story_page_images
)

# Mock response for OpenAI image generation
class MockImageResponse:
    def __init__(self, url):
        self.url = url

class MockImageData:
    def __init__(self, data):
        self.data = data

@pytest.mark.asyncio
async def test_generate_character_images():
    # Mock OpenAI client
    mock_client = AsyncMock()
    mock_client.images.generate.return_value = MockImageData([
        MockImageResponse("https://example.com/image1.png")
    ])
    
    # Test parameters
    character_name = "Test Character"
    character_traits = ["friendly", "brave", "smart"]
    
    # Call the function
    result = await generate_character_images(
        client=mock_client,
        character_name=character_name,
        character_traits=character_traits
    )
    
    # Assertions
    assert len(result) == 2
    assert result[0] == "https://example.com/image1.png"
    assert result[1] == "https://example.com/image1.png"
    
    # Verify the client was called correctly
    assert mock_client.images.generate.call_count == 2
    
    # Check the first call arguments
    call_args = mock_client.images.generate.call_args_list[0][1]
    assert call_args["model"] == "dall-e-3"
    assert character_name in call_args["prompt"]
    assert "friendly" in call_args["prompt"]
    assert "brave" in call_args["prompt"]
    assert "smart" in call_args["prompt"]
    assert call_args["size"] == "1024x1024"
    assert call_args["n"] == 1

@pytest.mark.asyncio
async def test_generate_character_images_with_dalle2():
    # Mock OpenAI client
    mock_client = AsyncMock()
    mock_client.images.generate.return_value = MockImageData([
        MockImageResponse("https://example.com/image1.png")
    ])
    
    # Test parameters
    character_name = "Test Character"
    character_traits = ["friendly", "brave", "smart"]
    
    # Call the function with DALL-E 2
    result = await generate_character_images(
        client=mock_client,
        character_name=character_name,
        character_traits=character_traits,
        dalle_version="dall-e-2"
    )
    
    # Assertions
    assert len(result) == 2
    
    # Verify the client was called with dall-e-2
    call_args = mock_client.images.generate.call_args_list[0][1]
    assert call_args["model"] == "dall-e-2"

@pytest.mark.asyncio
async def test_generate_character_images_with_progress_callback():
    # Mock OpenAI client
    mock_client = AsyncMock()
    mock_client.images.generate.return_value = MockImageData([
        MockImageResponse("https://example.com/image1.png")
    ])
    
    # Mock progress callback
    progress_callback = MagicMock()
    
    # Test parameters
    character_name = "Test Character"
    character_traits = ["friendly", "brave", "smart"]
    
    # Call the function
    result = await generate_character_images(
        client=mock_client,
        character_name=character_name,
        character_traits=character_traits,
        progress_callback=progress_callback
    )
    
    # Assertions
    assert len(result) == 2
    
    # Verify the progress callback was called
    assert progress_callback.call_count == 2
    progress_callback.assert_any_call(1, "https://example.com/image1.png")
    progress_callback.assert_any_call(2, "https://example.com/image1.png")

@pytest.mark.asyncio
async def test_generate_character_images_error_handling():
    # Mock OpenAI client that raises an exception
    mock_client = AsyncMock()
    mock_client.images.generate.side_effect = Exception("API Error")
    
    # Test parameters
    character_name = "Test Character"
    character_traits = ["friendly", "brave", "smart"]
    
    # Call the function and expect an exception
    with pytest.raises(Exception) as excinfo:
        await generate_character_images(
            client=mock_client,
            character_name=character_name,
            character_traits=character_traits
        )
    
    assert "API Error" in str(excinfo.value)

@pytest.mark.asyncio
async def test_generate_story_page_images():
    # Mock OpenAI client
    mock_client = AsyncMock()
    mock_client.images.generate.return_value = MockImageData([
        MockImageResponse("https://example.com/page_image.png")
    ])
    
    # Test parameters
    character_name = "Test Character"
    character_traits = ["friendly", "brave", "smart"]
    story_content = {
        "pages": [
            {
                "page_number": 1,
                "text": "Once upon a time...",
                "visual_description": "A character standing in a forest"
            },
            {
                "page_number": 2,
                "text": "The adventure begins...",
                "visual_description": "A character climbing a mountain"
            }
        ]
    }
    
    # Call the function
    result = await generate_story_page_images(
        client=mock_client,
        story_content=story_content,
        character_name=character_name,
        character_traits=character_traits
    )
    
    # Assertions
    assert len(result) == 2
    assert result[0]["page_number"] == 1
    assert len(result[0]["image_urls"]) == 2
    assert result[0]["image_urls"][0] == "https://example.com/page_image.png"
    assert result[1]["page_number"] == 2
    assert len(result[1]["image_urls"]) == 2
    
    # Verify the client was called correctly
    assert mock_client.images.generate.call_count == 4  # 2 pages x 2 images each
    
    # Check call arguments for first page
    call_args = mock_client.images.generate.call_args_list[0][1]
    assert call_args["model"] == "dall-e-3"
    assert character_name in call_args["prompt"]
    assert "forest" in call_args["prompt"]
    assert call_args["size"] == "1024x1024"
    
    # Check call arguments for second page
    call_args = mock_client.images.generate.call_args_list[2][1]
    assert "mountain" in call_args["prompt"] 