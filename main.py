"""
Call Copilot - Main Entry Point
Launch the overlay UI for real-time sales call assistance.
"""
import sys
import os

# Ensure src is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.overlay import main

if __name__ == "__main__":
    main()
