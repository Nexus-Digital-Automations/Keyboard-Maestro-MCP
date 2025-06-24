# MCP Context Manager: Keyboard Maestro MCP Server
# src/core/context_manager.py

"""
MCP context handling and session management.

This module implements the MCPContextManager class that handles MCP context
objects, session state, progress reporting, and resource access with
comprehensive tracking and lifecycle management.

Features:
- MCP context creation and lifecycle management
- Session state tracking and isolation
- Progress reporting and status updates
- Resource access coordination
- Context-aware logging and monitoring

Size: 197 lines (target: <200)
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import time
import uuid

from fastmcp import Context

from .utils.configuration import ServerConfiguration
from src.core.km_interface import KeyboardMaestroInterface
from src.contracts.decorators import requires, ensures
from src.types.domain_types import SessionStatus, ContextInfo


@dataclass
class SessionInfo:
    """Information about an active MCP session."""
    session_id: str
    client_id: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    status: SessionStatus = SessionStatus.ACTIVE
    context_count: int = 0
    total_requests: int = 0
    
    @property
    def duration_seconds(self) -> float:
        """Session duration in seconds."""
        return time.time() - self.created_at
    
    @property
    def idle_seconds(self) -> float:
        """Seconds since last activity."""
        return time.time() - self.last_activity


class MCPContextManager:
    """Manager for MCP contexts and session state."""
    
    def __init__(self, 
                 config: ServerConfiguration,
                 km_interface: KeyboardMaestroInterface):
        """Initialize context manager.
        
        Args:
            config: Server configuration
            km_interface: Keyboard Maestro interface
        """
        self._config = config
        self._km_interface = km_interface
        self._logger = logging.getLogger(__name__)
        
        # Session and context tracking
        self._sessions: Dict[str, SessionInfo] = {}
        self._active_contexts: Dict[str, ContextInfo] = {}
        self._context_cleanup_interval = 300  # 5 minutes
        self._session_timeout = 3600  # 1 hour
        
        # Background cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
    
    @property
    def active_session_count(self) -> int:
        """Number of active sessions."""
        return len([s for s in self._sessions.values() if s.status == SessionStatus.ACTIVE])
    
    @property
    def active_context_count(self) -> int:
        """Number of active contexts."""
        return len(self._active_contexts)
    
    async def initialize(self) -> None:
        """Initialize context manager and start background tasks."""
        try:
            self._logger.info("Initializing MCP context manager...")
            
            # Start background cleanup task
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            
            self._logger.debug("Context manager initialized")
            
        except Exception as e:
            self._logger.error(f"Context manager initialization failed: {e}")
            raise
    
    async def create_session(self, client_id: Optional[str] = None) -> str:
        """Create a new MCP session.
        
        Args:
            client_id: Optional client identifier
            
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        
        session_info = SessionInfo(
            session_id=session_id,
            client_id=client_id
        )
        
        self._sessions[session_id] = session_info
        self._logger.debug(f"Created session {session_id} for client {client_id}")
        
        return session_id
    
    @requires(lambda session_id: session_id is not None)
    async def create_context(self, session_id: str) -> ContextInfo:
        """Create MCP context for a session.
        
        Preconditions:
        - Session ID must be provided
        
        Args:
            session_id: Session ID to create context for
            
        Returns:
            Context information object
        """
        # Verify session exists and is active
        if session_id not in self._sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self._sessions[session_id]
        if session.status != SessionStatus.ACTIVE:
            raise ValueError(f"Session {session_id} is not active")
        
        # Create context info
        context_id = f"{session_id}_{uuid.uuid4().hex[:8]}"
        context_info = ContextInfo(
            context_id=context_id,
            session_id=session_id,
            created_at=time.time()
        )
        
        # Track context
        self._active_contexts[context_id] = context_info
        session.context_count += 1
        session.last_activity = time.time()
        
        self._logger.debug(f"Created context {context_id} for session {session_id}")
        return context_info
    
    async def handle_context_logging(self, 
                                   context_id: str,
                                   level: str,
                                   message: str) -> None:
        """Handle context-aware logging messages.
        
        Args:
            context_id: Context identifier
            level: Log level (info, warning, error, debug)
            message: Log message
        """
        if context_id not in self._active_contexts:
            self._logger.warning(f"Logging from unknown context: {context_id}")
            return
        
        context_info = self._active_contexts[context_id]
        
        # Log with context information
        log_message = f"[Context:{context_id[:8]}] {message}"
        
        if level.lower() == 'debug':
            self._logger.debug(log_message)
        elif level.lower() == 'info':
            self._logger.info(log_message)
        elif level.lower() == 'warning':
            self._logger.warning(log_message)
        elif level.lower() == 'error':
            self._logger.error(log_message)
        else:
            self._logger.info(log_message)
        
        # Update context activity
        context_info.last_activity = time.time()
    
    async def handle_progress_report(self,
                                   context_id: str,
                                   progress: int,
                                   total: int,
                                   message: Optional[str] = None) -> None:
        """Handle progress reporting from tools.
        
        Args:
            context_id: Context identifier
            progress: Current progress value
            total: Total progress value
            message: Optional progress message
        """
        if context_id not in self._active_contexts:
            self._logger.warning(f"Progress from unknown context: {context_id}")
            return
        
        context_info = self._active_contexts[context_id]
        
        # Update context progress
        context_info.current_progress = progress
        context_info.total_progress = total
        context_info.last_activity = time.time()
        
        # Log progress update
        progress_pct = (progress / total * 100) if total > 0 else 0
        log_msg = f"Progress {progress_pct:.1f}%"
        if message:
            log_msg += f": {message}"
        
        await self.handle_context_logging(context_id, 'info', log_msg)
    
    async def cleanup_context(self, context_id: str) -> None:
        """Clean up a specific context.
        
        Args:
            context_id: Context ID to cleanup
        """
        if context_id not in self._active_contexts:
            return
        
        context_info = self._active_contexts[context_id]
        
        # Update session stats
        if context_info.session_id in self._sessions:
            session = self._sessions[context_info.session_id]
            session.total_requests += context_info.request_count
        
        # Remove context
        del self._active_contexts[context_id]
        self._logger.debug(f"Cleaned up context {context_id}")
    
    async def cleanup_session(self, session_id: str) -> None:
        """Clean up a session and all its contexts.
        
        Args:
            session_id: Session ID to cleanup
        """
        if session_id not in self._sessions:
            return
        
        # Clean up all contexts for this session
        contexts_to_cleanup = [
            ctx_id for ctx_id, ctx_info in self._active_contexts.items()
            if ctx_info.session_id == session_id
        ]
        
        for context_id in contexts_to_cleanup:
            await self.cleanup_context(context_id)
        
        # Mark session as ended
        session = self._sessions[session_id]
        session.status = SessionStatus.ENDED
        
        self._logger.debug(f"Cleaned up session {session_id}")
    
    async def _cleanup_loop(self) -> None:
        """Background cleanup loop for expired contexts and sessions."""
        while True:
            try:
                await asyncio.sleep(self._context_cleanup_interval)
                await self._cleanup_expired_items()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Error in cleanup loop: {e}")
    
    async def _cleanup_expired_items(self) -> None:
        """Clean up expired contexts and sessions."""
        current_time = time.time()
        
        # Clean up expired contexts (no activity for 1 hour)
        expired_contexts = [
            ctx_id for ctx_id, ctx_info in self._active_contexts.items()
            if current_time - ctx_info.last_activity > 3600
        ]
        
        for context_id in expired_contexts:
            await self.cleanup_context(context_id)
        
        # Clean up expired sessions
        expired_sessions = [
            session_id for session_id, session in self._sessions.items()
            if (session.status == SessionStatus.ACTIVE and 
                current_time - session.last_activity > self._session_timeout)
        ]
        
        for session_id in expired_sessions:
            await self.cleanup_session(session_id)
        
        if expired_contexts or expired_sessions:
            self._logger.debug(f"Cleaned up {len(expired_contexts)} contexts, "
                             f"{len(expired_sessions)} sessions")
    
    def get_audio_core(self) -> 'AudioCore':
        """Get AudioCore instance.
        
        Returns:
            AudioCore instance for audio operations
        """
        from src.core.audio_core import AudioCore
        return AudioCore(self._km_interface)
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get context manager statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            'active_sessions': self.active_session_count,
            'active_contexts': self.active_context_count,
            'total_sessions': len(self._sessions),
            'session_details': [
                {
                    'session_id': session.session_id,
                    'client_id': session.client_id,
                    'duration_seconds': session.duration_seconds,
                    'idle_seconds': session.idle_seconds,
                    'status': session.status.value,
                    'context_count': session.context_count,
                    'total_requests': session.total_requests
                }
                for session in self._sessions.values()
            ]
        }
    
    async def shutdown(self) -> None:
        """Shutdown context manager and cleanup all resources."""
        try:
            self._logger.info("Shutting down context manager...")
            
            # Cancel cleanup task
            if self._cleanup_task:
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass
            
            # Clean up all active sessions
            for session_id in list(self._sessions.keys()):
                await self.cleanup_session(session_id)
            
            self._logger.debug("Context manager shutdown complete")
            
        except Exception as e:
            self._logger.error(f"Error during context manager shutdown: {e}")


# Global instance for convenience functions
_context_manager = None


def initialize_context_manager(config: ServerConfiguration, km_interface: KeyboardMaestroInterface) -> MCPContextManager:
    """Initialize the global context manager.
    
    Args:
        config: Server configuration
        km_interface: Keyboard Maestro interface
        
    Returns:
        Initialized context manager instance
    """
    global _context_manager
    _context_manager = MCPContextManager(config, km_interface)
    return _context_manager


def get_km_interface() -> KeyboardMaestroInterface:
    """Get KM interface instance from global context manager.
    
    Returns:
        Keyboard Maestro interface instance
    """
    global _context_manager
    if _context_manager is None:
        raise RuntimeError("Context manager not initialized")
    return _context_manager._km_interface


def get_audio_core() -> 'AudioCore':
    """Get AudioCore instance from global context manager.
    
    Returns:
        AudioCore instance for audio operations
    """
    global _context_manager
    if _context_manager is None:
        raise RuntimeError("Context manager not initialized")
    return _context_manager.get_audio_core()


def get_communication_core() -> 'CommunicationCore':
    """Get CommunicationCore instance from global context manager.
    
    Returns:
        CommunicationCore instance for communication operations
    """
    global _context_manager
    if _context_manager is None:
        raise RuntimeError("Context manager not initialized")
    # This would normally be part of the context manager
    from src.core.communication_core import CommunicationCore
    return CommunicationCore(get_km_interface())
