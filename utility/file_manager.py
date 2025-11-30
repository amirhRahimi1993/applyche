"""
File management utility for handling file uploads with size limits, folder cleanup, and rate limiting.
"""
import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Tuple, List
import sqlite3
import json


class FileManager:
    """Manages file uploads with size limits, folder cleanup, and rate limiting"""
    
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
    MAX_FOLDER_SIZE = 30 * 1024 * 1024  # 30 MB
    MAX_UPLOADS_PER_DAY = 20
    
    def __init__(self, base_folder: str = "uploaded_folders"):
        self.base_folder = Path(base_folder)
        self.base_folder.mkdir(exist_ok=True)
        self.rate_limit_db = self.base_folder / ".rate_limits.db"
        self._init_rate_limit_db()
    
    def _init_rate_limit_db(self):
        """Initialize SQLite database for rate limiting"""
        conn = sqlite3.connect(self.rate_limit_db)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS upload_logs (
                user_email TEXT NOT NULL,
                upload_date DATE NOT NULL,
                upload_count INTEGER DEFAULT 1,
                PRIMARY KEY (user_email, upload_date)
            )
        """)
        conn.commit()
        conn.close()
    
    def check_rate_limit(self, user_email: str) -> Tuple[bool, str]:
        """
        Check if user has exceeded daily upload limit.
        Returns (allowed, message)
        """
        today = datetime.now().date()
        conn = sqlite3.connect(self.rate_limit_db)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT upload_count FROM upload_logs
            WHERE user_email = ? AND upload_date = ?
        """, (user_email.lower(), today))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            count = result[0]
            if count >= self.MAX_UPLOADS_PER_DAY:
                return False, f"Daily upload limit reached ({self.MAX_UPLOADS_PER_DAY} files per day). Please try again tomorrow."
            return True, f"{count}/{self.MAX_UPLOADS_PER_DAY} uploads today"
        else:
            return True, f"0/{self.MAX_UPLOADS_PER_DAY} uploads today"
    
    def record_upload(self, user_email: str):
        """Record an upload for rate limiting"""
        today = datetime.now().date()
        conn = sqlite3.connect(self.rate_limit_db)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO upload_logs (user_email, upload_date, upload_count)
            VALUES (?, ?, 1)
            ON CONFLICT(user_email, upload_date) 
            DO UPDATE SET upload_count = upload_count + 1
        """, (user_email.lower(), today))
        
        conn.commit()
        conn.close()
    
    def get_user_folder(self, user_email: str, subfolder: str) -> Path:
        """Get or create user's subfolder"""
        # Sanitize email for filesystem (replace @ and . with _)
        safe_email = user_email.replace("@", "_at_").replace(".", "_")
        user_folder = self.base_folder / safe_email / subfolder
        user_folder.mkdir(parents=True, exist_ok=True)
        return user_folder
    
    def check_file_size(self, file_path: str) -> Tuple[bool, str]:
        """Check if file size is within limit"""
        size = os.path.getsize(file_path)
        if size > self.MAX_FILE_SIZE:
            size_mb = size / (1024 * 1024)
            max_mb = self.MAX_FILE_SIZE / (1024 * 1024)
            return False, f"File size ({size_mb:.2f} MB) exceeds maximum allowed size ({max_mb} MB)"
        return True, f"File size: {size / (1024 * 1024):.2f} MB"
    
    def get_folder_size(self, folder_path: Path) -> int:
        """Calculate total size of all files in folder"""
        total_size = 0
        for file_path in folder_path.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        return total_size
    
    def cleanup_folder(self, folder_path: Path):
        """Delete oldest files until folder size is under limit"""
        # Get all files with their modification times
        files = []
        for file_path in folder_path.rglob("*"):
            if file_path.is_file():
                files.append((file_path, file_path.stat().st_mtime))
        
        # Sort by modification time (oldest first)
        files.sort(key=lambda x: x[1])
        
        current_size = self.get_folder_size(folder_path)
        
        # Delete oldest files until under limit
        deleted_count = 0
        for file_path, _ in files:
            if current_size <= self.MAX_FOLDER_SIZE:
                break
            
            file_size = file_path.stat().st_size
            try:
                file_path.unlink()
                current_size -= file_size
                deleted_count += 1
            except Exception as e:
                print(f"Warning: Could not delete {file_path}: {e}")
        
        return deleted_count
    
    def save_file(
        self, 
        source_path: str, 
        user_email: str, 
        subfolder: str,
        custom_filename: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Path]]:
        """
        Save file to user's folder with size checks and cleanup.
        Returns (success, message, saved_path)
        """
        # Check rate limit
        allowed, rate_msg = self.check_rate_limit(user_email)
        if not allowed:
            return False, rate_msg, None
        
        # Check file size
        valid_size, size_msg = self.check_file_size(source_path)
        if not valid_size:
            return False, size_msg, None
        
        # Get destination folder
        dest_folder = self.get_user_folder(user_email, subfolder)
        
        # Check folder size and cleanup if needed
        current_size = self.get_folder_size(dest_folder)
        if current_size >= self.MAX_FOLDER_SIZE:
            deleted = self.cleanup_folder(dest_folder)
            if deleted > 0:
                print(f"Cleaned up {deleted} old file(s) to make room")
        
        # Generate filename
        if custom_filename:
            filename = custom_filename
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            original_name = Path(source_path).stem
            extension = Path(source_path).suffix
            filename = f"{original_name}_{timestamp}{extension}"
        
        dest_path = dest_folder / filename
        
        # Copy file
        try:
            shutil.copy2(source_path, dest_path)
            
            # Record upload for rate limiting
            self.record_upload(user_email)
            
            # Final cleanup check (in case file was large)
            final_size = self.get_folder_size(dest_folder)
            if final_size > self.MAX_FOLDER_SIZE:
                self.cleanup_folder(dest_folder)
            
            return True, f"File saved successfully. {size_msg}", dest_path
            
        except Exception as e:
            return False, f"Failed to save file: {str(e)}", None
    
    def get_user_upload_stats(self, user_email: str) -> dict:
        """Get upload statistics for user"""
        today = datetime.now().date()
        conn = sqlite3.connect(self.rate_limit_db)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT upload_count FROM upload_logs
            WHERE user_email = ? AND upload_date = ?
        """, (user_email.lower(), today))
        
        result = cursor.fetchone()
        conn.close()
        
        today_count = result[0] if result else 0
        remaining = max(0, self.MAX_UPLOADS_PER_DAY - today_count)
        
        return {
            "today_count": today_count,
            "max_per_day": self.MAX_UPLOADS_PER_DAY,
            "remaining": remaining,
            "max_file_size_mb": self.MAX_FILE_SIZE / (1024 * 1024),
            "max_folder_size_mb": self.MAX_FOLDER_SIZE / (1024 * 1024)
        }

