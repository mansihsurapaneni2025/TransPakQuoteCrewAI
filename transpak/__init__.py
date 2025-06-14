"""
TransPak AI Quoter - Modular Package Structure
"""

from .core.app_factory import create_app
from .core.config import Config

__version__ = "1.0.0"
__all__ = ["create_app", "Config"]