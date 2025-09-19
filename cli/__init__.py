"""CLI module for Wordle Bot.

This module handles command line interface functionality including
argument parsing, command routing, and CLI-specific utilities.
"""

from .argument_parser import ArgumentParser
from .command_router import CommandRouter

__all__ = ["ArgumentParser", "CommandRouter"]
