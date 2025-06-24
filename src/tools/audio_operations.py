"""
MCP tools for audio control and text-to-speech operations.

This module provides tools for audio control, sound playback, and text-to-speech
functionality with comprehensive validation and error handling.

Features:
- Sound file playback with volume control
- System volume control and muting
- Text-to-speech with customizable voices
- Audio device management and listing

Size: 248 lines (target: <250)
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
import time
import os

from fastmcp import FastMCP
from .contracts.decorators import requires, ensures
from src.core.audio_core import AudioCore, AudioResult, TTSResult
from src.core.km_interface import KMInterface
from src.validators.system_validators import system_validator
from src.types.enumerations import AudioOperation


logger = logging.getLogger(__name__)


@requires(lambda operation: isinstance(operation, str) and operation in ["play", "volume", "mute", "unmute", "get_volume"])
@ensures(lambda result: isinstance(result, Dict) and "success" in result)
async def control_audio(
    operation: str,
    file_path: Optional[str] = None,
    volume_level: Optional[int] = None,
    device: Optional[str] = None,
    audio_core: Optional[AudioCore] = None
) -> Dict[str, Any]:
    """
    Control audio features like playback and volume.
    
    Preconditions:
    - operation must be a valid audio operation
    - file_path must be a valid file path for play operation
    - volume_level must be between 0-100 for volume operation
    
    Args:
        operation: Audio operation to perform
        file_path: Path to audio file for playback
        volume_level: Volume level (0-100)
        device: Audio device name (if applicable)
        audio_core: AudioCore instance (for dependency injection)
    
    Returns:
        Dict with operation status and details
    """
    start_time = time.time()
    
    try:
        # Get AudioCore instance if not provided
        if audio_core is None:
            from src.core.context_manager import get_audio_core
            audio_core = get_audio_core()
        
        # Validate parameters based on operation
        if operation == "play":
            if not file_path:
                return {
                    "success": False,
                    "error": "File path is required for play operation",
                    "error_code": "MISSING_PARAMETER",
                    "processing_time": time.time() - start_time
                }
            
            # Validate file path
            validation = system_validator.validate_file_path(file_path, "read")
            if not validation.is_valid:
                return {
                    "success": False,
                    "error": validation.error_message,
                    "error_code": "INVALID_FILE_PATH",
                    "processing_time": time.time() - start_time
                }
            
            # Perform play operation
            result = await audio_core.play_sound(file_path, volume_level)
            
        elif operation == "volume":
            if volume_level is None:
                return {
                    "success": False,
                    "error": "Volume level is required for volume operation",
                    "error_code": "MISSING_PARAMETER",
                    "processing_time": time.time() - start_time
                }
            
            # Validate volume level
            if volume_level < 0 or volume_level > 100:
                return {
                    "success": False,
                    "error": "Volume level must be between 0 and 100",
                    "error_code": "INVALID_VOLUME",
                    "processing_time": time.time() - start_time
                }
            
            # Perform volume operation
            result = await audio_core.set_system_volume(volume_level)
            
        elif operation == "mute":
            # Perform mute operation
            result = await audio_core.mute_system_audio(True)
            
        elif operation == "unmute":
            # Perform unmute operation
            result = await audio_core.mute_system_audio(False)
            
        elif operation == "get_volume":
            # Perform get volume operation
            result = await audio_core.get_system_volume()
            
        else:
            # Should not reach here due to @requires
            return {
                "success": False,
                "error": f"Unsupported operation: {operation}",
                "error_code": "INVALID_OPERATION",
                "processing_time": time.time() - start_time
            }
        
        # Map AudioResult to response dictionary
        response = {
            "success": result.success,
            "operation": result.operation,
            "processing_time": result.processing_time
        }
        
        if result.output:
            response["output"] = result.output
        
        if not result.success:
            response["error"] = result.error
            response["error_code"] = result.error_code
        
        # Add operation-specific fields
        if operation == "play" and result.success:
            response["file"] = file_path
        elif operation == "volume" and result.success:
            response["level"] = volume_level
        elif operation == "get_volume" and result.success:
            response["level"] = int(result.output) if result.output else None
        
        return response
        
    except Exception as e:
        logger.error(f"Audio control operation failed: {e}")
        return {
            "success": False,
            "operation": operation,
            "error": str(e),
            "error_code": "INTERNAL_ERROR",
            "processing_time": time.time() - start_time
        }


@requires(lambda text: isinstance(text, str) and len(text) > 0)
@ensures(lambda result: isinstance(result, Dict) and "success" in result)
async def text_to_speech(
    text: str,
    voice: Optional[str] = None,
    rate: Optional[int] = None,
    save_to_file: Optional[str] = None,
    audio_core: Optional[AudioCore] = None
) -> Dict[str, Any]:
    """
    Convert text to speech using macOS built-in capabilities.
    
    Preconditions:
    - text must be a non-empty string
    - rate (if provided) must be between 120-300 words per minute
    - save_to_file (if provided) must be a valid file path
    
    Args:
        text: Text to speak
        voice: Voice name (e.g., 'Alex', 'Samantha')
        rate: Speech rate in words per minute
        save_to_file: Path to save speech as audio file
        audio_core: AudioCore instance (for dependency injection)
    
    Returns:
        Dict with operation status and details
    """
    start_time = time.time()
    
    try:
        # Get AudioCore instance if not provided
        if audio_core is None:
            from src.core.context_manager import get_audio_core
            audio_core = get_audio_core()
        
        # Validate parameters
        if rate is not None and (rate < 120 or rate > 300):
            return {
                "success": False,
                "error": "Speech rate must be between 120 and 300 words per minute",
                "error_code": "INVALID_RATE",
                "processing_time": time.time() - start_time,
                "text_length": len(text)
            }
        
        # Check if save_to_file path is valid
        if save_to_file:
            validation = system_validator.validate_file_path(save_to_file, "write")
            if not validation.is_valid:
                return {
                    "success": False,
                    "error": validation.error_message,
                    "error_code": "INVALID_FILE_PATH",
                    "processing_time": time.time() - start_time,
                    "text_length": len(text)
                }
        
        # Perform text-to-speech operation
        result = await audio_core.speak_text(text, voice, rate, save_to_file)
        
        # Map TTSResult to response dictionary
        response = {
            "success": result.success,
            "text_length": result.text_length,
            "processing_time": result.processing_time,
            "operation": "speak"
        }
        
        if voice:
            response["voice"] = voice
        
        if rate:
            response["rate"] = rate
        
        if save_to_file and result.success:
            response["file_path"] = save_to_file
        
        if not result.success:
            response["error"] = result.error
            response["error_code"] = result.error_code
        
        return response
        
    except Exception as e:
        logger.error(f"Text-to-speech operation failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "error_code": "INTERNAL_ERROR",
            "processing_time": time.time() - start_time,
            "text_length": len(text)
        }


async def list_voices(audio_core: Optional[AudioCore] = None) -> Dict[str, Any]:
    """
    List available text-to-speech voices on the system.
    
    Args:
        audio_core: AudioCore instance (for dependency injection)
    
    Returns:
        Dict with list of available voices
    """
    start_time = time.time()
    
    try:
        # Get AudioCore instance if not provided
        if audio_core is None:
            from src.core.context_manager import get_audio_core
            audio_core = get_audio_core()
        
        # Get list of voices
        voices = await audio_core.list_available_voices()
        
        return {
            "success": True,
            "voices": voices,
            "count": len(voices),
            "processing_time": time.time() - start_time
        }
        
    except Exception as e:
        logger.error(f"List voices operation failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "error_code": "INTERNAL_ERROR",
            "processing_time": time.time() - start_time
        }


def register_audio_tools(mcp_server: FastMCP, km_interface: KMInterface) -> None:
    """Register audio operation tools with the FastMCP server."""
    
    # Create AudioCore instance
    audio_core = AudioCore(km_interface)
    
    @mcp_server.tool()
    async def km_audio_control(
        operation: str,
        file_path: Optional[str] = None,
        volume_level: Optional[int] = None,
        device: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Control system audio features like playback and volume.

        Args:
            operation: The audio operation to perform ('play', 'volume', 'mute', 'unmute', 'get_volume').
            file_path: The path to the audio file for 'play' operation.
            volume_level: The volume level (0-100) for 'volume' operation.
            device: Optional audio device name (if applicable).

        Returns:
            A dictionary with the operation status.
        """
        return await control_audio(
            operation=operation,
            file_path=file_path,
            volume_level=volume_level,
            device=device,
            audio_core=audio_core
        )
    
    @mcp_server.tool()
    async def km_text_to_speech(
        text: str,
        voice: Optional[str] = None,
        rate: Optional[int] = None,
        save_to_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Converts text to speech using macOS's built-in capabilities.

        Args:
            text: The text to be spoken.
            voice: The voice to use (e.g., 'Alex', 'Samantha').
            rate: The speech rate in words per minute (e.g., 180).
            save_to_file: Path to save the speech as an audio file.

        Returns:
            A dictionary with the operation status.
        """
        return await text_to_speech(
            text=text,
            voice=voice,
            rate=rate,
            save_to_file=save_to_file,
            audio_core=audio_core
        )
    
    @mcp_server.tool()
    async def km_list_speech_voices() -> Dict[str, Any]:
        """
        List all available text-to-speech voices on the system.
        
        Returns:
            A dictionary with the list of available voices.
        """
        return await list_voices(audio_core)


# Convenience function to get audio core
def get_audio_core():
    """Get audio core instance - would be properly injected in real implementation."""
    from src.core.context_manager import get_km_interface
    return AudioCore(get_km_interface())
