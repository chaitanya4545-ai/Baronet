"""
OpenClaw Logger
Handles all logging with rotation, levels, and formatting
"""
from loguru import logger
import sys
from pathlib import Path
from datetime import datetime


class OpenClawLogger:
    """Centralized logging system for OpenClaw"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Remove default logger
        logger.remove()
        
        # Console output with colors
        logger.add(
            sys.stdout,
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
            level="INFO",
            colorize=True
        )
        
        # File output with rotation
        logger.add(
            self.log_dir / "openclaw_{time:YYYY-MM-DD}.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
            level="DEBUG",
            rotation="00:00",  # New file each day
            retention="30 days",
            compression="zip"
        )
        
        # Command history log (separate file)
        logger.add(
            self.log_dir / "commands.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
            level="INFO",
            filter=lambda record: "COMMAND" in record["extra"]
        )
        
        self.logger = logger
    
    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)
    
    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)
    
    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Log error message"""
        self.logger.error(message)
    
    def command(self, command: str, result: str):
        """Log command execution"""
        self.logger.bind(COMMAND=True).info(f"[CMD] {command} → {result}")
    
    def success(self, message: str):
        """Log success message"""
        self.logger.success(message)


# Global logger instance
log = OpenClawLogger()
