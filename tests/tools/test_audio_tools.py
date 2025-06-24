"""
Tests for audio and text-to-speech MCP tools.

This module contains tests for the audio control and text-to-speech tools
using mocks for AppleScript execution and KM interface.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import os
from typing import Dict, Any

from fastmcp import FastMCP
from src.core.km_interface import KMInterface
from src.core.audio_core import AudioCore, AudioResult, TTSResult
from src.tools.audio_operations import register_audio_tools


@pytest.fixture
def mock_km_interface():
    """Create mock KM interface for testing."""
    mock = AsyncMock(spec=KMInterface)
    
    # Configure mock AppleScript execution
    mock.execute_applescript = AsyncMock()
    mock.execute_applescript.return_value = MagicMock(
        success=True,
        output="0",
        error=None
    )
    
    return mock


@pytest.fixture
def mock_audio_core():
    """Create mock AudioCore for testing."""
    mock = AsyncMock(spec=AudioCore)
    
    # Configure mock methods
    mock.play_sound.return_value = AudioResult(
        success=True,
        operation="play",
        processing_time=0.1,
        output="/path/to/sound.mp3"
    )
    
    mock.set_system_volume.return_value = AudioResult(
        success=True,
        operation="set_volume",
        processing_time=0.05,
        output="75"
    )
    
    mock.get_system_volume.return_value = AudioResult(
        success=True,
        operation="get_volume",
        processing_time=0.03,
        output="50"
    )
    
    mock.mute_system_audio.return_value = AudioResult(
        success=True,
        operation="mute",
        processing_time=0.02
    )
    
    mock.speak_text.return_value = TTSResult(
        success=True,
        text_length=15,
        processing_time=0.2,
        voice="Alex"
    )
    
    mock.list_available_voices.return_value = [
        "Alex", "Samantha", "Daniel", "Karen"
    ]
    
    return mock


@pytest.fixture
def audio_mcp_server(mock_km_interface, mock_audio_core):
    """Create FastMCP server with audio tools registered."""
    server = FastMCP("test-audio-server")
    
    # Patch AudioCore constructor to return our mock
    with patch('src.tools.audio_operations.AudioCore', return_value=mock_audio_core):
        register_audio_tools(server, mock_km_interface)
    
    return server


class TestAudioTools:
    """Test suite for audio and text-to-speech tools."""
    
    @pytest.mark.asyncio
    async def test_km_audio_control_play(self, audio_mcp_server, mock_audio_core):
        """Test play operation with valid parameters."""
        file_path = "/path/to/sound.mp3"
        
        result = await audio_mcp_server.call_tool("km_audio_control", {
            "operation": "play",
            "file_path": file_path
        })
        
        # Check result structure
        assert result[0].text is not None
        
        # Parse JSON result
        import json
        response = json.loads(result[0].text)
        
        # Verify response
        assert response["success"] is True
        assert response["operation"] == "play"
        assert response["file"] == file_path
        assert "processing_time" in response
        
        # Verify mock was called correctly
        mock_audio_core.play_sound.assert_called_once_with(file_path, None)
    
    @pytest.mark.asyncio
    async def test_km_audio_control_play_with_volume(self, audio_mcp_server, mock_audio_core):
        """Test play operation with volume parameter."""
        file_path = "/path/to/sound.mp3"
        volume_level = 75
        
        result = await audio_mcp_server.call_tool("km_audio_control", {
            "operation": "play",
            "file_path": file_path,
            "volume_level": volume_level
        })
        
        # Parse JSON result
        import json
        response = json.loads(result[0].text)
        
        # Verify response
        assert response["success"] is True
        assert response["file"] == file_path
        
        # Verify mock was called correctly
        mock_audio_core.play_sound.assert_called_once_with(file_path, volume_level)
    
    @pytest.mark.asyncio
    async def test_km_audio_control_volume(self, audio_mcp_server, mock_audio_core):
        """Test volume operation with valid parameters."""
        volume_level = 75
        
        result = await audio_mcp_server.call_tool("km_audio_control", {
            "operation": "volume",
            "volume_level": volume_level
        })
        
        # Parse JSON result
        import json
        response = json.loads(result[0].text)
        
        # Verify response
        assert response["success"] is True
        assert response["operation"] == "set_volume"
        assert response["level"] == volume_level
        
        # Verify mock was called correctly
        mock_audio_core.set_system_volume.assert_called_once_with(volume_level)
    
    @pytest.mark.asyncio
    async def test_km_audio_control_mute(self, audio_mcp_server, mock_audio_core):
        """Test mute operation."""
        result = await audio_mcp_server.call_tool("km_audio_control", {
            "operation": "mute"
        })
        
        # Parse JSON result
        import json
        response = json.loads(result[0].text)
        
        # Verify response
        assert response["success"] is True
        assert response["operation"] == "mute"
        
        # Verify mock was called correctly
        mock_audio_core.mute_system_audio.assert_called_once_with(True)
    
    @pytest.mark.asyncio
    async def test_km_audio_control_unmute(self, audio_mcp_server, mock_audio_core):
        """Test unmute operation."""
        result = await audio_mcp_server.call_tool("km_audio_control", {
            "operation": "unmute"
        })
        
        # Parse JSON result
        import json
        response = json.loads(result[0].text)
        
        # Verify response
        assert response["success"] is True
        assert response["operation"] == "unmute"
        
        # Verify mock was called correctly
        mock_audio_core.mute_system_audio.assert_called_once_with(False)
    
    @pytest.mark.asyncio
    async def test_km_audio_control_get_volume(self, audio_mcp_server, mock_audio_core):
        """Test get_volume operation."""
        result = await audio_mcp_server.call_tool("km_audio_control", {
            "operation": "get_volume"
        })
        
        # Parse JSON result
        import json
        response = json.loads(result[0].text)
        
        # Verify response
        assert response["success"] is True
        assert response["operation"] == "get_volume"
        assert response["level"] == 50  # From mock response
        
        # Verify mock was called correctly
        mock_audio_core.get_system_volume.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_km_audio_control_invalid_operation(self, audio_mcp_server):
        """Test with invalid operation parameter."""
        result = await audio_mcp_server.call_tool("km_audio_control", {
            "operation": "invalid_op"
        })
        
        # Parse JSON result
        import json
        response = json.loads(result[0].text)
        
        # Verify response
        assert response["success"] is False
        assert "error" in response
        assert "error_code" in response
    
    @pytest.mark.asyncio
    async def test_km_audio_control_missing_file_path(self, audio_mcp_server):
        """Test play operation without file_path."""
        result = await audio_mcp_server.call_tool("km_audio_control", {
            "operation": "play"
        })
        
        # Parse JSON result
        import json
        response = json.loads(result[0].text)
        
        # Verify response
        assert response["success"] is False
        assert "error" in response
        assert "error_code" in response
    
    @pytest.mark.asyncio
    async def test_km_audio_control_missing_volume_level(self, audio_mcp_server):
        """Test volume operation without volume_level."""
        result = await audio_mcp_server.call_tool("km_audio_control", {
            "operation": "volume"
        })
        
        # Parse JSON result
        import json
        response = json.loads(result[0].text)
        
        # Verify response
        assert response["success"] is False
        assert "error" in response
        assert "error_code" in response
    
    @pytest.mark.asyncio
    async def test_km_text_to_speech(self, audio_mcp_server, mock_audio_core):
        """Test text-to-speech with basic parameters."""
        text = "Hello, world!"
        
        result = await audio_mcp_server.call_tool("km_text_to_speech", {
            "text": text
        })
        
        # Parse JSON result
        import json
        response = json.loads(result[0].text)
        
        # Verify response
        assert response["success"] is True
        assert response["text_length"] == 15  # From mock response
        assert response["operation"] == "speak"
        
        # Verify mock was called correctly
        mock_audio_core.speak_text.assert_called_once_with(text, None, None, None)
    
    @pytest.mark.asyncio
    async def test_km_text_to_speech_with_voice(self, audio_mcp_server, mock_audio_core):
        """Test text-to-speech with voice parameter."""
        text = "Hello, world!"
        voice = "Alex"
        
        result = await audio_mcp_server.call_tool("km_text_to_speech", {
            "text": text,
            "voice": voice
        })
        
        # Parse JSON result
        import json
        response = json.loads(result[0].text)
        
        # Verify response
        assert response["success"] is True
        assert response["voice"] == voice
        
        # Verify mock was called correctly
        mock_audio_core.speak_text.assert_called_once_with(text, voice, None, None)
    
    @pytest.mark.asyncio
    async def test_km_text_to_speech_with_rate(self, audio_mcp_server, mock_audio_core):
        """Test text-to-speech with rate parameter."""
        text = "Hello, world!"
        rate = 180
        
        result = await audio_mcp_server.call_tool("km_text_to_speech", {
            "text": text,
            "rate": rate
        })
        
        # Parse JSON result
        import json
        response = json.loads(result[0].text)
        
        # Verify response
        assert response["success"] is True
        assert response["rate"] == rate
        
        # Verify mock was called correctly
        mock_audio_core.speak_text.assert_called_once_with(text, None, rate, None)
    
    @pytest.mark.asyncio
    async def test_km_text_to_speech_with_save_to_file(self, audio_mcp_server, mock_audio_core):
        """Test text-to-speech with save_to_file parameter."""
        text = "Hello, world!"
        save_to_file = "/path/to/output.aiff"
        
        result = await audio_mcp_server.call_tool("km_text_to_speech", {
            "text": text,
            "save_to_file": save_to_file
        })
        
        # Parse JSON result
        import json
        response = json.loads(result[0].text)
        
        # Verify response
        assert response["success"] is True
        assert response["file_path"] == save_to_file
        
        # Verify mock was called correctly
        mock_audio_core.speak_text.assert_called_once_with(text, None, None, save_to_file)
    
    @pytest.mark.asyncio
    async def test_km_text_to_speech_invalid_rate(self, audio_mcp_server):
        """Test text-to-speech with invalid rate parameter."""
        text = "Hello, world!"
        rate = 1000  # Invalid rate
        
        result = await audio_mcp_server.call_tool("km_text_to_speech", {
            "text": text,
            "rate": rate
        })
        
        # Parse JSON result
        import json
        response = json.loads(result[0].text)
        
        # Verify response
        assert response["success"] is False
        assert "error" in response
        assert "error_code" in response
    
    @pytest.mark.asyncio
    async def test_km_list_speech_voices(self, audio_mcp_server, mock_audio_core):
        """Test listing available voices."""
        result = await audio_mcp_server.call_tool("km_list_speech_voices", {})
        
        # Parse JSON result
        import json
        response = json.loads(result[0].text)
        
        # Verify response
        assert response["success"] is True
        assert "voices" in response
        assert len(response["voices"]) == 4  # From mock response
        assert "count" in response
        assert response["count"] == 4
        
        # Verify mock was called correctly
        mock_audio_core.list_available_voices.assert_called_once()
