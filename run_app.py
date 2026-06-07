#!/usr/bin/env python3
"""
run_app.py  –  ZimAgent Desktop standalone launcher.

Used by PyInstaller as the entry-point script.
Can also be run directly:  python run_app.py
"""

import sys
import os

# Make the package importable from the repo root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from zimagent.main import main

if __name__ == "__main__":
    sys.exit(main())
