"""File operations MCP tools with defensive programming and comprehensive validation.

This module provides MCP tools for file system operations including copy, move, delete,
and directory management with security boundaries and error recovery.
"""

from typing import Dict, List, Optional, Any
from fastmcp import FastMCP, Context
from pathlib import Path
import asyncio

from src.contracts.decorators import requires, ensures
from src.contracts.exceptions import ValidationError, PermissionDeniedError
from src.core.system_operations import system_manager, OperationStatus
from src.validators.system_validators import system_validator
from src.boundaries.permission_checker import permission_checker, PermissionType


class FileOperationTools:
    """MCP tools for file system operations with defensive programming."""
    
    def __init__(self, mcp_server: FastMCP):
        self.mcp = mcp_server
        self._register_tools()
    
    def _register_tools(self):
        """Register all file operation MCP tools."""
        self.mcp.tool()(self.copy_file)
        self.mcp.tool()(self.move_file)
        self.mcp.tool()(self.delete_file)
        self.mcp.tool()(self.create_directory)
        self.mcp.tool()(self.list_directory)
        self.mcp.tool()(self.get_file_info)
        self.mcp.tool()(self.check_file_exists)
    
    @requires(lambda source_path: isinstance(source_path, str) and len(source_path.strip()) > 0)
    @requires(lambda destination_path: isinstance(destination_path, str) and len(destination_path.strip()) > 0)
    async def copy_file(
        self,
        source_path: str,
        destination_path: str,
        overwrite: bool = False,
        create_directories: bool = True,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """Copy a file from source to destination with comprehensive validation.
        
        Args:
            source_path: Path to source file
            destination_path: Path to destination file
            overwrite: Whether to overwrite existing destination
            create_directories: Whether to create missing parent directories
            ctx: MCP context for logging and progress
            
        Returns:
            Dict with operation result and details
        """
        try:
            if ctx:
                await ctx.info(f"Starting file copy: {source_path} -> {destination_path}")
            
            # Pre-operation validation
            validation_errors = []
            
            # Validate source path
            source_validation = system_validator.validate_file_path(source_path, "read")
            if not source_validation.is_valid:
                validation_errors.append(f"Source: {source_validation.error_message}")
            
            # Validate destination path
            dest_validation = system_validator.validate_file_path(destination_path, "write")
            if not dest_validation.is_valid:
                validation_errors.append(f"Destination: {dest_validation.error_message}")
            
            if validation_errors:
                error_msg = "Validation failed: " + "; ".join(validation_errors)
                if ctx:
                    await ctx.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "error_type": "validation_error",
                    "recovery_suggestions": [
                        "Check file paths are correct and accessible",
                        "Verify permissions for source and destination"
                    ]
                }
            
            # Create parent directories if requested
            if create_directories:
                dest_parent = Path(destination_path).parent
                if not dest_parent.exists():
                    try:
                        dest_parent.mkdir(parents=True, exist_ok=True)
                        if ctx:
                            await ctx.info(f"Created parent directories: {dest_parent}")
                    except Exception as e:
                        if ctx:
                            await ctx.error(f"Failed to create directories: {str(e)}")
                        return {
                            "success": False,
                            "error": f"Directory creation failed: {str(e)}",
                            "error_type": "filesystem_error"
                        }
            
            # Report progress
            if ctx:
                await ctx.report_progress(25, 100, "Validation complete, starting copy")
            
            # Perform copy operation
            result = await system_manager.copy_file(source_path, destination_path, overwrite)
            
            if ctx:
                await ctx.report_progress(100, 100, "File copy complete")
            
            if result.status == OperationStatus.SUCCESS:
                if ctx:
                    await ctx.info(f"File copied successfully in {result.execution_time:.2f}s")
                
                return {
                    "success": True,
                    "message": result.message,
                    "source_path": source_path,
                    "destination_path": destination_path,
                    "execution_time": result.execution_time,
                    "data": result.data
                }
            else:
                if ctx:
                    await ctx.error(f"File copy failed: {result.message}")
                
                return {
                    "success": False,
                    "error": result.message,
                    "error_type": result.status.value,
                    "execution_time": result.execution_time,
                    "recovery_actions": [action.name for action in result.recovery_actions],
                    "error_details": result.error_details
                }
                
        except Exception as e:
            error_msg = f"Unexpected error in file copy: {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "error_type": "unexpected_error",
                "recovery_suggestions": ["Retry operation", "Check system logs"]
            }
    
    @requires(lambda source_path: isinstance(source_path, str) and len(source_path.strip()) > 0)
    @requires(lambda destination_path: isinstance(destination_path, str) and len(destination_path.strip()) > 0)
    async def move_file(
        self,
        source_path: str,
        destination_path: str,
        overwrite: bool = False,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """Move a file from source to destination.
        
        Args:
            source_path: Path to source file
            destination_path: Path to destination file  
            overwrite: Whether to overwrite existing destination
            ctx: MCP context for logging and progress
            
        Returns:
            Dict with operation result and details
        """
        try:
            if ctx:
                await ctx.info(f"Starting file move: {source_path} -> {destination_path}")
            
            # First copy the file
            copy_result = await self.copy_file(source_path, destination_path, overwrite, True, ctx)
            
            if not copy_result["success"]:
                return copy_result
            
            if ctx:
                await ctx.report_progress(75, 100, "Copy complete, removing source")
            
            # Then delete the source
            delete_result = await self.delete_file(source_path, ctx)
            
            if delete_result["success"]:
                if ctx:
                    await ctx.info("File moved successfully")
                    await ctx.report_progress(100, 100, "Move operation complete")
                
                return {
                    "success": True,
                    "message": f"File moved from {source_path} to {destination_path}",
                    "source_path": source_path,
                    "destination_path": destination_path,
                    "operation": "move"
                }
            else:
                # Copy succeeded but delete failed - partial operation
                if ctx:
                    await ctx.error("Copy succeeded but source deletion failed")
                
                return {
                    "success": False,
                    "error": "Partial move: copy succeeded but source deletion failed",
                    "error_type": "partial_operation",
                    "copy_result": copy_result,
                    "delete_result": delete_result,
                    "recovery_suggestions": [
                        "Manually delete source file",
                        "Verify destination file integrity"
                    ]
                }
                
        except Exception as e:
            error_msg = f"Unexpected error in file move: {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "error_type": "unexpected_error"
            }
    
    @requires(lambda file_path: isinstance(file_path, str) and len(file_path.strip()) > 0)
    async def delete_file(
        self,
        file_path: str,
        force: bool = False,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """Delete a file with safety checks.
        
        Args:
            file_path: Path to file to delete
            force: Whether to force deletion (skip some safety checks)
            ctx: MCP context for logging
            
        Returns:
            Dict with operation result and details
        """
        try:
            if ctx:
                await ctx.info(f"Starting file deletion: {file_path}")
            
            # Validate file path
            validation = system_validator.validate_file_path(file_path, "write")
            if not validation.is_valid:
                error_msg = f"Path validation failed: {validation.error_message}"
                if ctx:
                    await ctx.error(error_msg)
                
                return {
                    "success": False,
                    "error": error_msg,
                    "error_type": "validation_error",
                    "recovery_suggestion": validation.recovery_suggestion
                }
            
            path_obj = Path(validation.sanitized_input)
            
            # Safety checks
            if not path_obj.exists():
                if ctx:
                    await ctx.info("File does not exist (already deleted)")
                
                return {
                    "success": True,
                    "message": "File does not exist (no action needed)",
                    "file_path": str(path_obj)
                }
            
            if path_obj.is_dir():
                return {
                    "success": False,
                    "error": "Path is a directory, not a file",
                    "error_type": "wrong_type",
                    "recovery_suggestions": ["Use directory deletion tool"]
                }
            
            # Additional safety for important system files
            if not force:
                dangerous_patterns = ['/System/', '/usr/', '/bin/', '/sbin/']
                if any(pattern in str(path_obj) for pattern in dangerous_patterns):
                    return {
                        "success": False,
                        "error": "Deletion of system files not allowed",
                        "error_type": "safety_violation",
                        "recovery_suggestions": ["Use force=true if absolutely necessary"]
                    }
            
            # Perform deletion
            try:
                path_obj.unlink()
                
                if ctx:
                    await ctx.info(f"File deleted successfully: {path_obj}")
                
                return {
                    "success": True,
                    "message": f"File deleted: {path_obj}",
                    "file_path": str(path_obj)
                }
                
            except PermissionError:
                return {
                    "success": False,
                    "error": "Permission denied for file deletion",
                    "error_type": "permission_error",
                    "recovery_suggestions": ["Check file permissions", "Run with elevated privileges"]
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Deletion failed: {str(e)}",
                    "error_type": "filesystem_error"
                }
                
        except Exception as e:
            error_msg = f"Unexpected error in file deletion: {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "error_type": "unexpected_error"
            }
    
    @requires(lambda directory_path: isinstance(directory_path, str) and len(directory_path.strip()) > 0)
    async def create_directory(
        self,
        directory_path: str,
        parents: bool = True,
        exist_ok: bool = True,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """Create a directory with optional parent creation.
        
        Args:
            directory_path: Path to directory to create
            parents: Whether to create parent directories
            exist_ok: Whether to succeed if directory exists
            ctx: MCP context for logging
            
        Returns:
            Dict with operation result and details
        """
        try:
            if ctx:
                await ctx.info(f"Creating directory: {directory_path}")
            
            # Validate path
            validation = system_validator.validate_file_path(directory_path, "write")
            if not validation.is_valid:
                error_msg = f"Path validation failed: {validation.error_message}"
                if ctx:
                    await ctx.error(error_msg)
                
                return {
                    "success": False,
                    "error": error_msg,
                    "error_type": "validation_error"
                }
            
            path_obj = Path(validation.sanitized_input)
            
            # Create directory
            try:
                path_obj.mkdir(parents=parents, exist_ok=exist_ok)
                
                if ctx:
                    await ctx.info(f"Directory created successfully: {path_obj}")
                
                return {
                    "success": True,
                    "message": f"Directory created: {path_obj}",
                    "directory_path": str(path_obj),
                    "parents_created": parents
                }
                
            except FileExistsError:
                return {
                    "success": False,
                    "error": "Directory already exists and exist_ok=False",
                    "error_type": "already_exists"
                }
            except PermissionError:
                return {
                    "success": False,
                    "error": "Permission denied for directory creation",
                    "error_type": "permission_error"
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Directory creation failed: {str(e)}",
                    "error_type": "filesystem_error"
                }
                
        except Exception as e:
            error_msg = f"Unexpected error in directory creation: {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "error_type": "unexpected_error"
            }
    
    @requires(lambda directory_path: isinstance(directory_path, str) and len(directory_path.strip()) > 0)
    async def list_directory(
        self,
        directory_path: str,
        include_hidden: bool = False,
        max_items: int = 1000,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """List directory contents with filtering and limits.
        
        Args:
            directory_path: Path to directory to list
            include_hidden: Whether to include hidden files (starting with .)
            max_items: Maximum number of items to return
            ctx: MCP context for logging
            
        Returns:
            Dict with directory listing and metadata
        """
        try:
            if ctx:
                await ctx.info(f"Listing directory: {directory_path}")
            
            # Validate path
            validation = system_validator.validate_file_path(directory_path, "read")
            if not validation.is_valid:
                return {
                    "success": False,
                    "error": f"Path validation failed: {validation.error_message}",
                    "error_type": "validation_error"
                }
            
            path_obj = Path(validation.sanitized_input)
            
            if not path_obj.exists():
                return {
                    "success": False,
                    "error": "Directory does not exist",
                    "error_type": "not_found"
                }
            
            if not path_obj.is_dir():
                return {
                    "success": False,
                    "error": "Path is not a directory",
                    "error_type": "wrong_type"
                }
            
            # List directory contents
            items = []
            item_count = 0
            
            try:
                for item in path_obj.iterdir():
                    if item_count >= max_items:
                        break
                    
                    # Skip hidden files unless requested
                    if not include_hidden and item.name.startswith('.'):
                        continue
                    
                    try:
                        stat_info = item.stat()
                        items.append({
                            "name": item.name,
                            "path": str(item),
                            "type": "directory" if item.is_dir() else "file",
                            "size": stat_info.st_size if item.is_file() else None,
                            "modified": stat_info.st_mtime,
                            "permissions": oct(stat_info.st_mode)[-3:]
                        })
                        item_count += 1
                        
                    except (PermissionError, OSError):
                        # Skip items we can't access
                        continue
                
                if ctx:
                    await ctx.info(f"Listed {len(items)} items from {directory_path}")
                
                return {
                    "success": True,
                    "directory_path": str(path_obj),
                    "items": items,
                    "total_items": len(items),
                    "truncated": item_count >= max_items,
                    "include_hidden": include_hidden
                }
                
            except PermissionError:
                return {
                    "success": False,
                    "error": "Permission denied for directory listing",
                    "error_type": "permission_error"
                }
                
        except Exception as e:
            error_msg = f"Unexpected error in directory listing: {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "error_type": "unexpected_error"
            }
    
    @requires(lambda file_path: isinstance(file_path, str) and len(file_path.strip()) > 0)
    async def get_file_info(
        self,
        file_path: str,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """Get detailed information about a file or directory.
        
        Args:
            file_path: Path to file or directory
            ctx: MCP context for logging
            
        Returns:
            Dict with file information and metadata
        """
        try:
            if ctx:
                await ctx.info(f"Getting file info: {file_path}")
            
            # Validate path
            validation = system_validator.validate_file_path(file_path, "read")
            if not validation.is_valid:
                return {
                    "success": False,
                    "error": f"Path validation failed: {validation.error_message}",
                    "error_type": "validation_error"
                }
            
            path_obj = Path(validation.sanitized_input)
            
            if not path_obj.exists():
                return {
                    "success": False,
                    "error": "File or directory does not exist",
                    "error_type": "not_found",
                    "file_path": str(path_obj)
                }
            
            try:
                stat_info = path_obj.stat()
                
                info = {
                    "success": True,
                    "path": str(path_obj),
                    "name": path_obj.name,
                    "type": "directory" if path_obj.is_dir() else "file",
                    "size": stat_info.st_size,
                    "created": stat_info.st_ctime,
                    "modified": stat_info.st_mtime,
                    "accessed": stat_info.st_atime,
                    "permissions": oct(stat_info.st_mode)[-3:],
                    "owner_readable": path_obj.stat().st_mode & 0o400 != 0,
                    "owner_writable": path_obj.stat().st_mode & 0o200 != 0,
                    "owner_executable": path_obj.stat().st_mode & 0o100 != 0
                }
                
                # Additional info for files
                if path_obj.is_file():
                    info["suffix"] = path_obj.suffix
                    info["stem"] = path_obj.stem
                
                if ctx:
                    await ctx.info(f"Retrieved info for {path_obj}")
                
                return info
                
            except PermissionError:
                return {
                    "success": False,
                    "error": "Permission denied for file info access",
                    "error_type": "permission_error"
                }
                
        except Exception as e:
            error_msg = f"Unexpected error getting file info: {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "error_type": "unexpected_error"
            }
    
    @requires(lambda file_path: isinstance(file_path, str) and len(file_path.strip()) > 0)
    async def check_file_exists(
        self,
        file_path: str,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """Check if a file or directory exists.
        
        Args:
            file_path: Path to check
            ctx: MCP context for logging
            
        Returns:
            Dict with existence status and basic info
        """
        try:
            # Basic path validation without permission checks
            if len(file_path.strip()) == 0:
                return {
                    "success": False,
                    "error": "Empty file path",
                    "error_type": "validation_error"
                }
            
            path_obj = Path(file_path.strip()).expanduser()
            
            exists = path_obj.exists()
            
            result = {
                "success": True,
                "file_path": str(path_obj),
                "exists": exists
            }
            
            if exists:
                try:
                    result["type"] = "directory" if path_obj.is_dir() else "file"
                    result["readable"] = path_obj.stat().st_mode & 0o400 != 0
                    result["writable"] = path_obj.stat().st_mode & 0o200 != 0
                except (PermissionError, OSError):
                    result["type"] = "unknown"
                    result["readable"] = False
                    result["writable"] = False
            
            if ctx:
                await ctx.info(f"File exists check: {file_path} -> {exists}")
            
            return result
            
        except Exception as e:
            error_msg = f"Error checking file existence: {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "error_type": "unexpected_error"
            }


def register_file_operation_tools(mcp_server: FastMCP) -> FileOperationTools:
    """Register file operation tools with MCP server."""
    return FileOperationTools(mcp_server)
