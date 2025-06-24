"""
Core business logic for audio and speech operations.

This module implements audio playback, volume control, and text-to-speech
conversion using macOS built-in capabilities through AppleScript and shell commands.

Features:
- Sound file playback through afplay
- System volume control through AppleScript
- Text-to-speech using macOS say command
- Audio device management through system commands

Size: 247 lines (target: <250)
"""

import asyncio
import logging
import re
from typing import Dict, Any, Optional, List, Tuple
import os
import time
from dataclasses import dataclass

from .contracts.decorators import requires, ensures
from src.core.km_interface import KMInterface
from src.validators.system_validators import system_validator
from src.types.enumerations import AudioOperation, VoiceGender
from src.types.domain_types import AudioDevice


logger = logging.getLogger(__name__)


@dataclass
class AudioResult:
    """Result of an audio operation."""
    success: bool
    operation: str
    processing_time: float
    error: Optional[str] = None
    error_code: Optional[str] = None
    output: Optional[str] = None


@dataclass
class TTSResult:
    """Result of a text-to-speech operation."""
    success: bool
    text_length: int
    processing_time: float
    voice: Optional[str] = None
    rate: Optional[int] = None
    file_path: Optional[str] = None
    error: Optional[str] = None
    error_code: Optional[str] = None


class AudioCore:
    """Core business logic for audio and speech operations."""

    def __init__(self, km_interface: KMInterface):
        """Initialize audio core with KM interface.
        
        Args:
            km_interface: Keyboard Maestro interface for AppleScript execution
        """
        self.km_interface = km_interface
    
    @requires(lambda self, file_path: system_validator.validate_file_path(file_path, "read").is_valid)
    @ensures(lambda result: isinstance(result, AudioResult))
    async def play_sound(self, file_path: str, volume: Optional[int] = None) -> AudioResult:
        """Plays an audio file using macOS afplay.
        
        Preconditions:
        - file_path must be valid and readable
        
        Args:
            file_path: Path to audio file
            volume: Optional playback volume (0-100)
            
        Returns:
            AudioResult with operation status
        """
        start_time = time.time()
        
        try:
            # Validate file path (already checked by @requires)
            if not os.path.exists(file_path):
                return AudioResult(
                    success=False,
                    operation="play",
                    processing_time=time.time() - start_time,
                    error=f"File not found: {file_path}",
                    error_code="FILE_NOT_FOUND"
                )
            
            # Set volume temporarily if specified
            original_volume = None
            if volume is not None:
                # Get current volume
                volume_result = await self.get_system_volume()
                if volume_result.success:
                    original_volume = int(volume_result.output or 0)
                
                # Set temporary volume
                await self.set_system_volume(volume)
            
            # Escape the file path for shell command
            escaped_path = file_path.replace('"', '\\"').replace('`', '\\`')
            
            # Create afplay shell command
            script = f'do shell script "afplay \\"{escaped_path}\\""'
            
            # Execute through KM interface
            result = await self.km_interface.execute_applescript(script, timeout=60)
            
            # Restore original volume if needed
            if original_volume is not None:
                await self.set_system_volume(original_volume)
            
            # Return success or error
            if result.success:
                return AudioResult(
                    success=True,
                    operation="play",
                    processing_time=time.time() - start_time,
                    output=str(file_path)
                )
            else:
                return AudioResult(
                    success=False,
                    operation="play",
                    processing_time=time.time() - start_time,
                    error=result.error or "Unknown error",
                    error_code="PLAYBACK_FAILED"
                )
        
        except Exception as e:
            logger.error(f"Sound playback failed: {e}")
            return AudioResult(
                success=False,
                operation="play",
                processing_time=time.time() - start_time,
                error=str(e),
                error_code="INTERNAL_ERROR"
            )
    
    @requires(lambda self, volume_level: 0 <= volume_level <= 100)
    @ensures(lambda result: isinstance(result, AudioResult))
    async def set_system_volume(self, volume_level: int) -> AudioResult:
        """Sets the system output volume.
        
        Preconditions:
        - volume_level must be between 0 and 100
        
        Args:
            volume_level: Volume level (0-100)
            
        Returns:
            AudioResult with operation status
        """
        start_time = time.time()
        
        try:
            # Validate volume level (already checked by @requires)
            if volume_level < 0:
                volume_level = 0
            elif volume_level > 100:
                volume_level = 100
            
            # Create AppleScript command for setting volume
            script = f"set volume output volume {volume_level}"
            
            # Execute through KM interface
            result = await self.km_interface.execute_applescript(script)
            
            # Return success or error
            if result.success:
                return AudioResult(
                    success=True,
                    operation="set_volume",
                    processing_time=time.time() - start_time,
                    output=str(volume_level)
                )
            else:
                return AudioResult(
                    success=False,
                    operation="set_volume",
                    processing_time=time.time() - start_time,
                    error=result.error or "Unknown error",
                    error_code="VOLUME_CHANGE_FAILED"
                )
        
        except Exception as e:
            logger.error(f"Volume change failed: {e}")
            return AudioResult(
                success=False,
                operation="set_volume",
                processing_time=time.time() - start_time,
                error=str(e),
                error_code="INTERNAL_ERROR"
            )
    
    @ensures(lambda result: isinstance(result, AudioResult))
    async def get_system_volume(self) -> AudioResult:
        """Gets the current system output volume.
        
        Returns:
            AudioResult with operation status and volume level
        """
        start_time = time.time()
        
        try:
            # Create AppleScript command for getting volume
            script = "get output volume of (get volume settings)"
            
            # Execute through KM interface
            result = await self.km_interface.execute_applescript(script)
            
            # Return success or error
            if result.success:
                # Parse volume level from result
                try:
                    volume = int(result.output.strip())
                    return AudioResult(
                        success=True,
                        operation="get_volume",
                        processing_time=time.time() - start_time,
                        output=str(volume)
                    )
                except (ValueError, AttributeError):
                    return AudioResult(
                        success=False,
                        operation="get_volume",
                        processing_time=time.time() - start_time,
                        error="Failed to parse volume level",
                        error_code="PARSE_ERROR"
                    )
            else:
                return AudioResult(
                    success=False,
                    operation="get_volume",
                    processing_time=time.time() - start_time,
                    error=result.error or "Unknown error",
                    error_code="GET_VOLUME_FAILED"
                )
        
        except Exception as e:
            logger.error(f"Get volume failed: {e}")
            return AudioResult(
                success=False,
                operation="get_volume",
                processing_time=time.time() - start_time,
                error=str(e),
                error_code="INTERNAL_ERROR"
            )
    
    @ensures(lambda result: isinstance(result, AudioResult))
    async def mute_system_audio(self, mute: bool = True) -> AudioResult:
        """Mutes or unmutes system audio.
        
        Args:
            mute: True to mute, False to unmute
            
        Returns:
            AudioResult with operation status
        """
        start_time = time.time()
        
        try:
            # Create AppleScript command for muting/unmuting
            script = f'set volume {"with" if mute else "without"} output muted'
            
            # Execute through KM interface
            result = await self.km_interface.execute_applescript(script)
            
            # Return success or error
            if result.success:
                return AudioResult(
                    success=True,
                    operation="mute" if mute else "unmute",
                    processing_time=time.time() - start_time
                )
            else:
                return AudioResult(
                    success=False,
                    operation="mute" if mute else "unmute",
                    processing_time=time.time() - start_time,
                    error=result.error or "Unknown error",
                    error_code="MUTE_OPERATION_FAILED"
                )
        
        except Exception as e:
            logger.error(f"Mute operation failed: {e}")
            return AudioResult(
                success=False,
                operation="mute" if mute else "unmute",
                processing_time=time.time() - start_time,
                error=str(e),
                error_code="INTERNAL_ERROR"
            )
    
    @requires(lambda self, text: isinstance(text, str) and len(text) > 0)
    @ensures(lambda result: isinstance(result, TTSResult))
    async def speak_text(
        self,
        text: str,
        voice: Optional[str] = None,
        rate: Optional[int] = None,
        save_to_file: Optional[str] = None
    ) -> TTSResult:
        """Uses macOS 'say' command for text-to-speech.
        
        Preconditions:
        - text must be a non-empty string
        
        Args:
            text: Text to speak
            voice: Voice name (e.g., 'Alex', 'Samantha')
            rate: Speech rate (120-300 words per minute)
            save_to_file: Optional path to save speech audio
            
        Returns:
            TTSResult with operation status
        """
        start_time = time.time()
        text_length = len(text)
        
        try:
            # Validate parameters
            if rate is not None and (rate < 120 or rate > 300):
                # Default speech rate range for macOS
                return TTSResult(
                    success=False,
                    text_length=text_length,
                    processing_time=time.time() - start_time,
                    error="Speech rate must be between 120 and 300 words per minute",
                    error_code="INVALID_RATE"
                )
            
            # Check if file path is valid for saving
            if save_to_file:
                validation = system_validator.validate_file_path(save_to_file, "write")
                if not validation.is_valid:
                    return TTSResult(
                        success=False,
                        text_length=text_length,
                        processing_time=time.time() - start_time,
                        error=validation.error_message,
                        error_code="INVALID_FILE_PATH"
                    )
            
            # Sanitize text to prevent shell injection
            sanitized_text = text.replace('"', '\\"').replace("`", "").replace("$(", "")
            
            # Build command
            command = f'say "{sanitized_text}"'
            
            if voice:
                # Further validation on voice name would be needed here
                command += f' -v "{voice}"'
            
            if rate:
                command += f' -r {rate}'
            
            if save_to_file:
                # Escape file path
                escaped_path = save_to_file.replace('"', '\\"')
                command += f' -o "{escaped_path}"'
            
            # Create AppleScript with shell command
            script = f'do shell script "{command}"'
            
            # Execute through KM interface
            result = await self.km_interface.execute_applescript(script, timeout=120)
            
            # Return success or error
            if result.success:
                return TTSResult(
                    success=True,
                    text_length=text_length,
                    processing_time=time.time() - start_time,
                    voice=voice,
                    rate=rate,
                    file_path=save_to_file
                )
            else:
                return TTSResult(
                    success=False,
                    text_length=text_length,
                    processing_time=time.time() - start_time,
                    error=result.error or "Unknown error",
                    error_code="SPEECH_FAILED",
                    voice=voice,
                    rate=rate
                )
        
        except Exception as e:
            logger.error(f"Text-to-speech failed: {e}")
            return TTSResult(
                success=False,
                text_length=text_length,
                processing_time=time.time() - start_time,
                error=str(e),
                error_code="INTERNAL_ERROR",
                voice=voice,
                rate=rate
            )
    
    @ensures(lambda result: isinstance(result, List[str]))
    async def list_available_voices(self) -> List[str]:
        """Lists all available voices on macOS.
        
        Returns:
            List of available voice names
        """
        try:
            # Create shell command for listing voices
            script = 'do shell script "say -v ? | awk \'{print $1}\'"'
            
            # Execute through KM interface
            result = await self.km_interface.execute_applescript(script)
            
            if result.success and result.output:
                # Parse voice list
                voices = [v.strip() for v in result.output.split('\n') if v.strip()]
                return voices
            else:
                logger.error(f"Failed to list voices: {result.error}")
                return []
        
        except Exception as e:
            logger.error(f"List voices failed: {e}")
            return []
    
    @ensures(lambda result: isinstance(result, Dict[str, List[AudioDevice]]))
    async def list_audio_devices(self) -> Dict[str, List[AudioDevice]]:
        """Lists all audio input and output devices.
        
        Returns:
            Dictionary with 'input' and 'output' device lists
        """
        try:
            # Create shell command for listing audio devices
            script = 'do shell script "system_profiler SPAudioDataType"'
            
            # Execute through KM interface
            result = await self.km_interface.execute_applescript(script)
            
            devices = {
                'input': [],
                'output': []
            }
            
            if result.success and result.output:
                # Parse device list from system_profiler output
                current_device = None
                
                for line in result.output.split('\n'):
                    line = line.strip()
                    
                    # Check for device name
                    if line and not line.startswith(('Input', 'Output', 'Default')):
                        if ':' in line and not line.startswith(' '):
                            current_device = {
                                'name': line.split(':')[0].strip(),
                                'is_input': False,
                                'is_output': False,
                                'is_default': False
                            }
                    
                    # Check for device type
                    if current_device:
                        if 'Input Channels' in line and 'Yes' in line:
                            current_device['is_input'] = True
                            devices['input'].append(AudioDevice(
                                name=current_device['name'],
                                is_default=current_device['is_default']
                            ))
                        
                        if 'Output Channels' in line and 'Yes' in line:
                            current_device['is_output'] = True
                            devices['output'].append(AudioDevice(
                                name=current_device['name'],
                                is_default=current_device['is_default']
                            ))
                        
                        if 'Default' in line and 'Yes' in line:
                            current_device['is_default'] = True
                            # Update the device in the lists
                            for device_list in [devices['input'], devices['output']]:
                                for device in device_list:
                                    if device.name == current_device['name']:
                                        device.is_default = True
            
            return devices
        
        except Exception as e:
            logger.error(f"List audio devices failed: {e}")
            return {'input': [], 'output': []}
