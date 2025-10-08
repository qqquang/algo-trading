"""
ORB Strategy Package

Opening Range Breakout (ORB) trading strategy implementation.
"""

from .orb_strategy import ORBStrategy
from . import orb_config

__version__ = '1.0.0'
__all__ = ['ORBStrategy', 'orb_config']
