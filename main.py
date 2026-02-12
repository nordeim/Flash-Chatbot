"""Entry point for Hugging Face Spaces deployment.

This file serves as the entry point for Hugging Face Spaces.
It properly sets up the Python path and imports from the src module.
"""

import os
import sys

# Add the current directory to Python path so 'src' can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the main application
from src.main import main

if __name__ == "__main__":
    main()
