"""
File Upload Security Utility
Validates file uploads with MIME type checking, size limits, and safe storage
"""
import os
import uuid
import magic
from pathlib import Path
from typing import Optional, Tuple
from fastapi import UploadFile, HTTPException, status
import logging

from ..config import settings

logger = logging.getLogger(__name__)


class FileUploadValidator:
    """Validates and secures file uploads"""
    
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.max_size_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        self.allowed_types = settings.get_allowed_upload_types()
        
        # Ensure upload directory exists
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def validate_file(self, file: UploadFile) -> Tuple[bool, Optional[str]]:
        """
        Validate uploaded file
        
        Returns:
            (is_valid, error_message)
        """
        # Check 1: File must have a filename
        if not file.filename:
            return False, "No filename provided"
        
        # Check 2: Block double extensions (e.g., file.pdf.exe)
        if self._has_double_extension(file.filename):
            logger.warning(f"Blocked double extension: {file.filename}")
            return False, "Invalid filename: double extensions not allowed"
        
        # Check 3: Read file content for validation
        try:
            content = file.file.read()
            file.file.seek(0)  # Reset file pointer
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            return False, "Failed to read file"
        
        # Check 4: File size validation
        file_size = len(content)
        if file_size > self.max_size_bytes:
            size_mb = file_size / (1024 * 1024)
            max_mb = self.max_size_bytes / (1024 * 1024)
            logger.warning(
                f"File too large: {file.filename} ({size_mb:.2f}MB > {max_mb}MB)"
            )
            return False, f"File too large. Maximum size: {max_mb}MB"
        
        # Check 5: MIME type validation using python-magic
        try:
            mime_type = magic.from_buffer(content, mime=True)
        except Exception as e:
            logger.error(f"Error detecting MIME type: {e}")
            # Fallback to file extension check
            mime_type = self._get_mime_from_extension(file.filename)
        
        if mime_type not in self.allowed_types:
            logger.warning(
                f"Blocked file with MIME type: {mime_type} (filename: {file.filename})"
            )
            return False, (
                f"File type not allowed: {mime_type}. "
                f"Allowed types: PDF, JPEG, PNG, DOC, DOCX"
            )
        
        return True, None
    
    def save_file(self, file: UploadFile) -> Tuple[str, str]:
        """
        Save file with UUID filename
        
        Returns:
            (file_path, original_filename)
        """
        # Validate first
        is_valid, error = self.validate_file(file)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )
        
        # Generate UUID filename
        file_extension = Path(file.filename).suffix.lower()
        safe_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = self.upload_dir / safe_filename
        
        # Save file
        try:
            content = file.file.read()
            with open(file_path, "wb") as f:
                f.write(content)
            
            logger.info(
                f"File saved: {file.filename} -> {safe_filename} "
                f"({len(content)} bytes)"
            )
            
            return str(file_path), file.filename
            
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save file: {str(e)}"
            )
    
    def delete_file(self, file_path: str) -> bool:
        """Delete uploaded file"""
        try:
            path = Path(file_path)
            if path.exists() and path.parent == self.upload_dir:
                path.unlink()
                logger.info(f"File deleted: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return False
    
    def _has_double_extension(self, filename: str) -> bool:
        """Check for double extensions (e.g., file.pdf.exe)"""
        parts = filename.split('.')
        if len(parts) < 3:
            return False
        
        # Check if second-to-last part looks like an extension
        dangerous_extensions = [
            'exe', 'bat', 'cmd', 'com', 'pif', 'scr', 'vbs', 'js',
            'jar', 'zip', 'rar', '7z', 'tar', 'gz', 'sh', 'php',
            'asp', 'aspx', 'jsp', 'py', 'rb', 'pl'
        ]
        
        second_last = parts[-2].lower()
        return second_last in dangerous_extensions
    
    def _get_mime_from_extension(self, filename: str) -> str:
        """Fallback MIME type detection from extension"""
        ext = Path(filename).suffix.lower()
        mime_map = {
            '.pdf': 'application/pdf',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        return mime_map.get(ext, 'application/octet-stream')


# Global instance
file_upload_validator = FileUploadValidator()
