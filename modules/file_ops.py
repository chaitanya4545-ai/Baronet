"""
OpenClaw File Operations Module
Safe file operations with sandboxing and validation
HARDENED: Atomic writes, input validation, crash consistency
"""
from pathlib import Path
from typing import Optional
import shutil
import tempfile
import os
from datetime import datetime
import re

from core.safety import PermissionLevel
from core.logger import log


class FileOperations:
    """Handles all file operations safely - HARDENED VERSION"""
    
    # HARDENING: Input limits
    MAX_FILENAME_LENGTH = 255
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB for text operations
    
    # HARDENING: Protected files (cannot be deleted)
    PROTECTED_FILES = ['.gitkeep', 'README.md', 'config.json', 'settings.json']
    
    def __init__(self, workspace: str = "C:\\OpenClaw\\workspace"):
        self.workspace = Path(workspace)
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.protected_files_full = [self.workspace / pf for pf in self.PROTECTED_FILES]
        log.info(f"File operations workspace: {self.workspace}")
    
    def _validate_filename(self, filename: str) -> tuple[bool, Optional[str]]:
        """HARDENING: Validate filename for security and size"""
        # Check length
        if len(filename) > self.MAX_FILENAME_LENGTH:
            return False, f"Filename too long (max {self.MAX_FILENAME_LENGTH} chars)"
        
        # Check for path traversal attempts
        if '..' in filename or '~' in filename:
            return False, "Path traversal not allowed (.. or ~)"
        
        # Check for absolute path attempts
        if filename.startswith('/') or filename.startswith('\\') or ':' in filename:
            return False, "Absolute paths not allowed"
        
        # Check for invalid characters (Windows)
        invalid_chars = r'[<>:"|?*]'
        if re.search(invalid_chars, filename):
            return False, f"Invalid characters in filename"
        
        return True, None
    
    def _resolve_path(self, path: str) -> Optional[Path]:
        """Resolve path relative to workspace - HARDENED (BUG FIX: No junk files)"""
        target = Path(path)
        
        # Normalize path to prevent traversal attacks
        try:
            normalized = target.resolve()
        except (OSError, RuntimeError):
            # Invalid path - DON'T create junk file
            log.error(f"Invalid path: {path}")
            return None
        
        # If absolute path, check if it's within workspace
        if target.is_absolute():
            try:
                normalized.relative_to(self.workspace.resolve())
                return normalized
            except ValueError:
                # Outside workspace - BLOCK, don't create file
                log.warning(f"SECURITY: Path {path} outside workspace, blocked")
                return None
        
        # Relative path - join with workspace and resolve
        final_path = (self.workspace / target).resolve()
        
        # Double-check still in workspace after resolution
        try:
            final_path.relative_to(self.workspace.resolve())
            return final_path
        except ValueError:
            log.error(f"SECURITY: Path traversal attempt blocked: {path}")
            return None
    
    def _atomic_write(self, file_path: Path, content: str) -> bool:
        """HARDENING: Atomic file write (crash-safe, BUG FIX: No double close)"""
        temp_fd = None
        temp_path = None
        
        try:
            # Write to temp file first
            temp_fd, temp_path = tempfile.mkstemp(dir=file_path.parent, text=True)
            
            # Write content to temp file
            os.write(temp_fd, content.encode('utf-8'))
            os.close(temp_fd)
            temp_fd = None  # Mark as closed
            
            # Atomic rename (OS-level operation)
            shutil.move(temp_path, file_path)
            return True
            
        except Exception as e:
            log.error(f"Atomic write failed: {e}")
            return False
            
        finally:
            # BUG FIX: Clean up only if still open/exists
            if temp_fd is not None:
                try:
                    os.close(temp_fd)
                except:
                    pass
            
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    pass
    
    def create(self, filename: str, content: str = "") -> dict:
        """
        Create a file with optional content - HARDENED
        Permission: MODERATE
        """
        try:
            # HARDENING: Validate input
            valid, error = self._validate_filename(filename)
            if not valid:
                return {'success': False, 'error': f'Invalid filename: {error}', 'code': 'INVALID_INPUT'}
            
            # HARDENING: Check content size
            if len(content) > self.MAX_CONTENT_LENGTH:
                return {
                    'success': False,
                    'error': f'Content too large (max {self.MAX_CONTENT_LENGTH} bytes)',
                    'code': 'SIZE_LIMIT'
                }
            
            file_path = self._resolve_path(filename)
            
            # BUG FIX: Check if path resolution failed
            if file_path is None:
                return {
                    'success': False,
                    'error': 'Invalid or blocked path',
                    'code': 'INVALID_PATH'
                }
            
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # HARDENING: Use atomic write
            if self._atomic_write(file_path, content):
                log.info(f"Created file: {file_path}")
                return {
                    'success': True,
                    'path': str(file_path),
                    'size': file_path.stat().st_size
                }
            else:
                return {'success': False, 'error': 'Atomic write failed', 'code': 'WRITE_FAILED'}
                
        except Exception as e:
            log.error(f"Failed to create file {filename}: {e}")
            return {
                'success': False,
                'error': str(e),
                'code': 'EXCEPTION'
            }
    
    def read(self, filename: str) -> dict:
        """
        Read file contents
        Permission: SAFE
        """
        try:
            file_path = self._resolve_path(filename)
            
            if not file_path.exists():
                return {
                    'success': False,
                    'error': f'File not found: {file_path}'
                }
            
            content = file_path.read_text(encoding='utf-8')
            
            log.info(f"Read file: {file_path} ({len(content)} chars)")
            return {
                'success': True,
                'path': str(file_path),
                'content': content,
                'size': len(content)
            }
        except Exception as e:
            log.error(f"Failed to read file {filename}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def write(self, filename: str, content: str) -> dict:
        """
        Write content to existing file (overwrites) - HARDENED
        Permission: MODERATE
        """
        try:
            # HARDENING: Validate input
            valid, error = self._validate_filename(filename)
            if not valid:
                return {'success': False, 'error': f'Invalid filename: {error}', 'code': 'INVALID_INPUT'}
            
            # HARDENING: Check content size
            if len(content) > self.MAX_CONTENT_LENGTH:
                return {
                    'success': False,
                    'error': f'Content too large (max {self.MAX_CONTENT_LENGTH} bytes)',
                    'code': 'SIZE_LIMIT'
                }
            
            file_path = self._resolve_path(filename)
            
            if not file_path.exists():
                log.warning(f"File {file_path} does not exist, creating it")
            
            # HARDENING: Use atomic write
            if self._atomic_write(file_path, content):
                log.info(f"Wrote to file: {file_path}")
                return {
                    'success': True,
                    'path': str(file_path),
                    'size': file_path.stat().st_size
                }
            else:
                return {'success': False, 'error': 'Atomic write failed', 'code': 'WRITE_FAILED'}
                
        except Exception as e:
            log.error(f"Failed to write file {filename}: {e}")
            return {
                'success': False,
                'error': str(e),
                'code': 'EXCEPTION'
            }
    
    def delete(self, filename: str) -> dict:
        """
        Delete a file - HARDENED with protected files
        Permission: DANGEROUS
        """
        try:
            file_path = self._resolve_path(filename)
            
            if not file_path.exists():
                return {
                    'success': False,
                    'error': f'File not found: {file_path}',
                    'code': 'NOT_FOUND'
                }
            
            # HARDENING: Check protected files
            if file_path in self.protected_files_full or file_path.name in self.PROTECTED_FILES:
                log.error(f"SECURITY: Attempted to delete protected file: {file_path}")
                return {
                    'success': False,
                    'error': f'Cannot delete protected file: {file_path.name}',
                    'code': 'PROTECTED'
                }
            
            # Backup before delete (crash-safe)
            # BUG FIX: Use dashes instead of colons (Windows-compatible)
            backup_dir = self.workspace / '.backups'
            backup_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')  # Dash, not colon
            backup_path = backup_dir / f"{file_path.stem}_{timestamp}{file_path.suffix}"
            
            try:
                shutil.copy2(file_path, backup_path)
            except Exception as backup_error:
                log.error(f"Backup failed, aborting delete: {backup_error}")
                return {
                    'success': False,
                    'error': 'Backup failed, delete aborted for safety',
                    'code': 'BACKUP_FAILED'
                }
            
            # Only delete if backup succeeded
            file_path.unlink()
            
            log.warning(f"Deleted file: {file_path} (backup: {backup_path})")
            return {
                'success': True,
                'path': str(file_path),
                'backup': str(backup_path)
            }
        except Exception as e:
            log.error(f"Failed to delete file {filename}: {e}")
            return {
                'success': False,
                'error': str(e),
                'code': 'EXCEPTION'
            }
    
    def list_files(self, directory: str = ".") -> dict:
        """
        List files in directory
        Permission: SAFE
        """
        try:
            dir_path = self._resolve_path(directory)
            
            if not dir_path.exists():
                return {
                    'success': False,
                    'error': f'Directory not found: {dir_path}'
                }
            
            files = []
            for item in dir_path.iterdir():
                files.append({
                    'name': item.name,
                    'type': 'dir' if item.is_dir() else 'file',
                    'size': item.stat().st_size if item.is_file() else None,
                    'modified': datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                })
            
            log.info(f"Listed {len(files)} items in {dir_path}")
            return {
                'success': True,
                'path': str(dir_path),
                'files': files,
                'count': len(files)
            }
        except Exception as e:
            log.error(f"Failed to list directory {directory}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_info(self, filename: str) -> dict:
        """
        Get file information
        Permission: SAFE
        """
        try:
            file_path = self._resolve_path(filename)
            
            if not file_path.exists():
                return {
                    'success': False,
                    'error': f'File not found: {file_path}'
                }
            
            stat = file_path.stat()
            
            return {
                'success': True,
                'path': str(file_path),
                'name': file_path.name,
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'is_file': file_path.is_file(),
                'is_dir': file_path.is_dir()
            }
        except Exception as e:
            log.error(f"Failed to get info for {filename}: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# Global file operations instance
file_ops = FileOperations()
